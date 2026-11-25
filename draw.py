#!/usr/bin/env python3
"""The World in One Day — Tuesday 24 November 2026: 35 stories (v3).

One 1024x1024 newspaper-style page summing up the day's world news.
Every story is dated 24 November 2026 (see the DATE CHECK box).
Built clean-room for bounty news-image-20261124.

Layout: navy masthead, giant serif date, red italic subline, 6-number
strip, region colour bar, 3 hero cards, 10 illustrated cards, world map
with numbered pins, 22-item list, DATE CHECK box, sources footer.

Every illustration is rendered onto its own layer and pasted masked to
its box, so no smoke or ink can escape its frame (v2 leaked smoke 4-7 px
above three boxes). Asserts at the end verify pin spacing, DATE CHECK
line widths, list line widths and the empty bands above every box.
"""

import itertools
import math
import os
import sys
from PIL import Image, ImageDraw, ImageFont

W = H = 1024
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "entry.png")

PAPER = (250, 244, 230)
CARD = (255, 253, 247)
INK = (35, 32, 28)
NAVY = (16, 32, 64)
RED = (178, 34, 34)
GREY = (90, 86, 80)
SEA = (108, 188, 224)
LAND = (233, 221, 191)
LAND_LINE = (178, 164, 138)

DJ = "/usr/share/fonts/truetype/dejavu/"
NOTO = "/usr/share/fonts/truetype/noto/"


def font(name, size):
    return ImageFont.truetype(DJ + name, size)


def f_serif_b(s):
    return font("DejaVuSerif-Bold.ttf", s)


def f_serif(s):
    return font("DejaVuSerif.ttf", s)


def f_serif_i(s):
    p = NOTO + "NotoSerif-Italic.ttf"
    if os.path.exists(p):
        return ImageFont.truetype(p, s)
    return font("DejaVuSerif.ttf", s)


def f_sans(s):
    return font("DejaVuSans.ttf", s)


def f_sans_b(s):
    return font("DejaVuSans-Bold.ttf", s)


def text_w(d, text, f):
    return d.textlength(text, font=f)


def wrap(d, text, f, max_w):
    """Greedy word wrap; returns list of lines, each <= max_w px."""
    lines, cur = [], ""
    for word in text.split(" "):
        trial = word if not cur else cur + " " + word
        if text_w(d, trial, f) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def draw_centred(d, cx, y_top, text, f, fill):
    """Draw text centred on cx, top edge at y_top."""
    w = text_w(d, text, f)
    d.text((cx - w / 2, y_top), text, font=f, fill=fill)


# ---------------------------------------------------------------- data
NUMBERS = [
    ("3", "tankers hit mines in Hormuz"),
    ("40", "wounded in Zaporizhzhia"),
    ("5,258", "heat deaths in England"),
    ("14", "partners face US tariffs"),
    ("$41bn", "Sanofi deal for Insmed"),
    ("6,803", "returned to Myanmar"),
]

REGIONS = [
    ("EUROPE", 11, (52, 102, 174)),
    ("MIDDLE EAST", 7, (178, 34, 34)),
    ("ASIA-PACIFIC", 10, (58, 138, 138)),
    ("AMERICAS", 3, (56, 140, 70)),
    ("TECH & BUSINESS", 3, (122, 80, 160)),
    ("SCIENCE & CULTURE", 1, (198, 158, 58)),
]

# heroes: (number, kicker, headline, deck, caption, scene key)
HEROES = [
    (1, "STRAIT OF HORMUZ \u00b7 IRAN WAR",
     "Iran claims three tankers hit mines",
     "Tehran vows to use all its tools against the US blockade. (Reuters)",
     "Strait of Hormuz \u00b7 Reuters", "tanker"),
    (2, "RIYADH \u00b7 HOUTHI ATTACK",
     "Houthi drone hits Riyadh tower again",
     "Second strike on the same tower in five days; 11 wounded. "
     "(Straits Times)",
     "Riyadh skyline \u00b7 AFP", "riyadh"),
    (3, "SHANGHAI \u00b7 CHINA POLITICS",
     "China probes Shanghai chief",
     "Chen Jining, a Politburo member, probed; first Shanghai chief "
     "since 2006. (Xinhua)",
     "Shanghai \u00b7 Xinhua", "shanghai"),
]

# cards: (number, label, headline, place, place colour, scene key)
CARDS = [
    (4, "MISSILE STRIKE", "Russian strike kills 2, wounds 40 in Zaporizhzhia",
     "ZAPORIZHZHIA, UKRAINE", (52, 102, 174), "zaporizhzhia"),
    (5, "GAZA STRIKE", "Israeli strikes kill Hamas security chief in Gaza",
     "GAZA CITY", (178, 34, 34), "gaza"),
    (6, "WARSHIP HIT", "Ukraine claims sinking of Russian warship off Benghazi",
     "BENGHAZI, LIBYA", (178, 34, 34), "warship"),
    (7, "$41BN DEAL", "Sanofi to buy Insmed for $41bn",
     "PARIS", (52, 102, 174), "sanofi"),
    (8, "GUILTY 10/12", "Huawei convicted on 10 of 12 counts in US trial",
     "BROOKLYN, US", (122, 80, 160), "huawei"),
    (9, "IOWA BLAST", "Army to detonate Iowa explosives after court refuses stay",
     "IOWA, US", (56, 140, 70), "iowa"),
    (10, "HEAT TOLL", "England records 5,258 heat deaths, worst since 2016",
     "LONDON", (52, 102, 174), "heat"),
    (11, "HANOI BLAST", "Hanoi hotpot gas blast kills 6, building collapses",
     "HANOI, VIETNAM", (58, 138, 138), "hanoi"),
    (12, "M5.6 QUAKE", "5.6 quake strikes Nepal near China border",
     "NEPAL", (58, 138, 138), "nepal"),
    (13, "CHIP SURGE", "Nvidia shares surge 31% as Huang returns",
     "SANTA CLARA, US", (122, 80, 160), "nvidia"),
]

