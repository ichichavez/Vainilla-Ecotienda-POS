from __future__ import annotations
import customtkinter as ctk
from datetime import date
from tkinter import messagebox
import webbrowser
from urllib.parse import quote

import models.cliente as cliente_model
import models.venta as venta_model
import models.despacho as despacho_model
import models.cambio as cambio_model
import models.producto as producto_model
import models.plantilla_mensaje as plantilla_model
import models.mensaje_whatsapp as wa_model
from utils.ui import debounce
from utils.money import money


# ─────────────────────────────────────────────────────────────────────────────
# Dispatch dialog
# ─────────────────────────────────────────────────────────────────────────────

class DespachoDialog(ctk.CTkToplevel):
    def __init__(self, master, cliente_id: int, prendas: list[dict],
                 on_done=None):
        super().__init__(master)
        self.title("Despachar prendas")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self._cancel)
        self.grab_set()
        self.cliente_id = cliente_id
        self.prendas = prendas
        self.on_done = on_done
        self._checks: dict[int, ctk.BooleanVar] = {}
        self._build_ui()
        self.update_idletasks()
        w, h = 560, 620
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    def _cancel(self):
        self.grab_release()
        self.destroy()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(self, text="Seleccioná las prendas a despachar",
                     font=ctk.CTkFont(size=15, weight="bold")).grid(
            row=0, column=0, padx=20, pady=(20, 10), sticky="w")

        # Items
        scroll = ctk.CTkScrollableFrame(self, height=180)
        scroll.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="nsew")
        scroll.grid_columnconfigure(0, weight=1)

        for p in self.prendas:
            var = ctk.BooleanVar(value=True)
            self._checks[p["id"]] = var
            parts = [p["nombre"]]
            if p.get("talle"):
                parts.append(f"T:{p['talle']}")
            if p.get("color"):
                parts.append(p["color"])
            label = f"  {' · '.join(parts)}  (x{p['cantidad']})  — Gs. {p['precio_unitario'] * p['cantidad']:,.2f}"
            ctk.CTkCheckBox(scroll, text=label, variable=var).pack(
                anchor="w", pady=3)

        # Form
        form = ctk.CTkFrame(self)
        form.grid(row=2, column=0, padx=20, pady=(0, 10), sticky="ew")
        form.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(form, text="Tipo:").grid(row=0, column=0, padx=12, pady=8, sticky="w")
        self._tipo_var = ctk.StringVar(value="envio")
        ctk.CTkSegmentedButton(form, values=["envio", "retiro"],
                               variable=self._tipo_var).grid(
            row=0, column=1, padx=12, pady=8, sticky="ew")

        ctk.CTkLabel(form, text="Fecha:").grid(row=1, column=0, padx=12, pady=8, sticky="w")
        self._fecha_var = ctk.StringVar(value=date.today().isoformat())
        ctk.CTkEntry(form, textvariable=self._fecha_var).grid(
            row=1, column=1, padx=12, pady=8, sticky="ew")

        ctk.CTkLabel(form, text="Dirección envío:").grid(row=2, column=0, padx=12, pady=8, sticky="w")
        self._dir_var = ctk.StringVar()
        ctk.CTkEntry(form, textvariable=self._dir_var,
                     placeholder_text="Opcional").grid(
            row=2, column=1, padx=12, pady=8, sticky="ew")

        ctk.CTkLabel(form, text="Costo envío:").grid(row=3, column=0, padx=12, pady=8, sticky="w")
        self._costo_var = ctk.StringVar(value="0")
        ctk.CTkEntry(form, textvariable=self._costo_var, width=100).grid(
            row=3, column=1, padx=12, pady=8, sticky="w")

        ctk.CTkLabel(form, text="Notas:").grid(row=4, column=0, padx=12, pady=8, sticky="nw")
        self._notas = ctk.CTkTextbox(form, height=60)
        self._notas.grid(row=4, column=1, padx=12, pady=8, sticky="ew")

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=3, column=0, padx=20, pady=(0, 16), sticky="ew")
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkButton(btn_frame, text="Confirmar despacho", height=42,
                      command=self._confirmar).grid(
            row=0, column=0, padx=(0, 6), sticky="ew")
        ctk.CTkButton(btn_frame, text="Cancelar", height=42,
                      fg_color="transparent", border_width=1,
                      text_color=("gray10", "gray90"),
                      command=self._cancel).grid(
            row=0, column=1, padx=(6, 0), sticky="ew")

    def _confirmar(self):
        selected_ids = [iv_id for iv_id, var in self._checks.items() if var.get()]
        if not selected_ids:
            messagebox.showwarning("Atención",
                                   "Seleccioná al menos una prenda.", parent=self)
            return
        try:
            costo_envio = float(self._costo_var.get().replace(",", ".") or "0")
        except ValueError:
            costo_envio = 0.0
        despacho_model.create(
            cliente_id=self.cliente_id,
            tipo=self._tipo_var.get(),
            fecha=self._fecha_var.get().strip(),
            notas=self._notas.get("1.0", "end").strip(),
            item_venta_ids=selected_ids,
            direccion_envio=self._dir_var.get().strip(),
            costo_envio=costo_envio,
        )
        messagebox.showinfo("Listo", "Despacho registrado correctamente.", parent=self)
        if self.on_done:
            self.on_done()
        self.grab_release()
        self.destroy()


