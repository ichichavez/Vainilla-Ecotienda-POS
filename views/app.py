from __future__ import annotations
from pathlib import Path
import customtkinter as ctk

import views.theme as theme
from views.dashboard import DashboardView
from views.nueva_venta import NuevaVentaView
from views.clientes_view import ClientesView
from views.productos_view import ProductosView
from views.caja_view import CajaView
from views.compras_view import ComprasView
from views.categorias_view import CategoriasView
from views.usuarios_view import UsuariosView
from views.reportes_view import ReportesView
from views.movimientos_view import MovimientosView
from views.gastos_view      import GastosView
from views.etiquetas_view   import EtiquetasView
from views.catalogo_view          import CatalogoView
from views.cajas_proveedor_view   import CajasProveedorView

# (view_name, permiso_key, label)
NAV_MAP = [
    ("dashboard",   "dashboard",   "🏠  Inicio"),
    ("nueva_venta", "ventas",      "🛒  Nueva Venta"),
    ("clientes",    "clientes",    "👥  Clientes"),
    ("productos",   "productos",   "📦  Productos"),
    ("caja",        "caja",        "💰  Caja del Día"),
    ("compras",     "compras",     "📥  Compras"),
    ("categorias",  "categorias",  "📁  Categorías"),
    ("usuarios",    "usuarios",    "👤  Usuarios"),
    ("reportes",    "reportes",    "📊  Reportes"),
    ("movimientos", "movimientos", "📋  Movimientos"),
    ("gastos",      "gastos",      "💸  Gastos"),
    ("etiquetas",        "etiquetas",   "🏷️  Etiquetas"),
    ("catalogo",         "catalogo",    "🛍️  Catálogo"),
    ("cajas_proveedor",  "compras",     "📦  Cajas proveedor"),
]

_VIEW_FACTORIES = {
    "dashboard":   lambda content, app: DashboardView(content, app),
    "nueva_venta": lambda content, app: NuevaVentaView(content, app),
    "clientes":    lambda content, app: ClientesView(content, app),
    "productos":   lambda content, app: ProductosView(content, app),
    "caja":        lambda content, app: CajaView(content, app),
    "compras":     lambda content, app: ComprasView(content, app),
    "categorias":  lambda content, app: CategoriasView(content, app),
    "usuarios":    lambda content, app: UsuariosView(content, app, app.usuario),
    "reportes":    lambda content, app: ReportesView(content, app),
    "movimientos": lambda content, app: MovimientosView(content, app),
    "gastos":      lambda content, app: GastosView(content, app),
    "etiquetas":       lambda content, app: EtiquetasView(content, app),
    "catalogo":        lambda content, app: CatalogoView(content, app),
    "cajas_proveedor": lambda content, app: CajasProveedorView(content, app),
}


