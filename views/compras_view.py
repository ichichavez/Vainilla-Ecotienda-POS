from __future__ import annotations
import customtkinter as ctk
from datetime import date
from tkinter import messagebox

import models.producto as producto_model
import models.compra as compra_model
from utils.ui import debounce


# ─────────────────────────────────────────────────────────────────────────────
# Helper dialog
# ─────────────────────────────────────────────────────────────────────────────

class _CompraItemDialog(ctk.CTkToplevel):
    """Dialog to enter quantity and purchase price for a product."""

    def __init__(self, master, producto: dict):
        super().__init__(master)
        self.title("Agregar a compra")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self._cancel)
        self.grab_set()
        self.result = None

        nombre = producto["nombre"]
        info = "  ·  ".join(filter(None, [
            producto.get("talle", ""), producto.get("color", "")
        ]))
        self.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self, text=nombre,
                     font=ctk.CTkFont(size=14, weight="bold")).grid(
            row=0, column=0, columnspan=2, padx=20, pady=(16, 2), sticky="w")
        if info:
            ctk.CTkLabel(self, text=info, text_color="gray60").grid(
                row=1, column=0, columnspan=2, padx=20, pady=(0, 10), sticky="w")

        ctk.CTkLabel(self, text="Cantidad:").grid(
            row=2, column=0, padx=16, pady=8, sticky="w")
        self._qty_var = ctk.StringVar(value="1")
        ctk.CTkEntry(self, textvariable=self._qty_var, width=80, height=36).grid(
            row=2, column=1, padx=16, pady=8, sticky="w")

        ctk.CTkLabel(self, text="Precio compra:").grid(
            row=3, column=0, padx=16, pady=8, sticky="w")
        self._precio_var = ctk.StringVar(value="0")
        ctk.CTkEntry(self, textvariable=self._precio_var, width=100, height=36).grid(
            row=3, column=1, padx=16, pady=8, sticky="w")

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=4, column=0, columnspan=2, padx=16, pady=(12, 16), sticky="ew")
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkButton(btn_frame, text="Agregar", height=38,
                      command=self._confirm).grid(
            row=0, column=0, padx=(0, 4), sticky="ew")
        ctk.CTkButton(btn_frame, text="Cancelar", height=38,
                      fg_color="transparent", border_width=1,
                      text_color=("gray10", "gray90"),
                      command=self._cancel).grid(
            row=0, column=1, padx=(4, 0), sticky="ew")

        self.update_idletasks()
        w, h = 360, 260
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    def _cancel(self):
        self.grab_release()
        self.destroy()

    def _confirm(self):
        try:
            qty = int(self._qty_var.get())
            precio = float(self._precio_var.get().replace(",", "."))
            if qty <= 0 or precio < 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning(
                "Error", "Ingresá cantidad y precio válidos.", parent=self)
            return
        self.result = (qty, precio)
        self.grab_release()
        self.destroy()


# ─────────────────────────────────────────────────────────────────────────────
# Main view
# ─────────────────────────────────────────────────────────────────────────────