# list: (number, region key, text) — every line must fit one column
LIST_ITEMS = [
    (14, "EU", "Germany first to get Delta system (Kyiv Ind.)"),
    (15, "EU", "Seven nations back EU Russian visa curbs (Kyiv Ind.)"),
    (16, "EU", "Zelensky urges NATO to admit Ukraine (Kyiv Ind.)"),
    (17, "EU", "Russia warns Estonia moves verge of war (IQMIA)"),
    (18, "EU", "Russian drone violates Polish airspace (Kyiv Ind.)"),
    (19, "ME", "Iraq PM: oil ministry to run Kurdish fields (Reuters)"),
    (20, "ME", "Gaza meningitis alert: 272 cases in October (WHO)"),
    (21, "AP", "Russian jets enter S. Korea air defence zone (AP)"),
    (22, "AP", "Hasina to return 16 Dec; Dhaka: handcuffs (Reuters)"),
    (23, "AP", "Japan to pay full ICC contribution early (Reuters)"),
    (24, "AP", "S. Korea offers $375,000 to catch AI cheats (WSJ)"),
    (25, "AP", "Solomon Islands to end China pact (10Things)"),
    (26, "AP", "Malaysia to return 6,803 to Myanmar (AP)"),
    (27, "AP", "Australia in Big Tech fine deal, up to 5% (Reuters)"),
    (28, "AM", "US plans tariffs on 14 partners (Reuters)"),
    (29, "EU", "UK sanctions Houthis over Riyadh strike (Reuters)"),
    (30, "ME", "US to train Syrian soldiers in demining (Reuters)"),
    (31, "AM", "DOJ admits deporting US citizen (The Hill)"),
    (32, "EU", "Lukashenko offers Zelenskiy flight to Moscow (Reuters)"),
    (33, "EU", "Latvia: war may hit tipping point in 2027 (Reuters)"),
    (34, "EU", "Russia claims 699 drones downed overnight (MOD)"),
    (35, "SCI", "Farthest black hole found, 630m yrs on (Principia)"),
]

REGION_COLOUR = {
    "EU": (52, 102, 174), "ME": (178, 34, 34), "AP": (58, 138, 138),
    "AM": (56, 140, 70), "TECH": (122, 80, 160), "SCI": (198, 158, 58),
}

# pins: (number, lon, lat, region, dx, dy) — dx/dy nudge the drawn centre
# so no two 14 px circles overlap; every pin stays in its true area.
PINS = [
    (1, 57.0, 26.0, "ME", 6, -2),
    (2, 46.7, 24.7, "ME", -3, 4),
    (3, 121.5, 31.2, "AP", 0, 0),
    (4, 35.2, 47.8, "EU", 2, -4),
    (5, 34.5, 31.5, "ME", -2, -2),
    (6, 20.0, 32.1, "ME", -4, 2),
    (7, 2.35, 48.85, "TECH", 6, 6),
    (8, -74.0, 40.7, "TECH", 0, 0),
    (9, -93.6, 41.9, "AM", 0, 0),
    (10, -0.1, 51.5, "EU", -2, -3),
    (11, 105.85, 21.0, "AP", 0, 4),
    (12, 85.0, 28.0, "AP", 0, 0),
    (13, -122.0, 37.3, "TECH", 0, 0),
]

# simplified continent outlines (lon, lat), drawn equirectangular
NORTH_AMERICA = [(-168, 66), (-162, 60), (-155, 58), (-150, 61), (-142, 60),
                 (-136, 58), (-130, 54), (-127, 50), (-124, 44), (-121, 37),
                 (-117, 33), (-112, 29), (-108, 25), (-105, 21), (-100, 18),
                 (-96, 16), (-92, 15), (-88, 13), (-84, 10), (-81, 8),
                 (-79, 9), (-82, 10), (-84, 12), (-87, 14), (-90, 14),
                 (-93, 15), (-96, 16), (-97, 18), (-94, 18), (-91, 19),
                 (-87, 21), (-84, 22), (-82, 23), (-80, 25), (-81, 27),
                 (-82, 29), (-84, 30), (-88, 30), (-90, 29), (-93, 30),
                 (-96, 29), (-97, 26), (-94, 26), (-91, 29), (-89, 30),
                 (-85, 30), (-82, 28), (-81, 26), (-80, 27), (-80, 31),
                 (-76, 34), (-75, 37), (-74, 40), (-71, 42), (-69, 44),
                 (-66, 45), (-60, 47), (-56, 50), (-54, 52), (-56, 55),
                 (-60, 56), (-64, 58), (-68, 58), (-72, 62), (-78, 62),
                 (-82, 66), (-86, 66), (-90, 68), (-95, 69), (-100, 68),
                 (-110, 68), (-120, 69), (-130, 70), (-140, 70), (-150, 70),
                 (-160, 71), (-166, 68)]
GREENLAND = [(-58, 64), (-52, 60), (-43, 60), (-40, 64), (-32, 68),
             (-22, 70), (-30, 76), (-45, 76), (-58, 74), (-60, 70)]
SOUTH_AMERICA = [(-79, 9), (-77, 6), (-77, 3), (-80, -2), (-81, -5),
                 (-79, -9), (-76, -13), (-72, -18), (-70, -22), (-70, -28),
                 (-72, -33), (-73, -38), (-73, -44), (-74, -49), (-71, -53),
                 (-68, -55), (-66, -55), (-65, -50), (-64, -45), (-62, -40),
                 (-58, -35), (-54, -34), (-50, -30), (-47, -26), (-43, -23),
                 (-40, -20), (-37, -14), (-35, -9), (-35, -6), (-38, -4),
                 (-42, -2), (-46, -1), (-50, 0), (-53, 4), (-56, 6),
                 (-60, 8), (-64, 10), (-68, 11), (-72, 12), (-76, 10)]
AFRICA = [(-17, 15), (-17, 20), (-15, 26), (-11, 30), (-6, 34), (-1, 35),
          (5, 37), (10, 37), (11, 34), (15, 32), (19, 32), (23, 32),
          (28, 31), (32, 31), (34, 28), (35, 23), (36, 20), (38, 17),
          (40, 14), (42, 11), (46, 11), (51, 12), (51, 10), (48, 6),
          (46, 2), (43, 0), (41, -3), (40, -8), (38, -13), (36, -18),
          (33, -24), (29, -29), (25, -33), (20, -35), (17, -33), (15, -28),
          (13, -20), (12, -14), (10, -6), (9, -1), (9, 4), (-7, 5),
          (-12, 8), (-16, 12)]
EUROPE = [(-10, 36), (-9, 39), (-9, 43), (-4, 44), (-1, 46), (-4, 48),
          (-1, 49), (2, 51), (4, 53), (7, 55), (8, 57), (10, 59), (6, 62),
          (11, 64), (16, 68), (21, 70), (27, 71), (32, 70), (38, 68),
          (42, 66), (44, 62), (40, 60), (36, 58), (32, 59), (28, 57),
          (26, 55), (23, 54), (20, 55), (17, 54), (13, 54), (9, 53),
          (5, 52), (1, 50), (-3, 47), (-5, 44), (-9, 40)]
