"""Tpose application shell: sidebar, navigation and lifecycle."""

from __future__ import annotations

import ctypes
import os
import subprocess
import sys
import tkinter as tk
from pathlib import Path

from PIL import Image, ImageTk

from . import theme as T
from .art import Artwork
from .dialogs import ConfirmDialog, MessageDialog
from .i18n import LANGUAGES, tr
from .library import scan_folder
from .pages import AboutPage, HistoryPage, SetupPage
from .session import SessionScreen
from .storage import Store
from .widgets import CanvasButton, IconButton, NavItem


def resource_root() -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(getattr(sys, "_MEIPASS"))
    return Path(__file__).resolve().parents[1]


def asset(*parts: str) -> Path:
    return resource_root().joinpath("assets", *parts)


PAGES = {
    "practice": SetupPage,
    "history": HistoryPage,
    "about": AboutPage,
}


class Sidebar(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=T.SIDEBAR, width=232)
        self.app = app
        self.pack_propagate(False)
        self._items: dict[str, NavItem] = {}
        self._photos = []
        self._build()

    def _build(self):
        brand = tk.Frame(self, bg=T.SIDEBAR)
        brand.pack(fill="x", padx=20, pady=(26, 26))
        logo = tk.Frame(brand, bg=T.SIDEBAR)
        logo.pack(anchor="w")
        try:
            icon = Image.open(asset("ui", "icon.png")).resize((48, 48), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(icon)
            self._photos.append(photo)
            tk.Label(logo, image=photo, bg=T.SIDEBAR, bd=0).pack(side="left", padx=(0, 12))
        except (OSError, ValueError):
            c = tk.Canvas(logo, width=48, height=48, bg=T.ACCENT, highlightthickness=0)
            c.pack(side="left", padx=(0, 12))
            c.create_text(24, 24, text="Tp", fill=T.CREAM, font=T.font(20, "bold", T.SERIF))
        word = tk.Frame(logo, bg=T.SIDEBAR)
        word.pack(side="left")
        tk.Label(word, text="Tpose", bg=T.SIDEBAR, fg=T.SESSION_TEXT,
                 font=T.font(28, "bold", T.SERIF)).pack(anchor="w")
        tk.Label(brand, text=self.t("brand.studio"), bg=T.SIDEBAR, fg=T.SIDEBAR_MUTED,
                 font=T.font(7, "bold")).pack(anchor="w", pady=(8, 0), padx=(1, 0))

        tk.Frame(self, bg=T.SIDEBAR_LINE, height=1).pack(fill="x", padx=18, pady=(0, 18))
        nav = tk.Frame(self, bg=T.SIDEBAR)
        nav.pack(fill="x")
        entries = [
            ("practice", "nav.practice", "spark"),
            ("history", "nav.history", "clock"),
            ("about", "nav.about", "info"),
        ]
        for key, label, icon in entries:
            item = NavItem(nav, self.t(label), icon, lambda k=key: self.app.show_page(k))
            item.pack(fill="x", padx=10, pady=1)
            self._items[key] = item

        bottom = tk.Frame(self, bg=T.SIDEBAR)
        bottom.pack(side="bottom", fill="x", padx=20, pady=(0, 18))
        tk.Frame(bottom, bg=T.SIDEBAR_LINE, height=1).pack(fill="x", pady=(0, 12))
        tk.Label(bottom, text="IDIOMA · LANGUAGE", bg=T.SIDEBAR, fg=T.SIDEBAR_MUTED,
                 font=T.font(6, "bold"), anchor="w").pack(anchor="w", pady=(0, 6))
        langs = tk.Frame(bottom, bg=T.SIDEBAR)
        langs.pack(anchor="w")
        self._lang_buttons = {}
        # Two columns: Spanish/Japanese on the left, English/Chinese on the
        # right. Chinese sits directly under English and Japanese under Spanish.
        for codes in (("es", "ja"), ("en", "zh")):
            column = tk.Frame(langs, bg=T.SIDEBAR)
            column.pack(side="left", anchor="n", padx=(0, 5))
            for code in codes:
                b = CanvasButton(
                    column, self.t(f"lang.{code}"), lambda c=code: self.app.set_language(c),
                    variant="sidebar", width=50, height=25, radius=6, font_size=7,
                    selected=self.app.lang == code, padx=5,
                )
                b.pack(fill="x", pady=(0, 3))
                self._lang_buttons[code] = b
        tk.Label(bottom, text=self.t("brand.version", v=self.app.version), bg=T.SIDEBAR,
                 fg=T.SIDEBAR_MUTED, font=T.font(7), anchor="w").pack(anchor="w", pady=(14, 1))
        tk.Label(bottom, text=self.t("brand.footer"), bg=T.SIDEBAR, fg=T.SIDEBAR_MUTED,
                 font=T.font(7, italic=True), anchor="w").pack(anchor="w")

    def set_selected(self, page: str):
        for key, item in self._items.items():
            item.set_selected(key == page)

    def t(self, key: str, **kwargs) -> str:
        return tr(self.app.lang, key, **kwargs)


class TposeApp:
    version = "2.0.0"

    def __init__(self, root: tk.Tk):
        self.root = root
        self.store = Store()
        T.set_language_font(self.store.lang)
        self.art = Artwork()
        self.folder_cache: dict[str, list[Path]] = {}
        self.session: SessionScreen | None = None
        self.shell: tk.Frame | None = None
        self.page: tk.Frame | None = None
        self.sidebar: Sidebar | None = None
        self.page_host: tk.Frame | None = None
        self.page_name = "practice"
        self._shell_dirty = False
        self._toast_after = None
        self._toast_label = None
        self._configure_root()
        self.root.report_callback_exception = self._report_exception
        self._build_shell()
        self.show_page("practice")

    # ------------------------------------------------------------------ root
    def _configure_root(self):
        self.root.title(self.t("app.title"))
        self.root.configure(bg=T.CREAM)
        try:
            self.root.iconbitmap(default=str(asset("ui", "icon.ico")))
        except tk.TclError:
            pass
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        left, top, aw, ah = self._work_area(sw, sh)
        w = min(1440, max(1040, aw - 60))
        h = min(900, max(620, ah - 40))
        w = min(w, max(980, aw - 20))
        h = min(h, max(590, ah - 20))
        x = left + max(0, (aw - w) // 2)
        y = top + max(0, (ah - h) // 2)
        self.root.geometry(f"{w}x{h}+{x}+{y}")
        self.root.minsize(min(1120, aw - 20), min(620, ah - 20))
        self.root.option_add("*tearOff", False)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        try:
            self._dark_titlebar()
        except Exception:
            pass
        self.root.after(250, self.ensure_window_chrome)
        self.root.bind("<Map>", lambda e: self.root.after(120, self.ensure_window_chrome), add="+")

    def _work_area(self, sw: int, sh: int):
        if not sys.platform.startswith("win"):
            return 0, 0, sw, sh
        try:
            class RECT(ctypes.Structure):
                _fields_ = [
                    ("left", ctypes.c_long),
                    ("top", ctypes.c_long),
                    ("right", ctypes.c_long),
                    ("bottom", ctypes.c_long),
                ]
            rect = RECT()
            if ctypes.windll.user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(rect), 0):
                return rect.left, rect.top, rect.right - rect.left, rect.bottom - rect.top
        except Exception:
            pass
        return 0, 0, sw, sh

    def _dark_titlebar(self):
        if not sys.platform.startswith("win"):
            return
        self.root.update_idletasks()
        user32 = ctypes.windll.user32
        user32.GetParent.argtypes = [ctypes.c_void_p]
        user32.GetParent.restype = ctypes.c_void_p
        hwnd = user32.GetParent(self.root.winfo_id())
        value = ctypes.c_int(1)
        for attribute in (20, 19):
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, attribute, ctypes.byref(value), ctypes.sizeof(value)
            )

    def ensure_window_chrome(self):
        """Restore caption buttons if a fullscreen transition dropped them."""
        if not sys.platform.startswith("win"):
            return
        try:
            if bool(self.root.attributes("-fullscreen")):
                return
            if self.root.overrideredirect():
                self.root.overrideredirect(False)
            self.root.update_idletasks()
            user32 = ctypes.windll.user32
            user32.GetParent.argtypes = [ctypes.c_void_p]
            user32.GetParent.restype = ctypes.c_void_p
            user32.SetWindowPos.argtypes = [
                ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int, ctypes.c_int,
                ctypes.c_int, ctypes.c_int, ctypes.c_uint,
            ]
            hwnd = user32.GetParent(self.root.winfo_id())
            if not hwnd:
                return
            get_long = getattr(user32, "GetWindowLongPtrW", user32.GetWindowLongW)
            set_long = getattr(user32, "SetWindowLongPtrW", user32.SetWindowLongW)
            get_long.restype = ctypes.c_ssize_t
            set_long.restype = ctypes.c_ssize_t
            set_long.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_ssize_t]
            style = get_long(hwnd, -16)  # GWL_STYLE
            required = 0x00020000 | 0x00010000 | 0x00080000 | 0x00C00000 | 0x00040000
            if (style & required) == required:
                return
            style |= required
            set_long(hwnd, -16, style)
            user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0, 0x0027)  # NOMOVE|NOSIZE|NOZORDER|FRAMECHANGED
        except Exception:
            pass

    @property
    def lang(self) -> str:
        return self.store.lang

    def t(self, key: str, **kwargs) -> str:
        return tr(self.lang, key, **kwargs)

    # --------------------------------------------------------------- shell
    def _build_shell(self):
        if self.shell is not None and self.shell.winfo_exists():
            self.shell.destroy()
        self.shell = tk.Frame(self.root, bg=T.CREAM)
        self.shell.pack(fill="both", expand=True)
        self.sidebar = Sidebar(self.shell, self)
        self.sidebar.pack(side="left", fill="y")
        self.page_host = tk.Frame(self.shell, bg=T.CREAM)
        self.page_host.pack(side="left", fill="both", expand=True)
        self.page = None
        self.show_page(self.page_name)
        if self.session is not None:
            self.shell.pack_forget()

    def show_page(self, name: str):
        if name not in PAGES:
            name = "practice"
        self.page_name = name
        if self.page is not None and self.page.winfo_exists():
            self.page.destroy()
        try:
            self.page = PAGES[name](self.page_host, self)
        except Exception as exc:
            self._report_exception("page", exc, None)
            self.page = tk.Frame(self.page_host, bg=T.CREAM)
            tk.Label(
                self.page, text=f"No se pudo abrir esta página.\n{exc}", bg=T.CREAM, fg=T.RED,
                font=T.font(10), justify="left",
            ).pack(padx=30, pady=30)
        self.page.pack(fill="both", expand=True)
        if self.sidebar:
            self.sidebar.set_selected(name)
        self.root.title(self.t("app.title"))

    def set_language(self, lang: str):
        if lang not in LANGUAGES or lang == self.lang:
            return
        T.set_language_font(lang)
        self.store.set("lang", lang)
        self.root.title(self.t("app.title"))
        if self.session is not None:
            self.session.apply_locale()
            self._shell_dirty = True
        else:
            self._build_shell()

    def toggle_language(self):
        current = list(LANGUAGES).index(self.lang) if self.lang in LANGUAGES else 0
        self.set_language(LANGUAGES[(current + 1) % len(LANGUAGES)])

    # -------------------------------------------------------------- helpers
    def folder_files(self, path: str) -> list[Path]:
        if not path:
            return []
        try:
            key = str(Path(path).resolve()).lower()
        except OSError:
            key = str(path).lower()
        if key not in self.folder_cache:
            self.folder_cache[key] = scan_folder(path)
        return self.folder_cache[key]

    # -------------------------------------------------------------- sessions
    def start_session(self, config: dict):
        folders = config.get("folders") or []
        if not folders:
            MessageDialog(self.root, self.t("practice.empty_title"), self.t("practice.empty_body"),
                          self.t("common.ok"), icon="folder").show()
            return
        if config.get("mode") == "timed" and not config.get("plan"):
            MessageDialog(self.root, self.t("plan.empty"), self.t("plan.empty"),
                          self.t("common.ok"), icon="timer").show()
            return
        files = []
        for path in folders:
            files.extend(self.folder_files(path))
        if not files:
            MessageDialog(self.root, self.t("dialog.no_images_title"), self.t("dialog.no_images"),
                          self.t("common.ok"), icon="folder").show()
            return
        if self.session is not None:
            self.session.destroy()
            self.session = None
        if self.shell is not None:
            self.shell.pack_forget()
        self.session = SessionScreen(self.root, self, dict(config))
        self.session.pack(fill="both", expand=True)
        self.root.configure(cursor="")

    def leave_session(self, page: str = "practice"):
        if self.session is not None:
            try:
                self.session.destroy()
            except tk.TclError:
                pass
            self.session = None
        if self._shell_dirty or self.shell is None or not self.shell.winfo_exists():
            self._shell_dirty = False
            self._build_shell()
        else:
            self.shell.pack(fill="both", expand=True)
        self.show_page(page)
        try:
            self.root.attributes("-fullscreen", False)
        except tk.TclError:
            pass
        self.root.after(80, self.ensure_window_chrome)
        self.root.configure(cursor="")

    def record_session(self, entry: dict):
        self.store.add_history(entry)

    # ---------------------------------------------------------------- dialogs
    def toast(self, text: str):
        if self._toast_label is not None and self._toast_label.winfo_exists():
            self._toast_label.destroy()
        if self._toast_after:
            try:
                self.root.after_cancel(self._toast_after)
            except tk.TclError:
                pass
        label = tk.Label(self.root, text=text, bg=T.INK, fg=T.SESSION_TEXT, font=T.font(9, "bold"),
                         padx=15, pady=8)
        label.place(relx=0.5, rely=1.0, y=-26, anchor="s")
        label.lift()
        self._toast_label = label
        self._toast_after = self.root.after(2400, self._hide_toast)

    def _hide_toast(self):
        if self._toast_label is not None and self._toast_label.winfo_exists():
            self._toast_label.destroy()
        self._toast_label = None

    def open_data_folder(self):
        try:
            if sys.platform.startswith("win"):
                os.startfile(self.store.dir)  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(self.store.dir)])
            else:
                subprocess.Popen(["xdg-open", str(self.store.dir)])
        except Exception:
            MessageDialog(self.page or self.root, self.t("dialog.error"),
                          self.t("dialog.open_folder_error"), self.t("common.ok"), icon="folder").show()

    def _report_exception(self, exc_type, exc_value, exc_tb):
        try:
            from .storage import data_dir
            import traceback
            with (data_dir() / "error.log").open("a", encoding="utf-8") as fh:
                traceback.print_exception(exc_type, exc_value, exc_tb, file=fh)
        except Exception:
            pass
        try:
            self.toast(self.t("dialog.unexpected"))
        except tk.TclError:
            pass

    # ----------------------------------------------------------------- close
    def _on_close(self):
        if self.session is not None and not getattr(self.session, "finished", False):
            ok = ConfirmDialog(self.root, self.t("session.close_title"), self.t("session.close_body"),
                               self.t("session.close_yes"), self.t("session.close_no"),
                               danger=False, icon="info").show()
            if not ok:
                return
            try:
                self.session.save_abandoned()
            except Exception:
                pass
        if self.session is not None:
            try:
                self.session.destroy()
            except Exception:
                pass
            self.session = None
        self.store.save()
        self.root.destroy()


def enable_windows_dpi():
    if not sys.platform.startswith("win"):
        return
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass
