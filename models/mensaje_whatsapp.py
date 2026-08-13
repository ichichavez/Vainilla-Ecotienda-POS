from __future__ import annotations
from database import get_connection


def create(cliente_id: int, contenido: str, fecha: str) -> int:
    conn = get_connection()
    try:
        with conn:
            cur = conn.execute(
                """INSERT INTO mensajes_whatsapp (cliente_id, contenido, fecha)
                   VALUES (?,?,?)""",
                (cliente_id, contenido, fecha)
            )
            return cur.lastrowid
    finally:
        conn.close()


def get_by_cliente(cliente_id: int) -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            """SELECT * FROM mensajes_whatsapp
               WHERE cliente_id=?
               ORDER BY fecha DESC, id DESC""",
            (cliente_id,)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()
