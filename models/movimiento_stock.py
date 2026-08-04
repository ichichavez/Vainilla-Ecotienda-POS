from __future__ import annotations
from database import get_connection


def log(producto_id: int, tipo: str, cantidad: int, fecha: str,
        referencia_id: int | None = None, notas: str = "") -> int:
    conn = get_connection()
    try:
        with conn:
            cur = conn.execute(
                """INSERT INTO movimientos_stock
                   (producto_id, tipo, cantidad, fecha, referencia_id, notas)
                   VALUES (?,?,?,?,?,?)""",
                (producto_id, tipo, cantidad, fecha, referencia_id, notas or "")
            )
            return cur.lastrowid
    finally:
        conn.close()


def get_by_producto(producto_id: int) -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            """SELECT m.*, p.nombre as producto_nombre
               FROM movimientos_stock m
               JOIN productos p ON p.id = m.producto_id
               WHERE m.producto_id=?
               ORDER BY m.fecha DESC, m.id DESC""",
            (producto_id,)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_by_range(desde: str, hasta: str) -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            """SELECT m.*, p.nombre as producto_nombre
               FROM movimientos_stock m
               JOIN productos p ON p.id = m.producto_id
               WHERE m.fecha BETWEEN ? AND ?
               ORDER BY m.fecha DESC, m.id DESC""",
            (desde, hasta)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_all() -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            """SELECT m.*, p.nombre as producto_nombre
               FROM movimientos_stock m
               JOIN productos p ON p.id = m.producto_id
               ORDER BY m.fecha DESC, m.id DESC"""
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()
