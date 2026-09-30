// shared timeline (seconds). 152 BPM
const B = 60 / 152, BAR = 4 * B, FPS = 30;
const T = { click: 2 * BAR, speed: 4 * BAR, struct: 6 * BAR, stretch: 8 * BAR, fov: 10 * BAR, scan: 12 * BAR, orbit: 14 * BAR, cta: 16 * BAR, loop: 19.5 * BAR, end: 20 * BAR };
module.exports = { B, BAR, FPS, T };
