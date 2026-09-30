const fs = require('fs');
const { open } = require('./common');
const { B, BAR, FPS, T } = require('./timeline');
const DPR = parseFloat(process.env.DPR || '2');
const OUT = process.env.OUT || 'frames';
const F0 = parseInt(process.env.F0 || '0'), F1 = parseInt(process.env.F1 || String(Math.round(T.end * FPS)));
const STRIDE = parseInt(process.env.STRIDE || '1');
fs.mkdirSync(OUT, { recursive: true });

const clamp = (x, a, b) => Math.max(a, Math.min(b, x));
const ease = (x) => { x = clamp(x, 0, 1); return x < .5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2; };
const outC = (x) => 1 - Math.pow(1 - clamp(x, 0, 1), 3);
const lerp = (a, b, x) => a + (b - a) * x;
// keyframes in beats relative to scene start: [[beat, value], ...] with eased segments
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

// director: returns what the page should look like at time t
function direct(t) {
  const p = { mode: 'site', hud: null, slider: null, cam: null, track: null, ghost: true };
  if (t < T.click) {
    p.mode = 'loading';
    const x = t / (1.5 * BAR);
    p.progress = clamp(x, 0, 1) * 100;
    const terms = ["INICIALIZANDO SISTEMA...", "ALINHANDO VÉRTEBRAS...", "CARREGANDO MATRIZ ÓSSEA...", "POLINDO TEXTURAS...", "OTIMIZANDO GALOPE...", "SINCRONIZANDO TROTE...", "INJETANDO ALGORITMOS...", "RENDERIZANDO DESERTO..."];
    p.loadText = x >= 1 ? 'SISTEMA PRONTO' : terms[Math.floor(t / (B / 2)) % terms.length];
    p.ready = x >= 1;
    p.cam = orbit(45, 60, 25, 2);
    return p;
  }
  if (t >= T.loop) { p.mode = 'loading'; p.progress = 100; p.loadText = 'SISTEMA PRONTO'; p.ready = true; p.cam = orbit(45, 60, 25, 2); return p; }
  p.track = 9;
  // intro swoop
  if (t < T.speed) {
    const x = outC((t - T.click) / (T.speed - T.click));
    const a = lerp(80, 40, x), r = lerp(70, 17, x), h = lerp(30, 3.2, x);
    p.cam = orbit(a, r, h, lerp(0, 2.2, x));
    return p;
  }
  const sceneBeat = (s) => (t - s) / B;
  if (t < T.scan) {
    // slow drift around horse across the 4 control scenes
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
    // frequency scan: hard cut per beat, new track per beat
    const b = sceneBeat(T.scan);
    p.hud = 'freq';
    const seq = [0, 1, 2, 3, 4, 5, 6, 7, 8];
    const idx = b < 7 ? Math.floor(b) : (b < 7.5 ? 7 : 8);
    p.track = seq[clamp(idx, 0, 8)];
    const angles = [[20, 12, 1.5, 2.5], [120, 15, 6, 2], [-60, 13, 1.0, 3], [200, 18, 9, 1.5], [70, 10, 2.5, 3], [-150, 16, 4, 2], [0, 20, 12, 1], [100, 11, 1.2, 3], [250, 14, 3, 2.5]];
    const a = angles[p.track];
    const within = b - Math.floor(b);
    p.cam = orbit(a[0] + within * 12, a[1], a[2], a[3]);
    p.slider = { id: 'radio-dial', v: p.track, noInput: true };
    return p;
  }
  if (t < T.cta) {
    const b = sceneBeat(T.orbit);
    p.hud = b < 7 ? 'ghost' : null;
    p.ghost = !(b >= 2 && b < 6);
    p.ghostPress = (b >= 2 && b < 2.5) || (b >= 6 && b < 6.5);
    const x = ease(b / 8);
    p.cam = orbit(lerp(40, 40 + 360, x), lerp(13, 18, x), lerp(1.4, 4, Math.sin(x * Math.PI)), 2.2);
    return p;
  }
  // CTA: pull back wide
  const x = outC((t - T.cta) / (T.loop - T.cta));
  p.cam = orbit(lerp(40, 70, x), lerp(18, 34, x), lerp(4, 11, x), lerp(2.2, 4.5, x));
  return p;
}

