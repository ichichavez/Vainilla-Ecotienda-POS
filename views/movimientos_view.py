from __future__ import annotations
from datetime import date
from tkinter import messagebox
import customtkinter as ctk

import models.movimiento_stock as mov_model
import models.producto as producto_model
from utils.ui import debounce


def _today() -> str:
    return date.today().isoformat()

def _first_of_month() -> str:
    today = date.today()
    return today.replace(day=1).isoformat()


TIPO_COLORS = {
    "venta":      "#e63946",
    "compra":     "#2d6a4f",
    "ajuste":     "#f4a261",
    "devolucion": "#4fc3f7",
    "cambio": "#e9c46a",
}


# ─────────────────────────────────────────────────────────────────────────────
# Ajuste manual dialog
# ─────────────────────────────────────────────────────────────────────────────

class AjusteDialog(ctk.CTkToplevel):
    def __init__(self, master, on_done=None):
        super().__init__(master)
        self.title("Ajuste manual de stock")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self._cancel)
        self.grab_set()
        self.on_done = on_done
        self._productos: list[dict] = []
        self._build_ui()
        self.update_idletasks()
        w, h = 480, 420
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        container = ctk.CTkFrame(self, fg_color="transparent")
        container.grid(row=0, column=0, sticky="nsew")
        container.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(container, text="Buscar producto *", anchor="w",
                     font=ctk.CTkFont(size=13)).grid(
            row=0, column=0, padx=(20, 8), pady=(16, 0), sticky="w")
        self._search_var = ctk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._search_productos())
        ctk.CTkEntry(container, textvariable=self._search_var,
                     placeholder_text="Nombre, talle o color...", height=36).grid(
            row=0, column=1, padx=(0, 20), pady=(16, 0), sticky="ew")

        self._prod_combo = ctk.CTkComboBox(container, values=[], state="readonly",
                                           height=36)
        self._prod_combo.grid(row=1, column=0, columnspan=2,
                              padx=20, pady=(6, 0), sticky="ew")

        ctk.CTkLabel(container, text="Cantidad *\n(+ entrada / - salida)", anchor="w",
                     font=ctk.CTkFont(size=13)).grid(
            row=2, column=0, padx=(20, 8), pady=(10, 0), sticky="w")
        self._cant_var = ctk.StringVar(value="1")
        ctk.CTkEntry(container, textvariable=self._cant_var, height=36).grid(
            row=2, column=1, padx=(0, 20), pady=(10, 0), sticky="ew")

        ctk.CTkLabel(container, text="Fecha *", anchor="w",
                     font=ctk.CTkFont(size=13)).grid(
            row=3, column=0, padx=(20, 8), pady=(10, 0), sticky="w")
        self._fecha_var = ctk.StringVar(value=_today())
        ctk.CTkEntry(container, textvariable=self._fecha_var, height=36).grid(
            row=3, column=1, padx=(0, 20), pady=(10, 0), sticky="ew")

        ctk.CTkLabel(container, text="Notas", anchor="w",
                     font=ctk.CTkFont(size=13)).grid(
            row=4, column=0, padx=(20, 8), pady=(10, 0), sticky="nw")
        self._notas = ctk.CTkTextbox(container, height=70)
        self._notas.grid(row=4, column=1, padx=(0, 20), pady=(10, 0), sticky="ew")

        btn_frame = ctk.CTkFrame(container, fg_color="transparent")
        btn_frame.grid(row=5, column=0, columnspan=2, padx=20, pady=(16, 20), sticky="ew")
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkButton(btn_frame, text="Guardar ajuste", height=40,
                      command=self._save).grid(
            row=0, column=0, padx=(0, 6), sticky="ew")
        ctk.CTkButton(btn_frame, text="Cancelar", height=40,
                      fg_color="transparent", border_width=1,
                      text_color=("gray10", "gray90"),
                      command=self._cancel).grid(
            row=0, column=1, padx=(6, 0), sticky="ew")

    def _search_productos(self):
        texto = self._search_var.get().strip()
        if texto:
            self._productos = producto_model.search(texto, activos_only=True)
        else:
            self._productos = producto_model.get_all(activos_only=True)[:50]
        labels = [
            f"{p['nombre']}"
            + (f" T:{p['talle']}" if p.get("talle") else "")
            + (f" {p['color']}" if p.get("color") else "")
            + f" (stock:{p['stock']})"
            for p in self._productos
        ]
        self._prod_combo.configure(values=labels)
        if labels:
            self._prod_combo.set(labels[0])

    def _save(self):
        sel = self._prod_combo.get()
        if not sel or not self._productos:
            messagebox.showwarning("Atención", "Seleccioná un producto.", parent=self)
            return
        idx = self._prod_combo.cget("values").index(sel) if sel in self._prod_combo.cget("values") else -1
        if idx < 0 or idx >= len(self._productos):
            messagebox.showwarning("Atención", "Seleccioná un producto válido.", parent=self)
            return
        prod = self._productos[idx]
        try:
            cantidad = int(self._cant_var.get())
        except ValueError:
            messagebox.showwarning("Atención", "La cantidad debe ser un entero.", parent=self)
            return
        if cantidad == 0:
            messagebox.showwarning("Atención", "La cantidad no puede ser 0.", parent=self)
            return
        fecha = self._fecha_var.get().strip()
        if not fecha:
            messagebox.showwarning("Atención", "Ingresá una fecha.", parent=self)
            return
        notas = self._notas.get("1.0", "end").strip()

        # Update stock
        import database
        conn = database.get_connection()
        try:
            with conn:
                conn.execute(
                    "UPDATE productos SET stock = stock + ? WHERE id=?",
                    (cantidad, prod["id"])
                )
        finally:
            conn.close()

        mov_model.log(prod["id"], "ajuste", cantidad, fecha, notas=notas)

        messagebox.showinfo("Listo", "Ajuste registrado.", parent=self)
        if self.on_done:
            self.on_done()
        self.grab_release()
        self.destroy()

    def _cancel(self):
        self.grab_release()
        self.destroy()


