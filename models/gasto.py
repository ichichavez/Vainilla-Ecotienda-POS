from __future__ import annotations
from database import get_connection


def create(fecha: str, categoria_id: int, descripcion: str,
           monto: float, pagado: bool = False,
           proveedor: str = "", numero_comprobante: str = "",
           forma_pago: str = "") -> int:
    conn = get_connection()
    try:
        with conn:
            cur = conn.execute(
                """INSERT INTO gastos
                   (fecha, categoria_id, descripcion, monto, pagado,
                    proveedor, numero_comprobante, forma_pago)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (fecha, categoria_id, descripcion, monto, int(pagado),
                 proveedor, numero_comprobante, forma_pago)
            )
            return cur.lastrowid
    finally:
        conn.close()


def get_all() -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            """SELECT g.*, c.nombre as categoria_nombre
               FROM gastos g
               JOIN categorias_gasto c ON c.id = g.categoria_id
               ORDER BY g.fecha DESC, g.id DESC"""
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_by_range(desde: str, hasta: str) -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            """SELECT g.*, c.nombre as categoria_nombre
               FROM gastos g
               JOIN categorias_gasto c ON c.id = g.categoria_id
               WHERE g.fecha BETWEEN ? AND ?
               ORDER BY g.fecha DESC, g.id DESC""",
            (desde, hasta)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def update(gasto_id: int, fecha: str, categoria_id: int,
           descripcion: str, monto: float, pagado: bool,
           proveedor: str = "", numero_comprobante: str = "",
           forma_pago: str = "") -> None:
    conn = get_connection()
    try:
        with conn:
            conn.execute(
                """UPDATE gastos
                   SET fecha=?, categoria_id=?, descripcion=?, monto=?, pagado=?,
                       proveedor=?, numero_comprobante=?, forma_pago=?
                   WHERE id=?""",
                (fecha, categoria_id, descripcion, monto, int(pagado),
                 proveedor, numero_comprobante, forma_pago, gasto_id)
            )
    finally:
        conn.close()


def delete(gasto_id: int) -> None:
    conn = get_connection()
    try:
        with conn:
            conn.execute("DELETE FROM gastos WHERE id=?", (gasto_id,))
    finally:
        conn.close()


def get_totales_by_range(desde: str, hasta: str) -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            """SELECT c.nombre as categoria, SUM(g.monto) as total, COUNT(*) as cantidad
               FROM gastos g
               JOIN categorias_gasto c ON c.id = g.categoria_id
               WHERE g.fecha BETWEEN ? AND ?
               GROUP BY g.categoria_id, c.nombre
               ORDER BY total DESC""",
            (desde, hasta)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()
