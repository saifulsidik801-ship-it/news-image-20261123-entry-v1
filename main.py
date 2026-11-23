#!/usr/bin/env python3
"""news-image-20261123: sum up the world's news of Monday 23 November 2026
in one 1024x1024 PNG front page, drawn entirely with Pillow.

No network. No randomness, no clock: every run writes identical bytes.
Output: $MAKEFUN_OUTPUT_DIR/entry.png (default /output/entry.png).
"""
import math
import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024

PAPER = (247, 243, 234)
INK = (16, 24, 38)
NAVY = (16, 35, 63)
NAVY2 = (24, 52, 88)
GOLD = (198, 148, 42)
RED = (178, 34, 34)
TEAL = (13, 110, 110)
WHITE = (255, 255, 255)
GREY = (90, 96, 104)
LIGHT = (233, 228, 216)
TILE_BG = (255, 255, 255)


# ---------------------------------------------------------------- fonts
def _find_font(names):
    bases = [
        "/usr/share/fonts/truetype/dejavu/",
        "/usr/share/fonts/truetype/liberation/",
        "/usr/share/fonts/truetype/noto/",
        "/usr/share/fonts/",
    ]
    for base in bases:
        for name in names:
            p = Path(base) / name
            if p.exists():
                return str(p)
    return None


SERIF_B = _find_font(["DejaVuSerif-Bold.ttf", "LiberationSerif-Bold.ttf"])
SANS_B = _find_font(["DejaVuSans-Bold.ttf", "LiberationSans-Bold.ttf"])
SANS = _find_font(["DejaVuSans.ttf", "LiberationSans-Regular.ttf"])
SANS_O = _find_font(["DejaVuSans-Oblique.ttf", "LiberationSans-Italic.ttf"])


def font(path, size):
    if path:
        return ImageFont.truetype(path, size)
    return ImageFont.load_default()


F_MAST = font(SERIF_B, 46)
F_DATE = font(SANS_B, 18)
F_KICK = font(SANS_B, 15)
F_LEAD = font(SERIF_B, 36)
F_LEADSUB = font(SANS, 18)
F_TILE_H = font(SANS_B, 17)
F_TILE_S = font(SANS, 13)
F_TAG = font(SANS_B, 11)
F_TICK = font(SANS_B, 14)
F_TICK_T = font(SANS, 14)
F_FOOT = font(SANS, 12)
F_NUM = font(SERIF_B, 30)


def wrap(draw, text, fnt, width):
    """Greedy word wrap to pixel width."""
    words = text.split()
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if draw.textlength(trial, font=fnt) <= width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def text(draw, xy, s, fnt, fill=INK, anchor="la"):
    draw.text(xy, s, font=fnt, fill=fill, anchor=anchor)


# ---------------------------------------------------------------- icons
# Every icon is drawn with plain Pillow primitives into a small box.
def icon_globe(d, x, y, s, c1=(13, 110, 110), c2=(198, 148, 42)):
    d.ellipse([x, y, x + s, y + s], fill=(38, 120, 170), outline=INK, width=3)
    d.arc([x + s * 0.22, y, x + s * 0.78, y + s], 270, 90, fill=WHITE, width=3)
    d.arc([x + s * 0.22, y, x + s * 0.78, y + s], 90, 270, fill=WHITE, width=3)
    d.line([x, y + s / 2, x + s, y + s / 2], fill=WHITE, width=3)
    d.ellipse([x + s * 0.18, y + s * 0.18, x + s * 0.42, y + s * 0.38], fill=(72, 160, 90))
    d.ellipse([x + s * 0.58, y + s * 0.60, x + s * 0.84, y + s * 0.82], fill=(72, 160, 90))


