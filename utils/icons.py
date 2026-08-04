"""
Genera iconos simples con PIL para el sidebar.
Cada icono se dibuja a 36×36 (2× para Retina) y se muestra a 18×18.
CTkImage maneja automáticamente el switch entre tema claro/oscuro.
"""
from __future__ import annotations
import customtkinter as ctk
from PIL import Image, ImageDraw

_S = 36       # tamaño de dibujo (px)
_M = _S // 2  # punto medio = 18
_D = 18       # tamaño de display

_CACHE: dict[str, ctk.CTkImage] = {}


def get(name: str) -> ctk.CTkImage:
    if name not in _CACHE:
        _CACHE[name] = _build(name)
    return _CACHE[name]


# ── helpers ───────────────────────────────────────────────────────────────────

def _pair(draw_fn) -> ctk.CTkImage:
    """Crea CTkImage con versión oscura (para tema claro) y clara (para tema oscuro)."""
    light = Image.new("RGBA", (_S, _S), (0, 0, 0, 0))
    dark  = Image.new("RGBA", (_S, _S), (0, 0, 0, 0))
    draw_fn(ImageDraw.Draw(light), (65, 65, 75))     # ícono oscuro sobre fondo claro
    draw_fn(ImageDraw.Draw(dark),  (195, 195, 210))  # ícono claro sobre fondo oscuro
    return ctk.CTkImage(light_image=light, dark_image=dark, size=(_D, _D))


# ── builders ──────────────────────────────────────────────────────────────────

def _home(d: ImageDraw.ImageDraw, c):
    # Techo (triángulo)
    d.polygon([(_M, 3), (_S-4, _M+1), (4, _M+1)], fill=c)
    # Cuerpo
    d.rectangle([(7, _M), (_S-7, _S-3)], fill=c)
    # Puerta (corte transparente)
    d.rectangle([(_M-4, _M+8), (_M+4, _S-3)], fill=(0, 0, 0, 0))


def _cart(d: ImageDraw.ImageDraw, c):
    # Cesta
    d.rectangle([(5, 8), (_S-5, _S-10)], fill=c)
    # Asa (línea superior)
    d.line([(3, 5), (5, 5)], fill=c, width=3)
    d.line([(3, 5), (5, 8)], fill=c, width=3)
    # Ruedas
    d.ellipse([(9, _S-10), (15, _S-4)], fill=c)
    d.ellipse([(_S-15, _S-10), (_S-9, _S-4)], fill=c)


def _people(d: ImageDraw.ImageDraw, c):
    # Persona izquierda - cabeza
    d.ellipse([(3, 3), (14, 14)], fill=c)
    # Persona izquierda - cuerpo
    d.ellipse([(1, 16), (16, _S-3)], fill=c)
    # Persona derecha - cabeza
    d.ellipse([(_S-14, 3), (_S-3, 14)], fill=c)
    # Persona derecha - cuerpo
    d.ellipse([(_S-16, 16), (_S-1, _S-3)], fill=c)


def _box(d: ImageDraw.ImageDraw, c):
    # Cara frontal
    d.rectangle([(5, _M+2), (_S-5, _S-3)], fill=c)
    # Cara superior (rombo)
    d.polygon([(_M, 4), (_S-5, _M-2), (_M, _M+2), (5, _M-2)], fill=c)
    # Línea central (simulando arista)
    d.line([(_M, 4), (_M, _M+2)], fill=(0, 0, 0, 0), width=2)


def _money(d: ImageDraw.ImageDraw, c):
    # 3 monedas apiladas (elipses)
    for i in range(3):
        y = _S - 6 - i * 9
        d.ellipse([(5, y-5), (_S-5, y+1)], fill=c)


def _truck(d: ImageDraw.ImageDraw, c):
    # Flecha hacia abajo (compras/recibir)
    d.polygon([(_M, _S-3), (5, _M+2), (_S-5, _M+2)], fill=c)
    d.rectangle([(_M-4, 3), (_M+4, _M+4)], fill=c)
    # Base
    d.rectangle([(4, _S-6), (_S-4, _S-3)], fill=c)


