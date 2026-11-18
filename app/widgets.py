"""Custom Tk widgets: buttons, toggles, navigation and layout helpers."""

from __future__ import annotations

import tkinter as tk
import tkinter.font as tkfont
from typing import Callable

from . import theme as T


def _round_points(x1, y1, x2, y2, r):
    r = max(1, min(r, (x2 - x1) / 2, (y2 - y1) / 2))
    return [
        x1 + r, y1, x1 + r, y1, x2 - r, y1, x2 - r, y1,
        x2, y1, x2, y1 + r, x2, y1 + r, x2, y2 - r, x2, y2 - r,
        x2, y2, x2 - r, y2, x2 - r, y2, x1 + r, y2, x1 + r, y2,
        x1, y2, x1, y2 - r, x1, y2 - r, x1, y1 + r, x1, y1 + r, x1, y1,
    ]


def round_rect(canvas: tk.Canvas, x1, y1, x2, y2, radius, fill, outline="", width=0, tags=None):
    pts = _round_points(x1, y1, x2, y2, radius)
    return canvas.create_polygon(
        pts, smooth=True, splinesteps=24, fill=fill, outline=outline, width=width, tags=tags
    )


def parent_bg(widget: tk.Misc) -> str:
    try:
        return widget.cget("bg")
    except tk.TclError:
        try:
            return widget.cget("background")
        except tk.TclError:
            return T.CREAM