ASIA = [(28, 41), (30, 45), (33, 46), (38, 47), (42, 46), (45, 43),
        (48, 42), (50, 44), (53, 46), (57, 47), (61, 46), (65, 45),
        (68, 44), (71, 42), (74, 41), (77, 39), (80, 37), (82, 34),
        (85, 31), (88, 29), (90, 26), (92, 23), (94, 20), (97, 17),
        (99, 13), (101, 9), (103, 6), (104, 2), (106, 8), (108, 12),
        (110, 16), (112, 20), (114, 22), (117, 24), (120, 27), (122, 31),
        (125, 34), (127, 37), (129, 40), (131, 43), (134, 44), (137, 46),
        (140, 49), (142, 53), (145, 57), (148, 59), (152, 59), (156, 57),
        (159, 56), (161, 59), (163, 61), (168, 64), (173, 65), (178, 66),
        (178, 68), (172, 69), (166, 69), (160, 70), (154, 71), (148, 72),
        (142, 73), (136, 73), (130, 72), (124, 73), (118, 74), (112, 75),
        (106, 76), (100, 76), (94, 75), (88, 74), (82, 73), (76, 72),
        (70, 71), (64, 70), (58, 69), (52, 68), (46, 67), (40, 66),
        (35, 65), (30, 62), (28, 58), (26, 53), (27, 48), (28, 44)]
AUSTRALIA = [(113, -22), (114, -28), (115, -32), (118, -35), (123, -34),
             (128, -32), (132, -32), (135, -35), (138, -35), (141, -38),
             (145, -38), (149, -37), (152, -33), (153, -28), (151, -24),
             (148, -20), (145, -17), (142, -14), (142, -11), (139, -12),
             (136, -13), (133, -12), (130, -13), (127, -14), (124, -16),
             (121, -19), (117, -20)]
NEW_GUINEA = [(131, -1), (135, -2), (138, -3), (141, -4), (144, -6),
              (147, -7), (150, -8), (147, -9), (144, -8), (141, -8),
              (138, -8), (135, -6), (132, -3)]
INDONESIA = [(95, 5), (98, 3), (100, 1), (102, -1), (104, -3), (106, -6),
             (109, -7), (112, -7), (115, -8), (118, -9), (120, -10),
             (123, -10), (126, -9), (129, -7), (131, -5), (133, -3),
             (136, -2), (138, -4), (140, -6), (141, -8)]
UK = [(-5, 50), (-3, 53), (-5, 56), (-3, 58), (-1, 57), (0, 53),
      (1, 51), (-2, 50)]
ARABIA = [(34, 31), (36, 33), (37, 36), (40, 34), (42, 31), (44, 29),
          (46, 27), (48, 29), (50, 28), (52, 26), (54, 26), (56, 26),
          (58, 24), (59, 22), (58, 19), (56, 17), (54, 16), (52, 15),
          (50, 14), (48, 14), (45, 13), (43, 12), (42, 14), (41, 17),
          (39, 21), (37, 25), (35, 29)]
INDIA = [(68, 23), (70, 21), (72, 19), (73, 16), (74, 13), (76, 10),
         (77, 8), (78, 9), (80, 11), (80, 14), (82, 17), (84, 19),
         (86, 20), (88, 22), (89, 24), (88, 26), (85, 28), (82, 30),
         (79, 31), (76, 32), (73, 31), (70, 28), (68, 25)]
JAPAN = [(130, 31), (132, 33), (134, 34), (136, 35), (138, 35), (140, 36),
         (141, 39), (141, 42), (143, 44), (141, 45), (140, 42), (139, 38),
         (137, 36), (135, 34), (133, 33)]
CONTINENTS = [NORTH_AMERICA, GREENLAND, SOUTH_AMERICA, AFRICA, EUROPE,
              ASIA, AUSTRALIA, NEW_GUINEA, INDONESIA, UK, JAPAN, ARABIA,
              INDIA]

DATE_CHECK_TEXT = (
    "Wires read on Tuesday 24 November 2026. Every story happened or was "
    "first reported on 24 November 2026, in any time zone. Left out: "
    "Shenzhen (19 Nov); COP31 (23 Nov); ICJ Rohingya ruling "
    "(19 Nov); 700,000 tally (23 Nov); Kerch Bridge (16\u201317 Nov); FBI "
    "hack (20 Nov); Poland missiles (20 Nov); Alcaraz win (22 Nov); "
    "Hormuz blockade (Apr 13, Jul 14); NATO space (23 Nov); Myanmar "
    "sanctions (23 Nov); Ebola teams trapped in Ituri (23 Nov); Grok "
    "suits (23 Nov); Oxfam toxic land (23 Nov)."
)

# ---------------------------------------------------------------- scenes
# Every scene draws on its own layer of size (w, h); the layer is pasted
# onto the page, so nothing a scene draws can leave its box. Smoke puffs
# are also kept well inside the layer on purpose (v2 leaked 4-7 px).


def scene_tanker(d, w, h):
    """Hormuz: tanker at sunset, flames, smoke kept inside the frame."""
    d.rectangle((0, 0, w, int(h * 0.62)), fill=(232, 122, 40))
    d.rectangle((0, int(h * 0.62), w, h), fill=(14, 42, 84))
    d.ellipse((w * 0.72, h * 0.10, w * 0.72 + 34, h * 0.10 + 34),
              fill=(250, 214, 140))
    # smoke puffs: centres low enough that no puff crosses y=0
    for cx, cy, r in [(0.16, 0.30, 13), (0.26, 0.24, 15), (0.38, 0.32, 12),
                      (0.52, 0.26, 11)]:
        d.ellipse((w * cx - r, h * cy - r, w * cx + r, h * cy + r),
                  fill=(70, 62, 78))
    # flames
    for fx in (0.30, 0.44, 0.58):
        d.polygon([(w * fx - 12, h * 0.62), (w * fx, h * 0.30),
                   (w * fx + 12, h * 0.62)], fill=(255, 176, 32))
        d.polygon([(w * fx - 6, h * 0.62), (w * fx, h * 0.44),
                   (w * fx + 6, h * 0.62)], fill=(255, 232, 120))
    # containers
    for i, col in enumerate([(178, 34, 34), (52, 102, 174), (56, 140, 70),
                             (198, 158, 58)]):
        x = w * (0.18 + i * 0.13)
        d.rectangle((x, h * 0.46, x + 30, h * 0.62), fill=col)
    # hull
    d.polygon([(8, h * 0.62), (w - 8, h * 0.62), (w - 26, h * 0.78),
               (24, h * 0.78)], fill=(16, 16, 20))
    d.rectangle((24, h * 0.72, w - 26, h * 0.78), fill=(178, 34, 34))
    # waves
    for i, yy in enumerate((0.84, 0.90)):
        for x in range(10, w - 20, 46):
            d.arc((x, h * yy, x + 30, h * yy + 8), 200, 340,
                  fill=(150, 200, 235), width=2)


