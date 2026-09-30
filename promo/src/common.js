const { chromium } = require('playwright');
const INIT = `
(() => {
  let vt = 0; const realNow = performance.now.bind(performance);
  let manual = false; const q = new Map(); let id = 0;
  const realRAF = window.requestAnimationFrame.bind(window);
  performance.now = () => manual ? vt : realNow();
  window.requestAnimationFrame = (cb) => { if (!manual) return realRAF(cb); const i=++id; q.set(i, cb); return i; };
  window.cancelAnimationFrame = (i) => q.delete(i);
  window.__goManual = () => { vt = realNow(); manual = true; };
  window.__step = (ms) => { vt += ms; const cbs=[...q.values()]; q.clear(); cbs.forEach(cb => cb(vt)); };
  // silence audio: never actually play (no 'ended' auto-advance)
  HTMLMediaElement.prototype.play = function(){ return Promise.resolve(); };
  Math.random = (() => { let s = 1337; return () => { s = (s * 1664525 + 1013904223) >>> 0; return s / 4294967296; }; })();
})();`;
const EXPOSE = `
        window.__dh = { THREE, scene, camera, controls, state, focusOffset, targetCamPos, wireMaterial, ghostMaterial, horseMaterial,
          changeTrack: (i) => window.changeTrack(i), toggleHud, updateThemeColors,
          get horse() { return horseModel; }, get wire() { return wireModel; }, get mixer() { return mixer; } };
        simulateLoading();`;
async function open(DPR = 2) {
  const b = await chromium.launch({ channel: 'chromium', proxy: { server: 'http://127.0.0.1:39717' },
    args: ['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist'] });
  const ctx = await b.newContext({ viewport: { width: 540, height: 960 }, deviceScaleFactor: DPR });
  await ctx.addInitScript(INIT);
  const page = await ctx.newPage();
  page.on('pageerror', e => console.log('ERR', e.message));
  await page.route('https://dezerthorse.github.io/cavalo/', async (route) => {
    const r = await route.fetch(); let html = await r.text();
    const re = /simulateLoading\(\);\s*animate\(\);/;
    if (!re.test(html)) console.log('WARN patch anchor missing');
    html = html.replace(re, EXPOSE + '\n        animate();');
    await route.fulfill({ response: r, body: html });
  });
  await page.goto('https://dezerthorse.github.io/cavalo/', { waitUntil: 'load', timeout: 90000 });
  await page.waitForFunction(() => window.__dh && window.__dh.state.modelReady, null, { timeout: 120000 });
  return { b, page };
}
module.exports = { open };
