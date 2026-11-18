"""Colours, type and small formatting helpers."""

from __future__ import annotations

import math
from datetime import datetime

# Light editorial palette for the studio.
CREAM = "#F3EDE3"
CREAM_DARK = "#E9DFD1"
PAPER = "#FBF8F2"
CARD = "#FBF8F2"
WHITE = "#FFFFFF"
INK = "#211C18"
INK_SOFT = "#3A322B"
MUTED = "#7C6F63"
FAINT = "#A89A8C"
LINE = "#DDD0C0"
LINE_STRONG = "#C9B8A5"
ACCENT = "#D65435"
ACCENT_DARK = "#B94329"
ACCENT_SOFT = "#F3D6CB"
ACCENT_PALE = "#FAEAE4"
GREEN = "#4E7259"
GREEN_SOFT = "#DDE9DE"
AMBER = "#B97C32"
RED = "#BC4436"

# Sidebar and immersive session.
SIDEBAR = "#1B1815"
SIDEBAR_HOVER = "#29241F"
SIDEBAR_ACTIVE = "#332C25"
SIDEBAR_TEXT = "#EFE6DA"
SIDEBAR_MUTED = "#9B8D7F"
SIDEBAR_LINE = "#352F29"

SESSION_BG = "#0C0B0A"
SESSION_PANEL = "#151210"
SESSION_PANEL_2 = "#1D1915"
SESSION_LINE = "#302A24"
SESSION_TEXT = "#F5EEE4"
SESSION_MUTED = "#A09386"

SANS = "Segoe UI"
SERIF = "Georgia"


def font(size: int, weight: str = "normal", family: str = SANS, italic: bool = False):
    style = ""
    if weight and weight != "normal":
        style = weight
    if italic:
        style = (style + " italic").strip()
    return (family, size, style) if style else (family, size)


def fit_scale(screen_h: int) -> float:
    """A gentle scale for very short screens; typography otherwise stays put."""
    return max(0.86, min(1.0, screen_h / 960))


def fmt_clock(seconds: float) -> str:
    seconds = max(0, int(math.ceil(seconds - 1e-6)))
    m, s = divmod(seconds, 60)
    if m >= 60:
        h, m = divmod(m, 60)
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def fmt_elapsed(seconds: float) -> str:
    seconds = max(0, int(seconds))
    m, s = divmod(seconds, 60)
    if m >= 60:
        h, m = divmod(m, 60)
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def fmt_short_duration(seconds: int, lang: str = "es") -> str:
    s = int(seconds)
    if s < 60:
        return f"{s} s"
    if s % 60 == 0:
        n = s // 60
        if n < 60:
            return f"{n} min"
        h, m = divmod(n, 60)
        return f"{h} h" if m == 0 else f"{h} h {m:02d} min"
    m, sec = divmod(s, 60)
    if m < 60:
        return f"{m} min {sec:02d} s"
    h, m = divmod(m, 60)
    return f"{h} h {m:02d} min"


def fmt_chip_duration(seconds: int) -> str:
    s = int(seconds)
    if s < 60:
        return f"{s} s"
    if s % 60 == 0:
        return f"{s // 60} min"
    m, sec = divmod(s, 60)
    return f"{m}:{sec:02d}"


def fmt_total(seconds: float, lang: str = "es") -> str:
    s = max(0, int(round(seconds)))
    if s < 60:
        return f"{s} s"
    m, sec = divmod(s, 60)
    if m < 60:
        if sec == 0:
            return f"{m} min"
        return f"{m} min {sec:02d} s"
    h, m = divmod(m, 60)
    sec = s % 60
    if sec:
        return f"{h} h {m:02d} min {sec:02d} s"
    if m:
        return f"{h} h {m:02d} min"
    return f"{h} h"


def fmt_hours_minutes(seconds: float, lang: str = "es") -> tuple[str, str]:
    """Return a large value and a small unit label for stat cards."""
    s = max(0, int(round(seconds)))
    if s < 3600:
        return (str(s // 60), "min")
    h = s / 3600
    if h < 10:
        return (f"{h:.1f}".replace(".", ","), "h")
    return (str(int(h)), "h")


MONTHS = {
    "es": ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"],
    "en": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
}


def fmt_date(iso: str, lang: str = "es", with_time: bool = True) -> str:
    try:
        dt = datetime.fromisoformat(iso).astimezone()
    except (ValueError, TypeError):
        return ""
    months = MONTHS.get(lang, MONTHS["es"])
    if lang == "en":
        date = f"{months[dt.month - 1]} {dt.day}, {dt.year}"
        if with_time:
            date += f" · {dt.strftime('%I:%M %p').lstrip('0')}"
    else:
        date = f"{dt.day} {months[dt.month - 1]} {dt.year}"
        if with_time:
            date += f" · {dt.strftime('%H:%M')}"
    return date


def fmt_int(n: int | float) -> str:
    return f"{int(n):,}".replace(",", ".")


def poses_label(n: int, lang: str = "es") -> str:
    if n == 1:
        return "1 pose"
    return f"{n} poses"


def images_label(n: int, lang: str = "es") -> str:
    if n == 1:
        return "1 imagen" if lang == "es" else "1 image"
    return f"{n} imágenes" if lang == "es" else f"{n} images"


def normalize_hex(value: str) -> str:
    return value if value.startswith("#") else f"#{value}"
