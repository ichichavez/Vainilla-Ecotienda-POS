from __future__ import annotations
import customtkinter as ctk
from datetime import date
from tkinter import messagebox

import models.caja_proveedor as caja_model
import views.theme as theme


# ─────────────────────────────────────────────────────────────────────────────
# Dialog: Nueva caja
# ─────────────────────────────────────────────────────────────────────────────

class _NuevaCajaDialog(ctk.CTkToplevel):
    """Registrar que un proveedor dejó una caja/bolsa con ropa."""

    def __init__(self, master):
        super().__init__(master)
        self.title("Registrar caja de proveedor")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self._cancel)
        self.grab_set()
        self.result = None
        self._build_ui()
        self.update_idletasks()
        w, h = 460, 360
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self, text="Nueva caja de proveedor",
            font=theme.font(theme.FONT_MD, "bold"),
        ).grid(row=0, column=0, padx=24, pady=(20, 16), sticky="w")

        form = ctk.CTkFrame(self, fg_color="transparent")
        form.grid(row=1, column=0, padx=24, sticky="ew")
        form.grid_columnconfigure(1, weight=1)

        # Proveedor
        ctk.CTkLabel(form, text="Proveedor *", anchor="w",
                     font=theme.font()).grid(
            row=0, column=0, padx=(0, 12), pady=(0, 10), sticky="w")
        self._proveedor_var = ctk.StringVar()
        ctk.CTkEntry(form, textvariable=self._proveedor_var,
                     height=36, placeholder_text="Nombre del proveedor").grid(
            row=0, column=1, pady=(0, 10), sticky="ew")

        # Descripción
        ctk.CTkLabel(form, text="Contenido", anchor="w",
                     font=theme.font()).grid(
            row=1, column=0, padx=(0, 12), pady=(0, 10), sticky="nw")
        self._desc_var = ctk.StringVar()
        ctk.CTkEntry(form, textvariable=self._desc_var, height=36,
                     placeholder_text="Ej: 2 bolsas ropa invierno, 15 remeras…").grid(
            row=1, column=1, pady=(0, 10), sticky="ew")

        # Fecha ingreso
        ctk.CTkLabel(form, text="Fecha ingreso", anchor="w",
                     font=theme.font()).grid(
            row=2, column=0, padx=(0, 12), pady=(0, 10), sticky="w")
        self._fecha_var = ctk.StringVar(value=date.today().isoformat())
        ctk.CTkEntry(form, textvariable=self._fecha_var, height=36).grid(
            row=2, column=1, pady=(0, 10), sticky="ew")

        # Notas
        ctk.CTkLabel(form, text="Notas", anchor="w",
                     font=theme.font()).grid(
            row=3, column=0, padx=(0, 12), pady=(0, 0), sticky="nw")
        self._notas = ctk.CTkTextbox(form, height=60)
        self._notas.grid(row=3, column=1, sticky="ew")

        # Botones
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=2, column=0, padx=24, pady=(20, 20), sticky="ew")
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(
            btn_frame, text="Guardar", height=40,
            fg_color=theme.PRIMARY, hover_color=theme.PRIMARY_HOVER,
            command=self._save,
        ).grid(row=0, column=0, padx=(0, 6), sticky="ew")
        ctk.CTkButton(
            btn_frame, text="Cancelar", height=40,
            fg_color="transparent", border_width=1,
            text_color=("gray10", "gray90"),
            command=self._cancel,
        ).grid(row=0, column=1, padx=(6, 0), sticky="ew")

    def _save(self):
        proveedor = self._proveedor_var.get().strip()
        if not proveedor:
            messagebox.showwarning("Atención", "El nombre del proveedor es obligatorio.",
                                   parent=self)
            return
        fecha = self._fecha_var.get().strip()
        if not fecha:
            messagebox.showwarning("Atención", "Ingresá la fecha de ingreso.", parent=self)
            return
        self.result = {
            "proveedor":   proveedor,
            "descripcion": self._desc_var.get().strip(),
            "fecha":       fecha,
            "notas":       self._notas.get("1.0", "end").strip(),
        }
        self.grab_release()
        self.destroy()

    def _cancel(self):
        self.grab_release()
        self.destroy()


# ─────────────────────────────────────────────────────────────────────────────
# Dialog: Registrar retiro
# ─────────────────────────────────────────────────────────────────────────────

