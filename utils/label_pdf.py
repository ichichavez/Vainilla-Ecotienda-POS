from __future__ import annotations

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
    from reportlab.graphics.barcode.code128 import Code128
    REPORTLAB_AVAILABLE = True
except ImportError:
    Code128 = None  # type: ignore[misc, assignment]
    REPORTLAB_AVAILABLE = False

LABEL_COLS = 3
LABEL_ROWS = 8


def generate_labels_pdf(filepath: str, items: list[dict]) -> None:
    """
    items: [{"producto": dict, "cantidad": int}, ...]
    Genera PDF A4 con grid 3×8 (24 etiquetas por página).
    Cada etiqueta muestra nombre, talle+color, precio grande y código de barras CODE128.
    """
    if not REPORTLAB_AVAILABLE:
        raise RuntimeError(
            "reportlab no está instalado. Ejecutá: pip install reportlab"
        )

    PAGE_W, PAGE_H = A4
    MARGIN = 5 * mm
    COL_W = (PAGE_W - 2 * MARGIN) / LABEL_COLS
    ROW_H = (PAGE_H - 2 * MARGIN) / LABEL_ROWS

    # Flatten labels
    labels: list = []
    for item in items:
        prod = item["producto"]
        for _ in range(max(1, int(item.get("cantidad", 1)))):
            labels.append(_make_label(prod, COL_W))

    # Pad to full rows
    while len(labels) % LABEL_COLS != 0:
        labels.append("")

    table_rows = [
        labels[i: i + LABEL_COLS]
        for i in range(0, len(labels), LABEL_COLS)
    ]

    table = Table(
        table_rows,
        colWidths=[COL_W] * LABEL_COLS,
        rowHeights=[ROW_H] * len(table_rows),
    )
    table.setStyle(TableStyle([
        ("GRID",          (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("LEFTPADDING",   (0, 0), (-1, -1), 3),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 3),
        ("TOPPADDING",    (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))

    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN,  bottomMargin=MARGIN,
    )
    doc.build([table])


def _make_label(prod: dict, col_w: float) -> list:
    styles = getSampleStyleSheet()

    nombre_style = ParagraphStyle(
        "lbl_nombre", parent=styles["Normal"],
        fontSize=7, alignment=1, leading=9, fontName="Helvetica-Bold",
    )
    detail_style = ParagraphStyle(
        "lbl_detail", parent=styles["Normal"],
        fontSize=6, alignment=1, leading=7,
        textColor=colors.HexColor("#666666"),
    )
    price_style = ParagraphStyle(
        "lbl_price", parent=styles["Normal"],
        fontSize=13, alignment=1, leading=16, fontName="Helvetica-Bold",
    )

    nombre = str(prod.get("nombre", ""))[:20]
    talle  = prod.get("talle", "")
    color  = prod.get("color", "")
    precio = prod.get("precio", 0) or 0
    codigo = str(prod.get("codigo_barras", "") or prod.get("id", ""))

    content: list = [Paragraph(nombre, nombre_style)]

    parts = []
    if talle:
        parts.append(f"T:{talle}")
    if color:
        parts.append(color)
    if parts:
        content.append(Paragraph(" · ".join(parts), detail_style))

    content.append(Paragraph(f"Gs. {precio:,.0f}", price_style))

    if codigo:
        try:
            bc = Code128(
                codigo,
                barHeight=7 * mm,
                barWidth=0.25 * mm,
                quiet=0,
            )
            bc.hAlign = "CENTER"
            content.append(bc)
        except Exception:
            pass

    return content
