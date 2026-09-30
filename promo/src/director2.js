const { B, BAR, T } = require('./timeline2');
const clamp = (x, a, b) => Math.max(a, Math.min(b, x));
const ease = (x) => { x = clamp(x, 0, 1); return x < .5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2; };
const outC = (x) => 1 - Math.pow(1 - clamp(x, 0, 1), 3);
const lerp = (a, b, x) => a + (b - a) * x;
function kf(keys, beat) {
  if (beat <= keys[0][0]) return keys[0][1];
  for (let i = 0; i < keys.length - 1; i++) {
    const [b0, v0] = keys[i], [b1, v1] = keys[i + 1];
    if (beat <= b1) return lerp(v0, v1, ease((beat - b0) / (b1 - b0)));
  }
  return keys[keys.length - 1][1];
}
function orbit(angDeg, r, h, ty) {
  const a = angDeg * Math.PI / 180;
  return { pos: [Math.sin(a) * r, h, Math.cos(a) * r], tgt: [0, ty, 0] };
}
const FAR = [70, 36, 4.5, 2];   // opening shot == closing shot (loop)

function direct(t) {
  const p = { mode: 'site', hud: null, slider: null, cam: null, track: null, ghost: true };
  const sceneBeat = (s) => (t - s) / B;
  if (t < T.speed) {
    // far horse in the haze, slow approach; colors ignite on bar 2
    if (t >= T.ignite) p.track = 9;
    const x = ease(t / T.speed);
    p.cam = orbit(lerp(FAR[0], 40, x), lerp(FAR[1], 17, x), lerp(FAR[2], 3.2, x), lerp(FAR[3], 2.2, x));
    return p;
  }
  p.track = 9;
  if (t < T.scan) {   // identical to v1 (frames reused)
    const u = (t - T.speed) / (T.scan - T.speed);
    let ang = lerp(40, 5, u), r = 17, h = 3.2, ty = 2.2;
    if (t < T.struct) { const b = sceneBeat(T.speed); p.hud = 'speed'; p.slider = { id: 'speed-slider', v: kf([[0.5, 100], [2, 15], [3, 15], [5, 200], [6.5, 200], [7.5, 100]], b) }; }
    else if (t < T.stretch) { const b = sceneBeat(T.struct); p.hud = 'struct'; p.slider = { id: 'structure-slider', v: kf([[0.5, 0], [2.5, 100], [4.5, 100], [5, 30], [5.5, 100], [6, 30], [6.5, 100]], b) }; ang = lerp(ang, ang + 50, ease(b / 8)); r = 14; }
    else if (t < T.fov) { const b = sceneBeat(T.stretch); p.hud = 'stretch'; const s = kf([[0.5, 0], [3, 100], [5, 100], [5.5, 40], [6, 100], [7.6, 0]], b); p.slider = { id: 'stretch-slider', v: s }; r = 17 + s / 100 * 26; h = 3.2 + s / 100 * 9; ty = 2.2 + s / 100 * 9; }
    else { const b = sceneBeat(T.fov); p.hud = 'fov'; p.slider = { id: 'fov-slider', v: kf([[0.5, 40], [2.5, 120], [4, 120], [5.5, 20], [7, 20], [7.8, 40]], b) }; }
    p.cam = orbit(ang, r, h, ty);
    return p;
  }
  if (t < T.orbit) {
    // 10 frequencies: one per beat, then hold on 10
    const b = sceneBeat(T.scan);
    p.hud = 'freq';
    p.track = clamp(Math.floor(b), 0, 9);
    const angles = [[20, 12, 1.5, 2.5], [120, 15, 6, 2], [-60, 13, 1.0, 3], [200, 18, 9, 1.5], [70, 10, 2.5, 3], [-150, 16, 4, 2], [0, 20, 12, 1], [100, 11, 1.2, 3], [250, 14, 3, 2.5], [40, 17, 3.2, 2.2]];
    const a = angles[p.track];
    if (b < 10) p.cam = orbit(a[0] + (b - Math.floor(b)) * 12, a[1], a[2], a[3]);
    else { const x = ease((b - 10) / 2); p.cam = orbit(lerp(40, 20, x), lerp(17, 13, x), lerp(3.2, 2, x), 2.2); }
    p.slider = { id: 'radio-dial', v: p.track, noInput: true };
    return p;
  }
  if (t < T.pitch) {
    const b = sceneBeat(T.orbit);
    p.hud = b < 7 ? 'ghost' : null;
    p.ghost = !(b >= 2 && b < 6);
    p.ghostPress = (b >= 2 && b < 2.5) || (b >= 6 && b < 6.5);
    const x = ease(b / 8);
    p.cam = orbit(lerp(20, 20 + 360, x), lerp(13, 18, x), lerp(2, 4, Math.sin(x * Math.PI)), 2.2);
    return p;
  }
  if (t < T.away) {
    // pitch + end card: slow drift, wide enough for text
    const x = ease((t - T.pitch) / (T.away - T.pitch));
    p.cam = orbit(lerp(20, 60, x), lerp(18, 28, x), lerp(4, 8, x), lerp(2.2, 3.5, x));
    return p;
  }
  // pull away back into the opening shot, colors return to track 01 → seamless loop
  const x = ease((t - T.away) / (T.end - T.away));
  if (t >= T.end - B) p.track = 0;
  p.cam = orbit(lerp(60, FAR[0], x), lerp(28, FAR[1], x), lerp(8, FAR[2], x), lerp(3.5, FAR[3], x));
  return p;
}
module.exports = { direct };
