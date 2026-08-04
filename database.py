import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "ventas.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_connection()
    with conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS categorias (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre      TEXT    NOT NULL UNIQUE,
                descripcion TEXT    NOT NULL DEFAULT '',
                activo      INTEGER NOT NULL DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS roles (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre      TEXT    NOT NULL UNIQUE,
                dashboard   INTEGER NOT NULL DEFAULT 0,
                ventas      INTEGER NOT NULL DEFAULT 0,
                clientes    INTEGER NOT NULL DEFAULT 0,
                productos   INTEGER NOT NULL DEFAULT 0,
                caja        INTEGER NOT NULL DEFAULT 0,
                compras     INTEGER NOT NULL DEFAULT 0,
                categorias  INTEGER NOT NULL DEFAULT 0,
                usuarios    INTEGER NOT NULL DEFAULT 0,
                activo      INTEGER NOT NULL DEFAULT 1
            );

            INSERT OR IGNORE INTO roles
                (nombre, dashboard, ventas, clientes, productos, caja, compras, categorias, usuarios)
            VALUES ('superadmin', 1, 1, 1, 1, 1, 1, 1, 1);

            INSERT OR IGNORE INTO roles
                (nombre, dashboard, ventas, clientes, caja)
            VALUES ('vendedor', 1, 1, 1, 1);

            INSERT OR IGNORE INTO roles
                (nombre, dashboard, ventas, clientes, productos, caja)
            VALUES ('usuario', 1, 1, 1, 1, 1);

            CREATE TABLE IF NOT EXISTS productos (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre        TEXT    NOT NULL,
                descripcion   TEXT    NOT NULL DEFAULT '',
                talle         TEXT    NOT NULL DEFAULT '',
                color         TEXT    NOT NULL DEFAULT '',
                precio        REAL    NOT NULL DEFAULT 0,
                stock         INTEGER NOT NULL DEFAULT 0,
                foto_path     TEXT    NOT NULL DEFAULT '',
                activo        INTEGER NOT NULL DEFAULT 1,
                categoria_id  INTEGER DEFAULT NULL REFERENCES categorias(id),
                codigo_barras TEXT    NOT NULL DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS clientes (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre   TEXT NOT NULL,
                ciudad   TEXT NOT NULL DEFAULT '',
                telefono TEXT NOT NULL DEFAULT '',
                notas    TEXT NOT NULL DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS ventas (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente_id          INTEGER NOT NULL,
                fecha               TEXT    NOT NULL,
                forma_pago          TEXT    NOT NULL,
                total               REAL    NOT NULL DEFAULT 0,
                monto_efectivo      REAL    NOT NULL DEFAULT 0,
                monto_transferencia REAL    NOT NULL DEFAULT 0,
                FOREIGN KEY (cliente_id) REFERENCES clientes(id)
            );

            CREATE TABLE IF NOT EXISTS items_venta (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                venta_id        INTEGER NOT NULL,
                producto_id     INTEGER NOT NULL,
                cantidad        INTEGER NOT NULL DEFAULT 1,
                precio_unitario REAL    NOT NULL,
                FOREIGN KEY (venta_id)    REFERENCES ventas(id),
                FOREIGN KEY (producto_id) REFERENCES productos(id)
            );

            CREATE TABLE IF NOT EXISTS despachos (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente_id  INTEGER NOT NULL,
                tipo        TEXT    NOT NULL,
                fecha       TEXT    NOT NULL,
                notas       TEXT    NOT NULL DEFAULT '',
                FOREIGN KEY (cliente_id) REFERENCES clientes(id)
            );

            CREATE TABLE IF NOT EXISTS items_despacho (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                despacho_id   INTEGER NOT NULL,
                item_venta_id INTEGER NOT NULL,
                FOREIGN KEY (despacho_id)   REFERENCES despachos(id),
                FOREIGN KEY (item_venta_id) REFERENCES items_venta(id)
            );

            CREATE TABLE IF NOT EXISTS usuarios (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                username      TEXT    NOT NULL UNIQUE,
                password_hash TEXT    NOT NULL,
                salt          TEXT    NOT NULL,
                rol_id        INTEGER NOT NULL DEFAULT 1 REFERENCES roles(id),
                activo        INTEGER NOT NULL DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS compras (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha     TEXT    NOT NULL,
                proveedor TEXT    NOT NULL DEFAULT '',
                total     REAL    NOT NULL DEFAULT 0,
                notas     TEXT    NOT NULL DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS items_compra (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                compra_id      INTEGER NOT NULL,
                producto_id    INTEGER NOT NULL,
                cantidad       INTEGER NOT NULL DEFAULT 1,
                precio_compra  REAL    NOT NULL DEFAULT 0,
                FOREIGN KEY (compra_id)   REFERENCES compras(id),
                FOREIGN KEY (producto_id) REFERENCES productos(id)
            );

            CREATE TABLE IF NOT EXISTS movimientos_stock (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                producto_id   INTEGER NOT NULL,
                tipo          TEXT    NOT NULL,
                cantidad      INTEGER NOT NULL,
                fecha         TEXT    NOT NULL,
                referencia_id INTEGER,
                notas         TEXT    NOT NULL DEFAULT '',
                FOREIGN KEY (producto_id) REFERENCES productos(id)
            );

            CREATE TABLE IF NOT EXISTS categorias_gasto (
                id     INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT    NOT NULL UNIQUE,
                activo INTEGER NOT NULL DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS gastos (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha        TEXT    NOT NULL,
                categoria_id INTEGER NOT NULL REFERENCES categorias_gasto(id),
                descripcion  TEXT    NOT NULL,
                monto        REAL    NOT NULL,
                pagado       INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS plantillas_mensaje (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre    TEXT NOT NULL UNIQUE,
                contenido TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS mensajes_whatsapp (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente_id INTEGER NOT NULL REFERENCES clientes(id),
                contenido  TEXT    NOT NULL,
                fecha      TEXT    NOT NULL
            );

            INSERT OR IGNORE INTO categorias_gasto (nombre) VALUES
                ('Alquiler'),('Servicios'),('Empleados'),
                ('Publicidad'),('Impuestos'),('Otros');

            INSERT OR IGNORE INTO plantillas_mensaje (nombre, contenido) VALUES
                ('Prendas listas', 'Hola {nombre_cliente}! Tus prendas están listas para retirar 😊'),
                ('Recordatorio deuda', 'Hola {nombre_cliente}, te recordamos que tenés un saldo pendiente.'),
                ('Nuevo catálogo', 'Hola {nombre_cliente}! Tenemos novedades, escribinos para más info 🛍️');

            CREATE TABLE IF NOT EXISTS cajas_proveedor (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                proveedor     TEXT    NOT NULL,
                descripcion   TEXT    NOT NULL DEFAULT '',
                fecha_ingreso TEXT    NOT NULL,
                fecha_retiro  TEXT    NOT NULL DEFAULT '',
                estado        TEXT    NOT NULL DEFAULT 'pendiente',
                notas         TEXT    NOT NULL DEFAULT ''
            );
        """)
    # Migración: codigo_barras en productos
    try:
        conn.execute(
            "ALTER TABLE productos ADD COLUMN codigo_barras TEXT NOT NULL DEFAULT ''"
        )
        conn.commit()
    except Exception:
        pass

    # Migración: montos de pago en ventas
    try:
        conn.execute(
            "ALTER TABLE ventas ADD COLUMN monto_efectivo REAL NOT NULL DEFAULT 0"
        )
        conn.execute(
            "ALTER TABLE ventas ADD COLUMN monto_transferencia REAL NOT NULL DEFAULT 0"
        )
        # Backfill ventas existentes
        conn.execute(
            "UPDATE ventas SET monto_efectivo=total WHERE forma_pago='efectivo'"
        )
        conn.execute(
            "UPDATE ventas SET monto_transferencia=total WHERE forma_pago='transferencia'"
        )
        conn.commit()
    except Exception:
        pass

    # Migración: permiso reportes en roles
    try:
        conn.execute(
            "ALTER TABLE roles ADD COLUMN reportes INTEGER NOT NULL DEFAULT 0"
        )
        conn.execute(
            "UPDATE roles SET reportes=1 WHERE nombre IN ('superadmin', 'usuario')"
        )
        conn.commit()
    except Exception:
        pass

    # Migración: precio_costo en productos
    try:
        conn.execute(
            "ALTER TABLE productos ADD COLUMN precio_costo REAL NOT NULL DEFAULT 0"
        )
        conn.commit()
    except Exception:
        pass

    # Migración: permisos gastos, etiquetas, catalogo en roles
    try:
        conn.execute(
            "ALTER TABLE roles ADD COLUMN gastos INTEGER NOT NULL DEFAULT 0"
        )
        conn.commit()
    except Exception:
        pass
    try:
        conn.execute(
            "ALTER TABLE roles ADD COLUMN etiquetas INTEGER NOT NULL DEFAULT 0"
        )
        conn.commit()
    except Exception:
        pass
    try:
        conn.execute(
            "ALTER TABLE roles ADD COLUMN catalogo INTEGER NOT NULL DEFAULT 0"
        )
        conn.commit()
    except Exception:
        pass
    try:
        conn.execute(
            "UPDATE roles SET gastos=1, etiquetas=1, catalogo=1 "
            "WHERE nombre IN ('superadmin','usuario')"
        )
        conn.execute(
            "UPDATE roles SET etiquetas=1 WHERE nombre='vendedor'"
        )
        conn.commit()
    except Exception:
        pass

    # Migraciones: nuevos campos en clientes
    for col, defn in [
        ("ci",         "TEXT NOT NULL DEFAULT ''"),
        ("correo",     "TEXT NOT NULL DEFAULT ''"),
        ("cumpleanos", "TEXT NOT NULL DEFAULT ''"),
        ("activo",     "INTEGER NOT NULL DEFAULT 1"),
        ("apellido",   "TEXT NOT NULL DEFAULT ''"),
    ]:
        try:
            conn.execute(f"ALTER TABLE clientes ADD COLUMN {col} {defn}")
            conn.commit()
        except Exception:
            pass

    # Migración: marca en productos
    try:
        conn.execute("ALTER TABLE productos ADD COLUMN marca TEXT NOT NULL DEFAULT ''")
        conn.commit()
    except Exception:
        pass

    # Migración: notas en ventas
    try:
        conn.execute("ALTER TABLE ventas ADD COLUMN notas TEXT NOT NULL DEFAULT ''")
        conn.commit()
    except Exception:
        pass

    # Migraciones: compras
    for col, defn in [
        ("numero_factura", "TEXT NOT NULL DEFAULT ''"),
        ("forma_pago",     "TEXT NOT NULL DEFAULT 'efectivo'"),
    ]:
        try:
            conn.execute(f"ALTER TABLE compras ADD COLUMN {col} {defn}")
            conn.commit()
        except Exception:
            pass

    # Migraciones: gastos
    for col, defn in [
        ("proveedor",          "TEXT NOT NULL DEFAULT ''"),
        ("numero_comprobante", "TEXT NOT NULL DEFAULT ''"),
        ("forma_pago",         "TEXT NOT NULL DEFAULT ''"),
    ]:
        try:
            conn.execute(f"ALTER TABLE gastos ADD COLUMN {col} {defn}")
            conn.commit()
        except Exception:
            pass

    # Migraciones: despachos
    for col, defn in [
        ("direccion_envio", "TEXT NOT NULL DEFAULT ''"),
        ("costo_envio",     "REAL NOT NULL DEFAULT 0"),
    ]:
        try:
            conn.execute(f"ALTER TABLE despachos ADD COLUMN {col} {defn}")
            conn.commit()
        except Exception:
            pass

    # Migración: renombrar variable en plantillas de WhatsApp
    try:
        conn.execute(
            "UPDATE plantillas_mensaje "
            "SET contenido = REPLACE(contenido, '{nombre_clienta}', '{nombre_cliente}')"
        )
        conn.commit()
    except Exception:
        pass

    conn.close()
