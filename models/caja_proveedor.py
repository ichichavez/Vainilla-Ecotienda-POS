from __future__ import annotations
from database import get_connection


def get_all(estado: str | None = None) -> list[dict]:
    conn = get_connection()
    if estado:
        rows = conn.execute(
            "SELECT * FROM cajas_proveedor WHERE estado=? ORDER BY fecha_ingreso DESC",
            (estado,),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM cajas_proveedor ORDER BY fecha_ingreso DESC"
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def create(
    proveedor: str,
    descripcion: str,
    fecha_ingreso: str,
    notas: str = "",
) -> int:
    conn = get_connection()
    with conn:
        cur = conn.execute(
            """INSERT INTO cajas_proveedor
               (proveedor, descripcion, fecha_ingreso, notas, estado)
               VALUES (?, ?, ?, ?, 'pendiente')""",
            (proveedor, descripcion, fecha_ingreso, notas),
        )
    conn.close()
    return cur.lastrowid


def marcar_retirado(caja_id: int, fecha_retiro: str, notas: str = "") -> None:
    conn = get_connection()
    with conn:
        conn.execute(
            """UPDATE cajas_proveedor
               SET estado='retirado', fecha_retiro=?, notas=?
               WHERE id=?""",
            (fecha_retiro, notas, caja_id),
        )
    conn.close()


def delete(caja_id: int) -> None:
    conn = get_connection()
    with conn:
        conn.execute("DELETE FROM cajas_proveedor WHERE id=?", (caja_id,))
    conn.close()
