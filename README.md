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

## Instalación en Windows

1. Instalá [Python 3.10+](https://www.python.org/downloads/) (marcá **Add python.exe to PATH**) y [Git](https://git-scm.com/download/win).
2. Abrí PowerShell o CMD y cloná el repo:

```bat
git clone https://github.com/ichichavez/Vainilla-Ecotienda-POS.git
cd Vainilla-Ecotienda-POS
```

3. Doble clic en estos scripts, en orden:

| Script | Qué hace |
|--------|----------|
| `instalar.bat` | Crea el entorno e instala dependencias |
| `crear_usuario.bat` | Crea el admin (editá antes `setup_user.py`) |
| `iniciar.bat` | Abre el punto de venta |
| `crear_acceso_directo.bat` | Crea un acceso directo en el Escritorio |
| `actualizar.bat` | Trae cambios de GitHub (`git pull`) |

La base SQLite (`ventas.db`) se crea sola y **no** se pisa al actualizar.

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
