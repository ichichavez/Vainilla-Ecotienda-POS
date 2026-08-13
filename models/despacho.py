from __future__ import annotations
from database import get_connection


def create(cliente_id: int, tipo: str, fecha: str,
           notas: str, item_venta_ids: list[int],
           direccion_envio: str = "", costo_envio: float = 0.0) -> int:
    """
    tipo: 'envio' | 'retiro'
    item_venta_ids: list of items_venta.id to mark as dispatched.
    Returns despacho id.
    """
    conn = get_connection()
    try:
        with conn:
            cur = conn.execute(
                """INSERT INTO despachos
                   (cliente_id, tipo, fecha, notas, direccion_envio, costo_envio)
                   VALUES (?,?,?,?,?,?)""",
                (cliente_id, tipo, fecha, notas, direccion_envio, costo_envio)
            )
            despacho_id = cur.lastrowid
            for iv_id in item_venta_ids:
                conn.execute(
                    "INSERT INTO items_despacho (despacho_id, item_venta_id) VALUES (?,?)",
                    (despacho_id, iv_id)
                )
        return despacho_id
    finally:
        conn.close()


def get_by_cliente(cliente_id: int) -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM despachos WHERE cliente_id=? ORDER BY fecha DESC, id DESC",
            (cliente_id,),
        ).fetchall()
        if not rows:
            return []
        despachos = [dict(r) for r in rows]
        despacho_ids = [d["id"] for d in despachos]
        placeholders = ",".join("?" * len(despacho_ids))
        item_rows = conn.execute(
            f"""SELECT id.despacho_id, iv.id, iv.venta_id, iv.producto_id,
                       iv.cantidad, iv.precio_unitario,
                       p.nombre, p.talle, p.color
                FROM items_despacho id
                JOIN items_venta iv ON id.item_venta_id = iv.id
                JOIN productos p ON iv.producto_id = p.id
                WHERE id.despacho_id IN ({placeholders})""",
            tuple(despacho_ids),
        ).fetchall()
        items_by_despacho: dict[int, list[dict]] = {}
        for row in item_rows:
            d = dict(row)
            did = d.pop("despacho_id")
            items_by_despacho.setdefault(did, []).append(d)
        for d in despachos:
            d["items"] = items_by_despacho.get(d["id"], [])
        return despachos
    finally:
        conn.close()