def icon_ship_fire(d, x, y, s):
    # hull
    d.polygon([(x, y + s * 0.55), (x + s, y + s * 0.55), (x + s * 0.85, y + s * 0.85),
               (x + s * 0.15, y + s * 0.85)], fill=(178, 34, 34))
    d.rectangle([x + s * 0.15, y + s * 0.30, x + s * 0.38, y + s * 0.55], fill=NAVY2)
    d.rectangle([x + s * 0.42, y + s * 0.30, x + s * 0.65, y + s * 0.55], fill=GOLD)
    d.rectangle([x + s * 0.69, y + s * 0.30, x + s * 0.88, y + s * 0.55], fill=(13, 110, 110))
    # flames
    for fx, fh in ((x + s * 0.28, 0.30), (x + s * 0.52, 0.38), (x + s * 0.74, 0.28)):
        d.polygon([(fx, y + s * 0.30), (fx + 9, y + s * 0.30 - fh * s),
                   (fx + 18, y + s * 0.30)], fill=(232, 120, 20))
    # waves
    for wy in (y + s * 0.92, y + s * 0.99):
        d.arc([x, wy - 4, x + s * 0.5, wy + 4], 200, 340, fill=(38, 120, 170), width=3)
        d.arc([x + s * 0.5, wy - 4, x + s, wy + 4], 200, 340, fill=(38, 120, 170), width=3)


def icon_ship_plain(d, x, y, s):
    # cargo ship with grey smoke: still burning, distinct from Gulf flames
    d.polygon([(x, y + s * 0.55), (x + s, y + s * 0.55), (x + s * 0.85, y + s * 0.85),
               (x + s * 0.15, y + s * 0.85)], fill=NAVY2)
    d.rectangle([x + s * 0.15, y + s * 0.30, x + s * 0.38, y + s * 0.55], fill=(178, 34, 34))
    d.rectangle([x + s * 0.42, y + s * 0.30, x + s * 0.65, y + s * 0.55], fill=GOLD)
    d.rectangle([x + s * 0.69, y + s * 0.30, x + s * 0.88, y + s * 0.55], fill=(13, 110, 110))
    for sx, sy, sr in ((0.30, 0.16, 10), (0.48, 0.08, 12), (0.68, 0.14, 9)):
        d.ellipse([x + s * sx - sr, y + s * sy - sr, x + s * sx + sr, y + s * sy + sr],
                  fill=(150, 150, 150))
    for wy in (y + s * 0.92, y + s * 0.99):
        d.arc([x, wy - 4, x + s * 0.5, wy + 4], 200, 340, fill=(38, 120, 170), width=3)
        d.arc([x + s * 0.5, wy - 4, x + s, wy + 4], 200, 340, fill=(38, 120, 170), width=3)


def icon_blast(d, x, y, s):
    d.rectangle([x + s * 0.15, y + s * 0.35, x + s * 0.55, y + s * 0.95], fill=(120, 124, 130))
    d.rectangle([x + s * 0.60, y + s * 0.55, x + s * 0.88, y + s * 0.95], fill=(150, 154, 160))
    for i in range(8):
        ang = i * 3.14159 / 4
        cx, cy = x + s * 0.45, y + s * 0.28
        ex, ey = cx + 26 * math.cos(ang), cy + 26 * math.sin(ang)
        d.line([cx, cy, ex, ey], fill=(232, 120, 20), width=4)
    d.ellipse([x + s * 0.32, y + s * 0.15, x + s * 0.58, y + s * 0.41], fill=(255, 190, 60))


def icon_planet(d, x, y, s):
    d.ellipse([x + s * 0.15, y + s * 0.15, x + s * 0.85, y + s * 0.85], fill=(150, 110, 70))
    d.ellipse([x + s * 0.28, y + s * 0.25, x + s * 0.45, y + s * 0.42], fill=(110, 80, 50))
    d.ellipse([x + s * 0.58, y + s * 0.55, x + s * 0.72, y + s * 0.68], fill=(110, 80, 50))
    d.ellipse([x - s * 0.05, y + s * 0.38, x + s * 1.05, y + s * 0.62],
              outline=GOLD, width=4)
    d.ellipse([x + s * 0.72, y + s * 0.02, x + s * 0.80, y + s * 0.10], fill=WHITE)
    d.ellipse([x + s * 0.05, y + s * 0.08, x + s * 0.11, y + s * 0.14], fill=WHITE)


