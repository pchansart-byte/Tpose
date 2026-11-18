"""The timed drawing session for Tpose."""

from __future__ import annotations

import math
import sys
import time
import tkinter as tk
from collections import OrderedDict
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageTk

from . import theme as T
from .dialogs import ConfirmDialog
from .i18n import tr
from .library import make_sequence, plan_label, plan_total
from .widgets import (
    CanvasButton,
    CircleButton,
    Hairline,
    IconButton,
    ProgressBar,
    ToggleSwitch,
    draw_icon,
    round_rect,
)


class SoundPlayer:
    def __init__(self, root: tk.Misc, enabled: bool = True):
        self.root = root
        self.enabled = enabled

    def play(self, name: str):
        if not self.enabled:
            return
        try:
            if sys.platform.startswith("win"):
                import winsound
                base = Path(__file__).resolve().parents[1]
                if getattr(sys, "frozen", False):
                    base = Path(getattr(sys, "_MEIPASS"))
                path = base / "assets" / "ui" / name
                winsound.PlaySound(
                    str(path), winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT
                )
            else:
                self.root.bell()
        except Exception:
            try:
                self.root.bell()
            except tk.TclError:
                pass


class TimerRing(tk.Canvas):
    def __init__(self, parent, bg: str):
        super().__init__(parent, width=72, height=72, bg=bg, highlightthickness=0, bd=0)
        self._bg = bg
        self._text = "00:00"
        self._fraction = 1.0
        self._color = T.ACCENT
        self._sub = ""
        self._flash_until = 0.0
        self._flash_after = None
        self._flash_color = "#FFB199"

    def set(self, text: str, fraction: float, color: str, sub: str = ""):
        self._text = text
        self._fraction = max(0.0, min(1.0, fraction))
        self._color = color
        self._sub = sub
        self._draw()

    def flash(self, color: str = "#FFB199", duration: float = 0.18):
        self._flash_color = color
        self._flash_until = time.monotonic() + duration
        self._draw()
        if self._flash_after:
            try:
                self.after_cancel(self._flash_after)
            except tk.TclError:
                pass
        self._flash_after = self.after(int(duration * 1000), self._clear_flash)

    def _clear_flash(self):
        self._flash_after = None
        self._flash_until = 0.0
        if self.winfo_exists():
            self._draw()

    def _draw(self):
        self.delete("all")
        self.create_oval(7, 7, 65, 65, outline=T.SESSION_LINE, width=3)
        if self._fraction > 0.002:
            self.create_arc(7, 7, 65, 65, start=90, extent=-359.9 * self._fraction,
                            style="arc", outline=self._color, width=3)
        fill = self._flash_color if time.monotonic() < self._flash_until else T.SESSION_TEXT
        self.create_text(36, 32 if self._sub else 36, text=self._text, fill=fill,
                         font=T.font(14, "bold"))
        if self._sub:
            self.create_text(36, 48, text=self._sub, fill=T.SESSION_MUTED, font=T.font(6, "bold"))

    def destroy(self):
        if self._flash_after:
            try:
                self.after_cancel(self._flash_after)
            except tk.TclError:
                pass
            self._flash_after = None
        super().destroy()


