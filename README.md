# Punto de Venta · Analia

Aplicación de escritorio para gestión de ventas, stock, clientes y caja.

## Stack

- **Python 3** + [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) (UI)
- **SQLite** (`ventas.db`, se crea al iniciar)
- **Pillow** (imágenes de productos)
- **openpyxl** / **reportlab** (exportación Excel y PDF / etiquetas)

## Módulos

| Módulo | Descripción |
|--------|-------------|
| Dashboard | Resumen del día (efectivo, transferencia, ventas) |
| Nueva Venta | Carga de ventas con cliente y formas de pago |
| Clientes | ABM, detalle, despachos y mensajes WhatsApp |
| Productos | Stock, categorías, fotos, código de barras |
| Caja | Movimientos del día |
| Compras | Ingreso de mercadería y cajas de proveedor |
| Gastos | Gastos por categoría |
| Reportes | Reportes e exportación |
| Etiquetas / Catálogo | PDF de etiquetas y catálogo |
| Usuarios | Roles y permisos (superadmin, vendedor, usuario) |

## Instalación

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Uso

```bash
python main.py
```

La primera vez se inicializa la base SQLite. Para crear un usuario administrador:

```bash
python setup_user.py
```

Editá `username` y `password` en `setup_user.py` antes de ejecutarlo (no subas contraseñas reales al repo).

## Estructura

```
├── main.py           # Entrada
├── database.py       # Schema SQLite y migraciones
├── setup_user.py     # Crear/actualizar usuario admin
├── models/           # Acceso a datos
├── views/            # Pantallas CustomTkinter
├── utils/            # Export Excel/PDF, iconos
└── assets/productos/ # Fotos de productos (local)
```

## Notas

- `ventas.db` y fotos de productos están en `.gitignore` (datos locales).
- Los permisos por rol se definen en la tabla `roles` y controlan el menú lateral.
