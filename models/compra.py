from __future__ import annotations
from database import get_connection


def create(fecha: str, proveedor: str, notas: str, items: list[dict],
           numero_factura: str = "", forma_pago: str = "efectivo") -> int:
    """
    items: [{"producto_id": int, "cantidad": int, "precio_compra": float}]
    Incrementa stock de cada producto dentro de la misma transacción.
    """
    total = sum(it["cantidad"] * it["precio_compra"] for it in items)
    conn = get_connection()
    try:
        with conn:
            cur = conn.execute(
                """INSERT INTO compras
                   (fecha, proveedor, total, notas, numero_factura, forma_pago)
                   VALUES (?,?,?,?,?,?)""",
                (fecha, proveedor, total, notas, numero_factura, forma_pago)
            )
            compra_id = cur.lastrowid
            for it in items:
                conn.execute(
                    """INSERT INTO items_compra
                       (compra_id, producto_id, cantidad, precio_compra)
                       VALUES (?,?,?,?)""",
                    (compra_id, it["producto_id"], it["cantidad"], it["precio_compra"])
                )
                conn.execute(
                    "UPDATE productos SET stock = stock + ? WHERE id=?",
                    (it["cantidad"], it["producto_id"])
                )
                conn.execute(
                    """INSERT INTO movimientos_stock
                       (producto_id, tipo, cantidad, fecha, referencia_id, notas)
                       VALUES (?,?,?,?,?,?)""",
                    (it["producto_id"], "compra", it["cantidad"],
                     fecha, compra_id, "")
                )
            return compra_id
    finally:
        conn.close()


def get_all() -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM compras ORDER BY fecha DESC, id DESC"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_by_date(fecha: str) -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM compras WHERE fecha=? ORDER BY id DESC",
            (fecha,)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_items(compra_id: int) -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            """SELECT ic.*, p.nombre, p.talle, p.color
               FROM items_compra ic
               JOIN productos p ON p.id = ic.producto_id
               WHERE ic.compra_id=?""",
            (compra_id,)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()