class SessionScreen(tk.Frame):
    def __init__(self, parent, app, config: dict):
        super().__init__(parent, bg=T.SESSION_BG)
        self.app = app
        self.store = app.store
        self.art = app.art
        self.config = dict(config)
        self.folder_paths = [str(p) for p in config.get("folders", [])]
        self.folder_names = [Path(p).name for p in self.folder_paths]
        self.mode = config.get("mode", "timed")
        self.plan = [dict(b) for b in config.get("plan", [])] if self.mode == "timed" else []
        if self.mode == "timed":
            self.sequence_plan = self.plan
        else:
            relaxed_plan = config.get("plan") or []
            relaxed_count = max(1, int(config.get("relaxed_count", 20)))
            if relaxed_plan:
                relaxed_count = max(1, int(relaxed_plan[0].get("count", relaxed_count)))
            self.sequence_plan = [{"count": relaxed_count, "duration": 0}]
        self.grayscale = bool(config.get("grayscale"))
        self.warning_seconds = max(5, min(30, int(config.get("warning_seconds", 10))))
        self.interval_sound = bool(config.get("interval_sound", False))
        self.show_timer = bool(config.get("show_timer", True)) and self.mode == "timed"
        self.sound = SoundPlayer(self, bool(config.get("sound", True)))
        self.folders_for_sequence = [{"path": p, "enabled": True} for p in self.folder_paths]
        self.session_id = self.store.begin_image_session()
        self.refs, self.durations = make_sequence(
            self.folders_for_sequence, self.sequence_plan,
            bool(config.get("shuffle", True)),
            usage=self.store.get("image_usage", {}),
            session_id=self.session_id,
        )
        self.total = max(1, len(self.refs))
        self.planned_seconds = sum(self.durations)
        self.index = 0
        self.ref = None
        self.running = True
        self.paused = False
        self.transitioning = False
        self.finished = False
        self.summary_visible = False
        self.seen: set[int] = set()
        self.completed_poses: set[int] = set()
        self.total_active = 0.0
        self.pose_elapsed = 0.0
        self.current_duration = 0
        self._last_tick = time.monotonic()
        self._last_tick_sec = None
        self._next_interval = 30
        self._tick_after = None
        self._resize_after = None
        self._hint_after = None
        self._cursor_after = None
        self._prefetch_after = None
        self._saved = False
        self._history_saved = False
        self._photos: list = []
        self._plate: Image.Image | None = None
        self._summary_completed = False
        # Per-image orientation/colour state and a small frame cache.  This is
        # what makes next/previous feel instant after the first prefetch.
        self._transforms: dict[int, dict] = {}
        self._frames: OrderedDict[tuple, tuple] = OrderedDict()
        self._last_stage_size: tuple[int, int] = (0, 0)
        self._skip_prefetch_once = False
        self._was_fullscreen = bool(self.app.root.attributes("-fullscreen"))
        self._was_zoomed = self.app.root.state() == "zoomed"
        self._window_geom = self.app.root.geometry()
        self._fullscreen = self._was_fullscreen
        self._source_name = self._folders_caption()

        self._build_ui()
        self._bind_keys()
        self._load_pose(0)
        self.after(80, self._first_layout)
        self._last_tick = time.monotonic()
        self._tick_after = self.after(90, self._tick)
        self._schedule_hint()
        self._arm_cursor_hide()

    def _folders_caption(self) -> str:
        if len(self.folder_names) == 1:
            return self.folder_names[0]
        if len(self.folder_names) > 1:
            return self.t("history.folder_count", n=len(self.folder_names))
        return "—"

    # ------------------------------------------------------------------- UI
    def _build_ui(self):
        self.stage = tk.Canvas(self, bg=T.SESSION_BG, highlightthickness=0, bd=0)
        self.stage.pack(fill="both", expand=True)
        self.stage.bind("<Configure>", self._on_configure)

        self.top = tk.Frame(self, bg=T.SESSION_PANEL, height=78)
        self.top.place(x=0, y=0, relwidth=1, height=78)
        self.top.grid_propagate(False)
        self.top.grid_columnconfigure(0, weight=1)
        self.top.grid_columnconfigure(1, weight=0)
        self.top.grid_columnconfigure(2, weight=1)

        left = tk.Frame(self.top, bg=T.SESSION_PANEL)
        left.grid(row=0, column=0, sticky="w", padx=18, pady=10)
        self.exit_btn = IconButton(
            left, "close", self._request_end, size=34, icon_size=15, bg=T.SESSION_PANEL,
            fg=T.SESSION_MUTED, hover_bg=T.SESSION_PANEL_2, tooltip=self.t("session.end"),
        )
        self.exit_btn.pack(side="left", padx=(0, 11))
        labels = tk.Frame(left, bg=T.SESSION_PANEL)
        labels.pack(side="left")
        self.mode_label = tk.Label(labels, text=self._mode_caption(), bg=T.SESSION_PANEL,
                                   fg=T.SESSION_TEXT, font=T.font(9, "bold"), anchor="w")
        self.mode_label.pack(anchor="w")

        center = tk.Frame(self.top, bg=T.SESSION_PANEL)
        center.place(relx=0.5, rely=0.5, anchor="center")
        self.timer_ring = TimerRing(center, T.SESSION_PANEL)
        self.no_timer = tk.Label(center, text=self._no_timer_caption(), bg=T.SESSION_PANEL,
                                 fg=T.SESSION_TEXT, font=T.font(9, "bold"))
        if self.show_timer:
            self.timer_ring.pack()
        else:
            self.no_timer.pack(pady=26)

        right = tk.Frame(self.top, bg=T.SESSION_PANEL)
        right.grid(row=0, column=2, sticky="e", padx=18, pady=10)
        self.rotate_btn = IconButton(
            right, "rotate", self._rotate, size=34, icon_size=17, bg=T.SESSION_PANEL,
            fg=T.SESSION_MUTED, hover_bg=T.SESSION_PANEL_2, tooltip=self.t("session.rotate"),
        )
        self.rotate_btn.pack(side="left", padx=3)
        self.flip_h_btn = IconButton(
            right, "flip_h", self._flip_h, size=34, icon_size=17, bg=T.SESSION_PANEL,
            fg=T.SESSION_MUTED, hover_bg=T.SESSION_PANEL_2, tooltip=self.t("session.flip_h"),
        )
        self.flip_h_btn.pack(side="left", padx=2)
        self.flip_v_btn = IconButton(
            right, "flip_v", self._flip_v, size=34, icon_size=17, bg=T.SESSION_PANEL,
            fg=T.SESSION_MUTED, hover_bg=T.SESSION_PANEL_2, tooltip=self.t("session.flip_v"),
        )
        self.flip_v_btn.pack(side="left", padx=2)
        self.bw_btn = IconButton(
            right, "contrast", self._toggle_bw, size=34, icon_size=17, bg=T.SESSION_PANEL,
            fg=T.SESSION_MUTED, hover_bg=T.SESSION_PANEL_2, tooltip=self.t("session.bw"),
        )
        self.bw_btn.pack(side="left", padx=2)
        self.timer_btn = IconButton(
            right, "timer" if self.show_timer else "timer_off", self._toggle_timer,
            size=34, icon_size=16, bg=T.SESSION_PANEL, fg=T.SESSION_MUTED,
            hover_bg=T.SESSION_PANEL_2,
            tooltip=self.t("session.hide_timer" if self.show_timer else "session.show_timer"),
        )
        if self.mode == "timed":
            self.timer_btn.pack(side="left", padx=3)
        self.sound_btn = IconButton(
            right, "sound" if self.sound.enabled else "mute", self._toggle_sound,
            size=34, icon_size=16, bg=T.SESSION_PANEL, fg=T.SESSION_MUTED,
            hover_bg=T.SESSION_PANEL_2,
            tooltip=self.t("session.mute" if self.sound.enabled else "session.unmute"),
        )
        self.sound_btn.pack(side="left", padx=3)
        self.full_btn = IconButton(
            right, "contract" if self._fullscreen else "expand", self._toggle_fullscreen,
            size=34, icon_size=16, bg=T.SESSION_PANEL, fg=T.SESSION_MUTED,
            hover_bg=T.SESSION_PANEL_2,
            tooltip=self.t("session.exit_fullscreen" if self._fullscreen else "session.fullscreen"),
        )
        self.full_btn.pack(side="left", padx=3)

        self.bottom = tk.Frame(self, bg=T.SESSION_PANEL, height=92)
        self.bottom.place(x=0, rely=1.0, y=-92, relwidth=1, height=92)
        self.progress = ProgressBar(self.bottom, height=3, bg=T.SESSION_PANEL, fill=T.ACCENT)
        self.progress.pack(fill="x", side="top")
        inner = tk.Frame(self.bottom, bg=T.SESSION_PANEL)
        inner.pack(fill="both", expand=True, padx=22)
        inner.grid_columnconfigure(0, weight=1)
        inner.grid_columnconfigure(1, weight=0)
        inner.grid_columnconfigure(2, weight=1)
        left_b = tk.Frame(inner, bg=T.SESSION_PANEL)
        left_b.grid(row=0, column=0, sticky="w")
        self.folder_line = tk.Label(left_b, text="", bg=T.SESSION_PANEL, fg=T.SESSION_MUTED,
                                    font=T.font(8, italic=True), anchor="w",
                                    wraplength=270, justify="left")
        self.folder_line.pack(anchor="w")
        self.counter = tk.Label(left_b, text="", bg=T.SESSION_PANEL, fg=T.SESSION_TEXT,
                                font=T.font(11, "bold"), anchor="w")
        self.counter.pack(anchor="w")
        self.bottom_meta = tk.Label(left_b, text="", bg=T.SESSION_PANEL, fg=T.SESSION_MUTED,
                                    font=T.font(7), anchor="w")
        self.bottom_meta.pack(anchor="w")

        controls = tk.Frame(inner, bg=T.SESSION_PANEL)
        controls.place(relx=0.5, rely=0.55, anchor="center")
        self.prev_btn = IconButton(
            controls, "prev", self._previous, size=38, icon_size=17, bg=T.SESSION_PANEL,
            fg=T.SESSION_MUTED, hover_bg=T.SESSION_PANEL_2, tooltip=self.t("session.prev"),
        )
        self.prev_btn.pack(side="left", padx=5)
        self.pause_btn = CircleButton(
            controls, "pause", self._toggle_pause, size=50, icon_size=20,
            fill=T.ACCENT, hover=T.ACCENT_HOVER, fg=T.WHITE, bg=T.SESSION_PANEL,
            tooltip=self.t("session.pause"),
        )
        self.pause_btn.pack(side="left", padx=8)
        self.next_btn = IconButton(
            controls, "next", self._next, size=38, icon_size=17, bg=T.SESSION_PANEL,
            fg=T.SESSION_TEXT, hover_bg=T.SESSION_PANEL_2, tooltip=self.t("session.next"),
        )
        self.next_btn.pack(side="left", padx=5)

        right_b = tk.Frame(inner, bg=T.SESSION_PANEL)
        right_b.grid(row=0, column=2, sticky="e")
        self.elapsed_label = tk.Label(right_b, text="00:00", bg=T.SESSION_PANEL, fg=T.SESSION_TEXT,
                                      font=T.font(9, "bold"), anchor="e")
        self.elapsed_label.pack(anchor="e")
        self.elapsed_caption = tk.Label(right_b, text=self.t("session.elapsed"), bg=T.SESSION_PANEL,
                                        fg=T.SESSION_MUTED, font=T.font(7), anchor="e")
        self.elapsed_caption.pack(anchor="e", pady=(0, 4))
        self.end_btn = CanvasButton(
            right_b, self.t("session.end"), self._request_end, variant="sidebar",
            width=84, height=28, radius=7, font_size=8, padx=8,
        )
        self.end_btn.pack(anchor="e")

        self.hint = tk.Frame(self, bg=T.SESSION_PANEL_2, padx=12, pady=6)
        self.hint_label = tk.Label(self.hint, text=self.t("session.hint"), bg=T.SESSION_PANEL_2,
                                   fg=T.SESSION_MUTED, font=T.font(7))
        self.hint_label.pack()
        self.hint.place(relx=0.5, rely=1.0, y=-104, anchor="s")
        self.hint.lift()

        self._build_pause_overlay()

    def _build_pause_overlay(self):
        self.pause_overlay = tk.Frame(self, bg=T.SESSION_PANEL_2, highlightbackground=T.SESSION_LINE,
                                      highlightthickness=1)
        inner = tk.Frame(self.pause_overlay, bg=T.SESSION_PANEL_2, padx=34, pady=26)
        inner.pack()
        badge = tk.Canvas(inner, width=52, height=52, bg=T.SESSION_PANEL_2, highlightthickness=0)
        badge.pack()
        badge.create_oval(2, 2, 50, 50, outline=T.ACCENT, width=1)
        draw_icon(badge, "pause", 26, 26, 20, T.ACCENT, 1.8)
        self.pause_title = tk.Label(inner, text=self.t("session.paused_title"), bg=T.SESSION_PANEL_2,
                                    fg=T.SESSION_TEXT, font=T.font(24, "bold", T.SERIF))
        self.pause_title.pack(pady=(10, 3))
        self.pause_body = tk.Label(inner, text=self.t("session.paused_body"), bg=T.SESSION_PANEL_2,
                                   fg=T.SESSION_MUTED, font=T.font(9))
        self.pause_body.pack()
        self.resume_btn = CanvasButton(
            inner, self.t("session.resume"), self._toggle_pause, variant="primary",
            width=200, height=40, font_size=9, icon="play",
        )
        self.resume_btn.pack(pady=(18, 4))
        self.rotate_pause_btn = CanvasButton(
            inner, self.t("session.rotate"), self._rotate, variant="sidebar",
            width=200, height=34, font_size=8, icon="rotate",
        )
        self.rotate_pause_btn.pack(pady=(0, 4))
        self.pause_hint = tk.Label(inner, text=self.t("session.resume_hint"), bg=T.SESSION_PANEL_2,
                                   fg=T.SESSION_MUTED, font=T.font(7))
        self.pause_hint.pack(pady=(2, 0))

    def _mode_caption(self) -> str:
        if self.mode == "timed":
            return f"{self.t('mode.timed')} · {self.t('plan.blocks', n=len(self.plan))}"
        return self.t("mode.relaxed")

    def _source_caption(self) -> str:
        if self.mode == "relaxed":
            return f"{self._source_name} · {self.t('mode.relaxed')}"
        return self._source_name

    def _no_timer_caption(self) -> str:
        return self.t("session.manual") if self.mode == "relaxed" else self.t("session.auto")

    # -------------------------------------------------------------- lifecycle
    def _first_layout(self):
        self._render_current()
        self.counter.configure(text=self._counter_text())
        self.bottom_meta.configure(text=self._bottom_meta())
        self.elapsed_label.configure(text="00:00")

    def _bind_keys(self):
        self._key_bind = self.app.root.bind("<KeyPress>", self._on_key, add="+")
        self._motion_bind = self.app.root.bind("<Motion>", self._wake_cursor, add="+")
        self._click_bind = self.app.root.bind("<Button-1>", self._wake_cursor, add="+")

    def _unbind_keys(self):
        for seq, fid in (("<KeyPress>", getattr(self, "_key_bind", None)),
                         ("<Motion>", getattr(self, "_motion_bind", None)),
                         ("<Button-1>", getattr(self, "_click_bind", None))):
            if fid:
                try:
                    self.app.root.unbind(seq, fid)
                except tk.TclError:
                    pass

    def _on_key(self, event):
        if self.finished or self.summary_visible:
            if event.keysym == "Escape":
                self.app.leave_session("practice")
            return
        if self._has_grab():
            return
        if isinstance(event.widget, (CanvasButton, CircleButton, IconButton, ToggleSwitch)):
            return
        key = event.keysym
        if key == "space":
            self._toggle_pause()
            return "break"
        if key == "Right":
            self._next()
            return "break"
        if key == "Left":
            self._previous()
            return "break"
        if key in ("r", "R"):
            self._rotate()
            return "break"
        if key in ("h", "H"):
            self._flip_h()
            return "break"
        if key in ("v", "V"):
            self._flip_v()
            return "break"
        if key in ("b", "B"):
            self._toggle_bw()
            return "break"
        if key in ("f", "F", "F11"):
            self._toggle_fullscreen()
            return "break"
        if key in ("s", "S"):
            self._toggle_sound()
            return "break"
        if key == "Escape":
            if self._fullscreen:
                self._toggle_fullscreen()
            elif self.paused:
                self._toggle_pause()
            else:
                self._request_end()
            return "break"

    def _has_grab(self):
        try:
            return self.app.root.grab_current() is not None
        except tk.TclError:
            return False

    # ----------------------------------------------------------------- timer
    def _tick(self):
        if self.finished:
            return
        now = time.monotonic()
        dt = max(0.0, min(0.5, now - self._last_tick))
        self._last_tick = now
        delay = 90
        if self.running and not self.paused and not self.transitioning:
            self.total_active += dt
            self.pose_elapsed += dt
            if self.mode == "timed":
                remaining = max(0.0, self.current_duration - self.pose_elapsed)
                if self.show_timer:
                    self._update_timer(remaining)
                self._warning_tick(remaining)
                if remaining <= self.warning_seconds + 0.5:
                    delay = 55
                if remaining <= 0:
                    self._auto_next()
            if self.interval_sound and self.total_active >= self._next_interval:
                self._next_interval += 30
                self.sound.play("chime.wav")
            self.elapsed_label.configure(text=T.fmt_elapsed(self.total_active))
        self._tick_after = self.after(delay, self._tick)

    def _update_timer(self, remaining: float | None):
        if self.mode != "timed" or remaining is None:
            return
        fraction = remaining / max(1, self.current_duration)
        color = T.ACCENT
        if remaining <= self.warning_seconds:
            color = "#E05A43"
        elif remaining <= self.warning_seconds + 5:
            color = "#D08A3E"
        self.timer_ring.set(T.fmt_clock(remaining), fraction, color)

    def _warning_tick(self, remaining: float):
        sec = int(math.ceil(remaining))
        if 0 < sec <= self.warning_seconds:
            if self._last_tick_sec != sec:
                self._last_tick_sec = sec
                if self.show_timer:
                    self.timer_ring.flash()
                self.sound.play("warning.wav")

    def _auto_next(self):
        if self.transitioning:
            return
        self.transitioning = True
        self.running = False
        self.completed_poses.add(self.index)
        if self.index < self.total - 1:
            self.sound.play("chime.wav")
        self._update_progress()
        if self.index >= self.total - 1:
            self.after(260, lambda: self._finish(True))
        else:
            self.after(220, lambda: self._advance())

    def _advance(self):
        self.transitioning = False
        self.running = True
        self.paused = False
        self.pose_elapsed = 0
        self._last_tick_sec = None
        self._load_pose(min(self.total - 1, self.index + 1))
        self._last_tick = time.monotonic()

    def _next(self):
        if self.finished or self.transitioning:
            return
        self._wake_cursor()
        if self.paused:
            self._toggle_pause()
        if self.index >= self.total - 1:
            self._request_end()
            return
        self.completed_poses.add(self.index)
        self._advance()
        self.sound.play("chime.wav")

    def _previous(self):
        if self.finished or self.transitioning:
            return
        self._wake_cursor()
        if self.paused:
            self._toggle_pause()
        if self.index <= 0:
            return
        self.index -= 1
        self._load_pose(self.index)
        self._last_tick = time.monotonic()

    def _load_pose(self, index):
        self.index = index
        self.ref = self.refs[index] if self.refs else None
        self.current_duration = self.durations[index] if index < len(self.durations) else 0
        if self.ref is not None:
            self.store.mark_image_used(self.ref.path, self.session_id)
            self._update_folder_name()
        self.seen.add(index)
        self.pose_elapsed = 0.0
        self._last_tick_sec = None
        self._state(index)
        self.counter.configure(text=self._counter_text())
        self.bottom_meta.configure(text=self._bottom_meta())
        self._update_progress()
        self._render_current()
        self._update_transform_buttons()
        if self.show_timer:
            self._update_timer(float(self.current_duration))

    def _counter_text(self) -> str:
        return self.t("session.pose_of", current=self.index + 1, total=self.total)

    def _update_folder_name(self):
        if not self.ref:
            return
        name = Path(self.ref.path).parent.name or self._folders_caption()
        self.folder_line.configure(text=name)

    def _bottom_meta(self) -> str:
        if self.mode == "relaxed":
            return self.t("session.manual")
        return f"{self.t('session.auto')} · {plan_label(self.plan, self.app.lang)}"

    def _update_progress(self):
        self.progress.set(min(1.0, len(self.completed_poses) / max(1, self.total)))

    # ---------------------------------------------------------------- drawing
    def _state(self, index=None):
        index = self.index if index is None else index
        return self._transforms.setdefault(index, {
            "rot": 0, "flip_h": False, "flip_v": False, "bw": False,
        })

    def _frame_key(self, index, w, h):
        st = self._state(index)
        return (index, w, h, st["rot"], st["flip_h"], st["flip_v"], st["bw"], self.grayscale)

    def _on_configure(self, event):
        if self.finished:
            return
        # Debounce resize storms.  Do not throw away the current image while
        # the user drags the window; apply one clean resize at the end.
        if self._resize_after:
            try:
                self.after_cancel(self._resize_after)
            except tk.TclError:
                pass
        self._resize_after = self.after(600, self._apply_resize)

    def _apply_resize(self):
        self._resize_after = None
        if self.finished:
            return
        w = self.stage.winfo_width()
        h = self.stage.winfo_height()
        if w < 200 or h < 200:
            return
        if (w, h) == self._last_stage_size:
            return
        self._last_stage_size = (w, h)
        self._frames.clear()
        if self._prefetch_after:
            try:
                self.after_cancel(self._prefetch_after)
            except tk.TclError:
                pass
            self._prefetch_after = None
        self._skip_prefetch_once = True
        self._render_current()

    def _compose_frame(self, index, w, h):
        ref = self.refs[index] if index < len(self.refs) else None
        if ref is None:
            return None
        st = self._state(index)
        max_w = max(220, w - 150)
        max_h = max(160, h - 78 - 92 - 28)
        aspect = self.art.image_aspect(ref.path, st["rot"])
        if aspect >= max_w / max_h:
            pw = max_w
            ph = int(round(max_w / aspect))
        else:
            ph = max_h
            pw = int(round(max_h * aspect))
        pw, ph = max(2, pw), max(2, ph)
        self.art.preload(ref.path)
        plate = self.art.photo(
            ref.path, (pw, ph), self.grayscale or st["bw"],
            st["rot"], st["flip_h"], st["flip_v"],
        )
        if plate is None:
            return None
        backdrop = self.art.backdrop(plate, (w, h), dim=0.16)
        return (
            ImageTk.PhotoImage(backdrop),
            ImageTk.PhotoImage(plate),
            plate, pw, ph,
        )

    def _cache_frame(self, key, frame):
        self._frames[key] = frame
        self._frames.move_to_end(key)
        while len(self._frames) > 6:
            self._frames.popitem(last=False)

    def _draw_frame(self, frame):
        bg_photo, photo, plate, pw, ph = frame
        self._plate = plate
        self._photos = [bg_photo, photo]
        w = self.stage.winfo_width()
        h = self.stage.winfo_height()
        self.stage.delete("all")
        self.stage.create_image(0, 0, image=bg_photo, anchor="nw")
        x = (w - pw) // 2
        y = 78 + (h - 78 - 92 - ph) // 2
        self.stage.create_rectangle(x - 1, y - 1, x + pw + 1, y + ph + 1,
                                    outline=T.SESSION_LINE, width=1)
        self.stage.create_image(x, y, image=photo, anchor="nw")

    def _render_current(self):
        if not self.ref or self.finished:
            return
        w = self.stage.winfo_width()
        h = self.stage.winfo_height()
        if w < 200 or h < 200:
            return
        self._last_stage_size = (w, h)
        key = self._frame_key(self.index, w, h)
        frame = self._frames.get(key)
        if frame is None:
            frame = self._compose_frame(self.index, w, h)
            if frame is None:
                self.stage.delete("all")
                self.stage.create_text(w / 2, h / 2, text=self.t("session.image_error"),
                                       fill=T.SESSION_MUTED, font=T.font(11))
                return
            self._cache_frame(key, frame)
        else:
            self._frames.move_to_end(key)
        self._draw_frame(frame)
        self._update_transform_buttons()
        self._schedule_prefetch()

    def _schedule_prefetch(self):
        if self._skip_prefetch_once:
            self._skip_prefetch_once = False
            return
        if self._prefetch_after:
            try:
                self.after_cancel(self._prefetch_after)
            except tk.TclError:
                pass
        self._prefetch_after = self.after(160, self._prefetch_adjacent)

    def _prefetch_adjacent(self):
        self._prefetch_after = None
        if self.finished or self.summary_visible or not self.ref:
            return
        w = self.stage.winfo_width()
        h = self.stage.winfo_height()
        if w < 200 or h < 200:
            return
        for index in (self.index + 1,):
            if not (0 <= index < self.total):
                continue
            key = self._frame_key(index, w, h)
            if key in self._frames:
                continue
            try:
                frame = self._compose_frame(index, w, h)
            except Exception:
                frame = None
            if frame is not None:
                self._cache_frame(key, frame)

    def _update_transform_buttons(self):
        st = self._state()
        self.flip_h_btn.set_active(bool(st["flip_h"]))
        self.flip_v_btn.set_active(bool(st["flip_v"]))
        self.bw_btn.set_active(bool(st["bw"]))

    def _rotate(self):
        if self.finished:
            return
        st = self._state()
        st["rot"] = (st["rot"] + 90) % 360
        self._wake_cursor()
        self._render_current()

    def _flip_h(self):
        if self.finished:
            return
        st = self._state()
        st["flip_h"] = not st["flip_h"]
        self._update_transform_buttons()
        self._render_current()

    def _flip_v(self):
        if self.finished:
            return
        st = self._state()
        st["flip_v"] = not st["flip_v"]
        self._update_transform_buttons()
        self._render_current()

    def _toggle_bw(self):
        if self.finished:
            return
        st = self._state()
        st["bw"] = not st["bw"]
        self._update_transform_buttons()
        self._render_current()

    # ---------------------------------------------------------------- actions
    def _toggle_pause(self):
        if self.finished or self.transitioning:
            return
        self.paused = not self.paused
        if self.paused:
            self.pause_btn.set_icon("play")
            if self.pause_btn.tooltip:
                self.pause_btn.tooltip.set_text(self.t("session.resume"))
            self.pause_overlay.place(relx=0.5, rely=0.5, anchor="center")
            self.pause_overlay.lift()
            self._wake_cursor()
            self._cancel_cursor_hide()
        else:
            self.pause_btn.set_icon("pause")
            if self.pause_btn.tooltip:
                self.pause_btn.tooltip.set_text(self.t("session.pause"))
            self.pause_overlay.place_forget()
            self._arm_cursor_hide()
        self._last_tick = time.monotonic()

    def _toggle_sound(self):
        self.sound.enabled = not self.sound.enabled
        self.store.set("sound", self.sound.enabled)
        self.sound_btn.set_icon("sound" if self.sound.enabled else "mute")
        if self.sound_btn.tooltip:
            self.sound_btn.tooltip.set_text(
                self.t("session.mute" if self.sound.enabled else "session.unmute")
            )

    def _toggle_timer(self):
        if self.mode != "timed":
            return
        self.show_timer = not self.show_timer
        self.store.set("show_timer", self.show_timer)
        if self.show_timer:
            self.timer_ring.pack()
            self.no_timer.pack_forget()
            self.timer_btn.set_icon("timer")
            if self.timer_btn.tooltip:
                self.timer_btn.tooltip.set_text(self.t("session.hide_timer"))
        else:
            self.timer_ring.pack_forget()
            self.no_timer.pack(pady=26)
            self.timer_btn.set_icon("timer_off")
            if self.timer_btn.tooltip:
                self.timer_btn.tooltip.set_text(self.t("session.show_timer"))
        self._last_tick_sec = None

    def _toggle_language(self):
        self.app.toggle_language()
        self.apply_locale()

    def apply_locale(self):
        self._source_name = self._folders_caption()
        self.mode_label.configure(text=self._mode_caption())
        self._update_folder_name()
        self.no_timer.configure(text=self._no_timer_caption())
        self.counter.configure(text=self._counter_text())
        self.bottom_meta.configure(text=self._bottom_meta())
        self.elapsed_caption.configure(text=self.t("session.elapsed"))
        self.end_btn.set_text(self.t("session.end"))
        self.hint_label.configure(text=self.t("session.hint"))
        self.pause_title.configure(text=self.t("session.paused_title"))
        self.pause_body.configure(text=self.t("session.paused_body"))
        self.resume_btn.set_text(self.t("session.resume"))
        self.rotate_pause_btn.set_text(self.t("session.rotate"))
        self.pause_hint.configure(text=self.t("session.resume_hint"))
        for button, key in (
            (self.exit_btn, "session.end"), (self.rotate_btn, "session.rotate"),
            (self.flip_h_btn, "session.flip_h"), (self.flip_v_btn, "session.flip_v"),
            (self.bw_btn, "session.bw"), (self.prev_btn, "session.prev"),
            (self.next_btn, "session.next"),
        ):
            if button.tooltip:
                button.tooltip.set_text(self.t(key))
        self.sound_btn.tooltip and self.sound_btn.tooltip.set_text(
            self.t("session.mute" if self.sound.enabled else "session.unmute"))
        self.timer_btn.tooltip and self.timer_btn.tooltip.set_text(
            self.t("session.hide_timer" if self.show_timer else "session.show_timer"))
        self.full_btn.tooltip and self.full_btn.tooltip.set_text(
            self.t("session.exit_fullscreen" if self._fullscreen else "session.fullscreen"))
        self.pause_btn.tooltip and self.pause_btn.tooltip.set_text(
            self.t("session.resume" if self.paused else "session.pause"))
        if self.summary_visible:
            self._build_summary(self._summary_completed)

    def _toggle_fullscreen(self):
        self._fullscreen = not self._fullscreen
        self.app.root.attributes("-fullscreen", self._fullscreen)
        self.full_btn.set_icon("contract" if self._fullscreen else "expand")
        if self.full_btn.tooltip:
            self.full_btn.tooltip.set_text(
                self.t("session.exit_fullscreen" if self._fullscreen else "session.fullscreen"))
        if not self._fullscreen:
            try:
                if self._was_zoomed:
                    self.app.root.state("zoomed")
                else:
                    self.app.root.geometry(self._window_geom)
            except tk.TclError:
                pass
            self.after(100, lambda: self.app.ensure_window_chrome(True))
        self._wake_cursor()
        self.after(140, self._render_current)

    # ---------------------------------------------------------------- cursor
    def _schedule_hint(self):
        self._hint_after = self.after(6000, self._hide_hint)

    def _hide_hint(self):
        if self.hint.winfo_exists():
            self.hint.place_forget()

    def _arm_cursor_hide(self):
        self._cancel_cursor_hide()
        if self.paused or self.summary_visible or self.finished:
            return
        self._cursor_after = self.after(2600, self._hide_cursor)

    def _cancel_cursor_hide(self):
        if self._cursor_after:
            try:
                self.after_cancel(self._cursor_after)
            except tk.TclError:
                pass
            self._cursor_after = None

    def _hide_cursor(self):
        if self.paused or self.summary_visible or self.finished:
            return
        try:
            self.app.root.configure(cursor="none")
        except tk.TclError:
            pass

    def _wake_cursor(self, _event=None):
        try:
            self.app.root.configure(cursor="")
        except tk.TclError:
            pass
        if not self.paused and not self.summary_visible and not self.finished:
            self._arm_cursor_hide()

    # ---------------------------------------------------------------- finish
    def _request_end(self):
        if self.finished:
            return
        self._wake_cursor()
        was_paused = self.paused
        self.paused = True
        self.pause_overlay.place_forget()
        ok = ConfirmDialog(
            self, self.t("session.confirm_end_title"), self.t("session.confirm_end_body"),
            self.t("session.confirm_end_yes"), self.t("session.confirm_end_no"),
            icon="info", icon_color=T.ACCENT,
        ).show()
        self.paused = was_paused
        if ok:
            self._finish(False)
        else:
            if self.paused:
                self.pause_overlay.place(relx=0.5, rely=0.5, anchor="center")
            self._last_tick = time.monotonic()

    def _finish(self, completed):
        if self.finished:
            return
        self.finished = True
        self.running = False
        self.paused = False
        self.summary_visible = True
        self._summary_completed = bool(completed)
        self._cancel_cursor_hide()
        self._toggle_ui_for_summary()
        self._save_history(completed)
        self._build_summary(completed)
        self.sound.play("chime.wav")
        try:
            self.app.root.configure(cursor="")
        except tk.TclError:
            pass

    def _toggle_ui_for_summary(self):
        for widget in (self.top, self.bottom, self.hint, self.pause_overlay):
            if widget.winfo_exists():
                widget.place_forget()

    def _save_history(self, completed):
        if self._saved:
            return False
        self._saved = True
        if self.total_active < 5 and len(self.seen) <= 1 and not completed:
            return False
        entry = {
            "date": datetime.now().astimezone().isoformat(timespec="seconds"),
            "mode": self.mode,
            "folders": self.folder_names,
            "plan": self.plan,
            "poses": len(self.seen),
            "total_seconds": int(round(self.total_active)),
            "planned_seconds": self.planned_seconds,
            "completed": bool(completed),
        }
        self.app.record_session(entry)
        self._history_saved = True
        return True

    def _build_summary(self, completed):
        if hasattr(self, "summary_overlay") and self.summary_overlay.winfo_exists():
            self.summary_overlay.destroy()
        self.summary_visible = True
        overlay = tk.Frame(self, bg=T.SESSION_BG)
        overlay.place(x=0, y=0, relwidth=1, relheight=1)
        overlay.lift()
        self.summary_overlay = overlay
        bg = tk.Canvas(overlay, bg=T.SESSION_BG, highlightthickness=0, bd=0)
        bg.pack(fill="both", expand=True)
        if self._plate is not None:
            try:
                ow, oh = overlay.winfo_width(), overlay.winfo_height()
                if ow < 20:
                    ow = 1440
                if oh < 20:
                    oh = 900
                backdrop = self.art.backdrop(self._plate, (max(2, ow), max(2, oh)), dim=0.22)
                photo = ImageTk.PhotoImage(backdrop)
                self._photos.append(photo)
                bg.create_image(0, 0, image=photo, anchor="nw")
            except (tk.TclError, ValueError):
                pass
        top_strip = tk.Frame(overlay, bg=T.SESSION_BG, height=56)
        top_strip.place(x=0, y=0, relwidth=1, height=56)
        tk.Label(top_strip, text="TPOSE", bg=T.SESSION_BG, fg=T.ACCENT,
                 font=T.font(8, "bold")).place(x=28, y=19)
        top_strip.lift()
        card = tk.Frame(bg, bg=T.SESSION_PANEL, highlightbackground=T.SESSION_LINE, highlightthickness=1)
        card.place(relx=0.5, rely=0.5, anchor="center")
        inner = tk.Frame(card, bg=T.SESSION_PANEL, padx=38, pady=30)
        inner.pack(fill="both", expand=True)
        tk.Label(inner, text=self.t("session.finished_title" if completed else "session.interrupted_title"),
                 bg=T.SESSION_PANEL, fg=T.ACCENT, font=T.font(8, "bold")).pack(pady=(2, 3))
        poses = len(self.seen)
        tk.Label(inner, text=T.images_label(poses, self.app.lang), bg=T.SESSION_PANEL,
                 fg=T.SESSION_TEXT, font=T.font(33, "bold", T.SERIF)).pack()
        tk.Label(inner, text=self.t("session.summary_time", time=T.fmt_total(self.total_active, self.app.lang)),
                 bg=T.SESSION_PANEL, fg=T.SESSION_MUTED, font=T.font(9)).pack(pady=(2, 0))
        Hairline(inner, color=T.SESSION_LINE).pack(fill="x", pady=(20, 16))
        stats = tk.Frame(inner, bg=T.SESSION_PANEL)
        stats.pack(fill="x")
        for i in range(3):
            stats.grid_columnconfigure(i, weight=1, uniform="sst")
        avg = self.total_active / max(1, len(self.completed_poses) or len(self.seen))
        stats_data = [
            (T.fmt_total(avg, self.app.lang), self.t("session.summary_avg")),
            (self.t(f"mode.{self.mode}"), self.t("session.summary_mode")),
            (self._folders_caption(), self.t("session.summary_folders")),
        ]
        for i, (value, label) in enumerate(stats_data):
            cell = tk.Frame(stats, bg=T.SESSION_PANEL)
            cell.grid(row=0, column=i, sticky="n")
            tk.Label(cell, text=value, bg=T.SESSION_PANEL, fg=T.SESSION_TEXT,
                     font=T.font(11, "bold"), wraplength=150, justify="center").pack()
            tk.Label(cell, text=label, bg=T.SESSION_PANEL, fg=T.SESSION_MUTED,
                     font=T.font(7)).pack(pady=(3, 0))
        if self.mode == "timed" and self.plan:
            tk.Label(inner, text=plan_label(self.plan, self.app.lang), bg=T.SESSION_PANEL,
                     fg=T.SESSION_MUTED, font=T.font(8), wraplength=520,
                     justify="center").pack(pady=(14, 0))
        tk.Label(inner, text=self.t("session.summary_encourage"), bg=T.SESSION_PANEL,
                 fg=T.SESSION_MUTED, font=T.font(8), wraplength=480,
                 justify="center").pack(pady=(16, 16))
        buttons = tk.Frame(inner, bg=T.SESSION_PANEL)
        buttons.pack(fill="x")
        CanvasButton(buttons, self.t("session.again"), self._repeat, variant="primary",
                     width=170, height=42, font_size=9, icon="play").pack(side="left")
        CanvasButton(buttons, self.t("session.new"), lambda: self.app.leave_session("practice"),
                     variant="sidebar", width=150, height=42, font_size=9, icon="grid").pack(
            side="left", padx=(8, 0))
        CanvasButton(buttons, self.t("session.to_history"), lambda: self.app.leave_session("history"),
                     variant="sidebar", width=150, height=42, font_size=9, icon="clock").pack(
            side="left", padx=(8, 0))
        if not self._history_saved:
            tk.Label(inner, text=self.t("session.too_short"), bg=T.SESSION_PANEL,
                     fg=T.SESSION_MUTED, font=T.font(7)).pack(pady=(10, 0))

    def _repeat(self):
        self.app.start_session(dict(self.config))

    def save_abandoned(self):
        if not self.finished and (self.total_active >= 5 or len(self.seen) > 1):
            self._save_history(False)

    def destroy(self):
        for attr in ("_tick_after", "_resize_after", "_hint_after", "_cursor_after", "_prefetch_after"):
            after = getattr(self, attr, None)
            if after:
                try:
                    self.after_cancel(after)
                except tk.TclError:
                    pass
        self._unbind_keys()
        if self._fullscreen:
            try:
                self.app.root.attributes("-fullscreen", False)
            except tk.TclError:
                pass
        try:
            self.app.root.configure(cursor="")
        except tk.TclError:
            pass
        super().destroy()

    def t(self, key: str, **kwargs) -> str:
        return tr(self.app.lang, key, **kwargs)
