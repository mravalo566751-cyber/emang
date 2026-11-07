"""
for emang - a vintage animated love letter (menu page + songs / message / photo pages)

Run:   python love_letter.py
Needs: pip install pillow numpy pygame     (tkinter ships with Python on Windows/macOS;
                                      on Linux: sudo apt install python3-tk)
Keep the 'assets' folder next to this file. It needs:
    letter.png, cat1.png ... cat6.png          (from Part 1)
    paper.png, photo.png, flowers.png,
    butterfly.png, candle.png                  (cut from your design sheet)
    icon_songs.png, icon_message.png, icon_photo.png   (the three menu stickers)
    

Runs FULLSCREEN.  Click the letter to open it.  Click anywhere else for hearts.
Press Esc (or Q) to quit.

Music: put your MP3 in the 'assets' folder (or next to this file) and set MUSIC_FILE
below. It starts automatically and loops until the app is closed. The little record
player (bottom-left) can pause / resume it.   Needs:  pip install pygame
"""
import math
import os
import random
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets")

W, H = 1280, 720          # logical canvas (W is adapted to your screen at launch)
FPS = 30

# ---- words you can edit ------------------------------------------------------
TEXT = "HAPPY BIRTHDAY"
SUBTITLE = "~ for emang ~"
HINT = "~ click the letter to open it ~"

GREETING = "haii, emang!"
BODY = ("hehe, soo cute jud kaayo sa imong nickname. happy birthday puu!\n\n"
        "kabalo ka, l honestly don\u2019t know what to say because i\u2019m just so thankful nga nakaila tika ganda-gandah mo puu. "
        "I don\u2019t know how to explain this feeling, but whenever i\u2019m with you, I feel happy, comfortable, and at peace. "
        "it\u2019s like I can just be myself without having to pretend to be someone else. "
        "you have this kind of presence nga bisan simple moments lang, you somehow make me special.\n\n"
        "and you know what? Every time I hear the song \u201cParaluman,\u201d ikaw jud akong mahinumduman. "
        "I don\u2019t know why, but something about that song reminds me of you. "
        "siguro it\u2019s the way the song makes everything feel soft, warm, and beautiful. just like how I see you. "
        "it\u2019s funny how a song can suddenly remind you of someone, and for me, that someone is you. "
        "maybe someday, whenever you hear that song, I hope you\u2019ll remember me too.\n\n"
        "i\u2019m really glad that our paths crossed. I never expected nga you\u2019d become someone this special to me, "
        "but I\u2019m genuinely happy that I got to know you. "
        "thank you for making me smile, for the little moments, and for simply being you.\n\n"
        "on your special day, I wish you genuine happiness, good health, peace of mind, and all the beautiful things life has to offer. "
        "I hope you achieve everything you\u2019re wishing and praying for. "
        "I hope life treats you kindly, and whenever things get difficult, I hope you never forget how much you are worth.\n\n"
        "I don\u2019t know what the future holds, but I\u2019m happy that I get to know you and share these little moments with you. "
        "I hope I can make you feel as special as you make me feel.\n\n"
        "enjoy your day, emang! keep that beautiful smile, and please stay the way you are. "
        "i\u2019m always rooting for you. happy birthday once again! "
        "i\u2019m  really lucky that somehow, out of all the people in this world, I got to meet you.")
SIGN = ""                 # optional sign-off shown after the last page (e.g. "Forever yours")
BODY_CPS = 45             # typing speed of the letter body (characters per second)

KEEP_CATS = False         # True = cats keep floating in the back after the letter opens

MUSIC_FILE = "music.mp3"  # your MP3 (looked up in 'assets' or next to this file)
MUSIC_VOLUME = 0.5        # 0.0 - 1.0
MUSIC_LABEL = "Paraluman - Adie"  # small text shown on the player
MUSIC_COVER = "portrait.png"      # picture shown on the spinning record (songs page); "" = plain disc

# ---- DVD orbiting the photo ----------------------------------------------
DVD_SIZE = 110            # disc diameter in pixels
DVD_SPEED = 1.0           # how fast it circles the portrait
DVD_TILT = -14            # tilt (degrees) of the orbit loop
DVD_SPIN = 240            # degrees per second the disc spins on its own axis
DVD_ORBIT_PAD = 45         # how far the orbit extends past the portrait's edges
DVD_ONLY_WHEN_PLAYING = False   # True = disc spins only while the music plays


# ---- menu page (the three sticker buttons) -----------------------------------
MENU_ITEMS = ("songs", "message", "photo")   # needs assets/icon_songs.png, icon_message.png, icon_photo.png
MENU_HINT = "~ pick puu🙈 ~"
MENU_DARK = False         # False = menu on the parchment background (like the first page); True = walnut
PHOTO_FILES = ["photo.png"]   # photos shown on the photo page - add more names, e.g. ["photo.png", "photo2.png"]
LABEL_FONTS = ["Poppins", "Nunito", "Quicksand", "Comfortaa", "Segoe UI", "Trebuchet MS",
               "Helvetica Neue", "Arial"]   # first one installed is used for the button text

# ---- vintage palette -------------------------------------------------------
INK = (92, 54, 38)
INK_SOFT = (140, 100, 74)
GOLD = (176, 132, 62)
WAX = (160, 40, 40)
PARCHMENT = (240, 215, 168)
WALNUT = (84, 55, 40)

SCRIPT_FONTS = [
    "Monotype Corsiva", "Apple Chancery", "Segoe Script", "Lucida Handwriting",
    "Edwardian Script ITC", "Palace Script MT", "Brush Script MT",
    "Snell Roundhand", "URW Chancery L", "Z003", "Georgia", "Palatino Linotype",
    "Times New Roman",
]


def clamp01(x):
    return max(0.0, min(1.0, x))


def ease_out_back(x):
    x = clamp01(x)
    c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2


def ease_out_cubic(x):
    x = clamp01(x)
    return 1 - (1 - x) ** 3


def smooth(x):
    x = clamp01(x)
    return x * x * (3 - 2 * x)