def draw_icon(canvas: tk.Canvas, name: str, cx: float, cy: float, size: float, color: str, width: float = 1.8):
    s = size / 2.0
    w = max(1.0, width)
    kw = {"fill": color, "width": w, "capstyle": "round", "joinstyle": "round"}
    line = canvas.create_line

    if name == "close":
        line(cx - s * 0.62, cy - s * 0.62, cx + s * 0.62, cy + s * 0.62, **kw)
        line(cx + s * 0.62, cy - s * 0.62, cx - s * 0.62, cy + s * 0.62, **kw)
    elif name == "play":
        canvas.create_polygon(cx - s * 0.45, cy - s * 0.72, cx + s * 0.78, cy, cx - s * 0.45, cy + s * 0.72,
                              fill=color, outline="")
    elif name == "pause":
        canvas.create_rectangle(cx - s * 0.52, cy - s * 0.7, cx - s * 0.16, cy + s * 0.7, fill=color, outline="")
        canvas.create_rectangle(cx + s * 0.16, cy - s * 0.7, cx + s * 0.52, cy + s * 0.7, fill=color, outline="")
    elif name == "next":
        canvas.create_polygon(cx - s * 0.66, cy - s * 0.58, cx + s * 0.28, cy, cx - s * 0.66, cy + s * 0.58,
                              fill=color, outline="")
        line(cx + s * 0.58, cy - s * 0.65, cx + s * 0.58, cy + s * 0.65, **kw)
    elif name == "prev":
        canvas.create_polygon(cx + s * 0.66, cy - s * 0.58, cx - s * 0.28, cy, cx + s * 0.66, cy + s * 0.58,
                              fill=color, outline="")
        line(cx - s * 0.58, cy - s * 0.65, cx - s * 0.58, cy + s * 0.65, **kw)
    elif name == "expand":
        for sx, sy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
            line(cx + sx * s * 0.72, cy + sy * s * 0.72, cx + sx * s * 0.72 - sx * s * 0.34,
                 cy + sy * s * 0.72, **kw)
            line(cx + sx * s * 0.72, cy + sy * s * 0.72, cx + sx * s * 0.72,
                 cy + sy * s * 0.72 - sy * s * 0.34, **kw)
    elif name == "contract":
        for sx, sy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
            line(cx + sx * s * 0.38, cy + sy * s * 0.38, cx + sx * s * 0.72,
                 cy + sy * s * 0.38, **kw)
            line(cx + sx * s * 0.38, cy + sy * s * 0.38, cx + sx * s * 0.38,
                 cy + sy * s * 0.72, **kw)
    elif name in ("sound", "mute"):
        canvas.create_polygon(
            cx - s * 0.78, cy - s * 0.18, cx - s * 0.42, cy - s * 0.18, cx - s * 0.02, cy - s * 0.56,
            cx - s * 0.02, cy + s * 0.56, cx - s * 0.42, cy + s * 0.18, cx - s * 0.78, cy + s * 0.18,
            fill=color, outline="",
        )
        if name == "sound":
            line(cx + s * 0.14, cy - s * 0.30, cx + s * 0.38, cy, cx + s * 0.14, cy + s * 0.30, **kw)
            line(cx + s * 0.36, cy - s * 0.48, cx + s * 0.62, cy, cx + s * 0.36, cy + s * 0.48, **kw)
        else:
            line(cx + s * 0.18, cy - s * 0.36, cx + s * 0.72, cy + s * 0.36, **kw)
            line(cx + s * 0.72, cy - s * 0.36, cx + s * 0.18, cy + s * 0.36, **kw)
    elif name in ("timer", "timer_off"):
        canvas.create_oval(cx - s * 0.62, cy - s * 0.62, cx + s * 0.62, cy + s * 0.62,
                           outline=color, width=w)
        line(cx, cy, cx, cy - s * 0.36, **kw)
        line(cx, cy, cx + s * 0.28, cy + s * 0.08, **kw)
        if name == "timer_off":
            line(cx - s * 0.78, cy + s * 0.78, cx + s * 0.78, cy - s * 0.78, **kw)
    elif name == "clock":
        canvas.create_oval(cx - s * 0.68, cy - s * 0.68, cx + s * 0.68, cy + s * 0.68,
                           outline=color, width=w)
        line(cx, cy, cx, cy - s * 0.38, **kw)
        line(cx, cy, cx + s * 0.30, cy + s * 0.14, **kw)
    elif name == "folder":
        line(cx - s * 0.74, cy - s * 0.38, cx - s * 0.20, cy - s * 0.38, cx + s * 0.02, cy - s * 0.62,
             **kw)
        canvas.create_line(cx - s * 0.74, cy - s * 0.38, cx + s * 0.74, cy - s * 0.38,
                           cx + s * 0.74, cy + s * 0.56, cx - s * 0.74, cy + s * 0.56,
                           cx - s * 0.74, cy - s * 0.38, **kw)
    elif name == "plus":
        line(cx - s * 0.64, cy, cx + s * 0.64, cy, **kw)
        line(cx, cy - s * 0.64, cx, cy + s * 0.64, **kw)
    elif name == "trash":
        line(cx - s * 0.62, cy - s * 0.46, cx + s * 0.62, cy - s * 0.46, **kw)
        line(cx - s * 0.26, cy - s * 0.72, cx + s * 0.26, cy - s * 0.72, **kw)
        line(cx - s * 0.48, cy - s * 0.46, cx - s * 0.38, cy + s * 0.66, **kw)
        line(cx + s * 0.48, cy - s * 0.46, cx + s * 0.38, cy + s * 0.66, **kw)
        line(cx - s * 0.38, cy + s * 0.66, cx + s * 0.38, cy + s * 0.66, **kw)
    elif name == "shuffle":
        line(cx - s * 0.76, cy - s * 0.36, cx - s * 0.28, cy - s * 0.36, cx, cy, cx + s * 0.54, cy, **kw)
        line(cx - s * 0.76, cy + s * 0.36, cx - s * 0.28, cy + s * 0.36, cx, cy, cx + s * 0.54, cy, **kw)
        line(cx + s * 0.32, cy - s * 0.18, cx + s * 0.62, cy, cx + s * 0.32, cy + s * 0.18, **kw)
        line(cx + s * 0.32, cy - s * 0.54, cx + s * 0.62, cy - s * 0.36, cx + s * 0.32, cy - s * 0.18, **kw)
    elif name == "contrast":
        canvas.create_oval(cx - s * 0.68, cy - s * 0.68, cx + s * 0.68, cy + s * 0.68,
                           outline=color, width=w)
        canvas.create_arc(cx - s * 0.68, cy - s * 0.68, cx + s * 0.68, cy + s * 0.68,
                          start=90, extent=-180, style="chord", fill=color, outline=color)
    elif name == "rotate":
        canvas.create_arc(cx - s * 0.64, cy - s * 0.64, cx + s * 0.64, cy + s * 0.64,
                          start=36, extent=286, style="arc", outline=color, width=w)
        line(cx + s * 0.42, cy - s * 0.70, cx + s * 0.76, cy - s * 0.46,
             cx + s * 0.42, cy - s * 0.30, **kw)
    elif name == "flip":
        line(cx, cy - s * 0.78, cx, cy + s * 0.78, **kw)
        canvas.create_polygon(cx - s * 0.12, cy - s * 0.55, cx - s * 0.82, cy, cx - s * 0.12, cy + s * 0.55,
                              fill=color, outline="")
        canvas.create_polygon(cx + s * 0.12, cy - s * 0.55, cx + s * 0.82, cy, cx + s * 0.12, cy + s * 0.55,
                              fill="", outline=color, width=w)
    elif name == "flip_h":
        line(cx, cy - s * 0.74, cx, cy + s * 0.74, **kw)
        canvas.create_polygon(cx - s * 0.16, cy - s * 0.52, cx - s * 0.78, cy, cx - s * 0.16, cy + s * 0.52,
                              fill=color, outline="")
        canvas.create_polygon(cx + s * 0.16, cy - s * 0.52, cx + s * 0.78, cy, cx + s * 0.16, cy + s * 0.52,
                              outline=color, width=w)
    elif name == "flip_v":
        line(cx - s * 0.74, cy, cx + s * 0.74, cy, **kw)
        canvas.create_polygon(cx - s * 0.52, cy - s * 0.16, cx, cy - s * 0.78, cx + s * 0.52, cy - s * 0.16,
                              fill=color, outline="")
        canvas.create_polygon(cx - s * 0.52, cy + s * 0.16, cx, cy + s * 0.78, cx + s * 0.52, cy + s * 0.16,
                              outline=color, width=w)
    elif name == "grid":
        for gx in (-1, 1):
            for gy in (-1, 1):
                canvas.create_rectangle(cx + gx * s * 0.7 - s * 0.22, cy + gy * s * 0.7 - s * 0.22,
                                        cx + gx * s * 0.7 + s * 0.22, cy + gy * s * 0.7 + s * 0.22,
                                        outline=color, width=w)
    elif name == "info":
        canvas.create_oval(cx - s * 0.7, cy - s * 0.7, cx + s * 0.7, cy + s * 0.7,
                           outline=color, width=w)
        line(cx, cy - s * 0.05, cx, cy + s * 0.42, **kw)
        canvas.create_oval(cx - s * 0.09, cy - s * 0.45, cx + s * 0.09, cy - s * 0.27,
                           fill=color, outline="")
    elif name == "book":
        line(cx - s * 0.76, cy - s * 0.54, cx - s * 0.10, cy - s * 0.36, cx - s * 0.10, cy + s * 0.62,
             cx - s * 0.76, cy + s * 0.44, cx - s * 0.76, cy - s * 0.54, **kw)
        line(cx + s * 0.76, cy - s * 0.54, cx + s * 0.10, cy - s * 0.36, cx + s * 0.10, cy + s * 0.62,
             cx + s * 0.76, cy + s * 0.44, cx + s * 0.76, cy - s * 0.54, **kw)
    elif name == "image":
        canvas.create_rectangle(cx - s * 0.76, cy - s * 0.58, cx + s * 0.76, cy + s * 0.58,
                                outline=color, width=w)
        canvas.create_oval(cx + s * 0.18, cy - s * 0.40, cx + s * 0.42, cy - s * 0.16,
                           outline=color, width=w)
        line(cx - s * 0.64, cy + s * 0.42, cx - s * 0.14, cy - s * 0.10, cx + s * 0.12, cy + s * 0.18,
             cx + s * 0.34, cy - s * 0.02, cx + s * 0.66, cy + s * 0.42, **kw)
    elif name == "arrow_left":
        line(cx + s * 0.6, cy, cx - s * 0.62, cy, **kw)
        line(cx - s * 0.62, cy, cx - s * 0.22, cy - s * 0.4, **kw)
        line(cx - s * 0.62, cy, cx - s * 0.22, cy + s * 0.4, **kw)
    elif name == "arrow_right":
        line(cx - s * 0.6, cy, cx + s * 0.62, cy, **kw)
        line(cx + s * 0.62, cy, cx + s * 0.22, cy - s * 0.4, **kw)
        line(cx + s * 0.62, cy, cx + s * 0.22, cy + s * 0.4, **kw)
    elif name == "chevron_right":
        line(cx - s * 0.26, cy - s * 0.52, cx + s * 0.28, cy, cx - s * 0.26, cy + s * 0.52, **kw)
    elif name == "check":
        line(cx - s * 0.58, cy + s * 0.02, cx - s * 0.12, cy + s * 0.48, cx + s * 0.64, cy - s * 0.46, **kw)
    elif name == "spark":
        line(cx, cy - s * 0.74, cx, cy + s * 0.74, **kw)
        line(cx - s * 0.74, cy, cx + s * 0.74, cy, **kw)
        line(cx - s * 0.44, cy - s * 0.44, cx + s * 0.44, cy + s * 0.44, **kw)
        line(cx + s * 0.44, cy - s * 0.44, cx - s * 0.44, cy + s * 0.44, **kw)


