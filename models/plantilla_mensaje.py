from __future__ import annotations
from database import get_connection


def get_all() -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM plantillas_mensaje ORDER BY nombre"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def create(nombre: str, contenido: str) -> int:
    conn = get_connection()
    try:
        with conn:
            cur = conn.execute(
                "INSERT INTO plantillas_mensaje (nombre, contenido) VALUES (?,?)",
                (nombre, contenido)
            )
            return cur.lastrowid
    finally:
        conn.close()


def update(plantilla_id: int, nombre: str, contenido: str) -> None:
    conn = get_connection()
    try:
        with conn:
            conn.execute(
                "UPDATE plantillas_mensaje SET nombre=?, contenido=? WHERE id=?",
                (nombre, contenido, plantilla_id)
            )
    finally:
        conn.close()


def delete(plantilla_id: int) -> None:
    conn = get_connection()
    try:
        with conn:
            conn.execute(
                "DELETE FROM plantillas_mensaje WHERE id=?", (plantilla_id,)
            )
    finally:
        conn.close()


def render(contenido: str, cliente: dict) -> str:
    result = contenido.replace("{nombre_cliente}", cliente.get("nombre", ""))
    result = result.replace("{nombre_clienta}", cliente.get("nombre", ""))
    return result