const APPLY = (p) => {
  const d = window.__dh, st = d.state;
  const ls = document.getElementById('loading-screen');
  document.body.dataset.hud = p.hud || '';
  if (p.mode === 'loading') {
    ls.style.display = 'flex'; ls.style.opacity = 1;
    document.getElementById('progress-container').style.display = p.ready ? 'none' : 'block';
    document.getElementById('progress-fill').style.width = p.progress + '%';
    document.getElementById('loading-text').innerText = p.loadText;
    document.getElementById('start-btn').style.display = p.ready ? 'block' : 'none';
  } else {
    if (ls.style.display !== 'none') { ls.style.display = 'none'; st.loaded = true; st.introFinished = true; d.controls.enabled = true; d.controls.enableDamping = false; }
  }
  if (p.track !== null && window.__curTrack !== p.track) { d.changeTrack(p.track); window.__curTrack = p.track; }
  const hud = document.getElementById('hud');
  if (p.hud) hud.classList.remove('collapsed'); else hud.classList.add('collapsed');
  if (st.ghostMode !== p.ghost) document.getElementById('ghost-btn').click();
  document.getElementById('ghost-btn').classList.toggle('pressed', !!p.ghostPress);
  let thumb = null;
  if (p.slider) {
    const el = document.getElementById(p.slider.id);
    const v = Math.round(p.slider.v);
    if (String(el.value) !== String(v) && !p.slider.noInput) { el.value = v; el.dispatchEvent(new Event('input', { bubbles: true })); }
    if (p.slider.noInput) el.value = v;
    const r = el.getBoundingClientRect(), mn = +el.min, mx = +el.max;
    const tw = 24;
    thumb = { x: r.left + tw / 2 + (v - mn) / (mx - mn) * (r.width - tw), y: r.top + r.height / 2 };
  }
  if (p.ghostPress) { const r = document.getElementById('ghost-btn').getBoundingClientRect(); thumb = { x: r.left + r.width / 2, y: r.top + r.height / 2 }; }
  if (p.cam) { d.camera.position.set(...p.cam.pos); d.controls.target.set(...p.cam.tgt); }
  window.__step(1000 / 30);
  return { thumb, color: getComputedStyle(document.documentElement).getPropertyValue('--primary-color').trim() };
};

const CSS = `
  *, *::before, *::after { transition: none !important; }
  #presave-popup, #cam-tooltip, #hud-toggle-btn, .desktop-footer { display: none !important; }
  #hud { top: auto !important; bottom: 215px !important; max-height: none !important; padding: 12px 15px !important; }
  #hud .hud-header { margin-bottom: 6px !important; }
  #hud .control-group, #hud .data-stream { display: none !important; }
  body[data-hud="freq"]   #hud .control-group[data-i="0"],
  body[data-hud="speed"]  #hud .control-group[data-i="1"],
  body[data-hud="struct"] #hud .control-group[data-i="2"],
  body[data-hud="stretch"] #hud .control-group[data-i="3"],
  body[data-hud="fov"]    #hud .control-group[data-i="4"],
  body[data-hud="ghost"]  #hud .control-group[data-i="5"] { display: block !important; border-bottom: none !important; margin-bottom: 0 !important; padding-bottom: 0 !important; }
  body[data-hud="ghost"] #hud .data-stream { display: block !important; max-height: 70px; overflow: hidden; }
  #ghost-btn.pressed { filter: invert(1); }
`;

(async () => {
  const { b, page } = await open(DPR);
  await page.waitForFunction(() => getComputedStyle(document.getElementById('start-btn')).display === 'block', null, { timeout: 120000 });
  await page.addStyleTag({ content: CSS });
  await page.evaluate(() => {
    // tag control groups in order for CSS
    const hud = document.getElementById('hud');
    [...hud.querySelectorAll('.control-group')].forEach((g, i) => g.dataset.i = i);
    window.__goManual();
  });
  // real start (audio init etc.), then warm up
  await page.evaluate(() => { document.getElementById('start-btn').click(); });
  await page.waitForTimeout(1500);
  await page.evaluate(() => { for (let i = 0; i < 5; i++) window.__step(33); });
  const meta = {};
  let t0 = Date.now();
  for (let f = 0; f < F1; f++) {
    const t = f / FPS;
    const r = await page.evaluate(APPLY, direct(t));
    if (f >= F0 && f % STRIDE === 0) {
      const path = `${OUT}/f${String(f).padStart(4, '0')}.png`;
      if (!fs.existsSync(path)) {
        for (let k = 0; k < 4; k++) {
          try { await page.screenshot({ path: path + '.tmp.png', timeout: 240000 }); fs.renameSync(path + '.tmp.png', path); break; }
          catch (e) { console.log('retry', f, e.message.split('\n')[0]); }
        }
      }
      meta[f] = r;
      if (f % 30 === 0) fs.writeFileSync(`${OUT}/meta_${F0}_${F1}.json`, JSON.stringify(meta));
    }
    if (f % 30 === 0) console.log('frame', f, ((Date.now() - t0) / 1000).toFixed(0) + 's');
  }
  fs.writeFileSync(`${OUT}/meta_${F0}_${F1}.json`, JSON.stringify(meta));
  await b.close();
})();