class CanvasButton(tk.Canvas):
    """A rounded, keyboard-accessible button drawn on a canvas."""

    PALETTES = {
        "primary": (T.ACCENT, T.WHITE, T.ACCENT_DARK, T.WHITE, ""),
        "dark": (T.INK, T.WHITE, "#090807", T.WHITE, ""),
        "secondary": (T.PAPER, T.INK, T.CREAM_DARK, T.INK, T.LINE_STRONG),
        "ghost": (T.CREAM, T.INK, T.CREAM_DARK, T.INK, T.LINE),
        "quiet": ("", T.MUTED, T.CREAM_DARK, T.INK, ""),
        "danger": (T.RED, T.WHITE, "#963329", T.WHITE, ""),
        "accent_soft": (T.ACCENT_SOFT, T.ACCENT_DARK, "#EDC5B6", T.ACCENT_DARK, ""),
        "sidebar": (T.SIDEBAR_HOVER, T.SIDEBAR_TEXT, T.SIDEBAR_ACTIVE, T.SESSION_TEXT, ""),
    }

    def __init__(
        self,
        parent,
        text: str,
        command: Callable | None = None,
        variant: str = "primary",
        width: int | None = None,
        height: int = 42,
        radius: int = 12,
        icon: str | None = None,
        font_size: int = 10,
        bold: bool = True,
        padx: int = 18,
        bg: str | None = None,
        anchor: str = "center",
        tooltip: str | None = None,
        selected: bool = False,
    ):
        self._bg = bg or parent_bg(parent)
        super().__init__(parent, bg=self._bg, highlightthickness=0, bd=0, takefocus=1)
        self._text = text
        self._command = command
        self._variant = variant
        self._radius = radius
        self._icon = icon
        self._font = tkfont.Font(family=T.SANS, size=font_size, weight="bold" if bold else "normal")
        self._padx = padx
        self._anchor = anchor
        self._selected = selected
        self._enabled = True
        self._hover = False
        self._focus = False
        self._height = height
        self._min_width = width if width is not None else self._natural_width()
        self.configure(width=self._min_width, height=height, cursor="hand2")
        self.bind("<Configure>", self._on_configure)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Return>", lambda e: self._invoke())
        self.bind("<space>", lambda e: self._invoke())
        self.bind("<FocusIn>", self._on_focus)
        self.bind("<FocusOut>", self._on_blur)
        self._pressed = False
        self._cw = self._min_width
        self.tooltip = Tooltip(self, tooltip) if tooltip else None
        self._draw()

    def _natural_width(self) -> int:
        return self._font.measure(self._text) + self._padx * 2 + (24 if self._icon else 0)

    def _on_configure(self, event):
        if event.width > 1:
            self._cw = event.width
            self._draw()

    def _on_enter(self, _event=None):
        self._hover = True
        self._draw()

    def _on_leave(self, _event=None):
        self._hover = False
        self._pressed = False
        self._draw()

    def _on_press(self, _event=None):
        if self._enabled:
            self._pressed = True
            self._draw()

    def _on_release(self, event=None):
        was = self._pressed
        self._pressed = False
        self._draw()
        if was and self._enabled:
            x, y = self.winfo_pointerxy()
            widget = self.winfo_containing(x, y)
            if widget is self:
                self._invoke()

    def _on_focus(self, _event=None):
        self._focus = True
        self._draw()

    def _on_blur(self, _event=None):
        self._focus = False
        self._draw()

    def _invoke(self):
        if self._enabled and self._command:
            self._command()

    def set_text(self, text: str, resize: bool = False):
        self._text = text
        if resize or self._cw <= self._natural_width():
            self._min_width = self._natural_width()
            self.configure(width=self._min_width)
        self._draw()

    def set_enabled(self, enabled: bool):
        self._enabled = enabled
        self.configure(cursor="hand2" if enabled else "arrow")
        self._draw()

    def set_selected(self, selected: bool):
        self._selected = selected
        self._draw()

    def set_variant(self, variant: str):
        self._variant = variant
        self._draw()

    def _draw(self):
        self.delete("all")
        h = max(2, self.winfo_height() or self._height)
        w = max(2, self.winfo_width() or self._cw or self._min_width)
        fill, fg, hover, fg_hover, outline = self.PALETTES.get(self._variant, self.PALETTES["primary"])
        if self._variant == "quiet":
            fill_eff, fg_eff = (hover if (self._hover or self._focus) else self._bg), (fg_hover if (self._hover or self._focus) else fg)
        elif self._variant == "secondary" and self._hover:
            fill_eff, fg_eff = hover, fg_hover
        elif self._variant == "ghost" and self._hover:
            fill_eff, fg_eff = hover, fg_hover
        elif self._selected:
            fill_eff, fg_eff, outline = T.ACCENT_SOFT, T.ACCENT_DARK, T.ACCENT
        elif self._hover:
            fill_eff, fg_eff = hover, fg_hover
        else:
            fill_eff, fg_eff = fill, fg
        if not self._enabled:
            fill_eff = self._bg if self._variant in ("quiet", "ghost") else T.CREAM_DARK
            fg_eff = T.FAINT
            outline = T.LINE
        if not fill_eff:
            fill_eff = self._bg
        pad = 1
        round_rect(self, pad, pad, w - pad, h - pad, self._radius, fill_eff, outline, 1)
        if self._focus and self._enabled:
            round_rect(self, 3, 3, w - 3, h - 3, max(2, self._radius - 3), "", T.ACCENT, 1)
        text_x = self._text_x(w)
        if self._icon:
            icon_x = text_x - self._font.measure(self._text) / 2 - 13
            draw_icon(self, self._icon, icon_x, h / 2, 15, fg_eff, 1.6)
        self.create_text(text_x, h / 2, text=self._text, fill=fg_eff, font=self._font, anchor="w" if self._anchor == "left" else "center")
        if self._anchor == "left":
            # For left labels, move the icon to the left edge.
            self.delete("all")
            round_rect(self, pad, pad, w - pad, h - pad, self._radius, fill_eff, outline, 1)
            if self._focus and self._enabled:
                round_rect(self, 3, 3, w - 3, h - 3, max(2, self._radius - 3), "", T.ACCENT, 1)
            if self._icon:
                draw_icon(self, self._icon, 22, h / 2, 16, fg_eff, 1.6)
            self.create_text(42 if self._icon else 16, h / 2, text=self._text, fill=fg_eff, font=self._font, anchor="w")

    def _text_x(self, width: int) -> float:
        if self._anchor == "left":
            return 42 if self._icon else 16
        extra = 13 if self._icon else 0
        return width / 2 + extra / 2


