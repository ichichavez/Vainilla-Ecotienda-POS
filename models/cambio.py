from __future__ import annotations

from database import get_connection


class CambioError(Exception):
    pass


def _get_item_pendiente(item_venta_id: int, cliente_id: int) -> dict:
    conn = get_connection()
    try:
        row = conn.execute(
            """SELECT iv.id, iv.venta_id, iv.producto_id, iv.cantidad, iv.precio_unitario,
                      v.cliente_id
               FROM items_venta iv
               JOIN ventas v ON v.id = iv.venta_id
               LEFT JOIN items_despacho id ON id.item_venta_id = iv.id
               WHERE iv.id = ? AND v.cliente_id = ? AND id.id IS NULL""",
            (item_venta_id, cliente_id),
        ).fetchone()
        if not row:
            raise CambioError(
                "La prenda no existe, ya fue despachada o no pertenece a este cliente."
            )
        return dict(row)
    finally:
        conn.close()


def registrar(
    item_venta_id: int,
    cliente_id: int,
    nuevo_producto_id: int,
    fecha: str,
    notas: str = "",
    forma_pago_diff: str = "",
) -> int:
    """
    Cambia una prenda acumulada (sin despachar) por otra.
    No hay devolución en efectivo: si el nuevo producto cuesta menos, se mantiene
    el precio pagado; si cuesta más, se cobra la diferencia.
    """
    item = _get_item_pendiente(item_venta_id, cliente_id)
    cantidad = int(item["cantidad"])
    precio_origen = float(item["precio_unitario"])
    producto_origen_id = int(item["producto_id"])
    venta_id = int(item["venta_id"])

    if nuevo_producto_id == producto_origen_id:
        raise CambioError("Elegí un producto distinto al actual.")

    conn = get_connection()
    try:
        nuevo = conn.execute(
            "SELECT id, nombre, precio, stock, activo FROM productos WHERE id=?",
            (nuevo_producto_id,),
        ).fetchone()
        if not nuevo or not nuevo["activo"]:
            raise CambioError("El producto de reemplazo no está disponible.")
        if int(nuevo["stock"]) < cantidad:
            raise CambioError(
                f"Stock insuficiente. Disponible: {nuevo['stock']}, necesario: {cantidad}."
            )

        precio_nuevo = float(nuevo["precio"])
        diferencia_unit = precio_nuevo - precio_origen
        diferencia_total = diferencia_unit * cantidad

        if diferencia_total > 0.009 and forma_pago_diff not in ("efectivo", "transferencia"):
            raise CambioError(
                "El nuevo producto cuesta más. Indicá cómo se cobra la diferencia."
            )

        precio_linea = precio_nuevo if diferencia_total > 0.009 else precio_origen

        with conn:
            conn.execute(
                "UPDATE productos SET stock = stock + ? WHERE id=?",
                (cantidad, producto_origen_id),
            )
            conn.execute(
                "UPDATE productos SET stock = stock - ? WHERE id=?",
                (cantidad, nuevo_producto_id),
            )
            conn.execute(
                """INSERT INTO movimientos_stock
                   (producto_id, tipo, cantidad, fecha, referencia_id, notas)
                   VALUES (?,?,?,?,?,?)""",
                (
                    producto_origen_id,
                    "devolucion",
                    cantidad,
                    fecha,
                    item_venta_id,
                    f"Cambio prenda acumulada (item {item_venta_id})",
                ),
            )
            conn.execute(
                """INSERT INTO movimientos_stock
                   (producto_id, tipo, cantidad, fecha, referencia_id, notas)
                   VALUES (?,?,?,?,?,?)""",
                (
                    nuevo_producto_id,
                    "cambio",
                    -cantidad,
                    fecha,
                    item_venta_id,
                    f"Cambio prenda acumulada (item {item_venta_id})",
                ),
            )
            conn.execute(
                """UPDATE items_venta
                   SET producto_id=?, precio_unitario=?
                   WHERE id=?""",
                (nuevo_producto_id, precio_linea, item_venta_id),
            )

            if diferencia_total > 0.009:
                if forma_pago_diff == "efectivo":
                    conn.execute(
                        """UPDATE ventas
                           SET total = total + ?,
                               monto_efectivo = monto_efectivo + ?
                           WHERE id=?""",
                        (diferencia_total, diferencia_total, venta_id),
                    )
                else:
                    conn.execute(
                        """UPDATE ventas
                           SET total = total + ?,
                               monto_transferencia = monto_transferencia + ?
                           WHERE id=?""",
                        (diferencia_total, diferencia_total, venta_id),
                    )

            cur = conn.execute(
                """INSERT INTO cambios
                   (cliente_id, fecha, item_venta_id,
                    producto_origen_id, producto_nuevo_id,
                    cantidad, precio_origen, precio_nuevo,
                    diferencia, forma_pago_diff, notas)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    cliente_id,
                    fecha,
                    item_venta_id,
                    producto_origen_id,
                    nuevo_producto_id,
                    cantidad,
                    precio_origen,
                    precio_nuevo,
                    diferencia_total,
                    forma_pago_diff if diferencia_total > 0.009 else "",
                    notas,
                ),
            )
            return cur.lastrowid
    finally:
        conn.close()


def get_by_cliente(cliente_id: int) -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            """SELECT c.*,
                      po.nombre AS origen_nombre, po.talle AS origen_talle,
                      po.color AS origen_color,
                      pn.nombre AS nuevo_nombre, pn.talle AS nuevo_talle,
                      pn.color AS nuevo_color
               FROM cambios c
               JOIN productos po ON po.id = c.producto_origen_id
               JOIN productos pn ON pn.id = c.producto_nuevo_id
               WHERE c.cliente_id = ?
               ORDER BY c.fecha DESC, c.id DESC""",
            (cliente_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()
