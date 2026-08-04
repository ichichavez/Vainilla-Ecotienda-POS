from __future__ import annotations
import hashlib
import os

from database import get_connection


def _hash(password: str, salt: bytes | None = None):
    if salt is None:
        salt = os.urandom(32)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return salt, key


def _verify(password: str, salt_hex: str, hash_hex: str) -> bool:
    salt = bytes.fromhex(salt_hex)
    stored = bytes.fromhex(hash_hex)
    _, key = _hash(password, salt)
    return key == stored


# ── Queries ──────────────────────────────────────────────────────────────────

def count() -> int:
    conn = get_connection()
    try:
        return conn.execute("SELECT COUNT(*) as n FROM usuarios").fetchone()["n"]
    finally:
        conn.close()


def get_all() -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            """SELECT u.id, u.username, u.rol_id, u.activo, r.nombre as rol_nombre
               FROM usuarios u
               JOIN roles r ON r.id = u.rol_id
               ORDER BY u.username"""
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_by_id(usuario_id: int) -> dict | None:
    conn = get_connection()
    try:
        row = conn.execute(
            """SELECT u.id, u.username, u.rol_id, u.activo, r.nombre as rol_nombre
               FROM usuarios u
               JOIN roles r ON r.id = u.rol_id
               WHERE u.id=?""",
            (usuario_id,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def username_exists(username: str) -> bool:
    conn = get_connection()
    try:
        return conn.execute(
            "SELECT 1 FROM usuarios WHERE username=?", (username,)
        ).fetchone() is not None
    finally:
        conn.close()


def create(username: str, password: str, rol_nombre: str = "usuario") -> int:
    salt, key = _hash(password)
    conn = get_connection()
    try:
        rol_row = conn.execute(
            "SELECT id FROM roles WHERE nombre=?", (rol_nombre,)
        ).fetchone()
        rol_id = rol_row["id"] if rol_row else 1
        with conn:
            cur = conn.execute(
                """INSERT INTO usuarios (username, password_hash, salt, rol_id, activo)
                   VALUES (?,?,?,?,1)""",
                (username, key.hex(), salt.hex(), rol_id)
            )
            return cur.lastrowid
    finally:
        conn.close()


def authenticate(username: str, password: str) -> dict | None:
    conn = get_connection()
    try:
        row = conn.execute(
            """SELECT u.*, r.nombre as rol_nombre,
               r.dashboard, r.ventas, r.clientes, r.productos,
               r.caja, r.compras, r.categorias, r.usuarios, r.reportes,
               r.gastos, r.etiquetas, r.catalogo
               FROM usuarios u
               JOIN roles r ON r.id = u.rol_id
               WHERE u.username=? AND u.activo=1""",
            (username,)
        ).fetchone()
        if not row:
            return None
        if _verify(password, row["salt"], row["password_hash"]):
            permisos = {
                "dashboard":  bool(row["dashboard"]),
                "ventas":     bool(row["ventas"]),
                "clientes":   bool(row["clientes"]),
                "productos":  bool(row["productos"]),
                "caja":       bool(row["caja"]),
                "compras":    bool(row["compras"]),
                "categorias": bool(row["categorias"]),
                "usuarios":   bool(row["usuarios"]),
                "reportes":   bool(row["reportes"]),
                "gastos":     bool(row["gastos"]),
                "etiquetas":  bool(row["etiquetas"]),
                "catalogo":   bool(row["catalogo"]),
            }
            return {
                "id":         row["id"],
                "username":   row["username"],
                "rol_id":     row["rol_id"],
                "rol_nombre": row["rol_nombre"],
                "permisos":   permisos,
            }
        return None
    finally:
        conn.close()


def update_password(usuario_id: int, new_password: str) -> None:
    salt, key = _hash(new_password)
    conn = get_connection()
    try:
        with conn:
            conn.execute(
                "UPDATE usuarios SET password_hash=?, salt=? WHERE id=?",
                (key.hex(), salt.hex(), usuario_id)
            )
    finally:
        conn.close()


def update_rol_id(usuario_id: int, rol_id: int) -> None:
    conn = get_connection()
    try:
        with conn:
            conn.execute(
                "UPDATE usuarios SET rol_id=? WHERE id=?", (rol_id, usuario_id)
            )
    finally:
        conn.close()


def toggle_activo(usuario_id: int) -> None:
    conn = get_connection()
    try:
        with conn:
            conn.execute(
                "UPDATE usuarios SET activo = 1 - activo WHERE id=?", (usuario_id,)
            )
    finally:
        conn.close()