class IconButton(tk.Canvas):
    def __init__(
        self,
        parent,
        icon: str,
        command: Callable | None = None,
        size: int = 38,
        icon_size: int = 18,
        bg: str | None = None,
        fg: str | None = None,
        hover_bg: str | None = None,
        tooltip: str | None = None,
        active: bool = False,
    ):
        self._bg = bg or parent_bg(parent)
        self._fg = fg or T.MUTED
        self._hover_bg = hover_bg or T.CREAM_DARK
        super().__init__(parent, width=size, height=size, bg=self._bg, highlightthickness=0, bd=0, takefocus=1)
        self._icon = icon
        self._command = command
        self._size = size
        self._icon_size = icon_size
        self._hover = False
        self._focus = False
        self._active = active
        self.configure(cursor="hand2")
        self.bind("<Enter>", self._enter)
        self.bind("<Leave>", self._leave)
        self.bind("<Button-1>", self._click)
        self.bind("<Return>", lambda e: self._command and self._command())
        self.bind("<space>", lambda e: self._command and self._command())
        self.bind("<FocusIn>", lambda e: (setattr(self, "_focus", True), self._draw()))
        self.bind("<FocusOut>", lambda e: (setattr(self, "_focus", False), self._draw()))
        self.tooltip = Tooltip(self, tooltip) if tooltip else None
        self._draw()

    def _enter(self, _e=None):
        self._hover = True
        self._draw()

    def _leave(self, _e=None):
        self._hover = False
        self._draw()

    def _click(self, _e=None):
        if self._command:
            self._command()

    def set_icon(self, icon: str):
        self._icon = icon
        self._draw()

    def set_active(self, active: bool):
        self._active = active
        self._draw()

    def set_colors(self, fg: str, bg: str, hover_bg: str):
        self._fg, self._bg, self._hover_bg = fg, bg, hover_bg
        self.configure(bg=bg)
        self._draw()

    def _draw(self):
        self.delete("all")
        s = self._size
        if self._hover or self._focus or self._active:
            round_rect(self, 1, 1, s - 1, s - 1, (s - 2) / 2, self._hover_bg, "")
        color = T.ACCENT if self._active else self._fg
        if self._focus:
            self.create_oval(1, 1, s - 1, s - 1, outline=T.ACCENT, width=1)
        draw_icon(self, self._icon, s / 2, s / 2, self._icon_size, color, max(1.4, self._icon_size / 10))


