"""Cache CTkImage thumbnails to avoid re-decoding files on every render."""
from __future__ import annotations

from pathlib import Path

_cache: dict[tuple[str, int, int], object] = {}


def get_thumbnail(foto_path: str, size: int = 52):
    if not foto_path or not Path(foto_path).exists():
        return None
    key = (str(Path(foto_path).resolve()), size, size)
    if key in _cache:
        return _cache[key]
    try:
        from PIL import Image
        import customtkinter as ctk

        img = Image.open(foto_path).resize((size, size))
        ctk_img = ctk.CTkImage(img, size=(size, size))
        _cache[key] = ctk_img
        return ctk_img
    except Exception:
        return None


def clear_cache() -> None:
    _cache.clear()
