from __future__ import annotations
from datetime import date
from tkinter import messagebox
import customtkinter as ctk

import models.gasto as gasto_model
import models.categoria_gasto as cat_gasto_model


def _today() -> str:
    return date.today().isoformat()

def _first_of_month() -> str:
    today = date.today()
    return today.replace(day=1).isoformat()


# ─────────────────────────────────────────────────────────────────────────────
# Gasto form dialog
# ─────────────────────────────────────────────────────────────────────────────

class GastoFormDialog(ctk.CTkToplevel):
    def __init__(self, master, gasto: dict | None = None, on_done=None):
        super().__init__(master)
        self.gasto = gasto
        self.on_done = on_done
        self.title("Editar gasto" if gasto else "Nuevo gasto")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self._cancel)
        self.grab_set()
        self._categorias: list[dict] = []
        self._build_ui()
        if gasto:
            self._fill(gasto)
        self.update_idletasks()
        w, h = 460, 560
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        container = ctk.CTkFrame(self, fg_color="transparent")
        container.grid(row=0, column=0, sticky="nsew")
        container.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(container, text="Fecha *", anchor="w",
                     font=ctk.CTkFont(size=13)).grid(
            row=0, column=0, padx=(20, 8), pady=(12, 0), sticky="w")
        self._fecha_var = ctk.StringVar(value=_today())
        ctk.CTkEntry(container, textvariable=self._fecha_var, height=36).grid(
            row=0, column=1, padx=(0, 20), pady=(12, 0), sticky="ew")

        ctk.CTkLabel(container, text="Categoría *", anchor="w",
                     font=ctk.CTkFont(size=13)).grid(
            row=1, column=0, padx=(20, 8), pady=(10, 0), sticky="w")
        self._categorias = cat_gasto_model.get_all(activos_only=True)
        cat_nombres = [c["nombre"] for c in self._categorias]
        self._cat_var = ctk.StringVar(value=cat_nombres[0] if cat_nombres else "")
        self._cat_combo = ctk.CTkComboBox(container, values=cat_nombres,
                                          variable=self._cat_var, height=36)
        self._cat_combo.grid(row=1, column=1, padx=(0, 20), pady=(10, 0), sticky="ew")

        ctk.CTkLabel(container, text="Descripción *", anchor="w",
                     font=ctk.CTkFont(size=13)).grid(
            row=2, column=0, padx=(20, 8), pady=(10, 0), sticky="w")
        self._desc_var = ctk.StringVar()
        ctk.CTkEntry(container, textvariable=self._desc_var, height=36).grid(
            row=2, column=1, padx=(0, 20), pady=(10, 0), sticky="ew")

        ctk.CTkLabel(container, text="Monto *", anchor="w",
                     font=ctk.CTkFont(size=13)).grid(
            row=3, column=0, padx=(20, 8), pady=(10, 0), sticky="w")
        self._monto_var = ctk.StringVar()
        ctk.CTkEntry(container, textvariable=self._monto_var, height=36).grid(
            row=3, column=1, padx=(0, 20), pady=(10, 0), sticky="ew")

        ctk.CTkLabel(container, text="Proveedor", anchor="w",
                     font=ctk.CTkFont(size=13)).grid(
            row=4, column=0, padx=(20, 8), pady=(10, 0), sticky="w")
        self._proveedor_var = ctk.StringVar()
        ctk.CTkEntry(container, textvariable=self._proveedor_var, height=36).grid(
            row=4, column=1, padx=(0, 20), pady=(10, 0), sticky="ew")

        ctk.CTkLabel(container, text="N° Comprobante", anchor="w",
                     font=ctk.CTkFont(size=13)).grid(
            row=5, column=0, padx=(20, 8), pady=(10, 0), sticky="w")
        self._nro_comp_var = ctk.StringVar()
        ctk.CTkEntry(container, textvariable=self._nro_comp_var, height=36).grid(
            row=5, column=1, padx=(0, 20), pady=(10, 0), sticky="ew")

        ctk.CTkLabel(container, text="Forma de pago", anchor="w",
                     font=ctk.CTkFont(size=13)).grid(
            row=6, column=0, padx=(20, 8), pady=(10, 0), sticky="w")
        self._forma_pago_var = ctk.StringVar()
        ctk.CTkComboBox(container, values=["", "efectivo", "transferencia",
                                           "tarjeta", "cheque", "cuenta corriente"],
                        variable=self._forma_pago_var, height=36).grid(
            row=6, column=1, padx=(0, 20), pady=(10, 0), sticky="ew")

        self._pagado_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(container, text="Pagado", variable=self._pagado_var).grid(
            row=7, column=0, columnspan=2, padx=20, pady=(12, 0), sticky="w")

        btn_frame = ctk.CTkFrame(container, fg_color="transparent")
        btn_frame.grid(row=8, column=0, columnspan=2, padx=20, pady=(16, 20), sticky="ew")
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

    def _fill(self, g: dict):
        self._fecha_var.set(g["fecha"])
        self._desc_var.set(g["descripcion"])
        self._monto_var.set(str(g["monto"]))
        self._pagado_var.set(bool(g["pagado"]))
        self._proveedor_var.set(g.get("proveedor", ""))
        self._nro_comp_var.set(g.get("numero_comprobante", ""))
        self._forma_pago_var.set(g.get("forma_pago", ""))
        cat_nombre = g.get("categoria_nombre", "")
        if cat_nombre:
            self._cat_var.set(cat_nombre)

    def _save(self):
        fecha = self._fecha_var.get().strip()
        desc  = self._desc_var.get().strip()
        if not fecha or not desc:
            messagebox.showwarning("Atención", "Fecha y descripción son obligatorias.",
                                   parent=self)
            return
        try:
            monto = float(self._monto_var.get().replace(",", "."))
        except ValueError:
            messagebox.showwarning("Atención", "El monto debe ser un número.", parent=self)
            return
        cat_nombre = self._cat_var.get()
        cat = next((c for c in self._categorias if c["nombre"] == cat_nombre), None)
        if not cat:
            messagebox.showwarning("Atención", "Seleccioná una categoría.", parent=self)
            return
        pagado = self._pagado_var.get()

        proveedor   = self._proveedor_var.get().strip()
        nro_comp    = self._nro_comp_var.get().strip()
        forma_pago  = self._forma_pago_var.get().strip()

        if self.gasto:
            gasto_model.update(self.gasto["id"], fecha, cat["id"], desc, monto, pagado,
                               proveedor=proveedor, numero_comprobante=nro_comp,
                               forma_pago=forma_pago)
        else:
            gasto_model.create(fecha, cat["id"], desc, monto, pagado,
                               proveedor=proveedor, numero_comprobante=nro_comp,
                               forma_pago=forma_pago)

        if self.on_done:
            self.on_done()
        self.grab_release()
        self.destroy()

    def _cancel(self):
        self.grab_release()
        self.destroy()


