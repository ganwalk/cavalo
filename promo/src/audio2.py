"""Sound design for the reel: the album track reacts to the same controls the video shows,
using the site's own audio formulas (playbackRate = trote, WaveShaper curve, FOV filters)."""
import numpy as np
from scipy.signal import butter, lfilter, lfilter_zi, sosfilt

SR = 48000
B = 60 / 152
BAR = 4 * B
T = dict(ignite=2*BAR, speed=4*BAR, struct=6*BAR, stretch=8*BAR, fov=10*BAR, scan=12*BAR,
         orbit=15*BAR, pitch=17*BAR, card=20*BAR, away=21.25*BAR, end=22*BAR)
N = int(round(T['end'] * SR))
PHASE = 0.019737
OFF = PHASE + 8 * BAR          # start inside the loop, on the grid

rng = np.random.default_rng(7)

def load(path):
    return np.fromfile(path, dtype=np.float32).reshape(-1, 2).astype(np.float64)

song = load('audio.f32')
tracks = {i: load(f'tracks/{i}.f32') for i in range(9)}
tracks[9] = song

t = np.arange(N) / SR

def ease(x):
    x = np.clip(x, 0, 1)
    return np.where(x < .5, 4*x**3, 1 - (-2*x + 2)**3 / 2)

def kf(keys, beat):
    beat = np.asarray(beat, dtype=float)
    out = np.full(beat.shape, keys[0][1], dtype=float)
    for (b0, v0), (b1, v1) in zip(keys[:-1], keys[1:]):
        m = (beat > b0) & (beat <= b1)
        out[m] = v0 + (v1 - v0) * ease((beat[m] - b0) / (b1 - b0))
    out[beat > keys[-1][0]] = keys[-1][1]
    return out

def read_at(src, pos):
    """linear-interpolated read of stereo src at fractional sample positions (wraps)."""
    L = len(src)
    pos = np.mod(pos, L - 1)
    i = np.floor(pos).astype(np.int64)
    f = (pos - i)[:, None]
    return src[i] * (1 - f) + src[np.minimum(i + 1, L - 1)] * f

def seg(a, b):
    return (t >= a) & (t < b)

# ---------------------------------------------------------------- source position (varispeed)
rate = np.ones(N)
sp = seg(T['speed'], T['struct'])
beat_sp = (t[sp] - T['speed']) / B
rate[sp] = np.maximum(0.1, kf([[0.5, 100], [2, 15], [3, 15], [5, 200], [6.5, 200], [7.5, 100]], beat_sp) / 100)
# grid position + accumulated varispeed drift, reset (re-locked) at bar lines
drift = np.zeros(N)
for a_, b_ in ((T['speed'], T['struct']),):
    m = seg(a_, b_)
    drift[m] = np.concatenate([[0], np.cumsum(rate[m] - 1)[:-1]])
pos = (OFF + t) * SR + drift
music = read_at(song, pos)
# 8ms crossfades across the re-lock seams
for tc in (T['struct'],):
    k = int(round(tc * SR)); w = int(0.008 * SR)
    pre = read_at(song, pos[k - 1] + np.arange(1, w + 1) * rate[k - 1])
    fade = np.linspace(0, 1, w)[:, None]
    music[k:k+w] = pre * (1 - fade) + music[k:k+w] * fade

# ---------------------------------------------------------------- estrutura de dados -> bitcrush
st = seg(T['struct'], T['stretch'])
s = kf([[0.5, 0], [2.5, 100], [4.5, 100], [5, 30], [5.5, 100], [6, 30], [6.5, 100]], (t[st] - T['struct']) / B) / 100
x = music[st]
bits = 16 - s * 11.5
q = 2.0 ** (bits - 1)
hold = np.maximum(1, np.round(1 + s * 7)).astype(int)
idx = np.arange(len(x))
held = idx - (idx % hold)
crushed = np.round(x[held] * q[:, None]) / q[:, None]
music[st] = x * (1 - s[:, None] * 0.85) + crushed * (s[:, None] * 0.85)

