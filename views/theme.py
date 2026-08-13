from __future__ import annotations
import customtkinter as ctk

# ── Brand colors ──────────────────────────────────────────────────────────────

PRIMARY        = "#2d6a4f"
PRIMARY_HOVER  = "#1b4332"
# Tinted background for active/selected state (light, dark)
PRIMARY_LIGHT  = ("#d4edda", "#1a3328")
PRIMARY_TEXT   = ("#1a3d2a", "#7ec8a0")

DANGER         = "#e63946"
DANGER_HOVER   = "#c1121f"

WARNING        = "#f4a261"

# ── Status badge colors ───────────────────────────────────────────────────────

STOCK_OK       = PRIMARY
STOCK_LOW      = WARNING
STOCK_EMPTY    = DANGER
STOCK_INACTIVE = "gray40"

# ── Dashboard card colors (oscuros, armoniosos) ───────────────────────────────

CARD_EFECTIVO      = "#163d52"   # azul petróleo
CARD_TRANSFERENCIA = "#1b4332"   # verde bosque
CARD_TOTAL         = "#2d1f4e"   # índigo profundo
CARD_VENTAS        = "#4a1f10"   # terracota oscura

# ── Typography scale ─────────────────────────────────────────────────────────

FONT_XS   = 10
FONT_SM   = 11
FONT_BASE = 13
FONT_MD   = 15
FONT_LG   = 20
FONT_HERO = 24


def font(size: int = FONT_BASE, weight: str = "normal") -> ctk.CTkFont:
    return ctk.CTkFont(size=size, weight=weight)
