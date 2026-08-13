from __future__ import annotations
from database import get_connection


def create(cliente_id: int, fecha: str, forma_pago: str,
           items: list[dict],
           monto_efectivo: float = 0.0,
           monto_transferencia: float = 0.0,
           notas: str = "") -> int:
    """
    items: [{"producto_id": int, "cantidad": int, "precio_unitario": float}, ...]
    Para forma_pago "mixto" se deben pasar monto_efectivo y monto_transferencia.
    Para "efectivo" o "transferencia" se calculan automáticamente.
    Descuenta stock de cada producto.
    """
    total = sum(i["cantidad"] * i["precio_unitario"] for i in items)

    if forma_pago == "efectivo":
        monto_efectivo, monto_transferencia = total, 0.0
    elif forma_pago == "transferencia":
        monto_efectivo, monto_transferencia = 0.0, total

    conn = get_connection()
    try:
        with conn:
            cur = conn.execute(
                """INSERT INTO ventas
                   (cliente_id, fecha, forma_pago, total, monto_efectivo, monto_transferencia,
                    notas)
                   VALUES (?,?,?,?,?,?,?)""",
                (cliente_id, fecha, forma_pago, total,
                 monto_efectivo, monto_transferencia, notas)
            )
            venta_id = cur.lastrowid
            for item in items:
                conn.execute(
                    """INSERT INTO items_venta
                       (venta_id, producto_id, cantidad, precio_unitario)
                       VALUES (?,?,?,?)""",
                    (venta_id, item["producto_id"],
                     item["cantidad"], item["precio_unitario"])
                )
                conn.execute(
                    "UPDATE productos SET stock = stock - ? WHERE id=?",
                    (item["cantidad"], item["producto_id"])
                )
                conn.execute(
                    """INSERT INTO movimientos_stock
                       (producto_id, tipo, cantidad, fecha, referencia_id, notas)
                       VALUES (?,?,?,?,?,?)""",
                    (item["producto_id"], "venta", -item["cantidad"],
                     fecha, venta_id, "")
                )
        return venta_id
    finally:
        conn.close()


def get_by_date(fecha: str) -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            """SELECT v.*, c.nombre as cliente_nombre
               FROM ventas v
               JOIN clientes c ON v.cliente_id = c.id
               WHERE v.fecha = ?
               ORDER BY v.id""",
            (fecha,)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_totales_by_date(fecha: str) -> dict:
    conn = get_connection()
    try:
        row = conn.execute(
            """SELECT
                 COALESCE(SUM(monto_efectivo), 0)      AS efectivo,
                 COALESCE(SUM(monto_transferencia), 0) AS transferencia,
                 COALESCE(SUM(total), 0)               AS total_general,
                 COUNT(*)                              AS cantidad
               FROM ventas WHERE fecha=?""",
            (fecha,)
        ).fetchone()
        return dict(row) if row else {
            "efectivo": 0, "transferencia": 0,
            "total_general": 0, "cantidad": 0
        }
    finally:
        conn.close()


def get_items_by_venta(venta_id: int) -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            """SELECT iv.*, p.nombre, p.talle, p.color
               FROM items_venta iv
               JOIN productos p ON iv.producto_id = p.id
               WHERE iv.venta_id = ?""",
            (venta_id,)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_by_cliente(cliente_id: int) -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM ventas WHERE cliente_id=? ORDER BY fecha DESC, id DESC",
            (cliente_id,)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_by_range(desde: str, hasta: str) -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            """SELECT v.*, c.nombre as cliente_nombre
               FROM ventas v
               JOIN clientes c ON v.cliente_id = c.id
               WHERE v.fecha BETWEEN ? AND ?
               ORDER BY v.fecha, v.id""",
            (desde, hasta)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_available_dates() -> list[str]:
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT DISTINCT fecha FROM ventas ORDER BY fecha DESC"
        ).fetchall()
        return [r["fecha"] for r in rows]
    finally:
        conn.close()