class _RetiroDialog(ctk.CTkToplevel):
    """Registrar que el proveedor vino a buscar su caja."""

    def __init__(self, master, caja: dict):
        super().__init__(master)
        self.title("Registrar retiro")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self._cancel)
        self.grab_set()
        self.result = None
        self._build_ui(caja)
        self.update_idletasks()
        w, h = 400, 280
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    def _build_ui(self, caja: dict):
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self, text="Registrar retiro de caja",
            font=theme.font(theme.FONT_MD, "bold"),
        ).grid(row=0, column=0, padx=24, pady=(20, 4), sticky="w")

        ctk.CTkLabel(
            self, text=f"Proveedor: {caja['proveedor']}",
            font=theme.font(), text_color="gray50",
        ).grid(row=1, column=0, padx=24, pady=(0, 16), sticky="w")

        form = ctk.CTkFrame(self, fg_color="transparent")
        form.grid(row=2, column=0, padx=24, sticky="ew")
        form.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(form, text="Fecha de retiro", anchor="w",
                     font=theme.font()).grid(
            row=0, column=0, padx=(0, 12), pady=(0, 10), sticky="w")
        self._fecha_var = ctk.StringVar(value=date.today().isoformat())
        ctk.CTkEntry(form, textvariable=self._fecha_var, height=36).grid(
            row=0, column=1, pady=(0, 10), sticky="ew")

        ctk.CTkLabel(form, text="Notas", anchor="w",
                     font=theme.font()).grid(
            row=1, column=0, padx=(0, 12), sticky="nw")
        self._notas = ctk.CTkTextbox(form, height=60)
        self._notas.grid(row=1, column=1, sticky="ew")

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=3, column=0, padx=24, pady=(20, 20), sticky="ew")
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(
            btn_frame, text="Confirmar retiro", height=40,
            fg_color=theme.PRIMARY, hover_color=theme.PRIMARY_HOVER,
            command=self._save,
        ).grid(row=0, column=0, padx=(0, 6), sticky="ew")
        ctk.CTkButton(
            btn_frame, text="Cancelar", height=40,
            fg_color="transparent", border_width=1,
            text_color=("gray10", "gray90"),
            command=self._cancel,
        ).grid(row=0, column=1, padx=(6, 0), sticky="ew")

    def _save(self):
        fecha = self._fecha_var.get().strip()
        if not fecha:
            messagebox.showwarning("Atención", "Ingresá la fecha de retiro.", parent=self)
            return
        self.result = {
            "fecha_retiro": fecha,
            "notas":        self._notas.get("1.0", "end").strip(),
        }
        self.grab_release()
        self.destroy()

    def _cancel(self):
        self.grab_release()
        self.destroy()


# ─────────────────────────────────────────────────────────────────────────────
# Main view
# ─────────────────────────────────────────────────────────────────────────────

