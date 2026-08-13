from __future__ import annotations
from tkinter import messagebox, filedialog
import customtkinter as ctk

import models.producto as producto_model
from utils.label_pdf import generate_labels_pdf
from utils.ui import debounce


# ─────────────────────────────────────────────────────────────────────────────
# Etiquetas view
# ─────────────────────────────────────────────────────────────────────────────

class EtiquetasView(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self._productos: list[dict] = []
        self._check_vars: dict[int, ctk.BooleanVar] = {}
        self._cant_vars:  dict[int, ctk.IntVar] = {}
        self._search_after = None
        self._build_ui()

    def _build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, padx=24, pady=(20, 8), sticky="ew")
        header.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(header, text="🏷️  Etiquetas de Precio",
                     font=ctk.CTkFont(size=22, weight="bold")).grid(
            row=0, column=0, sticky="w")

        btn_frame = ctk.CTkFrame(header, fg_color="transparent")
        btn_frame.grid(row=0, column=2)

        ctk.CTkButton(btn_frame, text="Seleccionar todos",
                      fg_color="transparent", border_width=1,
                      text_color=("gray10", "gray90"), width=140,
                      command=self._select_all).pack(side="left", padx=(0, 6))
        ctk.CTkButton(btn_frame, text="Limpiar",
                      fg_color="transparent", border_width=1,
                      text_color=("gray10", "gray90"), width=80,
                      command=self._clear_all).pack(side="left", padx=(0, 8))
        ctk.CTkButton(btn_frame, text="🖨️ Generar PDF",
                      command=self._generar_pdf).pack(side="left")

        # Search + info
        filter_row = ctk.CTkFrame(self, fg_color="transparent")
        filter_row.grid(row=1, column=0, padx=24, pady=(0, 8), sticky="ew")
        filter_row.grid_columnconfigure(0, weight=1)

        search_frame = ctk.CTkFrame(filter_row, fg_color="transparent")
        search_frame.grid(row=0, column=0, sticky="ew")
        search_frame.grid_columnconfigure(0, weight=1)

        self._search_var = ctk.StringVar()
        ctk.CTkEntry(search_frame, textvariable=self._search_var,
                     placeholder_text="Buscar producto...").grid(
            row=0, column=0, padx=(0, 8), sticky="ew")
        self._search_var.trace_add(
            "write",
            lambda *_: debounce(self, "_search_after", 250, self._load),
        )

        self._info_label = ctk.CTkLabel(filter_row, text="0 etiquetas seleccionadas",
                                         text_color="gray60",
                                         font=ctk.CTkFont(size=12))
        self._info_label.grid(row=1, column=0, pady=(4, 0), sticky="w")

        # Column headers
        cols = ctk.CTkFrame(self, fg_color="transparent")
        cols.grid(row=1, column=0, padx=28, pady=(40, 0), sticky="ew")
        cols.grid_columnconfigure(2, weight=1)
        for col, text, width in [
            (0, "", 36), (1, "Stock", 52),
            (2, "Nombre / Detalle", 0), (3, "Precio", 80), (4, "Cantidad", 90),
        ]:
            ctk.CTkLabel(cols, text=text, text_color="gray60",
                         font=ctk.CTkFont(size=11), width=width).grid(
                row=0, column=col, padx=4, sticky="w")

        # Scrollable list
        self._scroll = ctk.CTkScrollableFrame(self)
        self._scroll.grid(row=2, column=0, padx=24, pady=(0, 20), sticky="nsew")
        self._scroll.grid_columnconfigure(0, weight=1)

    def refresh(self, **kwargs):
        self._search_var.set("")
        self._load()

    def _load(self):
        texto = self._search_var.get().strip()
        if texto:
            self._productos = producto_model.search(texto, activos_only=True, limit=150)
        else:
            self._productos = producto_model.get_all(activos_only=True, limit=150)

        # Preserve existing selections/quantities
        old_checks = {pid: v.get() for pid, v in self._check_vars.items()}
        old_cants  = {pid: v.get() for pid, v in self._cant_vars.items()}

        self._check_vars.clear()
        self._cant_vars.clear()

        for w in self._scroll.winfo_children():
            w.destroy()

        if not self._productos:
            ctk.CTkLabel(self._scroll, text="No hay productos.",
                         text_color="gray60").pack(pady=20)
            return

        for p in self._productos:
            pid = p["id"]
            self._check_vars[pid] = ctk.BooleanVar(value=old_checks.get(pid, False))
            self._cant_vars[pid]  = ctk.IntVar(value=max(1, old_cants.get(pid, 1)))
            self._make_row(p)

        self._update_info()

    def _make_row(self, p: dict):
        pid = p["id"]
        row = ctk.CTkFrame(self._scroll, corner_radius=8)
        row.pack(fill="x", pady=2)
        row.grid_columnconfigure(2, weight=1)

        ctk.CTkCheckBox(
            row, text="", variable=self._check_vars[pid],
            command=self._update_info, width=36
        ).grid(row=0, column=0, padx=(12, 4), pady=10)

        stock = p["stock"]
        if stock == 0:
            sc, st = "#e63946", "0"
        elif stock <= 3:
            sc, st = "#f4a261", str(stock)
        else:
            sc, st = "#2d6a4f", str(stock)
        ctk.CTkLabel(row, text=f" {st} ", fg_color=sc, corner_radius=6,
                     font=ctk.CTkFont(size=11, weight="bold"), width=48).grid(
            row=0, column=1, padx=4, pady=10)

        name_frame = ctk.CTkFrame(row, fg_color="transparent")
        name_frame.grid(row=0, column=2, padx=4, pady=8, sticky="w")
        ctk.CTkLabel(name_frame, text=p["nombre"],
                     font=ctk.CTkFont(size=12, weight="bold"), anchor="w").pack(anchor="w")
        parts = []
        if p.get("talle"):
            parts.append(f"T:{p['talle']}")
        if p.get("color"):
            parts.append(p["color"])
        if parts:
            ctk.CTkLabel(name_frame, text=" · ".join(parts),
                         text_color="gray60", font=ctk.CTkFont(size=10)).pack(anchor="w")

        ctk.CTkLabel(row, text=f"Gs. {p['precio']:,.2f}",
                     font=ctk.CTkFont(size=12, weight="bold"), width=80).grid(
            row=0, column=3, padx=8, pady=10)

        spin_frame = ctk.CTkFrame(row, fg_color="transparent")
        spin_frame.grid(row=0, column=4, padx=(4, 12), pady=8)

        ctk.CTkButton(spin_frame, text="−", width=28,
                      command=lambda v=self._cant_vars[pid]: (
                          v.set(max(1, v.get() - 1)), self._update_info()
                      )).pack(side="left")
        ctk.CTkLabel(spin_frame, textvariable=self._cant_vars[pid],
                     width=32, anchor="center").pack(side="left")
        ctk.CTkButton(spin_frame, text="+", width=28,
                      command=lambda v=self._cant_vars[pid]: (
                          v.set(v.get() + 1), self._update_info()
                      )).pack(side="left")

    def _select_all(self):
        for v in self._check_vars.values():
            v.set(True)
        self._update_info()

    def _clear_all(self):
        for v in self._check_vars.values():
            v.set(False)
        self._update_info()

    def _update_info(self):
        total = sum(
            self._cant_vars[pid].get()
            for pid, v in self._check_vars.items()
            if v.get()
        )
        self._info_label.configure(text=f"{total} etiqueta(s) seleccionada(s)")

    def _generar_pdf(self):
        items = [
            {"producto": p, "cantidad": self._cant_vars[p["id"]].get()}
            for p in self._productos
            if self._check_vars.get(p["id"], ctk.BooleanVar()).get()
        ]
        if not items:
            messagebox.showwarning("Atención",
                                   "Seleccioná al menos un producto.", parent=self)
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
            initialfile="etiquetas",
            parent=self,
        )
        if not path:
            return
        try:
            generate_labels_pdf(path, items)
            messagebox.showinfo("Listo", f"PDF generado en:\n{path}", parent=self)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo generar el PDF:\n{e}", parent=self)
