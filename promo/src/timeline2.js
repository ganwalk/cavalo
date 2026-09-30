// v2 timeline (seconds). 152 BPM, 22 bars
const B = 60 / 152, BAR = 4 * B, FPS = 30;
const T = { ignite: 2 * BAR, speed: 4 * BAR, struct: 6 * BAR, stretch: 8 * BAR, fov: 10 * BAR, scan: 12 * BAR,
  orbit: 15 * BAR, pitch: 17 * BAR, card: 20 * BAR, away: 21.25 * BAR, end: 22 * BAR };
module.exports = { B, BAR, FPS, T };
