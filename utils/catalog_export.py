from __future__ import annotations
import base64
import html
from pathlib import Path

from utils.export import export_excel


def export_catalog_html(
    productos: list[dict],
    filepath: str,
    whatsapp: str = "",
) -> None:
    """
    Genera un HTML estático responsivo con grid de productos.
    - Fotos base64 embebidas si existen
    - Filtros JS por categoría
    - Botón WhatsApp por producto
    - Badge 'Sin stock' si stock=0
    """
    categories: list[str] = sorted({
        p.get("categoria_nombre") or "Sin categoría"
        for p in productos
    })

    product_cards = []
    for p in productos:
        cat = p.get("categoria_nombre") or "Sin categoría"
        nombre = html.escape(p.get("nombre", ""))
        talle  = html.escape(p.get("talle", ""))
        color  = html.escape(p.get("color", ""))
        precio = p.get("precio", 0) or 0
        stock  = p.get("stock", 0) or 0
        desc   = html.escape(p.get("descripcion", ""))

        # Embed image as base64 if available
        img_html = _img_tag(p.get("foto_path", ""))

        sin_stock_badge = (
            '<span class="badge-sin-stock">Sin stock</span>'
            if stock == 0 else ""
        )

        detail_parts = []
        if talle:
            detail_parts.append(f"Talle: {talle}")
        if color:
            detail_parts.append(color)
        detail_str = " · ".join(detail_parts)

        wa_btn = ""
        if whatsapp:
            wa_num = whatsapp.lstrip("+").replace(" ", "").replace("-", "")
            import urllib.parse
            msg = urllib.parse.quote(f"Me interesa {p.get('nombre','')}")
            wa_btn = (
                f'<a class="wa-btn" href="https://wa.me/{wa_num}?text={msg}" '
                f'target="_blank">💬 Consultar</a>'
            )

        card = f"""
        <div class="product-card" data-cat="{html.escape(cat)}">
            <div class="card-img">{img_html}{sin_stock_badge}</div>
            <div class="card-body">
                <div class="cat-label">{html.escape(cat)}</div>
                <div class="product-name">{nombre}</div>
                <div class="product-detail">{detail_str}</div>
                {'<div class="product-desc">' + desc + '</div>' if desc else ''}
                <div class="product-price">Gs. {precio:,.0f}</div>
                {wa_btn}
            </div>
        </div>"""
        product_cards.append((cat, card))

    cards_html = "\n".join(c for _, c in product_cards)

    filter_btns = '<button class="filter-btn active" onclick="filterCat(this,\'all\')">Todos</button>\n'
    for cat in categories:
        filter_btns += (
            f'<button class="filter-btn" onclick="filterCat(this,\'{html.escape(cat)}\')">'
            f'{html.escape(cat)}</button>\n'
        )

    page = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Catálogo</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: sans-serif; background: #f8f8f8; color: #222; }}
  h1 {{ text-align: center; padding: 24px 16px 8px; font-size: 1.8rem; }}
  .filters {{ display: flex; flex-wrap: wrap; gap: 8px; justify-content: center;
              padding: 12px 16px 16px; }}
  .filter-btn {{ padding: 6px 16px; border-radius: 20px; border: 1px solid #ccc;
                 background: #fff; cursor: pointer; font-size: 0.9rem; }}
  .filter-btn.active {{ background: #222; color: #fff; border-color: #222; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
           gap: 16px; padding: 16px; max-width: 1200px; margin: 0 auto; }}
  .product-card {{ background: #fff; border-radius: 10px; overflow: hidden;
                   box-shadow: 0 2px 8px rgba(0,0,0,.08); display: flex;
                   flex-direction: column; }}
  .card-img {{ position: relative; width: 100%; padding-top: 100%;
               background: #eee; overflow: hidden; }}
  .card-img img {{ position: absolute; inset: 0; width: 100%; height: 100%;
                   object-fit: cover; }}
  .card-img .placeholder {{ position: absolute; inset: 0; display: flex;
                             align-items: center; justify-content: center;
                             font-size: 3rem; color: #bbb; }}
  .badge-sin-stock {{ position: absolute; top: 8px; right: 8px;
                      background: #e63946; color: #fff; font-size: 0.75rem;
                      padding: 3px 8px; border-radius: 12px; font-weight: bold; }}
  .card-body {{ padding: 12px; flex: 1; display: flex; flex-direction: column; gap: 4px; }}
  .cat-label {{ font-size: 0.72rem; color: #888; text-transform: uppercase;
                letter-spacing: .05em; }}
  .product-name {{ font-size: 1rem; font-weight: 700; }}
  .product-detail {{ font-size: 0.85rem; color: #666; }}
  .product-desc {{ font-size: 0.8rem; color: #999; }}
  .product-price {{ font-size: 1.2rem; font-weight: 700; margin-top: auto;
                    padding-top: 8px; color: #222; }}
  .wa-btn {{ display: inline-block; margin-top: 8px; padding: 6px 14px;
             background: #25d366; color: #fff; border-radius: 20px;
             text-decoration: none; font-size: 0.85rem; font-weight: 600; }}
  .hidden {{ display: none !important; }}
</style>
</head>
<body>
<h1>Catálogo</h1>
<div class="filters">
{filter_btns}
</div>
<div class="grid" id="grid">
{cards_html}
</div>
<script>
function filterCat(btn, cat) {{
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  document.querySelectorAll('.product-card').forEach(card => {{
    if (cat === 'all' || card.dataset.cat === cat) {{
      card.classList.remove('hidden');
    }} else {{
      card.classList.add('hidden');
    }}
  }});
}}
</script>
</body>
</html>"""

    Path(filepath).write_text(page, encoding="utf-8")


def export_catalog_excel(productos: list[dict], filepath: str) -> None:
    """
    Excel compatible Mercado Libre / Tienda Nube.
    Columnas: Título | Descripción | Precio | Stock | Talle | Color | Categoría | Código | Foto
    """
    headers = [
        "Título", "Descripción", "Precio", "Stock",
        "Talle", "Color", "Categoría", "Código", "Foto",
    ]
    rows = [
        [
            p.get("nombre", ""),
            p.get("descripcion", ""),
            p.get("precio", 0),
            p.get("stock", 0),
            p.get("talle", ""),
            p.get("color", ""),
            p.get("categoria_nombre", ""),
            p.get("codigo_barras", ""),
            p.get("foto_path", ""),
        ]
        for p in productos
    ]
    export_excel(filepath, [{"title": "Catálogo", "headers": headers, "rows": rows}])


# ── helpers ───────────────────────────────────────────────────────────────────

def _img_tag(foto_path: str) -> str:
    if foto_path:
        p = Path(foto_path)
        if p.exists():
            ext = p.suffix.lower().lstrip(".")
            mime = {
                "jpg": "image/jpeg", "jpeg": "image/jpeg",
                "png": "image/png",  "webp": "image/webp",
            }.get(ext, "image/jpeg")
            try:
                data = base64.b64encode(p.read_bytes()).decode("ascii")
                return f'<img src="data:{mime};base64,{data}" alt="foto">'
            except Exception:
                pass
    return '<div class="placeholder">🛍️</div>'
