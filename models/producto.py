from __future__ import annotations
from database import get_connection


def get_all(activos_only: bool = True) -> list[dict]:
    conn = get_connection()
    try:
        where = "WHERE p.activo=1" if activos_only else ""
        q = f"""SELECT p.*, c.nombre as categoria_nombre
                FROM productos p
                LEFT JOIN categorias c ON c.id = p.categoria_id
                {where} ORDER BY p.nombre"""
        return [dict(r) for r in conn.execute(q).fetchall()]
    finally:
        conn.close()


def get_by_id(producto_id: int) -> dict | None:
    conn = get_connection()
    try:
        row = conn.execute(
            """SELECT p.*, c.nombre as categoria_nombre
               FROM productos p
               LEFT JOIN categorias c ON c.id = p.categoria_id
               WHERE p.id=?""",
            (producto_id,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_by_codigo_barras(codigo: str) -> dict | None:
    if not codigo:
        return None
    conn = get_connection()
    try:
        row = conn.execute(
            """SELECT p.*, c.nombre as categoria_nombre
               FROM productos p
               LEFT JOIN categorias c ON c.id = p.categoria_id
               WHERE p.codigo_barras=? AND p.activo=1""",
            (codigo,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def search(texto: str, activos_only: bool = True) -> list[dict]:
    conn = get_connection()
    try:
        pattern = f"%{texto}%"
        activo_clause = "AND p.activo=1" if activos_only else ""
        rows = conn.execute(
            f"""SELECT p.*, c.nombre as categoria_nombre
                FROM productos p
                LEFT JOIN categorias c ON c.id = p.categoria_id
                WHERE (p.nombre LIKE ? OR p.talle LIKE ? OR p.color LIKE ?
                       OR p.marca LIKE ? OR p.codigo_barras LIKE ?)
                {activo_clause}
                ORDER BY p.nombre""",
            (pattern, pattern, pattern, pattern, pattern)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def create(nombre: str, descripcion: str, talle: str, color: str,
           precio: float, stock: int, foto_path: str = "",
           categoria_id: int | None = None,
           codigo_barras: str = "",
           precio_costo: float = 0.0,
           marca: str = "") -> int:
    conn = get_connection()
    try:
        with conn:
            cur = conn.execute(
                """INSERT INTO productos
                   (nombre, descripcion, talle, color, precio, stock, foto_path,
                    categoria_id, codigo_barras, precio_costo, marca)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                (nombre, descripcion, talle, color, precio, stock, foto_path,
                 categoria_id, codigo_barras, precio_costo, marca)
            )
            return cur.lastrowid
    finally:
        conn.close()


def update(producto_id: int, nombre: str, descripcion: str, talle: str, color: str,
           precio: float, stock: int, foto_path: str = "",
           categoria_id: int | None = None,
           codigo_barras: str = "",
           precio_costo: float = 0.0,
           marca: str = "") -> None:
    conn = get_connection()
    try:
        with conn:
            conn.execute(
                """UPDATE productos
                   SET nombre=?, descripcion=?, talle=?, color=?, precio=?, stock=?,
                       foto_path=?, categoria_id=?, codigo_barras=?, precio_costo=?,
                       marca=?
                   WHERE id=?""",
                (nombre, descripcion, talle, color, precio, stock, foto_path,
                 categoria_id, codigo_barras, precio_costo, marca, producto_id)
            )
    finally:
        conn.close()


def get_margen(producto_id: int) -> dict:
    p = get_by_id(producto_id)
    if not p:
        return {}
    precio_venta = p["precio"]
    precio_costo = p.get("precio_costo", 0) or 0
    margen_abs = precio_venta - precio_costo
    margen_pct = (margen_abs / precio_costo * 100) if precio_costo > 0 else None
    return {
        "precio_venta": precio_venta,
        "precio_costo": precio_costo,
        "margen_abs":   margen_abs,
        "margen_pct":   margen_pct,
    }


def deactivate(producto_id: int) -> None:
    conn = get_connection()
    try:
        with conn:
            conn.execute("UPDATE productos SET activo=0 WHERE id=?", (producto_id,))
    finally:
        conn.close()


def update_stock(producto_id: int, delta: int) -> None:
    """Apply a stock delta (negative to decrement)."""
    conn = get_connection()
    try:
        with conn:
            conn.execute(
                "UPDATE productos SET stock = stock + ? WHERE id=?",
                (delta, producto_id)
            )
    finally:
        conn.close()