def scene_riyadh(d, w, h):
    """Riyadh at night: PIF Tower struck, drone, fire and smoke."""
    d.rectangle((0, 0, w, h), fill=(12, 18, 46))
    for sx, sy in [(0.06, 0.12), (0.20, 0.07), (0.33, 0.16), (0.55, 0.08),
                   (0.70, 0.14), (0.85, 0.06), (0.93, 0.20), (0.44, 0.05)]:
        d.ellipse((w * sx - 2, h * sy - 2, w * sx + 2, h * sy + 2),
                  fill=(240, 240, 220))
    d.ellipse((w * 0.82, h * 0.10, w * 0.82 + 26, h * 0.10 + 26),
              fill=(235, 228, 200))
    # skyline
    for bx, bw, bh, col in [(0.02, 0.10, 0.55, (38, 52, 88)),
                            (0.14, 0.08, 0.42, (48, 64, 104)),
                            (0.62, 0.09, 0.48, (38, 52, 88)),
                            (0.74, 0.11, 0.58, (48, 64, 104)),
                            (0.88, 0.09, 0.44, (38, 52, 88))]:
        d.rectangle((w * bx, h * (1 - bh), w * (bx + bw), h), fill=col)
        for wy in range(3):
            d.rectangle((w * bx + 4, h * (1 - bh) + 6 + wy * 12,
                         w * bx + 10, h * (1 - bh) + 12 + wy * 12),
                        fill=(250, 214, 120))
    # PIF Tower: tall, tapering, lit crown
    d.polygon([(w * 0.42, h), (w * 0.44, h * 0.08), (w * 0.52, h * 0.08),
               (w * 0.54, h)], fill=(72, 92, 140))
    for wy in range(5):
        d.rectangle((w * 0.455, h * (0.16 + wy * 0.15),
                     w * 0.505, h * (0.16 + wy * 0.15) + 5),
                    fill=(250, 214, 120))
    # fire at the crown + smoke rising, kept inside the frame
    d.polygon([(w * 0.44, h * 0.12), (w * 0.48, h * 0.02),
               (w * 0.52, h * 0.12)], fill=(255, 140, 30))
    for cx, cy, r in [(0.48, 0.22, 10), (0.53, 0.16, 8), (0.44, 0.15, 7)]:
        d.ellipse((w * cx - r, h * cy - r, w * cx + r, h * cy + r),
                  fill=(96, 96, 102))
    # small drone
    d.ellipse((w * 0.66, h * 0.20, w * 0.66 + 8, h * 0.20 + 5),
              fill=(220, 220, 220))
    d.line((w * 0.66 - 4, h * 0.20 + 2, w * 0.66 + 12, h * 0.20 + 2),
           fill=(220, 220, 220), width=1)


def scene_shanghai(d, w, h):
    """Shanghai by day: Oriental Pearl Tower over the Huangpu."""
    d.rectangle((0, 0, w, int(h * 0.72)), fill=(168, 205, 228))
    d.rectangle((0, int(h * 0.72), w, h), fill=(52, 110, 150))
    d.ellipse((w * 0.78, h * 0.08, w * 0.78 + 30, h * 0.08 + 30),
              fill=(250, 240, 190))
    # Jin Mao (stepped) and SWFC (trapezoid top)
    d.polygon([(w * 0.06, h * 0.72), (w * 0.06, h * 0.30),
               (w * 0.10, h * 0.30), (w * 0.10, h * 0.24),
               (w * 0.13, h * 0.24), (w * 0.13, h * 0.18),
               (w * 0.16, h * 0.18), (w * 0.16, h * 0.72)],
              fill=(120, 130, 145))
    d.polygon([(w * 0.68, h * 0.72), (w * 0.68, h * 0.22),
               (w * 0.80, h * 0.22), (w * 0.77, h * 0.12),
               (w * 0.71, h * 0.12), (w * 0.68, h * 0.22)],
              fill=(96, 108, 128))
    # Oriental Pearl Tower: needle with two spheres
    d.line((w * 0.42, h * 0.72, w * 0.42, h * 0.06), fill=(120, 60, 70),
           width=3)
    d.ellipse((w * 0.42 - 12, h * 0.52 - 12, w * 0.42 + 12, h * 0.52 + 12),
              fill=(196, 70, 90))
    d.ellipse((w * 0.42 - 8, h * 0.24 - 8, w * 0.42 + 8, h * 0.24 + 8),
              fill=(196, 70, 90))
    # low blocks + red banner
    d.rectangle((w * 0.22, h * 0.55, w * 0.34, h * 0.72), fill=(150, 150, 155))
    d.rectangle((w * 0.55, h * 0.60, w * 0.64, h * 0.72), fill=(150, 150, 155))
    d.rectangle((w * 0.86, h * 0.50, w * 0.97, h * 0.72), fill=(178, 34, 34))
    d.ellipse((w * 0.90, h * 0.56, w * 0.90 + 10, h * 0.56 + 10),
              fill=(255, 220, 80))
    # river shimmer
    for x in range(8, w - 10, 34):
        d.line((x, h * 0.84, x + 20, h * 0.84), fill=(200, 230, 245),
               width=2)


def scene_zaporizhzhia(d, w, h):
    """Night apartment block, blast hole with orange rim, smoke inside."""
    d.rectangle((0, 0, w, h), fill=(14, 20, 48))
    for sx, sy in [(0.08, 0.10), (0.25, 0.06), (0.55, 0.10), (0.75, 0.05),
                   (0.90, 0.14)]:
        d.ellipse((w * sx - 2, h * sy - 2, w * sx + 2, h * sy + 2),
                  fill=(240, 240, 220))
    d.rectangle((w * 0.10, h * 0.18, w * 0.90, h), fill=(34, 42, 68))
    for r in range(3):
        for c in range(5):
            wx = w * (0.16 + c * 0.15)
            wy = h * (0.26 + r * 0.24)
            d.rectangle((wx, wy, wx + 13, wy + 9), fill=(250, 214, 120))
    hx, hy = int(w * 0.55), int(h * 0.48)
    d.ellipse((hx - 17, hy - 12, hx + 17, hy + 12), fill=(255, 120, 30))
    d.ellipse((hx - 12, hy - 8, hx + 12, hy + 8), fill=(8, 8, 12))
    # smoke curling up from the hole, centres kept below the top edge
    for cx, cy, r in [(0.55, 0.30, 10), (0.60, 0.22, 8), (0.50, 0.24, 7)]:
        d.ellipse((w * cx - r, h * cy - r, w * cx + r, h * cy + r),
                  fill=(120, 120, 126))
    # rubble + rescuers
    d.polygon([(8, h), (40, h - 18), (80, h - 8), (110, h)],
              fill=(110, 106, 100))
    for rx in (0.72, 0.84):
        d.ellipse((w * rx, h * 0.78, w * rx + 9, h * 0.78 + 9),
                  fill=(240, 200, 160))
        d.rectangle((w * rx, h * 0.78 + 9, w * rx + 9, h), fill=(255, 120, 30))