# ─────────────────────────────────────────────────────────────────────────────
# Categorías management dialog
# ─────────────────────────────────────────────────────────────────────────────

class CategoriasGastoDialog(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Categorías de Gasto")
        self.protocol("WM_DELETE_WINDOW", self._close)
        self.grab_set()
        self._build_ui()
        self._load()
        self.update_idletasks()
        w, h = 380, 440
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    def _close(self):
        self.grab_release()
        self.destroy()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        top = ctk.CTkFrame(self, fg_color="transparent")
        top.grid(row=0, column=0, padx=16, pady=(16, 8), sticky="ew")
        top.grid_columnconfigure(0, weight=1)

        self._nueva_var = ctk.StringVar()
        ctk.CTkEntry(top, textvariable=self._nueva_var,
                     placeholder_text="Nueva categoría...").grid(
            row=0, column=0, padx=(0, 8), sticky="ew")
        ctk.CTkButton(top, text="Agregar", width=90,
                      command=self._agregar).grid(row=0, column=1)

        self._scroll = ctk.CTkScrollableFrame(self)
        self._scroll.grid(row=1, column=0, padx=16, pady=(0, 16), sticky="nsew")
        self._scroll.grid_columnconfigure(0, weight=1)

    def _load(self):
        for w in self._scroll.winfo_children():
            w.destroy()
        for c in cat_gasto_model.get_all(activos_only=False):
            self._make_row(c)

    def _make_row(self, c: dict):
        row = ctk.CTkFrame(self._scroll, corner_radius=6)
        row.pack(fill="x", pady=2)
        row.grid_columnconfigure(0, weight=1)

        color = "gray60" if not c["activo"] else ("gray10", "gray90")
        ctk.CTkLabel(row, text=c["nombre"],
                     text_color=color, anchor="w").grid(
            row=0, column=0, padx=12, pady=8, sticky="w")

        btn_text = "Activar" if not c["activo"] else "Desactivar"
        ctk.CTkButton(
            row, text=btn_text, width=90,
            fg_color="transparent", border_width=1,
            text_color=("gray10", "gray90"),
            command=lambda cid=c["id"]: self._toggle(cid)
        ).grid(row=0, column=1, padx=8, pady=6)

    def _agregar(self):
        nombre = self._nueva_var.get().strip()
        if not nombre:
            return
        try:
            cat_gasto_model.create(nombre)
        except Exception:
            messagebox.showwarning("Error",
                                   "Ya existe una categoría con ese nombre.",
                                   parent=self)
            return
        self._nueva_var.set("")
        self._load()

    def _toggle(self, cat_id: int):
        cat_gasto_model.toggle_activo(cat_id)
        self._load()


# ─────────────────────────────────────────────────────────────────────────────
# Main view
# ─────────────────────────────────────────────────────────────────────────────

class GastosView(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self._build_ui()

    def _build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, padx=24, pady=(20, 8), sticky="ew")
        header.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(header, text="💸  Gastos del Local",
                     font=ctk.CTkFont(size=22, weight="bold")).grid(
            row=0, column=0, sticky="w")

        btn_frame = ctk.CTkFrame(header, fg_color="transparent")
        btn_frame.grid(row=0, column=2)
        ctk.CTkButton(btn_frame, text="Categorías", width=110,
                      fg_color="transparent", border_width=1,
                      text_color=("gray10", "gray90"),
                      command=self._open_categorias).pack(side="left", padx=(0, 8))
        ctk.CTkButton(btn_frame, text="+ Nuevo gasto",
                      command=self._nuevo_gasto).pack(side="left")

        # Filters
        filters = ctk.CTkFrame(self, fg_color="transparent")
        filters.grid(row=1, column=0, padx=24, pady=(0, 8), sticky="ew")

        ctk.CTkLabel(filters, text="Desde:").pack(side="left", padx=(0, 4))
        self._desde_var = ctk.StringVar(value=_first_of_month())
        ctk.CTkEntry(filters, textvariable=self._desde_var, width=120).pack(
            side="left", padx=(0, 12))

        ctk.CTkLabel(filters, text="Hasta:").pack(side="left", padx=(0, 4))
        self._hasta_var = ctk.StringVar(value=_today())
        ctk.CTkEntry(filters, textvariable=self._hasta_var, width=120).pack(
            side="left", padx=(0, 12))

        self._cat_filter_var = ctk.StringVar(value="(Todas)")
        self._cat_filter_combo = ctk.CTkComboBox(
            filters, values=["(Todas)"], variable=self._cat_filter_var,
            width=140, command=lambda _: self._load()
        )
        self._cat_filter_combo.pack(side="left", padx=(0, 8))

        self._pagado_filter_var = ctk.StringVar(value="todos")
        ctk.CTkComboBox(
            filters, values=["todos", "pagado", "pendiente"],
            variable=self._pagado_filter_var, width=110,
            command=lambda _: self._load()
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(filters, text="Filtrar", width=80,
                      command=self._load).pack(side="left")

        # Content (list + summary)
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.grid(row=2, column=0, padx=24, pady=(0, 20), sticky="nsew")
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(0, weight=1)

        self._scroll = ctk.CTkScrollableFrame(content)
        self._scroll.grid(row=0, column=0, sticky="nsew")
        self._scroll.grid_columnconfigure(0, weight=1)

        # Summary frame
        self._summary_frame = ctk.CTkFrame(content, corner_radius=8)
        self._summary_frame.grid(row=1, column=0, pady=(8, 0), sticky="ew")
        self._summary_label = ctk.CTkLabel(
            self._summary_frame, text="",
            font=ctk.CTkFont(size=12), text_color="gray60"
        )
        self._summary_label.pack(padx=12, pady=8, anchor="w")

    def refresh(self, **kwargs):
        self._update_cat_combo()
        self._load()

    def _update_cat_combo(self):
        cats = cat_gasto_model.get_all(activos_only=False)
        valores = ["(Todas)"] + [c["nombre"] for c in cats]
        self._cat_filter_combo.configure(values=valores)

    def _load(self):
        desde = self._desde_var.get().strip() or _first_of_month()
        hasta = self._hasta_var.get().strip() or _today()
        gastos = gasto_model.get_by_range(desde, hasta)

        cat_f = self._cat_filter_var.get()
        if cat_f and cat_f != "(Todas)":
            gastos = [g for g in gastos if g.get("categoria_nombre") == cat_f]

        pago_f = self._pagado_filter_var.get()
        if pago_f == "pagado":
            gastos = [g for g in gastos if g.get("pagado")]
        elif pago_f == "pendiente":
            gastos = [g for g in gastos if not g.get("pagado")]

        for w in self._scroll.winfo_children():
            w.destroy()

        if not gastos:
            ctk.CTkLabel(self._scroll, text="No hay gastos en el período.",
                         text_color="gray60").pack(pady=20)
        else:
            for g in gastos:
                self._make_row(g)

        # Summary
        total = sum(g["monto"] for g in gastos)
        totales = gasto_model.get_totales_by_range(desde, hasta)
        if cat_f and cat_f != "(Todas)":
            totales = [t for t in totales if t["categoria"] == cat_f]
        summary_parts = [f"Total: ${total:,.2f}"]
        for t in totales:
            summary_parts.append(f"{t['categoria']}: ${t['total']:,.2f}")
        self._summary_label.configure(text="   |   ".join(summary_parts))

    def _make_row(self, g: dict):
        row = ctk.CTkFrame(self._scroll, corner_radius=8)
        row.pack(fill="x", pady=2)
        row.grid_columnconfigure(2, weight=1)

        ctk.CTkLabel(row, text=g.get("fecha", ""),
                     font=ctk.CTkFont(size=11), text_color="gray60", width=90).grid(
            row=0, column=0, padx=(12, 4), pady=10)

        ctk.CTkLabel(row, text=f"  {g.get('categoria_nombre', '')}  ",
                     fg_color="#1d3557", corner_radius=6,
                     font=ctk.CTkFont(size=10)).grid(
            row=0, column=1, padx=4, pady=10)

        desc_parts = [g.get("descripcion", "")]
        if g.get("proveedor"):
            desc_parts.append(f"[{g['proveedor']}]")
        if g.get("forma_pago"):
            desc_parts.append(g["forma_pago"])
        ctk.CTkLabel(row, text="  ".join(desc_parts),
                     anchor="w", font=ctk.CTkFont(size=12)).grid(
            row=0, column=2, padx=8, pady=10, sticky="w")

        ctk.CTkLabel(row, text=f"${g['monto']:,.2f}",
                     font=ctk.CTkFont(size=13, weight="bold")).grid(
            row=0, column=3, padx=8, pady=10)

        pagado = g.get("pagado")
        badge_color = "#2d6a4f" if pagado else "#f4a261"
        badge_text  = "pagado" if pagado else "pendiente"
        ctk.CTkLabel(row, text=f"  {badge_text}  ",
                     fg_color=badge_color, corner_radius=6,
                     font=ctk.CTkFont(size=10)).grid(
            row=0, column=4, padx=4, pady=10)

        ctk.CTkButton(row, text="Editar", width=70,
                      command=lambda gid=g["id"]: self._editar(gid)).grid(
            row=0, column=5, padx=4, pady=8)

        ctk.CTkButton(row, text="X", width=36,
                      fg_color="#e63946", hover_color="#c1121f",
                      command=lambda gid=g["id"]: self._eliminar(gid)).grid(
            row=0, column=6, padx=(0, 8), pady=8)

    def _nuevo_gasto(self):
        dlg = GastoFormDialog(self, on_done=self._load)
        self.wait_window(dlg)

    def _editar(self, gasto_id: int):
        import models.gasto as gm
        # Re-fetch single record
        gastos = gm.get_all()
        g = next((x for x in gastos if x["id"] == gasto_id), None)
        if not g:
            return
        dlg = GastoFormDialog(self, gasto=g, on_done=self._load)
        self.wait_window(dlg)

    def _eliminar(self, gasto_id: int):
        if not messagebox.askyesno("Confirmar", "¿Eliminar este gasto?"):
            return
        gasto_model.delete(gasto_id)
        self._load()

    def _open_categorias(self):
        dlg = CategoriasGastoDialog(self)
        self.wait_window(dlg)
        self._update_cat_combo()
