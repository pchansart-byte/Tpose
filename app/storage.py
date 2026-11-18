"""Portable settings and session history for Tpose."""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from .i18n import LANGUAGES


DEFAULT_PLAN = [
    {"count": 10, "duration": 30},
    {"count": 5, "duration": 120},
]

DEFAULT_CONFIG: dict[str, Any] = {
    "version": 2,
    "lang": "es",
    "theme": "day",
    "mode": "timed",
    "folders": [],
    "plan": DEFAULT_PLAN,
    "relaxed_count": 20,
    "shuffle": True,
    "grayscale": False,
    "rotation": 0,
    "warning_seconds": 10,
    "interval_sound": False,
    "show_timer": True,
    "sound": True,
    "session_seq": 0,
    "image_usage": {},
    "history": [],
}


def app_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[1]


def data_dir() -> Path:
    local = app_base_dir() / "datos"
    try:
        local.mkdir(parents=True, exist_ok=True)
        probe = local / ".write-test"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        return local
    except OSError:
        fallback = Path(os.environ.get("APPDATA", str(Path.home()))) / "Tpose"
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback


class Store:
    def __init__(self) -> None:
        self.dir = data_dir()
        self.path = self.dir / "config.json"
        self.data: dict[str, Any] = json.loads(json.dumps(DEFAULT_CONFIG))
        self.load()

    # ------------------------------------------------------------------ disk
    def load(self) -> None:
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError):
            return
        if not isinstance(raw, dict):
            return
        migrated = self._migrate(raw)
        for key, default in DEFAULT_CONFIG.items():
            value = migrated.get(key, default)
            if key in ("history", "folders", "plan"):
                self.data[key] = value if isinstance(value, list) else default
            elif key == "image_usage":
                self.data[key] = value if isinstance(value, dict) else {}
            elif isinstance(default, bool):
                self.data[key] = bool(value)
            elif isinstance(default, int):
                try:
                    self.data[key] = int(value)
                except (ValueError, TypeError):
                    self.data[key] = default
            else:
                self.data[key] = value if isinstance(value, str) else default
        self._validate()

    def _migrate(self, raw: dict) -> dict:
        data = dict(raw)
        # Tpose 2.0 replaced the single duration/count with a block plan.
        if "plan" not in data or not isinstance(data.get("plan"), list):
            old_count = data.get("count", 20)
            old_duration = data.get("duration", 60)
            try:
                data["plan"] = [{"count": int(old_count), "duration": int(old_duration)}]
            except (ValueError, TypeError):
                data["plan"] = json.loads(json.dumps(DEFAULT_PLAN))
        folders = []
        for f in data.get("folders", []):
            if isinstance(f, dict) and isinstance(f.get("path"), str):
                item = {"path": f["path"], "name": f.get("name") or Path(f["path"]).name}
                item["enabled"] = bool(f.get("enabled", True))
                folders.append(item)
        data["folders"] = folders
        data.pop("source", None)
        data.pop("duration", None)
        data.pop("count", None)
        data.pop("upside_down", None)
        data["version"] = 2
        return data

    def _validate(self) -> None:
        if self.data["lang"] not in LANGUAGES:
            self.data["lang"] = "es"
        if self.data.get("theme") not in ("day", "night"):
            self.data["theme"] = "day"
        if self.data["mode"] not in ("timed", "relaxed"):
            self.data["mode"] = "timed"
        if self.data["rotation"] not in (0, 90, 180, 270):
            self.data["rotation"] = 0
        try:
            warning = int(self.data["warning_seconds"])
        except (ValueError, TypeError):
            warning = 10
        self.data["warning_seconds"] = min(30, max(5, (warning // 5) * 5))
        self.data["relaxed_count"] = max(1, min(500, int(self.data["relaxed_count"])))
        try:
            self.data["session_seq"] = max(0, int(self.data["session_seq"]))
        except (ValueError, TypeError):
            self.data["session_seq"] = 0
        if not isinstance(self.data.get("image_usage"), dict):
            self.data["image_usage"] = {}
        clean_usage = {}
        for key, value in self.data["image_usage"].items():
            try:
                clean_usage[str(key)] = int(value)
            except (ValueError, TypeError):
                continue
        if len(clean_usage) > 20000:
            clean_usage = dict(sorted(clean_usage.items(), key=lambda item: item[1], reverse=True)[:15000])
        self.data["image_usage"] = clean_usage
        folders = []
        seen = set()
        for f in self.data.get("folders", []):
            if not (isinstance(f, dict) and isinstance(f.get("path"), str)):
                continue
            key = str(Path(f["path"]).resolve()).lower()
            if key in seen:
                continue
            seen.add(key)
            folders.append({
                "path": f["path"],
                "name": f.get("name") or Path(f["path"]).name,
                "enabled": bool(f.get("enabled", True)),
            })
        self.data["folders"] = folders
        plan = []
        for block in self.data.get("plan", []):
            if not isinstance(block, dict):
                continue
            try:
                count = int(block.get("count", 1))
                duration = int(block.get("duration", 30))
            except (ValueError, TypeError):
                continue
            count = max(1, min(500, count))
            duration = max(5, min(3600, duration))
            plan.append({"count": count, "duration": duration})
        self.data["plan"] = plan
        if not isinstance(self.data.get("history"), list):
            self.data["history"] = []

    def save(self) -> None:
        try:
            self.dir.mkdir(parents=True, exist_ok=True)
            tmp = self.path.with_suffix(".tmp")
            tmp.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")
            tmp.replace(self.path)
        except OSError:
            pass

    # --------------------------------------------------------------- settings
    def get(self, key: str, default=None):
        return self.data.get(key, default)

    def set(self, key: str, value, save: bool = True) -> None:
        self.data[key] = value
        if save:
            self.save()

    @property
    def lang(self) -> str:
        return self.data.get("lang", "es")

    @property
    def folders(self) -> list[dict[str, Any]]:
        return self.data.setdefault("folders", [])

    @property
    def plan(self) -> list[dict[str, int]]:
        return self.data.setdefault("plan", [])

    def add_folder(self, path: str) -> bool:
        path = str(Path(path).resolve())
        key = path.lower()
        for folder in self.folders:
            if str(Path(folder["path"]).resolve()).lower() == key:
                return False
        self.folders.append({"path": path, "name": Path(path).name or path, "enabled": True})
        self.save()
        return True

    def remove_folder(self, path: str) -> None:
        target = str(Path(path).resolve()).lower()
        self.data["folders"] = [
            f for f in self.folders if str(Path(f["path"]).resolve()).lower() != target
        ]
        self.save()

    def set_folder_enabled(self, path: str, enabled: bool) -> None:
        target = str(Path(path).resolve()).lower()
        for folder in self.folders:
            if str(Path(folder["path"]).resolve()).lower() == target:
                folder["enabled"] = bool(enabled)
                break
        self.save()

    def selected_folder_paths(self) -> list[str]:
        return [
            f["path"] for f in self.folders
            if f.get("enabled", True) and Path(f["path"]).is_dir()
        ]

    def set_plan(self, plan: list[dict[str, int]]) -> None:
        self.data["plan"] = plan
        self._validate()
        self.save()

    # ---------------------------------------------------------------- history
    @property
    def history(self) -> list[dict[str, Any]]:
        return self.data.setdefault("history", [])

    # ----------------------------------------------------------- image memory
    def begin_image_session(self) -> int:
        self.data["session_seq"] = int(self.data.get("session_seq", 0)) + 1
        self.save()
        return self.data["session_seq"]

    @staticmethod
    def image_key(path: str | Path) -> str:
        try:
            return str(Path(path).resolve())
        except OSError:
            return str(path)

    def mark_image_used(self, path: str | Path, session_id: int) -> None:
        self.data.setdefault("image_usage", {})[self.image_key(path)] = int(session_id)
        # Individual image writes are tiny and make the 3-session rule survive
        # an unexpected close or a crash mid-session.
        self.save()

    def add_history(self, entry: dict[str, Any]) -> dict[str, Any]:
        item = dict(entry)
        item.setdefault("date", datetime.now().astimezone().isoformat(timespec="seconds"))
        self.history.insert(0, item)
        self.data["history"] = self.history[:300]
        self.save()
        return item

    def clear_history(self) -> None:
        self.data["history"] = []
        self.save()
