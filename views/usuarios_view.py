from __future__ import annotations
import customtkinter as ctk
from tkinter import messagebox

import models.usuario as usuario_model
import models.rol as rol_model


# ─────────────────────────────────────────────────────────────────────────────
# Rol form dialog
# ─────────────────────────────────────────────────────────────────────────────

class RolFormDialog(ctk.CTkToplevel):
    def __init__(self, master, rol: dict | None = None, on_done=None):
        super().__init__(master)
        self.rol = rol
        self.on_done = on_done
        self.title("Editar rol" if rol else "Nuevo rol")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self._cancel)
        self.grab_set()
        self._build_ui()
        self.update_idletasks()
        w, h = 420, 620
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    def _build_ui(self):
        self.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self, text="Nombre *").grid(
            row=0, column=0, padx=16, pady=10, sticky="w")
        self._nombre_var = ctk.StringVar(
            value=self.rol["nombre"] if self.rol else "")
        ctk.CTkEntry(self, textvariable=self._nombre_var).grid(
            row=0, column=1, padx=16, pady=10, sticky="ew")

        ctk.CTkLabel(self, text="Permisos",
                     font=ctk.CTkFont(weight="bold")).grid(
            row=1, column=0, columnspan=2, padx=16, pady=(8, 4), sticky="w")

        perm_labels = {
            "dashboard":  "Inicio / Dashboard",
            "ventas":     "Ventas",
            "clientes":   "Clientes",
            "productos":  "Productos",
            "caja":       "Caja del Día",
            "compras":    "Compras",
            "categorias": "Categorías",
            "usuarios":   "Usuarios / Roles",
            "reportes":   "Reportes",
            "gastos":     "Gastos del Local",
            "etiquetas":  "Etiquetas de Precio",
            "catalogo":   "Catálogo Online",
        }

        self._perm_vars: dict[str, ctk.BooleanVar] = {}
        for i, key in enumerate(rol_model.PERMISOS_KEYS):
            var = ctk.BooleanVar(value=bool(self.rol[key]) if self.rol else False)
            self._perm_vars[key] = var
            ctk.CTkCheckBox(self, text=perm_labels[key], variable=var).grid(
                row=2 + i, column=0, columnspan=2, padx=24, pady=3, sticky="w")

        btn_row = 2 + len(rol_model.PERMISOS_KEYS)
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=btn_row, column=0, columnspan=2,
                       padx=16, pady=(12, 16), sticky="ew")
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
        nombre = self._nombre_var.get().strip()
        if not nombre:
            messagebox.showwarning("Error", "El nombre es obligatorio.", parent=self)
            return
        permisos = {k: v.get() for k, v in self._perm_vars.items()}
        try:
            if self.rol:
                rol_model.update(self.rol["id"], nombre, permisos)
            else:
                rol_model.create(nombre, permisos)
        except Exception:
            messagebox.showwarning(
                "Error", "Ya existe un rol con ese nombre.", parent=self)
            return
        if self.on_done:
            self.on_done()
        self.grab_release()
        self.destroy()


# ─────────────────────────────────────────────────────────────────────────────
# Usuario form dialog
# ─────────────────────────────────────────────────────────────────────────────

