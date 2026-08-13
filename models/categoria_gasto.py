from __future__ import annotations
from database import get_connection


def get_all(activos_only: bool = True) -> list[dict]:
    conn = get_connection()
    try:
        where = "WHERE activo=1" if activos_only else ""
        rows = conn.execute(
            f"SELECT * FROM categorias_gasto {where} ORDER BY nombre"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def create(nombre: str) -> int:
    conn = get_connection()
    try:
        with conn:
            cur = conn.execute(
                "INSERT INTO categorias_gasto (nombre) VALUES (?)", (nombre,)
            )
            return cur.lastrowid
    finally:
        conn.close()


def update(cat_id: int, nombre: str) -> None:
    conn = get_connection()
    try:
        with conn:
            conn.execute(
                "UPDATE categorias_gasto SET nombre=? WHERE id=?", (nombre, cat_id)
            )
    finally:
        conn.close()


def toggle_activo(cat_id: int) -> None:
    conn = get_connection()
    try:
        with conn:
            conn.execute(
                "UPDATE categorias_gasto SET activo = 1 - activo WHERE id=?",
                (cat_id,)
            )
    finally:
        conn.close()