def icon_ufo(d, x, y, s):
    d.ellipse([x, y + s * 0.45, x + s, y + s * 0.72], fill=(120, 124, 130))
    d.pieslice([x + s * 0.25, y + s * 0.18, x + s * 0.75, y + s * 0.62], 180, 360,
               fill=(120, 200, 220))
    for i in range(3):
        d.ellipse([x + s * (0.22 + i * 0.25), y + s * 0.55, x + s * (0.30 + i * 0.25),
                   y + s * 0.63], fill=GOLD)
    d.polygon([(x + s * 0.42, y + s * 0.72), (x + s * 0.58, y + s * 0.72),
               (x + s * 0.50, y + s * 0.95)], fill=(255, 220, 100))


def icon_badge(d, x, y, s):
    d.polygon([(x + s * 0.5, y), (x + s * 0.95, y + s * 0.18), (x + s * 0.95, y + s * 0.55),
               (x + s * 0.5, y + s), (x + s * 0.05, y + s * 0.55), (x + s * 0.05, y + s * 0.18)],
              fill=NAVY2, outline=GOLD, width=3)
    d.text((x + s * 0.5, y + s * 0.52), "*", font=font(SANS_B, int(s * 0.55)),
           fill=GOLD, anchor="mm")


def icon_flags(d, x, y, s):
    d.line([x + s * 0.22, y + s * 0.10, x + s * 0.22, y + s * 0.95], fill=INK, width=3)
    d.line([x + s * 0.78, y + s * 0.10, x + s * 0.78, y + s * 0.95], fill=INK, width=3)
    d.polygon([(x + s * 0.22, y + s * 0.10), (x + s * 0.55, y + s * 0.22),
               (x + s * 0.22, y + s * 0.34)], fill=(178, 34, 34))
    d.polygon([(x + s * 0.78, y + s * 0.10), (x + s * 0.45, y + s * 0.22),
               (x + s * 0.78, y + s * 0.34)], fill=(232, 120, 20))


def icon_chip(d, x, y, s):
    d.rectangle([x + s * 0.2, y + s * 0.2, x + s * 0.8, y + s * 0.8], fill=INK)
    d.rectangle([x + s * 0.35, y + s * 0.35, x + s * 0.65, y + s * 0.65], fill=GOLD)
    for i in range(3):
        yy = y + s * (0.3 + i * 0.2)
        d.line([x + s * 0.05, yy, x + s * 0.2, yy], fill=INK, width=3)
        d.line([x + s * 0.8, yy, x + s * 0.95, yy], fill=INK, width=3)
    d.line([x + s * 0.5, y + s * 0.05, x + s * 0.5, y + s * 0.2], fill=RED, width=5)
    d.line([x + s * 0.5, y + s * 0.05, x + s * 0.5, y + s * 0.2], fill=RED, width=5)


def icon_cricket(d, x, y, s):
    d.line([x + s * 0.30, y + s * 0.05, x + s * 0.62, y + s * 0.62], fill=(160, 110, 60), width=12)
    d.rectangle([x + s * 0.55, y + s * 0.55, x + s * 0.85, y + s * 0.95], fill=(200, 170, 110))
    d.ellipse([x + s * 0.08, y + s * 0.68, x + s * 0.32, y + s * 0.92], fill=RED)
    d.arc([x + s * 0.08, y + s * 0.68, x + s * 0.32, y + s * 0.92], 0, 180, fill=WHITE, width=2)


def icon_factory(d, x, y, s):
    d.polygon([(x, y + s * 0.95), (x, y + s * 0.55), (x + s * 0.25, y + s * 0.35),
               (x + s * 0.5, y + s * 0.55), (x + s * 0.75, y + s * 0.35),
               (x + s, y + s * 0.55), (x + s, y + s * 0.95)], fill=(120, 124, 130))
    d.rectangle([x + s * 0.70, y + s * 0.10, x + s * 0.82, y + s * 0.45], fill=(90, 94, 100))
    d.polygon([(x + s * 0.76, y + s * 0.10), (x + s * 0.68, y - s * 0.12),
               (x + s * 0.84, y - s * 0.12)], fill=(232, 120, 20))
    d.rectangle([x + s * 0.15, y + s * 0.65, x + s * 0.30, y + s * 0.80], fill=GOLD)


def icon_crowd(d, x, y, s):
    for cx, cy, r, col in ((0.28, 0.38, 0.16, NAVY2), (0.5, 0.30, 0.18, RED),
                           (0.72, 0.38, 0.16, TEAL)):
        d.ellipse([x + s * (cx - r), y + s * (cy - r), x + s * (cx + r), y + s * (cy + r)],
                  fill=col)
        d.pieslice([x + s * (cx - r - 0.06), y + s * (cy + r - 0.02),
                    x + s * (cx + r + 0.06), y + s * (cy + r + 0.42)], 180, 360, fill=col)
    d.line([x + s * 0.82, y + s * 0.55, x + s * 0.95, y + s * 0.30], fill=INK, width=4)
    d.rectangle([x + s * 0.86, y + s * 0.18, x + s, y + s * 0.34], fill=INK)


def icon_dove(d, x, y, s):
    # olive branch: diagonal stem with paired leaves (peace)
    d.line([x + s * 0.08, y + s * 0.90, x + s * 0.92, y + s * 0.10], fill=(72, 120, 60),
           width=5)
    for t in (0.18, 0.38, 0.58, 0.78):
        cx = x + s * (0.08 + 0.84 * t)
        cy = y + s * (0.90 - 0.80 * t)
        d.ellipse([cx - 16, cy - 22, cx + 2, cy - 4], fill=(72, 160, 90))
        d.ellipse([cx - 2, cy + 4, cx + 16, cy + 22], fill=(58, 140, 80))


def icon_robot(d, x, y, s):
    d.rectangle([x + s * 0.2, y + s * 0.25, x + s * 0.8, y + s * 0.75], fill=(150, 154, 160),
                outline=INK, width=2)
    d.ellipse([x + s * 0.32, y + s * 0.40, x + s * 0.44, y + s * 0.52], fill=RED)
    d.ellipse([x + s * 0.56, y + s * 0.40, x + s * 0.68, y + s * 0.52], fill=RED)
    d.line([x + s * 0.35, y + s * 0.62, x + s * 0.65, y + s * 0.62], fill=INK, width=3)
    d.line([x + s * 0.5, y + s * 0.25, x + s * 0.5, y + s * 0.08], fill=INK, width=3)
    d.ellipse([x + s * 0.44, y, x + s * 0.56, y + s * 0.12], fill=GOLD)
    d.line([x + s * 0.2, y + s * 0.5, x + s * 0.05, y + s * 0.5], fill=INK, width=3)
    d.line([x + s * 0.8, y + s * 0.5, x + s * 0.95, y + s * 0.5], fill=INK, width=3)


ICONS = {
    "globe": icon_globe, "ship": icon_ship_fire, "ship_plain": icon_ship_plain,
    "blast": icon_blast,
    "planet": icon_planet, "ufo": icon_ufo, "badge": icon_badge,
    "flags": icon_flags, "chip": icon_chip, "cricket": icon_cricket,
    "factory": icon_factory, "crowd": icon_crowd, "dove": icon_dove,
    "robot": icon_robot,
}

