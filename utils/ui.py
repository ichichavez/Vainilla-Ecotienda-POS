"""UI helpers for CustomTkinter views."""
from __future__ import annotations


def debounce(widget, after_id_attr: str, delay_ms: int, callback):
    """Cancel a previous after() and schedule callback after delay_ms.

    Usage:
        self._search_var.trace_add(
            "write",
            lambda *_: debounce(self, "_search_after", 250, self._load),
        )
    """
    prev = getattr(widget, after_id_attr, None)
    if prev is not None:
        try:
            widget.after_cancel(prev)
        except Exception:
            pass
    setattr(widget, after_id_attr, widget.after(delay_ms, callback))


def render_in_batches(widget, items, batch_size: int, render_fn, start: int = 0):
    """Render list items in chunks so the UI stays responsive."""
    end = min(start + batch_size, len(items))
    for i in range(start, end):
        render_fn(items[i], i)
    if end < len(items):
        widget.after(1, lambda: render_in_batches(
            widget, items, batch_size, render_fn, end))
