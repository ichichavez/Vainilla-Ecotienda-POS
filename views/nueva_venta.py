from __future__ import annotations
import customtkinter as ctk
from datetime import date
from tkinter import messagebox

import models.cliente as cliente_model
import models.producto as producto_model
import models.venta as venta_model
from utils.ui import debounce


# ─────────────────────────────────────────────────────────────────────────────
# Helper dialogs
# ─────────────────────────────────────────────────────────────────────────────

class SelectClienteDialog(ctk.CTkToplevel):
    """Modal to search and select a client."""

    def __init__(self, master):
        super().__init__(master)
        self.title("Seleccionar cliente")
        self.geometry("480x480")
        self.protocol("WM_DELETE_WINDOW", self._cancel)
        self.grab_set()
        self.result = None
        self._search_after = None
        self._build_ui()
        self._load("")

    def _cancel(self):
        self.grab_release()
        self.destroy()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        top = ctk.CTkFrame(self, fg_color="transparent")
        top.grid(row=0, column=0, padx=16, pady=12, sticky="ew")
        top.grid_columnconfigure(0, weight=1)

        self._search_var = ctk.StringVar()
        ctk.CTkEntry(top, textvariable=self._search_var,
                     placeholder_text="Buscar por nombre, CI, ciudad o correo...").grid(
            row=0, column=0, sticky="ew")
        self._search_var.trace_add(
            "write",
            lambda *_: debounce(
                self, "_search_after", 250,
                lambda: self._load(self._search_var.get()),
            ),
        )

        self._scroll = ctk.CTkScrollableFrame(self)
        self._scroll.grid(row=1, column=0, padx=16, pady=(0, 16), sticky="nsew")
        self._scroll.grid_columnconfigure(0, weight=1)

    def _load(self, texto: str):
        for w in self._scroll.winfo_children():
            w.destroy()
        clientes = (cliente_model.search(texto)
                    if texto.strip() else
                    cliente_model.get_all(limit=80))
        for c in clientes:
            nombre_completo = " ".join(filter(None, [c["nombre"], c.get("apellido", "")]))
            label = f"{nombre_completo}  —  {c['ciudad']}"
            btn = ctk.CTkButton(
                self._scroll, text=label, anchor="w",
                fg_color="transparent",
                hover_color=("gray70", "gray30"),
                text_color=("gray10", "gray90"),
                command=lambda x=c: self._select(x)
            )
            btn.pack(fill="x", pady=2)

    def _select(self, cliente: dict):
        self.result = cliente
        self.grab_release()
        self.destroy()


