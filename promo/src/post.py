"""Glitch post-production + captions for the DEZERT HORSE reel. Streams frames into ffmpeg."""
import glob, json, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
B = 60 / 152
BAR = 4 * B
T = dict(click=2*BAR, speed=4*BAR, struct=6*BAR, stretch=8*BAR, fov=10*BAR, scan=12*BAR,
         orbit=14*BAR, cta=16*BAR, loop=19.5*BAR, end=20*BAR)
NF = int(round(T['end'] * FPS))
FONT = 'vt323.ttf'
OUT = sys.argv[1] if len(sys.argv) > 1 else 'reel.mp4'
ONLY = [int(x) for x in sys.argv[2].split(',')] if len(sys.argv) > 2 else None  # preview specific frames

meta = {}
for fn in glob.glob('frames/meta_*.json'):
    meta.update({int(k): v for k, v in json.load(open(fn)).items()})

def ease(x):
    x = min(max(x, 0.0), 1.0)
    return 4*x**3 if x < .5 else 1 - (-2*x + 2)**3 / 2

def kf(keys, beat):
    if beat <= keys[0][0]: return keys[0][1]
    for (b0, v0), (b1, v1) in zip(keys[:-1], keys[1:]):
        if beat <= b1: return v0 + (v1 - v0) * ease((beat - b0) / (b1 - b0))
    return keys[-1][1]

def hex2rgb(h):
    h = h.strip().lstrip('#')
    if len(h) == 3: h = ''.join(c*2 for c in h)
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

fonts = {}
def font(sz):
    if sz not in fonts: fonts[sz] = ImageFont.truetype(FONT, sz)
    return fonts[sz]

# ------------------------------------------------------------------ captions
# (scene start, scene end, [(beat offset, text)])
CAPS = [
    (0.0,             T['click'],  [(0, 'ISSO NÃO É UM SITE.'), (4, 'É UM INSTRUMENTO.')]),
    (T['click'] + .2, T['speed'],  [(0, 'UM CAVALO.'), (2, 'UM DESERTO.'), (4, 'UM ÁLBUM PRA PILOTAR.')]),
    (T['speed'],      T['struct'], [(.5, 'ACELERE O TROTE.'), (3, 'A MÚSICA ACOMPANHA.')]),
    (T['struct'],     T['stretch'],[(.5, 'VEJA OS OSSOS'), (2, 'DO CÓDIGO.')]),
    (T['stretch'],    T['fov'],    [(.5, 'ESTIQUE O CAVALO.'), (3, 'O SOM DISTORCE.')]),
    (T['fov'],        T['scan'],   [(.5, 'ABRA A LENTE.'), (3, 'O SOM SE FECHA.')]),
    (T['scan'],       T['orbit'],  [(0, 'SINTONIZE'), (1, '10 FREQUÊNCIAS.')]),
    (T['orbit'],      T['cta'],    [(0, 'GIRE A CÂMERA.'), (2.5, 'ATRAVESSE O ESPECTRO.')]),
]
CPS = 26  # typewriter chars / second

def caption_state(t):
    for a, b, lines in CAPS:
        if a <= t < b:
            out = []
            for bo, txt in lines:
                ts = a + bo * B
                if t >= ts:
                    n = min(len(txt), int((t - ts) * CPS) + 1)
                    out.append((txt[:n], n < len(txt)))
            return out, (b - t)
    return [], 0

cap_cache = {}
def caption_layer(lines, color, blink):
    key = (tuple(lines), color, blink)
    if key in cap_cache: return cap_cache[key]
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    col = hex2rgb(color)
    txtcol = tuple(int(c * .45 + 255 * .55) for c in col)
    y = 330
    for i, (txt, typing) in enumerate(lines):
        sz = 96
        f = font(sz)
        shown = txt + ('█' if (typing or (i == len(lines) - 1 and blink)) else '')
        full_w = d.textlength(txt + '█', font=f)
        while full_w > 900 and sz > 50:
            sz -= 4; f = font(sz); full_w = d.textlength(txt + '█', font=f)
        tw = d.textlength(shown, font=f)
        x = 70
        pad = 18
        box = (x - pad, y - 6, x + tw + pad, y + sz + 4)
        d.rectangle(box, fill=(20, 10, 5, 215), outline=col + (255,), width=3)
        d.text((x, y - sz * 0.12), shown, font=f, fill=txtcol + (255,))
        y += sz + 42
    glow = lay.filter(ImageFilter.GaussianBlur(14))
    out = Image.alpha_composite(glow, lay)
    arr = np.asarray(out).astype(np.float32)
    cap_cache[key] = arr
    if len(cap_cache) > 64: cap_cache.pop(next(iter(cap_cache)))
    return arr

