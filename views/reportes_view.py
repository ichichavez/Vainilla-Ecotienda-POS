from __future__ import annotations
from datetime import date, datetime
from tkinter import messagebox
import customtkinter as ctk

import models.venta    as venta_model
import models.producto as producto_model
import models.compra   as compra_model
import models.gasto    as gasto_model
from utils.export import save_dialog, export_csv, export_excel


# ─── helpers ──────────────────────────────────────────────────────────────────

def _fmt_date(d: date) -> str:
    return d.strftime("%Y-%m-%d")

def _today() -> str:
    return _fmt_date(date.today())

def _first_of_month() -> str:
    today = date.today()
    return _fmt_date(today.replace(day=1))


# ─── DateEntry widget ─────────────────────────────────────────────────────────

class DateEntry(ctk.CTkFrame):
    """Simple YYYY-MM-DD entry with a label."""

    def __init__(self, parent, label: str, default: str = "", **kw):
        super().__init__(parent, fg_color="transparent", **kw)
        ctk.CTkLabel(self, text=label, font=ctk.CTkFont(size=13)).pack(side="left", padx=(0, 6))
        self._var = ctk.StringVar(value=default)
        ctk.CTkEntry(self, textvariable=self._var, width=120,
                     placeholder_text="AAAA-MM-DD").pack(side="left")

    def get(self) -> str:
        return self._var.get().strip()

    def set(self, value: str):
        self._var.set(value)


# ─── Preview table ────────────────────────────────────────────────────────────

class PreviewTable(ctk.CTkScrollableFrame):
    """Lightweight grid preview for export data."""

    CELL_PAD_X = 8
    CELL_PAD_Y = 3
    MAX_ROWS   = 200  # show at most this many rows in preview

    def __init__(self, parent, **kw):
        super().__init__(parent, **kw)

    def load(self, headers: list[str], rows: list[list]):
        # Clear previous widgets
        for w in self.winfo_children():
            w.destroy()

        font_h = ctk.CTkFont(size=11, weight="bold")
        font_d = ctk.CTkFont(size=11)

        for col, h in enumerate(headers):
            ctk.CTkLabel(self, text=h, font=font_h,
                         anchor="w").grid(row=0, column=col,
                                          padx=self.CELL_PAD_X,
                                          pady=self.CELL_PAD_Y, sticky="w")

        display_rows = rows[:self.MAX_ROWS]
        for row_idx, row in enumerate(display_rows, start=1):
            for col, val in enumerate(row):
                ctk.CTkLabel(self, text=str(val) if val is not None else "",
                             font=font_d, anchor="w").grid(
                    row=row_idx, column=col,
                    padx=self.CELL_PAD_X, pady=self.CELL_PAD_Y, sticky="w")

        if len(rows) > self.MAX_ROWS:
            ctk.CTkLabel(
                self,
                text=f"… y {len(rows) - self.MAX_ROWS} filas más (no se muestran en preview)",
                font=ctk.CTkFont(size=10), text_color="gray60"
            ).grid(row=len(display_rows) + 1, column=0,
                   columnspan=len(headers), pady=4, sticky="w")


# ─── Main view ────────────────────────────────────────────────────────────────

