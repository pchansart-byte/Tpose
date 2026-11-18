"""Colours, type and small formatting helpers."""

from __future__ import annotations

import math
import sys
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
ROW_ALT = "#F7F2E9"
ACCENT = "#D65435"
ACCENT_DARK = "#B94329"
ACCENT_HOVER = "#B94329"
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


def _pick_font(candidates: list[str]) -> str:
    try:
        import tkinter.font as tkfont
        from tkinter import _default_root

        if _default_root is not None:
            available = {name.lower(): name for name in tkfont.families(_default_root)}
            for candidate in candidates:
                if candidate.lower() in available:
                    return available[candidate.lower()]
    except Exception:
        pass
    return candidates[0]


def set_language_font(lang: str) -> None:
    global SANS, SERIF
    if lang == "zh":
        SANS = _pick_font([
            "Microsoft YaHei UI", "Microsoft YaHei", "Noto Sans CJK SC",
            "WenQuanYi Zen Hei", "Arial Unicode MS", "DejaVu Sans",
        ])
        SERIF = _pick_font([
            "SimSun", "Noto Serif CJK SC", "Songti SC", "DejaVu Serif",
        ])
    elif lang == "ja":
        SANS = _pick_font([
            "Yu Gothic UI", "Yu Gothic", "Meiryo UI", "Meiryo",
            "Noto Sans CJK JP", "TakaoPGothic", "DejaVu Sans",
        ])
        SERIF = _pick_font([
            "Yu Mincho", "Noto Serif CJK JP", "MS Mincho", "DejaVu Serif",
        ])
    else:
        SANS = _pick_font(["Segoe UI", "DejaVu Sans", "Arial"])
        SERIF = _pick_font(["Georgia", "DejaVu Serif", "Times New Roman"])


def font(size: int, weight: str = "normal", family: str | None = None, italic: bool = False):
    family = family or SANS
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


def fmt_chip_duration(seconds: int, lang: str = "es") -> str:
    s = int(seconds)
    if lang == "zh":
        if s < 60:
            return f"{s} 秒"
        if s % 60 == 0:
            return f"{s // 60} 分"
    elif lang == "ja":
        if s < 60:
            return f"{s} 秒"
        if s % 60 == 0:
            return f"{s // 60} 分"
    if s < 60:
        return f"{s} s"
    if s % 60 == 0:
        return f"{s // 60} min"
    m, sec = divmod(s, 60)
    return f"{m}:{sec:02d}"