# persistent top stamp
def stamp_layer(color, t):
    lay = Image.new('RGBA', (W, 140), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    col = hex2rgb(color)
    on = int(t / (B)) % 2 == 0
    if on: d.ellipse((72, 52, 94, 74), fill=(255, 40, 40, 235))
    tc = f'00:{int(t // 60):02d}:{int(t % 60):02d}'
    d.text((106, 36), f'AO VIVO  {tc}  //  DEZERTHORSE.GITHUB.IO/CAVALO', font=font(38), fill=col + (220,))
    return np.asarray(lay).astype(np.float32)

# CTA end card
def cta_layer(t, color):
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    col = hex2rgb(color)
    cream = tuple(int(c * .35 + 255 * .65) for c in col)
    bt = (t - T['cta']) / B
    def centered(txt, y, sz, fill, box=None):
        f = font(sz); tw = d.textlength(txt, font=f); x = (W - tw) / 2
        if box == 'solid':
            d.rectangle((x - 34, y - 14, x + tw + 34, y + sz + 8), fill=col + (255,))
        elif box == 'outline':
            d.rectangle((x - 30, y - 12, x + tw + 30, y + sz + 6), fill=(20, 10, 5, 215), outline=col + (255,), width=3)
        d.text((x, y - sz * 0.12), txt, font=f, fill=fill)
    if bt >= 0:
        word = 'EXPERIMENTE'
        n = min(len(word), int(bt * B * 30) + 1)
        centered(word[:n] + ('█' if n < len(word) or int(bt * 2) % 2 == 0 else ' '), 430, 176, cream + (255,))
    if bt >= 2:
        centered('dezerthorse.github.io/cavalo', 690, 66, (20, 10, 5, 255), box='solid')
    if bt >= 4:
        centered('[ LINK NA BIO ]', 820, 52, col + (255,))
    if bt >= 7:
        centered('DEZERT HORSE', 1150, 92, cream + (255,), box='outline')
        centered('ÁLBUM DISPONÍVEL EM TODAS AS PLATAFORMAS', 1290, 42, col + (255,))
    glow = lay.filter(ImageFilter.GaussianBlur(16))
    return np.asarray(Image.alpha_composite(glow, lay)).astype(np.float32)

def over(img, lay, y0=0, dx=0):
    h = lay.shape[0]
    region = img[y0:y0 + h]
    a = lay[..., 3:4] / 255.0
    src = lay[..., :3]
    if dx:
        # chromatic split of the overlay itself
        r = np.roll(src[..., 0], dx, axis=1); b = np.roll(src[..., 2], -dx, axis=1)
        src = np.stack([r, src[..., 1], b], -1)
    region[:] = region * (1 - a) + src * a
    return img

# ------------------------------------------------------------------ glitch intensity driven by the edit
CUTS = [T['click'], T['speed'], T['struct'], T['stretch'], T['fov'], T['scan'], T['orbit'], T['cta'], T['loop']]
SCAN_CUTS = [T['scan'] + k * B for k in range(8)] + [T['scan'] + 7.5 * B]

def intensity(t):
    g = 0.0
    bp = (t % B) / B
    g += 0.18 * np.exp(-bp * B / 0.07)                  # every beat: small kick
    for c in CUTS:
        dt = t - c
        if -0.1 < dt < 0.35: g = max(g, 1.0 * np.exp(-max(dt, 0) / 0.12))
    for c in SCAN_CUTS:
        dt = t - c
        if 0 <= dt < 0.2: g = max(g, 0.75 * np.exp(-dt / 0.07))
    if T['stretch'] <= t < T['fov']:
        s = kf([[0.5, 0], [3, 100], [5, 100], [5.5, 40], [6, 100], [7.6, 0]], (t - T['stretch']) / B) / 100
        g = max(g, 0.55 * s)
    if T['orbit'] + 7 * B <= t < T['cta']:
        g = max(g, 0.6)                                   # beat-repeat roll
    if t >= T['cta'] + 2 * BAR:
        g = max(g, 0.12 + 0.5 * ((t - T['cta'] - 2 * BAR) / (T['loop'] - T['cta'] - 2 * BAR)) ** 3)
    return float(min(g, 1.0))

# ------------------------------------------------------------------ effects
yy, xx = np.mgrid[0:H, 0:W]
scan_mask = np.where(yy % 4 < 1, 0.86, 1.0).astype(np.float32)[..., None]
grain = [np.random.default_rng(i).normal(0, 7, (H // 2, W // 2, 1)).astype(np.float32) for i in range(8)]
cx, cy = W / 2, H / 2
rr = np.sqrt(((xx - cx) / cx) ** 2 + ((yy - cy) / cy) ** 2).astype(np.float32)
vign = (1 - 0.28 * np.clip(rr - 0.4, 0, 1) ** 1.6)[..., None]

def chroma(img, dx):
    if dx == 0: return img
    out = img.copy()
    out[..., 0] = np.roll(img[..., 0], dx, axis=1)
    out[..., 2] = np.roll(img[..., 2], -dx, axis=1)
    return out

def slices(img, g, rng):
    n = int(g * 16)
    for _ in range(n):
        h = int(rng.integers(6, 140)); y = int(rng.integers(0, H - h))
        img[y:y+h] = np.roll(img[y:y+h], int(rng.normal(0, 1) * g * 180), axis=1)
    return img

def mosh(img, prev, g, rng):
    if prev is None: return img
    bs = 48
    n = int(g * 0.3 * (H // bs) * (W // bs))
    mvx, mvy = int(rng.integers(-24, 24)), int(rng.integers(-40, 8))
    src = np.roll(np.roll(prev, mvy, axis=0), mvx, axis=1)
    for _ in range(n):
        by = int(rng.integers(0, H // bs)) * bs; bx = int(rng.integers(0, W // bs)) * bs
        img[by:by+bs, bx:bx+bs] = src[by:by+bs, bx:bx+bs]
    return img

def pixelsort(img, rng, strength):
    h = int(200 + strength * 600); y0 = int(rng.integers(0, H - h))
    band = img[y0:y0+h]
    lum = band @ np.array([0.299, 0.587, 0.114], np.float32)
    thr = np.percentile(lum, 45)
    key = np.where(lum > thr, lum, -1)          # dark pixels stay, bright runs smear to one side
    order = np.argsort(key, axis=1, kind='stable')
    img[y0:y0+h] = np.take_along_axis(band, order[..., None], axis=1)
    return img

def pixelate(img, s):
    bs = int(2 + s * 22)
    if bs <= 2: return img
    small = img[::bs, ::bs]
    big = np.repeat(np.repeat(small, bs, 0), bs, 1)[:H, :W]
    lv = 3 + int((1 - s) * 12)
    big = np.round(big / 255 * lv) / lv * 255
    # only inside a horizontal data band that breathes with the slider, like corrupted memory
    return big

def radial_ab(img, amt):
    if amt < 0.5: return img
    out = img.copy()
    k = amt / 1000.0
    sx = (xx - cx) * k; sy = (yy - cy) * k
    xr = np.clip(xx + sx, 0, W - 1).astype(np.int32); yr = np.clip(yy + sy, 0, H - 1).astype(np.int32)
    xb = np.clip(xx - sx, 0, W - 1).astype(np.int32); yb = np.clip(yy - sy, 0, H - 1).astype(np.int32)
    out[..., 0] = img[yr, xr, 0]; out[..., 2] = img[yb, xb, 2]
    return out

def ring(img, x, y, pressed, col):
    lay = Image.new('RGBA', (160, 160), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    r = 30 if pressed else 38
    d.ellipse((80 - r, 80 - r, 80 + r, 80 + r), fill=(255, 255, 255, 70 if not pressed else 120), outline=(255, 255, 255, 230), width=5)
    lay = Image.alpha_composite(lay.filter(ImageFilter.GaussianBlur(6)), lay)
    arr = np.asarray(lay).astype(np.float32)
    x0, y0 = int(x - 80), int(y - 80)
    if 0 <= x0 < W - 160 and 0 <= y0 < H - 160:
        sub = img[y0:y0+160, x0:x0+160]
        a = arr[..., 3:4] / 255
        sub[:] = sub * (1 - a) + arr[..., :3] * a
    return img

# ------------------------------------------------------------------ main loop
def load(f):
    p = f'frames/f{f:04d}.png'
    if not os.path.exists(p):
        # fall back to the nearest captured frame
        cands = sorted(glob.glob('frames/f*.png'))
        p = min(cands, key=lambda c: abs(int(c[-8:-4]) - f))
    return np.asarray(Image.open(p).convert('RGB').resize((W, H))).astype(np.float32)

frames = ONLY if ONLY else range(NF)
proc = None
if not ONLY:
    proc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y',
        '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
        '-f', 'f32le', '-ar', '48000', '-ac', '2', '-i', 'mix.f32',
        '-af', 'loudnorm=I=-14:TP=-1.0:LRA=11',
        '-c:v', 'libx264', '-preset', 'slow', '-crf', '17', '-pix_fmt', 'yuv420p', '-profile:v', 'high',
        '-c:a', 'aac', '-b:a', '256k', '-ar', '48000', '-movflags', '+faststart', '-shortest', OUT], stdin=subprocess.PIPE)

prev = None
trail = None
for f in frames:
    t = f / FPS
    rng = np.random.default_rng(f * 7 + 3)
    m = meta.get(f) or meta.get(min(meta, key=lambda k: abs(k - f))) if meta else {}
    color = (m or {}).get('color') or '#ff6600'
    img = load(f)

    # speed: motion echo that grows with |trote - 100%|
    if T['speed'] <= t < T['struct']:
        sp = kf([[0.5, 100], [2, 15], [3, 15], [5, 200], [6.5, 200], [7.5, 100]], (t - T['speed']) / B)
        a = min(0.8, abs(sp - 100) / 100 * 0.75)
        if trail is not None and a > 0.02:
            img = img * (1 - a) + trail * a
        trail = img.copy()
    else:
        trail = img.copy()

    # estrutura de dados: a corrupted-memory band that follows the slider (matches the bitcrush)
    if T['struct'] <= t < T['stretch']:
        s = kf([[0.5, 0], [2.5, 100], [4.5, 100], [5, 30], [5.5, 100], [6, 30], [6.5, 100]], (t - T['struct']) / B) / 100
        if s > 0.03:
            px = pixelate(img, s)
            band_h = int(H * (0.08 + 0.35 * s))
            y0 = int((np.sin(t * 5) * 0.5 + 0.5) * (H * 0.55 - band_h) + H * 0.2)
            img[y0:y0+band_h] = px[y0:y0+band_h]

    # lente: radial chromatic aberration grows with FOV distance from 40
    if T['fov'] <= t < T['scan']:
        fv = kf([[0.5, 40], [2.5, 120], [4, 120], [5.5, 20], [7, 20], [7.8, 40]], (t - T['fov']) / B)
        img = radial_ab(img, abs(fv - 40) * 0.35)

    g = intensity(t)
    img = chroma(img, int(2 + g * 26))
    if g > 0.25:
        img = mosh(img, prev, g, rng)
        img = slices(img, g, rng)
    if g > 0.7 and rng.random() < 0.6:
        img = pixelsort(img, rng, g)

    # click flash
    dtc = t - T['click']
    if 0 <= dtc < 0.2:
        img = img + (255 - img) * float(np.exp(-dtc / 0.06))

    # overlays
    if T['cta'] <= t < T['loop']:
        lay = cta_layer(t, color)
        img = over(img, lay, 0, int(g * 14) if g > 0.3 else 0)
    else:
        lines, left = caption_state(t)
        if lines:
            blink = int(t / (B / 2)) % 2 == 0
            lay = caption_layer(lines, color, blink)
            # captions glitch out on the last frames of each scene
            dx = int(g * 18) if g > 0.3 else 0
            if left < 0.1:
                dx = int(rng.integers(20, 60))
            img = over(img, lay, 0, dx)
    if T['click'] <= t < T['loop']:
        img = over(img, stamp_layer(color, t - T['click']), 110)

    # touch indicator (real slider/button positions from the capture, css px * 2)
    th = (m or {}).get('thumb')
    if th and not (T['scan'] <= t < T['orbit']):
        pressed = T['orbit'] <= t < T['cta']
        img = ring(img, th['x'] * 2, th['y'] * 2, pressed, color)
    if T['click'] - 0.7 <= t < T['click'] + 0.12:
        img = ring(img, 540, 1034, t >= T['click'] - 0.05, color)

    # crt finish: scanlines, grain, vignette
    img = img * scan_mask
    gr = grain[f % 8]
    img = img + np.repeat(np.repeat(gr, 2, 0), 2, 1)
    img = img * vign
    img = np.clip(img, 0, 255)
    prev = img.copy()
    out8 = img.astype(np.uint8)
    if proc:
        proc.stdin.write(out8.tobytes())
    else:
        Image.fromarray(out8).save(f'preview_post_{f:04d}.png')
    if f % 60 == 0: print('post', f, flush=True)

if proc:
    proc.stdin.close(); proc.wait()
    print('done', OUT)
