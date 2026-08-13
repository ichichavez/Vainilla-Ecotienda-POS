import customtkinter as ctk
from datetime import date

import models.venta as venta_model
import models.cliente as cliente_model
import views.theme as theme


class DashboardView(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self._build_ui()

    def _build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, padx=24, pady=(24, 12), sticky="ew")
        ctk.CTkLabel(
            header, text="Inicio",
            font=theme.font(theme.FONT_HERO, "bold")
        ).pack(side="left")
        self._date_label = ctk.CTkLabel(
            header, text="", font=theme.font(theme.FONT_BASE), text_color="gray50"
        )
        self._date_label.pack(side="right")

        # Summary cards row
        cards_frame = ctk.CTkFrame(self, fg_color="transparent")
        cards_frame.grid(row=1, column=0, padx=24, pady=(0, 16), sticky="ew")
        for i in range(4):
            cards_frame.grid_columnconfigure(i, weight=1)

        self._card_efectivo      = self._make_card(cards_frame, "Efectivo hoy",      "Gs. 0.00", 0, theme.CARD_EFECTIVO)
        self._card_transferencia = self._make_card(cards_frame, "Transferencia hoy", "Gs. 0.00", 1, theme.CARD_TRANSFERENCIA)
        self._card_total         = self._make_card(cards_frame, "Total del día",      "Gs. 0.00", 2, theme.CARD_TOTAL)
        self._card_ventas        = self._make_card(cards_frame, "Ventas del día",     "0",     3, theme.CARD_VENTAS)

        # Pending clients section
        section_label = ctk.CTkLabel(
            self, text="Prendas acumuladas",
            font=theme.font(theme.FONT_MD, "bold")
        )
        section_label.grid(row=2, column=0, padx=24, pady=(4, 4), sticky="nw")

        self._pending_scroll = ctk.CTkScrollableFrame(self, label_text="")
        self._pending_scroll.grid(row=3, column=0, padx=24, pady=(0, 20), sticky="nsew")
        self._pending_scroll.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

    def _make_card(self, parent, title: str, value: str, col: int, color: str) -> ctk.CTkLabel:
        card = ctk.CTkFrame(parent, fg_color=color, corner_radius=12)
        card.grid(row=0, column=col, padx=5, pady=0, sticky="ew")
        ctk.CTkLabel(
            card, text=title,
            font=theme.font(theme.FONT_SM),
            text_color="#a0b8c8",
        ).pack(padx=16, pady=(16, 2), anchor="w")
        val_label = ctk.CTkLabel(
            card, text=value,
            font=theme.font(theme.FONT_LG, "bold"),
            text_color="white",
        )
        val_label.pack(padx=16, pady=(0, 16), anchor="w")
        return val_label

    def refresh(self, **kwargs):
        today = date.today().isoformat()
        self._date_label.configure(text=f"Hoy: {today}")

        totales = venta_model.get_totales_by_date(today)
        self._card_efectivo.configure(text=f"Gs. {totales['efectivo']:,.2f}")
        self._card_transferencia.configure(text=f"Gs. {totales['transferencia']:,.2f}")
        self._card_total.configure(text=f"Gs. {totales['total_general']:,.2f}")
        self._card_ventas.configure(text=str(totales["cantidad"]))

        self._load_pending_clients()

    def _load_pending_clients(self):
        # Clear old rows
        for w in self._pending_scroll.winfo_children():
            w.destroy()

        clientes = cliente_model.get_clientes_con_acumuladas()
        if not clientes:
            ctk.CTkLabel(
                self._pending_scroll,
                text="No hay prendas acumuladas pendientes.",
                text_color="gray60"
            ).pack(padx=16, pady=20)
            return

        for c in clientes:
            n = c["prendas_acumuladas"]
            row = ctk.CTkFrame(self._pending_scroll, corner_radius=8)
            row.pack(fill="x", padx=4, pady=4)
            row.grid_columnconfigure(1, weight=1)

            ctk.CTkLabel(
                row, text=c["nombre"],
                font=theme.font(theme.FONT_BASE, "bold")
            ).grid(row=0, column=0, padx=14, pady=12, sticky="w")

            ctk.CTkLabel(
                row, text=c["ciudad"] or "",
                text_color="gray50", font=theme.font(theme.FONT_SM)
            ).grid(row=0, column=1, padx=4, pady=12, sticky="w")

            badge = ctk.CTkLabel(
                row, text=f"  {n} prenda{'s' if n != 1 else ''}  ",
                fg_color=theme.DANGER, corner_radius=8,
                font=theme.font(theme.FONT_SM, "bold"),
                text_color="white",
            )
            badge.grid(row=0, column=2, padx=8, pady=12)

            ctk.CTkButton(
                row, text="Ver detalle", width=100,
                fg_color=theme.PRIMARY, hover_color=theme.PRIMARY_HOVER,
                font=theme.font(theme.FONT_SM),
                command=lambda cid=c["id"]: self.app.navigate_to_cliente(cid)
            ).grid(row=0, column=3, padx=10, pady=8)