def fmt_total(seconds: float, lang: str = "es") -> str:
    s = max(0, int(round(seconds)))
    if lang == "zh":
        if s < 60:
            return f"{s} 秒"
        m, sec = divmod(s, 60)
        if m < 60:
            return f"{m} 分" if sec == 0 else f"{m} 分 {sec:02d} 秒"
        h, m = divmod(m, 60)
        sec = s % 60
        if sec:
            return f"{h} 小时 {m:02d} 分 {sec:02d} 秒"
        return f"{h} 小时 {m:02d} 分" if m else f"{h} 小时"
    if lang == "ja":
        if s < 60:
            return f"{s} 秒"
        m, sec = divmod(s, 60)
        if m < 60:
            return f"{m} 分" if sec == 0 else f"{m} 分 {sec:02d} 秒"
        h, m = divmod(m, 60)
        sec = s % 60
        if sec:
            return f"{h} 時間 {m:02d} 分 {sec:02d} 秒"
        return f"{h} 時間 {m:02d} 分" if m else f"{h} 時間"
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
    if lang == "zh":
        return (str(s // 60), "分") if s < 3600 else (f"{s / 3600:.1f}", "小时")
    if lang == "ja":
        return (str(s // 60), "分") if s < 3600 else (f"{s / 3600:.1f}", "時間")
    if s < 3600:
        return (str(s // 60), "min")
    h = s / 3600
    if h < 10:
        return (f"{h:.1f}".replace(".", ","), "h")
    return (str(int(h)), "h")


MONTHS = {
    "es": ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"],
    "en": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
    "zh": [f"{n}月" for n in range(1, 13)],
    "ja": [f"{n}月" for n in range(1, 13)],
}


def fmt_date(iso: str, lang: str = "es", with_time: bool = True) -> str:
    try:
        dt = datetime.fromisoformat(iso).astimezone()
    except (ValueError, TypeError):
        return ""
    months = MONTHS.get(lang, MONTHS["es"])
    if lang == "zh":
        date = f"{dt.year}年{months[dt.month - 1]}{dt.day}日"
        if with_time:
            date += f" · {dt.strftime('%H:%M')}"
    elif lang == "ja":
        date = f"{dt.year}年{months[dt.month - 1]}{dt.day}日"
        if with_time:
            date += f" · {dt.strftime('%H:%M')}"
    elif lang == "en":
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
    if lang == "zh":
        return f"{n} 张图片"
    if lang == "ja":
        return f"{n} 枚の画像"
    if n == 1:
        return "1 pose"
    return f"{n} poses"


def images_label(n: int, lang: str = "es") -> str:
    if lang == "zh":
        return f"{n} 张图片"
    if lang == "ja":
        return f"{n} 枚の画像"
    if n == 1:
        return "1 imagen" if lang == "es" else "1 image"
    return f"{n} imágenes" if lang == "es" else f"{n} images"


def normalize_hex(value: str) -> str:
    return value if value.startswith("#") else f"#{value}"


THEME = "day"


def set_theme(mode: str) -> None:
    """Switch the whole app between the warm day palette and a cool night one."""
    global THEME, CREAM, CREAM_DARK, PAPER, CARD, WHITE, INK, INK_SOFT, MUTED, FAINT
    global LINE, LINE_STRONG, ROW_ALT, ACCENT, ACCENT_DARK, ACCENT_HOVER, ACCENT_SOFT, ACCENT_PALE
    global GREEN, GREEN_SOFT, AMBER, RED, SIDEBAR, SIDEBAR_HOVER, SIDEBAR_ACTIVE
    global SIDEBAR_TEXT, SIDEBAR_MUTED, SIDEBAR_LINE, SESSION_BG, SESSION_PANEL
    global SESSION_PANEL_2, SESSION_LINE, SESSION_TEXT, SESSION_MUTED
    THEME = "night" if mode == "night" else "day"
    if THEME == "night":
        CREAM = "#0E1418"
        CREAM_DARK = "#182229"
        PAPER = "#121B21"
        CARD = "#162127"
        WHITE = "#FFFFFF"
        INK = "#E6F0F5"
        INK_SOFT = "#CBD9E0"
        MUTED = "#9AAEB9"
        FAINT = "#708691"
        LINE = "#26343D"
        LINE_STRONG = "#354854"
        ROW_ALT = "#121C22"
        ACCENT = "#E36A4A"
        ACCENT_DARK = "#FFB59E"
        ACCENT_HOVER = "#B94A32"
        ACCENT_SOFT = "#3A2520"
        ACCENT_PALE = "#2A1D19"
        GREEN = "#86B99A"
        GREEN_SOFT = "#1A3028"
        AMBER = "#D6A35C"
        RED = "#E0796A"
        SIDEBAR = "#0A1014"
        SIDEBAR_HOVER = "#131E25"
        SIDEBAR_ACTIVE = "#1A2932"
        SIDEBAR_TEXT = "#DCE8EE"
        SIDEBAR_MUTED = "#8297A2"
        SIDEBAR_LINE = "#22313A"
        SESSION_BG = "#070C10"
        SESSION_PANEL = "#0D151A"
        SESSION_PANEL_2 = "#142129"
        SESSION_LINE = "#22323C"
        SESSION_TEXT = "#E6F0F5"
        SESSION_MUTED = "#91A5AF"
    else:
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
        ROW_ALT = "#F7F2E9"
        ACCENT = "#D65435"
        ACCENT_DARK = "#B94329"
        ACCENT_HOVER = "#B94329"
        ACCENT_SOFT = "#F3D6CB"
        ACCENT_PALE = "#FAEAE4"
        GREEN = "#4E7259"
        GREEN_SOFT = "#DDE9DE"
        AMBER = "#B97C32"
        RED = "#BC4436"
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