# ---- background ------------------------------------------------------------
def make_background(dark=False):
    rng = np.random.default_rng(7)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    cx, cy = W / 2, H / 2
    d = np.sqrt(((xx - cx) / (W / 2)) ** 2 + ((yy - cy) / (H / 2)) ** 2)

    base = np.zeros((H, W, 3), np.float32)
    base[...] = WALNUT if dark else PARCHMENT          # aged parchment / old walnut
    base *= (1.06 - 0.30 * np.clip(d - 0.35, 0, 1.2) ** 1.6)[..., None]  # vignette

    # mottled stains + fine grain
    blotch = Image.fromarray((rng.random((H // 40 + 1, W // 40 + 1)) * 255).astype("uint8"))
    blotch = np.asarray(blotch.resize((W, H), Image.BICUBIC), np.float32) / 255
    base *= (0.93 + 0.12 * blotch)[..., None]
    base += rng.normal(0, 4.5, (H, W, 1))
    # faint fibres
    fib = Image.new("L", (W, H), 0)
    fd = ImageDraw.Draw(fib)
    for _ in range(int(260 * W / 1100)):
        x, y = rng.integers(0, W), rng.integers(0, H)
        a = rng.random() * math.pi
        l = rng.integers(8, 30)
        fd.line([x, y, x + math.cos(a) * l, y + math.sin(a) * l], fill=int(rng.integers(20, 60)))
    fibv = np.asarray(fib.filter(ImageFilter.GaussianBlur(0.6)), np.float32) / 6
    base += (fibv if dark else -fibv)[..., None]

    img = Image.fromarray(np.clip(base, 0, 255).astype("uint8"), "RGB")

    # double-line border with corner ornaments
    dr = ImageDraw.Draw(img)
    m1, m2 = 22, 32
    line2 = (190, 150, 92) if dark else INK_SOFT
    dr.rectangle([m1, m1, W - m1, H - m1], outline=GOLD, width=3)
    dr.rectangle([m2, m2, W - m2, H - m2], outline=line2, width=1)
    for (x, y, sx, sy) in [(m2, m2, 1, 1), (W - m2, m2, -1, 1),
                           (m2, H - m2, 1, -1), (W - m2, H - m2, -1, -1)]:
        for r in (16, 10, 4):
            dr.arc([x + (r if sx > 0 else -r) - r,
                    y + (r if sy > 0 else -r) - r,
                    x + (r if sx > 0 else -r) + r,
                    y + (r if sy > 0 else -r) + r],
                   0, 360, fill=GOLD, width=1)
        dr.ellipse([x + sx * 16 - 3, y + sy * 16 - 3, x + sx * 16 + 3, y + sy * 16 + 3], fill=GOLD)
    return img


# ---- small drawn hearts / sparkles ----------------------------------------
def heart_sprite(size, color):
    s = size * 4
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    pts = []
    for i in range(120):
        t = i / 120 * 2 * math.pi
        x = 16 * math.sin(t) ** 3
        y = -(13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t))
        pts.append((s / 2 + x * s / 38, s / 2 + y * s / 38 - s * 0.03))
    d.polygon(pts, fill=color + (255,))
    d.line(pts + [pts[0]], fill=(255, 245, 225, 120), width=max(2, s // 30))
    return im.resize((size, size), Image.LANCZOS)


def sparkle_sprite(size, color):
    s = size * 4
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = s / 2
    d.polygon([(c, 0), (c + s * 0.09, c - s * 0.09), (s, c), (c + s * 0.09, c + s * 0.09),
               (c, s), (c - s * 0.09, c + s * 0.09), (0, c), (c - s * 0.09, c - s * 0.09)],
              fill=color + (255,))
    return im.resize((size, size), Image.LANCZOS)


def warm_glow(size, color=(255, 196, 112)):
    """Soft radial candle light."""
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)
    r = np.sqrt(((xx - size / 2) / (size / 2)) ** 2 + ((yy - size / 2) / (size / 2)) ** 2)
    a = np.clip(1 - r, 0, 1) ** 2.2
    arr = np.zeros((size, size, 4), np.uint8)
    arr[..., 0], arr[..., 1], arr[..., 2] = color
    arr[..., 3] = (a * 255).astype(np.uint8)
    return Image.fromarray(arr, "RGBA")


def shadow_of(sprite, blur=8, opacity=95, color=(60, 35, 20)):
    pad = blur * 3
    a = Image.new("L", (sprite.width + pad * 2, sprite.height + pad * 2), 0)
    a.paste(sprite.getchannel("A"), (pad, pad))
    a = a.filter(ImageFilter.GaussianBlur(blur)).point(lambda v: v * opacity // 255)
    sh = Image.new("RGBA", a.size, color + (0,))
    sh.putalpha(a)
    return sh, pad


def with_alpha(sprite, k):
    if k >= 0.995:
        return sprite
    s = sprite.copy()
    s.putalpha(s.getchannel("A").point(lambda v: int(v * k)))
    return s


def clip_composite(canvas, sp, x, y):
    """alpha_composite that tolerates sprites hanging off the canvas edge."""
    x, y = int(x), int(y)
    l, t = max(0, x), max(0, y)
    r, b = min(canvas.width, x + sp.width), min(canvas.height, y + sp.height)
    if r <= l or b <= t:
        return
    canvas.alpha_composite(sp.crop((l - x, t - y, r - x, b - y)), (l, t))


def load_asset(name):
    path = os.path.join(ASSETS, name)
    if not os.path.exists(path):
        sys.exit(f"Missing asset: {path}\nKeep the 'assets' folder next to love_letter.py.")
    return Image.open(path).convert("RGBA")


def make_polaroid(photo, height):
    """Photo is only RESIZED - never retouched. A cream frame + tape is added around it."""
    pw = int(photo.width * height / photo.height)
    pic = photo.resize((pw, height), Image.LANCZOS)
    pad, bottom, top = 13, 42, 26
    fw, fh = pw + 2 * pad, height + pad + bottom
    rng = np.random.default_rng(3)
    arr = np.zeros((fh, fw, 4), np.float32)
    arr[..., :3] = (247, 240, 224)
    arr[..., 3] = 255
    arr[..., :3] += rng.normal(0, 3, (fh, fw, 1))
    frame = Image.fromarray(np.clip(arr, 0, 255).astype("uint8"), "RGBA")
    frame.paste(pic, (pad, pad))
    d = ImageDraw.Draw(frame)
    d.rectangle([0, 0, fw - 1, fh - 1], outline=(205, 190, 160, 255), width=2)
    hs = heart_sprite(24, (170, 60, 60))
    frame.alpha_composite(hs, (fw // 2 - 12, height + pad + (bottom - 24) // 2))

    out = Image.new("RGBA", (fw, fh + top), (0, 0, 0, 0))
    out.alpha_composite(frame, (0, top))
    for cx_, ang in ((fw // 2, -4),):
        tape = Image.new("RGBA", (118, 34), (226, 205, 150, 175))
        td = ImageDraw.Draw(tape)
        for i in range(0, 34, 4):
            td.line([0, i, 118, i], fill=(210, 188, 134, 60))
        tape = tape.rotate(ang, expand=True, resample=Image.BICUBIC)
        out.alpha_composite(tape, (cx_ - tape.width // 2, top - tape.height // 2 + 4))
    return out


# ---- scene objects ---------------------------------------------------------
class Floater:
    """A cat sticker drifting around the letter."""

    def __init__(self, img, anchor, height, layer, delay, rng):
        self.base = img
        self.anchor = anchor
        self.layer = layer                    # 0 = behind letter, 1 = in front
        self.delay = delay
        self.h = height
        self.ph = [rng.uniform(0, 6.28) for _ in range(4)]
        self.sp = [rng.uniform(0.5, 1.1), rng.uniform(0.4, 0.9), rng.uniform(0.5, 0.9)]
        self.amp = (rng.uniform(14, 30), rng.uniform(14, 30))
        self.tilt = rng.uniform(7, 14) * rng.choice([-1, 1])
        self.cache = {}

    def _sprite(self, scale, ang):
        key = (round(scale * 40), round(ang / 2))
        if key not in self.cache:
            w = max(8, int(self.base.width * self.h / self.base.height * scale))
            h = max(8, int(self.h * scale))
            sp = self.base.resize((w, h), Image.LANCZOS).rotate(
                key[1] * 2, resample=Image.BICUBIC, expand=True)
            sh, pad = shadow_of(sp, 6, 90)
            self.cache[key] = (sp, sh, pad)
            if len(self.cache) > 400:
                self.cache.pop(next(iter(self.cache)))
        return self.cache[key]

    def draw(self, canvas, t, vis=1.0):
        local = t - self.delay
        if local <= 0 or vis <= 0.02:
            return
        pop = ease_out_back(local / 0.9)
        x = self.anchor[0] + self.amp[0] * math.sin(t * self.sp[0] + self.ph[0])
        y = self.anchor[1] + self.amp[1] * math.sin(t * self.sp[1] + self.ph[1]) \
            + 6 * math.sin(t * 2.1 + self.ph[3])
        ang = self.tilt * math.sin(t * self.sp[2] + self.ph[2])
        scale = max(0.02, pop) * (1 + 0.03 * math.sin(t * 1.7 + self.ph[3])) * vis
        sp, sh, pad = self._sprite(max(0.03, scale), ang)
        clip_composite(canvas, sh, x - sh.width / 2 + 7, y - sh.height / 2 + 10)
        clip_composite(canvas, sp, x - sp.width / 2, y - sp.height / 2)


class Prop:
    """A decoration of the opened letter: enters with a bounce, then drifts gently."""

    def __init__(self, img, height, home, delay, enter=(0, 0), dur=1.1, drift=(0, 0),
                 tilt=0.0, base_ang=0.0, speed=1.0, flap=False, seed=0, ang_q=0.5):
        self.base, self.h, self.home, self.delay = img, height, home, delay
        self.enter, self.dur, self.drift = enter, dur, drift
        self.tilt, self.base_ang, self.speed, self.flap = tilt, base_ang, speed, flap
        self.ang_q = ang_q
        r = random.Random(seed)
        self.ph = [r.uniform(0, 6.28) for _ in range(4)]
        self.cache = {}
        self.rect = None           # (cx, cy, w, h) of last drawn sprite
        self.vis = 0.0

    def _sprite(self, scale, ang, fx):
        key = (round(scale * 40), round(ang / self.ang_q), round(fx * 6))
        if key not in self.cache:
            w = max(8, int(self.base.width * self.h / self.base.height * scale * (key[2] / 6)))
            h = max(8, int(self.h * scale))
            sp = self.base.resize((w, h), Image.LANCZOS).rotate(
                key[1] * self.ang_q, resample=Image.BICUBIC, expand=True)
            sh, pad = shadow_of(sp, 6, 95)
            self.cache[key] = (sp, sh)
            if len(self.cache) > 500:
                self.cache.pop(next(iter(self.cache)))
        return self.cache[key]

    def draw(self, canvas, u):
        local = u - self.delay
        if local <= 0:
            self.rect, self.vis = None, 0.0
            return
        k = local / self.dur
        pop = ease_out_back(k)
        scale = 0.55 + 0.45 * ease_out_cubic(k)
        t = u * self.speed
        x = self.home[0] + self.enter[0] * (1 - pop) \
            + self.drift[0] * (math.sin(0.9 * t + self.ph[0]) + 0.3 * math.sin(2.3 * t + self.ph[1]))
        y = self.home[1] + self.enter[1] * (1 - pop) \
            + self.drift[1] * (math.sin(0.7 * t + self.ph[1]) + 0.3 * math.sin(1.9 * t + self.ph[2]))
        ang = self.base_ang + self.tilt * math.sin(1.1 * t + self.ph[2])
        fx = 1.0
        if self.flap:
            fx = 0.70 + 0.30 * abs(math.sin(u * 7.5 + self.ph[3]))
        sp, sh = self._sprite(scale, ang, fx)
        clip_composite(canvas, sh, x - sh.width / 2 + 7, y - sh.height / 2 + 10)
        clip_composite(canvas, sp, x - sp.width / 2, y - sp.height / 2)
        self.rect = (x, y, sp.width, sp.height)
        self.vis = clamp01(local / 0.4)


class Particle:
    def __init__(self, sprite, x, y, vx, vy, life, sway=0.0, spin=0.0):
        self.sprite, self.x, self.y, self.vx, self.vy = sprite, x, y, vx, vy
        self.life, self.age, self.sway, self.spin = life, 0.0, sway, spin
        self.ph = random.uniform(0, 6.28)


# ---- orbiting DVD ------------------------------------------------------------
def dvd_sprite(size):
    """Silver DVD with a rainbow sheen, so the spin is visible."""
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)
    c = (size - 1) / 2
    dx, dy = xx - c, yy - c
    r = np.sqrt(dx ** 2 + dy ** 2) / (size / 2)
    ang = np.arctan2(dy, dx)
    silver = 190 + 45 * np.sin(3 * ang)
    rainbow = 0.5 + 0.5 * np.cos(2 * ang[..., None] + np.array([0, 2.1, 4.2]))
    rgb = silver[..., None] * 0.72 + rainbow * 255 * 0.28
    rgb[r < 0.34] = rgb[r < 0.34] * 0.55 + 120          # clear hub ring
    rgb[r > 0.965] *= 0.6                               # dark rim
    px = size / 2
    a = np.clip((1 - r) * px, 0, 1) * np.clip((r - 0.12) * px, 0, 1)
    arr = np.dstack([np.clip(rgb, 0, 255), a * 255]).astype(np.uint8)
    return Image.fromarray(arr, "RGBA")


def record_sprite(size, photo):
    """Black vinyl record with the photo as its round label (so the picture spins with the music)."""
    S = 2
    n = size * S
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    c = (n - 1) / 2
    r = np.sqrt((xx - c) ** 2 + (yy - c) ** 2) / (n / 2)
    ang = np.arctan2(yy - c, xx - c)
    base = 26 + 12 * (0.5 + 0.5 * np.sin(r * 170))                   # fine grooves
    base = base + np.clip(np.cos(2 * ang), 0, 1) ** 8 * 38 * (r > 0.62)   # light sheen
    rgb = np.dstack([base, base * 0.93, base * 0.88])
    a = np.clip((1 - r) * n / 2, 0, 1)
    vinyl = Image.fromarray(np.dstack([np.clip(rgb, 0, 255), a * 255]).astype(np.uint8), "RGBA")

    ld = int(n * 0.62)
    side = min(photo.size)
    l, t = (photo.width - side) // 2, (photo.height - side) // 2
    pic = photo.crop((l, t, l + side, t + side)).resize((ld, ld), Image.LANCZOS).convert("RGBA")
    mask = Image.new("L", (ld, ld), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, ld - 1, ld - 1], fill=255)
    off = (n - ld) // 2
    vinyl.paste(pic, (off, off), mask)
    d = ImageDraw.Draw(vinyl)
    d.ellipse([off, off, off + ld - 1, off + ld - 1], outline=GOLD + (255,), width=S * 3)
    hr = n * 0.028
    d.ellipse([c - hr, c - hr, c + hr, c + hr], fill=(232, 205, 156, 255), outline=INK + (255,), width=S)
    return vinyl.resize((size, size), Image.LANCZOS)


class OrbitDVD:
    """A DVD that spins while circling a target rectangle (behind it, then in front)."""

    def __init__(self, size=110, delay=4.4, speed=1.0, tilt=-14, spin=240, src=None):
        self.src = src if src is not None else dvd_sprite(size * 2)
        self.size, self.delay, self.speed, self.spin = size, delay, speed, spin
        self.tilt = math.radians(tilt)
        self.cache = {}
        self.spin_angle = 0.0
        self.last_u = None

    def _sprite(self, scale, spin):
        key = (round(scale * 30), int(spin // 6) % 60)
        if key not in self.cache:
            d = max(8, int(self.size * key[0] / 30))
            sp = self.src.resize((d, d), Image.LANCZOS).rotate(-key[1] * 6, resample=Image.BICUBIC)
            self.cache[key] = (sp, shadow_of(sp, 5, 90)[0])
            if len(self.cache) > 300:
                self.cache.pop(next(iter(self.cache)))
        return self.cache[key]

    def update(self, u, spinning=True):
        """Advance the self-spin once per frame (call before the draw calls)."""
        if self.last_u is not None and spinning:
            self.spin_angle += self.spin * max(0.0, min(0.1, u - self.last_u))
        self.last_u = u

    def draw(self, canvas, u, rect, front):
        if rect is None:
            return
        local = u - self.delay
        if local <= 0:
            return
        cx, cy, w, h = rect
        th = local * self.speed * 1.6
        depth = math.sin(th)
        if (depth >= 0) != front:
            return
        ex, ey = (w * 0.5 + DVD_ORBIT_PAD) * math.cos(th), (h * 0.5 + 30) * 0.55 * depth
        x = cx + ex * math.cos(self.tilt) - ey * math.sin(self.tilt)
        y = cy + ex * math.sin(self.tilt) + ey * math.cos(self.tilt)
        scale = (0.85 + 0.15 * depth) * max(0.05, ease_out_back(local / 1.0))
        sp, sh = self._sprite(scale, self.spin_angle)
        clip_composite(canvas, sh, x - sh.width / 2 + 6, y - sh.height / 2 + 9)
        clip_composite(canvas, sp, x - sp.width / 2, y - sp.height / 2)


# ---- Spotify mini player -----------------------------------------------------
class MusicControl:
    """Background music on a loop.
    1) pygame.mixer if it is installed and can read the file;
    2) otherwise, on Windows, the built-in MCI player (no install needed, plays MP3)."""
    EXTS = (".mp3", ".ogg", ".wav", ".flac")

    def __init__(self, filename, volume=0.5):
        self.playing = False
        self.ok = False
        self.pg = None
        self.mci = False
        self.volume = volume
        self.error = ""
        self.path = self._find(filename)
        if not self.path:
            self.error = f"no audio file found (looked for '{filename}' in {ASSETS} and {HERE})"
            print(f"[music] {self.error}")
            return
        print(f"[music] python: {sys.executable}")
        print(f"[music] file:   {self.path}")

        # --- try pygame first
        try:
            import pygame
            if not pygame.mixer.get_init():
                try:
                    pygame.mixer.init()
                except Exception:
                    pygame.mixer.quit()
                    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
            pygame.mixer.music.load(self.path)
            pygame.mixer.music.set_volume(volume)
            self.pg, self.ok = pygame, True
            print("[music] using pygame")
            return
        except ImportError:
            self.error = (f"pygame is not installed for THIS python. Run:  "
                          f"\"{sys.executable}\" -m pip install pygame")
        except Exception as e:
            self.error = f"pygame could not load the file: {e}"
        print(f"[music] {self.error}")

        # --- fallback: Windows MCI (no extra install)
        if os.name == "nt":
            try:
                self._mci_open()
                self.ok, self.mci = True, True
                print("[music] using the Windows built-in player instead")
            except Exception as e:
                self.error += f"  | Windows player failed too: {e}"
                print(f"[music] {self.error}")

    # ---- Windows MCI helpers
    def _mci(self, cmd):
        import ctypes
        buf = ctypes.create_unicode_buffer(255)
        err = ctypes.windll.winmm.mciSendStringW(cmd, buf, 254, 0)
        if err:
            msg = ctypes.create_unicode_buffer(255)
            ctypes.windll.winmm.mciGetErrorStringW(err, msg, 254)
            raise RuntimeError(f"{msg.value} (MCI error {err}) for: {cmd}")
        return buf.value

    def _mci_open(self):
        self._mci("close bgm") if False else None
        self._mci(f'open "{self.path}" type mpegvideo alias bgm')
        try:
            self._mci(f"setaudio bgm volume to {int(self.volume * 1000)}")
        except Exception:
            pass

    def _find(self, filename):
        """Exact name first, then the same name with other extensions, then any audio file."""
        if os.path.isabs(filename) and os.path.exists(filename):
            return filename
        stem = os.path.splitext(filename)[0]
        for base in (ASSETS, HERE):
            p = os.path.join(base, filename)
            if os.path.exists(p):
                return p
        for base in (ASSETS, HERE):
            for ext in self.EXTS:
                p = os.path.join(base, stem + ext)
                if os.path.exists(p):
                    return p
        for base in (ASSETS, HERE):                      # last resort: first audio file found
            if os.path.isdir(base):
                for f in sorted(os.listdir(base)):
                    if f.lower().endswith(self.EXTS):
                        return os.path.join(base, f)
        return None

    def start(self):
        if not self.ok:
            return
        try:
            if self.mci:
                self._mci("play bgm repeat")
            else:
                self.pg.mixer.music.play(loops=-1)          # -1 = loop forever
            self.playing = True
        except Exception as e:
            self.error = f"could not play: {e}"
            print(f"[music] {self.error}")

    def press(self, name):
        if not self.ok:
            print(f"[music] not available: {self.error}")
            return
        try:
            if self.mci:
                self._mci("pause bgm" if self.playing else "resume bgm")
            elif self.playing:
                self.pg.mixer.music.pause()
            else:
                self.pg.mixer.music.unpause()
            self.playing = not self.playing
        except Exception as e:
            print(f"[music] {e}")

    def stop(self):
        if not self.ok:
            return
        try:
            if self.mci:
                self._mci("stop bgm")
                self._mci("close bgm")
            else:
                self.pg.mixer.music.stop()
                self.pg.mixer.quit()
        except Exception:
            pass


class PlayerCard:
    """Small brass-and-parchment record player, bottom-left."""
    X0, Y0, CW, CH = 52, H - 52 - 60, 188, 60
    BTN = {"play": (96, 41)}                                          # relative to card
    LABEL_POS = (62, 17)                                              # relative to card

    def __init__(self, ctrl):
        self.ctrl = ctrl
        self.enabled = True
        self.angle = 0.0
        self.last = 0.0
        self.disc_src = self._disc()
        self.disc_cache = {}
        self.base = {}
        for playing in (False, True):
            img = self._build(playing)
            self.base[playing] = (img,) + shadow_of(img, 5, 90)

    def alpha(self, t):
        return smooth((t - 4.6) / 1.0)

    def _build(self, playing):
        S = 4
        w, h = self.CW * S, self.CH * S
        im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.rounded_rectangle([S, S, w - S, h - S], radius=10 * S,
                            fill=(232, 205, 156, 240), outline=GOLD, width=2 * S)
        d.rounded_rectangle([5 * S, 5 * S, w - 5 * S, h - 5 * S], radius=7 * S,
                            outline=INK_SOFT, width=S // 2)
        d.ellipse([(32 - 24) * S, (30 - 24) * S, (32 + 24) * S, (30 + 24) * S],
                  outline=GOLD, width=S)
        ink = INK + (255,)

        def poly(pts):
            d.polygon([(x * S, y * S) for x, y in pts], fill=ink)

        def rect(x0, y0, x1, y1):
            d.rectangle([x0 * S, y0 * S, x1 * S, y1 * S], fill=ink)

        cx, cy = self.BTN["play"]
        d.ellipse([(cx - 11) * S, (cy - 11) * S, (cx + 11) * S, (cy + 11) * S],
                  fill=(244, 224, 184, 255), outline=GOLD, width=int(1.5 * S))
        if playing:
            rect(cx - 4.5, cy - 5, cx - 1.5, cy + 5)
            rect(cx + 1.5, cy - 5, cx + 4.5, cy + 5)
        else:
            poly([(cx - 3, cy - 5.5), (cx + 5.5, cy), (cx - 3, cy + 5.5)])
        return im.resize((self.CW, self.CH), Image.LANCZOS)

    @staticmethod
    def _disc():
        S, size = 4, 44
        n = size * S
        im = Image.new("RGBA", (n, n), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.ellipse([0, 0, n - 1, n - 1], fill=(38, 26, 22, 255))
        for k in range(5):
            r = n / 2 * (0.98 - k * 0.09)
            d.ellipse([n / 2 - r, n / 2 - r, n / 2 + r, n / 2 + r],
                      outline=(66, 48, 40, 255), width=S // 2)
        d.arc([n * .1, n * .1, n * .9, n * .9], 200, 250, fill=(135, 108, 90, 255), width=2 * S)
        d.arc([n * .1, n * .1, n * .9, n * .9], 20, 70, fill=(135, 108, 90, 255), width=2 * S)
        r = n * 0.30
        d.ellipse([n / 2 - r, n / 2 - r, n / 2 + r, n / 2 + r],
                  fill=WAX + (255,), outline=GOLD + (255,), width=S)
        d.ellipse([n / 2 + n * .17 - n * .035, n / 2 - n * .035,
                   n / 2 + n * .17 + n * .035, n / 2 + n * .035], fill=GOLD + (255,))
        hr = n * 0.04
        d.ellipse([n / 2 - hr, n / 2 - hr, n / 2 + hr, n / 2 + hr], fill=(232, 205, 156, 255))
        return im.resize((size, size), Image.LANCZOS)

    def hit(self, x, y, t):
        if not self.enabled or t < 5.0:
            return None
        for name, (bx, by) in self.BTN.items():
            rad = 14 if name == "play" else 12
            if (x - self.X0 - bx) ** 2 + (y - self.Y0 - by) ** 2 <= rad ** 2:
                return name
        return None

    def press(self, name):
        self.ctrl.press(name)

    def draw(self, canvas, t):
        dt = max(0.0, min(0.1, t - self.last))
        self.last = t
        playing = self.ctrl.playing
        if playing:
            self.angle = (self.angle + 130 * dt) % 360
        a = self.alpha(t)
        if a <= 0.01:
            return
        base, sh, pad = self.base[playing]
        card = base.copy()

        k = int(self.angle // 6) % 60
        if k not in self.disc_cache:
            self.disc_cache[k] = self.disc_src.rotate(-k * 6, resample=Image.BICUBIC)
        card.alpha_composite(self.disc_cache[k], (10, 8))

        bars = ImageDraw.Draw(card)                       # tiny equalizer
        for i in range(3):
            hgt = 3 + (7 * (0.5 + 0.5 * math.sin(t * (5.5 + i * 1.7) + i * 2.0)) if playing else 0)
            bx = self.CW - 30 + i * 6
            bars.rectangle([bx, 24 - hgt, bx + 3, 24],
                           fill=(GOLD if playing else INK_SOFT) + (255,))

        clip_composite(canvas, with_alpha(sh, a), self.X0 - pad + 3, self.Y0 - pad + 5)
        clip_composite(canvas, with_alpha(card, a), self.X0, self.Y0)


class Scene:
    def __init__(self):
        rng = random.Random(11)
        self.rng = rng
        self.bg_light = make_background().convert("RGBA")
        self.bg_dark = make_background(dark=True).convert("RGBA")

        # ---------------- Part 1 : closed letter + cats
        letter = load_asset("letter.png")
        lw = 540
        self.letter = letter.resize((lw, int(letter.height * lw / letter.width)), Image.LANCZOS)
        self.letter_center = (W / 2, 418)
        self.seal_frac = (0.523, 0.600)
        self.letter_cache = {}
        self.letter_rect = (0, 0, 0, 0)

        cats = [load_asset(f"cat{i}.png") for i in range(1, 7)]
        dx = (W - 1100) / 2
        # (cat index, anchor x, y, height, layer, delay)
        layout = [
            (1, 70, 330, 120, 0, 0.9), (4, 1035, 345, 125, 0, 1.05),
            (2, 235, 420, 140, 0, 0.7), (5, 870, 430, 140, 0, 0.8),
            (0, 215, 105, 105, 0, 1.2), (3, 900, 100, 105, 0, 1.3),
            (3, 165, 215, 175, 1, 1.1), (0, 935, 235, 175, 1, 1.2),
            (5, 150, 560, 170, 1, 1.35), (1, 955, 565, 170, 1, 1.45),
            (4, 330, 640, 125, 1, 1.55), (2, 790, 645, 125, 1, 1.65),
        ]
        self.floaters = [Floater(cats[c], (x + dx, y), h, lay, d, rng)
                         for c, x, y, h, lay, d in layout]

        # ---------------- Menu : three sticker buttons (songs / message / photo)
        self.icons = {}
        for n, h in (("songs", 205), ("message", 205), ("photo", 215)):
            self.icons[n] = (load_asset(f"icon_{n}.png"), h)
        self.icon_home = {"songs": (W / 2 - 270, 225), "message": (W / 2 + 270, 225),
                          "photo": (W / 2, 490)}
        self.icon_cache = {}
        self.icon_rect = {}
        self.menu_vis = {n: 0.0 for n in MENU_ITEMS}
        self.hov = {n: 0.0 for n in MENU_ITEMS}
        self.hover = None

        # ---------------- pages
        self.mode = None            # None (closed) | "menu" | "message" | "photo" | "songs"
        self.t_mode = 0.0
        self.serial = 0             # +1 on every page change
        self.pending = None         # (name, time) while the menu icons shrink away
        self.dark_k = 0.0           # 0 = parchment background, 1 = walnut background

        # ---------------- Message page : the opened letter
        cx = W / 2 - 22                                   # composition centre
        self.paper_h = 660
        paper = load_asset("paper.png")
        self.paper = paper.resize((int(paper.width * self.paper_h / paper.height), self.paper_h),
                                  Image.LANCZOS)
        self.paper_center = (cx - 15, 365)
        self.paper_cache = {}
        self.paper_rect = None
        self.text_cx = self.paper_center[0] - 4           # centre of the writing area
        self.text_top = self.paper_center[1] - self.paper_h / 2

        flowers, candle, butterfly = (load_asset("flowers.png"), load_asset("candle.png"),
                                      load_asset("butterfly.png"))
        self.props = {
            "flowers": Prop(flowers, 335, (cx - 375, 535), 2.7,
                            enter=(-520, 60), dur=1.3, drift=(0, 3), tilt=2.2, speed=0.9, seed=1),
            "candle": Prop(candle, 345, (cx + 400, 540), 3.3,
                           enter=(0, 420), dur=1.3, drift=(0, 3), tilt=0.0, speed=0.8, seed=3),
            "butterfly": Prop(butterfly, 165, (cx - 395, 150), 3.6,
                              enter=(-520, -320), dur=2.4, drift=(42, 26), tilt=11, base_ang=-8,
                              speed=1.0, flap=True, seed=4, ang_q=1.5),
        }
        self.glow_cache = {}
        self.glow_src = {"big": warm_glow(620), "small": warm_glow(210)}

        # ---------------- Photo / Songs pages share these decorations (timed from page start)
        hx = W / 2
        self.pprops = {
            "flowers": Prop(flowers, 335, (hx - 420, 535), 0.9,
                            enter=(-520, 60), dur=1.3, drift=(0, 3), tilt=2.2, speed=0.9, seed=11),
            "candle": Prop(candle, 345, (hx + 420, 540), 1.2,
                           enter=(0, 420), dur=1.3, drift=(0, 3), tilt=0.0, speed=0.8, seed=13),
            "butterfly": Prop(butterfly, 165, (hx - 440, 150), 1.5,
                              enter=(-520, -320), dur=2.4, drift=(42, 26), tilt=11, base_ang=-8,
                              speed=1.0, flap=True, seed=14, ang_q=1.5),
        }

        # Photo page: polaroid(s) in the middle, with the DVD circling the centre one
        imgs = [Image.open(os.path.join(ASSETS, f)).convert("RGBA")
                for f in PHOTO_FILES if os.path.exists(os.path.join(ASSETS, f))]
        if not imgs:
            imgs = [load_asset("photo.png")]
        n = len(imgs)
        ph = 380 if n == 1 else (320 if n == 2 else 270)
        self.photo_props = []
        for i, im in enumerate(imgs):
            card = make_polaroid(im, ph)
            off = (i - (n - 1) / 2) * card.width * 0.86
            ang = 3 if n == 1 else (-5 if i % 2 == 0 else 5)
            self.photo_props.append(
                Prop(card, card.height, (hx + off, 395 + (i % 2) * 12), 0.3 + 0.25 * i,
                     enter=(0, -520), dur=1.3, drift=(2, 4), tilt=1.3, base_ang=ang,
                     speed=0.8, seed=20 + i))
        self.photo_mid = n // 2
        self.pdvd = OrbitDVD(size=DVD_SIZE, delay=1.4, speed=DVD_SPEED, tilt=DVD_TILT, spin=DVD_SPIN)

        # Songs page: a big spinning disc + play / pause button
        cover_path = os.path.join(ASSETS, MUSIC_COVER) if MUSIC_COVER else ""
        cover_src = None
        if cover_path and os.path.exists(cover_path):
            cover_src = record_sprite(600, Image.open(cover_path).convert("RGBA"))
        self.big_dvd = OrbitDVD(size=300, src=cover_src)
        self.disc_angle = 0.0
        self.disc_pos = (W / 2, 300)
        self.btn_pos = (W / 2, 592)
        self.big_btn = {}
        for playing in (False, True):
            b = self._big_btn(playing)
            self.big_btn[playing] = (b, shadow_of(b, 5, 95)[0])

        # ---------------- shared
        self.hearts = [heart_sprite(s, c) for s, c in
                       [(18, (170, 60, 60)), (26, (190, 80, 70)), (34, (150, 40, 45)),
                        (22, (205, 120, 95))]]
        self.sparkle = sparkle_sprite(16, (196, 150, 70))
        self.glow = self._glow(150)
        self.particles = []
        self.ambient_timer = 0.0
        self.last_t = 0.0
        self.t_open = None
        self._settled = False
        self.seal_pos = self.letter_center
        self.sparkles = [(rng.uniform(60, W - 60), rng.uniform(60, H - 60),
                          rng.uniform(0, 6.28), rng.uniform(1, 2.5)) for _ in range(26)]

        # ---------------- music player (bottom-left)
        self.music = MusicControl(MUSIC_FILE, MUSIC_VOLUME)
        self.player = PlayerCard(self.music)

    @staticmethod
    def _glow(size):
        g = Image.new("L", (size, size), 0)
        ImageDraw.Draw(g).ellipse([size * .28, size * .28, size * .72, size * .72], fill=255)
        g = g.filter(ImageFilter.GaussianBlur(size * 0.14))
        im = Image.new("RGBA", (size, size), (200, 50, 45, 0))
        im.putalpha(g)
        return im

    @staticmethod
    def _big_btn(playing):
        S, n = 4, 76 * 4
        im = Image.new("RGBA", (n, n), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.ellipse([S, S, n - S, n - S], fill=(244, 224, 184, 255), outline=GOLD, width=3 * S)
        ink, c = INK + (255,), n / 2
        if playing:
            d.rectangle([c - 13 * S, c - 14 * S, c - 5 * S, c + 14 * S], fill=ink)
            d.rectangle([c + 5 * S, c - 14 * S, c + 13 * S, c + 14 * S], fill=ink)
        else:
            d.polygon([(c - 8 * S, c - 15 * S), (c + 16 * S, c), (c - 8 * S, c + 15 * S)], fill=ink)
        return im.resize((76, 76), Image.LANCZOS)

    # -- state
    def u(self, t):
        """Seconds since the closed letter was clicked (None while it is still closed)."""
        return None if self.t_open is None else t - self.t_open

    def mu(self, t):
        """Message-page clock (same timeline the opened letter always used)."""
        return (t - self.t_mode + 0.9) if self.mode == "message" else None

    def hit_letter(self, x, y):
        l, t, r, b = self.letter_rect
        return self.t_open is None and l <= x <= r and t <= y <= b

    def open(self, t):
        if self.t_open is None:
            self.t_open = t
            self.mode, self.t_mode = "menu", t + 1.5      # icons pop in once the letter is gone
            self.serial += 1
            self.burst(self.seal_pos[0], self.seal_pos[1], 34)

    def choose(self, name, t):
        if self.mode == "menu" and self.pending is None and self.menu_vis.get(name, 0) > 0.5:
            self.pending = (name, t + 0.45)
            x, y = self.icon_home[name]
            self.burst(x, y, 18)

    def go_menu(self, t):
        if self.mode in ("message", "photo", "songs"):
            self.mode, self.t_mode, self.pending = "menu", t, None
            self.serial += 1
            self._settled = False

    def label_pos(self, name):
        x, y = self.icon_home[name]
        return x, y + self.icons[name][1] / 2 + 30

    def menu_hit(self, x, y):
        if self.mode != "menu" or self.pending is not None:
            return None
        for n in MENU_ITEMS:
            if self.menu_vis[n] < 0.5:
                continue
            cx, cy, w, h = self.icon_rect.get(n, (-999, -999, 0, 0))
            if abs(x - cx) <= w / 2 and abs(y - cy) <= h / 2:
                return n
            lx, ly = self.label_pos(n)
            if abs(x - lx) <= 10 * len(n) + 30 and abs(y - ly) <= 22:      # the text is a button too
                return n
        return None

    def big_hit(self, x, y, t):
        if self.mode != "songs" or t - self.t_mode < 1.0:
            return False
        return (x - self.btn_pos[0]) ** 2 + (y - self.btn_pos[1]) ** 2 <= 40 ** 2

    # -- helpers
    def letter_sprite(self, scale, ang):
        key = (round(scale * 50), round(ang * 4))
        if key not in self.letter_cache:
            w, h = self.letter.size
            sp = self.letter.resize((max(8, int(w * scale)), max(8, int(h * scale))), Image.LANCZOS)
            sp = sp.rotate(ang, resample=Image.BICUBIC, expand=True)
            sh, pad = shadow_of(sp, 16, 120)
            self.letter_cache[key] = (sp, sh, pad)
            if len(self.letter_cache) > 300:
                self.letter_cache.pop(next(iter(self.letter_cache)))
        return self.letter_cache[key]

    def paper_sprite(self, scale, ang):
        key = (round(scale * 40), round(ang * 2))
        if key not in self.paper_cache:
            w, h = self.paper.size
            sp = self.paper.resize((max(8, int(w * key[0] / 40)), max(8, int(h * key[0] / 40))),
                                   Image.LANCZOS)
            sp = sp.rotate(key[1] / 2, resample=Image.BICUBIC, expand=True)
            sh, pad = shadow_of(sp, 14, 130)
            self.paper_cache[key] = (sp, sh)
            if len(self.paper_cache) > 200:
                self.paper_cache.pop(next(iter(self.paper_cache)))
        return self.paper_cache[key]

    def icon_sprite(self, name, scale, ang):
        key = (name, round(scale * 40), round(ang * 2))
        if key not in self.icon_cache:
            im, h = self.icons[name]
            hh = max(8, int(h * scale))
            ww = max(8, int(im.width * hh / im.height))
            sp = im.resize((ww, hh), Image.LANCZOS).rotate(key[2] / 2, resample=Image.BICUBIC, expand=True)
            self.icon_cache[key] = (sp, shadow_of(sp, 8, 100)[0])
            if len(self.icon_cache) > 400:
                self.icon_cache.pop(next(iter(self.icon_cache)))
        return self.icon_cache[key]

    def glow_sprite(self, name, level):
        key = (name, level)
        if key not in self.glow_cache:
            self.glow_cache[key] = with_alpha(self.glow_src[name], level / 12)
        return self.glow_cache[key]

    def candle_glow(self, canvas, t, c):
        if c.rect is None:
            return
        x, y, w, h = c.rect
        fx, fy = x + 0.20 * w, y - 0.38 * h                  # flame position on the sprite
        flick = (0.78 + 0.14 * math.sin(t * 13.0) + 0.08 * math.sin(t * 21 + 1.3)
                 + 0.06 * math.sin(t * 5.1))
        lvl = max(1, min(12, int(round(flick * 12 * 0.60 * c.vis))))
        big, small = self.glow_sprite("big", max(1, lvl // 2)), self.glow_sprite("small", lvl)
        clip_composite(canvas, big, fx - big.width / 2, fy - big.height / 2)
        clip_composite(canvas, small, fx - small.width / 2, fy - small.height / 2)

    def burst(self, x, y, n=22):
        for _ in range(n):
            a = random.uniform(0, 6.28)
            v = random.uniform(90, 300)
            self.particles.append(Particle(random.choice(self.hearts), x, y,
                                           math.cos(a) * v, math.sin(a) * v - 120,
                                           random.uniform(1.4, 2.4), random.uniform(0, 14)))

    def spawn_ambient(self):
        self.particles.append(Particle(random.choice(self.hearts), random.uniform(60, W - 60),
                                       H + 20, random.uniform(-12, 12), random.uniform(-70, -40),
                                       random.uniform(9, 14), random.uniform(10, 26)))

    # -- render one frame
    def render(self, t):
        dt = max(0.0, min(0.1, t - self.last_t))
        self.last_t = t
        u = self.u(t)

        # menu icon was chosen -> switch to its page once the icons have shrunk away
        if self.pending is not None and t >= self.pending[1]:
            self.mode, self.t_mode, self.pending = self.pending[0], t, None
            self.serial += 1
            self._settled = False
        m = t - self.t_mode

        # background: parchment (closed + menu) <-> candle-lit walnut (pages)
        want_dark = (self.mode in ("message", "photo", "songs") or self.pending is not None
                     or (MENU_DARK and self.mode == "menu"))
        step = dt / 0.9
        self.dark_k = clamp01(self.dark_k + (step if want_dark else -step))
        if self.dark_k <= 0.002:
            canvas = self.bg_light.copy()
        elif self.dark_k >= 0.998:
            canvas = self.bg_dark.copy()
        else:
            canvas = Image.blend(self.bg_light, self.bg_dark, smooth(self.dark_k))

        # twinkling sparkles
        for x, y, ph, sp in self.sparkles:
            a = 0.5 + 0.5 * math.sin(t * sp + ph)
            if a > 0.2 and t > 0.6:
                clip_composite(canvas, with_alpha(self.sparkle, a * 0.8), x, y)

        # cats
        for f in self.floaters:
            if u is None:
                vis = 1.0
            elif KEEP_CATS and f.layer == 0:
                vis = 1.0
            else:
                vis = 1 - ease_out_cubic(u / 0.9)
            if f.layer == 0:
                f.draw(canvas, t, vis)

        # ---- the letter: drops in, floats / breathes; on click it shakes, then slides away
        intro = ease_out_back(t / 1.1)
        bob = 11 * math.sin(t * 1.25)
        sway = 2.6 * math.sin(t * 0.8 + 0.6)
        scale = max(0.05, intro) * (1 + 0.012 * math.sin(t * 2.0))
        drop = (1 - ease_out_cubic(t / 1.1)) * -260
        fa, dy = 1.0, 0.0
        if u is not None:
            scale *= 1 + 0.10 * ease_out_cubic(u / 0.8)
            sway += 5 * math.sin(u * 38) * clamp01(u / 0.15) * max(0.0, 1 - u / 0.85)
            if u > 0.8:
                q = clamp01((u - 0.8) / 1.0)
                fa = 1 - q
                dy = 170 * ease_out_cubic(q)
                scale *= 1 - 0.12 * q
        cx, cy = self.letter_center[0], self.letter_center[1] + bob + drop + dy
        sp, sh, pad = self.letter_sprite(scale, sway)

        if fa > 0.01:
            self.letter_rect = (cx - sp.width / 2, cy - sp.height / 2,
                                cx + sp.width / 2, cy + sp.height / 2)
            clip_composite(canvas, with_alpha(sh, fa), cx - sh.width / 2 + 10, cy - sh.height / 2 + 22)
            clip_composite(canvas, with_alpha(sp, fa), cx - sp.width / 2, cy - sp.height / 2)

            # wax seal heartbeat glow (rotate the seal offset with the letter)
            if t > 1.0:
                ox = (self.seal_frac[0] - 0.5) * self.letter.width * scale
                oy = (self.seal_frac[1] - 0.5) * self.letter.height * scale
                r = math.radians(-sway)
                sx = cx + ox * math.cos(r) - oy * math.sin(r)
                sy = cy + ox * math.sin(r) + oy * math.cos(r)
                beat = max(0.0, math.sin(t * 3.4)) ** 6 + 0.6 * max(0.0, math.sin(t * 3.4 - 0.9)) ** 8
                if u is not None:
                    beat = max(beat, 0.9)
                g = self.glow.copy()
                g.putalpha(g.getchannel("A").point(lambda v: int(v * (0.25 + 0.65 * beat) * fa)))
                gs = int(150 * (0.85 + 0.35 * beat))
                g = g.resize((gs, gs), Image.BICUBIC)
                clip_composite(canvas, g, sx - gs / 2, sy - gs / 2)
                if u is None:
                    self.seal_pos = (sx, sy)
                    # auto heart puff on every few beats
                    if int(t * 3.4 / (2 * math.pi) * 0.5 * 2) != getattr(self, "_last_puff", -1) and beat > 0.9:
                        self._last_puff = int(t * 3.4 / (2 * math.pi) * 0.5 * 2)
                        self.burst(sx, sy - 10, 5)

        for f in self.floaters:
            if f.layer == 1:
                f.draw(canvas, t, 1.0 if u is None else 1 - ease_out_cubic(u / 0.9))

        # ---- MENU : three sticker buttons
        for n in MENU_ITEMS:
            self.menu_vis[n] = 0.0
        if self.mode == "menu":
            exit_ = 0.0
            if self.pending is not None:
                exit_ = clamp01((t - (self.pending[1] - 0.45)) / 0.45)
            for i, n in enumerate(MENU_ITEMS):
                local = m - 0.22 * i
                if local <= 0:
                    continue
                chosen = self.pending is not None and self.pending[0] == n
                tgt = 1.0 if (self.hover == n and self.pending is None and local > 0.4) else 0.0
                self.hov[n] += (tgt - self.hov[n]) * min(1.0, dt * 12)
                vis = clamp01(local / 0.35) * (1 - exit_)
                sc = max(0.02, ease_out_back(local / 0.8)) * (1 + 0.07 * self.hov[n])
                sc *= (1 - 0.40 * exit_) if chosen else (1 - 0.20 * exit_)
                hx_, hy_ = self.icon_home[n]
                y = hy_ + 6 * math.sin(t * 1.3 + i * 1.7)
                ang = 3 * math.sin(t * 0.9 + i * 2.1)
                isp, ish = self.icon_sprite(n, max(0.03, sc), ang)
                clip_composite(canvas, with_alpha(ish, vis), hx_ - ish.width / 2 + 7, y - ish.height / 2 + 10)
                clip_composite(canvas, with_alpha(isp, vis), hx_ - isp.width / 2, y - isp.height / 2)
                self.icon_rect[n] = (hx_, y, isp.width, isp.height)
                self.menu_vis[n] = vis

        # ---- MESSAGE page : the letter slides out of the speech bubble
        elif self.mode == "message":
            mu = m + 0.9
            p = clamp01(m / 1.5)
            e = ease_out_cubic(p)
            ox_, oy_ = self.icon_home["message"]
            px = ox_ + (self.paper_center[0] - ox_) * e
            py = oy_ + (self.paper_center[1] - oy_) * e
            psc = 0.25 + 0.75 * ease_out_back(p)
            pang = -7 * (1 - e)
            psp, psh = self.paper_sprite(psc, pang)
            pa = clamp01(p / 0.2)
            clip_composite(canvas, with_alpha(psh, pa), px - psh.width / 2 + 8, py - psh.height / 2 + 14)
            clip_composite(canvas, with_alpha(psp, pa), px - psp.width / 2, py - psp.height / 2)
            if p >= 1.0 and not self._settled:
                self._settled = True
                self.burst(px - 230, py + 140, 14)
                self.burst(px + 230, py + 140, 14)

            self.props["flowers"].draw(canvas, mu)
            self.props["candle"].draw(canvas, mu)
            self.candle_glow(canvas, t, self.props["candle"])
            self.props["butterfly"].draw(canvas, mu)

        # ---- PHOTO page : polaroid(s) with the DVD circling them
        elif self.mode == "photo":
            self.pdvd.update(m, spinning=(self.music.playing or not DVD_ONLY_WHEN_PLAYING))
            self.pprops["flowers"].draw(canvas, m)
            mid = self.photo_props[self.photo_mid]
            self.pdvd.draw(canvas, m, mid.rect, front=False)      # behind the photo
            for pp in self.photo_props:
                pp.draw(canvas, m)
            self.pdvd.draw(canvas, m, mid.rect, front=True)       # in front of the photo
            self.pprops["candle"].draw(canvas, m)
            self.candle_glow(canvas, t, self.pprops["candle"])
            self.pprops["butterfly"].draw(canvas, m)

        # ---- SONGS page : big spinning disc + play / pause
        elif self.mode == "songs":
            if self.music.playing:
                self.disc_angle = (self.disc_angle + 150 * dt) % 360
            self.pprops["flowers"].draw(canvas, m)
            dcx, dcy = self.disc_pos
            pop = max(0.05, ease_out_back(clamp01((m - 0.2) / 0.9)))
            g = self.glow_sprite("big", 5)
            clip_composite(canvas, with_alpha(g, clamp01((m - 0.2) / 0.9)), dcx - g.width / 2, dcy - g.height / 2)
            dsp, dsh = self.big_dvd._sprite(pop, self.disc_angle)
            clip_composite(canvas, dsh, dcx - dsh.width / 2 + 8, dcy - dsh.height / 2 + 12)
            clip_composite(canvas, dsp, dcx - dsp.width / 2, dcy - dsp.height / 2)
            ba = clamp01((m - 0.7) / 0.5)
            if ba > 0.01:
                bsp, bsh = self.big_btn[self.music.playing]
                bx, by = self.btn_pos
                clip_composite(canvas, with_alpha(bsh, ba), bx - bsh.width / 2 + 3, by - bsh.height / 2 + 6)
                clip_composite(canvas, with_alpha(bsp, ba), bx - bsp.width / 2, by - bsp.height / 2)
            self.pprops["candle"].draw(canvas, m)
            self.candle_glow(canvas, t, self.pprops["candle"])
            self.pprops["butterfly"].draw(canvas, m)

        # ---- particles (ambient rising hearts + click bursts)
        self.ambient_timer += dt
        if t > 1.5 and self.ambient_timer > 0.55:
            self.ambient_timer = 0
            self.spawn_ambient()
        alive = []
        for p in self.particles:
            p.age += dt
            if p.age >= p.life:
                continue
            p.vy += 120 * dt if p.vy < 0 and abs(p.vx) > 40 else 0     # burst hearts arc back down gently
            p.x += (p.vx + p.sway * math.sin(t * 2 + p.ph)) * dt
            p.y += p.vy * dt
            if abs(p.vx) > 40:
                p.vx *= 0.96
                p.vy *= 0.96
            fade = min(1.0, p.age / 0.3, (p.life - p.age) / 0.6)
            clip_composite(canvas, with_alpha(p.sprite, fade * 0.9), p.x - p.sprite.width / 2,
                           p.y - p.sprite.height / 2)
            alive.append(p)
        self.particles = alive

        # ---- the little record player is hidden (the songs page has its own big one)
        self.player.enabled = False

        return canvas.convert("RGB")


# ---- GUI ---------------------------------------------------------------------
def run():
    global W
    import time
    import tkinter as tk
    from tkinter import font as tkfont
    from PIL import ImageTk

    root = tk.Tk()
    root.title("For Ella")
    root.configure(bg="#e9d9ba")
    root.attributes("-fullscreen", True)               # fullscreen by default
    root.update()
    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()

    W = max(1100, int(round(H * sw / sh)))              # fit the logical canvas to the screen shape
    s = min(sw / W, sh / H)                             # logical -> screen scale
    ox, oy = (sw - W * s) / 2, (sh - H * s) / 2

    def X(x): return ox + x * s
    def Y(y): return oy + y * s

    canvas = tk.Canvas(root, width=sw, height=sh, highlightthickness=0, bg="#e9d9ba")
    canvas.pack(fill="both", expand=True)

    scene = Scene()
    scene.music.start()                                 # begin looping the MP3
    if not scene.music.ok:                              # show why the music is silent
        print("MUSIC PROBLEM:", scene.music.error)
        root.title("MUSIC PROBLEM: " + scene.music.error[:80])
    families = set(tkfont.families())
    family = next((f for f in SCRIPT_FONTS if f in families), "TkDefaultFont")
    body_family = family if family != "TkDefaultFont" else "Times"
    label_family = next((f for f in LABEL_FONTS if f in families), body_family)

    def F(px, fam=None):
        return tkfont.Font(family=fam or family, size=-max(8, int(px * s)), slant="italic")

    title_font, sub_font, hint_font = F(72), F(19, body_family), F(18, body_family)
    greet_font, body_font, sign_font = F(40), F(17, body_family), F(30)
    music_font = F(15, body_family)
    label_font = tkfont.Font(family=label_family, size=-max(8, int(30 * s)), weight="bold")
    page_font = F(54)

    hex_ = lambda c: "#%02x%02x%02x" % tuple(c)
    img_id = canvas.create_image(ox, oy, anchor="nw")
    shadow = canvas.create_text(X(W / 2 + 3), Y(95 + 3), text="", font=title_font, fill="#c9b48c")
    title = canvas.create_text(X(W / 2), Y(95), text="", font=title_font, fill=hex_(INK))
    line_l = canvas.create_line(0, 0, 0, 0, fill=hex_(GOLD), width=2)
    line_r = canvas.create_line(0, 0, 0, 0, fill=hex_(GOLD), width=2)
    diamond = canvas.create_polygon(0, 0, 0, 0, 0, 0, 0, 0, fill=hex_(GOLD), outline="")
    sub = canvas.create_text(X(W / 2), Y(150), text="", font=sub_font, fill=hex_(INK_SOFT))
    hint = canvas.create_text(X(W / 2), Y(H - 30), text="", font=hint_font, fill=hex_(INK_SOFT))

    # --- menu: the text under each sticker is a button too
    menu_hint = canvas.create_text(X(W / 2), Y(62), text="", font=hint_font, fill=hex_(INK_SOFT))
    menu_label = {n: canvas.create_text(0, 0, text="", font=label_font, fill=hex_(INK), anchor="center")
                  for n in MENU_ITEMS}
    menu_bg = WALNUT if MENU_DARK else PARCHMENT
    menu_fg = PARCHMENT if MENU_DARK else INK

    # --- page titles + "back to menu" button
    page_title = canvas.create_text(X(W / 2), Y(72), text="", font=page_font, fill=hex_(PARCHMENT))
    song_title = canvas.create_text(X(W / 2), Y(492), text="", font=F(30, body_family), fill=hex_(PARCHMENT))
    BACK_X, BACK_Y, BACK_R = 80, 66, 17
    back_o = canvas.create_oval(X(BACK_X - BACK_R), Y(BACK_Y - BACK_R), X(BACK_X + BACK_R), Y(BACK_Y + BACK_R),
                                fill=hex_((244, 224, 184)), outline=hex_(GOLD), width=2, state="hidden")
    back_t = canvas.create_text(X(BACK_X), Y(BACK_Y - 2), text="\u2039",
                                font=tkfont.Font(family=body_family, size=-max(8, int(26 * s))),
                                fill=hex_(INK), state="hidden")
    back_l = canvas.create_text(X(BACK_X + 26), Y(BACK_Y), text="menu", font=F(20, body_family),
                                fill=hex_(PARCHMENT), anchor="w", state="hidden")

    # --- text that is written on the opened parchment
    tcx, ttop = scene.text_cx, scene.text_top
    wrap = int(330 * s)
    greet = canvas.create_text(X(tcx), Y(ttop + 100), text="", font=greet_font, fill=hex_(INK), anchor="n")
    orn_l = canvas.create_line(0, 0, 0, 0, fill=hex_(GOLD), width=2, state="hidden")
    orn_r = canvas.create_line(0, 0, 0, 0, fill=hex_(GOLD), width=2, state="hidden")
    orn_d = canvas.create_polygon(0, 0, 0, 0, 0, 0, 0, 0, fill=hex_(GOLD), outline="", state="hidden")
    body = canvas.create_text(X(tcx), Y(ttop + 188), text="", font=body_font, fill=hex_(INK),
                              anchor="n", justify="center", width=wrap)
    sign = canvas.create_text(X(tcx), Y(ttop + 505), text="", font=sign_font, fill=hex_(INK), anchor="n")
    BTN_Y, BTN_DX, BTN_R = ttop + 632, 50, 13           # small page buttons (logical px)
    turn_hint = canvas.create_text(X(tcx), Y(BTN_Y), text="", font=F(15, body_family),
                                   fill=hex_(INK_SOFT), anchor="center")
    btn_font = F(24, body_family)

    def make_btn(bx, glyph):
        o = canvas.create_oval(X(bx - BTN_R), Y(BTN_Y - BTN_R), X(bx + BTN_R), Y(BTN_Y + BTN_R),
                               fill=hex_((244, 224, 184)), outline=hex_(GOLD), width=2, state="hidden")
        t_ = canvas.create_text(X(bx), Y(BTN_Y - 2), text=glyph, font=btn_font,
                                fill=hex_(INK), state="hidden")
        return o, t_

    btn_back_o, btn_back_t = make_btn(tcx - BTN_DX, "\u2039")
    btn_next_o, btn_next_t = make_btn(tcx + BTN_DX, "\u203a")

    # --- split the long letter into pages that fit on the parchment
    def wrap_lines(text, font, maxw):
        lines = []
        for para in text.split("\n"):
            if not para.strip():
                lines.append("")
                continue
            cur = ""
            for wd in para.split():
                trial = (cur + " " + wd).strip()
                if not cur or font.measure(trial) <= maxw:
                    cur = trial
                else:
                    lines.append(cur)
                    cur = wd
            lines.append(cur)
        return lines

    LS = body_font.metrics("linespace") / s            # line height in logical px
    BODY_Y0, BODY_Y1 = 188, 105                         # body top on page 1 / later pages
    BODY_BOTTOM = 598
    caps = (int((BODY_BOTTOM - BODY_Y0) / LS), int((BODY_BOTTOM - BODY_Y1) / LS))
    all_lines = wrap_lines(BODY, body_font, wrap)
    pages, i, cap = [], 0, caps[0]
    while i < len(all_lines):
        while i < len(all_lines) and all_lines[i] == "":
            i += 1
        chunk = all_lines[i:i + cap]
        while chunk and chunk[-1] == "":
            chunk.pop()
        if chunk:
            pages.append("\n".join(chunk))
        i += cap
        cap = caps[1]
    pages = pages or [""]

    # --- label on the little record player
    music_label = canvas.create_text(X(PlayerCard.X0 + PlayerCard.LABEL_POS[0]),
                                     Y(PlayerCard.Y0 + PlayerCard.LABEL_POS[1]),
                                     text="", font=music_font, fill=hex_(INK), anchor="w")

    state = {"photo": None, "bgc": None, "serial": -1, "page": 0, "page_t0": 0.0,
             "done": False, "force": False}
    start = time.time()

    def lerp_color(c1, c2, k):
        return "#%02x%02x%02x" % tuple(int(a + (b - a) * k) for a, b in zip(c1, c2))

    def hide_letter_items():
        canvas.itemconfig(greet, text="")
        canvas.itemconfig(body, text="")
        canvas.itemconfig(sign, text="")
        canvas.itemconfig(turn_hint, text="")
        for it in (orn_l, orn_r, orn_d, btn_back_o, btn_back_t, btn_next_o, btn_next_t):
            canvas.itemconfig(it, state="hidden")

    def tick():
        t0 = time.time()
        t = t0 - start
        u = scene.u(t)
        frame = scene.render(t)
        mode = scene.mode
        m = t - scene.t_mode
        if abs(s - 1) > 1e-3:
            frame = frame.resize((int(W * s), int(H * s)), Image.BILINEAR)
        state["photo"] = ImageTk.PhotoImage(frame)
        canvas.itemconfig(img_id, image=state["photo"])

        # a new page starts -> the letter starts again from page 1
        if state["serial"] != scene.serial:
            state.update(serial=scene.serial, page=0, page_t0=0.0, done=False, force=False)

        # letterbox colour follows the background
        bgc = hex_(WALNUT) if scene.dark_k > 0.5 else "#e9d9ba"
        if state["bgc"] != bgc:
            state["bgc"] = bgc
            canvas.configure(bg=bgc)
            root.configure(bg=bgc)

        # ---------------- closed letter screen
        if u is None:
            # typewriter "HAPPY BIRTHDAY" with a slow fade-in of ink
            k = max(0.0, (t - 1.4) / 1.6)
            n = min(len(TEXT), int(k * len(TEXT)) + (1 if k > 0 else 0))
            shown = TEXT[:n]
            fade = min(1.0, max(0.0, (t - 1.4) / 0.9))
            canvas.itemconfig(shadow, text=shown, fill=lerp_color(PARCHMENT, (201, 180, 140), fade))
            canvas.itemconfig(title, text=shown, fill=lerp_color(PARCHMENT, INK, fade))

            # flourish under the title
            ft = min(1.0, max(0.0, (t - 3.0) / 1.0))
            if ft > 0:
                half = 130 * ease_out_cubic(ft)
                canvas.coords(line_l, X(W / 2 - 12), Y(138), X(W / 2 - 12 - half), Y(138))
                canvas.coords(line_r, X(W / 2 + 12), Y(138), X(W / 2 + 12 + half), Y(138))
                canvas.coords(diamond, X(W / 2), Y(131), X(W / 2 + 7), Y(138),
                              X(W / 2), Y(145), X(W / 2 - 7), Y(138))
                canvas.itemconfig(sub, text=SUBTITLE if ft > 0.6 else "")
                canvas.coords(sub, X(W / 2), Y(162 + 2 * math.sin(t * 1.5)))
            # little hint
            if t > 4.5:
                pulse = 0.5 + 0.5 * math.sin(t * 2.2)
                canvas.itemconfig(hint, text=HINT, fill=lerp_color(INK_SOFT, (222, 195, 150), pulse * 0.65))
        else:
            # title fades into the parchment, then everything old hides
            k = clamp01(u / 0.7)
            canvas.itemconfig(title, fill=lerp_color(INK, PARCHMENT, k))
            canvas.itemconfig(shadow, fill=lerp_color((201, 180, 140), PARCHMENT, k))
            canvas.itemconfig(sub, fill=lerp_color(INK_SOFT, PARCHMENT, k))
            canvas.itemconfig(hint, text="")
            if k >= 1.0:
                for it in (title, shadow, sub, line_l, line_r, diamond):
                    canvas.itemconfig(it, state="hidden")

        # ---------------- menu: sticker labels (they are buttons too)
        in_menu = mode == "menu"
        any_vis = 0.0
        for n in MENU_ITEMS:
            vis = scene.menu_vis[n] if in_menu else 0.0
            any_vis = max(any_vis, vis)
            if vis > 0.03:
                lx, ly = scene.label_pos(n)
                hot = scene.hover == n and scene.pending is None
                base = WAX if hot else menu_fg
                canvas.coords(menu_label[n], X(lx), Y(ly))
                canvas.itemconfig(menu_label[n], text=n, fill=lerp_color(menu_bg, base, vis))
            else:
                canvas.itemconfig(menu_label[n], text="")
        if any_vis > 0.03:
            canvas.itemconfig(menu_hint, text=MENU_HINT, fill=lerp_color(menu_bg, INK_SOFT if not MENU_DARK else (222, 195, 150), any_vis))
        else:
            canvas.itemconfig(menu_hint, text="")

        # ---------------- back-to-menu button + page titles
        on_page = mode in ("message", "photo", "songs") and m > 0.8
        for it in (back_o, back_t, back_l):
            canvas.itemconfig(it, state="normal" if on_page else "hidden")
        if mode in ("photo", "songs"):
            canvas.itemconfig(page_title, text=mode, fill=lerp_color(WALNUT, PARCHMENT, clamp01(m / 0.8)))
        else:
            canvas.itemconfig(page_title, text="")
        if mode == "songs":
            canvas.itemconfig(song_title, text=MUSIC_LABEL,
                              fill=lerp_color(WALNUT, PARCHMENT, clamp01((m - 0.5) / 0.8)))
        else:
            canvas.itemconfig(song_title, text="")

        # ---------------- message page: the love letter is "written" onto the parchment
        mu = scene.mu(t)
        if mu is None:
            hide_letter_items()
        else:
            u = mu
            pg = state["page"]
            last = len(pages) - 1
            g_end = 3.4 + len(GREETING) / 26                    # when the greeting is finished
            if pg == 0:
                n = 10 ** 6 if state["force"] else int(max(0.0, u - 3.4) * 26)
                canvas.itemconfig(greet, text=GREETING[:n])
                if n >= len(GREETING):
                    o = 1.0 if state["force"] else clamp01((u - g_end) / 0.8)
                    half = 62 * ease_out_cubic(o)
                    for it in (orn_l, orn_r, orn_d):
                        canvas.itemconfig(it, state="normal")
                    oy_ = ttop + 168
                    canvas.coords(orn_l, X(tcx - 9), Y(oy_), X(tcx - 9 - half), Y(oy_))
                    canvas.coords(orn_r, X(tcx + 9), Y(oy_), X(tcx + 9 + half), Y(oy_))
                    canvas.coords(orn_d, X(tcx), Y(oy_ - 5), X(tcx + 5), Y(oy_), X(tcx), Y(oy_ + 5), X(tcx - 5), Y(oy_))
                chars = 10 ** 6 if state["force"] else (u - g_end) * BODY_CPS
                body_y = ttop + BODY_Y0
            else:
                canvas.itemconfig(greet, text="")
                for it in (orn_l, orn_r, orn_d):
                    canvas.itemconfig(it, state="hidden")
                chars = 10 ** 6 if state["force"] else (u - state["page_t0"]) * BODY_CPS
                body_y = ttop + BODY_Y1

            page_text = pages[pg]
            canvas.coords(body, X(tcx), Y(body_y))
            canvas.itemconfig(body, text=page_text[:max(0, int(chars))])
            state["done"] = chars >= len(page_text) and (pg > 0 or u > g_end)

            if state["done"] and pg == last and SIGN:
                canvas.coords(sign, X(tcx), Y(body_y + (page_text.count("\n") + 1) * LS + 14))
                canvas.itemconfig(sign, text=SIGN + " \u2665")
            else:
                canvas.itemconfig(sign, text="")

            show = len(pages) > 1 and u > 5.0
            canvas.itemconfig(turn_hint, text=("%d / %d" % (pg + 1, len(pages))) if show else "")
            for o_, t_, ok in ((btn_back_o, btn_back_t, pg > 0), (btn_next_o, btn_next_t, pg < last)):
                canvas.itemconfig(o_, state="normal" if show else "hidden",
                                  fill=hex_((244, 224, 184) if ok else (222, 200, 160)),
                                  outline=hex_(GOLD if ok else (200, 175, 130)))
                canvas.itemconfig(t_, state="normal" if show else "hidden",
                                  fill=hex_(INK if ok else (190, 165, 125)))

        # music player label fades in together with the card
        pa = scene.player.alpha(t) if scene.player.enabled else 0.0
        if pa > 0.01:
            canvas.itemconfig(music_label, text=MUSIC_LABEL,
                              fill=lerp_color((232, 205, 156), INK, pa))
        else:
            canvas.itemconfig(music_label, text="")
        canvas.tag_raise(music_label)

        elapsed = int((time.time() - t0) * 1000)
        root.after(max(1, int(1000 / FPS) - elapsed), tick)

    def to_logical(e):
        return (e.x - ox) / s, (e.y - oy) / s

    def paper_button(x, y, u_):
        if u_ is None or u_ < 5.0 or len(pages) < 2:
            return None
        for name, bx in (("back", tcx - BTN_DX), ("next", tcx + BTN_DX)):
            if (x - bx) ** 2 + (y - BTN_Y) ** 2 <= (BTN_R + 3) ** 2:
                return name
        return None

    def back_hit(x, y, t):
        return (scene.mode in ("message", "photo", "songs") and t - scene.t_mode > 0.8
                and 50 <= x <= 160 and 40 <= y <= 92)

    def on_click(e):
        x, y = to_logical(e)
        t = time.time() - start
        mode = scene.mode

        if back_hit(x, y, t):                            # "menu" button on every page
            scene.go_menu(t)
            return
        btn = scene.player.hit(x, y, t)
        if btn:                                          # record-player buttons
            scene.player.press(btn)
            return

        if mode == "menu":
            name = scene.menu_hit(x, y)                  # sticker or its text
            if name:
                scene.choose(name, t)
                return
        elif mode == "message":
            u_ = scene.mu(t)
            pb = paper_button(x, y, u_)
            if pb == "next":
                if not state["done"]:
                    state["force"] = True                  # finish typing this page first
                elif state["page"] < len(pages) - 1:
                    state["page"] += 1
                    state["page_t0"] = u_
                    state["done"], state["force"] = False, False
                return
            if pb == "back":
                if state["page"] > 0:
                    state["page"] -= 1
                    state["force"] = True                  # earlier pages appear fully written
                return
        elif mode == "songs":
            if scene.big_hit(x, y, t):
                scene.music.press("play")
                return
        elif mode is None:
            if scene.hit_letter(x, y) and t > 1.2:
                scene.open(t)
                canvas.config(cursor="")
                return
        scene.burst(x, y, 26)

    def on_move(e):
        x, y = to_logical(e)
        t = time.time() - start
        scene.hover = scene.menu_hit(x, y)
        over = (scene.hit_letter(x, y) or scene.player.hit(x, y, t) or scene.hover
                or back_hit(x, y, t) or paper_button(x, y, scene.mu(t)) or scene.big_hit(x, y, t))
        canvas.config(cursor="hand2" if over else "")

    canvas.bind("<Button-1>", on_click)
    canvas.bind("<Motion>", on_move)
    root.bind("<Escape>", lambda e: root.destroy())
    root.bind("q", lambda e: root.destroy())
    tick()
    root.mainloop()
    scene.music.stop()


if __name__ == "__main__":
    if "--test" in sys.argv:      # headless frame dump (no tkinter needed)
        s = Scene()
        for i, tt in enumerate([0.3, 1.0, 2.5, 5.0]):
            s.render(tt - 0.03)
            s.render(tt).save(f"/tmp/frame{i}.png")
        s.open(5.0)
        steps = [(5.6, None), (8.2, "menu"), (None, "message"), (13.5, "msg"), (None, "back"),
                 (None, "photo"), (None, "songs")]
        s.render(6.6); s.render(6.63)
        s.render(8.0).save("/tmp/menu.png")
        s.choose("message", 8.0)
        for tt in (8.2, 8.5, 9.2, 10.5, 12.0, 14.0):
            s.render(tt)
        s.render(14.5).save("/tmp/message.png")
        s.go_menu(15.0)
        for tt in (15.3, 16.0):
            s.render(tt)
        s.render(17.0).save("/tmp/menu2.png")
        s.choose("photo", 17.0)
        for tt in (17.3, 17.6, 18.0, 19.0, 20.0, 21.5):
            s.render(tt)
        s.render(22.0).save("/tmp/photo.png")
        s.go_menu(23.0)
        for tt in (23.5, 24.5, 25.0):
            s.render(tt)
        s.choose("songs", 25.0)
        for tt in (25.3, 25.6, 26.0, 27.0, 28.0):
            s.render(tt)
        s.render(29.0).save("/tmp/songs.png")
        print("frames saved")
    else:
        run()