"""Backup helpers for the local SQLite database."""
from __future__ import annotations

import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

from database import DB_PATH


def default_backup_name() -> str:
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    return f"ventas_backup_{stamp}.db"


def backup_database(dest: str | Path) -> Path:
    """Copy ventas.db to dest using SQLite's online backup (safe with WAL)."""
    dest_path = Path(dest)
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    if not DB_PATH.exists():
        raise FileNotFoundError(f"No se encontró la base de datos: {DB_PATH}")

    src = sqlite3.connect(str(DB_PATH), timeout=30)
    try:
        dst = sqlite3.connect(str(dest_path))
        try:
            src.backup(dst)
        finally:
            dst.close()
    finally:
        src.close()

    return dest_path


def backup_product_photos(dest_dir: str | Path) -> Path | None:
    """Copy assets/productos into dest_dir/productos if any photos exist."""
    src = DB_PATH.parent / "assets" / "productos"
    if not src.exists() or not any(src.iterdir()):
        return None
    dest = Path(dest_dir) / "productos"
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(src, dest)
    return dest