# ─────────────────────────────────────────────────────────────────────────────
# Main view
# ─────────────────────────────────────────────────────────────────────────────

class MovimientosView(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self._search_after = None
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self._build_ui()

    def _build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, padx=24, pady=(20, 8), sticky="ew")
        header.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(header, text="📋  Movimientos de Stock",
                     font=ctk.CTkFont(size=22, weight="bold")).grid(
            row=0, column=0, sticky="w")
        ctk.CTkButton(header, text="+ Ajuste manual",
                      command=self._nuevo_ajuste).grid(row=0, column=2)

        # Filters
        filters = ctk.CTkFrame(self, fg_color="transparent")
        filters.grid(row=1, column=0, padx=24, pady=(0, 8), sticky="ew")
        filters.grid_columnconfigure(0, weight=1)

        row1 = ctk.CTkFrame(filters, fg_color="transparent")
        row1.grid(row=0, column=0, sticky="ew")
        row1.grid_columnconfigure(0, weight=1)

        self._search_var = ctk.StringVar()
        ctk.CTkEntry(row1, textvariable=self._search_var,
                     placeholder_text="Buscar producto...").grid(
            row=0, column=0, padx=(0, 8), sticky="ew")
        self._search_var.trace_add(
            "write",
            lambda *_: debounce(self, "_search_after", 250, self._load),
        )

        self._tipo_var = ctk.StringVar(value="todos")
        ctk.CTkComboBox(
            row1, values=["todos", "venta", "compra", "ajuste", "devolucion", "cambio"],
            variable=self._tipo_var, width=130,
            command=lambda _: self._load()
        ).grid(row=0, column=1, padx=(0, 8))

        row2 = ctk.CTkFrame(filters, fg_color="transparent")
        row2.grid(row=1, column=0, pady=(6, 0), sticky="w")

        ctk.CTkLabel(row2, text="Desde:").pack(side="left", padx=(0, 4))
        self._desde_var = ctk.StringVar(value=_first_of_month())
        ctk.CTkEntry(row2, textvariable=self._desde_var, width=120).pack(side="left", padx=(0, 12))

        ctk.CTkLabel(row2, text="Hasta:").pack(side="left", padx=(0, 4))
        self._hasta_var = ctk.StringVar(value=_today())
        ctk.CTkEntry(row2, textvariable=self._hasta_var, width=120).pack(side="left", padx=(0, 12))

        ctk.CTkButton(row2, text="Filtrar", width=80,
                      command=self._load).pack(side="left")

        # Scrollable list
        self._scroll = ctk.CTkScrollableFrame(self)
        self._scroll.grid(row=2, column=0, padx=24, pady=(0, 20), sticky="nsew")
        self._scroll.grid_columnconfigure(0, weight=1)

    def refresh(self, **kwargs):
        self._load()

    def _load(self):
        desde = self._desde_var.get().strip() or _first_of_month()
        hasta = self._hasta_var.get().strip() or _today()
        movs = mov_model.get_by_range(desde, hasta)

        texto = self._search_var.get().strip().lower()
        if texto:
            movs = [m for m in movs
                    if texto in (m.get("producto_nombre") or "").lower()]

        tipo = self._tipo_var.get()
        if tipo != "todos":
            movs = [m for m in movs if m.get("tipo") == tipo]

        for w in self._scroll.winfo_children():
            w.destroy()

        if not movs:
            ctk.CTkLabel(self._scroll, text="No hay movimientos.",
                         text_color="gray60").pack(pady=20)
            return

        for m in movs:
            self._make_row(m)

    def _make_row(self, m: dict):
        row = ctk.CTkFrame(self._scroll, corner_radius=8)
        row.pack(fill="x", pady=2)
        row.grid_columnconfigure(1, weight=1)

        tipo = m.get("tipo", "")
        badge_color = TIPO_COLORS.get(tipo, "gray40")
        ctk.CTkLabel(row, text=f"  {tipo}  ",
                     fg_color=badge_color, corner_radius=6,
                     font=ctk.CTkFont(size=11, weight="bold"), width=80).grid(
            row=0, column=0, padx=(12, 8), pady=10)

        ctk.CTkLabel(row, text=m.get("producto_nombre", ""),
                     font=ctk.CTkFont(size=12, weight="bold"), anchor="w").grid(
            row=0, column=1, padx=4, pady=10, sticky="w")

        cant = m.get("cantidad", 0)
        cant_color = "#2d6a4f" if cant > 0 else "#e63946"
        ctk.CTkLabel(row, text=f"{'+' if cant > 0 else ''}{cant}",
                     text_color=cant_color,
                     font=ctk.CTkFont(size=13, weight="bold"), width=50).grid(
            row=0, column=2, padx=8, pady=10)

        ctk.CTkLabel(row, text=m.get("fecha", ""),
                     text_color="gray60", font=ctk.CTkFont(size=11), width=90).grid(
            row=0, column=3, padx=8, pady=10)

        ref = m.get("referencia_id")
        ref_text = f"ref#{ref}" if ref else ""
        notas = m.get("notas", "") or ""
        extra = "  ".join(filter(None, [ref_text, notas]))
        if extra:
            ctk.CTkLabel(row, text=extra,
                         text_color="gray50", font=ctk.CTkFont(size=10)).grid(
                row=0, column=4, padx=(0, 12), pady=10)

    def _after_ajuste(self):
        self.app.mark_data_changed(
            "productos", "catalogo", "etiquetas", "reportes", "dashboard",
        )
        self._load()

    def _nuevo_ajuste(self):
        dlg = AjusteDialog(self, on_done=self._after_ajuste)
        self.wait_window(dlg)
