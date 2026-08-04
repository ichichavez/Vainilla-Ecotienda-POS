from __future__ import annotations
from database import get_connection


def get_all(activos_only: bool = False) -> list[dict]:
    conn = get_connection()
    try:
        where = "WHERE activo=1" if activos_only else ""
        return [dict(r) for r in
                conn.execute(f"SELECT * FROM clientes {where} ORDER BY nombre").fetchall()]
    finally:
        conn.close()


def get_by_id(cliente_id: int) -> dict | None:
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM clientes WHERE id=?", (cliente_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def search(texto: str, activos_only: bool = False) -> list[dict]:
    conn = get_connection()
    try:
        pattern = f"%{texto}%"
        activo_clause = "AND activo=1" if activos_only else ""
        rows = conn.execute(
            f"""SELECT * FROM clientes
               WHERE (nombre LIKE ? OR apellido LIKE ? OR ciudad LIKE ?
                      OR ci LIKE ? OR correo LIKE ?)
               {activo_clause}
               ORDER BY nombre""",
            (pattern, pattern, pattern, pattern, pattern)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def create(nombre: str, apellido: str = "", ciudad: str = "", telefono: str = "",
           notas: str = "", ci: str = "", correo: str = "",
           cumpleanos: str = "") -> int:
    conn = get_connection()
    try:
        with conn:
            cur = conn.execute(
                """INSERT INTO clientes
                   (nombre, apellido, ciudad, telefono, notas, ci, correo, cumpleanos)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (nombre, apellido, ciudad, telefono, notas, ci, correo, cumpleanos)
            )
            return cur.lastrowid
    finally:
        conn.close()


def update(cliente_id: int, nombre: str, apellido: str = "", ciudad: str = "",
           telefono: str = "", notas: str = "",
           ci: str = "", correo: str = "", cumpleanos: str = "") -> None:
    conn = get_connection()
    try:
        with conn:
            conn.execute(
                """UPDATE clientes
                   SET nombre=?, apellido=?, ciudad=?, telefono=?, notas=?,
                       ci=?, correo=?, cumpleanos=?
                   WHERE id=?""",
                (nombre, apellido, ciudad, telefono, notas, ci, correo, cumpleanos,
                 cliente_id)
            )
    finally:
        conn.close()


def get_prendas_acumuladas(cliente_id: int) -> list[dict]:
    """Items sold but not yet dispatched."""
    conn = get_connection()
    try:
        rows = conn.execute(
            """SELECT iv.id, iv.venta_id, iv.producto_id, iv.cantidad, iv.precio_unitario,
                      p.nombre, p.talle, p.color, v.fecha, v.forma_pago
               FROM items_venta iv
               JOIN ventas v      ON iv.venta_id   = v.id
               JOIN productos p   ON iv.producto_id = p.id
               LEFT JOIN items_despacho id ON iv.id = id.item_venta_id
               WHERE v.cliente_id = ? AND id.id IS NULL
               ORDER BY v.fecha""",
            (cliente_id,)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_count_acumuladas(cliente_id: int) -> int:
    conn = get_connection()
    try:
        row = conn.execute(
            """SELECT COUNT(*) as n
               FROM items_venta iv
               JOIN ventas v ON iv.venta_id = v.id
               LEFT JOIN items_despacho id ON iv.id = id.item_venta_id
               WHERE v.cliente_id = ? AND id.id IS NULL""",
            (cliente_id,)
        ).fetchone()
        return row["n"] if row else 0
    finally:
        conn.close()


def toggle_activo(cliente_id: int) -> None:
    conn = get_connection()
    try:
        with conn:
            conn.execute(
                "UPDATE clientes SET activo = 1 - activo WHERE id=?",
                (cliente_id,)
            )
    finally:
        conn.close()


def get_all_with_acumuladas() -> list[dict]:
    """All clients with their pending item count."""
    clientes = get_all()
    for c in clientes:
        c["prendas_acumuladas"] = get_count_acumuladas(c["id"])
    return clientes