class ComprasView(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.carrito: list[dict] = []   # [{producto, cantidad, precio_compra}]
        self._search_after = None
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self._build_ui()

    # ── UI construction ──────────────────────────────────────────────────────

    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, padx=24, pady=(20, 8), sticky="ew")
        ctk.CTkLabel(header, text="Nueva Compra",
                     font=ctk.CTkFont(size=24, weight="bold")).pack(side="left")

        self._build_info_bar()

        main = ctk.CTkFrame(self, fg_color="transparent")
        main.grid(row=2, column=0, padx=24, pady=(0, 16), sticky="nsew")
        main.grid_columnconfigure(0, weight=3)
        main.grid_columnconfigure(1, weight=2)
        main.grid_rowconfigure(0, weight=1)
        self._build_product_panel(main)
        self._build_cart_panel(main)

    def _build_info_bar(self):
        bar = ctk.CTkFrame(self)
        bar.grid(row=1, column=0, padx=24, pady=(0, 8), sticky="ew")
        bar.grid_columnconfigure(1, weight=1)
        bar.grid_columnconfigure(3, weight=1)

        ctk.CTkLabel(bar, text="Proveedor:",
                     font=ctk.CTkFont(size=13)).grid(
            row=0, column=0, padx=(14, 6), pady=(10, 4))
        self._proveedor_var = ctk.StringVar()
        ctk.CTkEntry(bar, textvariable=self._proveedor_var,
                     placeholder_text="Nombre del proveedor").grid(
            row=0, column=1, padx=6, pady=(10, 4), sticky="ew")

        ctk.CTkLabel(bar, text="N° Factura:",
                     font=ctk.CTkFont(size=13)).grid(
            row=0, column=2, padx=(14, 6), pady=(10, 4))
        self._nro_factura_var = ctk.StringVar()
        ctk.CTkEntry(bar, textvariable=self._nro_factura_var,
                     placeholder_text="Opcional").grid(
            row=0, column=3, padx=(6, 14), pady=(10, 4), sticky="ew")

        ctk.CTkLabel(bar, text="Forma pago:",
                     font=ctk.CTkFont(size=13)).grid(
            row=1, column=0, padx=(14, 6), pady=(4, 10))
        self._forma_pago_var = ctk.StringVar(value="efectivo")
        ctk.CTkComboBox(bar, values=["efectivo", "transferencia", "cheque", "cuenta corriente"],
                        variable=self._forma_pago_var, width=160).grid(
            row=1, column=1, padx=6, pady=(4, 10), sticky="w")

        ctk.CTkLabel(bar, text="Notas:",
                     font=ctk.CTkFont(size=13)).grid(
            row=1, column=2, padx=(14, 6), pady=(4, 10))
        self._notas_var = ctk.StringVar()
        ctk.CTkEntry(bar, textvariable=self._notas_var,
                     placeholder_text="Opcional").grid(
            row=1, column=3, padx=(6, 14), pady=(4, 10), sticky="ew")

    def _build_product_panel(self, parent):
        frame = ctk.CTkFrame(parent)
        frame.grid(row=0, column=0, padx=(0, 6), pady=0, sticky="nsew")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(3, weight=1)

        ctk.CTkLabel(frame, text="Productos",
                     font=ctk.CTkFont(size=15, weight="bold")).grid(
            row=0, column=0, padx=16, pady=(14, 6), sticky="w")

        # ── Barcode scan entry ──
        scan_frame = ctk.CTkFrame(frame, fg_color="transparent")
        scan_frame.grid(row=1, column=0, padx=12, pady=(0, 4), sticky="ew")
        scan_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(scan_frame, text="📷", font=ctk.CTkFont(size=16)).grid(
            row=0, column=0, padx=(0, 6))
        self._scan_var = ctk.StringVar()
        self._scan_entry = ctk.CTkEntry(
            scan_frame, textvariable=self._scan_var,
            placeholder_text="Escanear código de barras...")
        self._scan_entry.grid(row=0, column=1, sticky="ew")
        self._scan_entry.bind("<Return>", lambda _: self._on_scan())

        # ── Text search ──
        search_frame = ctk.CTkFrame(frame, fg_color="transparent")
        search_frame.grid(row=2, column=0, padx=12, pady=(0, 6), sticky="ew")
        search_frame.grid_columnconfigure(0, weight=1)
        self._search_var = ctk.StringVar()
        ctk.CTkEntry(search_frame, textvariable=self._search_var,
                     placeholder_text="Buscar producto...").grid(
            row=0, column=0, sticky="ew")
        self._search_var.trace_add(
            "write",
            lambda *_: debounce(self, "_search_after", 250, self._filter_products),
        )

        self._prod_scroll = ctk.CTkScrollableFrame(frame)
        self._prod_scroll.grid(row=3, column=0, padx=12, pady=(0, 12), sticky="nsew")
        self._prod_scroll.grid_columnconfigure(0, weight=1)

    def _build_cart_panel(self, parent):
        frame = ctk.CTkFrame(parent)
        frame.grid(row=0, column=1, padx=(6, 0), pady=0, sticky="nsew")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(frame, text="Items de compra",
                     font=ctk.CTkFont(size=15, weight="bold")).grid(
            row=0, column=0, padx=16, pady=(14, 6), sticky="w")

        self._cart_scroll = ctk.CTkScrollableFrame(frame)
        self._cart_scroll.grid(row=1, column=0, padx=12, pady=6, sticky="nsew")
        self._cart_scroll.grid_columnconfigure(0, weight=1)

        self._total_lbl = ctk.CTkLabel(
            frame, text="Total: Gs. 0.00",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        self._total_lbl.grid(row=2, column=0, padx=16, pady=8)

        ctk.CTkButton(
            frame, text="CONFIRMAR COMPRA", height=46,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#2d6a4f", hover_color="#1b4332",
            command=self._confirmar_compra
        ).grid(row=3, column=0, padx=12, pady=(0, 14), sticky="ew")

    # ── Refresh ──────────────────────────────────────────────────────────────

    def refresh(self, **kwargs):
        self.carrito = []
        self._proveedor_var.set("")
        self._nro_factura_var.set("")
        self._forma_pago_var.set("efectivo")
        self._notas_var.set("")
        self._scan_var.set("")
        self._search_var.set("")
        self._filter_products()
        self._render_cart()

    # ── Scan ─────────────────────────────────────────────────────────────────

    def _on_scan(self):
        codigo = self._scan_var.get().strip()
        self._scan_var.set("")
        if not codigo:
            return
        producto = producto_model.get_by_codigo_barras(codigo)
        if not producto:
            messagebox.showwarning(
                "Código no encontrado",
                f"No se encontró ningún producto con el código:\n{codigo}",
                parent=self)
            return
        self._add_to_cart(producto)

    # ── Product panel ────────────────────────────────────────────────────────

    def _filter_products(self):
        texto = self._search_var.get().strip()
        productos = (producto_model.search(texto, limit=80)
                     if texto else
                     producto_model.get_all(limit=80))
        for w in self._prod_scroll.winfo_children():
            w.destroy()
        for p in productos:
            self._make_product_row(p)

    def _make_product_row(self, p: dict):
        row = ctk.CTkFrame(self._prod_scroll, corner_radius=8)
        row.pack(fill="x", pady=3)
        row.grid_columnconfigure(1, weight=1)

        stock = p["stock"]
        ctk.CTkLabel(row, text=f" {stock} ",
                     fg_color="#2d6a4f", corner_radius=6,
                     font=ctk.CTkFont(size=11)).grid(
            row=0, column=0, padx=(10, 8), pady=10)

        info_parts = [p["nombre"]]
        if p.get("talle"):
            info_parts.append(f"T:{p['talle']}")
        if p.get("color"):
            info_parts.append(p["color"])
        ctk.CTkLabel(row, text="  ".join(info_parts),
                     font=ctk.CTkFont(size=12), anchor="w").grid(
            row=0, column=1, pady=10, sticky="w")

        ctk.CTkButton(
            row, text="+", width=36, height=28,
            command=lambda prod=p: self._add_to_cart(prod)
        ).grid(row=0, column=2, padx=10, pady=8)

    def _add_to_cart(self, producto: dict):
        dlg = _CompraItemDialog(self, producto)
        self.wait_window(dlg)
        if not dlg.result:
            return
        qty, precio_compra = dlg.result
        for item in self.carrito:
            if item["producto"]["id"] == producto["id"]:
                item["cantidad"] += qty
                item["precio_compra"] = precio_compra
                self._render_cart()
                return
        self.carrito.append({
            "producto":      producto,
            "cantidad":      qty,
            "precio_compra": precio_compra,
        })
        self._render_cart()

    # ── Cart panel ───────────────────────────────────────────────────────────

    def _render_cart(self):
        for w in self._cart_scroll.winfo_children():
            w.destroy()

        total = 0.0
        for idx, item in enumerate(self.carrito):
            total += item["cantidad"] * item["precio_compra"]
            self._make_cart_row(idx, item)

        if not self.carrito:
            ctk.CTkLabel(self._cart_scroll, text="Sin items.",
                         text_color="gray60").pack(pady=20)

        self._total_lbl.configure(text=f"Total: Gs. {total:,.2f}")

    def _make_cart_row(self, idx: int, item: dict):
        p = item["producto"]
        qty = item["cantidad"]
        precio = item["precio_compra"]
        subtotal = qty * precio

        row = ctk.CTkFrame(self._cart_scroll, corner_radius=8)
        row.pack(fill="x", pady=3)
        row.grid_columnconfigure(0, weight=1)

        name_parts = [p["nombre"]]
        if p.get("talle"):
            name_parts.append(f"T:{p['talle']}")
        ctk.CTkLabel(row, text=" · ".join(name_parts),
                     font=ctk.CTkFont(size=11, weight="bold"), anchor="w").grid(
            row=0, column=0, padx=10, pady=(8, 2), sticky="w")

        info = ctk.CTkFrame(row, fg_color="transparent")
        info.grid(row=1, column=0, padx=8, pady=(0, 8), sticky="ew")
        info.grid_columnconfigure(2, weight=1)

        ctk.CTkLabel(info, text=f"x{qty}  @  Gs. {precio:,.2f}").grid(
            row=0, column=0, padx=4)
        ctk.CTkLabel(info, text=f"= Gs. {subtotal:,.2f}",
                     font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=1, padx=8)

        ctk.CTkButton(
            info, text="✕", width=28, height=24,
            fg_color="#e63946", hover_color="#c1121f",
            command=lambda i=idx: self._remove_item(i)
        ).grid(row=0, column=3, padx=4)

    def _remove_item(self, idx: int):
        self.carrito.pop(idx)
        self._render_cart()

    # ── Confirm ──────────────────────────────────────────────────────────────

    def _confirmar_compra(self):
        if not self.carrito:
            messagebox.showwarning(
                "Atención", "Agregá al menos un producto.", parent=self)
            return

        total = sum(it["cantidad"] * it["precio_compra"] for it in self.carrito)
        proveedor = self._proveedor_var.get().strip()

        confirm = messagebox.askyesno(
            "Confirmar compra",
            f"Proveedor: {proveedor or '(sin especificar)'}\n"
            f"Total: Gs. {total:,.2f}\n"
            f"Items: {len(self.carrito)}\n\n"
            f"¿Confirmar? El stock se incrementará.",
            parent=self
        )
        if not confirm:
            return

        items = [
            {
                "producto_id":   it["producto"]["id"],
                "cantidad":      it["cantidad"],
                "precio_compra": it["precio_compra"],
            }
            for it in self.carrito
        ]
        compra_model.create(
            fecha=date.today().isoformat(),
            proveedor=proveedor,
            notas=self._notas_var.get().strip(),
            items=items,
            numero_factura=self._nro_factura_var.get().strip(),
            forma_pago=self._forma_pago_var.get(),
        )
        messagebox.showinfo(
            "Listo", "Compra registrada y stock actualizado.", parent=self)
        self.refresh()