# ---------------------------------------------------------------- content
# Every story below was first reported on Monday 23 November 2026.
LEAD = {
    "tag": "CLIMATE  •  ANTALYA, TURKIYE",
    "head": "COP31 COLLAPSES: NO DEAL ON FOSSIL FUELS",
    "sub": ("Climate talks end with no deal as oil states block fossil-fuel "
            "language; Guterres \u201cdeeply disappointed\u201d in the "
            "\u201cworst ever\u201d outcome."),
}

TILES = [
    ("GULF CRISIS", "ship", "GULF ON EDGE",
     "Bahrain demands UN action after Iran hits a civilian site; 25 tankers "
     "struck around Hormuz in a week."),
    ("UKRAINE", "blast", "KYIV REGION HIT",
     "Russian drone strikes a building outside Kyiv; at least 14 missing "
     "as rescuers dig through rubble."),
    ("BALTIC SEA", "ship_plain", "CARGO SHIP ABLAZE",
     "Russian cargo ship still on fire off Finland after an attack at sea."),
    ("SPACE", "planet", "HELLO, MERCURY",
     "Europe-Japan probe BepiColombo enters orbit around Mercury after an "
     "eight-year voyage."),
    ("DEFENCE", "ufo", "43 NEW UAP FILES",
     "Pentagon releases 43 more declassified UAP files, including three "
     "Middle East military videos."),
    ("MEXICO", "badge", "CARTEL KINGPIN CAUGHT",
     "Mexico seizes FBI most-wanted boss \u201cEl Chapo Isidro\u201d; 11 killed "
     "in Sinaloa firefights."),
    ("SOUTH ASIA", "flags", "DELHI TALKS",
     "Nepal PM Balendra Shah holds bilateral talks with PM Modi in New Delhi."),
    ("SEOUL", "chip", "MINISTER QUITS",
     "South Korea\u2019s education minister resigns over an AI exam-cheating "
     "scandal."),
    ("CRICKET", "cricket", "720/9d \u2014 A RECORD",
     "India post a record total in the Wellington Test against New Zealand."),
    ("INDONESIA", "factory", "FACTORY FIRE",
     "Seven bodies recovered and 50 missing after a factory blaze."),
    ("PORTUGAL", "crowd", "STREETS ERUPT",
     "Thousands march in Lisbon as living costs fuel anger."),
    ("GAZA", "dove", "NINE KILLED IN 48 HOURS",
     "Israeli strikes kill nine; toll since the October 2025 ceasefire "
     "reaches 1,661."),
]

TICKER = [
    "Nigeria boat capsize kills 24",
    "France protests: 6th Saturday",
    "Likud-Yashar talks resume",
    "BBC Verify: Crimea Bridge blasts",
    "Tata Steel \u20b928,000-crore sale",
    "MP Wadkute dies in Delhi",
    "Tarantino welcomes baby boy",
    "Delta: 3,500 Atlanta delays",
    "Myanmar slams ASEAN ruling",
    "Ex-police chief De Gennaro dead",
]

TAG_COLORS = {
    "GULF CRISIS": RED, "UKRAINE": NAVY2, "BALTIC SEA": TEAL,
    "SPACE": (90, 60, 140), "DEFENCE": (90, 96, 104), "MEXICO": (140, 90, 20),
    "SOUTH ASIA": (178, 90, 20), "SEOUL": (13, 110, 110),
    "CRICKET": (20, 110, 60), "INDONESIA": RED, "PORTUGAL": (150, 60, 90),
    "GAZA": (90, 96, 104),
}


# ---------------------------------------------------------------- drawing
def draw_tile(d, x, y, w, h, tag, icon, head, sub):
    d.rectangle([x, y, x + w, y + h], fill=TILE_BG, outline=(200, 194, 178), width=1)
    col = TAG_COLORS.get(tag, NAVY2)
    d.rectangle([x, y, x + w, y + 22], fill=col)
    text(d, (x + 8, y + 11), tag, F_TAG, fill=WHITE, anchor="lm")
    ix, iy, isize = x + 10, y + 32, 62
    ICONS[icon](d, ix, iy, isize)
    tx = x + 82
    tw = w - 92
    lines = wrap(d, head, F_TILE_H, tw)
    ly = y + 30
    for ln in lines[:3]:
        text(d, (tx, ly), ln, F_TILE_H)
        ly += 20
    sub_lines = wrap(d, sub, F_TILE_S, tw)
    sy = ly + 2
    for ln in sub_lines[:3]:
        text(d, (tx, sy), ln, F_TILE_S, fill=(60, 64, 70))
        sy += 16


