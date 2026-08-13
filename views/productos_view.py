from __future__ import annotations
import customtkinter as ctk
from tkinter import messagebox, filedialog
import shutil
from pathlib import Path

import models.producto as producto_model
import models.categoria as categoria_model
from views.constants import LIST_BATCH_SIZE
from utils.ui import debounce, render_in_batches

ASSETS_DIR = Path(__file__).parent.parent / "assets" / "productos"


# ─────────────────────────────────────────────────────────────────────────────
# Product form dialog
# ─────────────────────────────────────────────────────────────────────────────

class ProductoFormDialog(ctk.CTkToplevel):
    """Dialog to create or edit a product."""

    def __init__(self, master, producto: dict | None = None, on_done=None):
        super().__init__(master)
        self.producto = producto
        self.on_done = on_done
        self.foto_path = producto["foto_path"] if producto else ""
        self.title("Editar producto" if producto else "Nuevo producto")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self._cancel)
        self.grab_set()
        self._build_ui()
        if producto:
            self._fill(producto)
        # Centrar en pantalla con tamaño fijo amplio
        self.update_idletasks()
        w, h = 520, 660
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    def _build_ui(self):
        # Contenedor principal con padding uniforme
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        container.grid(row=0, column=0, padx=0, pady=0, sticky="nsew")
        container.grid_columnconfigure(1, weight=1)

        fields = [
            ("Nombre *",          "nombre"),
            ("Marca",             "marca"),
            ("Descripción",       "descripcion"),
            ("Talle",             "talle"),
            ("Color",             "color"),
            ("Precio de costo",   "precio_costo"),
            ("Precio de venta *", "precio"),
            ("Stock *",           "stock"),
            ("Código de barras",  "codigo_barras"),
        ]
        self._vars: dict[str, ctk.StringVar] = {}
        for i, (label, key) in enumerate(fields):
            ctk.CTkLabel(container, text=label, anchor="w",
                         font=ctk.CTkFont(size=13)).grid(
                row=i, column=0, padx=(20, 8), pady=(8, 0), sticky="w")
            var = ctk.StringVar()
            ctk.CTkEntry(container, textvariable=var, height=36).grid(
                row=i, column=1, padx=(0, 20), pady=(8, 0), sticky="ew")
            self._vars[key] = var

        # Separador visual antes de categoría
        row_sep = len(fields)
        ctk.CTkFrame(container, height=1, fg_color="gray30").grid(
            row=row_sep, column=0, columnspan=2,
            padx=20, pady=(12, 4), sticky="ew")

        # Category
        row_cat = row_sep + 1
        ctk.CTkLabel(container, text="Categoría", anchor="w",
                     font=ctk.CTkFont(size=13)).grid(
            row=row_cat, column=0, padx=(20, 8), pady=(4, 0), sticky="w")
        categorias = categoria_model.get_all(activos_only=True)
        self._categorias_list = [{"id": None, "nombre": "(Sin categoría)"}] + categorias
        cat_nombres = [c["nombre"] for c in self._categorias_list]
        self._cat_var = ctk.StringVar(value="(Sin categoría)")
        ctk.CTkComboBox(container, values=cat_nombres, variable=self._cat_var,
                        height=36).grid(
            row=row_cat, column=1, padx=(0, 20), pady=(4, 0), sticky="ew")

        # Photo
        row_foto = row_cat + 1
        ctk.CTkLabel(container, text="Foto", anchor="w",
                     font=ctk.CTkFont(size=13)).grid(
            row=row_foto, column=0, padx=(20, 8), pady=(8, 0), sticky="w")
        foto_frame = ctk.CTkFrame(container, fg_color="transparent")
        foto_frame.grid(row=row_foto, column=1, padx=(0, 20), pady=(8, 0), sticky="ew")
        foto_frame.grid_columnconfigure(0, weight=1)
        self._foto_label = ctk.CTkLabel(foto_frame, text="(sin foto)",
                                        text_color="gray60", anchor="w")
        self._foto_label.grid(row=0, column=0, sticky="w")
        ctk.CTkButton(foto_frame, text="Seleccionar", width=110, height=32,
                      command=self._pick_photo).grid(row=0, column=1, padx=(8, 0))

        # ── Botones ──────────────────────────────────────────────────────────
        btn_row = row_foto + 1
        btn_frame = ctk.CTkFrame(container, fg_color="transparent")
        btn_frame.grid(row=btn_row, column=0, columnspan=2,
                       padx=20, pady=(16, 8), sticky="ew")
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

        if self.producto:
            ctk.CTkButton(container, text="Desactivar producto", height=36,
                          fg_color="#e63946", hover_color="#c1121f",
                          command=self._deactivate).grid(
                row=btn_row + 1, column=0, columnspan=2,
                padx=20, pady=(0, 16), sticky="ew")

    def _fill(self, p: dict):
        self._vars["nombre"].set(p["nombre"])
        self._vars["marca"].set(p.get("marca", ""))
        self._vars["descripcion"].set(p["descripcion"])
        self._vars["talle"].set(p["talle"])
        self._vars["color"].set(p["color"])
        self._vars["precio_costo"].set(str(p.get("precio_costo", 0) or 0))
        self._vars["precio"].set(str(p["precio"]))
        self._vars["stock"].set(str(p["stock"]))
        if p["foto_path"]:
            self._foto_label.configure(text=Path(p["foto_path"]).name)
            self.foto_path = p["foto_path"]
        if p.get("categoria_nombre"):
            self._cat_var.set(p["categoria_nombre"])
        self._vars["codigo_barras"].set(p.get("codigo_barras", ""))

    def _pick_photo(self):
        path = filedialog.askopenfilename(
            parent=self,
            title="Seleccionar foto",
            filetypes=[("Imágenes", "*.png *.jpg *.jpeg *.webp"), ("Todos", "*.*")]
        )
        if not path:
            return
        ASSETS_DIR.mkdir(parents=True, exist_ok=True)
        dest = ASSETS_DIR / Path(path).name
        shutil.copy2(path, dest)
        self.foto_path = str(dest)
        self._foto_label.configure(text=Path(path).name)

    def _save(self):
        nombre = self._vars["nombre"].get().strip()
        if not nombre:
            messagebox.showwarning("Atención", "El nombre es obligatorio.", parent=self)
            return
        try:
            precio_costo = float(
                self._vars["precio_costo"].get().replace(",", ".") or "0"
            )
            precio = float(self._vars["precio"].get().replace(",", "."))
            stock = int(self._vars["stock"].get())
        except ValueError:
            messagebox.showwarning("Atención",
                                   "Precio y stock deben ser números válidos.", parent=self)
            return

        cat_nombre = self._cat_var.get()
        cat = next(
            (c for c in self._categorias_list if c["nombre"] == cat_nombre), None)
        categoria_id = cat["id"] if cat else None

        codigo_barras = self._vars["codigo_barras"].get().strip()

        marca = self._vars["marca"].get().strip()

        if self.producto:
            producto_model.update(
                self.producto["id"],
                nombre,
                self._vars["descripcion"].get().strip(),
                self._vars["talle"].get().strip(),
                self._vars["color"].get().strip(),
                precio, stock, self.foto_path, categoria_id, codigo_barras,
                precio_costo, marca
            )
        else:
            producto_model.create(
                nombre,
                self._vars["descripcion"].get().strip(),
                self._vars["talle"].get().strip(),
                self._vars["color"].get().strip(),
                precio, stock, self.foto_path, categoria_id, codigo_barras,
                precio_costo, marca
            )

        if self.on_done:
            self.on_done()
        self.grab_release()
        self.destroy()

    def _cancel(self):
        self.grab_release()
        self.destroy()

    def _deactivate(self):
        if not messagebox.askyesno(
            "Confirmar",
            "¿Desactivar este producto? No aparecerá en el catálogo.",
            parent=self
        ):
            return
        producto_model.deactivate(self.producto["id"])
        if self.on_done:
            self.on_done()
        self.grab_release()
        self.destroy()


