"""DEZERT HORSE — case reel v2: how HTML/CSS/JavaScript/WebGL/GLSL/Web Audio turned an album into an
interactive site, and an invitation to do the same for the viewer's project. Streams frames into ffmpeg."""
import glob, json, os, re, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
B = 60 / 152
BAR = 4 * B
T = dict(ignite=2*BAR, speed=4*BAR, struct=6*BAR, stretch=8*BAR, fov=10*BAR, scan=12*BAR,
         orbit=15*BAR, pitch=17*BAR, card=20*BAR, away=21.25*BAR, end=22*BAR)
NF = int(T['end'] * FPS)
FONT = 'vt323.ttf'
OUT = sys.argv[1] if len(sys.argv) > 1 else 'reel2.mp4'
ONLY = [int(x) for x in sys.argv[2].split(',')] if len(sys.argv) > 2 else None
REUSE = (190, 568)   # slider scenes are identical to v1: frames reused from frames/

meta = {}
for fn in glob.glob('frames2/meta_*.json'):
    meta.update({int(k): v for k, v in json.load(open(fn)).items()})
for fn in glob.glob('frames/meta_*.json'):
    for k, v in json.load(open(fn)).items():
        if REUSE[0] <= int(k) <= REUSE[1]: meta[int(k)] = v

THEMES = ["#dcb386", "#ffd700", "#aacc00", "#81b29a", "#48cae4", "#4a90e2", "#9b59b6", "#e91e63", "#d00000", "#ff6600"]

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

SPEED_K = [[0.5, 100], [2, 15], [3, 15], [5, 200], [6.5, 200], [7.5, 100]]
STRUCT_K = [[0.5, 0], [2.5, 100], [4.5, 100], [5, 30], [5.5, 100], [6, 30], [6.5, 100]]
STRETCH_K = [[0.5, 0], [3, 100], [5, 100], [5.5, 40], [6, 100], [7.6, 0]]
FOV_K = [[0.5, 40], [2.5, 120], [4, 120], [5.5, 20], [7, 20], [7.8, 40]]

# ------------------------------------------------------------------ captions: (start, end, [(beat, text)])
CAPS = [
    (0.25,          T['ignite'],  [(0, 'UM ÁLBUM MERECE'), (2.5, 'MAIS QUE UM LINK.')]),
    (T['ignite'],   T['speed'],   [(0, 'ENTÃO VIROU'), (1.5, 'UM SITE INTERATIVO.')]),
    (T['speed'],    T['struct'],  [(.25, 'JAVASCRIPT LIGA'), (2, 'O TROTE À MÚSICA.')]),
    (T['struct'],   T['stretch'], [(.25, 'WEBGL MOSTRA'), (2, 'O ESQUELETO 3D.')]),
    (T['stretch'],  T['fov'],     [(.25, 'A WEB AUDIO API'), (2, 'DISTORCE O SOM.')]),
    (T['fov'],      T['scan'],    [(.25, 'A LENTE DA CÂMERA'), (2, 'VIRA FILTRO DE ÁUDIO.')]),
    (T['scan'],     T['orbit'],   [(0, '10 FAIXAS.'), (1, '10 FREQUÊNCIAS.'), (10, 'CADA UMA COM SUA COR.')]),
    (T['orbit'],    T['pitch'],   [(0, 'GLSL + THREE.JS:'), (2, '3D DIRETO NO NAVEGADOR.')]),
    (T['pitch'],    T['card'] - B,[(0, 'E O SEU PROJETO?'), (4, 'ÁLBUM. CLIPE. SHOW.'), (5.5, 'EXPOSIÇÃO. MARCA.'), (8, 'TAMBÉM PODE VIRAR'), (9, 'UMA EXPERIÊNCIA.')]),
]
CPS = 30

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
def caption_layer(lines, color, blink, y=330, sz0=96):
    key = (tuple(lines), color, blink, y, sz0)
    if key in cap_cache: return cap_cache[key]
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    col = hex2rgb(color)
    txtcol = tuple(int(c * .45 + 255 * .55) for c in col)
    for i, (txt, typing) in enumerate(lines):
        sz = sz0; f = font(sz)
        shown = txt + ('█' if (typing or (i == len(lines) - 1 and blink)) else '')
        full_w = d.textlength(txt + '█', font=f)
        while full_w > 900 and sz > 50:
            sz -= 4; f = font(sz); full_w = d.textlength(txt + '█', font=f)
        tw = d.textlength(shown, font=f)
        x, pad = 70, 18
        d.rectangle((x - pad, y - 6, x + tw + pad, y + sz + 4), fill=(20, 10, 5, 215), outline=col + (255,), width=3)
        d.text((x, y - sz * 0.12), shown, font=f, fill=txtcol + (255,))
        y += sz + 42
    glow = lay.filter(ImageFilter.GaussianBlur(14))
    arr = np.asarray(Image.alpha_composite(glow, lay)).astype(np.float32)
    cap_cache[key] = arr
    if len(cap_cache) > 64: cap_cache.pop(next(iter(cap_cache)))
    return arr