class UsuarioFormDialog(ctk.CTkToplevel):
    def __init__(self, master, usuario: dict | None = None,
                 usuario_actual: dict | None = None, on_done=None):
        super().__init__(master)
        self.usuario = usuario
        self.usuario_actual = usuario_actual
        self.on_done = on_done
        self.title("Editar usuario" if usuario else "Nuevo usuario")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self._cancel)
        self.grab_set()
        self._build_ui()
        self.update_idletasks()
        w, h = 440, 460
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    def _build_ui(self):
        self.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self, text="Usuario").grid(
            row=0, column=0, padx=16, pady=10, sticky="w")
        self._user_var = ctk.StringVar(
            value=self.usuario["username"] if self.usuario else "")
        entry = ctk.CTkEntry(self, textvariable=self._user_var)
        entry.grid(row=0, column=1, padx=16, pady=10, sticky="ew")
        if self.usuario:
            entry.configure(state="disabled")

        ctk.CTkLabel(self, text="Contraseña").grid(
            row=1, column=0, padx=16, pady=10, sticky="w")
        self._pass_var = ctk.StringVar()
        ctk.CTkEntry(
            self, textvariable=self._pass_var, show="*",
            placeholder_text="Dejar vacío para no cambiar" if self.usuario else ""
        ).grid(row=1, column=1, padx=16, pady=10, sticky="ew")

        ctk.CTkLabel(self, text="Confirmar").grid(
            row=2, column=0, padx=16, pady=10, sticky="w")
        self._pass2_var = ctk.StringVar()
        ctk.CTkEntry(self, textvariable=self._pass2_var, show="*").grid(
            row=2, column=1, padx=16, pady=10, sticky="ew")

        # Role combobox loaded from roles table
        ctk.CTkLabel(self, text="Rol").grid(
            row=3, column=0, padx=16, pady=10, sticky="w")
        self._roles_list = rol_model.get_all(activos_only=True)
        rol_nombres = [r["nombre"] for r in self._roles_list]
        current_rol = (self.usuario["rol_nombre"]
                       if self.usuario else (rol_nombres[0] if rol_nombres else ""))
        self._rol_var = ctk.StringVar(value=current_rol)
        ctk.CTkComboBox(self, values=rol_nombres, variable=self._rol_var).grid(
            row=3, column=1, padx=16, pady=10, sticky="ew")

        btn_frame2 = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame2.grid(row=4, column=0, columnspan=2, padx=16, pady=(16, 6), sticky="ew")
        btn_frame2.grid_columnconfigure(0, weight=1)
        btn_frame2.grid_columnconfigure(1, weight=1)
        ctk.CTkButton(btn_frame2, text="Guardar", height=40,
                      command=self._save).grid(
            row=0, column=0, padx=(0, 6), sticky="ew")
        ctk.CTkButton(btn_frame2, text="Cancelar", height=40,
                      fg_color="transparent", border_width=1,
                      text_color=("gray10", "gray90"),
                      command=self._cancel).grid(
            row=0, column=1, padx=(6, 0), sticky="ew")

        if (self.usuario and self.usuario_actual
                and self.usuario["id"] != self.usuario_actual["id"]):
            activo = self.usuario.get("activo", 1)
            ctk.CTkButton(
                self,
                text="Desactivar usuario" if activo else "Activar usuario",
                fg_color="#e63946" if activo else "#2d6a4f",
                hover_color="#c1121f" if activo else "#1b4332",
                command=self._toggle_activo
            ).grid(row=5, column=0, columnspan=2, padx=16, pady=(0, 16), sticky="ew")

    def _save(self):
        username = self._user_var.get().strip()
        password = self._pass_var.get()
        password2 = self._pass2_var.get()
        rol_nombre = self._rol_var.get()

        if not self.usuario and not username:
            messagebox.showwarning(
                "Error", "El nombre de usuario es obligatorio.", parent=self)
            return

        if password or not self.usuario:
            if len(password) < 4:
                messagebox.showwarning(
                    "Error", "La contraseña debe tener al menos 4 caracteres.",
                    parent=self)
                return
            if password != password2:
                messagebox.showwarning(
                    "Error", "Las contraseñas no coinciden.", parent=self)
                return

        rol_row = next(
            (r for r in self._roles_list if r["nombre"] == rol_nombre), None)

        if self.usuario:
            if password:
                usuario_model.update_password(self.usuario["id"], password)
            if rol_row:
                usuario_model.update_rol_id(self.usuario["id"], rol_row["id"])
        else:
            if usuario_model.username_exists(username):
                messagebox.showwarning(
                    "Error", "Ese nombre de usuario ya existe.", parent=self)
                return
            usuario_model.create(username, password, rol_nombre)

        if self.on_done:
            self.on_done()
        self.grab_release()
        self.destroy()

    def _cancel(self):
        self.grab_release()
        self.destroy()

    def _toggle_activo(self):
        usuario_model.toggle_activo(self.usuario["id"])
        if self.on_done:
            self.on_done()
        self.grab_release()
        self.destroy()


# ─────────────────────────────────────────────────────────────────────────────
# Main view (tabbed: Usuarios + Roles)
# ─────────────────────────────────────────────────────────────────────────────