def _folder(d: ImageDraw.ImageDraw, c):
    # Pestaña
    d.rectangle([(3, 8), (14, 13)], fill=c)
    # Cuerpo carpeta
    d.rectangle([(3, 12), (_S-3, _S-4)], fill=c)
    # Líneas de contenido
    d.line([(8, 19), (_S-8, 19)], fill=(0, 0, 0, 0), width=2)
    d.line([(8, 25), (_S-8, 25)], fill=(0, 0, 0, 0), width=2)


def _users(d: ImageDraw.ImageDraw, c):
    # Cabeza
    d.ellipse([(_M-8, 2), (_M+8, 18)], fill=c)
    # Cuerpo
    d.ellipse([(_M-12, 20), (_M+12, _S-2)], fill=c)


def _chart(d: ImageDraw.ImageDraw, c):
    # 3 barras de distinta altura
    d.rectangle([(4, _S-14), (11, _S-3)], fill=c)
    d.rectangle([(_M-4, _S-22), (_M+4, _S-3)], fill=c)
    d.rectangle([(_S-11, _S-28), (_S-4, _S-3)], fill=c)
    # Línea base
    d.line([(3, _S-3), (_S-3, _S-3)], fill=c, width=2)


def _arrows_updown(d: ImageDraw.ImageDraw, c):
    # Flecha arriba
    d.polygon([(_M, 2), (_M-7, 13), (_M+7, 13)], fill=c)
    d.rectangle([(_M-3, 11), (_M+3, _M-1)], fill=c)
    # Flecha abajo
    d.polygon([(_M, _S-2), (_M-7, _S-13), (_M+7, _S-13)], fill=c)
    d.rectangle([(_M-3, _M+1), (_M+3, _S-11)], fill=c)


def _receipt(d: ImageDraw.ImageDraw, c):
    # Ticket/recibo
    d.rectangle([(5, 3), (_S-5, _S-3)], fill=c)
    # Líneas de texto (cortes transparentes)
    for y in [11, 18, 25]:
        d.line([(9, y), (_S-9, y)], fill=(0, 0, 0, 0), width=2)


def _tag(d: ImageDraw.ImageDraw, c):
    # Etiqueta de precio (pentágono con punta derecha)
    d.polygon([
        (4, 4), (_S-10, 4), (_S-3, _M), (_S-10, _S-4), (4, _S-4)
    ], fill=c)
    # Agujero
    d.ellipse([(7, _M-4), (15, _M+4)], fill=(0, 0, 0, 0))


def _grid(d: ImageDraw.ImageDraw, c):
    # 2×2 cuadrícula
    d.rectangle([(3, 3), (_M-3, _M-3)], fill=c)
    d.rectangle([(_M+3, 3), (_S-3, _M-3)], fill=c)
    d.rectangle([(3, _M+3), (_M-3, _S-3)], fill=c)
    d.rectangle([(_M+3, _M+3), (_S-3, _S-3)], fill=c)


def _eye(d: ImageDraw.ImageDraw, c):
    d.ellipse([(3, 10), (_S-3, 26)], outline=c, width=3)
    d.ellipse([(_M-5, _M-4), (_M+5, _M+6)], fill=c)


def _eye_off(d: ImageDraw.ImageDraw, c):
    d.ellipse([(3, 10), (_S-3, 26)], outline=c, width=3)
    d.line([(5, 28), (_S-5, 8)], fill=c, width=3)


def _default(d: ImageDraw.ImageDraw, c):
    d.ellipse([(4, 4), (_S-4, _S-4)], fill=c)


# ── dispatch ──────────────────────────────────────────────────────────────────

_BUILDERS = {
    "inicio":      _home,
    "dashboard":   _home,
    "nueva_venta": _cart,
    "clientes":    _people,
    "productos":   _box,
    "caja":        _money,
    "compras":     _truck,
    "categorias":  _folder,
    "usuarios":    _users,
    "reportes":    _chart,
    "movimientos": _arrows_updown,
    "gastos":      _receipt,
    "etiquetas":   _tag,
    "catalogo":    _grid,
    "eye":         _eye,
    "eye_off":     _eye_off,
}


def _build(name: str) -> ctk.CTkImage:
    fn = _BUILDERS.get(name, _default)
    return _pair(fn)