class CircleButton(tk.Canvas):
    def __init__(
        self,
        parent,
        icon: str,
        command: Callable | None = None,
        size: int = 54,
        icon_size: int = 21,
        fill: str = T.ACCENT,
        hover: str = T.ACCENT_DARK,
        fg: str = T.WHITE,
        bg: str | None = None,
        tooltip: str | None = None,
    ):
        self._bg = bg or parent_bg(parent)
        super().__init__(parent, width=size, height=size, bg=self._bg, highlightthickness=0, bd=0, takefocus=1)
        self._icon = icon
        self._command = command
        self._size = size
        self._icon_size = icon_size
        self._fill = fill
        self._hover_fill = hover
        self._fg = fg
        self._hover = False
        self._focus = False
        self.configure(cursor="hand2")
        self.bind("<Enter>", self._enter)
        self.bind("<Leave>", self._leave)
        self.bind("<Button-1>", lambda e: self._command and self._command())
        self.bind("<Return>", lambda e: self._command and self._command())
        self.bind("<space>", lambda e: self._command and self._command())
        self.bind("<FocusIn>", lambda e: (setattr(self, "_focus", True), self._draw()))
        self.bind("<FocusOut>", lambda e: (setattr(self, "_focus", False), self._draw()))
        self.tooltip = Tooltip(self, tooltip) if tooltip else None
        self._draw()

    def _enter(self, _e=None):
        self._hover = True
        self._draw()

    def _leave(self, _e=None):
        self._hover = False
        self._draw()

    def set_icon(self, icon: str):
        self._icon = icon
        self._draw()

    def _draw(self):
        self.delete("all")
        s = self._size
        self.create_oval(2, 2, s - 2, s - 2, fill=self._hover_fill if self._hover else self._fill,
                         outline=T.ACCENT if self._focus else "")
        draw_icon(self, self._icon, s / 2, s / 2, self._icon_size, self._fg, 1.9)