# ─────────────────────────────────────────────────────────────────────────────
# Main view
# ─────────────────────────────────────────────────────────────────────────────

class ProductosView(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self._search_after = None
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)
        self._build_ui()

    def _build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, padx=24, pady=(20, 8), sticky="ew")
        header.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(header, text="Productos",
                     font=ctk.CTkFont(size=24, weight="bold")).grid(
            row=0, column=0, sticky="w")
        ctk.CTkButton(header, text="+ Nuevo producto",
                      command=self._nuevo_producto).grid(row=0, column=2)

        # Filter bar
        filter_frame = ctk.CTkFrame(self, fg_color="transparent")
        filter_frame.grid(row=1, column=0, padx=24, pady=(0, 8), sticky="ew")
        filter_frame.grid_columnconfigure(0, weight=1)

        self._search_var = ctk.StringVar()
        ctk.CTkEntry(filter_frame, textvariable=self._search_var,
                     placeholder_text="Buscar por nombre, talle o color...").grid(
            row=0, column=0, padx=(0, 8), sticky="ew")
        self._search_var.trace_add(
            "write",
            lambda *_: debounce(self, "_search_after", 250, self._load),
        )

        self._cat_var = ctk.StringVar(value="(Todas)")
        self._cat_combo = ctk.CTkComboBox(
            filter_frame, values=["(Todas)"], variable=self._cat_var,
            width=160, command=lambda _: self._load())
        self._cat_combo.grid(row=0, column=1, padx=(0, 8))

        self._show_inactive_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(filter_frame, text="Mostrar inactivos",
                        variable=self._show_inactive_var,
                        command=self._load).grid(row=0, column=2)

        # Column headers
        cols = ctk.CTkFrame(self, fg_color="transparent")
        cols.grid(row=2, column=0, padx=28, pady=(0, 2), sticky="ew")
        cols.grid_columnconfigure(1, weight=1)
        for col, text, width in [
            (0, "Stock", 60), (1, "Nombre / Detalle", 0),
            (2, "Precio", 90), (3, "", 120)
        ]:
            ctk.CTkLabel(cols, text=text, text_color="gray60",
                         font=ctk.CTkFont(size=11), width=width).grid(
                row=0, column=col, padx=4, sticky="w")

        # Scrollable list
        self._scroll = ctk.CTkScrollableFrame(self)
        self._scroll.grid(row=3, column=0, padx=24, pady=(0, 20), sticky="nsew")
        self._scroll.grid_columnconfigure(0, weight=1)

    def refresh(self, force: bool = False, **kwargs):
        if force:
            self._search_var.set("")
            self._show_inactive_var.set(False)
            self._cat_var.set("(Todas)")
        self._update_cat_combo()
        self._load()

    def _update_cat_combo(self):
        categorias = categoria_model.get_all(activos_only=True)
        nombres = ["(Todas)"] + [c["nombre"] for c in categorias]
        self._cat_combo.configure(values=nombres)

    def _load(self):
        texto = self._search_var.get().strip()
        activos_only = not self._show_inactive_var.get()

        if texto:
            productos = producto_model.search(texto, activos_only=activos_only, limit=150)
        else:
            productos = producto_model.get_all(activos_only=activos_only, limit=150)

        cat_filter = self._cat_var.get()
        if cat_filter and cat_filter != "(Todas)":
            productos = [p for p in productos
                         if p.get("categoria_nombre") == cat_filter]

        for w in self._scroll.winfo_children():
            w.destroy()

        if not productos:
            ctk.CTkLabel(self._scroll, text="No hay productos.",
                         text_color="gray60").pack(pady=20)
            return

        render_in_batches(
            self, productos, LIST_BATCH_SIZE,
            lambda p, _i: self._make_row(p),
        )

    def _make_row(self, p: dict):
        row = ctk.CTkFrame(self._scroll, corner_radius=8)
        row.pack(fill="x", pady=3)
        row.grid_columnconfigure(1, weight=1)

        # Stock badge
        stock = p["stock"]
        if not p["activo"]:
            badge_color, badge_text = "gray40", "inactivo"
        elif stock == 0:
            badge_color, badge_text = "#e63946", "0"
        elif stock <= 3:
            badge_color, badge_text = "#f4a261", str(stock)
        else:
            badge_color, badge_text = "#2d6a4f", str(stock)

        ctk.CTkLabel(row, text=f" {badge_text} ",
                     fg_color=badge_color, corner_radius=6,
                     font=ctk.CTkFont(size=11, weight="bold"), width=48).grid(
            row=0, column=0, padx=(12, 8), pady=12, rowspan=2)

        # Name + details
        ctk.CTkLabel(row, text=p["nombre"],
                     font=ctk.CTkFont(size=13, weight="bold"), anchor="w").grid(
            row=0, column=1, padx=4, pady=(10, 1), sticky="w")

        detail_parts = []
        if p.get("categoria_nombre"):
            detail_parts.append(p["categoria_nombre"])
        if p.get("marca"):
            detail_parts.append(p["marca"])
        if p.get("talle"):
            detail_parts.append(f"Talle: {p['talle']}")
        if p.get("color"):
            detail_parts.append(p["color"])
        if p.get("descripcion"):
            detail_parts.append(p["descripcion"])

        if detail_parts:
            ctk.CTkLabel(row, text="  ·  ".join(detail_parts),
                         text_color="gray60", font=ctk.CTkFont(size=11),
                         anchor="w").grid(
                row=1, column=1, padx=4, pady=(0, 10), sticky="w")

        # Price + margin badge
        price_frame = ctk.CTkFrame(row, fg_color="transparent")
        price_frame.grid(row=0, column=2, padx=8, pady=8, rowspan=2)

        ctk.CTkLabel(price_frame, text=f"Gs. {p['precio']:,.2f}",
                     font=ctk.CTkFont(size=13, weight="bold")).pack()

        costo = p.get("precio_costo", 0) or 0
        if costo > 0:
            margen_pct = (p["precio"] - costo) / costo * 100
            if margen_pct >= 20:
                mc, mt = "#2d6a4f", f"+{margen_pct:.0f}%"
            elif margen_pct >= 0:
                mc, mt = "#f4a261", f"+{margen_pct:.0f}%"
            else:
                mc, mt = "#e63946", f"{margen_pct:.0f}%"
            ctk.CTkLabel(price_frame, text=f" {mt} ",
                         fg_color=mc, corner_radius=4,
                         font=ctk.CTkFont(size=9)).pack(pady=(2, 0))

        # Edit button
        ctk.CTkButton(row, text="Editar", width=90,
                      command=lambda prod=p: self._editar(prod)).grid(
            row=0, column=3, padx=12, pady=12, rowspan=2)

    def _nuevo_producto(self):
        dlg = ProductoFormDialog(self, on_done=self._after_product_change)
        self.wait_window(dlg)

    def _editar(self, producto: dict):
        dlg = ProductoFormDialog(self, producto=producto, on_done=self._after_product_change)
        self.wait_window(dlg)

    def _after_product_change(self):
        self.app.mark_data_changed(
            "productos", "catalogo", "etiquetas", "nueva_venta", "reportes",
        )
        self._load()
