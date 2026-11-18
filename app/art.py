"""Fast photo composition for Tpose."""

from __future__ import annotations

from collections import OrderedDict
from pathlib import Path

from PIL import Image, ImageFilter, ImageOps


def _gradient(size: tuple[int, int], stops: list[tuple[float, tuple[int, int, int]]]) -> Image.Image:
    w, h = size
    strip = Image.new("RGB", (1, max(2, h)))
    px = strip.load()
    for y in range(h):
        t = y / max(1, h - 1)
        left, right = stops[0], stops[-1]
        for i in range(len(stops) - 1):
            a, b = stops[i], stops[i + 1]
            if a[0] <= t <= b[0]:
                left, right = a, b
                break
        span = max(1e-6, right[0] - left[0])
        k = max(0.0, min(1.0, (t - left[0]) / span))
        px[0, y] = tuple(int(round(left[1][j] + (right[1][j] - left[1][j]) * k)) for j in range(3))
    return strip.resize((w, h))


def _radial(size: tuple[int, int], strength: int) -> Image.Image:
    w, h = size
    g = Image.radial_gradient("L").resize((w, h), Image.Resampling.BILINEAR)
    return ImageOps.invert(g).point(lambda x: int((x / 255) ** 1.65 * strength))


def _photo_background(size: tuple[int, int]) -> Image.Image:
    w, h = size
    bg = _gradient(size, [(0.0, (28, 24, 21)), (0.55, (16, 14, 12)), (1.0, (8, 7, 6))])
    glow = _radial(size, 48).point(lambda x: int(x * 0.45))
    bg = Image.composite(Image.new("RGB", size, (84, 58, 42)), bg, glow)
    edge = _radial(size, 255).point(lambda x: int(max(0, x - 190) / 65 * 50))
    vign = Image.new("RGBA", size, (4, 3, 2, 0))
    vign.putalpha(edge)
    bg = Image.alpha_composite(bg.convert("RGBA"), vign).convert("RGB")
    grain = Image.effect_noise((max(1, w // 4), max(1, h // 4)), 8).convert("L").resize(size)
    grain = grain.point(lambda x: int(max(0, x - 128) * 0.07))
    return Image.alpha_composite(
        bg.convert("RGBA"),
        Image.merge("RGBA", (*Image.new("RGB", size, (30, 22, 16)).split(), grain)),
    ).convert("RGB")


class Artwork:
    def __init__(self) -> None:
        self._backgrounds: OrderedDict[tuple[int, int], Image.Image] = OrderedDict()
        self._covers: OrderedDict[tuple, Image.Image] = OrderedDict()
        # Decoding a phone photo once is the main speed win for next/previous.
        self._sources: OrderedDict[str, Image.Image] = OrderedDict()
        self._base_bg: Image.Image | None = None

    def _source(self, path: str | Path) -> Image.Image:
        key = str(path)
        if key in self._sources:
            self._sources.move_to_end(key)
            return self._sources[key]
        with Image.open(path) as im:
            im = ImageOps.exif_transpose(im)
            if getattr(im, "is_animated", False):
                im.seek(0)
            im = im.convert("RGBA") if im.mode in ("RGBA", "LA", "P") else im.convert("RGB")
            im.thumbnail((2200, 2200), Image.Resampling.LANCZOS)
            im = im.copy()
        self._sources[key] = im
        if len(self._sources) > 12:
            self._sources.popitem(last=False)
        return im

    def preload(self, path: str | Path) -> None:
        try:
            self._source(path)
        except (OSError, ValueError):
            pass

    def _transformed(self, path: str | Path, rotation: int = 0,
                     flip_h: bool = False, flip_v: bool = False) -> Image.Image:
        im = self._source(path)
        if rotation % 360:
            im = im.rotate(-(rotation % 360), expand=True)
        if flip_h:
            im = ImageOps.mirror(im)
        if flip_v:
            im = ImageOps.flip(im)
        return im

    def background(self, size: tuple[int, int]) -> Image.Image:
        key = (max(2, int(size[0])), max(2, int(size[1])))
        if key in self._backgrounds:
            self._backgrounds.move_to_end(key)
            return self._backgrounds[key]
        if self._base_bg is None:
            self._base_bg = _photo_background((1600, 1000))
        # Resizing a fixed studio plate is far cheaper than rebuilding the
        # gradient, glow, vignette and grain for every resize event.
        bg = ImageOps.fit(self._base_bg, key, Image.Resampling.LANCZOS, centering=(0.5, 0.5))
        self._backgrounds[key] = bg
        if len(self._backgrounds) > 16:
            self._backgrounds.popitem(last=False)
        return bg

    def image_aspect(self, path: str | Path, rotation: int = 0) -> float:
        try:
            im = self._source(path)
            w, h = im.size
        except (OSError, ValueError):
            return 4 / 3
        if rotation % 180 == 90:
            w, h = h, w
        return (w / h) if w and h else 4 / 3

    def photo(
        self,
        path: str | Path,
        size: tuple[int, int],
        grayscale: bool = False,
        rotation: int = 0,
        flip_h: bool = False,
        flip_v: bool = False,
    ) -> Image.Image | None:
        try:
            im = self._transformed(path, rotation, flip_h, flip_v)
        except (OSError, ValueError):
            return None
        w, h = max(2, int(size[0])), max(2, int(size[1]))
        canvas = self.background((w, h)).convert("RGBA")
        im = ImageOps.contain(im, (int(w * 0.965), int(h * 0.965)), Image.Resampling.LANCZOS)
        if im.mode != "RGBA":
            im = im.convert("RGBA")
        canvas.alpha_composite(im, ((w - im.width) // 2, (h - im.height) // 2))
        out = canvas.convert("RGB")
        if grayscale:
            out = ImageOps.grayscale(out).convert("RGB")
        return out

    def cover(self, path: str | Path, size: tuple[int, int], rotation: int = 0,
              flip_h: bool = False, flip_v: bool = False) -> Image.Image | None:
        key = (str(path), size[0], size[1], rotation, flip_h, flip_v)
        if key in self._covers:
            return self._covers[key]
        try:
            im = self._transformed(path, rotation, flip_h, flip_v).convert("RGB")
        except (OSError, ValueError):
            return None
        out = ImageOps.fit(im, size, Image.Resampling.LANCZOS, centering=(0.5, 0.4))
        self._covers[key] = out
        if len(self._covers) > 12:
            self._covers.popitem(last=False)
        return out

    def backdrop(self, image: Image.Image, size: tuple[int, int], dim: float = 0.22) -> Image.Image:
        w, h = max(2, int(size[0])), max(2, int(size[1]))
        # Blur and compose at a small size, then upscale. This is many times
        # faster than a full-resolution Gaussian blur on every image change.
        sw, sh = max(80, w // 7), max(60, h // 7)
        small = ImageOps.fit(image, (sw, sh), Image.Resampling.BILINEAR, centering=(0.5, 0.45))
        small = small.filter(ImageFilter.GaussianBlur(max(3, min(sw, sh) // 22)))
        bg = small.resize((w, h), Image.Resampling.BILINEAR)
        overlay = Image.new("RGBA", (w, h), (10, 9, 8, int(255 * (1.0 - dim))))
        return Image.alpha_composite(bg.convert("RGBA"), overlay).convert("RGB")
