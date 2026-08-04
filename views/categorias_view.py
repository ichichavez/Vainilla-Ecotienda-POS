from __future__ import annotations
import customtkinter as ctk
from tkinter import messagebox

import models.categoria as categoria_model


# ─────────────────────────────────────────────────────────────────────────────
# Form dialog
# ─────────────────────────────────────────────────────────────────────────────

class CategoriaFormDialog(ctk.CTkToplevel):
    def __init__(self, master, categoria: dict | None = None, on_done=None):
        super().__init__(master)
        self.categoria = categoria
        self.on_done = on_done
        self.title("Editar categoría" if categoria else "Nueva categoría")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self._cancel)
        self.grab_set()
        self._build_ui()
        self.update_idletasks()
        w, h = 420, 300 if not categoria else 360
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        container = ctk.CTkFrame(self, fg_color="transparent")
        container.grid(row=0, column=0, sticky="nsew")
        container.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(container, text="Nombre *", anchor="w",
                     font=ctk.CTkFont(size=13)).grid(
            row=0, column=0, padx=(20, 8), pady=(16, 0), sticky="w")
        self._nombre_var = ctk.StringVar(
            value=self.categoria["nombre"] if self.categoria else "")
        ctk.CTkEntry(container, textvariable=self._nombre_var, height=36).grid(
            row=0, column=1, padx=(0, 20), pady=(16, 0), sticky="ew")

        ctk.CTkLabel(container, text="Descripción", anchor="w",
                     font=ctk.CTkFont(size=13)).grid(
            row=1, column=0, padx=(20, 8), pady=(10, 0), sticky="w")
        self._desc_var = ctk.StringVar(
            value=self.categoria["descripcion"] if self.categoria else "")
        ctk.CTkEntry(container, textvariable=self._desc_var, height=36).grid(
            row=1, column=1, padx=(0, 20), pady=(10, 0), sticky="ew")

        btn_frame = ctk.CTkFrame(container, fg_color="transparent")
        btn_frame.grid(row=2, column=0, columnspan=2, padx=20, pady=(16, 8), sticky="ew")
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

        if self.categoria:
            activo = self.categoria.get("activo", 1)
            ctk.CTkButton(
                container,
                text="Desactivar" if activo else "Activar",
                fg_color="#e63946" if activo else "#2d6a4f",
                hover_color="#c1121f" if activo else "#1b4332",
                command=self._toggle
            ).grid(row=3, column=0, columnspan=2, padx=20, pady=(0, 16), sticky="ew")

    def _cancel(self):
        self.grab_release()
        self.destroy()

    def _save(self):
        nombre = self._nombre_var.get().strip()
        if not nombre:
            messagebox.showwarning("Error", "El nombre es obligatorio.", parent=self)
            return
        desc = self._desc_var.get().strip()
        try:
            if self.categoria:
                categoria_model.update(self.categoria["id"], nombre, desc)
            else:
                categoria_model.create(nombre, desc)
        except Exception:
            messagebox.showwarning(
                "Error", "Ya existe una categoría con ese nombre.", parent=self)
            return
        if self.on_done:
            self.on_done()
        self.grab_release()
        self.destroy()

    def _toggle(self):
        categoria_model.toggle_activo(self.categoria["id"])
        if self.on_done:
            self.on_done()
        self.grab_release()
        self.destroy()


# ─────────────────────────────────────────────────────────────────────────────
# Main view
# ─────────────────────────────────────────────────────────────────────────────

class CategoriasView(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self._build_ui()

    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, padx=24, pady=(20, 8), sticky="ew")
        header.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(header, text="Categorías",
                     font=ctk.CTkFont(size=24, weight="bold")).grid(
            row=0, column=0, sticky="w")
        ctk.CTkButton(header, text="+ Nueva categoría",
                      command=self._nueva).grid(row=0, column=2)

        self._scroll = ctk.CTkScrollableFrame(self)
        self._scroll.grid(row=1, column=0, padx=24, pady=(0, 20), sticky="nsew")
        self._scroll.grid_columnconfigure(0, weight=1)

    def refresh(self, **kwargs):
        self._load()

    def _load(self):
        for w in self._scroll.winfo_children():
            w.destroy()

        categorias = categoria_model.get_all(activos_only=False)
        if not categorias:
            ctk.CTkLabel(self._scroll, text="No hay categorías.",
                         text_color="gray60").pack(pady=20)
            return

        for cat in categorias:
            self._make_row(cat)

    def _make_row(self, cat: dict):
        row = ctk.CTkFrame(self._scroll, corner_radius=8)
        row.pack(fill="x", pady=4)
        row.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(row, text=cat["nombre"],
                     font=ctk.CTkFont(size=13, weight="bold"), anchor="w").grid(
            row=0, column=0, padx=14, pady=12, sticky="w")

        if cat.get("descripcion"):
            ctk.CTkLabel(row, text=cat["descripcion"],
                         text_color="gray60", font=ctk.CTkFont(size=11),
                         anchor="w").grid(
                row=0, column=1, padx=8, pady=12, sticky="w")

        ctk.CTkLabel(
            row,
            text="  activa  " if cat["activo"] else "  inactiva  ",
            fg_color="#2d6a4f" if cat["activo"] else "gray40",
            corner_radius=6, font=ctk.CTkFont(size=11)
        ).grid(row=0, column=2, padx=4, pady=12)

        ctk.CTkButton(row, text="Editar", width=90,
                      command=lambda c=cat: self._editar(c)).grid(
            row=0, column=3, padx=12, pady=10)

    def _nueva(self):
        dlg = CategoriaFormDialog(self, on_done=self._load)
        self.wait_window(dlg)

    def _editar(self, cat: dict):
        dlg = CategoriaFormDialog(self, categoria=cat, on_done=self._load)
        self.wait_window(dlg)