# ─────────────────────────────────────────────────────────────────────────────
# Exchange dialog (prenda acumulada → otro producto, sin devolución en efectivo)
# ─────────────────────────────────────────────────────────────────────────────

class CambioDialog(ctk.CTkToplevel):
    def __init__(self, master, cliente_id: int, prenda: dict, on_done=None):
        super().__init__(master)
        self.title("Cambiar prenda")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self._cancel)
        self.grab_set()
        self.cliente_id = cliente_id
        self.prenda = prenda
        self.on_done = on_done
        self._selected: dict | None = None
        self._search_after = None
        self._build_ui()
        self._load_productos("")
        self.update_idletasks()
        w, h = 560, 640
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    def _cancel(self):
        self.grab_release()
        self.destroy()

    def _prenda_label(self, p: dict) -> str:
        parts = [p["nombre"]]
        if p.get("talle"):
            parts.append(f"T:{p['talle']}")
        if p.get("color"):
            parts.append(p["color"])
        return " · ".join(parts)

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1)

        p = self.prenda
        actual = self._prenda_label(p)
        ctk.CTkLabel(
            self,
            text="Prenda actual (acumulada, sin despachar)",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=0, column=0, padx=20, pady=(20, 4), sticky="w")
        ctk.CTkLabel(
            self,
            text=f"{actual}  x{p['cantidad']}  —  {money(p['precio_unitario'] * p['cantidad'])}",
            text_color="gray60",
        ).grid(row=1, column=0, padx=20, pady=(0, 10), sticky="w")

        ctk.CTkLabel(
            self,
            text="Buscar producto de reemplazo",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=2, column=0, padx=20, pady=(0, 6), sticky="w")

        top = ctk.CTkFrame(self, fg_color="transparent")
        top.grid(row=3, column=0, padx=20, pady=(0, 6), sticky="ew")
        top.grid_columnconfigure(0, weight=1)

        self._search_var = ctk.StringVar()
        ctk.CTkEntry(
            top,
            textvariable=self._search_var,
            placeholder_text="Nombre, talle, color, marca o código…",
        ).grid(row=0, column=0, sticky="ew")
        self._search_var.trace_add(
            "write",
            lambda *_: debounce(self, "_search_after", 250,
                                lambda: self._load_productos(self._search_var.get())),
        )

        self._prod_scroll = ctk.CTkScrollableFrame(self, height=220)
        self._prod_scroll.grid(row=4, column=0, padx=20, pady=(0, 10), sticky="nsew")
        self._prod_scroll.grid_columnconfigure(0, weight=1)

        info = ctk.CTkFrame(self, corner_radius=8)
        info.grid(row=5, column=0, padx=20, pady=(0, 10), sticky="ew")
        info.grid_columnconfigure(0, weight=1)
        self._diff_label = ctk.CTkLabel(
            info,
            text="Seleccioná el producto nuevo.",
            text_color="gray60",
            wraplength=500,
            justify="left",
        )
        self._diff_label.grid(row=0, column=0, padx=12, pady=10, sticky="w")

        self._pago_frame = ctk.CTkFrame(info, fg_color="transparent")
        self._pago_frame.grid(row=1, column=0, padx=12, pady=(0, 10), sticky="ew")
        ctk.CTkLabel(self._pago_frame, text="Cobrar diferencia:").pack(side="left")
        self._pago_var = ctk.StringVar(value="efectivo")
        ctk.CTkSegmentedButton(
            self._pago_frame,
            values=["efectivo", "transferencia"],
            variable=self._pago_var,
        ).pack(side="left", padx=(8, 0))
        self._pago_frame.grid_remove()

        ctk.CTkLabel(self, text="Notas (opcional):").grid(
            row=6, column=0, padx=20, pady=(0, 4), sticky="w")
        self._notas = ctk.CTkTextbox(self, height=50)
        self._notas.grid(row=7, column=0, padx=20, pady=(0, 10), sticky="ew")

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=8, column=0, padx=20, pady=(0, 16), sticky="ew")
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkButton(
            btn_frame, text="Confirmar cambio", height=42,
            fg_color="#2d6a4f", hover_color="#1b4332",
            command=self._confirmar,
        ).grid(row=0, column=0, padx=(0, 6), sticky="ew")
        ctk.CTkButton(
            btn_frame, text="Cancelar", height=42,
            fg_color="transparent", border_width=1,
            text_color=("gray10", "gray90"),
            command=self._cancel,
        ).grid(row=0, column=1, padx=(6, 0), sticky="ew")

    def _load_productos(self, texto: str):
        for w in self._prod_scroll.winfo_children():
            w.destroy()
        productos = (
            producto_model.search(texto.strip(), limit=80)
            if texto.strip()
            else producto_model.get_all(limit=80)
        )
        if not productos:
            ctk.CTkLabel(
                self._prod_scroll, text="Sin resultados.",
                text_color="gray60",
            ).pack(pady=12)
            return
        for prod in productos:
            if prod["id"] == self.prenda["producto_id"]:
                continue
            parts = [prod["nombre"]]
            if prod.get("talle"):
                parts.append(f"T:{prod['talle']}")
            if prod.get("color"):
                parts.append(prod["color"])
            label = f"{' · '.join(parts)}  —  {money(prod['precio'])}  (stock: {prod['stock']})"
            btn = ctk.CTkButton(
                self._prod_scroll,
                text=label,
                anchor="w",
                fg_color="transparent",
                border_width=1,
                text_color=("gray10", "gray90"),
                hover_color=("gray85", "gray25"),
                command=lambda p=prod: self._select_producto(p),
            )
            btn.pack(fill="x", pady=2)

    def _select_producto(self, prod: dict):
        self._selected = prod
        cantidad = int(self.prenda["cantidad"])
        precio_origen = float(self.prenda["precio_unitario"])
        precio_nuevo = float(prod["precio"])
        diff_unit = precio_nuevo - precio_origen
        diff_total = diff_unit * cantidad

        if diff_total > 0.009:
            self._diff_label.configure(
                text=(
                    f"Nuevo: {self._prenda_label(prod)} · {money(prod['precio'])}\n"
                    f"Diferencia a cobrar: {money(diff_total)} (no se devuelve efectivo si cuesta menos)."
                ),
                text_color=("gray10", "gray90"),
            )
            self._pago_frame.grid()
        elif diff_total < -0.009:
            self._diff_label.configure(
                text=(
                    f"Nuevo: {self._prenda_label(prod)} · {money(prod['precio'])}\n"
                    f"El nuevo cuesta menos. No se devuelve dinero; solo se cambia la prenda."
                ),
                text_color="#e9c46a",
            )
            self._pago_frame.grid_remove()
        else:
            self._diff_label.configure(
                text=(
                    f"Nuevo: {self._prenda_label(prod)} · mismo precio. "
                    "Cambio directo sin cobro adicional."
                ),
                text_color="#81c784",
            )
            self._pago_frame.grid_remove()

    def _confirmar(self):
        if not self._selected:
            messagebox.showwarning(
                "Atención", "Seleccioná el producto de reemplazo.", parent=self)
            return
        cantidad = int(self.prenda["cantidad"])
        if int(self._selected["stock"]) < cantidad:
            messagebox.showwarning(
                "Sin stock",
                f"Solo hay {self._selected['stock']} unidad(es) disponibles.",
                parent=self,
            )
            return
        try:
            cambio_model.registrar(
                item_venta_id=self.prenda["id"],
                cliente_id=self.cliente_id,
                nuevo_producto_id=self._selected["id"],
                fecha=date.today().isoformat(),
                notas=self._notas.get("1.0", "end").strip(),
                forma_pago_diff=self._pago_var.get(),
            )
        except cambio_model.CambioError as e:
            messagebox.showerror("No se pudo cambiar", str(e), parent=self)
            return
        messagebox.showinfo(
            "Listo",
            "Prenda cambiada correctamente.\n"
            "Sigue acumulada hasta que se despache.",
            parent=self,
        )
        if self.on_done:
            self.on_done()
        self.grab_release()
        self.destroy()