class App(ctk.CTk):
    def __init__(self, usuario: dict):
        super().__init__()
        self.usuario = usuario
        self._logout_requested = False
        self._theme = "Light"
        self._current_view: str | None = None
        self._views_ready: set[str] = set()
        self._dirty_views: set[str] = set()
        self._nav_font = ctk.CTkFont(size=theme.FONT_BASE)
        self._nav_font_active = ctk.CTkFont(size=theme.FONT_BASE, weight="bold")

        self.title("Punto de Venta · Analia")
        self.geometry("1200x720")
        self.minsize(960, 640)

        self._build_layout()
        self._build_sidebar()
        self._build_views()

        # Navigate to first available view
        first = next(iter(self._view_factories), None)
        if first:
            self.show_view(first)

        self.lift()
        self.focus_force()

    # ── Layout ───────────────────────────────────────────────────────────────

    def _build_layout(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = ctk.CTkFrame(self, width=210, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_columnconfigure(0, weight=1)

        self.content = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

    def _build_sidebar(self):
        # ── Logo ──
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_frame.grid(row=0, column=0, padx=20, pady=(24, 16), sticky="w")
        ctk.CTkLabel(
            logo_frame, text="●",
            font=ctk.CTkFont(size=10), text_color=theme.PRIMARY
        ).grid(row=0, column=0, padx=(0, 6), sticky="w")
        ctk.CTkLabel(
            logo_frame, text="Analia",
            font=ctk.CTkFont(size=20, weight="bold")
        ).grid(row=0, column=1, sticky="w")
        ctk.CTkLabel(
            logo_frame, text="PUNTO DE VENTA",
            font=ctk.CTkFont(size=theme.FONT_XS), text_color="gray50"
        ).grid(row=1, column=0, columnspan=2, sticky="w")

        ctk.CTkFrame(self.sidebar, height=1, fg_color="gray30").grid(
            row=2, column=0, padx=16, pady=(0, 8), sticky="ew")

        # ── Nav buttons (only permitted views) ──
        permisos = self.usuario["permisos"]
        self.nav_buttons: dict[str, ctk.CTkButton] = {}
        nav_row = 3
        for view_name, perm_key, label in NAV_MAP:
            if permisos.get(perm_key):
                btn = ctk.CTkButton(
                    self.sidebar,
                    text=label,
                    anchor="w",
                    height=40,
                    corner_radius=8,
                    fg_color="transparent",
                    text_color=("gray10", "gray90"),
                    hover_color=("gray75", "gray25"),
                    font=ctk.CTkFont(size=13),
                    command=lambda v=view_name: self.show_view(v),
                )
                btn.grid(row=nav_row, column=0, padx=10, pady=1, sticky="ew")
                self.nav_buttons[view_name] = btn
                nav_row += 1

        # ── Spacer ──
        self.sidebar.grid_rowconfigure(50, weight=1)

        ctk.CTkFrame(self.sidebar, height=1, fg_color="gray30").grid(
            row=51, column=0, padx=16, pady=(0, 8), sticky="ew")

        # ── User info ──
        user_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        user_frame.grid(row=52, column=0, padx=14, pady=(0, 4), sticky="ew")
        user_frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(user_frame, text=self.usuario["username"],
                     font=ctk.CTkFont(size=12, weight="bold"), anchor="w").grid(
            row=0, column=0, sticky="w")
        ctk.CTkLabel(user_frame, text=self.usuario["rol_nombre"],
                     font=ctk.CTkFont(size=10), text_color="gray60", anchor="w").grid(
            row=1, column=0, sticky="w")

        # ── Theme toggle ──
        self._theme_btn = ctk.CTkButton(
            self.sidebar,
            text="🌙  Modo oscuro",
            anchor="w",
            height=36,
            corner_radius=8,
            fg_color="transparent",
            text_color=("gray10", "gray90"),
            hover_color=("gray75", "gray25"),
            font=ctk.CTkFont(size=12),
            command=self._toggle_theme,
        )
        self._theme_btn.grid(row=53, column=0, padx=10, pady=2, sticky="ew")

        # ── Backup / Import DB (superadmin) ──
        db_row = 54
        if self.usuario.get("rol_nombre") == "superadmin":
            ctk.CTkButton(
                self.sidebar,
                text="💾  Respaldar base",
                anchor="w",
                height=36,
                corner_radius=8,
                fg_color="transparent",
                text_color=("gray10", "gray90"),
                hover_color=("gray75", "gray25"),
                font=ctk.CTkFont(size=12),
                command=self._backup_database,
            ).grid(row=db_row, column=0, padx=10, pady=2, sticky="ew")
            db_row += 1
            ctk.CTkButton(
                self.sidebar,
                text="📥  Importar base",
                anchor="w",
                height=36,
                corner_radius=8,
                fg_color="transparent",
                text_color=("gray10", "gray90"),
                hover_color=("gray75", "gray25"),
                font=ctk.CTkFont(size=12),
                command=self._import_database,
            ).grid(row=db_row, column=0, padx=10, pady=2, sticky="ew")
            db_row += 1

        # ── Logout ──
        ctk.CTkButton(
            self.sidebar,
            text="🚪  Cerrar sesión",
            anchor="w",
            height=36,
            corner_radius=8,
            fg_color="transparent",
            text_color="#e63946",
            hover_color=("gray75", "gray25"),
            font=ctk.CTkFont(size=12),
            command=self._logout,
        ).grid(row=db_row, column=0, padx=10, pady=(2, 14), sticky="ew")

    def _build_views(self):
        permisos = self.usuario["permisos"]
        # Lazy: only create views when first opened (faster startup).
        self._view_factories: dict[str, object] = {}
        self.views: dict[str, ctk.CTkFrame] = {}
        for view_name, perm_key, _ in NAV_MAP:
            if permisos.get(perm_key):
                self._view_factories[view_name] = _VIEW_FACTORIES[view_name]

    # ── Navigation ───────────────────────────────────────────────────────────

    def mark_data_changed(self, *view_names: str) -> None:
        """Mark views stale so they refresh on next visit."""
        self._dirty_views.update(view_names)

    def _ensure_view(self, view_name: str) -> ctk.CTkFrame:
        if view_name not in self.views:
            factory = self._view_factories[view_name]
            view = factory(self.content, self)
            view.grid(row=0, column=0, sticky="nsew")
            self.views[view_name] = view
        return self.views[view_name]

    def show_view(self, view_name: str, force: bool = False, **kwargs):
        for name, btn in self.nav_buttons.items():
            if name == view_name:
                btn.configure(
                    fg_color=theme.PRIMARY_LIGHT,
                    text_color=theme.PRIMARY_TEXT,
                    font=self._nav_font_active,
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=("gray10", "gray90"),
                    font=self._nav_font,
                )
        view = self._ensure_view(view_name)
        view.tkraise()
        first_visit = view_name not in self._views_ready
        if force or first_visit or view_name in self._dirty_views:
            view.refresh(force=force, **kwargs)
            self._views_ready.add(view_name)
            self._dirty_views.discard(view_name)
        self._current_view = view_name

    def navigate_to_cliente(self, cliente_id: int):
        if "clientes" not in self._view_factories:
            return
        self.show_view("clientes")
        self.views["clientes"].open_detalle(cliente_id)

    # ── Theme ────────────────────────────────────────────────────────────────

    def _toggle_theme(self):
        self._theme = "Light" if self._theme == "Dark" else "Dark"
        ctk.set_appearance_mode(self._theme)
        if self._theme == "Light":
            self._theme_btn.configure(text="🌙  Modo oscuro")
        else:
            self._theme_btn.configure(text="☀️  Modo claro")

    def _backup_database(self):
        from tkinter import filedialog, messagebox
        from utils.backup import backup_full

        parent = filedialog.askdirectory(
            parent=self,
            title="Elegí dónde crear la carpeta de respaldo completo",
        )
        if not parent:
            return
        try:
            result = backup_full(parent)
            c = result["counts"]
            resumen = (
                f"Productos: {c.get('productos', 0)}  ·  "
                f"Clientes: {c.get('clientes', 0)}  ·  "
                f"Ventas: {c.get('ventas', 0)}  ·  "
                f"Usuarios: {c.get('usuarios', 0)}"
            )
            fotos = ""
            if result["photos"]:
                fotos = f"\n\nFotos de productos:\n{result['photos']}"
            messagebox.showinfo(
                "Respaldo completo listo",
                f"Carpeta creada:\n{result['folder']}\n\n"
                f"Incluye ventas.db con TODOS los datos:\n{resumen}{fotos}\n\n"
                "Para restaurar: Importar base y elegí ventas.db o la carpeta entera.",
                parent=self,
            )
        except Exception as e:
            messagebox.showerror(
                "Error al respaldar",
                f"No se pudo guardar el respaldo:\n{e}",
                parent=self,
            )

    def _import_database(self):
        from tkinter import filedialog, messagebox
        from utils.backup import import_database

        if self.usuario.get("rol_nombre") != "superadmin":
            messagebox.showerror(
                "Sin permiso",
                "Solo el superadmin puede importar la base de datos.",
                parent=self,
            )
            return

        if not messagebox.askyesno(
            "Importar base de datos",
            "Esto reemplazará TODOS los datos actuales (ventas, clientes, productos, etc.)\n"
            "con los del archivo de respaldo.\n\n"
            "Usuarios: solo se importan cuentas SUPERADMIN del respaldo.\n"
            "Vendedores u otros usuarios del respaldo NO se copian.\n\n"
            "Se guardará un respaldo de seguridad en backups\\ antes de continuar.\n\n"
            "¿Continuar?",
            parent=self,
        ):
            return

        path = filedialog.askdirectory(
            parent=self,
            title="Elegí la carpeta del respaldo (contiene ventas.db)",
        )
        if not path:
            path = filedialog.askopenfilename(
                parent=self,
                title="O elegí solo el archivo ventas.db",
                filetypes=[("SQLite DB", "*.db"), ("All files", "*.*")],
            )
        if not path:
            return

        try:
            safety, n_admins, photos = import_database(path)
        except Exception as e:
            messagebox.showerror(
                "Error al importar",
                f"No se pudo importar el respaldo:\n{e}",
                parent=self,
            )
            return

        extra = ""
        if safety:
            extra = f"\n\nRespaldo de seguridad:\n{safety}"
        if photos:
            extra += f"\n\nFotos restauradas:\n{photos}"
        messagebox.showinfo(
            "Importación completa",
            f"Datos importados correctamente (productos, clientes, ventas, etc.).\n"
            f"Superadmin importados: {n_admins}{extra}\n\n"
            "La sesión se cerrará. Volvé a entrar con el superadmin del respaldo.",
            parent=self,
        )
        self._logout()

    # ── Logout ───────────────────────────────────────────────────────────────

    def _logout(self):
        self._logout_requested = True
        self.destroy()
