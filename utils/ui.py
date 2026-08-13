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
