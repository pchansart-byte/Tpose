"""Tpose pages: practice setup, local history and about."""

from __future__ import annotations

import sys
import tkinter as tk
from datetime import datetime, timedelta
from pathlib import Path
from tkinter import filedialog

from PIL import Image, ImageOps, ImageTk

from . import exports
from . import theme as T
from .art import Artwork
from .dialogs import ConfirmDialog, MessageDialog, NumberDialog, PlanBlockDialog
from .folders import pick_folders
from .i18n import tr
from .library import plan_label, plan_total, scan_folder
from .storage import Store
from .widgets import (
    CanvasButton,
    Hairline,
    IconButton,
    ProgressBar,
    ScrollFrame,
    ToggleRow,
    draw_icon,
    round_rect,
)


class Page(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=T.CREAM)
        self.app = app
        self.store: Store = app.store
        self.art: Artwork = app.art
        self._photos: list[ImageTk.PhotoImage] = []

    @property
    def lang(self) -> str:
        return self.app.lang

    def t(self, key: str, **kwargs) -> str:
        return tr(self.lang, key, **kwargs)

    def keep(self, photo):
        self._photos.append(photo)
        return photo


def section_head(parent, number: str, title: str, note: str = "", bg=T.CREAM):
    row = tk.Frame(parent, bg=bg)
    num = tk.Label(row, text=number, bg=bg, fg=T.ACCENT, font=T.font(9, "bold"))
    num.pack(side="left", anchor="n", pady=(3, 0))
    tk.Label(row, text=title, bg=bg, fg=T.INK, font=T.font(13, "bold"), anchor="w").pack(
        side="left", padx=(9, 0)
    )
    if note:
        tk.Label(row, text=note, bg=bg, fg=T.MUTED, font=T.font(8), anchor="w").pack(
            side="left", padx=(12, 0), pady=(3, 0)
        )
    return row