class CajasProveedorView(ctk.CTkFrame):

    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self._build_ui()

    # ── UI ───────────────────────────────────────────────────────────────────

    def _build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, padx=24, pady=(24, 12), sticky="ew")
        header.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            header, text="Cajas de Proveedor",
            font=theme.font(theme.FONT_HERO, "bold"),
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkButton(
            header, text="+ Nueva caja",
            fg_color=theme.PRIMARY, hover_color=theme.PRIMARY_HOVER,
            font=theme.font(theme.FONT_BASE),
            command=self._nueva_caja,
        ).grid(row=0, column=2, sticky="e")

        # Filter bar
        filter_bar = ctk.CTkFrame(self, fg_color="transparent")
        filter_bar.grid(row=1, column=0, padx=24, pady=(0, 8), sticky="ew")

        ctk.CTkLabel(filter_bar, text="Mostrar:",
                     font=theme.font()).pack(side="left", padx=(0, 8))
        self._filtro_var = ctk.StringVar(value="pendiente")
        seg = ctk.CTkSegmentedButton(
            filter_bar,
            values=["pendiente", "retirado", "todos"],
            variable=self._filtro_var,
            command=lambda _: self._load(),
        )
        seg.pack(side="left")

        # List
        self._scroll = ctk.CTkScrollableFrame(self)
        self._scroll.grid(row=2, column=0, padx=24, pady=(0, 20), sticky="nsew")
        self._scroll.grid_columnconfigure(0, weight=1)

    # ── Data ─────────────────────────────────────────────────────────────────

    def refresh(self, **kwargs):
        self._filtro_var.set("pendiente")
        self._load()

    def _load(self):
        for w in self._scroll.winfo_children():
            w.destroy()

        filtro = self._filtro_var.get()
        estado = None if filtro == "todos" else filtro
        cajas = caja_model.get_all(estado=estado)

        if not cajas:
            msg = {
                "pendiente": "No hay cajas pendientes de retiro.",
                "retirado":  "No hay cajas retiradas registradas.",
                "todos":     "No hay cajas registradas.",
            }.get(filtro, "")
            ctk.CTkLabel(
                self._scroll, text=msg, text_color="gray50",
                font=theme.font(),
            ).pack(pady=30)
            return

        for caja in cajas:
            self._make_row(caja)

    def _make_row(self, caja: dict):
        pendiente = caja["estado"] == "pendiente"

        row = ctk.CTkFrame(self._scroll, corner_radius=10)
        row.pack(fill="x", pady=4)
        row.grid_columnconfigure(1, weight=1)

        # Estado badge
        badge_color = theme.WARNING if pendiente else theme.PRIMARY
        badge_text  = "pendiente" if pendiente else "retirado"
        ctk.CTkLabel(
            row,
            text=f"  {badge_text}  ",
            fg_color=badge_color,
            corner_radius=8,
            font=theme.font(theme.FONT_SM, "bold"),
            text_color="white",
        ).grid(row=0, column=0, padx=(14, 10), pady=(14, 6), sticky="nw")

        # Info
        info = ctk.CTkFrame(row, fg_color="transparent")
        info.grid(row=0, column=1, pady=(12, 10), sticky="ew")

        ctk.CTkLabel(
            info, text=caja["proveedor"],
            font=theme.font(theme.FONT_BASE, "bold"), anchor="w",
        ).pack(anchor="w")

        if caja["descripcion"]:
            ctk.CTkLabel(
                info, text=caja["descripcion"],
                font=theme.font(theme.FONT_SM), text_color="gray50", anchor="w",
            ).pack(anchor="w")

        dates_text = f"Ingresó: {caja['fecha_ingreso']}"
        if caja["fecha_retiro"]:
            dates_text += f"   ·   Retiró: {caja['fecha_retiro']}"
        ctk.CTkLabel(
            info, text=dates_text,
            font=theme.font(theme.FONT_SM), text_color="gray50", anchor="w",
        ).pack(anchor="w", pady=(2, 0))

        if caja["notas"]:
            ctk.CTkLabel(
                info, text=f"Nota: {caja['notas']}",
                font=theme.font(theme.FONT_SM), text_color="gray50", anchor="w",
            ).pack(anchor="w")

        # Acciones
        actions = ctk.CTkFrame(row, fg_color="transparent")
        actions.grid(row=0, column=2, padx=(8, 12), pady=12, sticky="e")

        if pendiente:
            ctk.CTkButton(
                actions, text="Registrar retiro", width=140,
                fg_color=theme.PRIMARY, hover_color=theme.PRIMARY_HOVER,
                font=theme.font(theme.FONT_SM),
                command=lambda c=caja: self._registrar_retiro(c),
            ).pack(pady=(0, 4))

        ctk.CTkButton(
            actions, text="Eliminar", width=140,
            fg_color="transparent", border_width=1,
            text_color=theme.DANGER,
            hover_color=("gray85", "gray20"),
            font=theme.font(theme.FONT_SM),
            command=lambda c=caja: self._eliminar(c),
        ).pack()

    # ── Actions ──────────────────────────────────────────────────────────────

    def _nueva_caja(self):
        dlg = _NuevaCajaDialog(self)
        self.wait_window(dlg)
        if dlg.result:
            caja_model.create(
                proveedor=dlg.result["proveedor"],
                descripcion=dlg.result["descripcion"],
                fecha_ingreso=dlg.result["fecha"],
                notas=dlg.result["notas"],
            )
            self._load()

    def _registrar_retiro(self, caja: dict):
        dlg = _RetiroDialog(self, caja)
        self.wait_window(dlg)
        if dlg.result:
            caja_model.marcar_retirado(
                caja_id=caja["id"],
                fecha_retiro=dlg.result["fecha_retiro"],
                notas=dlg.result["notas"],
            )
            self._load()

    def _eliminar(self, caja: dict):
        if not messagebox.askyesno(
            "Confirmar",
            f"¿Eliminar el registro de caja de '{caja['proveedor']}'?",
            parent=self,
        ):
            return
        caja_model.delete(caja["id"])
        self._load()
