import customtkinter as ctk
from datetime import date

import models.venta as venta_model


class CajaView(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)
        self._build_ui()

    def _build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, padx=24, pady=(20, 8), sticky="ew")
        header.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(header, text="Caja del Día",
                     font=ctk.CTkFont(size=24, weight="bold")).grid(
            row=0, column=0, sticky="w")

        # Date selector
        date_frame = ctk.CTkFrame(header, fg_color="transparent")
        date_frame.grid(row=0, column=2, padx=0)
        ctk.CTkLabel(date_frame, text="Fecha:").pack(side="left", padx=(0, 6))
        self._fecha_var = ctk.StringVar(value=date.today().isoformat())
        self._fecha_entry = ctk.CTkEntry(date_frame, textvariable=self._fecha_var,
                                         width=120)
        self._fecha_entry.pack(side="left", padx=(0, 6))
        ctk.CTkButton(date_frame, text="Buscar", width=80,
                      command=self._load).pack(side="left")

        # Quick date buttons
        quick_frame = ctk.CTkFrame(self, fg_color="transparent")
        quick_frame.grid(row=1, column=0, padx=24, pady=(0, 8), sticky="w")

        ctk.CTkLabel(quick_frame, text="Acceso rápido:",
                     text_color="gray60").pack(side="left", padx=(0, 8))
        ctk.CTkButton(quick_frame, text="Hoy", width=70,
                      command=lambda: self._set_date(date.today().isoformat())).pack(
            side="left", padx=3)

        # Summary cards
        cards = ctk.CTkFrame(self, fg_color="transparent")
        cards.grid(row=2, column=0, padx=24, pady=(0, 12), sticky="ew")
        for i in range(3):
            cards.grid_columnconfigure(i, weight=1)

        self._card_efectivo      = self._make_card(cards, "Efectivo",      "$0.00", 0, "#2d6a4f")
        self._card_transferencia = self._make_card(cards, "Transferencia", "$0.00", 1, "#1d3557")
        self._card_total         = self._make_card(cards, "Total general", "$0.00", 2, "#4a4e69")

        # Sales list
        list_label = ctk.CTkFrame(self, fg_color="transparent")
        list_label.grid(row=3, column=0, padx=24, pady=(0, 4), sticky="ew")
        list_label.grid_columnconfigure(1, weight=1)
        self._ventas_title = ctk.CTkLabel(list_label, text="Ventas del día",
                                          font=ctk.CTkFont(size=16, weight="bold"))
        self._ventas_title.grid(row=0, column=0, sticky="w")
        self._count_label = ctk.CTkLabel(list_label, text="",
                                         text_color="gray60")
        self._count_label.grid(row=0, column=1, padx=12, sticky="w")

        self._scroll = ctk.CTkScrollableFrame(self)
        self._scroll.grid(row=4, column=0, padx=24, pady=(0, 20), sticky="nsew")
        self._scroll.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1)

    def _make_card(self, parent, title: str, value: str,
                   col: int, color: str) -> ctk.CTkLabel:
        card = ctk.CTkFrame(parent, fg_color=color, corner_radius=12)
        card.grid(row=0, column=col, padx=6, pady=0, sticky="ew")
        ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=11),
                     text_color="gray80").pack(padx=16, pady=(14, 2), anchor="w")
        val_label = ctk.CTkLabel(card, text=value,
                                 font=ctk.CTkFont(size=22, weight="bold"))
        val_label.pack(padx=16, pady=(0, 14), anchor="w")
        return val_label

    def refresh(self, **kwargs):
        self._fecha_var.set(date.today().isoformat())
        self._load()

    def _set_date(self, fecha: str):
        self._fecha_var.set(fecha)
        self._load()

    def _load(self):
        fecha = self._fecha_var.get().strip()

        # Update summary cards
        totales = venta_model.get_totales_by_date(fecha)
        self._card_efectivo.configure(text=f"${totales['efectivo']:,.2f}")
        self._card_transferencia.configure(text=f"${totales['transferencia']:,.2f}")
        self._card_total.configure(text=f"${totales['total_general']:,.2f}")

        cantidad = totales["cantidad"]
        self._count_label.configure(
            text=f"{cantidad} venta{'s' if cantidad != 1 else ''}")

        # Populate list
        ventas = venta_model.get_by_date(fecha)
        for w in self._scroll.winfo_children():
            w.destroy()

        if not ventas:
            ctk.CTkLabel(self._scroll,
                         text=f"No hay ventas registradas para {fecha}.",
                         text_color="gray60").pack(pady=20)
            return

        for v in ventas:
            self._make_venta_card(v)

    def _make_venta_card(self, v: dict):
        forma = v["forma_pago"]
        if forma == "efectivo":
            pago_color = "#2d6a4f"
        elif forma == "transferencia":
            pago_color = "#1d3557"
        else:
            pago_color = "#4a4e69"   # mixto

        card = ctk.CTkFrame(self._scroll, corner_radius=8)
        card.pack(fill="x", pady=4)
        card.grid_columnconfigure(1, weight=1)

        # Payment badge
        ctk.CTkLabel(card, text=f" {forma} ",
                     fg_color=pago_color, corner_radius=6,
                     font=ctk.CTkFont(size=11, weight="bold")).grid(
            row=0, column=0, padx=(12, 8), pady=(10, 2), rowspan=2)

        # Client name
        ctk.CTkLabel(card, text=v["cliente_nombre"],
                     font=ctk.CTkFont(size=13, weight="bold"), anchor="w").grid(
            row=0, column=1, padx=4, pady=(10, 1), sticky="w")

        # Items detail
        items = venta_model.get_items_by_venta(v["id"])
        items_text = "  ·  ".join(
            f"{it['nombre']} x{it['cantidad']}" for it in items
        )
        detail_parts = [items_text]
        if forma == "mixto":
            detail_parts.append(
                f"ef ${v['monto_efectivo']:,.2f}  /  "
                f"transf ${v['monto_transferencia']:,.2f}"
            )
        ctk.CTkLabel(card, text="   ".join(detail_parts),
                     text_color="gray60", font=ctk.CTkFont(size=11),
                     anchor="w").grid(
            row=1, column=1, padx=4, pady=(0, 10), sticky="w")

        # Total
        ctk.CTkLabel(card, text=f"${v['total']:,.2f}",
                     font=ctk.CTkFont(size=16, weight="bold")).grid(
            row=0, column=2, padx=16, pady=12, rowspan=2)