class NavItem(tk.Canvas):
    def __init__(self, parent, text: str, icon: str, command: Callable, selected: bool = False):
        super().__init__(parent, width=212, height=44, bg=T.SIDEBAR, highlightthickness=0, bd=0, takefocus=1)
        self._text = text
        self._icon = icon
        self._command = command
        self._selected = selected
        self._hover = False
        self.configure(cursor="hand2")
        self.bind("<Enter>", self._enter)
        self.bind("<Leave>", self._leave)
        self.bind("<Button-1>", lambda e: self._command())
        self.bind("<Return>", lambda e: self._command())
        self.bind("<space>", lambda e: self._command())
        self._font = tkfont.Font(family=T.SANS, size=10, weight="bold")
        self._draw()

    def _enter(self, _e=None):
        self._hover = True
        self._draw()

    def _leave(self, _e=None):
        self._hover = False
        self._draw()

    def set_selected(self, selected: bool):
        self._selected = selected
        self._draw()

    def _draw(self):
        self.delete("all")
        if self._selected:
            round_rect(self, 0, 2, 212, 42, 10, T.SIDEBAR_ACTIVE, "")
            self.create_rectangle(0, 12, 3, 32, fill=T.ACCENT, outline="")
            color = T.SESSION_TEXT
        elif self._hover:
            round_rect(self, 0, 2, 212, 42, 10, T.SIDEBAR_HOVER, "")
            color = T.SIDEBAR_TEXT
        else:
            color = T.SIDEBAR_MUTED
        draw_icon(self, self._icon, 22, 22, 17, T.ACCENT if self._selected else color, 1.6)
        self.create_text(44, 22, text=self._text, anchor="w", fill=color, font=self._font)


