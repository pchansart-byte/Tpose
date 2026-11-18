"""Local image folders and session sequencing for Tpose."""

from __future__ import annotations

import os
import random
import re
from dataclasses import dataclass
from pathlib import Path

SUPPORTED_IMAGES = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".tif", ".tiff"}


def natural_key(text: str):
    return [int(p) if p.isdigit() else p.casefold() for p in re.split(r"(\d+)", text)]


def scan_folder(path: str | os.PathLike) -> list[Path]:
    root = Path(path)
    if not root.is_dir():
        return []
    files: list[Path] = []
    try:
        for base, dirs, names in os.walk(root):
            dirs[:] = sorted(
                [d for d in dirs if not d.startswith(".") and d not in ("__pycache__", "node_modules")],
                key=str.casefold,
            )
            for name in names:
                if name.startswith("."):
                    continue
                if Path(name).suffix.lower() in SUPPORTED_IMAGES:
                    files.append(Path(base) / name)
    except OSError:
        return []
    files.sort(key=lambda p: natural_key(str(p.relative_to(root))))
    return files


def folder_images(folders: list[dict]) -> list[Path]:
    """Union of all enabled, existing folders, de-duplicated and ordered."""
    seen: set[str] = set()
    out: list[Path] = []
    for folder in folders:
        path = folder.get("path")
        if not path or not folder.get("enabled", True):
            continue
        for image in scan_folder(path):
            try:
                key = str(image.resolve()).lower()
            except OSError:
                key = str(image).lower()
            if key not in seen:
                seen.add(key)
                out.append(image)
    return out


@dataclass(frozen=True)
class Reference:
    path: Path

    @property
    def key(self) -> str:
        return str(self.path)


def expand_plan(plan: list[dict]) -> list[int]:
    durations: list[int] = []
    for block in plan:
        try:
            count = max(1, min(500, int(block.get("count", 1))))
            raw_duration = int(block.get("duration", 30))
            duration = 0 if raw_duration <= 0 else max(5, min(3600, raw_duration))
        except (ValueError, TypeError):
            continue
        durations.extend([duration] * count)
    return durations


def _image_key(path: Path) -> str:
    try:
        return str(path.resolve())
    except OSError:
        return str(path)


def make_sequence(
    folders: list[dict],
    plan: list[dict],
    shuffle: bool = True,
    rng: random.Random | None = None,
    usage: dict | None = None,
    session_id: int = 0,
    avoid_sessions: int = 3,
) -> tuple[list[Reference], list[int]]:
    """Return references and the per-image duration plan.

    Images seen in any of the previous ``avoid_sessions`` sessions are kept at
    the back of the queue.  They are only reused when the plan asks for more
    images than the available pool can provide.  Selecting several folders
    always randomises the pool.
    """
    rng = rng or random.Random()
    files = folder_images(folders)
    durations = expand_plan(plan)
    if not files or not durations:
        return [], []
    usage = usage or {}
    enabled_folders = sum(
        1 for f in folders
        if f.get("enabled", True) and Path(str(f.get("path", ""))).is_dir()
    )
    do_shuffle = shuffle or enabled_folders > 1
    cutoff = int(session_id) - max(0, int(avoid_sessions))
    eligible = []
    fallback = []
    for path in files:
        last = int(usage.get(_image_key(path), -10**9))
        if last < cutoff:
            eligible.append(path)
        else:
            fallback.append(path)
    if do_shuffle:
        rng.shuffle(eligible)
    fallback.sort(key=lambda p: int(usage.get(_image_key(p), -10**9)))
    pool = eligible + fallback
    if not pool:
        return [], []
    chosen: list[Path] = []
    need = len(durations)
    while len(chosen) < need:
        if not chosen:
            chosen.extend(pool)
        else:
            # If the plan is larger than the whole library, recycle it in a
            # fresh random order rather than freezing the session.
            batch = list(pool)
            if do_shuffle:
                rng.shuffle(batch)
            chosen.extend(batch)
    refs = [Reference(p) for p in chosen[:need]]
    return refs, durations


def plan_label(plan: list[dict], lang: str = "es") -> str:
    from . import theme as T

    if not plan:
        return "—"
    parts = []
    for block in plan[:4]:
        count = int(block.get("count", 0))
        duration = int(block.get("duration", 0))
        parts.append(f"{count}×{T.fmt_chip_duration(duration, lang)}")
    if len(plan) > 4:
        parts.append("…")
    return " · ".join(parts)


def plan_total(plan: list[dict]) -> tuple[int, int]:
    poses = 0
    seconds = 0
    for block in plan:
        try:
            count = int(block.get("count", 0))
            duration = int(block.get("duration", 0))
        except (ValueError, TypeError):
            continue
        poses += count
        seconds += count * duration
    return poses, seconds
