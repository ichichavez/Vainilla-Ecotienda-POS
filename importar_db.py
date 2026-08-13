"""Importar respaldo de base de datos (solo superadmin en usuarios).

Uso:
    python importar_db.py ruta\\al\\respaldo.db

O ejecutar importar.bat e indicar la ruta del archivo .db
"""
from __future__ import annotations

import sys
from pathlib import Path

from utils.backup import import_database


def main() -> int:
    if len(sys.argv) < 2:
        print("Uso: python importar_db.py <archivo_respaldo.db>")
        return 1

    source = Path(sys.argv[1])
    try:
        safety, n_admins, photos = import_database(source)
    except Exception as e:
        print(f"ERROR: {e}")
        return 1

    print("Importación completada.")
    if safety:
        print(f"Respaldo de seguridad (datos anteriores): {safety}")
    print(f"Usuarios superadmin importados: {n_admins}")
    if photos:
        print(f"Fotos de productos restauradas: {photos}")
    print("Reiniciá la aplicación e iniciá sesión con el superadmin del respaldo.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