class ToggleSwitch(tk.Canvas):
    def __init__(self, parent, value: bool = False, command: Callable | None = None, bg: str | None = None):
        self._bg = bg or parent_bg(parent)
        super().__init__(parent, width=44, height=24, bg=self._bg, highlightthickness=0, bd=0, takefocus=1)
        self._value = bool(value)
        self._command = command
        self._hover = False
        self.configure(cursor="hand2")
        self.bind("<Button-1>", self._toggle)
        self.bind("<Return>", self._toggle)
        self.bind("<space>", self._toggle)
        self.bind("<Enter>", lambda e: (setattr(self, "_hover", True), self._draw()))
        self.bind("<Leave>", lambda e: (setattr(self, "_hover", False), self._draw()))
        self.bind("<FocusIn>", lambda e: self._draw())
        self.bind("<FocusOut>", lambda e: self._draw())
        self._draw()

    def get(self) -> bool:
        return self._value

    def set_value(self, value: bool, notify: bool = False):
        self._value = bool(value)
        self._draw()
        if notify and self._command:
            self._command(self._value)

    def _toggle(self, _e=None):
        self._value = not self._value
        self._draw()
        if self._command:
            self._command(self._value)

    def _draw(self):
        self.delete("all")
        on = self._value
        track = T.GREEN if on else (T.LINE_STRONG if self._hover else T.LINE)
        round_rect(self, 1, 1, 43, 23, 11, track, "")
        x = 33 if on else 11
        self.create_oval(x - 8, 4, x + 8, 20, fill=T.WHITE, outline="#C9BCAD")


class ToggleRow(tk.Frame):
    def __init__(
        self,
        parent,
        title: str,
        description: str = "",
        value: bool = False,
        command: Callable | None = None,
        bg: str = T.CARD,
        title_width: int = 0,
        tooltip_text: str | None = None,
    ):
        super().__init__(parent, bg=bg)
        self._command = command
        self._bg = bg
        left = tk.Frame(self, bg=bg)
        left.pack(side="left", fill="x", expand=True)
        self.title_label = tk.Label(
            left, text=title, bg=bg, fg=T.INK, font=T.font(10, "bold"), anchor="w", justify="left"
        )
        self.title_label.pack(anchor="w")
        if description:
            self.desc_label = tk.Label(
                left, text=description, bg=bg, fg=T.MUTED, font=T.font(8), anchor="w", justify="left",
                wraplength=title_width or 250,
            )
            self.desc_label.pack(anchor="w", pady=(1, 0))
        else:
            self.desc_label = None
        self.switch = ToggleSwitch(self, value, self._changed, bg=bg)
        self.switch.pack(side="right", padx=(10, 0))
        if tooltip_text:
            Tooltip(self.title_label, tooltip_text)
            Tooltip(self.switch, tooltip_text)
        for w in (self, left, self.title_label, *( [self.desc_label] if self.desc_label else [] )):
            w.bind("<Button-1>", lambda e: self.switch._toggle())
            try:
                w.configure(cursor="hand2")
            except tk.TclError:
                pass

    def _changed(self, value):
        if self._command:
            self._command(value)

    def get(self) -> bool:
        return self.switch.get()

    def set_value(self, value: bool):
        self.switch.set_value(value)


