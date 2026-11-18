#!/usr/bin/env python3
"""Tpose — a portable gesture-drawing studio for your own references.

Run with:  python tpose.py
The Windows executable is the double-click entry point for most people.
"""

from __future__ import annotations

import argparse
import copy
import shutil
import sys
import tempfile
import tkinter as tk
import traceback
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Tpose — gesture drawing studio")
    parser.add_argument("--self-test", action="store_true", help="smoke-test the app and exit")
    parser.add_argument("--page", default=None, choices=["practice", "history", "about"])
    parser.add_argument("--lang", default=None, choices=["es", "en"])
    args = parser.parse_args()

    from app.application import TposeApp, enable_windows_dpi

    enable_windows_dpi()
    root = tk.Tk()
    if args.self_test:
        root.withdraw()
    try:
        app = TposeApp(root)
        if args.lang:
            app.set_language(args.lang)
        if args.page:
            app.show_page(args.page)
        if args.self_test:
            return run_self_test(root, app)
        root.mainloop()
        return 0
    except Exception:
        traceback.print_exc()
        try:
            root.destroy()
        except tk.TclError:
            pass
        return 1


def run_self_test(root: tk.Tk, app) -> int:
    from PIL import Image
    from app import exports

    original = copy.deepcopy(app.store.data)
    temp = Path(tempfile.mkdtemp(prefix="tpose_test_"))
    try:
        for i in range(3):
            Image.new("RGB", (640, 480), (210 - i * 25, 150 + i * 20, 120)).save(temp / f"pose-{i}.jpg")
        app.store.data.update({
            "lang": "es", "mode": "timed",
            "folders": [{"path": str(temp), "name": "Test", "enabled": True}],
            "plan": [{"count": 2, "duration": 30}, {"count": 1, "duration": 60}],
            "relaxed_count": 3, "rotation": 0, "grayscale": False, "sound": False,
        })
        app.folder_cache.clear()
        for page in ("practice", "history", "about"):
            app.show_page(page)
            root.update_idletasks()
            root.update()
        app.set_language("en")
        root.update_idletasks()
        root.update()
        app.set_language("es")
        app.show_page("practice")
        root.update()
        page = app.page
        assert page is not None
        assert len(page.store.folders) == 1
        app.start_session({
            "mode": "timed", "folders": [str(temp)],
            "plan": [{"count": 2, "duration": 30}, {"count": 1, "duration": 60}],
            "shuffle": True, "grayscale": False, "rotation": 0,
            "show_timer": True, "sound": False,
        })
        root.update_idletasks()
        root.update()
        assert app.session is not None
        app.session._finish(True)
        root.update_idletasks()
        root.update()
        assert app.session.summary_visible
        png = temp / "stats.png"
        xlsx = temp / "stats.xlsx"
        exports.export_png(png, app.store.history, "es")
        exports.export_xlsx(xlsx, app.store.history, "es")
        assert png.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
        import zipfile
        with zipfile.ZipFile(xlsx) as z:
            assert "xl/workbook.xml" in z.namelist()
        app.leave_session("history")
        root.update_idletasks()
        root.update()
        print("SELF-TEST OK: pages, folders, plan, session, summary, PNG and XLSX")
        return 0
    except Exception:
        traceback.print_exc()
        return 1
    finally:
        try:
            app.store.data = original
            app.store.save()
        except Exception:
            pass
        try:
            root.destroy()
        except tk.TclError:
            pass
        shutil.rmtree(temp, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
