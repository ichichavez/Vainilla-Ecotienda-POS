from __future__ import annotations
import customtkinter as ctk
from tkinter import messagebox

import models.usuario as usuario_model
from utils import icons


class LoginWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.resultado: dict | None = None
        self.title("Punto de Venta · Analia")
        self.geometry("420x480")
        self.resizable(False, False)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        if usuario_model.count() == 0:
            self._build_setup()
        else:
            self._build_login()

        # Forzar foco en la ventana y en el primer campo
        self.lift()
        self.focus_force()
        self.after(150, self._focus_first)

    def _focus_first(self):
        if hasattr(self, "_user_entry"):
            self._user_entry.focus_set()

    def _create_password_entry(
        self,
        parent,
        row: int,
        textvariable: ctk.StringVar,
        *,
        placeholder: str = "",
        pady: tuple[int, int] = (4, 6),
    ) -> ctk.CTkEntry:
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=row, column=0, padx=32, pady=pady, sticky="ew")
        frame.grid_columnconfigure(0, weight=1)

        entry = ctk.CTkEntry(
            frame,
            textvariable=textvariable,
            show="*",
            placeholder_text=placeholder,
        )
        entry.grid(row=0, column=0, sticky="ew")

        eye_icon = icons.get("eye")
        eye_off_icon = icons.get("eye_off")
        visible = {"on": False}

        def toggle_visibility():
            visible["on"] = not visible["on"]
            entry.configure(show="" if visible["on"] else "*")
            toggle_btn.configure(
                image=eye_off_icon if visible["on"] else eye_icon
            )

        toggle_btn = ctk.CTkButton(
            frame,
            image=eye_icon,
            text="",
            width=38,
            height=38,
            fg_color=("gray85", "gray25"),
            hover_color=("gray75", "gray35"),
            command=toggle_visibility,
        )
        toggle_btn.grid(row=0, column=1, padx=(6, 0))
        return entry

    # ── Login form ───────────────────────────────────────────────────────────

    def _build_login(self):
        card = ctk.CTkFrame(self, corner_radius=16)
        card.grid(row=0, column=0, padx=40, pady=40, sticky="nsew")
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(card, text="Analia",
                     font=ctk.CTkFont(size=34, weight="bold")).grid(
            row=0, column=0, padx=30, pady=(36, 4))
        ctk.CTkLabel(card, text="PUNTO DE VENTA",
                     font=ctk.CTkFont(size=11), text_color="gray60").grid(
            row=1, column=0, padx=30, pady=(0, 30))

        ctk.CTkLabel(card, text="Usuario", anchor="w").grid(
            row=2, column=0, padx=32, sticky="w")
        self._user_var = ctk.StringVar()
        self._user_entry = ctk.CTkEntry(card, textvariable=self._user_var,
                                        placeholder_text="nombre de usuario")
        self._user_entry.grid(row=3, column=0, padx=32, pady=(4, 14), sticky="ew")

        ctk.CTkLabel(card, text="Contraseña", anchor="w").grid(
            row=4, column=0, padx=32, sticky="w")
        self._pass_var = ctk.StringVar()
        pass_entry = self._create_password_entry(
            card, 5, self._pass_var, placeholder="contraseña"
        )
        pass_entry.bind("<Return>", lambda _: self._do_login())
        self._user_entry.bind("<Return>", lambda _: pass_entry.focus_set())

        self._error_lbl = ctk.CTkLabel(card, text="", text_color="#e63946",
                                       font=ctk.CTkFont(size=11))
        self._error_lbl.grid(row=6, column=0, padx=32, pady=(4, 0))

        ctk.CTkButton(card, text="Iniciar sesión", height=44,
                      font=ctk.CTkFont(size=14),
                      command=self._do_login).grid(
            row=7, column=0, padx=32, pady=(12, 36), sticky="ew")

    def _do_login(self):
        username = self._user_var.get().strip()
        password = self._pass_var.get()
        if not username or not password:
            self._error_lbl.configure(text="Completá usuario y contraseña.")
            return
        user = usuario_model.authenticate(username, password)
        if user:
            self.resultado = user
            self.destroy()
        else:
            self._error_lbl.configure(text="Usuario o contraseña incorrectos.")

    # ── First-time setup form ─────────────────────────────────────────────────

    def _build_setup(self):
        card = ctk.CTkFrame(self, corner_radius=16)
        card.grid(row=0, column=0, padx=40, pady=30, sticky="nsew")
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(card, text="Primera configuración",
                     font=ctk.CTkFont(size=20, weight="bold")).grid(
            row=0, column=0, padx=30, pady=(30, 4))
        ctk.CTkLabel(card, text="Creá el usuario superadmin",
                     font=ctk.CTkFont(size=12), text_color="gray60").grid(
            row=1, column=0, padx=30, pady=(0, 20))

        ctk.CTkLabel(card, text="Usuario", anchor="w").grid(
            row=2, column=0, padx=32, sticky="w")
        self._user_var = ctk.StringVar()
        self._user_entry = ctk.CTkEntry(card, textvariable=self._user_var)
        self._user_entry.grid(row=3, column=0, padx=32, pady=(4, 10), sticky="ew")

        ctk.CTkLabel(card, text="Contraseña", anchor="w").grid(
            row=4, column=0, padx=32, sticky="w")
        self._pass_var = ctk.StringVar()
        self._create_password_entry(card, 5, self._pass_var, pady=(4, 10))

        ctk.CTkLabel(card, text="Confirmar contraseña", anchor="w").grid(
            row=6, column=0, padx=32, sticky="w")
        self._pass2_var = ctk.StringVar()
        self._create_password_entry(card, 7, self._pass2_var, pady=(4, 6))

        self._error_lbl = ctk.CTkLabel(card, text="", text_color="#e63946",
                                       font=ctk.CTkFont(size=11))
        self._error_lbl.grid(row=8, column=0, padx=32, pady=(4, 0))

        ctk.CTkButton(card, text="Crear superusuario", height=44,
                      font=ctk.CTkFont(size=14),
                      command=self._do_setup).grid(
            row=9, column=0, padx=32, pady=(12, 30), sticky="ew")

    def _do_setup(self):
        username = self._user_var.get().strip()
        password = self._pass_var.get()
        password2 = self._pass2_var.get()
        if not username:
            self._error_lbl.configure(text="Ingresá un nombre de usuario.")
            return
        if len(password) < 4:
            self._error_lbl.configure(
                text="La contraseña debe tener al menos 4 caracteres.")
            return
        if password != password2:
            self._error_lbl.configure(text="Las contraseñas no coinciden.")
            return
        usuario_model.create(username, password, "superadmin")
        self.resultado = usuario_model.authenticate(username, password)
        self.destroy()