class ScrollFrame(tk.Frame):
    def __init__(self, parent, bg: str = T.CREAM, padding: int = 0):
        super().__init__(parent, bg=bg)
        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0, bd=0)
        self.vsb = tk.Scrollbar(
            self, orient="vertical", command=self.canvas.yview, width=10,
            bg=T.LINE_STRONG, activebackground=T.MUTED, troughcolor=bg,
            relief="flat", bd=0, highlightthickness=0, elementborderwidth=0,
        )
        self.canvas.configure(yscrollcommand=self._on_scroll)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.vsb.pack(side="right", fill="y")
        self.body = tk.Frame(self.canvas, bg=bg)
        self._window = self.canvas.create_window((0, 0), window=self.body, anchor="nw")
        self.body.bind("<Configure>", self._on_body)
        self.canvas.bind("<Configure>", self._on_canvas)
        self._padding = padding
        # Keep the slim scrollbar mounted. Showing/hiding it changes the
        # canvas width and used to cause layout oscillation on resize.
        self._visible = True
        self._bind_wheel(self)
        self._bind_wheel(self.body)

    def _on_body(self, _event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas(self, event):
        if event.width > 2:
            self.canvas.itemconfigure(self._window, width=event.width)

    def _update_scrollbar(self):
        return

    def _on_scroll(self, first, last):
        self.vsb.set(first, last)

    def scroll_top(self):
        self.canvas.yview_moveto(0)

    def _bind_wheel(self, widget):
        widget.bind("<MouseWheel>", self._wheel, add="+")

    def bind_wheel_tree(self, widget=None):
        widget = widget or self.body
        self._bind_wheel(widget)
        for child in widget.winfo_children():
            self.bind_wheel_tree(child)

    def _wheel(self, event):
        if not self._visible:
            return
        delta = event.delta
        if delta:
            self.canvas.yview_scroll(int(-delta / 120), "units")
        return "break"


class ProgressBar(tk.Canvas):
    def __init__(self, parent, height: int = 4, bg: str = T.CREAM_DARK, fill: str = T.ACCENT):
        super().__init__(parent, height=height, bg=bg, highlightthickness=0, bd=0)
        self._fraction = 0.0
        self._fill = fill
        self._bg = bg
        self.bind("<Configure>", lambda e: self._draw())

    def set(self, fraction: float):
        self._fraction = max(0.0, min(1.0, fraction))
        self._draw()

    def _draw(self):
        self.delete("all")
        w = self.winfo_width()
        h = self.winfo_height()
        if w <= 1:
            return
        round_rect(self, 0, 0, w, h, h / 2, self._bg, "")
        if self._fraction > 0:
            round_rect(self, 0, 0, max(h, w * self._fraction), h, h / 2, self._fill, "")


class Tooltip:
    def __init__(self, widget: tk.Widget, text: str, delay: int = 450):
        self.widget = widget
        self.text = text
        self.delay = delay
        self._after = None
        self._tip = None
        widget.bind("<Enter>", self._enter, add="+")
        widget.bind("<Leave>", self._leave, add="+")
        widget.bind("<Button-1>", self._leave, add="+")

    def _enter(self, _e=None):
        self._after = self.widget.after(self.delay, self._show)

    def _leave(self, _e=None):
        if self._after:
            try:
                self.widget.after_cancel(self._after)
            except tk.TclError:
                pass
            self._after = None
        if self._tip:
            self._tip.destroy()
            self._tip = None

    def _show(self):
        if self._tip:
            return
        x = self.widget.winfo_rootx() + self.widget.winfo_width() // 2
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 8
        tip = tk.Toplevel(self.widget)
        tip.wm_overrideredirect(True)
        tip.configure(bg=T.INK)
        label = tk.Label(
            tip, text=self.text, bg=T.INK, fg=T.SESSION_TEXT, font=T.font(8),
            padx=9, pady=5,
        )
        label.pack()
        tip.update_idletasks()
        tw = tip.winfo_reqwidth()
        tip.geometry(f"+{max(0, x - tw // 2)}+{y}")
        self._tip = tip

    def set_text(self, text: str):
        self.text = text


class Hairline(tk.Frame):
    def __init__(self, parent, color: str = T.LINE, height: int = 1):
        super().__init__(parent, bg=color, height=height)


def make_badge(parent, text: str, bg=T.ACCENT_SOFT, fg=T.ACCENT_DARK, bg_parent=None):
    return tk.Label(
        parent, text=text, bg=bg, fg=fg, font=T.font(8, "bold"), padx=9, pady=4,
    )


def clear_children(widget: tk.Widget):
    for child in widget.winfo_children():
        child.destroy()