# ─────────────────────────────────────────────────────────────────────────────
# Plantillas manager dialog
# ─────────────────────────────────────────────────────────────────────────────

class PlantillasMensajeDialog(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Gestionar Plantillas")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self._close)
        self.grab_set()
        self._build_ui()
        self._load()
        self.update_idletasks()
        w, h = 520, 500
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    def _close(self):
        self.grab_release()
        self.destroy()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # New plantilla form
        top = ctk.CTkFrame(self, corner_radius=8)
        top.grid(row=0, column=0, padx=16, pady=(16, 8), sticky="ew")
        top.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(top, text="Nombre:").grid(
            row=0, column=0, padx=10, pady=6, sticky="w")
        self._nombre_var = ctk.StringVar()
        ctk.CTkEntry(top, textvariable=self._nombre_var).grid(
            row=0, column=1, padx=10, pady=6, sticky="ew")

        ctk.CTkLabel(top, text="Contenido:").grid(
            row=1, column=0, padx=10, pady=6, sticky="nw")
        self._contenido_box = ctk.CTkTextbox(top, height=70)
        self._contenido_box.grid(row=1, column=1, padx=10, pady=6, sticky="ew")

        ctk.CTkLabel(top, text="Variable: {nombre_cliente}",
                     text_color="gray60", font=ctk.CTkFont(size=10)).grid(
            row=2, column=0, columnspan=2, padx=10, sticky="w")
        ctk.CTkButton(top, text="Agregar plantilla",
                      command=self._agregar).grid(
            row=3, column=0, columnspan=2, padx=10, pady=8, sticky="ew")

        # List
        self._scroll = ctk.CTkScrollableFrame(self)
        self._scroll.grid(row=1, column=0, padx=16, pady=(0, 16), sticky="nsew")
        self._scroll.grid_columnconfigure(0, weight=1)

    def _load(self):
        for w in self._scroll.winfo_children():
            w.destroy()
        for p in plantilla_model.get_all():
            self._make_row(p)

    def _make_row(self, p: dict):
        row = ctk.CTkFrame(self._scroll, corner_radius=6)
        row.pack(fill="x", pady=3)
        row.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(row, text=p["nombre"],
                     font=ctk.CTkFont(size=12, weight="bold"), anchor="w").grid(
            row=0, column=0, padx=10, pady=(8, 2), sticky="w")
        ctk.CTkLabel(row, text=p["contenido"],
                     text_color="gray60", font=ctk.CTkFont(size=10),
                     wraplength=340, anchor="w", justify="left").grid(
            row=1, column=0, padx=10, pady=(0, 8), sticky="w")

        ctk.CTkButton(row, text="Eliminar", width=80,
                      fg_color="#e63946", hover_color="#c1121f",
                      command=lambda pid=p["id"]: self._eliminar(pid)).grid(
            row=0, column=1, rowspan=2, padx=(8, 10), pady=8)

    def _agregar(self):
        nombre = self._nombre_var.get().strip()
        contenido = self._contenido_box.get("1.0", "end").strip()
        if not nombre or not contenido:
            messagebox.showwarning("Atención",
                                   "Nombre y contenido son obligatorios.", parent=self)
            return
        try:
            plantilla_model.create(nombre, contenido)
        except Exception:
            messagebox.showwarning("Error",
                                   "Ya existe una plantilla con ese nombre.", parent=self)
            return
        self._nombre_var.set("")
        self._contenido_box.delete("1.0", "end")
        self._load()

    def _eliminar(self, plantilla_id: int):
        if not messagebox.askyesno("Confirmar", "¿Eliminar esta plantilla?",
                                   parent=self):
            return
        plantilla_model.delete(plantilla_id)
        self._load()


# ─────────────────────────────────────────────────────────────────────────────
# Main detail dialog
# ─────────────────────────────────────────────────────────────────────────────

class ClienteDetalleDialog(ctk.CTkToplevel):
    def __init__(self, master, cliente_id: int, on_close=None):
        super().__init__(master)
        self.title("Detalle de cliente")
        self.geometry("740x700")
        self.grab_set()
        self.cliente_id = cliente_id
        self.on_close = on_close
        self.protocol("WM_DELETE_WINDOW", self._close)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self._tabs_loaded: set[str] = set()
        self._build_ui()
        self._load_info()

    def _close(self):
        self.grab_release()
        if self.on_close:
            self.on_close()
        self.destroy()

    def _build_ui(self):
        # Tabs: Info | Prendas acumuladas | Historial
        self._tabview = ctk.CTkTabview(self, command=self._on_tab_changed)
        self._tabview.grid(row=0, column=0, padx=16, pady=16, sticky="nsew")
        self.grid_rowconfigure(0, weight=1)

        self._tab_info      = self._tabview.add("Datos")
        self._tab_prendas   = self._tabview.add("Prendas acumuladas")
        self._tab_historial = self._tabview.add("Historial")
        self._tab_whatsapp  = self._tabview.add("WhatsApp")

        self._build_info_tab()
        self._build_prendas_tab()
        self._build_historial_tab()
        self._build_whatsapp_tab()

    # ── Info tab ─────────────────────────────────────────────────────────────

    def _build_info_tab(self):
        tab = self._tab_info
        tab.grid_columnconfigure(1, weight=1)

        fields = [
            ("Nombre *",  "nombre"),
            ("Apellido",  "apellido"),
            ("C.I.",      "ci"),
            ("Ciudad",    "ciudad"),
            ("Teléfono",  "telefono"),
            ("Correo",    "correo"),
            ("Cumpleaños","cumpleanos"),
        ]
        self._info_vars = {}
        for i, (label, key) in enumerate(fields):
            ctk.CTkLabel(tab, text=label, font=ctk.CTkFont(size=13)).grid(
                row=i, column=0, padx=12, pady=(8, 0), sticky="w")
            var = ctk.StringVar()
            entry = ctk.CTkEntry(tab, textvariable=var, height=34)
            if key == "cumpleanos":
                entry.configure(placeholder_text="YYYY-MM-DD")
            entry.grid(row=i, column=1, padx=12, pady=(8, 0), sticky="ew")
            self._info_vars[key] = var

        n = len(fields)
        ctk.CTkLabel(tab, text="Notas", font=ctk.CTkFont(size=13)).grid(
            row=n, column=0, padx=12, pady=(8, 0), sticky="nw")
        self._notas_box = ctk.CTkTextbox(tab, height=80)
        self._notas_box.grid(row=n, column=1, padx=12, pady=(8, 0), sticky="ew")

        btn_frame = ctk.CTkFrame(tab, fg_color="transparent")
        btn_frame.grid(row=n + 1, column=0, columnspan=2, padx=12, pady=12, sticky="ew")
        btn_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkButton(btn_frame, text="Guardar cambios",
                      command=self._save_info).grid(row=0, column=0, sticky="ew")

        self._activo_btn = ctk.CTkButton(
            btn_frame, text="Eliminar cliente", height=36,
            fg_color="#e63946", hover_color="#c1121f",
            command=self._toggle_activo,
        )
        self._activo_btn.grid(row=1, column=0, pady=(8, 0), sticky="ew")

    # ── Prendas tab ───────────────────────────────────────────────────────────

    def _build_prendas_tab(self):
        tab = self._tab_prendas
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        btn_frame = ctk.CTkFrame(tab, fg_color="transparent")
        btn_frame.grid(row=0, column=0, pady=(0, 8), sticky="ew")

        ctk.CTkButton(btn_frame, text="Despachar prendas",
                      fg_color="#e63946", hover_color="#c1121f",
                      command=self._despachar).pack(side="left", padx=(0, 8))
        ctk.CTkLabel(
            btn_frame,
            text="Si no le queda, usá Cambiar en cada prenda (sin devolver efectivo).",
            text_color="gray60",
            font=ctk.CTkFont(size=11),
        ).pack(side="left")

        self._prendas_scroll = ctk.CTkScrollableFrame(tab)
        self._prendas_scroll.grid(row=1, column=0, sticky="nsew")
        self._prendas_scroll.grid_columnconfigure(0, weight=1)

    # ── Historial tab ─────────────────────────────────────────────────────────

    def _build_historial_tab(self):
        tab = self._tab_historial
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(0, weight=1)

        self._hist_scroll = ctk.CTkScrollableFrame(tab)
        self._hist_scroll.grid(row=0, column=0, sticky="nsew")
        self._hist_scroll.grid_columnconfigure(0, weight=1)

    # ── WhatsApp tab ──────────────────────────────────────────────────────────

    def _build_whatsapp_tab(self):
        tab = self._tab_whatsapp
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(2, weight=1)

        # Controls
        ctrl = ctk.CTkFrame(tab, fg_color="transparent")
        ctrl.grid(row=0, column=0, pady=(0, 8), sticky="ew")
        ctrl.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(ctrl, text="Plantilla:").grid(
            row=0, column=0, padx=(0, 8), sticky="w")
        self._plantillas: list[dict] = []
        self._plantilla_var = ctk.StringVar()
        self._plantilla_combo = ctk.CTkComboBox(
            ctrl, values=[], variable=self._plantilla_var,
            width=220, command=self._on_plantilla_change
        )
        self._plantilla_combo.grid(row=0, column=1, padx=(0, 8), sticky="ew")

        ctk.CTkButton(ctrl, text="Gestionar", width=100,
                      fg_color="transparent", border_width=1,
                      text_color=("gray10", "gray90"),
                      command=self._gestionar_plantillas).grid(row=0, column=2)

        # Editable message
        ctk.CTkLabel(tab, text="Mensaje:", anchor="w").grid(
            row=1, column=0, pady=(0, 4), sticky="w")
        self._wa_msg_box = ctk.CTkTextbox(tab, height=100)
        self._wa_msg_box.grid(row=2, column=0, sticky="nsew")

        # Send button
        btn_frame = ctk.CTkFrame(tab, fg_color="transparent")
        btn_frame.grid(row=3, column=0, pady=(8, 0), sticky="ew")
        ctk.CTkButton(btn_frame, text="📱 Abrir WhatsApp",
                      fg_color="#25d366", hover_color="#1ebe57",
                      text_color="white",
                      command=self._abrir_whatsapp).pack(side="left")

        # History
        ctk.CTkLabel(tab, text="Historial de mensajes:",
                     font=ctk.CTkFont(size=12), anchor="w").grid(
            row=4, column=0, pady=(12, 4), sticky="w")
        self._wa_hist_scroll = ctk.CTkScrollableFrame(tab, height=150)
        self._wa_hist_scroll.grid(row=5, column=0, sticky="ew")
        self._wa_hist_scroll.grid_columnconfigure(0, weight=1)

    # ── Data loading ─────────────────────────────────────────────────────────

    def _on_tab_changed(self, _tab_name: str = ""):
        tab = self._tabview.get()
        if tab == "Prendas acumuladas" and tab not in self._tabs_loaded:
            self._load_prendas()
            self._tabs_loaded.add(tab)
        elif tab == "Historial" and tab not in self._tabs_loaded:
            self._load_historial()
            self._tabs_loaded.add(tab)
        elif tab == "WhatsApp" and tab not in self._tabs_loaded:
            self._load_whatsapp()
            self._tabs_loaded.add(tab)

    def _reload_after_prenda_action(self):
        self._load_prendas()
        self._load_historial()
        self._tabs_loaded.add("Historial")
        master = self.master
        if hasattr(master, "app"):
            master.app.mark_data_changed("dashboard", "clientes")

    def _load_info(self):
        c = cliente_model.get_by_id(self.cliente_id)
        if not c:
            return

        nombre_completo = " ".join(filter(None, [c.get("nombre", ""), c.get("apellido", "")]))
        self.title(f"Detalle — {nombre_completo or c['nombre']}")
        self._info_vars["nombre"].set(c.get("nombre", ""))
        self._info_vars["apellido"].set(c.get("apellido", ""))
        self._info_vars["ci"].set(c.get("ci", ""))
        self._info_vars["ciudad"].set(c.get("ciudad", ""))
        self._info_vars["telefono"].set(c.get("telefono", ""))
        self._info_vars["correo"].set(c.get("correo", ""))
        self._info_vars["cumpleanos"].set(c.get("cumpleanos", ""))
        self._notas_box.delete("1.0", "end")
        self._notas_box.insert("1.0", c.get("notas", ""))

        activo = c.get("activo", 1)
        if activo:
            self._activo_btn.configure(
                text="Eliminar cliente",
                fg_color="#e63946",
                hover_color="#c1121f",
            )
        else:
            self._activo_btn.configure(
                text="Reactivar cliente",
                fg_color="#2d6a4f",
                hover_color="#1b4332",
            )

    def _load(self):
        self._load_info()
        tab = self._tabview.get()
        self._on_tab_changed(tab)

    def _load_prendas(self):
        for w in self._prendas_scroll.winfo_children():
            w.destroy()

        self._prendas = cliente_model.get_prendas_acumuladas(self.cliente_id)

        if not self._prendas:
            ctk.CTkLabel(self._prendas_scroll,
                         text="No hay prendas acumuladas.",
                         text_color="gray60").pack(pady=20)
            return

        for p in self._prendas:
            row = ctk.CTkFrame(self._prendas_scroll, corner_radius=8)
            row.pack(fill="x", pady=3)
            row.grid_columnconfigure(1, weight=1)

            parts = [p["nombre"]]
            if p.get("talle"):
                parts.append(f"T:{p['talle']}")
            if p.get("color"):
                parts.append(p["color"])
            ctk.CTkLabel(row, text=" · ".join(parts),
                         font=ctk.CTkFont(size=12, weight="bold"), anchor="w").grid(
                row=0, column=0, padx=12, pady=(8, 2), sticky="w")
            ctk.CTkLabel(row, text=f"Comprado: {p['fecha']}",
                         text_color="gray60", font=ctk.CTkFont(size=11)).grid(
                row=1, column=0, padx=12, pady=(0, 8), sticky="w")
            ctk.CTkLabel(row, text=f"x{p['cantidad']}",
                         font=ctk.CTkFont(size=12)).grid(
                row=0, column=1, padx=8, pady=8, rowspan=2)
            ctk.CTkLabel(row,
                         text=f"Gs. {p['precio_unitario'] * p['cantidad']:,.2f}",
                         font=ctk.CTkFont(size=12, weight="bold")).grid(
                row=0, column=2, padx=12, pady=8, rowspan=2)
            ctk.CTkButton(
                row, text="Cambiar", width=90,
                fg_color="#2d6a4f", hover_color="#1b4332",
                command=lambda prenda=p: self._cambiar_prenda(prenda),
            ).grid(row=0, column=3, padx=(0, 12), pady=8, rowspan=2)

    def _load_historial(self):
        for w in self._hist_scroll.winfo_children():
            w.destroy()

        ventas = venta_model.get_by_cliente(self.cliente_id)
        items_map = venta_model.get_items_by_venta_ids([v["id"] for v in ventas])
        despachos = despacho_model.get_by_cliente(self.cliente_id)
        cambios = cambio_model.get_by_cliente(self.cliente_id)

        # Merge and sort by date descending
        events = []
        for v in ventas:
            events.append(("venta", v["fecha"], v))
        for d in despachos:
            events.append(("despacho", d["fecha"], d))
        for c in cambios:
            events.append(("cambio", c["fecha"], c))
        events.sort(key=lambda x: x[1], reverse=True)

        if not events:
            ctk.CTkLabel(self._hist_scroll,
                         text="No hay historial aún.", text_color="gray60").pack(pady=20)
            return

        for kind, fecha, data in events:
            if kind == "venta":
                self._make_venta_row(data, items_map.get(data["id"], []))
            elif kind == "cambio":
                self._make_cambio_row(data)
            else:
                self._make_despacho_row(data)

    def _make_venta_row(self, v: dict, items: list[dict] | None = None):
        card = ctk.CTkFrame(self._hist_scroll, corner_radius=8,
                            fg_color=("gray90", "gray20"))
        card.pack(fill="x", pady=4)
        card.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(card, text="🛒 Venta",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color="#4fc3f7").grid(
            row=0, column=0, padx=12, pady=(8, 2), sticky="w")
        ctk.CTkLabel(card, text=v["fecha"],
                     text_color="gray60").grid(
            row=0, column=1, padx=8, pady=(8, 2), sticky="w")
        ctk.CTkLabel(card, text=f"Gs. {v['total']:,.2f}  ({v['forma_pago']})",
                     font=ctk.CTkFont(size=12, weight="bold")).grid(
            row=0, column=2, padx=12, pady=(8, 2))

        # Detail items
        if items is None:
            items = venta_model.get_items_by_venta(v["id"])
        for item in items:
            parts = [item["nombre"]]
            if item.get("talle"):
                parts.append(f"T:{item['talle']}")
            ctk.CTkLabel(card,
                         text=f"   · {' '.join(parts)}  x{item['cantidad']}",
                         text_color="gray60", font=ctk.CTkFont(size=11)).grid(
                row=items.index(item) + 1, column=0, columnspan=3,
                padx=12, pady=1, sticky="w")
        card.grid_rowconfigure(len(items) + 1, minsize=8)

    def _make_despacho_row(self, d: dict):
        card = ctk.CTkFrame(self._hist_scroll, corner_radius=8,
                            fg_color=("gray85", "gray18"))
        card.pack(fill="x", pady=4)
        card.grid_columnconfigure(1, weight=1)

        tipo_icon = "🚚" if d["tipo"] == "envio" else "🏪"
        ctk.CTkLabel(card,
                     text=f"{tipo_icon} Despacho ({d['tipo']})",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color="#81c784").grid(
            row=0, column=0, padx=12, pady=(8, 2), sticky="w")
        ctk.CTkLabel(card, text=d["fecha"], text_color="gray60").grid(
            row=0, column=1, padx=8, pady=(8, 2), sticky="w")

        for i, item in enumerate(d.get("items", [])):
            parts = [item["nombre"]]
            if item.get("talle"):
                parts.append(f"T:{item['talle']}")
            ctk.CTkLabel(card,
                         text=f"   · {' '.join(parts)}  x{item['cantidad']}",
                         text_color="gray60", font=ctk.CTkFont(size=11)).grid(
                row=i + 1, column=0, columnspan=3,
                padx=12, pady=1, sticky="w")

        extra_parts = []
        if d.get("direccion_envio"):
            extra_parts.append(f"Dirección: {d['direccion_envio']}")
        if d.get("costo_envio"):
            extra_parts.append(f"Costo envío: Gs. {d['costo_envio']:,.2f}")
        if d.get("notas"):
            extra_parts.append(f"Nota: {d['notas']}")

        if extra_parts:
            ctk.CTkLabel(card, text="   " + "  ·  ".join(extra_parts),
                         text_color="gray50", font=ctk.CTkFont(size=11)).grid(
                row=len(d["items"]) + 1, column=0, columnspan=3,
                padx=12, pady=(2, 8), sticky="w")
        else:
            card.grid_rowconfigure(len(d["items"]) + 1, minsize=8)

    def _make_cambio_row(self, c: dict):
        def _lbl(nombre, talle, color):
            parts = [nombre]
            if talle:
                parts.append(f"T:{talle}")
            if color:
                parts.append(color)
            return " · ".join(parts)

        card = ctk.CTkFrame(self._hist_scroll, corner_radius=8,
                            fg_color=("gray88", "gray22"))
        card.pack(fill="x", pady=4)
        card.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            card, text="🔄 Cambio de prenda",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#e9c46a",
        ).grid(row=0, column=0, padx=12, pady=(8, 2), sticky="w")
        ctk.CTkLabel(card, text=c["fecha"], text_color="gray60").grid(
            row=0, column=1, padx=8, pady=(8, 2), sticky="w")

        origen = _lbl(c["origen_nombre"], c.get("origen_talle"), c.get("origen_color"))
        nuevo = _lbl(c["nuevo_nombre"], c.get("nuevo_talle"), c.get("nuevo_color"))
        ctk.CTkLabel(
            card,
            text=f"   {origen}  →  {nuevo}  x{c['cantidad']}",
            text_color="gray60", font=ctk.CTkFont(size=11),
        ).grid(row=1, column=0, columnspan=3, padx=12, pady=1, sticky="w")

        extra = []
        if float(c.get("diferencia") or 0) > 0.009:
            extra.append(
                f"Diferencia cobrada: {money(c['diferencia'])} ({c.get('forma_pago_diff')})"
            )
        else:
            extra.append("Sin devolución en efectivo")
        if c.get("notas"):
            extra.append(c["notas"])
        ctk.CTkLabel(
            card, text="   " + " · ".join(extra),
            text_color="gray50", font=ctk.CTkFont(size=11),
        ).grid(row=2, column=0, columnspan=3, padx=12, pady=(2, 8), sticky="w")

    def _load_whatsapp(self):
        self._plantillas = plantilla_model.get_all()
        nombres = [p["nombre"] for p in self._plantillas]
        self._plantilla_combo.configure(values=nombres)
        if nombres:
            self._plantilla_var.set(nombres[0])
            self._on_plantilla_change(nombres[0])
        self._load_wa_hist()

    def _on_plantilla_change(self, value: str):
        plantilla = next(
            (p for p in self._plantillas if p["nombre"] == value), None
        )
        if not plantilla:
            return
        c = cliente_model.get_by_id(self.cliente_id)
        if not c:
            return
        rendered = plantilla_model.render(plantilla["contenido"], c)
        self._wa_msg_box.delete("1.0", "end")
        self._wa_msg_box.insert("1.0", rendered)

    def _load_wa_hist(self):
        for w in self._wa_hist_scroll.winfo_children():
            w.destroy()
        msgs = wa_model.get_by_cliente(self.cliente_id)
        if not msgs:
            ctk.CTkLabel(self._wa_hist_scroll,
                         text="Sin mensajes enviados.", text_color="gray60").pack(pady=8)
            return
        for m in msgs:
            card = ctk.CTkFrame(self._wa_hist_scroll, corner_radius=6)
            card.pack(fill="x", pady=2)
            card.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(card, text=m["fecha"],
                         text_color="gray50", font=ctk.CTkFont(size=10), anchor="w").grid(
                row=0, column=0, padx=10, pady=(6, 2), sticky="w")
            ctk.CTkLabel(card, text=m["contenido"],
                         text_color="gray80", font=ctk.CTkFont(size=11),
                         wraplength=560, anchor="w", justify="left").grid(
                row=1, column=0, padx=10, pady=(0, 6), sticky="w")

    def _abrir_whatsapp(self):
        c = cliente_model.get_by_id(self.cliente_id)
        if not c:
            return
        tel = (c.get("telefono") or "").strip()
        msg = self._wa_msg_box.get("1.0", "end").strip()
        if not msg:
            messagebox.showwarning("Atención", "El mensaje está vacío.", parent=self)
            return
        wa_num = tel.lstrip("+").replace(" ", "").replace("-", "")
        url = f"https://wa.me/{wa_num}?text={quote(msg)}" if wa_num else \
              f"https://wa.me/?text={quote(msg)}"
        webbrowser.open(url)
        # Log message
        wa_model.create(self.cliente_id, msg, date.today().isoformat())
        self._load_wa_hist()

    def _gestionar_plantillas(self):
        dlg = PlantillasMensajeDialog(self)
        self.wait_window(dlg)
        self._load_whatsapp()

    # ── Actions ───────────────────────────────────────────────────────────────

    def _toggle_activo(self):
        c = cliente_model.get_by_id(self.cliente_id)
        if not c:
            return

        activo = c.get("activo", 1)
        if activo:
            nombre = " ".join(filter(None, [c.get("nombre", ""), c.get("apellido", "")]))
            if not messagebox.askyesno(
                "Confirmar",
                f"¿Eliminar a {nombre}?\n\n"
                "El cliente dejará de aparecer en el listado, "
                "pero se conservará su historial de ventas.",
                parent=self,
            ):
                return

        cliente_model.toggle_activo(self.cliente_id)
        if activo:
            self._close()
        else:
            self._load()

    def _save_info(self):
        nombre = self._info_vars["nombre"].get().strip()
        if not nombre:
            messagebox.showwarning("Atención", "El nombre es obligatorio.", parent=self)
            return
        apellido = self._info_vars["apellido"].get().strip()
        cliente_model.update(
            self.cliente_id,
            nombre,
            apellido=apellido,
            ciudad=self._info_vars["ciudad"].get().strip(),
            telefono=self._info_vars["telefono"].get().strip(),
            notas=self._notas_box.get("1.0", "end").strip(),
            ci=self._info_vars["ci"].get().strip(),
            correo=self._info_vars["correo"].get().strip(),
            cumpleanos=self._info_vars["cumpleanos"].get().strip(),
        )
        messagebox.showinfo("Listo", "Datos actualizados.", parent=self)
        nombre_completo = " ".join(filter(None, [nombre, apellido]))
        self.title(f"Detalle — {nombre_completo}")

    def _cambiar_prenda(self, prenda: dict):
        dlg = CambioDialog(self, self.cliente_id, prenda,
                           on_done=self._reload_after_prenda_action)
        self.wait_window(dlg)

    def _despachar(self):
        if not self._prendas:
            messagebox.showinfo("Sin prendas",
                                "No hay prendas acumuladas para despachar.", parent=self)
            return
        dlg = DespachoDialog(self, self.cliente_id, self._prendas,
                             on_done=self._reload_after_prenda_action)
        self.wait_window(dlg)
