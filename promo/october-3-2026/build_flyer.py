#!/usr/bin/env python3
"""Compose the October 3, 2026 Freestyle Grapplerz Instagram Story flyer.

The two-grappler artwork is extracted from official Freestyle Grapplerz
event art and treated as a locked graphic: uniform scale/position/tonal
adjustments only — no redrawing, no pose changes, no anatomy edits.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
FONTS = ROOT / "fonts"
W, H = 1080, 1920

# Palette — premium combat sports
BLACK = (8, 8, 9, 255)
CHARCOAL = (18, 18, 20, 255)
INK = (28, 28, 31, 255)
GRAPHITE = (58, 60, 64, 255)
OFFWHITE = (236, 232, 224, 255)
SILVER = (196, 196, 198, 255)
GOLD = (184, 154, 98, 255)
GOLD_DIM = (138, 114, 70, 255)
GOLD_DEEP = (98, 80, 48, 255)
MUTED = (118, 116, 112, 255)

# Instagram Reel chrome
SAFE_TOP = 170
SAFE_BOTTOM = 1680
SAFE_LEFT = 72
SAFE_RIGHT = 1008


def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONTS / name), size)


def text_size(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.FreeTypeFont) -> tuple[int, int]:
    bbox = draw.textbbox((0, 0), text, font=fnt)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def draw_tracked(
    draw: ImageDraw.ImageDraw,
    text: str,
    y: int,
    fnt: ImageFont.FreeTypeFont,
    fill,
    tracking: int = 0,
    center_x: int = W // 2,
    x: int | None = None,
) -> tuple[int, int, int, int]:
    """Draw text with letter-spacing. Returns bounding box."""
    widths = []
    for ch in text:
        widths.append(text_size(draw, ch, fnt)[0])
    total = sum(widths) + tracking * max(len(text) - 1, 0)
    if x is None:
        cx = center_x - total // 2
    else:
        cx = x
    h = text_size(draw, text.replace(" ", "A"), fnt)[1]
    cursor = cx
    for ch, tw in zip(text, widths):
        draw.text((cursor, y), ch, font=fnt, fill=fill)
        cursor += tw + tracking
    return cx, y, cx + total, y + h


def rounded_rect(draw, box, radius, fill=None, outline=None, width=1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def _flood_from_edges(mask: np.ndarray) -> np.ndarray:
    """Return True for pixels connected to the image border (background)."""
    h, w = mask.shape
    bg = np.zeros((h, w), dtype=bool)
    stack = []
    for x in range(w):
        if mask[0, x]:
            stack.append((0, x))
        if mask[h - 1, x]:
            stack.append((h - 1, x))
    for y in range(h):
        if mask[y, 0]:
            stack.append((y, 0))
        if mask[y, w - 1]:
            stack.append((y, w - 1))
    seen = np.zeros((h, w), dtype=bool)
    while stack:
        y, x = stack.pop()
        if seen[y, x]:
            continue
        seen[y, x] = True
        if not mask[y, x]:
            continue
        bg[y, x] = True
        if y > 0:
            stack.append((y - 1, x))
        if y < h - 1:
            stack.append((y + 1, x))
        if x > 0:
            stack.append((y, x - 1))
        if x < w - 1:
            stack.append((y, x + 1))
    return bg


def extract_official_crest() -> Image.Image:
    """Isolate the official two-grappler crest from the Chapter 5 banner.

    Only compositing: the original crest pixels are copied, never redrawn.
    """
    src = Image.open(ASSETS / "source-banner-ch5.png").convert("RGBA")
    # Left crest only — the right instance is interrupted by the venue bar.
    region = src.crop((0, 8, 248, 312))
    arr = np.array(region).astype(np.int16)
    r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
    lum = 0.2126 * r + 0.7152 * g + 0.0722 * b

    gold = (r > 95) & (g > 55) & (r > b + 18) & (r > g - 8)
    white_fg = (lum > 190) & (np.abs(r - g) < 28) & (np.abs(g - b) < 28)
    metal = gold | white_fg

    # Expand the metal silhouette so muscle recesses stay inside the lockup.
    metal_img = Image.fromarray(metal.astype(np.uint8) * 255, "L")
    metal_img = metal_img.filter(ImageFilter.MaxFilter(9))
    metal_img = metal_img.filter(ImageFilter.MinFilter(3))
    dilated = np.array(metal_img) > 40

    is_sky = (b > 125) & (b > r + 12) & (g > 95)
    is_cloud = (lum > 175) & (b > r - 8) & (g > r - 8) & ~gold
    is_water = (g > 70) & (b > 80) & (r < 150) & (g > r - 5) & (b > r) & ~gold
    background = is_sky | is_cloud | is_water | ~dilated

    keep = dilated & ~background
    # Drop any leftover photo pixels still attached to the border.
    drop = _flood_from_edges(~keep)
    keep = keep & ~drop

    keep_img = Image.fromarray(keep.astype(np.uint8) * 255, "L")
    keep_img = keep_img.filter(ImageFilter.MaxFilter(3))
    keep_img = keep_img.filter(ImageFilter.GaussianBlur(0.8))
    alpha = np.array(keep_img)

    ys, xs = np.where(alpha > 20)
    if len(xs) == 0:
        raise RuntimeError("Could not isolate the official grappler crest")
    pad = 4
    x0, x1 = max(0, int(xs.min()) - pad), min(region.width, int(xs.max()) + pad + 1)
    y0, y1 = max(0, int(ys.min()) - pad), min(region.height, int(ys.max()) + pad + 1)

    crop = region.crop((x0, y0, x1, y1))
    crop_a = Image.fromarray(alpha[y0:y1, x0:x1], "L")
    out = Image.new("RGBA", crop.size, (0, 0, 0, 0))
    out.paste(crop, (0, 0))
    out.putalpha(crop_a)

    # Knock out leftover sky/cloud pixels that survived the metal dilate.
    px = np.array(out)
    pr, pg, pb, pa = px[:, :, 0], px[:, :, 1], px[:, :, 2], px[:, :, 3]
    leftover_sky = (pa > 0) & (pb > 145) & (pg > 140) & (pb >= pr) & (pr < 220)
    leftover_cloud = (
        (pa > 0)
        & (pr > 170)
        & (pg > 185)
        & (pb > 185)
        & (np.abs(pg.astype(int) - pb.astype(int)) < 22)
    )
    px[leftover_sky | leftover_cloud, 3] = 0
    out = Image.fromarray(px, "RGBA")
    bbox = out.getbbox()
    return out.crop(bbox) if bbox else out


def to_graphite_grapplers(crest: Image.Image) -> Image.Image:
    """Tonal remap of the locked crest into a dark graphite relief.

    Anatomy and silhouette are unchanged. Gold figures become charcoal /
    gunmetal; the FG monogram stays a muted metallic gold.
    """
    arr = np.array(crest).astype(np.float32)
    r, g, b, a = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2], arr[:, :, 3]
    lum = 0.2126 * r + 0.7152 * g + 0.0722 * b

    metal = (a > 18) & ((r > b + 12) | (lum > 70))
    letters = (a > 18) & (lum > 188) & (np.abs(r - g) < 30)

    t = np.clip(lum / 255.0, 0, 1)
    t = np.power(t, 1.25)
    # Highlights cap well below the off-white headline.
    graphite_r = 10 + t * 96
    graphite_g = 11 + t * 100
    graphite_b = 13 + t * 106

    nr = np.where(metal, graphite_r, r)
    ng = np.where(metal, graphite_g, g)
    nb = np.where(metal, graphite_b, b)

    nr[letters] = 176
    ng[letters] = 146
    nb[letters] = 92

    out = np.stack([nr, ng, nb, a], axis=-1).clip(0, 255).astype(np.uint8)
    img = Image.fromarray(out, "RGBA")
    img = ImageEnhance.Contrast(img).enhance(1.20)
    img = ImageEnhance.Brightness(img).enhance(0.80)
    # Re-apply muted gold to the FG letters after tonal adjustments.
    px = np.array(img)
    px[letters, 0] = 176
    px[letters, 1] = 146
    px[letters, 2] = 92
    return Image.fromarray(px, "RGBA")


def isolate_grapplers(graphite: Image.Image) -> Image.Image:
    """Keep the full two-athlete lockup, including both heads and both bodies."""
    bbox = graphite.getbbox()
    return graphite.crop(bbox) if bbox else graphite


def make_texture(size: tuple[int, int]) -> Image.Image:
    w, h = size
    rng = np.random.default_rng(3)
    noise = rng.integers(0, 255, (h, w), dtype=np.uint8)
    tex = Image.fromarray(noise, "L").convert("RGBA")
    # Fine grain only.
    arr = np.array(tex)
    arr[:, :, 3] = 14
    return Image.fromarray(arr, "RGBA")


def draw_vignette(base: Image.Image) -> None:
    cx, cy = W / 2, H * 0.38
    max_r = math.hypot(W, H) * 0.62
    yy, xx = np.mgrid[0:H, 0:W]
    dist = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / max_r
    alpha = np.clip((dist - 0.35) * 210, 0, 150).astype(np.uint8)
    vig = np.zeros((H, W, 4), dtype=np.uint8)
    vig[:, :, 3] = alpha
    base.alpha_composite(Image.fromarray(vig, "RGBA"))


def florida_path():
    data = json.loads((ASSETS / "florida.geojson").read_text())
    coords = data["features"][0]["geometry"]["coordinates"][0]
    return coords


def draw_florida(draw: ImageDraw.ImageDraw, box, fill=None, outline=GOLD_DEEP, width=2, mark_clearwater=True):
    coords = florida_path()
    lons = [p[0] for p in coords]
    lats = [p[1] for p in coords]
    minx, maxx, miny, maxy = min(lons), max(lons), min(lats), max(lats)
    x0, y0, x1, y1 = box
    bw, bh = x1 - x0, y1 - y0
    sx = bw / (maxx - minx)
    sy = bh / (maxy - miny)
    s = min(sx, sy)
    # Center in box
    ox = x0 + (bw - (maxx - minx) * s) / 2
    oy = y1  # lat grows upward

    def proj(lon, lat):
        return (ox + (lon - minx) * s, oy - (lat - miny) * s)

    pts = [proj(lon, lat) for lon, lat in coords]
    if fill:
        draw.polygon(pts, fill=fill)
    draw.line(pts + [pts[0]], fill=outline, width=width, joint="curve")

    if mark_clearwater:
        # Clearwater / Tampa Bay ~ 27.97 N, 82.80 W
        cx, cy = proj(-82.80, 27.965)
        r = 5
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=GOLD)
        draw.ellipse([cx - r * 2.4, cy - r * 2.4, cx + r * 2.4, cy + r * 2.4], outline=GOLD, width=1)


def corner_brackets(draw: ImageDraw.ImageDraw, box, length=42, color=GOLD_DIM, width=2):
    x0, y0, x1, y1 = box
    # TL
    draw.line([(x0, y0 + length), (x0, y0), (x0 + length, y0)], fill=color, width=width)
    # TR
    draw.line([(x1 - length, y0), (x1, y0), (x1, y0 + length)], fill=color, width=width)
    # BL
    draw.line([(x0, y1 - length), (x0, y1), (x0 + length, y1)], fill=color, width=width)
    # BR
    draw.line([(x1 - length, y1), (x1, y1), (x1, y1 - length)], fill=color, width=width)


def hairline(draw, y, x0=SAFE_LEFT + 40, x1=SAFE_RIGHT - 40, color=GOLD_DEEP):
    draw.line([(x0, y), (x1, y)], fill=color, width=1)
    # center diamond tick
    mid = (x0 + x1) // 2
    draw.polygon([(mid - 5, y), (mid, y - 5), (mid + 5, y), (mid, y + 5)], fill=GOLD)


def radial_well(size: tuple[int, int], radius: int, color=(28, 30, 32, 70)) -> Image.Image:
    """Soft charcoal disc so the relief reads as carved out of the field."""
    w, h = size
    yy, xx = np.ogrid[:h, :w]
    cx, cy = w / 2, h / 2
    dist = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / radius
    fall = np.clip(1.0 - dist, 0, 1)
    fall = fall ** 1.6
    layer = np.zeros((h, w, 4), dtype=np.uint8)
    layer[:, :, 0] = color[0]
    layer[:, :, 1] = color[1]
    layer[:, :, 2] = color[2]
    layer[:, :, 3] = (fall * color[3]).astype(np.uint8)
    return Image.fromarray(layer, "RGBA")


def build():
    ASSETS.mkdir(exist_ok=True)

    crest = extract_official_crest()
    crest.save(ASSETS / "fg-crest-official.png")
    graphite = to_graphite_grapplers(crest)
    graphite.save(ASSETS / "fg-crest-graphite.png")
    hero = isolate_grapplers(graphite)
    hero.save(ASSETS / "fg-grapplers-graphite.png")

    canvas = Image.new("RGBA", (W, H), BLACK)
    draw = ImageDraw.Draw(canvas)
    draw.rectangle([0, 0, W, H], fill=BLACK)

    canvas.alpha_composite(make_texture((W, H)))
    draw_vignette(canvas)
    draw = ImageDraw.Draw(canvas)

    # Geometric frame — inset from Instagram chrome
    corner_brackets(draw, (48, 86, W - 48, H - 86), length=52, color=GOLD_DIM, width=2)
    draw.rectangle([62, 100, W - 62, H - 100], outline=(40, 36, 28, 255), width=1)

    # Small FG monogram — upper left, below Reel chrome
    fnt_mono = font("Cinzel-Bold.ttf", 20)
    draw.rectangle([88, 176, 160, 228], outline=GOLD_DIM, width=1)
    draw_tracked(draw, "FG", 190, fnt_mono, GOLD, tracking=5, center_x=124)

    # ---- Brand name (hierarchy #1) ----
    fnt_fs = font("BebasNeue-latin.ttf", 100)
    fnt_gz = font("Cinzel-Black.ttf", 46)
    draw_tracked(draw, "FREESTYLE", 250, fnt_fs, OFFWHITE, tracking=12)
    draw_tracked(draw, "GRAPPLERZ", 356, fnt_gz, GOLD, tracking=16)
    hairline(draw, 424, x0=200, x1=W - 200)
    fnt_sub = font("BarlowCondensed-Medium.ttf", 20)
    draw_tracked(draw, "BRAZILIAN JIU-JITSU  ·  GRAPPLING", 442, fnt_sub, MUTED, tracking=6)

    # ---- Locked grappler artwork (uniform scale only) ----
    # Keep native sharpness: modest upscale, prominent but not full-bleed.
    target_w = 560
    scale = target_w / hero.width
    hero_w = int(hero.width * scale)
    hero_h = int(hero.height * scale)
    hero_big = hero.resize((hero_w, hero_h), Image.Resampling.LANCZOS)
    hero_big = hero_big.filter(ImageFilter.UnsharpMask(radius=1.2, percent=80, threshold=2))

    hx = (W - hero_w) // 2
    hy = 468
    well = radial_well((hero_w + 160, hero_h + 120), radius=int(hero_w * 0.48), color=(36, 38, 42, 90))
    canvas.alpha_composite(well, (hx - 80, hy - 40))

    sa = np.array(hero_big.getchannel("A"))
    sh = np.zeros((hero_h, hero_w, 4), dtype=np.uint8)
    sh[:, :, 3] = (sa.astype(np.float32) * 0.40).astype(np.uint8)
    shadow = Image.fromarray(sh, "RGBA").filter(ImageFilter.GaussianBlur(16))
    canvas.alpha_composite(shadow, (hx, hy + 12))
    canvas.alpha_composite(hero_big, (hx, hy))
    draw = ImageDraw.Draw(canvas)

    # Faint Florida watermark behind the date — identity without tourism clutter.
    fl_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    fl_draw = ImageDraw.Draw(fl_layer)
    draw_florida(
        fl_draw,
        (390, 1188, 690, 1490),
        fill=None,
        outline=GOLD_DEEP,
        width=3,
        mark_clearwater=True,
    )
    fl_arr = np.array(fl_layer)
    fl_arr[:, :, 3] = (fl_arr[:, :, 3].astype(np.float32) * 0.16).astype(np.uint8)
    canvas.alpha_composite(Image.fromarray(fl_arr, "RGBA"))
    draw = ImageDraw.Draw(canvas)

    # ---- Date (hierarchy #2) — one of the largest elements ----
    date_top = 1190
    fnt_date = font("BebasNeue-latin.ttf", 152)
    fnt_year = font("Cinzel-Bold.ttf", 26)
    draw_tracked(draw, "OCTOBER 3", date_top, fnt_date, OFFWHITE, tracking=10)
    draw_tracked(draw, "2  0  2  6", date_top + 154, fnt_year, GOLD, tracking=12)
    hairline(draw, date_top + 206, x0=250, x1=W - 250)

    # ---- Location (hierarchy #3) ----
    fnt_city = font("Oswald-700.ttf", 40)
    fnt_venue = font("BarlowCondensed-Medium.ttf", 24)
    draw_tracked(draw, "CLEARWATER, FLORIDA", date_top + 230, fnt_city, OFFWHITE, tracking=8)
    draw_tracked(draw, "ROSS NORTON RECREATION CENTER", date_top + 284, fnt_venue, MUTED, tracking=5)

    # ---- CTA (hierarchy #4) ----
    cta_y = 1538
    fnt_cta = font("Oswald-700.ttf", 32)
    tw, th = text_size(draw, "REGISTRATION OPEN", fnt_cta)
    pad_x, pad_y = 38, 18
    box = [
        W // 2 - tw // 2 - pad_x,
        cta_y,
        W // 2 + tw // 2 + pad_x,
        cta_y + th + pad_y * 2,
    ]
    rounded_rect(draw, box, 2, fill=(20, 18, 14, 255), outline=GOLD, width=2)
    draw_tracked(draw, "REGISTRATION OPEN", cta_y + pad_y - 2, fnt_cta, GOLD, tracking=7)

    fnt_reg = font("BarlowCondensed-SemiBold.ttf", 26)
    draw_tracked(draw, "REGISTER NOW ON SMOOTHCOMP", box[3] + 30, fnt_reg, OFFWHITE, tracking=5)

    fnt_ig = font("BarlowCondensed-Regular.ttf", 22)
    draw_tracked(draw, "@freestylegrapplerz", box[3] + 74, fnt_ig, MUTED, tracking=3)

    draw.line([(SAFE_LEFT + 80, H - 118), (SAFE_RIGHT - 80, H - 118)], fill=GOLD_DEEP, width=1)

    rgb = canvas.convert("RGB")
    out = ROOT / "FREESTYLE_GRAPPLERZ_OCT3_2026_1080x1920.png"
    rgb.save(out, "PNG", optimize=True)
    print(f"wrote {out} {rgb.size}")
    print(f"crest {crest.size} hero {hero.size} placed {hero_w}x{hero_h} at {hx},{hy}")
    return out


if __name__ == "__main__":
    build()