class UsuariosView(ctk.CTkFrame):
    def __init__(self, master, app, usuario_actual: dict):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.usuario_actual = usuario_actual
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._build_ui()

    def _build_ui(self):
        self._tabs = ctk.CTkTabview(self)
        self._tabs.grid(row=0, column=0, padx=24, pady=20, sticky="nsew")
        self._tabs.add("Usuarios")
        self._tabs.add("Roles")
        self._build_usuarios_tab(self._tabs.tab("Usuarios"))
        self._build_roles_tab(self._tabs.tab("Roles"))

    def _build_usuarios_tab(self, parent):
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(parent, fg_color="transparent")
        header.grid(row=0, column=0, pady=(8, 6), sticky="ew")
        header.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(header, text="Usuarios",
                     font=ctk.CTkFont(size=20, weight="bold")).grid(
            row=0, column=0, sticky="w")
        ctk.CTkButton(header, text="+ Nuevo usuario",
                      command=self._nuevo_usuario).grid(row=0, column=2)

        self._users_scroll = ctk.CTkScrollableFrame(parent)
        self._users_scroll.grid(row=1, column=0, sticky="nsew")
        self._users_scroll.grid_columnconfigure(0, weight=1)

    def _build_roles_tab(self, parent):
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(parent, fg_color="transparent")
        header.grid(row=0, column=0, pady=(8, 6), sticky="ew")
        header.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(header, text="Roles",
                     font=ctk.CTkFont(size=20, weight="bold")).grid(
            row=0, column=0, sticky="w")
        ctk.CTkButton(header, text="+ Nuevo rol",
                      command=self._nuevo_rol).grid(row=0, column=2)

        self._roles_scroll = ctk.CTkScrollableFrame(parent)
        self._roles_scroll.grid(row=1, column=0, sticky="nsew")
        self._roles_scroll.grid_columnconfigure(0, weight=1)

    def refresh(self, **kwargs):
        self._load_usuarios()
        self._load_roles()

    def _load_usuarios(self):
        for w in self._users_scroll.winfo_children():
            w.destroy()
        for u in usuario_model.get_all():
            self._make_usuario_row(u)

    def _load_roles(self):
        for w in self._roles_scroll.winfo_children():
            w.destroy()
        for r in rol_model.get_all():
            self._make_rol_row(r)

    def _make_usuario_row(self, u: dict):
        row = ctk.CTkFrame(self._users_scroll, corner_radius=8)
        row.pack(fill="x", pady=4)
        row.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(row, text=u["username"],
                     font=ctk.CTkFont(size=13, weight="bold"), anchor="w").grid(
            row=0, column=0, padx=14, pady=12, sticky="w")

        rol_color = "#7b2d8b" if u["rol_nombre"] == "superadmin" else "#1d3557"
        ctk.CTkLabel(row, text=f"  {u['rol_nombre']}  ",
                     fg_color=rol_color, corner_radius=6,
                     font=ctk.CTkFont(size=11)).grid(
            row=0, column=1, padx=8, pady=12, sticky="w")

        ctk.CTkLabel(
            row,
            text="  activo  " if u["activo"] else "  inactivo  ",
            fg_color="#2d6a4f" if u["activo"] else "gray40",
            corner_radius=6, font=ctk.CTkFont(size=11)
        ).grid(row=0, column=2, padx=4, pady=12)

        if u["id"] == self.usuario_actual["id"]:
            ctk.CTkLabel(row, text="  vos  ",
                         fg_color="#f4a261", corner_radius=6,
                         text_color="black",
                         font=ctk.CTkFont(size=11)).grid(
                row=0, column=3, padx=4, pady=12)

        ctk.CTkButton(row, text="Editar", width=90,
                      command=lambda uid=u["id"]: self._editar_usuario(uid)).grid(
            row=0, column=4, padx=12, pady=10)

    def _make_rol_row(self, r: dict):
        row = ctk.CTkFrame(self._roles_scroll, corner_radius=8)
        row.pack(fill="x", pady=4)
        row.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(row, text=r["nombre"],
                     font=ctk.CTkFont(size=13, weight="bold"), anchor="w").grid(
            row=0, column=0, padx=14, pady=12, sticky="w")

        perms_on = [k for k in rol_model.PERMISOS_KEYS if r.get(k)]
        perm_text = ", ".join(perms_on) if perms_on else "(sin permisos)"
        ctk.CTkLabel(row, text=perm_text, text_color="gray60",
                     font=ctk.CTkFont(size=11), anchor="w").grid(
            row=0, column=1, padx=8, pady=12, sticky="w")

        ctk.CTkButton(row, text="Editar", width=90,
                      command=lambda rid=r["id"]: self._editar_rol(rid)).grid(
            row=0, column=2, padx=12, pady=10)

    def _nuevo_usuario(self):
        dlg = UsuarioFormDialog(self, on_done=self._load_usuarios)
        self.wait_window(dlg)

    def _editar_usuario(self, usuario_id: int):
        u = usuario_model.get_by_id(usuario_id)
        dlg = UsuarioFormDialog(self, usuario=u,
                                usuario_actual=self.usuario_actual,
                                on_done=self._load_usuarios)
        self.wait_window(dlg)

    def _nuevo_rol(self):
        dlg = RolFormDialog(self, on_done=self._load_roles)
        self.wait_window(dlg)

    def _editar_rol(self, rol_id: int):
        r = rol_model.get_by_id(rol_id)
        dlg = RolFormDialog(self, rol=r, on_done=self._load_roles)
        self.wait_window(dlg)