class SetupPage(Page):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        self._mode_buttons = {}
        self._plan_rows = 0
        self.sf = ScrollFrame(self, bg=T.CREAM)
        self.sf.pack(fill="both", expand=True)
        self.content = tk.Frame(self.sf.body, bg=T.CREAM)
        self.content.pack(fill="both", expand=True, padx=34, pady=20)
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_columnconfigure(1, weight=0, minsize=356)
        self._header()
        self.left = tk.Frame(self.content, bg=T.CREAM)
        self.left.grid(row=1, column=0, sticky="nw", padx=(0, 26))
        self.right = tk.Frame(self.content, bg=T.CREAM, width=356)
        self.right.grid(row=1, column=1, sticky="n")
        self._build_left()
        self._build_summary()
        self.after(60, self.sf.bind_wheel_tree)

    def _header(self):
        header = tk.Frame(self.content, bg=T.CREAM)
        header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 20))
        left = tk.Frame(header, bg=T.CREAM)
        left.pack(side="left", fill="x", expand=True)
        eyebrow = tk.Frame(left, bg=T.CREAM)
        eyebrow.pack(anchor="w")
        tk.Frame(eyebrow, bg=T.ACCENT, width=26, height=3).pack(side="left", padx=(0, 9), pady=4)
        tk.Label(eyebrow, text=self.t("practice.eyebrow"), bg=T.CREAM, fg=T.ACCENT,
                 font=T.font(8, "bold")).pack(side="left")
        tk.Label(left, text=self.t("practice.title"), bg=T.CREAM, fg=T.INK,
                 font=T.font(29, "bold", T.SERIF), justify="left", anchor="w").pack(
            anchor="w", pady=(7, 4)
        )
        tk.Label(left, text=self.t("practice.subtitle"), bg=T.CREAM, fg=T.MUTED,
                 font=T.font(9), justify="left", anchor="w", wraplength=620).pack(anchor="w")
        date = datetime.now()
        months = T.MONTHS.get(self.lang, T.MONTHS["es"])
        if self.lang in ("zh", "ja"):
            date_text = f"{months[date.month - 1]}{date.day}日"
        else:
            date_text = f"{date.day:02d}  {months[date.month - 1].upper()}"
        tk.Label(header, text=date_text,
                 bg=T.CREAM, fg=T.FAINT, font=T.font(8, "bold"), anchor="e").pack(
            side="right", padx=(18, 0), pady=(8, 0)
        )

    def _build_left(self):
        for child in self.left.winfo_children():
            child.destroy()
        self._folders_box = tk.Frame(self.left, bg=T.CREAM)
        self._folders_box.pack(fill="x", pady=(0, 18))
        self._mode_box = tk.Frame(self.left, bg=T.CREAM)
        self._mode_box.pack(fill="x", pady=(0, 18))
        self._plan_box = tk.Frame(self.left, bg=T.CREAM)
        self._plan_box.pack(fill="x", pady=(0, 18))
        self._options_box = tk.Frame(self.left, bg=T.CREAM)
        self._options_box.pack(fill="x", pady=(0, 8))
        self._fill_folders(self._folders_box)
        self._fill_mode(self._mode_box)
        self._fill_plan(self._plan_box)
        self._fill_options(self._options_box)

    def _refresh_folders(self):
        for child in self._folders_box.winfo_children():
            child.destroy()
        self._fill_folders(self._folders_box)

    def _refresh_plan(self):
        for child in self._plan_box.winfo_children():
            child.destroy()
        self._fill_plan(self._plan_box)

    def _refresh_options(self):
        for child in self._options_box.winfo_children():
            child.destroy()
        self._fill_options(self._options_box)

    # ---------------------------------------------------------------- folders
    def _fill_folders(self, container):
        section_head(container, "01", self.t("practice.step1"), self.t("practice.step1_note")).pack(
            fill="x", pady=(0, 7)
        )
        if not self.store.folders:
            empty = tk.Frame(container, bg=T.CARD, highlightbackground=T.LINE, highlightthickness=1)
            empty.pack(fill="x", pady=(0, 7))
            inner = tk.Frame(empty, bg=T.CARD, padx=14, pady=13)
            inner.pack(fill="x")
            icon = tk.Canvas(inner, width=34, height=34, bg=T.CARD, highlightthickness=0)
            icon.pack(side="left", padx=(0, 11))
            round_rect(icon, 1, 1, 33, 33, 8, T.ACCENT_PALE, "")
            draw_icon(icon, "folder", 17, 17, 15, T.ACCENT, 1.5)
            text = tk.Frame(inner, bg=T.CARD)
            text.pack(side="left", fill="x", expand=True)
            tk.Label(text, text=self.t("practice.empty_title"), bg=T.CARD, fg=T.INK,
                     font=T.font(9, "bold"), anchor="w").pack(anchor="w")
            tk.Label(text, text=self.t("practice.empty_body"), bg=T.CARD, fg=T.MUTED,
                     font=T.font(8), justify="left", anchor="w", wraplength=360).pack(anchor="w")
        else:
            for folder in self.store.folders:
                self._folder_row(container, folder)
        CanvasButton(
            container, self.t("practice.add_folders"), self._add_folder, variant="ghost",
            icon="folder", width=300, height=38, font_size=9, anchor="left",
        ).pack(fill="x", pady=(7, 0))
        tk.Label(container, text=self.t("practice.folder_hint"), bg=T.CREAM, fg=T.FAINT,
                 font=T.font(8), anchor="w").pack(anchor="w", padx=4, pady=(3, 0))

    def _folder_row(self, parent, folder):
        path = folder["path"]
        exists = Path(path).is_dir()
        files = self.app.folder_files(path) if exists else []
        enabled = bool(folder.get("enabled", True)) and exists
        card = tk.Frame(parent, bg=T.CARD if enabled else T.PAPER,
                        highlightbackground=T.ACCENT if enabled else T.LINE,
                        highlightthickness=1, cursor="hand2")
        card.pack(fill="x", pady=3)
        inner = tk.Frame(card, bg=T.CARD if enabled else T.PAPER, padx=11, pady=8)
        inner.pack(fill="x")
        check = tk.Canvas(inner, width=20, height=20, bg=T.CARD if enabled else T.PAPER,
                          highlightthickness=0, cursor="hand2")
        check.pack(side="left", padx=(0, 9))
        if enabled:
            check.create_oval(1, 1, 19, 19, fill=T.ACCENT, outline="")
            draw_icon(check, "check", 10, 10, 11, T.WHITE, 1.5)
        else:
            check.create_oval(2, 2, 18, 18, outline=T.LINE_STRONG, width=1)
        text = tk.Frame(inner, bg=T.CARD if enabled else T.PAPER, cursor="hand2")
        text.pack(side="left", fill="x", expand=True)
        name = folder.get("name") or Path(path).name
        tk.Label(text, text=name, bg=T.CARD if enabled else T.PAPER, fg=T.INK,
                 font=T.font(9, "bold"), anchor="w", justify="left", wraplength=370).pack(anchor="w")
        parts = Path(path).parts
        display = str(Path(*parts[-3:])) if len(parts) > 3 else path
        if len(parts) > 3:
            display = "…\\" + display
        tk.Label(text, text=display, bg=T.CARD if enabled else T.PAPER, fg=T.MUTED,
                 font=T.font(7), anchor="w", justify="left", wraplength=370).pack(anchor="w")
        if exists:
            count_text = self.t("practice.image_count" if len(files) == 1 else "practice.images_count",
                                n=len(files))
            color = T.ACCENT if enabled and files else T.RED if not files else T.FAINT
        else:
            count_text = self.t("practice.folder_missing")
            color = T.RED
        tk.Label(text, text=count_text, bg=T.CARD if enabled else T.PAPER, fg=color,
                 font=T.font(8, "bold"), anchor="w").pack(anchor="w", pady=(2, 0))
        rm = IconButton(inner, "trash", lambda p=path: self._remove_folder(p), size=26, icon_size=13,
                        bg=T.CARD if enabled else T.PAPER, fg=T.FAINT, hover_bg=T.ACCENT_PALE,
                        tooltip=self.t("practice.remove_folder"))
        rm.pack(side="right", anchor="n", padx=(6, 0))
        clickables = [card, inner, check, text, *text.winfo_children()]
        for widget in clickables:
            widget.bind("<Button-1>", lambda e, p=path: self._toggle_folder(p))
            try:
                widget.configure(cursor="hand2")
            except tk.TclError:
                pass

    def _add_folder(self):
        paths = pick_folders(self, self.t("dialog.folder_title"))
        if not paths:
            return
        added = 0
        empty = 0
        duplicate = 0
        for path in paths:
            files = scan_folder(path)
            if not files:
                empty += 1
                continue
            if not self.store.add_folder(path):
                duplicate += 1
                continue
            self.app.folder_cache[str(Path(path).resolve()).lower()] = files
            added += 1
        if added:
            if added == 1:
                self.app.toast(self.t("practice.folder_added"))
            else:
                self.app.toast(self.t("practice.folders_added", n=added))
            self._refresh_folders()
            self._build_summary()
        elif empty:
            MessageDialog(self, self.t("dialog.no_images_title"), self.t("dialog.no_images"),
                          self.t("common.ok"), icon="folder").show()
        elif duplicate:
            MessageDialog(self, self.t("dialog.duplicate_title"), self.t("practice.folder_duplicate"),
                          self.t("common.ok"), icon="folder").show()

    def _toggle_folder(self, path):
        folder = next((f for f in self.store.folders if f["path"] == path), None)
        if folder is None:
            return
        self.store.set_folder_enabled(path, not folder.get("enabled", True))
        self._refresh_folders()
        self._build_summary()

    def _remove_folder(self, path):
        folder = next((f for f in self.store.folders if f["path"] == path), None)
        name = folder.get("name") if folder else Path(path).name
        ok = ConfirmDialog(
            self, self.t("dialog.remove_title"), f"{name}\n\n{self.t('dialog.remove_body')}",
            self.t("dialog.remove_yes"), self.t("common.cancel"), danger=True, icon="trash",
            icon_color=T.RED,
        ).show()
        if not ok:
            return
        self.store.remove_folder(path)
        self.app.folder_cache.pop(str(Path(path).resolve()).lower(), None)
        self._refresh_folders()
        self._build_summary()

    # ------------------------------------------------------------------- mode
    def _fill_mode(self, box):
        self._mode_buttons = {}
        section_head(box, "02", self.t("practice.step2")).pack(fill="x", pady=(0, 7))
        row = tk.Frame(box, bg=T.CREAM)
        row.pack(fill="x")
        for i, key in enumerate(("timed", "relaxed")):
            b = CanvasButton(
                row, self.t(f"mode.{key}"), lambda k=key: self._select_mode(k),
                variant="ghost", width=138, height=38, font_size=9,
                selected=self.store.get("mode") == key,
            )
            b.pack(side="left", padx=(0 if i == 0 else 8, 0))
            self._mode_buttons[key] = b
        self._mode_desc = tk.Label(
            box, text=self.t(f"mode.{self.store.get('mode')}_desc"), bg=T.CREAM, fg=T.MUTED,
            font=T.font(8), anchor="w", justify="left", wraplength=620,
        )
        self._mode_desc.pack(anchor="w", pady=(7, 0))

    def _select_mode(self, mode):
        self.store.set("mode", mode)
        for key, btn in self._mode_buttons.items():
            btn.set_selected(key == mode)
        self._mode_desc.configure(text=self.t(f"mode.{mode}_desc"))
        self._refresh_plan()
        self._refresh_options()
        self._build_summary()

    # ------------------------------------------------------------------- plan
    def _fill_plan(self, box):
        if self.store.get("mode") == "relaxed":
            section_head(box, "03", self.t("plan.relaxed_count")).pack(fill="x", pady=(0, 7))
            row = tk.Frame(box, bg=T.CREAM)
            row.pack(fill="x")
            values = [10, 20, 30, 50]
            current = int(self.store.get("relaxed_count"))
            if current not in values:
                values.insert(0, current)
            for i, value in enumerate(values):
                CanvasButton(
                    row, str(value), lambda v=value: self._set_relaxed_count(v),
                    variant="ghost", width=58, height=32, radius=9, font_size=8,
                    selected=value == current,
                ).grid(row=i // 5, column=i % 5, sticky="w", padx=(0, 5), pady=(0, 4))
            CanvasButton(box, f"+ {self.t('common.custom')}", self._custom_relaxed,
                         variant="quiet", width=150, height=26, font_size=8, padx=0).pack(
                anchor="w", pady=(2, 0)
            )
            return

        head = section_head(box, "03", self.t("practice.step3"), self.t("practice.step3_note"))
        head.pack(fill="x", pady=(0, 7))
        plan = self.store.plan
        if not plan:
            tk.Label(box, text=self.t("plan.empty"), bg=T.CREAM, fg=T.MUTED,
                     font=T.font(8), anchor="w").pack(anchor="w", pady=(0, 7))
        for i, block in enumerate(plan):
            self._plan_row(box, i, block)
        CanvasButton(box, f"+ {self.t('plan.add')}", self._add_block, variant="ghost",
                     width=180, height=34, font_size=8, icon="plus").pack(anchor="w", pady=(5, 0))
        poses, seconds = plan_total(plan)
        if plan:
            total = tk.Frame(box, bg=T.ACCENT_PALE, padx=12, pady=8)
            total.pack(fill="x", pady=(7, 0))
            tk.Label(total, text=self.t("plan.total"), bg=T.ACCENT_PALE, fg=T.ACCENT_DARK,
                     font=T.font(8, "bold")).pack(side="left")
            tk.Label(total, text=f"{T.images_label(poses, self.lang)} · {T.fmt_total(seconds, self.lang)}",
                     bg=T.ACCENT_PALE, fg=T.ACCENT_DARK, font=T.font(8)).pack(side="right")

    def _plan_row(self, parent, index, block):
        card = tk.Frame(parent, bg=T.CARD, highlightbackground=T.LINE, highlightthickness=1)
        card.pack(fill="x", pady=3)
        inner = tk.Frame(card, bg=T.CARD, padx=11, pady=7)
        inner.pack(fill="x")
        tk.Label(inner, text=f"{index + 1:02d}", bg=T.CARD, fg=T.ACCENT, font=T.font(8, "bold"),
                 width=3, anchor="w").pack(side="left")
        text = tk.Frame(inner, bg=T.CARD)
        text.pack(side="left", fill="x", expand=True)
        count = int(block.get("count", 0))
        duration = int(block.get("duration", 30))
        line = tk.Frame(text, bg=T.CARD)
        line.pack(anchor="w")
        tk.Label(line, text=f"{count}", bg=T.CARD, fg=T.INK, font=T.font(11, "bold")).pack(side="left")
        unit = self.t("common.pose" if count == 1 else "common.poses")
        tk.Label(line, text=f" {unit}  ×  {T.fmt_chip_duration(duration, self.lang)}",
                 bg=T.CARD, fg=T.MUTED, font=T.font(9)).pack(side="left")
        tk.Label(text, text=f"{self.t('plan.block_total')}: {T.fmt_total(count * duration, self.lang)}",
                 bg=T.CARD, fg=T.FAINT, font=T.font(7), anchor="w").pack(anchor="w")
        CanvasButton(inner, self.t("common.edit"), lambda i=index: self._edit_block(i),
                     variant="quiet", width=54, height=25, font_size=7, padx=5).pack(
            side="right", padx=(5, 0)
        )
        IconButton(inner, "trash", lambda i=index: self._remove_block(i), size=25, icon_size=12,
                   bg=T.CARD, fg=T.FAINT, hover_bg=T.ACCENT_PALE,
                   tooltip=self.t("plan.remove")).pack(side="right", padx=(5, 0))

    def _block_dialog(self, title, count, duration):
        return PlanBlockDialog(
            self, title,
            self.t("dialog.block_count"), self.t("dialog.block_time"),
            self.t("dialog.block_minutes"), self.t("dialog.block_seconds"),
            self.t("dialog.block_total"), self.t("plan.presets"),
            self.t("common.save"), self.t("common.cancel"),
            self.t("dialog.block_invalid"), count, duration,
            count_unit=self.t("common.poses"),
        ).show()

    def _add_block(self):
        values = self._block_dialog(self.t("dialog.block_add_title"), 5, 60)
        if values:
            plan = list(self.store.plan)
            plan.append({"count": values[0], "duration": values[1]})
            self.store.set_plan(plan)
            self._build_plan_only()

    def _edit_block(self, index):
        plan = list(self.store.plan)
        if not 0 <= index < len(plan):
            return
        block = plan[index]
        values = self._block_dialog(self.t("dialog.block_edit_title"), block["count"], block["duration"])
        if values:
            plan[index] = {"count": values[0], "duration": values[1]}
            self.store.set_plan(plan)
            self._build_plan_only()

    def _remove_block(self, index):
        plan = list(self.store.plan)
        if 0 <= index < len(plan):
            del plan[index]
            self.store.set_plan(plan)
            self._build_plan_only()

    def _build_plan_only(self):
        self._refresh_plan()
        self._build_summary()

    def _set_relaxed_count(self, value):
        self.store.set("relaxed_count", int(value))
        self._build_plan_only()

    def _custom_relaxed(self):
        value = NumberDialog(
            self, self.t("plan.relaxed_count"), self.t("dialog.relaxed_invalid"),
            int(self.store.get("relaxed_count")), 1, 500, self.t("common.poses"),
            self.t("common.save"), self.t("common.cancel"),
            self.t("dialog.relaxed_invalid"),
        ).show()
        if value:
            self.store.set("relaxed_count", value)
            self._build_plan_only()

    # ---------------------------------------------------------------- options
    def _fill_options(self, box):
        section_head(box, "04", self.t("practice.step4")).pack(fill="x", pady=(0, 7))
        grid = tk.Frame(box, bg=T.CREAM)
        grid.pack(fill="x")
        opts = [
            ("shuffle", "settings.shuffle", "settings.shuffle_desc"),
            ("grayscale", "settings.grayscale", "settings.grayscale_desc"),
            ("sound", "settings.sound", "settings.sound_desc"),
        ]
        if self.store.get("mode") == "timed":
            opts.append(("show_timer", "settings.show_timer", "settings.show_timer_desc"))
        for i, (key, title, desc) in enumerate(opts):
            row = ToggleRow(
                grid, self.t(title), "", bool(self.store.get(key)),
                lambda v, k=key: self.store.set(k, bool(v)), bg=T.CREAM,
                tooltip_text=self.t(desc),
            )
            row.grid(row=0, column=i, sticky="w", padx=(0 if i == 0 else 7, 0),
                     pady=(2, 4))
        for i in range(4):
            grid.grid_columnconfigure(i, weight=1, uniform="opt")

        if self.store.get("mode") == "timed":
            warn = tk.Frame(box, bg=T.CREAM)
            warn.pack(fill="x", pady=(6, 0))
            tk.Label(warn, text=self.t("settings.warning"), bg=T.CREAM, fg=T.INK,
                     font=T.font(9, "bold")).pack(side="left", padx=(0, 7))
            self.warning_btn = CanvasButton(
                warn, f"{int(self.store.get('warning_seconds', 10))} s  ▾",
                self._open_warning_menu, variant="ghost", width=74, height=28,
                radius=8, font_size=8, padx=6,
                tooltip=self.t("settings.warning_desc"),
            )
            self.warning_btn.pack(side="left")
            interval = ToggleRow(
                warn, self.t("settings.interval_sound"), "", bool(self.store.get("interval_sound")),
                lambda v: self.store.set("interval_sound", bool(v)), bg=T.CREAM,
                tooltip_text=self.t("settings.interval_sound_desc"),
            )
            interval.pack(side="right")

    def _open_warning_menu(self):
        menu = tk.Menu(self, tearoff=0, bg=T.PAPER, fg=T.INK,
                       activebackground=T.ACCENT_SOFT, activeforeground=T.INK,
                       font=T.font(9), bd=0)
        for seconds in range(5, 31, 5):
            menu.add_command(
                label=self.t("settings.warning_value", n=seconds),
                command=lambda s=seconds: self._set_warning(s),
            )
        self._warning_menu = menu
        x = self.warning_btn.winfo_rootx()
        y = self.warning_btn.winfo_rooty() + self.warning_btn.winfo_height()
        try:
            menu.tk_popup(x, y)
        finally:
            menu.grab_release()

    def _set_warning(self, seconds):
        self.store.set("warning_seconds", int(seconds))
        self.warning_btn.set_text(f"{int(seconds)} s  ▾")

    # ---------------------------------------------------------------- summary
    def _build_summary(self):
        if hasattr(self, "summary") and self.summary.winfo_exists():
            self._refresh_summary()
            return
        self.summary = tk.Frame(self.right, bg=T.SIDEBAR)
        self.summary.pack(fill="both", expand=True)
        body = tk.Frame(self.summary, bg=T.SIDEBAR, padx=21, pady=20)
        body.pack(fill="both", expand=True)
        head = tk.Frame(body, bg=T.SIDEBAR)
        head.pack(fill="x")
        tk.Label(head, text=self.t("setup.your_session"), bg=T.SIDEBAR, fg=T.ACCENT,
                 font=T.font(8, "bold")).pack(side="left")
        dot = tk.Canvas(head, width=8, height=8, bg=T.SIDEBAR, highlightthickness=0)
        dot.pack(side="right", pady=2)
        dot.create_oval(1, 1, 7, 7, fill=T.GREEN, outline="")

        self._sum_cover = tk.Label(body, bg=T.SESSION_PANEL, bd=0,
                                   fg=T.SESSION_MUTED, font=T.font(8), height=7,
                                   cursor="hand2")
        self._sum_cover.pack(fill="x", pady=(12, 12))
        self._sum_cover.bind("<Button-1>", lambda e: self._add_folder())
        self._sum_cover_photo = None
        self._sum_cover_key = ("__unset__",)

        line = tk.Frame(body, bg=T.SIDEBAR)
        line.pack(fill="x")
        self._sum_big = tk.Label(line, text="0", bg=T.SIDEBAR, fg=T.SESSION_TEXT,
                                 font=T.font(30, "bold", T.SERIF), anchor="w")
        self._sum_big.pack(side="left", anchor="s")
        self._sum_small = tk.Label(line, text="", bg=T.SIDEBAR, fg=T.SIDEBAR_MUTED,
                                    font=T.font(9), anchor="w")
        self._sum_small.pack(side="left", padx=(7, 0), pady=(0, 7))

        rows = tk.Frame(body, bg=T.SIDEBAR)
        rows.pack(fill="x", pady=(13, 0))
        self._sum_values = {}
        for key, label in (
            ("images", "setup.images"),
            ("total", "setup.total"),
            ("mode", "setup.mode"),
            ("folders", "setup.folders"),
            ("plan", "setup.plan"),
        ):
            r = tk.Frame(rows, bg=T.SIDEBAR)
            r.pack(fill="x", pady=2)
            tk.Label(r, text=self.t(label), bg=T.SIDEBAR, fg=T.SIDEBAR_MUTED,
                     font=T.font(8), anchor="w").pack(side="left")
            value = tk.Label(r, text="", bg=T.SIDEBAR, fg=T.SESSION_TEXT,
                             font=T.font(8, "bold"), anchor="e", wraplength=205,
                             justify="right")
            value.pack(side="right")
            self._sum_values[key] = value

        Hairline(body, color=T.SIDEBAR_LINE).pack(fill="x", pady=(13, 13))
        self._sum_start = CanvasButton(body, self.t("setup.start"), self._start,
                                       variant="primary", width=300, height=44,
                                       font_size=10, icon="play")
        self._sum_start.pack(fill="x")
        self._sum_note = tk.Label(body, text="", bg=T.SIDEBAR, fg=T.ACCENT_SOFT,
                                  font=T.font(8), wraplength=290, justify="left",
                                  anchor="w")
        self._sum_note.pack(anchor="w", pady=(8, 0))
        tip = tk.Frame(body, bg=T.SIDEBAR)
        tip.pack(fill="x", pady=(12, 0))
        tk.Frame(tip, bg=T.ACCENT, width=2, height=14).pack(side="left", anchor="n", padx=(0, 7))
        tk.Label(tip, text=self.t("setup.tip"), bg=T.SIDEBAR, fg=T.SIDEBAR_MUTED,
                 font=T.font(8), wraplength=265, justify="left", anchor="w").pack(
            side="left", fill="x", expand=True
        )
        self._refresh_summary()

    def _refresh_summary(self):
        if not hasattr(self, "_sum_big") or not self._sum_big.winfo_exists():
            return
        mode = self.store.get("mode")
        folders = self.store.selected_folder_paths()
        if mode == "timed":
            poses, seconds = plan_total(self.store.plan)
        else:
            poses, seconds = int(self.store.get("relaxed_count")), 0
        self._sum_big.configure(text=str(poses))
        self._sum_small.configure(
            text=self.t("common.pose" if poses == 1 else "common.poses")
        )
        if mode == "timed":
            if self.store.plan:
                plan_value = self.t("plan.blocks", n=len(self.store.plan))
            else:
                plan_value = self.t("setup.no_planned")
            total_text = T.fmt_total(seconds, self.lang)
        else:
            plan_value = self.t("session.manual")
            total_text = self.t("session.no_time")
        values = {
            "images": str(poses),
            "total": total_text,
            "mode": self.t(f"mode.{mode}"),
            "folders": str(len(folders)),
            "plan": plan_value,
        }
        for key, label in self._sum_values.items():
            label.configure(text=values.get(key, ""))
        can_start = bool(folders) and ((mode == "relaxed") or bool(self.store.plan))
        self._sum_start.set_enabled(can_start)
        if can_start:
            self._sum_note.configure(text="")
        else:
            self._sum_note.configure(
                text=self.t("setup.no_folders") if not folders else self.t("plan.empty")
            )
        photo, key = self._summary_cover_data()
        if key != self._sum_cover_key:
            self._sum_cover_key = key
            self._sum_cover_photo = photo
            if photo is not None:
                self._sum_cover.configure(image=photo, text="", height=0)
            else:
                self._sum_cover.configure(image="", text=self.t("practice.add_folder"),
                                          height=7, compound="center")
        elif photo is not None and self._sum_cover_photo is None:
            self._sum_cover_photo = photo
            self._sum_cover.configure(image=photo, text="", height=0)

    def _summary_cover_data(self):
        folders = self.store.selected_folder_paths()
        if not folders:
            return None, None
        files = self.app.folder_files(folders[0])
        if not files:
            return None, None
        key = (folders[0], str(files[0]))
        if key == self._sum_cover_key and self._sum_cover_photo is not None:
            return self._sum_cover_photo, key
        pil = self.art.cover(files[0], (314, 172), 0)
        if pil is None:
            return None, key
        return self.keep(ImageTk.PhotoImage(pil)), key

    def _draw_placeholder(self, canvas):
        canvas.delete("all")
        w = max(1, canvas.winfo_width())
        canvas.create_rectangle(0, 0, w, 150, fill=T.SESSION_PANEL, outline="")
        draw_icon(canvas, "folder", w / 2, 70, 30, T.SESSION_MUTED, 1.6)
        canvas.create_text(w / 2, 102, text=self.t("practice.add_folder"),
                           fill=T.SESSION_MUTED, font=T.font(8))

    def _start(self):
        folders = self.store.selected_folder_paths()
        if not folders:
            MessageDialog(self, self.t("practice.empty_title"), self.t("practice.empty_body"),
                          self.t("common.ok"), icon="folder").show()
            return
        mode = self.store.get("mode")
        if mode == "timed" and not self.store.plan:
            MessageDialog(self, self.t("plan.empty"), self.t("plan.empty"),
                          self.t("common.ok"), icon="timer").show()
            return
        config = {
            "mode": mode,
            "folders": folders,
            "plan": [dict(b) for b in self.store.plan] if mode == "timed"
                    else [{"count": int(self.store.get("relaxed_count")), "duration": 0}],
            "relaxed_count": int(self.store.get("relaxed_count")),
            "shuffle": bool(self.store.get("shuffle")),
            "grayscale": bool(self.store.get("grayscale")),
            "rotation": 0,
            "warning_seconds": int(self.store.get("warning_seconds", 10)),
            "interval_sound": bool(self.store.get("interval_sound")),
            "show_timer": bool(self.store.get("show_timer")),
            "sound": bool(self.store.get("sound")),
        }
        self.app.start_session(config)


class WeeklyChart(tk.Canvas):
    def __init__(self, parent, bg=T.CARD):
        super().__init__(parent, height=168, bg=bg, highlightthickness=0, bd=0)
        self._data = []
        self._bg = bg
        self.bind("<Configure>", lambda e: self._draw())

    def set_data(self, data):
        self._data = data
        self._draw()

    def _draw(self):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w < 20:
            return
        pad_l, pad_r, pad_t, pad_b = 8, 8, 24, 28
        base = h - pad_b
        if not self._data:
            self.create_text(w / 2, h / 2, text="—", fill=T.FAINT, font=T.font(12))
            return
        mx = max([d[1] for d in self._data] + [1])
        for frac in (0.25, 0.5, 0.75):
            y = pad_t + (base - pad_t) * (1 - frac)
            self.create_line(pad_l, y, w - pad_r, y, fill=T.LINE, dash=(2, 4))
        n = len(self._data)
        slot = (w - pad_l - pad_r) / n
        bw = min(34, slot * 0.48)
        today = datetime.now().date()
        for i, (label, seconds, is_today) in enumerate(self._data):
            x = pad_l + slot * i + slot / 2
            bh = (base - pad_t) * (seconds / mx) if mx else 0
            if bh > 2:
                round_rect(self, x - bw / 2, base - bh, x + bw / 2, base, min(5, bw / 2),
                           T.ACCENT if is_today else T.LINE_STRONG, "")
                if seconds >= 3600:
                    val = f"{seconds / 3600:.1f}h".replace(".", ",")
                elif seconds >= 60:
                    val = f"{int(round(seconds / 60))}m"
                else:
                    val = f"{int(seconds)}s"
                self.create_text(x, base - bh - 10, text=val,
                                 fill=T.MUTED, font=T.font(7, "bold"))
            else:
                self.create_oval(x - 2, base - 2, x + 2, base + 2, fill=T.LINE_STRONG, outline="")
            self.create_text(x, base + 13, text=label, fill=T.INK if is_today else T.MUTED,
                             font=T.font(8, "bold" if is_today else "normal"))

    def lang_ref(self):
        # Filled by HistoryPage; fallback keeps the chart usable.
        return getattr(self, "lang", "es")


class HistoryPage(Page):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.sf = ScrollFrame(self, bg=T.CREAM)
        self.sf.pack(fill="both", expand=True)
        self.content = tk.Frame(self.sf.body, bg=T.CREAM)
        self.content.pack(fill="both", expand=True, padx=34, pady=20)
        self.chart = None
        self._render()
        self.after(60, self.sf.bind_wheel_tree)

    def _header(self):
        row = tk.Frame(self.content, bg=T.CREAM)
        row.pack(fill="x")
        left = tk.Frame(row, bg=T.CREAM)
        left.pack(side="left")
        eyebrow = tk.Frame(left, bg=T.CREAM)
        eyebrow.pack(anchor="w")
        tk.Frame(eyebrow, bg=T.ACCENT, width=26, height=3).pack(side="left", padx=(0, 9), pady=4)
        tk.Label(eyebrow, text=self.t("history.eyebrow"), bg=T.CREAM, fg=T.ACCENT,
                 font=T.font(8, "bold")).pack(side="left")
        tk.Label(left, text=self.t("history.title"), bg=T.CREAM, fg=T.INK,
                 font=T.font(29, "bold", T.SERIF), anchor="w").pack(anchor="w", pady=(9, 5))
        tk.Label(left, text=self.t("history.subtitle"), bg=T.CREAM, fg=T.MUTED,
                 font=T.font(9), anchor="w").pack(anchor="w")
        if self.store.history:
            buttons = tk.Frame(row, bg=T.CREAM)
            buttons.pack(side="right", anchor="n", pady=(4, 0))
            CanvasButton(buttons, self.t("history.export_image"), lambda: self._export("png"),
                         variant="ghost", icon="image", width=112, height=33, font_size=8).pack(
                side="left", padx=(0, 6)
            )
            CanvasButton(buttons, self.t("history.export_excel"), lambda: self._export("xlsx"),
                         variant="ghost", icon="grid", width=108, height=33, font_size=8).pack(
                side="left", padx=(0, 6)
            )
            CanvasButton(buttons, self.t("history.clear"), self._clear, variant="quiet",
                         icon="trash", width=150, height=33, font_size=8).pack(side="left")

    def _render(self):
        for child in self.content.winfo_children():
            child.destroy()
        self._header()
        history = self.store.history
        if not history:
            self._empty()
            return
        s = exports.summary(history)
        stats = tk.Frame(self.content, bg=T.CREAM)
        stats.pack(fill="x", pady=(22, 0))
        for i in range(4):
            stats.grid_columnconfigure(i, weight=1, uniform="st")
        cards = [
            (T.fmt_total(s["total"], self.lang), self.t("history.total_time"), True),
            (str(s["sessions"]), self.t("history.sessions"), False),
            (str(s["poses"]), self.t("history.poses"), False),
            (T.fmt_total(s["average"], self.lang), self.t("history.average"), False),
        ]
        for i, (value, label, accent) in enumerate(cards):
            self._stat(stats, i, value, label, accent)

        chart_box = tk.Frame(self.content, bg=T.CARD, highlightbackground=T.LINE, highlightthickness=1)
        chart_box.pack(fill="x", pady=(16, 0))
        head = tk.Frame(chart_box, bg=T.CARD)
        head.pack(fill="x", padx=16, pady=(13, 0))
        tk.Label(head, text=self.t("history.week"), bg=T.CARD, fg=T.INK,
                 font=T.font(10, "bold")).pack(side="left")
        week = exports.week_data(history)
        tk.Label(head, text=T.fmt_total(sum(d[1] for d in week), self.lang), bg=T.CARD,
                 fg=T.FAINT, font=T.font(8)).pack(side="right")
        chart = WeeklyChart(chart_box)
        chart.lang = self.lang
        chart.pack(fill="x", padx=12, pady=(2, 10))
        chart.set_data([(self.t(f"weekday.{key}"), secs, day == datetime.now().date())
                        for day, secs, key in week])
        tk.Label(self.content, text=self.t("history.recent"), bg=T.CREAM, fg=T.INK,
                 font=T.font(13, "bold"), anchor="w").pack(anchor="w", pady=(22, 8))
        listing = tk.Frame(self.content, bg=T.CARD, highlightbackground=T.LINE, highlightthickness=1)
        listing.pack(fill="x")
        for i, entry in enumerate(history[:30]):
            self._row(listing, entry, i)

    def _stat(self, parent, col, value, label, accent):
        bg = T.SIDEBAR if accent else T.CARD
        card = tk.Frame(parent, bg=bg, highlightbackground=T.SIDEBAR if accent else T.LINE,
                        highlightthickness=1)
        card.grid(row=0, column=col, sticky="nsew", padx=(0 if col == 0 else 8, 0))
        tk.Label(card, text=value, bg=bg, fg=T.ACCENT if accent else T.INK,
                 font=T.font(21, "bold", T.SERIF), anchor="w").pack(anchor="w", padx=15, pady=(11, 0))
        tk.Label(card, text=label, bg=bg, fg=T.SIDEBAR_MUTED if accent else T.MUTED,
                 font=T.font(8), anchor="w").pack(anchor="w", padx=15, pady=(0, 12))

    def _plan_text(self, entry):
        if entry.get("mode") == "relaxed":
            return self.t("history.free")
        return plan_label(entry.get("plan") or [], self.lang)

    def _row(self, parent, entry, index):
        bg = T.CARD if index % 2 == 0 else "#F7F2E9"
        row = tk.Frame(parent, bg=bg, padx=14, pady=9)
        row.pack(fill="x")
        left = tk.Frame(row, bg=bg, width=180)
        left.pack(side="left")
        tk.Label(left, text=T.fmt_date(entry.get("date", ""), self.lang), bg=bg, fg=T.INK,
                 font=T.font(8, "bold"), anchor="w").pack(anchor="w")
        folders = entry.get("folders") or []
        mode = self.t("history.mode_timed" if entry.get("mode") == "timed" else "history.mode_relaxed")
        tk.Label(left, text=f"{mode} · {self.t('history.folder_count', n=len(folders))}",
                 bg=bg, fg=T.MUTED, font=T.font(8), anchor="w").pack(anchor="w")
        mid = tk.Frame(row, bg=bg)
        mid.pack(side="left", fill="x", expand=True)
        tk.Label(mid, text=self._plan_text(entry), bg=bg, fg=T.INK, font=T.font(8, "bold"),
                 anchor="w", wraplength=430, justify="left").pack(anchor="w")
        tk.Label(mid, text=f"{T.images_label(int(entry.get('poses', 0)), self.lang)} · "
                            f"{T.fmt_total(entry.get('total_seconds', 0), self.lang)}",
                 bg=bg, fg=T.MUTED, font=T.font(8), anchor="w").pack(anchor="w")
        done = bool(entry.get("completed"))
        tk.Label(row, text=self.t("history.completed") if done else self.t("history.interrupted"),
                 bg=T.GREEN_SOFT if done else T.ACCENT_SOFT,
                 fg=T.GREEN if done else T.ACCENT_DARK,
                 font=T.font(7, "bold"), padx=8, pady=3).pack(side="right")
        if index < len(self.store.history) - 1:
            Hairline(parent, color=T.LINE).pack(fill="x")

    def _empty(self):
        box = tk.Frame(self.content, bg=T.CARD, highlightbackground=T.LINE, highlightthickness=1)
        box.pack(fill="x", pady=(26, 0))
        inner = tk.Frame(box, bg=T.CARD, pady=44)
        inner.pack()
        icon = tk.Canvas(inner, width=64, height=64, bg=T.CARD, highlightthickness=0)
        icon.pack()
        round_rect(icon, 4, 4, 60, 60, 30, T.ACCENT_PALE, "")
        draw_icon(icon, "clock", 32, 32, 26, T.ACCENT, 1.8)
        tk.Label(inner, text=self.t("history.empty"), bg=T.CARD, fg=T.MUTED,
                 font=T.font(10), justify="center").pack(pady=(12, 14))
        CanvasButton(inner, self.t("history.start"), lambda: self.app.show_page("practice"),
                     variant="primary", width=200, height=40, font_size=9, icon="play").pack()

    def _export(self, kind):
        if not self.store.history:
            return
        if kind == "png":
            path = filedialog.asksaveasfilename(
                parent=self, title=self.t("history.export_image_title"),
                defaultextension=".png", initialfile="Tpose_historial.png",
                filetypes=[("PNG", "*.png")],
            )
        else:
            path = filedialog.asksaveasfilename(
                parent=self, title=self.t("history.export_excel_title"),
                defaultextension=".xlsx", initialfile="Tpose_historial.xlsx",
                filetypes=[("Excel", "*.xlsx")],
            )
        if not path:
            return
        try:
            if kind == "png":
                exports.export_png(path, self.store.history, self.lang)
            else:
                exports.export_xlsx(path, self.store.history, self.lang)
            self.app.toast(self.t("history.exported"))
        except Exception:
            MessageDialog(self, self.t("dialog.error"), self.t("history.export_error"),
                          self.t("common.ok"), icon="info").show()

    def _clear(self):
        ok = ConfirmDialog(self, self.t("history.clear_title"), self.t("history.clear_body"),
                           self.t("history.clear_yes"), self.t("common.cancel"), danger=True,
                           icon="trash", icon_color=T.RED).show()
        if ok:
            self.store.clear_history()
            self.app.toast(self.t("toast.history_cleared"))
            self.app.show_page("history")


class AboutPage(Page):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        sf = ScrollFrame(self, bg=T.CREAM)
        sf.pack(fill="both", expand=True)
        content = tk.Frame(sf.body, bg=T.CREAM)
        content.pack(fill="both", expand=True, padx=34, pady=24)
        self._header(content)
        self._body(content)
        self.after(60, sf.bind_wheel_tree)

    def _header(self, parent):
        row = tk.Frame(parent, bg=T.CREAM)
        row.pack(fill="x")
        left = tk.Frame(row, bg=T.CREAM)
        left.pack(side="left", fill="x", expand=True)
        eyebrow = tk.Frame(left, bg=T.CREAM)
        eyebrow.pack(anchor="w")
        tk.Frame(eyebrow, bg=T.ACCENT, width=26, height=3).pack(side="left", padx=(0, 9), pady=4)
        tk.Label(eyebrow, text=self.t("about.eyebrow"), bg=T.CREAM, fg=T.ACCENT,
                 font=T.font(8, "bold")).pack(side="left")
        tk.Label(left, text=self.t("about.title"), bg=T.CREAM, fg=T.INK,
                 font=T.font(28, "bold", T.SERIF), justify="left", anchor="w").pack(
            anchor="w", pady=(9, 6)
        )
        tk.Label(left, text=self.t("about.subtitle"), bg=T.CREAM, fg=T.MUTED,
                 font=T.font(9), justify="left", anchor="w", wraplength=650).pack(anchor="w")
        try:
            base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
            icon = Image.open(base / "assets" / "ui" / "icon.png").resize((96, 96), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(icon)
            self.keep(photo)
            tk.Label(row, image=photo, bg=T.CREAM, bd=0).pack(side="right", padx=(20, 0), anchor="n")
        except (OSError, ValueError):
            pass

    def _body(self, parent):
        row = tk.Frame(parent, bg=T.CREAM)
        row.pack(fill="both", expand=True, pady=(24, 0))
        row.grid_columnconfigure(0, weight=1, uniform="about")
        row.grid_columnconfigure(1, weight=1, uniform="about")

        how = tk.Frame(row, bg=T.CARD, highlightbackground=T.LINE, highlightthickness=1)
        how.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        inner = tk.Frame(how, bg=T.CARD, padx=18, pady=16)
        inner.pack(fill="both", expand=True)
        tk.Label(inner, text=self.t("about.how_t"), bg=T.CARD, fg=T.INK,
                 font=T.font(11, "bold"), anchor="w").pack(anchor="w", pady=(0, 8))
        for i, key in enumerate(("about.how_1", "about.how_2", "about.how_3"), 1):
            line = tk.Frame(inner, bg=T.CARD)
            line.pack(fill="x", pady=4)
            n = tk.Canvas(line, width=24, height=24, bg=T.CARD, highlightthickness=0)
            n.pack(side="left", anchor="n")
            round_rect(n, 1, 1, 23, 23, 11, T.ACCENT_PALE, "")
            n.create_text(12, 12, text=str(i), fill=T.ACCENT_DARK, font=T.font(8, "bold"))
            tk.Label(line, text=self.t(key), bg=T.CARD, fg=T.MUTED, font=T.font(8),
                     wraplength=380, justify="left", anchor="w").pack(
                side="left", fill="x", expand=True, padx=(8, 0)
            )

        shortcuts = tk.Frame(row, bg=T.CARD, highlightbackground=T.LINE, highlightthickness=1)
        shortcuts.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        si = tk.Frame(shortcuts, bg=T.CARD, padx=18, pady=16)
        si.pack(fill="both", expand=True)
        tk.Label(si, text=self.t("about.shortcuts"), bg=T.CARD, fg=T.INK,
                 font=T.font(11, "bold"), anchor="w").pack(anchor="w", pady=(0, 8))
        pairs = [
            ("key.space", "about.shortcut_pause"),
            ("key.arrows", "about.shortcut_move"),
            ("key.rotate", "about.shortcut_rotate"),
            ("key.flip", "about.shortcut_flip"),
            ("key.bw", "about.shortcut_bw"),
            ("key.fullscreen", "about.shortcut_full"),
            ("key.escape", "about.shortcut_exit"),
            ("key.sound", "about.shortcut_sound"),
        ]
        for key, desc in pairs:
            line = tk.Frame(si, bg=T.CARD)
            line.pack(fill="x", pady=3)
            tk.Label(line, text=self.t(key), bg=T.CREAM_DARK, fg=T.INK, font=T.font(8, "bold"),
                     padx=7, pady=3).pack(side="left")
            tk.Label(line, text=self.t(desc), bg=T.CARD, fg=T.MUTED, font=T.font(8),
                     anchor="w").pack(side="left", padx=(9, 0))

        credits = tk.Frame(parent, bg=T.CREAM_DARK)
        credits.pack(fill="x", pady=(20, 0))
        inner = tk.Frame(credits, bg=T.CREAM_DARK, padx=20, pady=18)
        inner.pack(fill="x")
        tk.Label(inner, text=self.t("about.credits_t"), bg=T.CREAM_DARK, fg=T.INK,
                 font=T.font(10, "bold"), anchor="w").pack(anchor="w")
        tk.Label(inner, text=self.t("about.credits"), bg=T.CREAM_DARK, fg=T.INK_SOFT,
                 font=T.font(11, "italic", T.SERIF), wraplength=900, justify="left",
                 anchor="w").pack(anchor="w", pady=(6, 10))
        bottom = tk.Frame(inner, bg=T.CREAM_DARK)
        bottom.pack(fill="x")
        tk.Label(bottom, text=self.t("brand.version", v=self.app.version) + "  ·  " + self.t("about.made"),
                 bg=T.CREAM_DARK, fg=T.FAINT, font=T.font(8)).pack(side="left")
        CanvasButton(bottom, self.t("about.folder"), self.app.open_data_folder, variant="ghost",
                     icon="folder", width=180, height=32, font_size=8).pack(side="right")
