from __future__ import annotations
from database import get_connection

PERMISOS_KEYS = [
    "dashboard", "ventas", "clientes", "productos",
    "caja", "compras", "categorias", "usuarios", "reportes",
    "gastos", "etiquetas", "catalogo",
]


def get_all(activos_only: bool = False) -> list[dict]:
    conn = get_connection()
    try:
        q = ("SELECT * FROM roles WHERE activo=1 ORDER BY nombre"
             if activos_only else "SELECT * FROM roles ORDER BY nombre")
        return [dict(r) for r in conn.execute(q).fetchall()]
    finally:
        conn.close()


def get_by_id(rol_id: int) -> dict | None:
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM roles WHERE id=?", (rol_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_by_nombre(nombre: str) -> dict | None:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM roles WHERE nombre=?", (nombre,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def create(nombre: str, permisos: dict) -> int:
    conn = get_connection()
    try:
        with conn:
            cur = conn.execute(
                """INSERT INTO roles
                   (nombre, dashboard, ventas, clientes, productos,
                    caja, compras, categorias, usuarios, reportes,
                    gastos, etiquetas, catalogo)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    nombre,
                    int(bool(permisos.get("dashboard"))),
                    int(bool(permisos.get("ventas"))),
                    int(bool(permisos.get("clientes"))),
                    int(bool(permisos.get("productos"))),
                    int(bool(permisos.get("caja"))),
                    int(bool(permisos.get("compras"))),
                    int(bool(permisos.get("categorias"))),
                    int(bool(permisos.get("usuarios"))),
                    int(bool(permisos.get("reportes"))),
                    int(bool(permisos.get("gastos"))),
                    int(bool(permisos.get("etiquetas"))),
                    int(bool(permisos.get("catalogo"))),
                )
            )
            return cur.lastrowid
    finally:
        conn.close()


def update(rol_id: int, nombre: str, permisos: dict) -> None:
    conn = get_connection()
    try:
        with conn:
            conn.execute(
                """UPDATE roles SET nombre=?, dashboard=?, ventas=?, clientes=?,
                   productos=?, caja=?, compras=?, categorias=?, usuarios=?,
                   reportes=?, gastos=?, etiquetas=?, catalogo=?
                   WHERE id=?""",
                (
                    nombre,
                    int(bool(permisos.get("dashboard"))),
                    int(bool(permisos.get("ventas"))),
                    int(bool(permisos.get("clientes"))),
                    int(bool(permisos.get("productos"))),
                    int(bool(permisos.get("caja"))),
                    int(bool(permisos.get("compras"))),
                    int(bool(permisos.get("categorias"))),
                    int(bool(permisos.get("usuarios"))),
                    int(bool(permisos.get("reportes"))),
                    int(bool(permisos.get("gastos"))),
                    int(bool(permisos.get("etiquetas"))),
                    int(bool(permisos.get("catalogo"))),
                    rol_id,
                )
            )
    finally:
        conn.close()


def toggle_activo(rol_id: int) -> None:
    conn = get_connection()
    try:
        with conn:
            conn.execute(
                "UPDATE roles SET activo = 1 - activo WHERE id=?", (rol_id,)
            )
    finally:
        conn.close()