class ReportesView(ctk.CTkFrame):

    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Title
        ctk.CTkLabel(self, text="📊  Reportes",
                     font=ctk.CTkFont(size=20, weight="bold")).grid(
            row=0, column=0, padx=24, pady=(20, 8), sticky="w")

        # Tabs
        self._tabs = ctk.CTkTabview(self)
        self._tabs.grid(row=1, column=0, padx=16, pady=(0, 16), sticky="nsew")

        self._build_tab_caja()
        self._build_tab_rango()
        self._build_tab_inventario()
        self._build_tab_compras()
        self._build_tab_margenes()
        self._build_tab_gastos()

    # ── Tab 1: Caja del Día ───────────────────────────────────────────────────

    def _build_tab_caja(self):
        tab = self._tabs.add("Caja del Día")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(2, weight=1)

        # Controls row
        ctrl = ctk.CTkFrame(tab, fg_color="transparent")
        ctrl.grid(row=0, column=0, padx=8, pady=(8, 4), sticky="w")

        self._caja_date = DateEntry(ctrl, "Fecha:", default=_today())
        self._caja_date.pack(side="left", padx=(0, 16))

        ctk.CTkButton(ctrl, text="Exportar CSV",   width=130,
                      command=self._export_caja_csv).pack(side="left", padx=4)
        ctk.CTkButton(ctrl, text="Exportar Excel", width=130,
                      command=self._export_caja_xlsx).pack(side="left", padx=4)
        ctk.CTkButton(ctrl, text="Actualizar",     width=100,
                      fg_color="transparent",
                      border_width=1,
                      text_color=("gray10", "gray90"),
                      command=self._refresh_caja).pack(side="left", padx=(12, 4))

        # Info label
        self._caja_info = ctk.CTkLabel(tab, text="", font=ctk.CTkFont(size=12),
                                        text_color="gray60")
        self._caja_info.grid(row=1, column=0, padx=8, pady=(0, 4), sticky="w")

        # Preview
        self._caja_preview = PreviewTable(tab)
        self._caja_preview.grid(row=2, column=0, padx=8, pady=(0, 8), sticky="nsew")

        # Cache
        self._caja_headers: list = []
        self._caja_rows:    list = []

    def _get_caja_data(self) -> tuple[list, list]:
        fecha = self._caja_date.get()
        if not fecha:
            fecha = _today()
        ventas = venta_model.get_by_date(fecha)
        headers = ["Fecha", "Cliente", "Items", "Forma de Pago",
                   "Efectivo", "Transferencia", "Total"]
        rows = []
        for v in ventas:
            items = venta_model.get_items_by_venta(v["id"])
            items_str = "; ".join(
                f"{it['nombre']} {it['talle']} {it['color']} x{it['cantidad']}"
                for it in items
            )
            rows.append([
                v["fecha"],
                v["cliente_nombre"],
                items_str,
                v["forma_pago"],
                v["monto_efectivo"],
                v["monto_transferencia"],
                v["total"],
            ])
        return headers, rows

    def _refresh_caja(self):
        headers, rows = self._get_caja_data()
        self._caja_headers = headers
        self._caja_rows    = rows
        self._caja_preview.load(headers, rows)
        total = sum(r[6] for r in rows) if rows else 0
        self._caja_info.configure(
            text=f"{len(rows)} venta(s) — Total: Gs. {total:,.2f}"
        )

    def _export_caja_csv(self):
        headers, rows = self._get_caja_data()
        fecha = self._caja_date.get() or _today()
        path = save_dialog(f"caja_{fecha}", "csv")
        if not path:
            return
        export_csv(path, headers, rows)
        messagebox.showinfo("Exportado", f"Archivo guardado en:\n{path}")

    def _export_caja_xlsx(self):
        headers, rows = self._get_caja_data()
        fecha = self._caja_date.get() or _today()
        path = save_dialog(f"caja_{fecha}", "xlsx")
        if not path:
            return
        export_excel(path, [{"title": "Caja del Día", "headers": headers, "rows": rows}])
        messagebox.showinfo("Exportado", f"Archivo guardado en:\n{path}")

    # ── Tab 2: Ventas por Rango ───────────────────────────────────────────────

    def _build_tab_rango(self):
        tab = self._tabs.add("Ventas por Rango")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(2, weight=1)

        ctrl = ctk.CTkFrame(tab, fg_color="transparent")
        ctrl.grid(row=0, column=0, padx=8, pady=(8, 4), sticky="w")

        self._rango_desde = DateEntry(ctrl, "Desde:", default=_first_of_month())
        self._rango_desde.pack(side="left", padx=(0, 12))

        self._rango_hasta = DateEntry(ctrl, "Hasta:", default=_today())
        self._rango_hasta.pack(side="left", padx=(0, 16))

        ctk.CTkButton(ctrl, text="Exportar CSV",   width=130,
                      command=self._export_rango_csv).pack(side="left", padx=4)
        ctk.CTkButton(ctrl, text="Exportar Excel", width=130,
                      command=self._export_rango_xlsx).pack(side="left", padx=4)
        ctk.CTkButton(ctrl, text="Actualizar",     width=100,
                      fg_color="transparent",
                      border_width=1,
                      text_color=("gray10", "gray90"),
                      command=self._refresh_rango).pack(side="left", padx=(12, 4))

        self._rango_info = ctk.CTkLabel(tab, text="", font=ctk.CTkFont(size=12),
                                         text_color="gray60")
        self._rango_info.grid(row=1, column=0, padx=8, pady=(0, 4), sticky="w")

        self._rango_preview = PreviewTable(tab)
        self._rango_preview.grid(row=2, column=0, padx=8, pady=(0, 8), sticky="nsew")

    def _get_rango_data(self) -> tuple[list, list]:
        desde = self._rango_desde.get() or _first_of_month()
        hasta = self._rango_hasta.get() or _today()
        ventas = venta_model.get_by_range(desde, hasta)
        headers = ["Fecha", "Cliente", "Items", "Forma de Pago",
                   "Efectivo", "Transferencia", "Total"]
        rows = []
        total_efectivo = 0.0
        total_transfer = 0.0
        total_general  = 0.0
        for v in ventas:
            items = venta_model.get_items_by_venta(v["id"])
            items_str = "; ".join(
                f"{it['nombre']} {it['talle']} {it['color']} x{it['cantidad']}"
                for it in items
            )
            rows.append([
                v["fecha"],
                v["cliente_nombre"],
                items_str,
                v["forma_pago"],
                v["monto_efectivo"],
                v["monto_transferencia"],
                v["total"],
            ])
            total_efectivo += v["monto_efectivo"]
            total_transfer += v["monto_transferencia"]
            total_general  += v["total"]

        if rows:
            rows.append(["TOTAL", "", "", "",
                          total_efectivo, total_transfer, total_general])
        return headers, rows

    def _refresh_rango(self):
        headers, rows = self._get_rango_data()
        self._rango_preview.load(headers, rows)
        data_rows = [r for r in rows if r[0] != "TOTAL"]
        total = sum(r[6] for r in data_rows)
        self._rango_info.configure(
            text=f"{len(data_rows)} venta(s) — Total: Gs. {total:,.2f}"
        )

    def _export_rango_csv(self):
        headers, rows = self._get_rango_data()
        desde = self._rango_desde.get() or _first_of_month()
        hasta = self._rango_hasta.get() or _today()
        path = save_dialog(f"ventas_{desde}_{hasta}", "csv")
        if not path:
            return
        export_csv(path, headers, rows)
        messagebox.showinfo("Exportado", f"Archivo guardado en:\n{path}")

    def _export_rango_xlsx(self):
        headers, rows = self._get_rango_data()
        desde = self._rango_desde.get() or _first_of_month()
        hasta = self._rango_hasta.get() or _today()
        path = save_dialog(f"ventas_{desde}_{hasta}", "xlsx")
        if not path:
            return
        export_excel(path, [{"title": "Ventas", "headers": headers, "rows": rows}])
        messagebox.showinfo("Exportado", f"Archivo guardado en:\n{path}")

    # ── Tab 3: Inventario ─────────────────────────────────────────────────────

    def _build_tab_inventario(self):
        tab = self._tabs.add("Inventario")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(2, weight=1)

        ctrl = ctk.CTkFrame(tab, fg_color="transparent")
        ctrl.grid(row=0, column=0, padx=8, pady=(8, 4), sticky="w")

        self._inv_inactivos = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(ctrl, text="Incluir inactivos",
                        variable=self._inv_inactivos).pack(side="left", padx=(0, 16))

        ctk.CTkButton(ctrl, text="Exportar CSV",   width=130,
                      command=self._export_inv_csv).pack(side="left", padx=4)
        ctk.CTkButton(ctrl, text="Exportar Excel", width=130,
                      command=self._export_inv_xlsx).pack(side="left", padx=4)
        ctk.CTkButton(ctrl, text="Actualizar",     width=100,
                      fg_color="transparent",
                      border_width=1,
                      text_color=("gray10", "gray90"),
                      command=self._refresh_inventario).pack(side="left", padx=(12, 4))

        self._inv_info = ctk.CTkLabel(tab, text="", font=ctk.CTkFont(size=12),
                                       text_color="gray60")
        self._inv_info.grid(row=1, column=0, padx=8, pady=(0, 4), sticky="w")

        self._inv_preview = PreviewTable(tab)
        self._inv_preview.grid(row=2, column=0, padx=8, pady=(0, 8), sticky="nsew")

    def _get_inventario_data(self) -> tuple[list, list]:
        activos_only = not self._inv_inactivos.get()
        productos = producto_model.get_all(activos_only=activos_only)
        headers = ["ID", "Nombre", "Categoría", "Talle", "Color",
                   "Código Barras", "Precio", "Stock", "Activo"]
        rows = [
            [
                p["id"],
                p["nombre"],
                p.get("categoria_nombre") or "",
                p["talle"],
                p["color"],
                p["codigo_barras"],
                p["precio"],
                p["stock"],
                "Sí" if p["activo"] else "No",
            ]
            for p in productos
        ]
        return headers, rows

    def _refresh_inventario(self):
        headers, rows = self._get_inventario_data()
        self._inv_preview.load(headers, rows)
        self._inv_info.configure(text=f"{len(rows)} producto(s)")

    def _export_inv_csv(self):
        headers, rows = self._get_inventario_data()
        path = save_dialog(f"inventario_{_today()}", "csv")
        if not path:
            return
        export_csv(path, headers, rows)
        messagebox.showinfo("Exportado", f"Archivo guardado en:\n{path}")

    def _export_inv_xlsx(self):
        headers, rows = self._get_inventario_data()
        path = save_dialog(f"inventario_{_today()}", "xlsx")
        if not path:
            return
        export_excel(path, [{"title": "Inventario", "headers": headers, "rows": rows}])
        messagebox.showinfo("Exportado", f"Archivo guardado en:\n{path}")

    # ── Tab 4: Historial de Compras ───────────────────────────────────────────

    def _build_tab_compras(self):
        tab = self._tabs.add("Historial de Compras")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(2, weight=1)

        ctrl = ctk.CTkFrame(tab, fg_color="transparent")
        ctrl.grid(row=0, column=0, padx=8, pady=(8, 4), sticky="w")

        self._comp_desde = DateEntry(ctrl, "Desde:", default=_first_of_month())
        self._comp_desde.pack(side="left", padx=(0, 12))

        self._comp_hasta = DateEntry(ctrl, "Hasta:", default=_today())
        self._comp_hasta.pack(side="left", padx=(0, 16))

        ctk.CTkButton(ctrl, text="Exportar CSV",   width=130,
                      command=self._export_comp_csv).pack(side="left", padx=4)
        ctk.CTkButton(ctrl, text="Exportar Excel", width=130,
                      command=self._export_comp_xlsx).pack(side="left", padx=4)
        ctk.CTkButton(ctrl, text="Actualizar",     width=100,
                      fg_color="transparent",
                      border_width=1,
                      text_color=("gray10", "gray90"),
                      command=self._refresh_compras).pack(side="left", padx=(12, 4))

        self._comp_info = ctk.CTkLabel(tab, text="", font=ctk.CTkFont(size=12),
                                        text_color="gray60")
        self._comp_info.grid(row=1, column=0, padx=8, pady=(0, 4), sticky="w")

        self._comp_preview = PreviewTable(tab)
        self._comp_preview.grid(row=2, column=0, padx=8, pady=(0, 8), sticky="nsew")

    def _get_compras_data(self) -> tuple[list, list]:
        desde = self._comp_desde.get() or _first_of_month()
        hasta = self._comp_hasta.get() or _today()
        compras = compra_model.get_all()
        compras = [c for c in compras if desde <= c["fecha"] <= hasta]

        headers = ["Fecha", "Proveedor", "Producto", "Talle", "Color",
                   "Cantidad", "Precio Compra", "Total Compra"]
        rows = []
        for c in compras:
            items = compra_model.get_items(c["id"])
            for it in items:
                subtotal = it["cantidad"] * it["precio_compra"]
                rows.append([
                    c["fecha"],
                    c["proveedor"],
                    it["nombre"],
                    it["talle"],
                    it["color"],
                    it["cantidad"],
                    it["precio_compra"],
                    subtotal,
                ])
        return headers, rows

    def _refresh_compras(self):
        headers, rows = self._get_compras_data()
        self._comp_preview.load(headers, rows)
        total = sum(r[7] for r in rows)
        self._comp_info.configure(
            text=f"{len(rows)} item(s) — Total: Gs. {total:,.2f}"
        )

    def _export_comp_csv(self):
        headers, rows = self._get_compras_data()
        desde = self._comp_desde.get() or _first_of_month()
        hasta = self._comp_hasta.get() or _today()
        path = save_dialog(f"compras_{desde}_{hasta}", "csv")
        if not path:
            return
        export_csv(path, headers, rows)
        messagebox.showinfo("Exportado", f"Archivo guardado en:\n{path}")

    def _export_comp_xlsx(self):
        headers, rows = self._get_compras_data()
        desde = self._comp_desde.get() or _first_of_month()
        hasta = self._comp_hasta.get() or _today()
        path = save_dialog(f"compras_{desde}_{hasta}", "xlsx")
        if not path:
            return
        export_excel(path, [{"title": "Compras", "headers": headers, "rows": rows}])
        messagebox.showinfo("Exportado", f"Archivo guardado en:\n{path}")

    # ── Tab 5: Márgenes ───────────────────────────────────────────────────────

    def _build_tab_margenes(self):
        tab = self._tabs.add("Márgenes")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(2, weight=1)

        ctrl = ctk.CTkFrame(tab, fg_color="transparent")
        ctrl.grid(row=0, column=0, padx=8, pady=(8, 4), sticky="w")

        self._mrg_inactivos = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(ctrl, text="Incluir inactivos",
                        variable=self._mrg_inactivos).pack(side="left", padx=(0, 16))

        ctk.CTkButton(ctrl, text="Exportar CSV",   width=130,
                      command=self._export_mrg_csv).pack(side="left", padx=4)
        ctk.CTkButton(ctrl, text="Exportar Excel", width=130,
                      command=self._export_mrg_xlsx).pack(side="left", padx=4)
        ctk.CTkButton(ctrl, text="Actualizar",     width=100,
                      fg_color="transparent", border_width=1,
                      text_color=("gray10", "gray90"),
                      command=self._refresh_margenes).pack(side="left", padx=(12, 4))

        self._mrg_info = ctk.CTkLabel(tab, text="", font=ctk.CTkFont(size=12),
                                       text_color="gray60")
        self._mrg_info.grid(row=1, column=0, padx=8, pady=(0, 4), sticky="w")

        self._mrg_preview = PreviewTable(tab)
        self._mrg_preview.grid(row=2, column=0, padx=8, pady=(0, 8), sticky="nsew")

    def _get_margenes_data(self) -> tuple[list, list]:
        activos_only = not self._mrg_inactivos.get()
        productos = producto_model.get_all(activos_only=activos_only)
        headers = ["ID", "Nombre", "Categoría", "Talle", "Color",
                   "Costo", "PVP", "Margen Gs.", "Margen %"]
        rows = []
        for p in productos:
            costo  = p.get("precio_costo", 0) or 0
            pvp    = p.get("precio", 0) or 0
            m_abs  = pvp - costo
            m_pct  = round((m_abs / costo * 100), 1) if costo > 0 else None
            rows.append([
                p["id"],
                p["nombre"],
                p.get("categoria_nombre") or "",
                p.get("talle", ""),
                p.get("color", ""),
                costo,
                pvp,
                round(m_abs, 2),
                m_pct,
            ])
        return headers, rows

    def _refresh_margenes(self):
        headers, rows = self._get_margenes_data()
        self._mrg_preview.load(headers, rows)
        self._mrg_info.configure(text=f"{len(rows)} producto(s)")

    def _export_mrg_csv(self):
        headers, rows = self._get_margenes_data()
        path = save_dialog(f"margenes_{_today()}", "csv")
        if not path:
            return
        export_csv(path, headers, rows)
        messagebox.showinfo("Exportado", f"Archivo guardado en:\n{path}")

    def _export_mrg_xlsx(self):
        headers, rows = self._get_margenes_data()
        path = save_dialog(f"margenes_{_today()}", "xlsx")
        if not path:
            return
        export_excel(path, [{"title": "Márgenes", "headers": headers, "rows": rows}])
        messagebox.showinfo("Exportado", f"Archivo guardado en:\n{path}")

    # ── Tab 6: Gastos ─────────────────────────────────────────────────────────

    def _build_tab_gastos(self):
        tab = self._tabs.add("Gastos")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(2, weight=1)

        ctrl = ctk.CTkFrame(tab, fg_color="transparent")
        ctrl.grid(row=0, column=0, padx=8, pady=(8, 4), sticky="w")

        self._gasto_desde = DateEntry(ctrl, "Desde:", default=_first_of_month())
        self._gasto_desde.pack(side="left", padx=(0, 12))

        self._gasto_hasta = DateEntry(ctrl, "Hasta:", default=_today())
        self._gasto_hasta.pack(side="left", padx=(0, 16))

        ctk.CTkButton(ctrl, text="Exportar CSV",   width=130,
                      command=self._export_gasto_csv).pack(side="left", padx=4)
        ctk.CTkButton(ctrl, text="Exportar Excel", width=130,
                      command=self._export_gasto_xlsx).pack(side="left", padx=4)
        ctk.CTkButton(ctrl, text="Actualizar",     width=100,
                      fg_color="transparent", border_width=1,
                      text_color=("gray10", "gray90"),
                      command=self._refresh_gastos).pack(side="left", padx=(12, 4))

        self._gasto_info = ctk.CTkLabel(tab, text="", font=ctk.CTkFont(size=12),
                                         text_color="gray60")
        self._gasto_info.grid(row=1, column=0, padx=8, pady=(0, 4), sticky="w")

        self._gasto_preview = PreviewTable(tab)
        self._gasto_preview.grid(row=2, column=0, padx=8, pady=(0, 8), sticky="nsew")

    def _get_gastos_data(self) -> tuple[list, list]:
        desde = self._gasto_desde.get() or _first_of_month()
        hasta = self._gasto_hasta.get() or _today()
        gastos = gasto_model.get_by_range(desde, hasta)
        headers = ["Fecha", "Categoría", "Descripción", "Monto", "Pagado"]
        rows = [
            [
                g["fecha"],
                g.get("categoria_nombre", ""),
                g["descripcion"],
                g["monto"],
                "Sí" if g["pagado"] else "No",
            ]
            for g in gastos
        ]
        if rows:
            total = sum(g["monto"] for g in gastos)
            rows.append(["TOTAL", "", "", total, ""])
        return headers, rows

    def _refresh_gastos(self):
        headers, rows = self._get_gastos_data()
        self._gasto_preview.load(headers, rows)
        data_rows = [r for r in rows if r[0] != "TOTAL"]
        total = sum(r[3] for r in data_rows)
        # Category summary
        desde = self._gasto_desde.get() or _first_of_month()
        hasta = self._gasto_hasta.get() or _today()
        totales = gasto_model.get_totales_by_range(desde, hasta)
        cat_summary = "   ".join(
            f"{t['categoria']}: Gs. {t['total']:,.2f}" for t in totales
        )
        self._gasto_info.configure(
            text=f"{len(data_rows)} gasto(s) — Total: Gs. {total:,.2f}   {cat_summary}"
        )

    def _export_gasto_csv(self):
        headers, rows = self._get_gastos_data()
        desde = self._gasto_desde.get() or _first_of_month()
        hasta = self._gasto_hasta.get() or _today()
        path = save_dialog(f"gastos_{desde}_{hasta}", "csv")
        if not path:
            return
        export_csv(path, headers, rows)
        messagebox.showinfo("Exportado", f"Archivo guardado en:\n{path}")

    def _export_gasto_xlsx(self):
        headers, rows = self._get_gastos_data()
        desde = self._gasto_desde.get() or _first_of_month()
        hasta = self._gasto_hasta.get() or _today()
        path = save_dialog(f"gastos_{desde}_{hasta}", "xlsx")
        if not path:
            return
        export_excel(path, [{"title": "Gastos", "headers": headers, "rows": rows}])
        messagebox.showinfo("Exportado", f"Archivo guardado en:\n{path}")

    # ── refresh (called by App on navigation) ────────────────────────────────

    def refresh(self, **kwargs):
        self._refresh_caja()
        self._refresh_inventario()
