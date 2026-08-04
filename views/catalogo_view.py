from __future__ import annotations
from tkinter import messagebox, filedialog
import customtkinter as ctk
from pathlib import Path

import models.producto as producto_model
import models.categoria as categoria_model
from utils.catalog_export import export_catalog_html, export_catalog_excel


# ─────────────────────────────────────────────────────────────────────────────
# Catálogo view
# ─────────────────────────────────────────────────────────────────────────────

class CatalogoView(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self._productos: list[dict] = []
        self._whatsapp: str = ""
        self._build_ui()

    def _build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, padx=24, pady=(20, 8), sticky="ew")
        header.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(header, text="🛍️  Catálogo Online",
                     font=ctk.CTkFont(size=22, weight="bold")).grid(
            row=0, column=0, sticky="w")

        btn_frame = ctk.CTkFrame(header, fg_color="transparent")
        btn_frame.grid(row=0, column=2)
        ctk.CTkButton(btn_frame, text="Exportar HTML",
                      command=self._export_html).pack(side="left", padx=(0, 8))
        ctk.CTkButton(btn_frame, text="Exportar Excel (ML/TN)",
                      fg_color="transparent", border_width=1,
                      text_color=("gray10", "gray90"),
                      command=self._export_excel).pack(side="left")

        # Config + filters
        config = ctk.CTkFrame(self, fg_color="transparent")
        config.grid(row=1, column=0, padx=24, pady=(0, 8), sticky="ew")

        ctk.CTkLabel(config, text="WhatsApp tienda:").pack(side="left", padx=(0, 6))
        self._wa_var = ctk.StringVar()
        ctk.CTkEntry(config, textvariable=self._wa_var,
                     placeholder_text="+5491100000000", width=160).pack(
            side="left", padx=(0, 16))

        self._cat_var = ctk.StringVar(value="(Todas)")
        self._cat_combo = ctk.CTkComboBox(
            config, values=["(Todas)"], variable=self._cat_var,
            width=150, command=lambda _: self._load()
        )
        self._cat_combo.pack(side="left", padx=(0, 8))

        self._solo_stock_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(config, text="Solo con stock",
                        variable=self._solo_stock_var,
                        command=self._load).pack(side="left", padx=(0, 8))

        self._solo_activos_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(config, text="Solo activos",
                        variable=self._solo_activos_var,
                        command=self._load).pack(side="left")

        self._info_label = ctk.CTkLabel(config, text="",
                                         text_color="gray60",
                                         font=ctk.CTkFont(size=12))
        self._info_label.pack(side="left", padx=(12, 0))

        # Scrollable product grid
        self._scroll = ctk.CTkScrollableFrame(self)
        self._scroll.grid(row=2, column=0, padx=24, pady=(0, 20), sticky="nsew")
        self._scroll.grid_columnconfigure(0, weight=1)

    def refresh(self, **kwargs):
        self._update_cat_combo()
        self._load()

    def _update_cat_combo(self):
        cats = categoria_model.get_all(activos_only=True)
        self._cat_combo.configure(
            values=["(Todas)"] + [c["nombre"] for c in cats]
        )

    def _load(self):
        activos_only = self._solo_activos_var.get()
        self._productos = producto_model.get_all(activos_only=activos_only)

        cat_f = self._cat_var.get()
        if cat_f and cat_f != "(Todas)":
            self._productos = [
                p for p in self._productos
                if p.get("categoria_nombre") == cat_f
            ]

        if self._solo_stock_var.get():
            self._productos = [p for p in self._productos if p.get("stock", 0) > 0]

        self._info_label.configure(
            text=f"{len(self._productos)} producto(s)"
        )
        self._render_grid()

    def _render_grid(self):
        for w in self._scroll.winfo_children():
            w.destroy()

        if not self._productos:
            ctk.CTkLabel(self._scroll, text="No hay productos.",
                         text_color="gray60").pack(pady=20)
            return

        # Simple list view (grid with thumbnail)
        for p in self._productos:
            self._make_card(p)

    def _make_card(self, p: dict):
        card = ctk.CTkFrame(self._scroll, corner_radius=8)
        card.pack(fill="x", pady=3)
        card.grid_columnconfigure(1, weight=1)

        # Miniatura
        thumb_frame = ctk.CTkFrame(card, width=56, height=56,
                                    fg_color="gray20", corner_radius=6)
        thumb_frame.grid(row=0, column=0, padx=10, pady=8, rowspan=2)
        thumb_frame.grid_propagate(False)

        foto_path = p.get("foto_path", "")
        if foto_path and Path(foto_path).exists():
            try:
                from PIL import Image
                import customtkinter as ctk2
                img = Image.open(foto_path).resize((52, 52))
                ctk_img = ctk2.CTkImage(img, size=(52, 52))
                ctk.CTkLabel(thumb_frame, image=ctk_img, text="").place(
                    relx=0.5, rely=0.5, anchor="center")
            except Exception:
                ctk.CTkLabel(thumb_frame, text="🛍️", font=ctk.CTkFont(size=20)).place(
                    relx=0.5, rely=0.5, anchor="center")
        else:
            ctk.CTkLabel(thumb_frame, text="🛍️", font=ctk.CTkFont(size=20)).place(
                relx=0.5, rely=0.5, anchor="center")

        # Name + details
        ctk.CTkLabel(card, text=p["nombre"],
                     font=ctk.CTkFont(size=12, weight="bold"), anchor="w").grid(
            row=0, column=1, padx=4, pady=(10, 2), sticky="w")

        parts = []
        if p.get("categoria_nombre"):
            parts.append(p["categoria_nombre"])
        if p.get("talle"):
            parts.append(f"T:{p['talle']}")
        if p.get("color"):
            parts.append(p["color"])
        if parts:
            ctk.CTkLabel(card, text="  ·  ".join(parts),
                         text_color="gray60", font=ctk.CTkFont(size=11),
                         anchor="w").grid(
                row=1, column=1, padx=4, pady=(0, 10), sticky="w")

        # Price
        ctk.CTkLabel(card, text=f"${p['precio']:,.2f}",
                     font=ctk.CTkFont(size=13, weight="bold")).grid(
            row=0, column=2, padx=12, pady=10, rowspan=2)

        # Stock badge
        stock = p.get("stock", 0)
        if stock == 0:
            ctk.CTkLabel(card, text="  Sin stock  ",
                         fg_color="#e63946", corner_radius=6,
                         font=ctk.CTkFont(size=10)).grid(
                row=0, column=3, padx=(0, 12), pady=10, rowspan=2)

    def _get_filtered_productos(self) -> list[dict]:
        return self._productos

    def _export_html(self):
        productos = self._get_filtered_productos()
        if not productos:
            messagebox.showwarning("Atención", "No hay productos para exportar.", parent=self)
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".html",
            filetypes=[("HTML files", "*.html"), ("All files", "*.*")],
            initialfile="catalogo",
            parent=self,
        )
        if not path:
            return
        wa = self._wa_var.get().strip()
        try:
            export_catalog_html(productos, path, whatsapp=wa)
            messagebox.showinfo("Listo", f"Catálogo HTML guardado en:\n{path}", parent=self)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo exportar:\n{e}", parent=self)

    def _export_excel(self):
        productos = self._get_filtered_productos()
        if not productos:
            messagebox.showwarning("Atención", "No hay productos para exportar.", parent=self)
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
            initialfile="catalogo",
            parent=self,
        )
        if not path:
            return
        try:
            export_catalog_excel(productos, path)
            messagebox.showinfo("Listo", f"Catálogo Excel guardado en:\n{path}", parent=self)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo exportar:\n{e}", parent=self)
