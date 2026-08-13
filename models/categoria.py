from __future__ import annotations
from database import get_connection


def get_all(activos_only: bool = True) -> list[dict]:
    conn = get_connection()
    try:
        q = ("SELECT * FROM categorias WHERE activo=1 ORDER BY nombre"
             if activos_only else "SELECT * FROM categorias ORDER BY nombre")
        return [dict(r) for r in conn.execute(q).fetchall()]
    finally:
        conn.close()


def get_by_id(categoria_id: int) -> dict | None:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM categorias WHERE id=?", (categoria_id,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def create(nombre: str, descripcion: str = "") -> int:
    conn = get_connection()
    try:
        with conn:
            cur = conn.execute(
                "INSERT INTO categorias (nombre, descripcion) VALUES (?,?)",
                (nombre, descripcion)
            )
            return cur.lastrowid
    finally:
        conn.close()


def update(categoria_id: int, nombre: str, descripcion: str = "") -> None:
    conn = get_connection()
    try:
        with conn:
            conn.execute(
                "UPDATE categorias SET nombre=?, descripcion=? WHERE id=?",
                (nombre, descripcion, categoria_id)
            )
    finally:
        conn.close()


def toggle_activo(categoria_id: int) -> None:
    conn = get_connection()
    try:
        with conn:
            conn.execute(
                "UPDATE categorias SET activo = 1 - activo WHERE id=?",
                (categoria_id,)
            )
    finally:
        conn.close()