def scene_gaza(d, w, h):
    """Gaza street by day: blocks, blast hole, smoke, rubble slab."""
    d.rectangle((0, 0, w, int(h * 0.60)), fill=(170, 205, 230))
    d.rectangle((0, int(h * 0.60), w, h), fill=(150, 146, 138))
    for bx, bw, bh in [(0.04, 0.22, 0.60), (0.30, 0.26, 0.60),
                       (0.60, 0.20, 0.60), (0.82, 0.16, 0.60)]:
        d.rectangle((w * bx, h * (0.60 - bh * 0.62), w * (bx + bw),
                     h * 0.60), fill=(196, 182, 158))
        for r in range(2):
            for c in range(2):
                d.rectangle((w * bx + 6 + c * 16, h * (0.60 - bh * 0.62) + 7 + r * 13,
                             w * bx + 15 + c * 16, h * (0.60 - bh * 0.62) + 15 + r * 13),
                            fill=(90, 110, 130))
    hx, hy = int(w * 0.44), int(h * 0.34)
    d.ellipse((hx - 16, hy - 11, hx + 16, hy + 11), fill=(255, 120, 30))
    d.ellipse((hx - 11, hy - 7, hx + 11, hy + 7), fill=(8, 8, 12))
    for cx, cy, r in [(0.44, 0.18, 10), (0.49, 0.13, 8), (0.40, 0.15, 7)]:
        d.ellipse((w * cx - r, h * cy - r, w * cx + r, h * cy + r),
                  fill=(96, 96, 100))
    d.polygon([(8, h), (50, h - 16), (110, h - 6), (150, h)],
              fill=(110, 106, 100))
    d.rectangle((w * 0.68, h * 0.82, w * 0.68 + 34, h * 0.82 + 6),
                fill=(178, 34, 34))


