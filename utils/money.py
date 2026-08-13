"""Currency display helpers (Paraguayan Guaraní)."""


def money(amount: float | int | None) -> str:
    """Format an amount as Gs. 1,234.56"""
    if amount is None:
        amount = 0
    return f"Gs. {float(amount):,.2f}"
