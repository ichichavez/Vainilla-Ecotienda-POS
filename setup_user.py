"""Crea o actualiza un usuario administrador.

Editá USERNAME y PASSWORD antes de ejecutar:
    python setup_user.py
"""
import models.usuario as u

USERNAME = "admin"
PASSWORD = "cambiar_esta_clave"


if u.username_exists(USERNAME):
    from database import get_connection

    conn = get_connection()
    row = conn.execute(
        "SELECT id FROM usuarios WHERE username=?", (USERNAME,)
    ).fetchone()
    conn.close()
    u.update_password(row["id"], PASSWORD)
    print(f"Contraseña actualizada para {USERNAME} (id={row['id']})")
else:
    uid = u.create(USERNAME, PASSWORD, rol_nombre="superadmin")
    print(f"Usuario creado: {USERNAME} (id={uid}, rol=superadmin)")

auth = u.authenticate(USERNAME, PASSWORD)
print("Login OK" if auth else "Login FALLÓ")