# ---------------------------------------------------------------- alongamento -> WaveShaper (site curve)
sh = seg(T['stretch'], T['fov'])
amt = kf([[0.5, 0], [3, 100], [5, 100], [5.5, 40], [6, 100], [7.6, 0]], (t[sh] - T['stretch']) / B) / 100 * 400
x = np.clip(music[sh], -1, 1)
deg = np.pi / 180
kk = amt[:, None]
shaped = np.where(kk < 1, x, (3 + kk) * x * 20 * deg / (np.pi + kk * np.abs(x)))
# loudness compensation so the drive reads as texture, not volume
rms_in = np.sqrt(np.mean(x**2) + 1e-9); rms_out = np.sqrt(np.mean(shaped**2) + 1e-9)
music[sh] = shaped * min(1.0, rms_in / rms_out * 1.25)

# ---------------------------------------------------------------- lente (FOV) -> HP/LP (site formulas)
fv = seg(T['fov'], T['scan'])
fov = kf([[0.5, 40], [2.5, 120], [4, 120], [5.5, 20], [7, 20], [7.8, 40]], (t[fv] - T['fov']) / B)
x = music[fv].copy()
blk = 256
zi_h = zi_l = None
out = np.zeros_like(x)
for a in range(0, len(x), blk):
    tt = max(0.0, (fov[a] - 40) / 80)
    hp = 20 + tt**2 * 700
    lp = 22000 * 0.15**tt
    bh, ah = butter(2, hp / (SR / 2), 'high')
    bl, al = butter(2, min(lp, 23000) / (SR / 2), 'low')
    if zi_h is None:
        zi_h = np.zeros((2, 2)); zi_l = np.zeros((2, 2))
    y = np.zeros_like(x[a:a+blk])
    for c in range(2):
        yh, zi_h[:, c] = lfilter(bh, ah, x[a:a+blk, c], zi=zi_h[:, c])
        y[:, c], zi_l[:, c] = lfilter(bl, al, yh, zi=zi_l[:, c])
    out[a:a+blk] = y * (1.0 + tt * 1.7)
music[fv] = out

# ---------------------------------------------------------------- frequência -> radio scan across the album
def rms(a):
    return np.sqrt(np.mean(a**2) + 1e-12)

ref = rms(song[int(20*SR):int(30*SR)])
sc = seg(T['scan'], T['orbit'])
beats = (t - T['scan']) / B
trk = np.clip(np.floor(beats), 0, 10).astype(int)   # 10 = back to the song after the scan
scan = np.zeros((sc.sum(), 2))
ts = t[sc]; tr = trk[sc]
for i in range(10):
    m = tr == i
    if not m.any():
        continue
    src = tracks[i]
    start = len(src) * 0.35 if i < 9 else (OFF + ts[m][0]) * SR
    p = start + (np.arange(m.sum()))
    chunk = read_at(src, p)
    chunk *= ref / max(rms(src[int(start):int(start) + SR]), 1e-4)
    scan[m] = chunk
# short fades at every switch + tuning static bursts
switch = np.flatnonzero(np.diff(tr) != 0) + 1
env = np.ones(len(tr))
fw = int(0.006 * SR)
for s_ in switch:
    env[max(0, s_-fw):s_] *= np.linspace(1, 0, min(fw, s_))
    env[s_:s_+fw] *= np.linspace(0, 1, len(env[s_:s_+fw]))
scan *= env[:, None]
noise = rng.standard_normal((len(tr), 2))
bn, an = butter(2, [900 / (SR/2), 5200 / (SR/2)], 'band')
noise = lfilter(bn, an, noise, axis=0)
nenv = np.zeros(len(tr))
bw = int(0.07 * SR)
for s_ in np.concatenate([[0], switch]):
    nenv[s_:s_+bw] = np.maximum(nenv[s_:s_+bw], np.linspace(1, 0, len(nenv[s_:s_+bw])) ** 1.5)
