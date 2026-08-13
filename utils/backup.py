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


def default_backup_folder_name() -> str:
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    return f"Vainilla_respaldo_{stamp}"


def _count_table_rows(db_path: Path) -> dict[str, int]:
    conn = sqlite3.connect(str(db_path), timeout=30)
    try:
        counts: dict[str, int] = {}
        for table in ("productos", "clientes", "ventas", "usuarios", "compras", "gastos"):
            try:
                row = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
                counts[table] = int(row[0]) if row else 0
            except sqlite3.Error:
                pass
        return counts
    finally:
        conn.close()


def backup_full(dest_parent: str | Path) -> dict:
    """
    Respaldo completo en una carpeta:
      - ventas.db  (productos, clientes, ventas, stock, usuarios, etc.)
      - productos/ (fotos de productos, si hay)
    """
    parent = Path(dest_parent)
    parent.mkdir(parents=True, exist_ok=True)
    folder = parent / default_backup_folder_name()
    folder.mkdir(parents=True, exist_ok=True)

    db_dest = folder / "ventas.db"
    backup_database(db_dest)
    photos_dest = backup_product_photos(folder)
    counts = _count_table_rows(db_dest)

    return {
        "folder": folder,
        "db": db_dest,
        "photos": photos_dest,
        "counts": counts,
    }


def restore_product_photos(near_db_path: str | Path) -> Path | None:
    """Restore product photos from a backup folder next to the .db file."""
    db_path = Path(near_db_path)
    candidates = [
        db_path.parent / "productos",
        db_path.parent / f"{db_path.stem}_fotos" / "productos",
    ]
    src: Path | None = None
    for candidate in candidates:
        if candidate.exists() and any(candidate.iterdir()):
            src = candidate
            break
    if src is None:
        return None

    dest = DB_PATH.parent / "assets" / "productos"
    dest.mkdir(parents=True, exist_ok=True)
    for item in dest.iterdir():
        if item.is_file():
            item.unlink()
        elif item.is_dir():
            shutil.rmtree(item)
    for item in src.iterdir():
        target = dest / item.name
        if item.is_dir():
            shutil.copytree(item, target)
        else:
            shutil.copy2(item, target)

    try:
        from utils.image_cache import clear_cache
        clear_cache()
    except Exception:
        pass

    return dest


def resolve_backup_db(source: str | Path) -> Path:
    """Accept a .db file or a backup folder containing ventas.db."""
    source_path = Path(source)
    if source_path.is_dir():
        for name in ("ventas.db",):
            candidate = source_path / name
            if candidate.exists():
                return candidate
        db_files = sorted(source_path.glob("*.db"))
        if not db_files:
            raise ValueError(
                "La carpeta no contiene ventas.db ni otro archivo .db válido."
            )
        return db_files[0]
    return source_path


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


_REQUIRED_TABLES = frozenset({"ventas", "usuarios", "roles", "productos"})


def _validate_pos_database(db_path: Path) -> None:
    conn = sqlite3.connect(str(db_path), timeout=30)
    try:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        tables = {r[0] for r in rows}
        missing = _REQUIRED_TABLES - tables
        if missing:
            raise ValueError(
                "El archivo no parece un respaldo de Vainilla Ecotienda POS "
                f"(faltan tablas: {', '.join(sorted(missing))})."
            )
    finally:
        conn.close()


def _keep_only_superadmin_users() -> int:
    """Remove all users except superadmin. Returns superadmin count."""
    conn = sqlite3.connect(str(DB_PATH), timeout=30)
    conn.row_factory = sqlite3.Row
    try:
        with conn:
            conn.execute("PRAGMA foreign_keys = OFF")
            conn.execute(
                """DELETE FROM usuarios
                   WHERE rol_id NOT IN (
                       SELECT id FROM roles WHERE nombre = 'superadmin'
                   )"""
            )
            row = conn.execute(
                """SELECT COUNT(*) AS n FROM usuarios u
                   JOIN roles r ON r.id = u.rol_id
                   WHERE r.nombre = 'superadmin'"""
            ).fetchone()
            return int(row["n"]) if row else 0
    finally:
        conn.close()


def import_database(
    source: str | Path,
    backups_dir: str | Path | None = None,
) -> tuple[Path | None, int]:
    """
    Import a .db backup over ventas.db.
    All business data is restored; only superadmin users are kept from the backup.
    Creates a safety copy of the current DB first (if it exists).
    Returns (safety_backup_path or None, superadmin_user_count).
    """
    source_path = resolve_backup_db(source)

    if not source_path.exists():
        raise FileNotFoundError(f"No se encontró el archivo: {source_path}")

    _validate_pos_database(source_path)

    dest_backups = Path(backups_dir) if backups_dir else DB_PATH.parent / "backups"
    dest_backups.mkdir(parents=True, exist_ok=True)

    safety_path: Path | None = None
    if DB_PATH.exists():
        safety_path = dest_backups / default_backup_name()
        backup_database(safety_path)

    src = sqlite3.connect(str(source_path), timeout=30)
    try:
        dst = sqlite3.connect(str(DB_PATH))
        try:
            src.backup(dst)
            dst.commit()
        finally:
            dst.close()
    finally:
        src.close()

    superadmin_count = _keep_only_superadmin_users()

    photos_restored = restore_product_photos(source_path)

    from database import init_db
    init_db()

    return safety_path, superadmin_count, photos_restored