def scene_warship(d, w, h):
    """Grey warship, black smoke, orange blast — smoke clipped in-layer."""
    d.rectangle((0, 0, w, int(h * 0.55)), fill=(150, 190, 220))
    for cx, cy, r in [(0.2, 0.16, 9), (0.45, 0.10, 12), (0.75, 0.18, 8)]:
        d.ellipse((w * cx - r, h * cy - r // 2, w * cx + r, h * cy + r // 2),
                  fill=(240, 240, 238))
    d.rectangle((0, int(h * 0.55), w, h), fill=(30, 80, 130))
    for i in range(4):
        yy = int(h * 0.62) + i * 8
        d.arc((10 + i * 40, yy, 50 + i * 40, yy + 8), 200, 340,
              fill=(180, 210, 235), width=2)
    hy = int(h * 0.52)
    d.polygon([(16, hy), (w - 16, hy), (w - 34, hy + 14), (30, hy + 14)],
              fill=(90, 95, 100))
    d.rectangle((w * 0.42, hy - 12, w * 0.48, hy), fill=(70, 75, 80))
    # blast + black smoke rising from the deck, centres inside the layer
    d.polygon([(w * 0.62, hy), (w * 0.68, hy - 22), (w * 0.74, hy)],
              fill=(255, 140, 30))
    for cx, cy, r in [(0.68, 0.30, 11), (0.73, 0.22, 9), (0.63, 0.24, 8)]:
        d.ellipse((w * cx - r, h * cy - r, w * cx + r, h * cy + r),
                  fill=(40, 40, 44))


def scene_sanofi(d, w, h):
    """White pharma building, green cross, coins and a rising chart."""
    d.rectangle((0, 0, w, h), fill=(168, 205, 228))
    d.rectangle((w * 0.08, h * 0.22, w * 0.92, h * 0.78), fill=(245, 245, 240))
    d.rectangle((w * 0.08, h * 0.22, w * 0.92, h * 0.30), fill=(52, 102, 174))
    for c in range(4):
        d.rectangle((w * (0.14 + c * 0.20), h * 0.38,
                     w * (0.14 + c * 0.20) + 16, h * 0.38 + 12),
                    fill=(140, 180, 220))
    d.rectangle((w * 0.44, h * 0.42, w * 0.44 + 8, h * 0.42 + 22),
                fill=(34, 160, 80))
    d.rectangle((w * 0.44 - 7, h * 0.42 + 7, w * 0.44 + 15, h * 0.42 + 15),
                fill=(34, 160, 80))
    d.line([(8, h * 0.86), (w * 0.35, h * 0.70), (w * 0.60, h * 0.76),
            (w - 8, h * 0.55)], fill=(34, 160, 80), width=3)
    for cx in (0.14, 0.24):
        d.ellipse((w * cx - 8, h * 0.82 - 8, w * cx + 8, h * 0.82 + 8),
                  fill=(220, 180, 60))
        d.text((w * cx, h * 0.82), "$", font=f_sans_b(10),
               fill=(120, 90, 20), anchor="mm")


def scene_huawei(d, w, h):
    """Courthouse: pediment, columns, gavel and scales."""
    d.rectangle((0, 0, w, h), fill=(176, 206, 230))
    d.polygon([(w * 0.10, h * 0.34), (w * 0.50, h * 0.08),
               (w * 0.90, h * 0.34)], fill=(196, 182, 158))
    d.ellipse((w * 0.47, h * 0.16, w * 0.53, h * 0.28), fill=(178, 34, 34))
    for c in range(4):
        x = w * (0.16 + c * 0.20)
        d.rectangle((x, h * 0.34, x + 10, h * 0.86), fill=(245, 245, 240))
    d.rectangle((w * 0.08, h * 0.86, w * 0.92, h * 0.94), fill=(120, 110, 96))
    # gavel
    d.line([(w * 0.72, h * 0.55), (w * 0.88, h * 0.42)], fill=(120, 80, 40),
           width=4)
    d.rectangle((w * 0.84, h * 0.36, w * 0.84 + 18, h * 0.36 + 8),
                fill=(90, 60, 30))
    d.ellipse((w * 0.70, h * 0.66, w * 0.70 + 12, h * 0.66 + 5),
              fill=(200, 170, 90))


def scene_iowa(d, w, h):
    """Open field, warning sign, detonation plume behind a fence."""
    d.rectangle((0, 0, w, int(h * 0.55)), fill=(150, 190, 220))
    d.ellipse((w * 0.80, h * 0.08, w * 0.80 + 24, h * 0.08 + 24),
              fill=(250, 230, 140))
    d.rectangle((0, int(h * 0.55), w, h), fill=(126, 150, 80))
    # detonation plume, kept inside the frame
    d.polygon([(w * 0.55, h * 0.55), (w * 0.62, h * 0.18),
               (w * 0.69, h * 0.55)], fill=(255, 140, 30))
    d.polygon([(w * 0.59, h * 0.55), (w * 0.62, h * 0.32),
               (w * 0.65, h * 0.55)], fill=(255, 220, 110))
    for cx, cy, r in [(0.62, 0.22, 9), (0.66, 0.16, 7)]:
        d.ellipse((w * cx - r, h * cy - r, w * cx + r, h * cy + r),
                  fill=(120, 116, 110))
    # fence posts + warning triangle
    for x in range(8, w - 8, 26):
        d.rectangle((x, h * 0.62, x + 3, h * 0.92), fill=(110, 90, 60))
    d.polygon([(w * 0.12, h * 0.52), (w * 0.20, h * 0.30),
               (w * 0.28, h * 0.52)], fill=(250, 210, 40))
    d.text((w * 0.20, h * 0.42), "!", font=f_sans_b(13), fill=(20, 20, 20),
           anchor="mm")


def scene_heat(d, w, h):
    """Big sun, red thermometer, heat haze over dry ground."""
    d.rectangle((0, 0, w, int(h * 0.62)), fill=(250, 214, 140))
    d.rectangle((0, int(h * 0.62), w, h), fill=(198, 158, 90))
    d.ellipse((w * 0.10, h * 0.06, w * 0.10 + 40, h * 0.06 + 40),
              fill=(255, 120, 30))
    for i in range(8):
        ang = i * 3.14159 / 4
        x0 = w * 0.10 + 20 + 26 * math.cos(ang)
        y0 = h * 0.06 + 20 + 26 * math.sin(ang)
        x1 = w * 0.10 + 20 + 34 * math.cos(ang)
        y1 = h * 0.06 + 20 + 34 * math.sin(ang)
        d.line([(x0, y0), (x1, y1)], fill=(255, 120, 30), width=3)
    # thermometer
    d.rounded_rectangle((w * 0.62, h * 0.14, w * 0.62 + 12, h * 0.72),
                        radius=6, fill=(245, 245, 240), outline=(150, 40, 40))
    d.ellipse((w * 0.62 - 2, h * 0.66, w * 0.62 + 14, h * 0.66 + 16),
              fill=(220, 40, 40))
    d.rectangle((w * 0.62 + 4, h * 0.30, w * 0.62 + 8, h * 0.70),
                fill=(220, 40, 40))
    for i in range(3):
        d.arc((w * 0.80 + i * 12, h * 0.30, w * 0.80 + i * 12 + 8,
               h * 0.30 + 22), 270, 90, fill=(178, 34, 34), width=2)


def scene_hanoi(d, w, h):
    """Hanoi street: shophouses, gas flame, rubble, smoke inside frame."""
    d.rectangle((0, 0, w, int(h * 0.62)), fill=(170, 205, 230))
    d.rectangle((0, int(h * 0.62), w, h), fill=(150, 146, 138))
    for bx, bw in [(0.04, 0.24), (0.32, 0.28), (0.64, 0.22), (0.88, 0.10)]:
        d.rectangle((w * bx, h * 0.18, w * (bx + bw), h * 0.62),
                    fill=(196, 182, 158))
        d.rectangle((w * bx + 5, h * 0.28, w * bx + 14, h * 0.28 + 10),
                    fill=(90, 110, 130))
    # gas flame + smoke from the middle shophouse
    d.polygon([(w * 0.40, h * 0.62), (w * 0.46, h * 0.30),
               (w * 0.52, h * 0.62)], fill=(60, 120, 220))
    d.polygon([(w * 0.43, h * 0.62), (w * 0.46, h * 0.42),
               (w * 0.49, h * 0.62)], fill=(255, 220, 110))
    for cx, cy, r in [(0.46, 0.24, 9), (0.50, 0.18, 7), (0.42, 0.19, 6)]:
        d.ellipse((w * cx - r, h * cy - r, w * cx + r, h * cy + r),
                  fill=(110, 110, 114))
    d.polygon([(8, h), (44, h - 14), (90, h - 6), (130, h)],
              fill=(110, 106, 100))


def scene_nepal(d, w, h):
    """Himalayas, red seismograph zigzag, one small house."""
    d.rectangle((0, 0, w, int(h * 0.60)), fill=(170, 205, 230))
    d.ellipse((w * 0.78, h * 0.08, w * 0.78 + 22, h * 0.08 + 22),
              fill=(250, 240, 190))
    d.polygon([(0, h * 0.60), (w * 0.22, h * 0.14), (w * 0.44, h * 0.60)],
              fill=(140, 150, 170))
    d.polygon([(w * 0.16, h * 0.24), (w * 0.22, h * 0.14),
               (w * 0.28, h * 0.24)], fill=(245, 245, 240))
    d.polygon([(w * 0.36, h * 0.60), (w * 0.60, h * 0.08),
               (w * 0.84, h * 0.60)], fill=(110, 122, 148))
    d.polygon([(w * 0.55, h * 0.20), (w * 0.60, h * 0.08),
               (w * 0.65, h * 0.20)], fill=(245, 245, 240))
    d.rectangle((0, int(h * 0.60), w, h), fill=(150, 130, 90))
    # seismograph line
    pts = [(8, h * 0.72), (30, h * 0.72), (40, h * 0.66), (50, h * 0.80),
           (60, h * 0.64), (72, h * 0.82), (84, h * 0.70), (96, h * 0.72),
           (120, h * 0.72), (132, h * 0.66), (144, h * 0.78), (156, h * 0.72),
           (w - 8, h * 0.72)]
    d.line(pts, fill=(220, 40, 40), width=2)
    # house
    d.rectangle((w * 0.70, h * 0.78, w * 0.70 + 22, h * 0.78 + 12),
                fill=(196, 182, 158))
    d.polygon([(w * 0.70 - 3, h * 0.78), (w * 0.70 + 11, h * 0.78 - 9),
               (w * 0.70 + 25, h * 0.78)], fill=(178, 34, 34))


def scene_nvidia(d, w, h):
    """Dark board, green rising chart, big AI tile."""
    d.rectangle((0, 0, w, h), fill=(18, 60, 44))
    for gy in range(4):
        d.line([(0, h * (0.2 + gy * 0.2)), (w, h * (0.2 + gy * 0.2))],
               fill=(34, 96, 70), width=1)
    d.line([(8, h * 0.82), (w * 0.35, h * 0.62), (w * 0.58, h * 0.68),
            (w - 8, h * 0.22)], fill=(120, 220, 90), width=3)
    d.ellipse((w - 16, h * 0.16, w - 8, h * 0.16 + 8), fill=(120, 220, 90))
    d.rectangle((w * 0.30, h * 0.18, w * 0.30 + 52, h * 0.18 + 32),
                fill=(34, 160, 80))
    d.text((w * 0.30 + 26, h * 0.18 + 16), "AI", font=f_sans_b(20),
           fill=(255, 255, 255), anchor="mm")


SCENES = {
    "tanker": scene_tanker, "riyadh": scene_riyadh,
    "shanghai": scene_shanghai, "zaporizhzhia": scene_zaporizhzhia,
    "gaza": scene_gaza, "warship": scene_warship, "sanofi": scene_sanofi,
    "huawei": scene_huawei, "iowa": scene_iowa, "heat": scene_heat,
    "hanoi": scene_hanoi, "nepal": scene_nepal, "nvidia": scene_nvidia,
}


# ---------------------------------------------------------------- page
HERO_X = [(24, 337), (356, 668), (687, 999)]
HERO_TOP, HERO_PIC_BOT, HERO_CAP_BOT, HERO_BOT = 196, 295, 313, 424
CARD_X = [25, 222, 419, 616, 813]
CARD_W, CARD_ROWS, CARD_H, CARD_PIC_H = 185, [430, 563], 130, 68
MAP_BOX = (24, 738, 360, 927)
LIST_X = [376, 688]
LIST_Y0, LIST_DY = 738, 17


def paste_scene(im, key, x0, y0, w, h):
    """Render a scene onto its own layer and paste it masked to its box."""
    layer = Image.new("RGB", (w, h), (255, 255, 255))
    ld = ImageDraw.Draw(layer)
    SCENES[key](ld, w, h)
    im.paste(layer, (x0, y0))


def draw_masthead(d):
    d.rectangle((0, 0, W, 30), fill=NAVY)
    d.text((24, 15), "THE WORLD IN ONE DAY", font=f_sans_b(15),
           fill=(255, 255, 255), anchor="lm")
    d.text((1000, 15),
           "35 STORIES \u00b7 6 REGIONS \u00b7 EVERY ONE DATED "
           "TUESDAY 24 NOVEMBER 2026",
           font=f_sans_b(11), fill=(255, 255, 255), anchor="rm")


def draw_top(d):
    draw_centred(d, 512, 38, "Tuesday 24 November 2026", f_serif_b(58), INK)
    draw_centred(d, 512, 102,
                 "Three tankers hit mines \u00b7 Houthi drone hits Riyadh "
                 "tower \u00b7 China probes Shanghai chief",
                 f_serif_i(16), RED)
    d.line([(24, 123), (1000, 123)], fill=INK, width=1)
    cell_w = (1000 - 24) / 6
    for i, (num, cap) in enumerate(NUMBERS):
        cx = 24 + cell_w * (i + 0.5)
        draw_centred(d, cx, 126, num, f_sans_b(24), RED)
        draw_centred(d, cx, 152, cap, f_sans(10), GREY)
        if i:
            d.line([(24 + cell_w * i, 128), (24 + cell_w * i, 158)],
                   fill=(200, 192, 178), width=1)
    seg_w = (1000 - 24) / 6
    for i, (name, count, col) in enumerate(REGIONS):
        x0 = 24 + seg_w * i
        d.rectangle((x0, 164, x0 + seg_w, 188), fill=col)
        draw_centred(d, x0 + seg_w / 2, 171, "%s %d" % (name, count),
                     f_sans_b(12), (255, 255, 255))


def draw_heroes(im, d):
    for (num, kicker, headline, deck, caption, key), (x0, x1) in zip(
            HEROES, HERO_X):
        w = x1 - x0
        d.rectangle((x0, HERO_TOP, x1, HERO_BOT), fill=CARD)
        paste_scene(im, key, x0, HERO_TOP, w, HERO_PIC_BOT - HERO_TOP)
        d.rectangle((x0, HERO_PIC_BOT, x1, HERO_CAP_BOT), fill=(16, 16, 20))
        d.text((x0 + 8, (HERO_PIC_BOT + HERO_CAP_BOT) / 2), caption,
               font=f_sans(11), fill=(255, 255, 255), anchor="lm")
        d.text((x0 + 8, 320), kicker, font=f_sans_b(12), fill=RED)
        lines = wrap(d, headline, f_sans_b(25), w - 16)
        assert len(lines) == 2, "hero %d headline wraps to %d lines: %r" % (
            num, len(lines), lines)
        y = 336
        for ln in lines:
            d.text((x0 + 8, y), ln, font=f_sans_b(25), fill=INK)
            y += 29
        deck_lines = wrap(d, deck, f_sans(11), w - 16)
        assert len(deck_lines) <= 2, "hero %d deck %d lines" % (
            num, len(deck_lines))
        y = 397
        for ln in deck_lines:
            d.text((x0 + 8, y), ln, font=f_sans(11), fill=INK)
            y += 13
        cx, cy = x1 - 17, 327
        d.ellipse((cx - 11, cy - 11, cx + 11, cy + 11), fill=RED)
        d.text((cx, cy), str(num), font=f_sans_b(13), fill=(255, 255, 255),
               anchor="mm")
        d.rectangle((x0, HERO_TOP, x1, HERO_BOT), outline=INK, width=1)


def draw_cards(im, d):
    for idx, (num, label, headline, place, pcol, key) in enumerate(CARDS):
        row = CARD_ROWS[idx // 5]
        x0 = CARD_X[idx % 5]
        x1, y0 = x0 + CARD_W, row
        d.rectangle((x0, y0, x1, y0 + CARD_H), fill=CARD)
        paste_scene(im, key, x0, y0, CARD_W, CARD_PIC_H)
        tab_w = text_w(d, label, f_sans_b(10)) + 12
        d.rectangle((x0, y0, x0 + tab_w, y0 + 16), fill=RED)
        d.text((x0 + 6, y0 + 8), label, font=f_sans_b(10),
               fill=(255, 255, 255), anchor="lm")
        lines = wrap(d, headline, f_sans_b(13), CARD_W - 16)
        assert len(lines) <= 3, "card %d headline %d lines" % (num,
                                                                len(lines))
        y = y0 + 74
        for ln in lines:
            d.text((x0 + 8, y), ln, font=f_sans_b(13), fill=INK)
            y += 14
        d.text((x0 + 8, y0 + 117), place, font=f_sans_b(10), fill=pcol)
        cx, cy = x1 - 12, y0 + 121
        d.ellipse((cx - 9, cy - 9, cx + 9, cy + 9), fill=RED)
        d.text((cx, cy), str(num), font=f_sans_b(10), fill=(255, 255, 255),
               anchor="mm")
        d.rectangle((x0, y0, x1, y0 + CARD_H), outline=INK, width=1)


def draw_bottom_headers(d):
    d.text((24, 706), "WHERE IT HAPPENED", font=f_sans_b(16), fill=INK)
    d.text((376, 706), "ALSO ON TUESDAY 24 NOVEMBER", font=f_sans_b(16),
           fill=INK)


def draw_map(d):
    x0, y0, x1, y1 = MAP_BOX
    d.rectangle((x0, y0, x1, y1), fill=SEA)
    mx = lambda lon: x0 + (lon + 180) / 360 * (x1 - x0)
    my = lambda lat: y0 + (90 - lat) / 180 * (y1 - y0)
    for poly in CONTINENTS:
        pts = [(mx(lon), my(lat)) for lon, lat in poly]
        d.polygon(pts, fill=LAND, outline=LAND_LINE)
    centres = []
    for num, lon, lat, region, dx, dy in PINS:
        cx, cy = mx(lon) + dx, my(lat) + dy
        centres.append((num, cx, cy))
        d.ellipse((cx - 7, cy - 7, cx + 7, cy + 7),
                  fill=REGION_COLOUR[region], outline=(255, 255, 255),
                  width=1)
        d.text((cx, cy), str(num), font=f_sans_b(8), fill=(255, 255, 255),
               anchor="mm")
    closest = (None, 999.0)
    for (n1, x1a, y1a), (n2, x2a, y2a) in itertools.combinations(centres, 2):
        dist = ((x1a - x2a) ** 2 + (y1a - y2a) ** 2) ** 0.5
        if dist < closest[1]:
            closest = ((n1, n2), dist)
    assert closest[1] >= 15, "pins %s only %.1f px apart" % closest
    print("closest pin pair: %s at %.1f px" % closest)
    # caption pill INSIDE the map, bottom-left over empty South Atlantic sea
    pill_text = "pins match story numbers"
    tw = text_w(d, pill_text, f_serif_i(11))
    px0, py0 = x0 + 8, y1 - 29
    d.rounded_rectangle((px0, py0, px0 + tw + 16, py0 + 18), radius=9,
                        fill=(20, 45, 90))
    d.text((px0 + 8, py0 + 9), pill_text, font=f_serif_i(11),
           fill=(255, 255, 255), anchor="lm")
    d.rectangle((x0, y0, x1, y1), outline=INK, width=1)


def draw_list(d):
    for i, (num, region, text) in enumerate(LIST_ITEMS):
        col = i // 11
        row = i % 11
        x = LIST_X[col]
        y = LIST_Y0 + row * LIST_DY
        d.text((x, y), str(num), font=f_sans_b(11),
               fill=REGION_COLOUR[region])
        line = text
        w = text_w(d, line, f_sans(11))
        assert w <= 306, "list %d too wide: %.1f px: %r" % (num, w, line)
        d.text((x + 20, y), line, font=f_sans(11), fill=INK)


def draw_date_check(d):
    d.rectangle((24, 930, 150, 986), fill=RED)
    d.text((87, 958), "DATE CHECK", font=f_sans_b(12),
           fill=(255, 255, 255), anchor="mm")
    d.rectangle((150, 930, 1000, 986), fill=CARD, outline=RED, width=2)
    lines = wrap(d, DATE_CHECK_TEXT, f_sans(10), 834)
    assert len(lines) == 3, "DATE CHECK wraps to %d lines" % len(lines)
    widths = []
    # 3 lines, 10 px font, 14 px pitch: block height 2*14+10 = 38 px
    # in a 56 px box -> top gap = bottom gap = 9 px (centred).
    y = 939
    top_gap = y - 930
    bottom_gap = 986 - (y + 2 * 14 + 10)
    assert top_gap == bottom_gap, "DATE CHECK not centred: top %d bottom %d" % (top_gap, bottom_gap)
    for ln in lines:
        w = text_w(d, ln, f_sans(10))
        widths.append(round(w, 1))
        assert 740 <= w <= 839, "DATE CHECK line %.1f px: %r" % (w, ln)
        d.text((158, y), ln, font=f_sans(10), fill=INK)
        y += 14
    print("DATE CHECK lines: %s gaps top=%d bottom=%d" % (widths, top_gap, bottom_gap))


def draw_footer(d):
    left = ("Sources: Reuters, AP, BBC, Kyiv Ind., Straits Times, Xinhua, "
            "UKHSA, Sanofi, WHO, ESA, WSJ, NYT, The Hill \u2014 24 Nov 2026")
    right = ("THE WORLD IN ONE DAY \u2014 24 NOVEMBER 2026 \u00b7 "
             "ONE PAGE")
    assert (text_w(d, left, f_sans(10)) + text_w(d, right, f_sans_b(10))
            <= 966), "footer too wide"
    d.text((24, 996), left, font=f_sans(10), fill=GREY)
    d.text((1000, 996), right, font=f_sans_b(10), fill=INK, anchor="ra")


def check_bands(im):
    """No illustration ink may sit in the cream bands above any box."""
    px = im.load()

    def non_paper(x, y):
        r, g, b = px[x, y]
        return max(abs(r - PAPER[0]), abs(g - PAPER[1]),
                   abs(b - PAPER[2])) > 25

    bands = [("heroes", 24, 1000, 189, 196),
             ("cards row 1", 24, 1000, 425, 430),
             ("cards row 2", 24, 1000, 561, 563)]
    for name, x0, x1, ya, yb in bands:
        n = sum(1 for y in range(ya, yb) for x in range(x0, x1)
                if non_paper(x, y))
        print("band %s: %d non-paper px" % (name, n))
        assert n == 0, "band %s has %d stray px" % (name, n)


def main():
    im = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(im)
    assert sum(c for _, c, _ in REGIONS) == 35, "region bar must total 35"
    draw_masthead(d)
    draw_top(d)
    draw_heroes(im, d)
    draw_cards(im, d)
    draw_bottom_headers(d)
    draw_map(d)
    draw_list(d)
    draw_date_check(d)
    draw_footer(d)
    check_bands(im)
    im.save(OUT)
    print("saved %s %dx%d" % (OUT, W, H))


if __name__ == "__main__":
    main()