class NuevaClienteDialog(ctk.CTkToplevel):
    """Modal to create a new client inline."""

    def __init__(self, master):
        super().__init__(master)
        self.title("Nuevo cliente")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self._cancel)
        self.grab_set()
        self.result = None
        self._build_ui()
        self.update_idletasks()
        w, h = 460, 530
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        container = ctk.CTkFrame(self, fg_color="transparent")
        container.grid(row=0, column=0, sticky="nsew")
        container.grid_columnconfigure(1, weight=1)

        fields = [
            ("Nombre *",        "nombre"),
            ("Apellido",        "apellido"),
            ("C.I.",            "ci"),
            ("Ciudad",          "ciudad"),
            ("Teléfono",        "telefono"),
            ("Correo",          "correo"),
            ("Cumpleaños",      "cumpleanos"),
        ]
        self._vars = {}
        for i, (label, key) in enumerate(fields):
            ctk.CTkLabel(container, text=label, anchor="w",
                         font=ctk.CTkFont(size=13)).grid(
                row=i, column=0, padx=(20, 8), pady=(10, 0), sticky="w")
            var = ctk.StringVar()
            entry = ctk.CTkEntry(container, textvariable=var, height=36)
            if key == "cumpleanos":
                entry.configure(placeholder_text="YYYY-MM-DD")
            entry.grid(row=i, column=1, padx=(0, 20), pady=(10, 0), sticky="ew")
            self._vars[key] = var

        ctk.CTkLabel(container, text="Notas", anchor="w",
                     font=ctk.CTkFont(size=13)).grid(
            row=len(fields), column=0, padx=(20, 8), pady=(10, 0), sticky="nw")
        self._notas = ctk.CTkTextbox(container, height=70)
        self._notas.grid(row=len(fields), column=1, padx=(0, 20), pady=(10, 0), sticky="ew")

        btn_frame = ctk.CTkFrame(container, fg_color="transparent")
        btn_frame.grid(row=len(fields) + 1, column=0, columnspan=2,
                       padx=20, pady=(14, 20), sticky="ew")
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(btn_frame, text="Guardar", height=40,
                      command=self._save).grid(
            row=0, column=0, padx=(0, 6), sticky="ew")
        ctk.CTkButton(btn_frame, text="Cancelar", height=40,
                      fg_color="transparent", border_width=1,
                      text_color=("gray10", "gray90"),
                      command=self._cancel).grid(
            row=0, column=1, padx=(6, 0), sticky="ew")

    def _cancel(self):
        self.grab_release()
        self.destroy()

    def _save(self):
        nombre = self._vars["nombre"].get().strip()
        if not nombre:
            messagebox.showwarning("Atención", "El nombre es obligatorio.", parent=self)
            return
        cid = cliente_model.create(
            nombre,
            apellido=self._vars["apellido"].get().strip(),
            ciudad=self._vars["ciudad"].get().strip(),
            telefono=self._vars["telefono"].get().strip(),
            notas=self._notas.get("1.0", "end").strip(),
            ci=self._vars["ci"].get().strip(),
            correo=self._vars["correo"].get().strip(),
            cumpleanos=self._vars["cumpleanos"].get().strip(),
        )
        self.result = cliente_model.get_by_id(cid)
        self.grab_release()
        self.destroy()


class CantidadDialog(ctk.CTkToplevel):
    """Small modal to enter a quantity."""

    def __init__(self, master, producto: dict):
        super().__init__(master)
        self.title("Agregar al carrito")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self._cancel)
        self.grab_set()
        self.result = None

        nombre = producto["nombre"]
        talle = producto.get("talle", "")
        color = producto.get("color", "")
        info = " · ".join(filter(None, [talle, color]))
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self, text=nombre,
                     font=ctk.CTkFont(size=14, weight="bold")).grid(
            row=0, column=0, padx=20, pady=(20, 4))
        if info:
            ctk.CTkLabel(self, text=info, text_color="gray60").grid(
                row=1, column=0, padx=20, pady=(0, 10))

        ctk.CTkLabel(self, text="Cantidad:").grid(row=2, column=0, padx=20, pady=4)
        self._qty_var = ctk.StringVar(value="1")
        ctk.CTkEntry(self, textvariable=self._qty_var, width=80,
                     justify="center").grid(row=3, column=0, pady=4)

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=4, column=0, padx=20, pady=16, sticky="ew")
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
        w, h = 320, 230
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    def _cancel(self):
        self.grab_release()
        self.destroy()

    def _confirm(self):
        try:
            qty = int(self._qty_var.get())
            if qty <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Error", "Ingresá una cantidad válida.", parent=self)
            return
        self.result = qty
        self.grab_release()
        self.destroy()


# ─────────────────────────────────────────────────────────────────────────────
# Main view
# ─────────────────────────────────────────────────────────────────────────────

