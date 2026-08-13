import customtkinter as ctk
from tkinter import messagebox

import models.cliente as cliente_model
from views.cliente_detalle import ClienteDetalleDialog
from utils.ui import debounce


class ClientesView(ctk.CTkFrame):
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

        ctk.CTkLabel(header, text="Clientes",
                     font=ctk.CTkFont(size=24, weight="bold")).grid(
            row=0, column=0, sticky="w")

        ctk.CTkButton(header, text="+ Nuevo cliente",
                      command=self._nueva_cliente).grid(
            row=0, column=2, padx=0)

        # Search + filters
        search_frame = ctk.CTkFrame(self, fg_color="transparent")
        search_frame.grid(row=1, column=0, padx=24, pady=(0, 8), sticky="ew")
        search_frame.grid_columnconfigure(0, weight=1)

        self._search_var = ctk.StringVar()
        ctk.CTkEntry(search_frame, textvariable=self._search_var,
                     placeholder_text="Buscar por nombre, CI, ciudad o correo...").grid(
            row=0, column=0, padx=(0, 8), sticky="ew")
        self._search_var.trace_add(
            "write",
            lambda *_: debounce(self, "_search_after", 250, self._load),
        )

        self._show_inactive_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(search_frame, text="Mostrar inactivos",
                        variable=self._show_inactive_var,
                        command=self._load).grid(row=0, column=1)

        # List
        self._scroll = ctk.CTkScrollableFrame(self)
        self._scroll.grid(row=2, column=0, padx=24, pady=(0, 20), sticky="nsew")
        self._scroll.grid_columnconfigure(0, weight=1)

    def refresh(self, **kwargs):
        self._search_var.set("")
        self._show_inactive_var.set(False)
        self._load()

    def _load(self):
        texto = self._search_var.get().strip()
        activos_only = not self._show_inactive_var.get()
        clientes = (cliente_model.search(texto, activos_only=activos_only)
                    if texto else
                    cliente_model.get_all(activos_only=activos_only))

        for w in self._scroll.winfo_children():
            w.destroy()

        if not clientes:
            ctk.CTkLabel(self._scroll, text="No se encontraron clientes.",
                         text_color="gray60").pack(pady=20)
            return

        counts = cliente_model.get_acumuladas_counts([c["id"] for c in clientes])
        for c in clientes:
            self._make_row(c, counts.get(c["id"], 0))

    def _make_row(self, c: dict, n_acum: int):
        row = ctk.CTkFrame(self._scroll, corner_radius=8)
        row.pack(fill="x", pady=4)
        row.grid_columnconfigure(1, weight=1)

        activo = c.get("activo", 1)
        nombre_completo = " ".join(filter(None, [c["nombre"], c.get("apellido", "")]))

        # Name
        nombre_color = ("gray10", "gray90") if activo else "gray50"
        ctk.CTkLabel(row, text=nombre_completo,
                     font=ctk.CTkFont(size=13, weight="bold"), anchor="w",
                     text_color=nombre_color).grid(
            row=0, column=0, padx=14, pady=(10, 2), sticky="w")
        ctk.CTkLabel(row, text=c["ciudad"] or "—",
                     text_color="gray60", font=ctk.CTkFont(size=11)).grid(
            row=1, column=0, padx=14, pady=(0, 10), sticky="w")

        # Phone
        ctk.CTkLabel(row, text=c["telefono"] or "",
                     text_color="gray60", anchor="w").grid(
            row=0, column=1, padx=8, pady=10, sticky="w", rowspan=2)

        # Badges
        badge_col = 2
        if not activo:
            ctk.CTkLabel(
                row, text="  inactivo  ",
                fg_color="gray40", corner_radius=10,
                font=ctk.CTkFont(size=11)
            ).grid(row=0, column=badge_col, padx=4, pady=10, rowspan=2)
            badge_col += 1

        if n_acum > 0:
            ctk.CTkLabel(
                row,
                text=f"  {n_acum} acumulada{'s' if n_acum != 1 else ''}  ",
                fg_color="#e63946", corner_radius=10,
                font=ctk.CTkFont(size=11, weight="bold")
            ).grid(row=0, column=badge_col, padx=4, pady=10, rowspan=2)

        ctk.CTkButton(row, text="Ver detalle", width=110,
                      command=lambda cid=c["id"]: self.open_detalle(cid)).grid(
            row=0, column=4, padx=(12, 4), pady=10, rowspan=2)

        if activo:
            ctk.CTkButton(
                row, text="Eliminar", width=90,
                fg_color="#e63946", hover_color="#c1121f",
                command=lambda cid=c["id"], nom=nombre_completo: self._eliminar(cid, nom),
            ).grid(row=0, column=5, padx=(4, 12), pady=10, rowspan=2)
        else:
            ctk.CTkButton(
                row, text="Reactivar", width=90,
                fg_color="#2d6a4f", hover_color="#1b4332",
                command=lambda cid=c["id"]: self._reactivar(cid),
            ).grid(row=0, column=5, padx=(4, 12), pady=10, rowspan=2)

    def _eliminar(self, cliente_id: int, nombre: str):
        if not messagebox.askyesno(
            "Confirmar",
            f"¿Eliminar a {nombre}?\n\n"
            "El cliente dejará de aparecer en el listado, "
            "pero se conservará su historial de ventas.",
            parent=self,
        ):
            return
        cliente_model.toggle_activo(cliente_id)
        self._load()

    def _reactivar(self, cliente_id: int):
        cliente_model.toggle_activo(cliente_id)
        self._load()

    def _nueva_cliente(self):
        from views.nueva_venta import NuevaClienteDialog
        dlg = NuevaClienteDialog(self)
        self.wait_window(dlg)
        self._load()

    def open_detalle(self, cliente_id: int):
        dlg = ClienteDetalleDialog(self, cliente_id, on_close=self._load)
        self.wait_window(dlg)