scan += noise * nenv[:, None] * 0.35
back = tr == 10
scan[back] = music[sc][back] * env[back][:, None]
music[sc] = scan

# ---------------------------------------------------------------- orbit: beat-repeat into the CTA
ob = seg(T['orbit'] + 7 * B, T['pitch'])
a0 = int((T['orbit'] + 7 * B) * SR)
n = ob.sum()
local = np.arange(n)
# repeats: 1/8 for first half of the beat, then 1/16, then 1/32
lens = np.where(local < n / 2, B / 2, np.where(local < 3 * n / 4, B / 4, B / 8)) * SR
starts = np.where(local < n / 2, 0, np.where(local < 3 * n / 4, n / 2, 3 * n / 4))
music[ob] = music[a0 + (np.mod(local - starts, lens)).astype(int)]
# ghost toggles: tape-stop blips at beats 2 and 6 of the orbit
for bb in (2, 6):
    a = int((T['orbit'] + bb * B) * SR); L = int(0.12 * SR)
    r = np.linspace(1, 0.2, L)
    music[a:a+L] = read_at(music, a + np.cumsum(r))

# ---------------------------------------------------------------- opening / closing: the desert breathes open and closed (seamless loop)
def lowpass_sweep(x, f_of_t):
    out = np.zeros_like(x); zi = np.zeros((2, 2)); blk = 256
    for a in range(0, len(x), blk):
        bl, al = butter(2, min(f_of_t[a], 20000) / (SR / 2), 'low')
        for c in range(2):
            out[a:a+blk, c], zi[:, c] = lfilter(bl, al, x[a:a+blk, c], zi=zi[:, c])
    return out

static = lfilter(*butter(2, [300/(SR/2), 7000/(SR/2)], 'band'), rng.standard_normal((N, 2)), axis=0)
op = seg(0, T['ignite'])
u = t[op] / T['ignite']
music[op] = lowpass_sweep(music[op], 320 * (20000 / 320) ** (u ** 2.2)) * (0.55 + 0.35 * u)[:, None] + static[op] * 0.05
rs = seg(T['ignite'] - BAR / 2, T['ignite'])
music[rs] += static[rs] * (np.linspace(0, 1, rs.sum()) ** 2)[:, None] * 0.3
a = int(T['ignite'] * SR); L = int(0.5 * SR)
kick = np.sin(2*np.pi*np.cumsum(np.linspace(140, 40, L))/SR) * np.exp(-np.arange(L)/SR*9)
music[a:a+L] += kick[:, None] * 0.55
# tape stop on the last beat before the end card, then the drop
a = int((T['card'] - B) * SR); L = int(B * SR)
r = np.linspace(1, 0.0, L) ** 1.3
music[a:a+L] = read_at(music, a + np.cumsum(r)) * np.linspace(1, 0.3, L)[:, None]
a = int(T['card'] * SR); L = int(0.5 * SR)
music[a:a+L] += kick[:, None] * 0.5
cl = seg(T['away'], T['end'])
u = (t[cl] - T['away']) / (T['end'] - T['away'])
music[cl] = lowpass_sweep(music[cl], 20000 * (320 / 20000) ** (u ** 0.8)) * (0.9 - 0.35 * u)[:, None] + static[cl] * 0.05 * u[:, None]

# small fades at the very edges so the loop point doesn't click
e = int(0.01 * SR)
music[:e] *= np.linspace(0, 1, e)[:, None]; music[-e:] *= np.linspace(1, 0, e)[:, None]

music = np.tanh(music * 1.1) * 0.9
music.astype(np.float32).tofile('mix2.f32')
print('ok', music.shape, N / SR, 'peak', np.abs(music).max())