class NuevaVentaView(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.cliente: dict | None = None
        self.carrito: list[dict] = []   # [{producto, cantidad}]
        self.forma_pago = ctk.StringVar(value="efectivo")
        self._search_after = None
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self._build_ui()

    # ── UI construction ──────────────────────────────────────────────────────

    def _build_ui(self):
        # Title
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, padx=24, pady=(20, 8), sticky="ew")
        ctk.CTkLabel(header, text="Nueva Venta",
                     font=ctk.CTkFont(size=24, weight="bold")).pack(side="left")

        # Client selector bar
        self._build_client_bar()

        # Main content: left = products, right = cart
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.grid(row=2, column=0, padx=24, pady=(0, 16), sticky="nsew")
        main.grid_columnconfigure(0, weight=3)
        main.grid_columnconfigure(1, weight=2)
        main.grid_rowconfigure(0, weight=1)
        self._build_product_panel(main)
        self._build_cart_panel(main)

    def _build_client_bar(self):
        bar = ctk.CTkFrame(self)
        bar.grid(row=1, column=0, padx=24, pady=(0, 8), sticky="ew")
        bar.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(bar, text="Cliente:", font=ctk.CTkFont(size=13)).grid(
            row=0, column=0, padx=14, pady=10)

        self._cliente_label = ctk.CTkLabel(
            bar, text="(ninguna seleccionada)",
            text_color="gray60", font=ctk.CTkFont(size=13)
        )
        self._cliente_label.grid(row=0, column=1, padx=8, pady=10, sticky="w")

        ctk.CTkButton(bar, text="Seleccionar cliente", width=160,
                      command=self._select_client).grid(
            row=0, column=2, padx=6, pady=8)
        ctk.CTkButton(bar, text="+ Nuevo cliente", width=140,
                      fg_color="#2d6a4f", hover_color="#1b4332",
                      command=self._new_client).grid(
            row=0, column=3, padx=6, pady=8)

    def _build_product_panel(self, parent):
        frame = ctk.CTkFrame(parent)
        frame.grid(row=0, column=0, padx=(0, 6), pady=0, sticky="nsew")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(3, weight=1)

        ctk.CTkLabel(frame, text="Catálogo de productos",
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
            placeholder_text="Escanear código de barras (Enter para agregar)...")
        self._scan_entry.grid(row=0, column=1, sticky="ew")
        self._scan_entry.bind("<Return>", lambda _: self._on_scan())

        # ── Text search ──
        search_frame = ctk.CTkFrame(frame, fg_color="transparent")
        search_frame.grid(row=2, column=0, padx=12, pady=(0, 6), sticky="ew")
        search_frame.grid_columnconfigure(0, weight=1)
        self._search_var = ctk.StringVar()
        ctk.CTkEntry(search_frame, textvariable=self._search_var,
                     placeholder_text="Buscar por nombre, marca, talle, color o código...").grid(
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
        self._cart_panel = frame

        ctk.CTkLabel(frame, text="Carrito",
                     font=ctk.CTkFont(size=15, weight="bold")).grid(
            row=0, column=0, padx=16, pady=(14, 6), sticky="w")

        self._cart_scroll = ctk.CTkScrollableFrame(frame)
        self._cart_scroll.grid(row=1, column=0, padx=12, pady=6, sticky="nsew")
        self._cart_scroll.grid_columnconfigure(0, weight=1)

        # ── Payment method ──
        pay = ctk.CTkFrame(frame, fg_color="transparent")
        pay.grid(row=2, column=0, padx=12, pady=4, sticky="ew")
        pay.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(pay, text="Forma de pago:").grid(
            row=0, column=0, sticky="w", pady=(4, 2))
        ctk.CTkSegmentedButton(
            pay,
            values=["efectivo", "transferencia", "mixto"],
            variable=self.forma_pago,
            command=self._on_forma_pago_change,
        ).grid(row=1, column=0, sticky="ew", pady=(0, 4))

        # ── Mixto breakdown (hidden by default) ──
        self._mixto_frame = ctk.CTkFrame(pay, fg_color="transparent")
        self._mixto_frame.grid(row=2, column=0, sticky="ew", pady=(2, 0))
        self._mixto_frame.grid_columnconfigure(1, weight=1)
        self._mixto_frame.grid_columnconfigure(3, weight=1)

        ctk.CTkLabel(self._mixto_frame, text="Efectivo $",
                     font=ctk.CTkFont(size=12)).grid(
            row=0, column=0, padx=(0, 4), pady=4, sticky="w")
        self._ef_var = ctk.StringVar(value="0")
        self._ef_entry = ctk.CTkEntry(
            self._mixto_frame, textvariable=self._ef_var, width=90)
        self._ef_entry.grid(row=0, column=1, padx=(0, 10), pady=4, sticky="ew")
        self._ef_var.trace_add("write", lambda *_: self._recalc_transferencia())

        ctk.CTkLabel(self._mixto_frame, text="Transferencia $",
                     font=ctk.CTkFont(size=12)).grid(
            row=0, column=2, padx=(0, 4), pady=4, sticky="w")
        self._tr_lbl = ctk.CTkLabel(
            self._mixto_frame, text="$0.00",
            font=ctk.CTkFont(size=12, weight="bold"))
        self._tr_lbl.grid(row=0, column=3, padx=4, pady=4, sticky="w")

        self._mixto_frame.grid_remove()  # oculto hasta que se elija "mixto"

        # ── Total ──
        self._total_lbl = ctk.CTkLabel(
            frame, text="Total: $0.00",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        self._total_lbl.grid(row=3, column=0, padx=16, pady=8)

        # ── Confirm ──
        ctk.CTkButton(
            frame, text="CONFIRMAR VENTA", height=46,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#e63946", hover_color="#c1121f",
            command=self._confirmar_venta
        ).grid(row=4, column=0, padx=12, pady=(0, 14), sticky="ew")

    # ── Refresh ──────────────────────────────────────────────────────────────

    def refresh(self, **kwargs):
        self.cliente = None
        self.carrito = []
        self.forma_pago.set("efectivo")
        self._mixto_frame.grid_remove()
        self._cliente_label.configure(text="(ninguna seleccionada)", text_color="gray60")
        self._scan_var.set("")
        self._search_var.set("")
        self._filter_products()
        self._render_cart()

    # ── Client actions ───────────────────────────────────────────────────────

    def _select_client(self):
        dlg = SelectClienteDialog(self)
        self.wait_window(dlg)
        if dlg.result:
            self.cliente = dlg.result
            nc = " ".join(filter(None, [dlg.result["nombre"], dlg.result.get("apellido", "")]))
            self._cliente_label.configure(
                text=f"{nc}  ({dlg.result['ciudad']})",
                text_color=("gray10", "gray90")
            )

    def _new_client(self):
        dlg = NuevaClienteDialog(self)
        self.wait_window(dlg)
        if dlg.result:
            self.cliente = dlg.result
            nc = " ".join(filter(None, [dlg.result["nombre"], dlg.result.get("apellido", "")]))
            self._cliente_label.configure(
                text=f"{nc}  ({dlg.result['ciudad']})",
                text_color=("gray10", "gray90")
            )

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
        if producto["stock"] <= 0:
            messagebox.showwarning(
                "Sin stock",
                f"'{producto['nombre']}' no tiene stock disponible.",
                parent=self)
            return
        # Agregar directamente 1 unidad al carrito
        for item in self.carrito:
            if item["producto"]["id"] == producto["id"]:
                if item["cantidad"] >= producto["stock"]:
                    messagebox.showwarning(
                        "Stock insuficiente",
                        f"Solo hay {producto['stock']} unidades disponibles.",
                        parent=self)
                    return
                item["cantidad"] += 1
                self._render_cart()
                return
        self.carrito.append({"producto": producto, "cantidad": 1})
        self._render_cart()

    # ── Product actions ──────────────────────────────────────────────────────

    def _filter_products(self):
        texto = self._search_var.get().strip()
        productos = (producto_model.search(texto, limit=80)
                     if texto else
                     producto_model.get_all(limit=80))
        for w in self._prod_scroll.winfo_children():
            w.destroy()
        if not productos:
            ctk.CTkLabel(self._prod_scroll, text="Sin resultados.",
                         text_color="gray60").pack(pady=16)
            return
        for p in productos:
            self._make_product_row(p)

    def _make_product_row(self, p: dict):
        row = ctk.CTkFrame(self._prod_scroll, corner_radius=8)
        row.pack(fill="x", pady=3)
        row.grid_columnconfigure(1, weight=1)

        # Stock badge
        stock = p["stock"]
        badge_color = "#e63946" if stock == 0 else "#2d6a4f"
        ctk.CTkLabel(row, text=f" {stock} ", fg_color=badge_color,
                     corner_radius=6, font=ctk.CTkFont(size=11)).grid(
            row=0, column=0, padx=(10, 8), pady=10)

        info_parts = [p["nombre"]]
        if p.get("talle"):
            info_parts.append(f"T:{p['talle']}")
        if p.get("color"):
            info_parts.append(p["color"])
        ctk.CTkLabel(row, text="  ".join(info_parts),
                     font=ctk.CTkFont(size=12), anchor="w").grid(
            row=0, column=1, pady=10, sticky="w")

        ctk.CTkLabel(row, text=f"${p['precio']:,.2f}",
                     font=ctk.CTkFont(size=12, weight="bold")).grid(
            row=0, column=2, padx=8, pady=10)

        add_btn = ctk.CTkButton(
            row, text="+", width=36, height=28,
            command=lambda prod=p: self._add_to_cart(prod),
            state="normal" if stock > 0 else "disabled"
        )
        add_btn.grid(row=0, column=3, padx=10, pady=8)

    def _add_to_cart(self, producto: dict):
        dlg = CantidadDialog(self, producto)
        self.wait_window(dlg)
        if not dlg.result:
            return
        qty = dlg.result
        if qty > producto["stock"]:
            messagebox.showwarning(
                "Stock insuficiente",
                f"Solo hay {producto['stock']} unidades disponibles.", parent=self)
            return
        # If already in cart, just increment
        for item in self.carrito:
            if item["producto"]["id"] == producto["id"]:
                item["cantidad"] += qty
                self._render_cart()
                return
        self.carrito.append({"producto": producto, "cantidad": qty})
        self._render_cart()

    # ── Cart rendering ───────────────────────────────────────────────────────

    def _render_cart(self):
        for w in self._cart_scroll.winfo_children():
            w.destroy()

        total = 0.0
        for idx, item in enumerate(self.carrito):
            p = item["producto"]
            qty = item["cantidad"]
            subtotal = qty * p["precio"]
            total += subtotal
            self._make_cart_row(idx, item)

        if not self.carrito:
            ctk.CTkLabel(self._cart_scroll, text="El carrito está vacío.",
                         text_color="gray60").pack(pady=20)

        self._total_lbl.configure(text=f"Total: ${total:,.2f}")

    def _make_cart_row(self, idx: int, item: dict):
        p = item["producto"]
        qty = item["cantidad"]
        subtotal = qty * p["precio"]

        row = ctk.CTkFrame(self._cart_scroll, corner_radius=8)
        row.pack(fill="x", pady=3)
        row.grid_columnconfigure(0, weight=1)

        name_parts = [p["nombre"]]
        if p.get("talle"):
            name_parts.append(f"T:{p['talle']}")
        ctk.CTkLabel(row, text=" · ".join(name_parts),
                     font=ctk.CTkFont(size=11, weight="bold"), anchor="w").grid(
            row=0, column=0, padx=10, pady=(8, 2), sticky="w")

        controls = ctk.CTkFrame(row, fg_color="transparent")
        controls.grid(row=1, column=0, padx=8, pady=(0, 8), sticky="ew")
        controls.grid_columnconfigure(2, weight=1)

        ctk.CTkButton(controls, text="−", width=28, height=24,
                      command=lambda i=idx: self._change_qty(i, -1)).grid(
            row=0, column=0, padx=2)
        ctk.CTkLabel(controls, text=str(qty), width=30,
                     anchor="center").grid(row=0, column=1, padx=4)
        ctk.CTkButton(controls, text="+", width=28, height=24,
                      command=lambda i=idx: self._change_qty(i, 1)).grid(
            row=0, column=2, padx=2, sticky="w")

        ctk.CTkLabel(controls,
                     text=f"${subtotal:,.2f}",
                     font=ctk.CTkFont(size=11, weight="bold")).grid(
            row=0, column=3, padx=8)

        ctk.CTkButton(controls, text="✕", width=28, height=24,
                      fg_color="#e63946", hover_color="#c1121f",
                      command=lambda i=idx: self._remove_item(i)).grid(
            row=0, column=4, padx=4)

    def _change_qty(self, idx: int, delta: int):
        item = self.carrito[idx]
        new_qty = item["cantidad"] + delta
        if new_qty <= 0:
            self._remove_item(idx)
            return
        max_stock = item["producto"]["stock"]
        if new_qty > max_stock:
            messagebox.showwarning("Stock insuficiente",
                                   f"Solo hay {max_stock} en stock.", parent=self)
            return
        item["cantidad"] = new_qty
        self._render_cart()

    def _remove_item(self, idx: int):
        self.carrito.pop(idx)
        self._render_cart()

    # ── Payment method ───────────────────────────────────────────────────────

    def _on_forma_pago_change(self, value: str):
        if value == "mixto":
            self._mixto_frame.grid()
            total = sum(it["cantidad"] * it["producto"]["precio"]
                        for it in self.carrito)
            self._ef_var.set(f"{total:.2f}")
            self._recalc_transferencia()
        else:
            self._mixto_frame.grid_remove()

    def _recalc_transferencia(self):
        total = sum(it["cantidad"] * it["producto"]["precio"]
                    for it in self.carrito)
        try:
            ef = float(self._ef_var.get().replace(",", "."))
            tr = total - ef
            self._tr_lbl.configure(
                text=f"${tr:,.2f}",
                text_color="gray60" if tr < 0 else ("gray10", "gray90"),
            )
        except ValueError:
            self._tr_lbl.configure(text="—", text_color="gray60")

    # ── Confirm sale ─────────────────────────────────────────────────────────

    def _confirmar_venta(self):
        if not self.cliente:
            messagebox.showwarning("Atención", "Seleccioná un cliente.", parent=self)
            return
        if not self.carrito:
            messagebox.showwarning("Atención", "El carrito está vacío.", parent=self)
            return

        items = [
            {
                "producto_id":     it["producto"]["id"],
                "cantidad":        it["cantidad"],
                "precio_unitario": it["producto"]["precio"],
            }
            for it in self.carrito
        ]
        total = sum(i["cantidad"] * i["precio_unitario"] for i in items)
        forma = self.forma_pago.get()

        # Calcular montos según forma de pago
        monto_ef = 0.0
        monto_tr = 0.0
        if forma == "mixto":
            try:
                monto_ef = float(self._ef_var.get().replace(",", "."))
                monto_tr = round(total - monto_ef, 2)
            except ValueError:
                messagebox.showwarning(
                    "Error", "Ingresá un monto válido en efectivo.", parent=self)
                return
            if monto_ef < 0 or monto_tr < 0:
                messagebox.showwarning(
                    "Error",
                    f"Los montos no pueden ser negativos.\n"
                    f"Efectivo: ${monto_ef:,.2f}  |  Transferencia: ${monto_tr:,.2f}",
                    parent=self)
                return
            detalle_pago = (
                f"Forma de pago: mixto\n"
                f"  · Efectivo:       ${monto_ef:,.2f}\n"
                f"  · Transferencia:  ${monto_tr:,.2f}"
            )
        else:
            detalle_pago = f"Forma de pago: {forma}"

        confirm = messagebox.askyesno(
            "Confirmar venta",
            f"Cliente: {' '.join(filter(None, [self.cliente['nombre'], self.cliente.get('apellido', '')]))}\n"
            f"{detalle_pago}\n"
            f"Total: ${total:,.2f}\n\n¿Confirmar?",
            parent=self
        )
        if not confirm:
            return

        venta_model.create(
            cliente_id=self.cliente["id"],
            fecha=date.today().isoformat(),
            forma_pago=forma,
            items=items,
            monto_efectivo=monto_ef,
            monto_transferencia=monto_tr,
        )
        messagebox.showinfo("Listo", "Venta registrada correctamente.", parent=self)
        self.refresh()