def main():
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)

    # outer frame
    d.rectangle([4, 4, W - 5, H - 5], outline=INK, width=4)

    # ---- masthead
    d.rectangle([10, 10, W - 11, 108], fill=NAVY)
    text(d, (28, 58), "THE WORLD TODAY", F_MAST, fill=WHITE, anchor="lm")
    text(d, (W - 28, 44), "MONDAY  \u2022  23 NOVEMBER 2026", F_DATE,
         fill=GOLD, anchor="rm")
    text(d, (W - 28, 74), "ONE PAGE  \u2022  23 STORIES", F_DATE,
         fill=WHITE, anchor="rm")
    d.rectangle([10, 108, W - 11, 112], fill=GOLD)

    # ---- lead story
    ly0, ly1 = 122, 296
    d.rectangle([20, ly0, W - 21, ly1], fill=WHITE, outline=(200, 194, 178), width=1)
    d.rectangle([20, ly0, W - 21, ly0 + 26], fill=RED)
    text(d, (34, ly0 + 13), LEAD["tag"], F_TAG, fill=WHITE, anchor="lm")
    text(d, (W - 34, ly0 + 13), "LEAD STORY", F_TAG, fill=WHITE, anchor="rm")
    head_lines = wrap(d, LEAD["head"], F_LEAD, 700)
    hy = ly0 + 38
    for ln in head_lines:
        text(d, (34, hy), ln, F_LEAD)
        hy += 42
    sub_lines = wrap(d, LEAD["sub"], F_LEADSUB, 700)
    sy = hy + 6
    for ln in sub_lines:
        text(d, (34, sy), ln, F_LEADSUB, fill=(60, 64, 70))
        sy += 24
    # lead art: globe with smoke, gold ring
    gx, gy, gs = 760, ly0 + 42, 116
    d.ellipse([gx - 8, gy - 8, gx + gs + 8, gy + gs + 8], outline=GOLD, width=3)
    icon_globe(d, gx, gy, gs)

    # ---- tile grid: 3 cols x 4 rows
    gx0, gy0 = 20, 310
    tw, th, gap = 322, 138, 8
    for i, (tag, icon, head, sub) in enumerate(TILES):
        cx = gx0 + (i % 3) * (tw + gap)
        cy = gy0 + (i // 3) * (th + gap)
        draw_tile(d, cx, cy, tw, th, tag, icon, head, sub)

    # ---- ticker: also today
    ty0 = gy0 + 4 * th + 3 * gap + 8  # 894
    d.rectangle([20, ty0, W - 21, ty0 + 84], fill=NAVY)
    text(d, (34, ty0 + 12), "ALSO TODAY", F_TAG, fill=GOLD)
    tick_txt = "   \u2022   ".join(TICKER)
    tlines = wrap(d, tick_txt, F_TICK_T, W - 68)
    ty = ty0 + 30
    for ln in tlines[:3]:
        text(d, (34, ty), ln, F_TICK_T, fill=WHITE)
        ty += 18

    # ---- footer
    fy = ty0 + 84 + 10
    d.line([20, fy, W - 21, fy], fill=(200, 194, 178), width=1)
    text(d, (W // 2, fy + 14),
         "All stories first reported Monday 23 November 2026  \u2022  Compiled from wire reports",
         F_FOOT, fill=GREY, anchor="ma")

    out_dir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "entry.png"
    img.save(out_path, format="PNG", optimize=True)
    print(f"wrote {out_path} ({out_path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
