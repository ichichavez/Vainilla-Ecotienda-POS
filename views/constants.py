"""Shared constants for navigation and cache invalidation."""

DIRTY_AFTER_SALE = (
    "dashboard", "caja", "clientes", "productos",
    "reportes", "movimientos", "etiquetas", "catalogo",
)
DIRTY_AFTER_STOCK = DIRTY_AFTER_SALE + ("compras", "cajas_proveedor")

# Rows rendered per UI frame when building long lists
LIST_BATCH_SIZE = 30
