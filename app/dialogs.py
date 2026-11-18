"""Small, consistent modal dialogs."""

from __future__ import annotations

import tkinter as tk
from typing import Callable

from . import theme as T
from .i18n import tr
from .widgets import CanvasButton, IconButton, round_rect


class BaseDialog(tk.Toplevel):
    def __init__(self, parent: tk.Misc, title: str, width: int = 440):
        super().__init__(parent)
        self.withdraw()
        self._parent = parent
        self._result = None
        self.overrideredirect(True)
        self.configure(bg=T.CARD)
        self.attributes("-topmost", True)
        self.transient(parent.winfo_toplevel())
        self.resizable(False, False)
        self._outer = tk.Frame(self, bg=T.CARD, highlightbackground=T.LINE_STRONG, highlightthickness=1)
        self._outer.pack(fill="both", expand=True)
        self._body = tk.Frame(self._outer, bg=T.CARD, padx=26, pady=22)
        self._body.pack(fill="both", expand=True)
        self._width = width
        header = tk.Frame(self._body, bg=T.CARD)
        header.pack(fill="x")
        self._title = tk.Label(
            header, text=title, bg=T.CARD, fg=T.INK, font=T.font(16, "bold"), anchor="w", justify="left",
        )
        self._title.pack(side="left", fill="x", expand=True)
        self._close = IconButton(
            header, "close", self._cancel, size=30, icon_size=13, bg=T.CARD, fg=T.MUTED,
            hover_bg=T.CREAM_DARK,
        )
        self._close.pack(side="right")
        self.content = tk.Frame(self._body, bg=T.CARD)
        self.content.pack(fill="both", expand=True, pady=(12, 0))
        self.footer = tk.Frame(self._body, bg=T.CARD)
        self.footer.pack(fill="x", pady=(22, 0))
        self.bind("<Escape>", lambda e: self._cancel())
        self.protocol("WM_DELETE_WINDOW", self._cancel)

    def add_message(self, text: str, size: int = 10):
        label = tk.Label(
            self.content, text=text, bg=T.CARD, fg=T.MUTED, font=T.font(size),
            anchor="w", justify="left", wraplength=self._width - 56,
        )
        label.pack(fill="x", pady=(0, 4))
        return label

    def add_buttons(self, cancel_text: str, confirm_text: str, danger: bool = False):
        self.confirm_btn = CanvasButton(
            self.footer, confirm_text, self._confirm, variant="danger" if danger else "primary",
            width=160, height=38, font_size=9,
        )
        self.confirm_btn.pack(side="right")
        self.cancel_btn = CanvasButton(
            self.footer, cancel_text, self._cancel, variant="ghost", width=120, height=38, font_size=9,
        )
        self.cancel_btn.pack(side="right", padx=(0, 10))

    def _confirm(self):
        self._result = True
        self._finish()

    def _cancel(self):
        self._result = False
        self._finish()

    def _finish(self):
        try:
            self.grab_release()
        except tk.TclError:
            pass
        self.destroy()

    def _center(self):
        self.update_idletasks()
        parent = self._parent.winfo_toplevel()
        parent.update_idletasks()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        w = max(320, self.winfo_reqwidth())
        h = max(120, self.winfo_reqheight())
        x = px + max(0, (pw - w) // 2)
        y = py + max(0, (ph - h) // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _raise_above(self):
        # ``transient`` and ``overrideredirect`` can drop the topmost hint on
        # Windows when the window is mapped; reassert it once it exists.
        try:
            self.attributes("-topmost", True)
            self.lift()
            self.focus_force()
        except tk.TclError:
            pass

    def show(self):
        self._center()
        self.deiconify()
        self.update_idletasks()
        self._raise_above()
        self.after(15, self._raise_above)
        try:
            self.grab_set()
        except tk.TclError:
            pass
        self.focus_force()
        self.wait_window(self)
        return self._result


class ConfirmDialog(BaseDialog):
    def __init__(self, parent, title: str, body: str, confirm_text: str, cancel_text: str,
                 danger: bool = False, icon: str = "info", icon_color: str = T.ACCENT):
        super().__init__(parent, title, width=430)
        self.content.configure(padx=0)
        row = tk.Frame(self.content, bg=T.CARD)
        row.pack(fill="x")
        badge = tk.Canvas(row, width=42, height=42, bg=T.CARD, highlightthickness=0)
        badge.pack(side="left", anchor="n", padx=(0, 14))
        round_rect(badge, 0, 0, 42, 42, 21, T.ACCENT_PALE, "")
        from .widgets import draw_icon
        draw_icon(badge, icon, 21, 21, 18, icon_color, 1.8)
        label = tk.Label(
            row, text=body, bg=T.CARD, fg=T.MUTED, font=T.font(10),
            anchor="w", justify="left", wraplength=330,
        )
        label.pack(side="left", fill="x", expand=True)
        self.add_buttons(cancel_text, confirm_text, danger=danger)
        self.bind("<Return>", lambda e: self._confirm())


class MessageDialog(BaseDialog):
    def __init__(self, parent, title: str, body: str, ok_text: str, icon: str = "info"):
        super().__init__(parent, title, width=420)
        row = tk.Frame(self.content, bg=T.CARD)
        row.pack(fill="x")
        badge = tk.Canvas(row, width=40, height=40, bg=T.CARD, highlightthickness=0)
        badge.pack(side="left", anchor="n", padx=(0, 14))
        round_rect(badge, 0, 0, 40, 40, 20, T.ACCENT_PALE, "")
        from .widgets import draw_icon
        draw_icon(badge, icon, 20, 20, 17, T.ACCENT, 1.7)
        tk.Label(
            row, text=body, bg=T.CARD, fg=T.MUTED, font=T.font(10),
            anchor="w", justify="left", wraplength=330,
        ).pack(side="left", fill="x", expand=True)
        self.ok_btn = CanvasButton(self.footer, ok_text, self._confirm, variant="primary", width=130, height=38, font_size=9)
        self.ok_btn.pack(side="right")
        self.bind("<Return>", lambda e: self._confirm())


class PlanBlockDialog(BaseDialog):
    def __init__(
        self,
        parent,
        title: str,
        count_label: str,
        time_label: str,
        minutes_label: str,
        seconds_label: str,
        total_label: str,
        presets_label: str,
        confirm_text: str,
        cancel_text: str,
        invalid_text: str,
        count: int = 5,
        duration: int = 60,
        count_unit: str = "imágenes",
    ):
        super().__init__(parent, title, width=470)
        self.invalid_text = invalid_text
        self._count = tk.StringVar(value=str(count))
        self._mins = tk.StringVar(value=str(duration // 60))
        self._secs = tk.StringVar(value=str(duration % 60))
        for var in (self._count, self._mins, self._secs):
            var.trace_add("write", lambda *_: self._update_total())

        tk.Label(self.content, text=count_label, bg=T.CARD, fg=T.INK,
                 font=T.font(9, "bold"), anchor="w").pack(anchor="w")
        box = tk.Frame(self.content, bg=T.PAPER, highlightbackground=T.LINE_STRONG, highlightthickness=1)
        box.pack(fill="x", pady=(4, 12))
        self.count_entry = tk.Entry(
            box, textvariable=self._count, bg=T.PAPER, fg=T.INK, insertbackground=T.ACCENT,
            relief="flat", font=T.font(15, "bold"), justify="center", width=7,
            highlightthickness=0, bd=0,
        )
        self.count_entry.pack(side="left", fill="x", expand=True, padx=(12, 4), pady=8)
        tk.Label(box, text=count_unit, bg=T.PAPER, fg=T.MUTED, font=T.font(9)).pack(side="left", padx=(0, 12))

        tk.Label(self.content, text=time_label, bg=T.CARD, fg=T.INK,
                 font=T.font(9, "bold"), anchor="w").pack(anchor="w")
        time_box = tk.Frame(self.content, bg=T.CARD)
        time_box.pack(fill="x", pady=(4, 0))
        self.min_entry = self._time_field(time_box, self._mins, minutes_label, 0)
        self.sec_entry = self._time_field(time_box, self._secs, seconds_label, 1)

        presets = tk.Frame(self.content, bg=T.CARD)
        presets.pack(fill="x", pady=(9, 0))
        tk.Label(presets, text=presets_label, bg=T.CARD, fg=T.MUTED, font=T.font(8)).pack(
            side="left", padx=(0, 6)
        )
        for seconds in (10, 30, 60, 120, 300, 600):
            CanvasButton(
                presets, T.fmt_chip_duration(seconds),
                lambda s=seconds: self._set_duration(s),
                variant="ghost", width=52, height=26, radius=7, font_size=7, padx=5,
            ).pack(side="left", padx=(0, 4))

        self.total = tk.Label(self.content, text="", bg=T.ACCENT_PALE, fg=T.ACCENT_DARK,
                              font=T.font(9, "bold"), anchor="w", padx=12, pady=8)
        self.total.pack(fill="x", pady=(14, 0))
        self.error = tk.Label(self.content, text="", bg=T.CARD, fg=T.RED, font=T.font(8), anchor="w")
        self.error.pack(fill="x", pady=(6, 0))
        self.add_buttons(cancel_text, confirm_text)
        self.bind("<Return>", lambda e: self._confirm())
        self.after(60, self._focus_count)
        self._update_total()

    def _time_field(self, parent, var, suffix, col):
        box = tk.Frame(parent, bg=T.PAPER, highlightbackground=T.LINE_STRONG, highlightthickness=1)
        box.grid(row=0, column=col, sticky="ew", padx=(0 if col == 0 else 8, 0))
        parent.grid_columnconfigure(col, weight=1)
        tk.Entry(
            box, textvariable=var, bg=T.PAPER, fg=T.INK, insertbackground=T.ACCENT,
            relief="flat", font=T.font(15, "bold"), justify="center", width=6,
            highlightthickness=0, bd=0,
        ).pack(side="left", fill="x", expand=True, padx=(10, 4), pady=8)
        tk.Label(box, text=suffix, bg=T.PAPER, fg=T.MUTED, font=T.font(9)).pack(side="left", padx=(0, 10))
        return box

    def _focus_count(self):
        try:
            self.count_entry.focus_set()
            self.count_entry.selection_range(0, "end")
        except tk.TclError:
            pass

    def _set_duration(self, seconds: int):
        self._mins.set(str(seconds // 60))
        self._secs.set(str(seconds % 60))
        self._update_total()

    def _values(self):
        try:
            count = int(float(self._count.get().replace(",", ".")))
            minutes = int(float(self._mins.get().replace(",", ".")))
            seconds = int(float(self._secs.get().replace(",", ".")))
            duration = minutes * 60 + seconds
        except ValueError:
            return None
        if not (1 <= count <= 500) or not (5 <= duration <= 3600):
            return None
        return count, duration

    def _update_total(self):
        values = self._values()
        if values is None:
            self.total.configure(text="—")
            return
        count, duration = values
        total = count * duration
        self.total.configure(text=f"{count} × {T.fmt_chip_duration(duration)} = {T.fmt_total(total)}")

    def _confirm(self):
        values = self._values()
        if values is None:
            self.error.configure(text=self.invalid_text)
            return
        self._result = values
        self._finish()


class NumberDialog(BaseDialog):
    def __init__(self, parent, title: str, hint: str, value: int, minimum: int, maximum: int,
                 unit: str, confirm_text: str, cancel_text: str, invalid_text: str):
        super().__init__(parent, title, width=390)
        self.minimum = minimum
        self.maximum = maximum
        self.invalid_text = invalid_text
        self._var = tk.StringVar(value=str(value))
        self.add_message(hint)
        box = tk.Frame(self.content, bg=T.PAPER, highlightbackground=T.LINE_STRONG, highlightthickness=1)
        box.pack(fill="x", pady=(14, 0))
        self.entry = tk.Entry(
            box, textvariable=self._var, bg=T.PAPER, fg=T.INK, insertbackground=T.ACCENT,
            relief="flat", font=T.font(20, "bold"), justify="center", width=8,
            highlightthickness=0, bd=0,
        )
        self.entry.pack(side="left", fill="x", expand=True, padx=(12, 4), pady=10)
        tk.Label(box, text=unit, bg=T.PAPER, fg=T.MUTED, font=T.font(10)).pack(side="left", padx=(0, 14))
        self.error = tk.Label(self.content, text="", bg=T.CARD, fg=T.RED, font=T.font(8), anchor="w")
        self.error.pack(fill="x", pady=(6, 0))
        self.add_buttons(cancel_text, confirm_text)
        self.bind("<Return>", lambda e: self._confirm())
        self.after(60, self._select_all)

    def _select_all(self):
        try:
            self.entry.focus_set()
            self.entry.selection_range(0, "end")
        except tk.TclError:
            pass

    def _confirm(self):
        raw = self._var.get().strip().replace(",", ".")
        try:
            value = int(float(raw))
        except ValueError:
            self.error.configure(text=self.invalid_text)
            return
        if value < self.minimum or value > self.maximum:
            self.error.configure(text=self.invalid_text)
            return
        self._result = value
        self._finish()