# ------------------------------------------------------------------ live code panel (real lines from index.htm, live values)
def code_for(t):
    if T['ignite'] + B <= t < T['speed']:
        return 'index.htm — HTML', ['<div id="canvas-container"></div>',
                                    '<script type="module">',
                                    "  import * as THREE from 'three';",
                                    "  loader.load('Horse.glb', ...);"]
    if T['speed'] <= t < T['struct']:
        v = kf(SPEED_K, (t - T['speed']) / B)
        return 'JAVASCRIPT', [f'speedSlider.value = {v:.0f};',
                              f'mixer.timeScale = {v / 100 * 2:.2f};',
                              f'bgMusic.playbackRate = {max(0.1, v / 100):.2f};']
    if T['struct'] <= t < T['stretch']:
        s = kf(STRUCT_K, (t - T['struct']) / B) / 100
        return 'THREE.JS / WEBGL', ['new THREE.MeshBasicMaterial({',
                                    '  wireframe: true, transparent: true });',
                                    f'wireMaterial.opacity = {s:.2f};']
    if T['stretch'] <= t < T['fov']:
        s = kf(STRETCH_K, (t - T['stretch']) / B) / 100
        return 'WEB AUDIO API', [f'horseModel.scale.y = {0.025 * (1 + s * 3):.4f};',
                                 'distortionNode = ctx.createWaveShaper();',
                                 f'distortionNode.curve = makeDistortionCurve({s * 400:.0f});']
    if T['fov'] <= t < T['scan']:
        fv = kf(FOV_K, (t - T['fov']) / B)
        tt = max(0, (fv - 40) / 80)
        return 'WEB AUDIO API', [f'camera.fov = {fv:.0f};',
                                 f'fovFilterLow.frequency  = {22000 * 0.15 ** tt:.0f}; // Hz',
                                 f'fovFilterHigh.frequency = {20 + tt ** 2 * 700:.0f}; // Hz']
    if T['scan'] <= t < T['orbit']:
        i = int(min(9, max(0, (t - T['scan']) // B)))
        return 'JAVASCRIPT + CSS', [f'changeTrack({i});',
                                    f'bgMusic.src = tracks[{i}].url;',
                                    f"--primary-color: {THEMES[i]};"]
    if T['orbit'] <= t < T['orbit'] + 7 * B:
        b = (t - T['orbit']) / B
        mat = 'horseMaterial' if 2 <= b < 6 else 'ghostMaterial'
        return 'GLSL', ['gl_PointSize = size * blink * (300.0 / -mv.z);',
                        'gl_FragColor = vec4(color, 1.0);',
                        f'horseModel.material = {mat};']
    return None, None

TOK = re.compile(r"(//.*$)|('[^']*'|\"[^\"]*\")|(\b\d+(?:\.\d+)?\b|#[0-9a-fA-F]{6})|(\b(?:new|const|import|from|true|false|vec4|float)\b)|(<[^>]*>)|([A-Za-z_][\w.]*)|(.)")

def code_layer(title, lines, color):
    col = hex2rgb(color)
    cream = tuple(int(c * .3 + 255 * .7) for c in col)
    fs = 42; lh = 50
    h = 64 + lh * len(lines) + 18
    x0, x1, y0 = 40, W - 40, 0
    lay = Image.new('RGBA', (W, h + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    d.rectangle((x0, y0, x1, y0 + h), fill=(12, 7, 3, 225), outline=col + (255,), width=3)
    d.rectangle((x0, y0, x1, y0 + 46), fill=col + (255,))
    d.text((x0 + 18, y0 + 2), f'> {title}', font=font(40), fill=(20, 10, 5, 255))
    f = font(fs)
    for li, line in enumerate(lines):
        x = x0 + 22; y = y0 + 60 + li * lh
        for m in TOK.finditer(line):
            s = m.group(0)
            if m.group(1): c = (150, 130, 110)
            elif m.group(2): c = (180, 230, 140)
            elif m.group(3): c = (255, 255, 255)
            elif m.group(4) or m.group(5): c = col
            else: c = cream
            d.text((x, y), s, font=f, fill=c + (255,))
            x += d.textlength(s, font=f)
    glow = lay.filter(ImageFilter.GaussianBlur(10))
    return np.asarray(Image.alpha_composite(glow, lay)).astype(np.float32)

STACK = ['HTML', 'CSS', 'JAVASCRIPT', 'THREE.JS', 'WEBGL', 'GLSL', 'WEB AUDIO']
def chips_layer(n, color, y=0, sz=44, center=False):
    col = hex2rgb(color)
    lay = Image.new('RGBA', (W, 220), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    f = font(sz)
    rows, cur, wsum = [], [], 0
    for c in STACK[:n]:
        w = d.textlength(c, font=f) + 36
        if wsum + w > 940 and cur: rows.append(cur); cur, wsum = [], 0
        cur.append((c, w)); wsum += w + 14
    if cur: rows.append(cur)
    for ri, row in enumerate(rows):
        tot = sum(w for _, w in row) + 14 * (len(row) - 1)
        x = (W - tot) / 2 if center else 70 - 18
        yy = 10 + ri * (sz + 34)
        for c, w in row:
            d.rectangle((x, yy, x + w, yy + sz + 14), fill=col + (255,))
            d.text((x + 18, yy + 2), c, font=f, fill=(20, 10, 5, 255))
            x += w + 14
    glow = lay.filter(ImageFilter.GaussianBlur(10))
    return np.asarray(Image.alpha_composite(glow, lay)).astype(np.float32)

def freq_layer(i, color):
    col = hex2rgb(color)
    lay = Image.new('RGBA', (W, 200), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    txt = f'FREQ {i + 1:02d}/10'
    d.text((70, 0), txt, font=font(150), fill=tuple(int(c * .5 + 255 * .5) for c in col) + (255,))
    glow = lay.filter(ImageFilter.GaussianBlur(16))
    return np.asarray(Image.alpha_composite(glow, lay)).astype(np.float32)

def card_layer(t, color):
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    col = hex2rgb(color)
    cream = tuple(int(c * .35 + 255 * .65) for c in col)
    bt = (t - T['card']) / B
    def centered(txt, y, sz, fill, box=None):
        f = font(sz); tw = d.textlength(txt, font=f); x = (W - tw) / 2
        if box == 'solid':
            d.rectangle((x - 34, y - 14, x + tw + 34, y + sz + 8), fill=col + (255,))
        elif box == 'outline':
            d.rectangle((x - 30, y - 12, x + tw + 30, y + sz + 6), fill=(20, 10, 5, 215), outline=col + (255,), width=3)
        d.text((x, y - sz * 0.12), txt, font=f, fill=fill)
    w1 = 'SITES INTERATIVOS'
    n = min(len(w1), int(bt * B * 34) + 1)
    centered(w1[:n], 330, 124, cream + (255,))
    if bt >= 0.5: centered('PARA ARTISTAS', 470, 124, cream + (255,))
    if bt >= 1.75: centered('VEJA FUNCIONANDO:', 800, 46, col + (255,))
    if bt >= 2: centered('dezerthorse.github.io/cavalo', 870, 66, (20, 10, 5, 255), box='solid')
    if bt >= 3: centered('FALE COM @GANWALK', 1060, 70, cream + (255,), box='outline')
    glow = lay.filter(ImageFilter.GaussianBlur(16))
    arr = np.asarray(Image.alpha_composite(glow, lay)).astype(np.float32)
    return arr, bt

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
def stamp_layer(color, t):
    lay = Image.new('RGBA', (W, 140), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    col = hex2rgb(color)
    on = int(t / (B)) % 2 == 0
    if on: d.ellipse((72, 52, 94, 74), fill=(255, 40, 40, 235))
    tc = f'00:{int(t // 60):02d}:{int(t % 60):02d}'
    d.text((106, 36), f'AO VIVO  {tc}  //  DEZERTHORSE.GITHUB.IO/CAVALO', font=font(38), fill=col + (220,))
    return np.asarray(lay).astype(np.float32)
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

# ------------------------------------------------------------------ glitch intensity driven by the edit
CUTS = [T['ignite'], T['speed'], T['struct'], T['stretch'], T['fov'], T['scan'], T['orbit'], T['pitch'], T['card']]
SCAN_CUTS = [T['scan'] + k * B for k in range(1, 11)]

def intensity(t):
    g = 0.0
    bp = (t % B) / B
    g += 0.16 * np.exp(-bp * B / 0.07)
    for c in CUTS:
        dt = t - c
        if -0.1 < dt < 0.35: g = max(g, 1.0 * np.exp(-max(dt, 0) / 0.12))
    for c in SCAN_CUTS:
        dt = t - c
        if 0 <= dt < 0.2: g = max(g, 0.75 * np.exp(-dt / 0.07))
    if T['stretch'] <= t < T['fov']:
        g = max(g, 0.55 * kf(STRETCH_K, (t - T['stretch']) / B) / 100)
    if T['orbit'] + 7 * B <= t < T['pitch']:
        g = max(g, 0.6)
    if T['card'] - B <= t < T['card']:
        g = max(g, 0.35 + 0.5 * (t - T['card'] + B) / B)          # tape stop
    if t < 0.4:
        g = max(g, 0.5 * (1 - t / 0.4))                            # loop seam
    if t >= T['away']:
        g = max(g, 0.15 + 0.6 * ((t - T['away']) / (T['end'] - T['away'])) ** 2)
    return float(min(g, 1.0))

def load(f):
    d = 'frames' if REUSE[0] <= f <= REUSE[1] else 'frames2'
    p = f'{d}/f{f:04d}.png'
    if not os.path.exists(p):
        cands = sorted(glob.glob('frames2/f*.png')) + [f'frames/f{k:04d}.png' for k in range(REUSE[0], REUSE[1] + 1)]
        p = min(cands, key=lambda c: abs(int(c[-8:-4]) - f))
    return np.asarray(Image.open(p).convert('RGB').resize((W, H))).astype(np.float32)

frames = ONLY if ONLY else range(NF)
proc = None
if not ONLY:
    proc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y',
        '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
        '-f', 'f32le', '-ar', '48000', '-ac', '2', '-i', 'mix2.f32',
        '-af', 'loudnorm=I=-14:TP=-1.0:LRA=11',
        '-c:v', 'libx264', '-preset', 'slow', '-crf', '21', '-maxrate', '12M', '-bufsize', '24M',
        '-pix_fmt', 'yuv420p', '-profile:v', 'high', '-level', '4.2', '-g', '30',
        '-c:a', 'aac', '-b:a', '256k', '-ar', '48000', '-movflags', '+faststart', '-shortest', OUT], stdin=subprocess.PIPE)

prev = None
trail = None
for f in frames:
    t = f / FPS
    rng = np.random.default_rng(f * 7 + 3)
    m = meta.get(f) or (meta.get(min(meta, key=lambda k: abs(k - f))) if meta else {})
    color = (m or {}).get('color') or '#ff6600'
    img = load(f)

    if T['speed'] <= t < T['struct']:
        sp = kf(SPEED_K, (t - T['speed']) / B)
        a = min(0.8, abs(sp - 100) / 100 * 0.75)
        if trail is not None and a > 0.02:
            img = img * (1 - a) + trail * a
    trail = img.copy()

    if T['struct'] <= t < T['stretch']:
        s = kf(STRUCT_K, (t - T['struct']) / B) / 100
        if s > 0.03:
            px = pixelate(img, s)
            band_h = int(H * (0.08 + 0.35 * s))
            y0 = int((np.sin(t * 5) * 0.5 + 0.5) * (H * 0.55 - band_h) + H * 0.2)
            img[y0:y0+band_h] = px[y0:y0+band_h]

    if T['fov'] <= t < T['scan']:
        img = radial_ab(img, abs(kf(FOV_K, (t - T['fov']) / B) - 40) * 0.35)

    g = intensity(t)
    img = chroma(img, int(2 + g * 26))
    if g > 0.25:
        img = mosh(img, prev, g, rng)
        img = slices(img, g, rng)
    if g > 0.7 and rng.random() < 0.6:
        img = pixelsort(img, rng, g)

    dti = t - T['ignite']
    if 0 <= dti < 0.2:
        img = img + (255 - img) * float(0.6 * np.exp(-dti / 0.06))

    # overlays
    jitter = int(g * 18) if g > 0.3 else 0
    if T['card'] <= t:
        lay, bt = card_layer(t, color)
        if t >= T['away']:
            jitter = int(rng.integers(10, 30 + int(80 * (t - T['away']) / (T['end'] - T['away']))))
        img = over(img, lay, 0, jitter)
        if bt >= 0.75:
            img = over(img, chips_layer(min(len(STACK), int((bt - 0.75) * 6) + 1), color, sz=40, center=True), 630, jitter)
    else:
        lines, left = caption_state(t)
        if lines:
            blink = int(t / (B / 2)) % 2 == 0
            lay = caption_layer(lines, color, blink)
            dx = jitter if left >= 0.1 else int(rng.integers(20, 60))
            img = over(img, lay, 0, dx)
        # stack chips during the "virou um site" beat
        if T['ignite'] + 3.5 * B <= t < T['speed']:
            n = int((t - T['ignite'] - 3.5 * B) / (B / 2)) + 1
            img = over(img, chips_layer(min(n, len(STACK)), color), 610, jitter)
        if T['scan'] <= t < T['orbit']:
            i = int(min(9, max(0, (t - T['scan']) // B)))
            img = over(img, freq_layer(i, color), 620 if t < T['scan'] + 10 * B else 760, jitter)
        title, code = code_for(t)
        if code:
            cl = code_layer(title, code, color)
            y = 1060 if not (T['ignite'] <= t < T['speed']) else 1180
            if T['orbit'] <= t < T['pitch']: y = 900
            img = over(img, cl, y, jitter)
    if t < T['away']:
        img = over(img, stamp_layer(color, t), 110)

    th = (m or {}).get('thumb')
    if th and not (T['scan'] <= t < T['orbit']) and T['speed'] <= t < T['pitch']:
        img = ring(img, th['x'] * 2, th['y'] * 2, T['orbit'] <= t < T['pitch'], color)

    img = img * scan_mask
    img = img + np.repeat(np.repeat(grain[f % 8], 2, 0), 2, 1)
    img = img * vign
    img = np.clip(img, 0, 255)
    prev = img.copy()
    out8 = img.astype(np.uint8)
    if proc:
        proc.stdin.write(out8.tobytes())
    else:
        Image.fromarray(out8).save(f'pv2_{f:04d}.png')
    if f % 60 == 0: print('post', f, flush=True)

if proc:
    proc.stdin.close(); proc.wait()
    print('done', OUT)
