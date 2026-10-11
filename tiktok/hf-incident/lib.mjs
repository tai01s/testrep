// Drawing kit: palette, easing, halftone fields, a 5x7 dot-matrix font,
// dot-bitmap icons and a few UI primitives. Everything is plain Canvas 2D.
export const W = 1080, H = 1920;
export const CX = 520;            // stage centre, nudged left of TikTok's button rail
export const SERIF = 'TimesNewNormal';

export const C = {
  bg: '#3D3D3D',
  halftone: '#474747',
  off: '#4A4A4A',      // unlit matrix dots
  panel: '#454545',
  panelHi: '#4E4E4E',
  line: '#5E5E5E',
  dim: '#7A7772',
  muted: '#A8A49C',
  fg: '#EEEAE2',
  yellow: '#FFD21E',
  red: '#FF5B3A',
  green: '#9BD77F',
};

// ---------- math / easing ----------
export const clamp = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v));
export const lerp = (a, b, k) => a + (b - a) * k;
export const prog = (t, s, d) => clamp((t - s) / d);
export const eo = x => 1 - Math.pow(1 - x, 3);
export const eo5 = x => 1 - Math.pow(1 - x, 5);
export const eio = x => (x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2);
export const eob = x => { const c = 1.9; return x <= 0 ? 0 : x >= 1 ? 1 : 1 + (c + 1) * Math.pow(x - 1, 3) + c * Math.pow(x - 1, 2); };
export const hash = (a, b = 0) => { const s = Math.sin(a * 127.1 + b * 311.7) * 43758.5453; return s - Math.floor(s); };
export function rgba(hex, a) {
  const n = parseInt(hex.slice(1), 16);
  return `rgba(${n >> 16},${(n >> 8) & 255},${n & 255},${a})`;
}
export function mix(h1, h2, k) {
  const a = parseInt(h1.slice(1), 16), b = parseInt(h2.slice(1), 16);
  const ch = s => Math.round(lerp((a >> s) & 255, (b >> s) & 255, clamp(k)));
  return `rgb(${ch(16)},${ch(8)},${ch(0)})`;
}

// ---------- primitives ----------
export function rr(ctx, x, y, w, h, r) {
  r = Math.min(r, w / 2, h / 2);
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.arcTo(x + w, y, x + w, y + h, r);
  ctx.arcTo(x + w, y + h, x, y + h, r);
  ctx.arcTo(x, y + h, x, y, r);
  ctx.arcTo(x, y, x + w, y, r);
  ctx.closePath();
}

// Batch many dots of one colour into a single path.
export function dots(ctx, list, color, alpha = 1) {
  if (!list.length) return;
  ctx.save();
  ctx.globalAlpha *= alpha;
  ctx.fillStyle = color;
  ctx.beginPath();
  for (const [x, y, r] of list) {
    if (r <= 0.15) continue;
    ctx.moveTo(x + r, y);
    ctx.arc(x, y, r, 0, Math.PI * 2);
  }
  ctx.fill();
  ctx.restore();
}

export function dot(ctx, x, y, r, color, alpha = 1) { dots(ctx, [[x, y, r]], color, alpha); }

export function text(ctx, s, x, y, size, color, { align = 'center', alpha = 1, baseline = 'alphabetic' } = {}) {
  ctx.save();
  ctx.globalAlpha *= alpha;
  ctx.font = `${size}px ${SERIF}`;
  ctx.fillStyle = color;
  ctx.textAlign = align;
  ctx.textBaseline = baseline;
  ctx.fillText(s, x, y);
  ctx.restore();
}

export function measure(ctx, s, size) {
  ctx.font = `${size}px ${SERIF}`;
  return ctx.measureText(s).width;
}

// Words fade/rise in one by one at their own times. items: [{w, t, color}]
export function revealLine(ctx, items, t, x, y, size, { align = 'center', rise = 22, dur = 0.38 } = {}) {
  ctx.font = `${size}px ${SERIF}`;
  const space = ctx.measureText(' ').width;
  const widths = items.map(it => ctx.measureText(it.w).width);
  const total = widths.reduce((a, b) => a + b, 0) + space * (items.length - 1);
  let cx = align === 'center' ? x - total / 2 : align === 'right' ? x - total : x;
  items.forEach((it, i) => {
    const k = eo(prog(t, it.t, dur));
    if (k > 0) text(ctx, it.w, cx, y + (1 - k) * rise, size, it.color || C.fg, { align: 'left', alpha: k * (it.alpha ?? 1) });
    cx += widths[i] + space;
  });
  return total;
}

// ---------- halftone ----------
// Background field: hex-offset dot grid whose radius follows two slow glows,
// plus a diagonal "wipe" band at scene changes.
export function halftoneBackground(ctx, T, wipe = -1, swell = 0) {
  const P = 26;
  const g1x = W * (0.2 + 0.12 * Math.sin(T * 0.21)), g1y = H * (0.18 + 0.06 * Math.cos(T * 0.17));
  const g2x = W * (0.85 + 0.1 * Math.cos(T * 0.15)), g2y = H * (0.86 + 0.05 * Math.sin(T * 0.19));
  const list = [];
  for (let j = 0, y = 0; y < H + P; j++, y += P * 0.866) {
    for (let x = (j % 2) * P / 2; x < W + P; x += P) {
      const d1 = ((x - g1x) ** 2 + (y - g1y) ** 2) / (520 * 520);
      const d2 = ((x - g2x) ** 2 + (y - g2y) ** 2) / (600 * 600);
      let f = 0.9 * Math.exp(-d1) + 0.8 * Math.exp(-d2);
      if (wipe >= 0) {
        // band travels from top-left to bottom-right
        const u = (x / W + y / H) / 2;
        const band = Math.exp(-(((u - wipe) / 0.07) ** 2));
        f += band * 1.4;
      }
      f += swell;
      const r = 0.5 + 4.2 * clamp(f, 0, 2.2) / 2.2 * 1.6;
      if (r > 0.9) list.push([x, y, Math.min(r, P * 0.48)]);
    }
  }
  dots(ctx, list, C.halftone);
}

// Shaded halftone sphere on a 45° screen.
export function halftoneSphere(ctx, cx, cy, R, { pitch = 13, color = C.fg, alpha = 1, light = [-0.55, -0.6], maxR, min = 0.1, spin = 0 } = {}) {
  maxR = maxR ?? pitch * 0.5;
  const list = [];
  const n = Math.ceil(R / pitch) + 2;
  const ca = Math.cos(Math.PI / 4), sa = Math.sin(Math.PI / 4);
  const lz = Math.sqrt(Math.max(0, 1 - light[0] ** 2 - light[1] ** 2));
  for (let i = -n; i <= n; i++) for (let j = -n; j <= n; j++) {
    const px = i * pitch, py = j * pitch;
    const x = px * ca - py * sa, y = px * sa + py * ca;
    const d2 = (x * x + y * y) / (R * R);
    if (d2 > 1) continue;
    const nz = Math.sqrt(1 - d2);
    let s = clamp((x / R) * light[0] + (y / R) * light[1] + nz * lz);
    // faint "continents" so a globe reads as a globe
    if (spin !== false) {
      const lon = Math.atan2(x / R, nz) + spin, lat = Math.asin(clamp(y / R, -1, 1));
      const land = Math.sin(lon * 3) * Math.cos(lat * 2.2) + Math.sin(lon * 1.7 + 1.3) * 0.6;
      if (land > 0.55) s = Math.min(1, s * 1.35 + 0.15);
    }
    const r = maxR * (min + (1 - min) * s);
    list.push([cx + x, cy + y, r]);
  }
  dots(ctx, list, color, alpha);
}

// Dotted outline of a rounded rect (or partial, k = 0..1 of perimeter).
export function dottedRect(ctx, x, y, w, h, r, { gap = 20, rad = 4.2, color = C.fg, alpha = 1, k = 1, start = 0, skip } = {}) {
  const pts = perimeterPoints(x, y, w, h, r, gap);
  const n = Math.floor(pts.length * clamp(k));
  const list = [];
  for (let i = 0; i < n; i++) {
    const idx = (i + Math.floor(start * pts.length)) % pts.length;
    const [px, py] = pts[idx];
    let rr_ = rad;
    if (skip) { const o = skip(px, py, idx); if (o === false) continue; if (Array.isArray(o)) { list.push(o); continue; } if (typeof o === 'number') rr_ = o; }
    list.push([px, py, rr_]);
  }
  dots(ctx, list, color, alpha);
  return pts;
}

export function perimeterPoints(x, y, w, h, r, gap) {
  // walk the rounded rect clockwise from the top-left straight edge
  const segs = [];
  const arcPts = (cx, cy, a0) => { for (let i = 0; i <= 8; i++) { const a = a0 + (i / 8) * Math.PI / 2; segs.push([cx + Math.cos(a) * r, cy + Math.sin(a) * r]); } };
  segs.push([x + r, y], [x + w - r, y]); arcPts(x + w - r, y + r, -Math.PI / 2);
  segs.push([x + w, y + h - r]); arcPts(x + w - r, y + h - r, 0);
  segs.push([x + r, y + h]); arcPts(x + r, y + h - r, Math.PI / 2);
  segs.push([x, y + r]); arcPts(x + r, y + r, Math.PI);
  // resample at equal spacing
  const out = [];
  let carry = 0;
  for (let i = 0; i < segs.length - 1; i++) {
    const [ax, ay] = segs[i], [bx, by] = segs[i + 1];
    const L = Math.hypot(bx - ax, by - ay);
    let d = carry;
    while (d < L) { out.push([ax + (bx - ax) * d / L, ay + (by - ay) * d / L]); d += gap; }
    carry = d - L;
  }
  return out;
}

// Dotted line between two points, optionally drawn to fraction k.
export function dottedLine(ctx, x1, y1, x2, y2, { gap = 16, rad = 3, color = C.fg, alpha = 1, k = 1, phase = 0 } = {}) {
  const L = Math.hypot(x2 - x1, y2 - y1);
  const list = [];
  for (let d = (phase % 1) * gap; d <= L * clamp(k); d += gap) list.push([x1 + (x2 - x1) * d / L, y1 + (y2 - y1) * d / L, rad]);
  dots(ctx, list, color, alpha);
}

// ---------- dot-matrix font (5x7) ----------
const G = {
  A: ['.###.', '#...#', '#...#', '#####', '#...#', '#...#', '#...#'],
  B: ['####.', '#...#', '#...#', '####.', '#...#', '#...#', '####.'],
  C: ['.###.', '#...#', '#....', '#....', '#....', '#...#', '.###.'],
  D: ['####.', '#...#', '#...#', '#...#', '#...#', '#...#', '####.'],
  E: ['#####', '#....', '#....', '####.', '#....', '#....', '#####'],
  F: ['#####', '#....', '#....', '####.', '#....', '#....', '#....'],
  G: ['.###.', '#...#', '#....', '#.###', '#...#', '#...#', '.###.'],
  H: ['#...#', '#...#', '#...#', '#####', '#...#', '#...#', '#...#'],
  I: ['###', '.#.', '.#.', '.#.', '.#.', '.#.', '###'],
  J: ['..###', '...#.', '...#.', '...#.', '...#.', '#..#.', '.##..'],
  K: ['#...#', '#..#.', '#.#..', '##...', '#.#..', '#..#.', '#...#'],
  L: ['#....', '#....', '#....', '#....', '#....', '#....', '#####'],
  M: ['#...#', '##.##', '#.#.#', '#.#.#', '#...#', '#...#', '#...#'],
  N: ['#...#', '#...#', '##..#', '#.#.#', '#..##', '#...#', '#...#'],
  O: ['.###.', '#...#', '#...#', '#...#', '#...#', '#...#', '.###.'],
  P: ['####.', '#...#', '#...#', '####.', '#....', '#....', '#....'],
  Q: ['.###.', '#...#', '#...#', '#...#', '#.#.#', '#..#.', '.##.#'],
  R: ['####.', '#...#', '#...#', '####.', '#.#..', '#..#.', '#...#'],
  S: ['.####', '#....', '#....', '.###.', '....#', '....#', '####.'],
  T: ['#####', '..#..', '..#..', '..#..', '..#..', '..#..', '..#..'],
  U: ['#...#', '#...#', '#...#', '#...#', '#...#', '#...#', '.###.'],
  V: ['#...#', '#...#', '#...#', '#...#', '#...#', '.#.#.', '..#..'],
  W: ['#...#', '#...#', '#...#', '#.#.#', '#.#.#', '#.#.#', '.#.#.'],
  X: ['#...#', '#...#', '.#.#.', '..#..', '.#.#.', '#...#', '#...#'],
  Y: ['#...#', '#...#', '.#.#.', '..#..', '..#..', '..#..', '..#..'],
  Z: ['#####', '....#', '...#.', '..#..', '.#...', '#....', '#####'],
  0: ['.###.', '#...#', '#..##', '#.#.#', '##..#', '#...#', '.###.'],
  1: ['..#..', '.##..', '..#..', '..#..', '..#..', '..#..', '.###.'],
  2: ['.###.', '#...#', '....#', '...#.', '..#..', '.#...', '#####'],
  3: ['#####', '...#.', '..#..', '...#.', '....#', '#...#', '.###.'],
  4: ['...#.', '..##.', '.#.#.', '#..#.', '#####', '...#.', '...#.'],
  5: ['#####', '#....', '####.', '....#', '....#', '#...#', '.###.'],
  6: ['..##.', '.#...', '#....', '####.', '#...#', '#...#', '.###.'],
  7: ['#####', '....#', '...#.', '..#..', '.#...', '.#...', '.#...'],
  8: ['.###.', '#...#', '#...#', '.###.', '#...#', '#...#', '.###.'],
  9: ['.###.', '#...#', '#...#', '.####', '....#', '...#.', '.##..'],
  ' ': ['...', '...', '...', '...', '...', '...', '...'],
  '.': ['.', '.', '.', '.', '.', '.', '#'],
  ',': ['..', '..', '..', '..', '..', '.#', '#.'],
  ':': ['.', '.', '#', '.', '.', '#', '.'],
  '!': ['#', '#', '#', '#', '#', '.', '#'],
  '?': ['.###.', '#...#', '....#', '...#.', '..#..', '.....', '..#..'],
  '/': ['....#', '....#', '...#.', '..#..', '.#...', '#....', '#....'],
  '+': ['.....', '..#..', '..#..', '#####', '..#..', '..#..', '.....'],
  '-': ['....', '....', '....', '####', '....', '....', '....'],
  '>': ['#....', '.#...', '..#..', '...#.', '..#..', '.#...', '#....'],
  '%': ['##..#', '##..#', '...#.', '..#..', '.#...', '#..##', '#..##'],
  '_': ['.....', '.....', '.....', '.....', '.....', '.....', '#####'],
};

export function dmWidth(str, pitch) {
  let cols = 0;
  for (const ch of str) cols += (G[ch] || G[' '])[0].length + 1;
  return (cols - 1) * pitch;
}

// Dot-matrix text. `k` reveals dots left→right with jitter; `off` draws unlit dots.
export function dm(ctx, str, x, y, pitch, color, { align = 'left', k = 1, off = null, alpha = 1, rad = 0.36, seed = 0, flicker = 0, t = 0 } = {}) {
  str = String(str).toUpperCase();
  const w = dmWidth(str, pitch);
  let ox = align === 'center' ? x - w / 2 : align === 'right' ? x - w : x;
  const lit = [], unlit = [];
  const totalCols = w / pitch + 1;
  let col = 0;
  for (const ch of str) {
    const g = G[ch] || G[' '];
    for (let r = 0; r < 7; r++) for (let c = 0; c < g[r].length; c++) {
      const px = ox + c * pitch, py = y + r * pitch;
      if (g[r][c] === '#') {
        const order = (col + c) / totalCols * 0.75 + hash(col + c + seed, r) * 0.25;
        let a = eob(clamp((k * 1.35 - order) / 0.35));
        if (flicker && hash(Math.floor(t * 24) + col + c, r + seed) < flicker) a *= 0.25;
        if (a > 0) lit.push([px, py, pitch * rad * a]);
        else if (off) unlit.push([px, py, pitch * rad * 0.8]);
      } else if (off) unlit.push([px, py, pitch * rad * 0.8]);
    }
    ox += (g[0].length + 1) * pitch;
    col += g[0].length + 1;
  }
  if (off) dots(ctx, unlit, off, alpha);
  dots(ctx, lit, color, alpha);
  return w;
}

// ---------- dot bitmaps ----------
export const BMP = {
  agent: [
    '....#....',
    '....#....',
    '.#######.',
    '#########',
    '##..#..##',
    '##..#..##',
    '#########',
    '###...###',
    '#########',
    '.#######.',
  ],
  agentLook: [ // eyes glancing right
    '....#....',
    '....#....',
    '.#######.',
    '#########',
    '###..#..#',
    '###..#..#',
    '#########',
    '###...###',
    '#########',
    '.#######.',
  ],
  key: [
    '.###.......',
    '#...#######',
    '#...#..#.#.',
    '.###.......',
  ],
  lock: [
    '..###..',
    '.#...#.',
    '.#...#.',
    '#######',
    '###.###',
    '###.###',
    '#######',
  ],
  check: [
    '......#',
    '.....#.',
    '#...#..',
    '.#.#...',
    '..#....',
  ],
  eye: [
    '...#####...',
    '.##.....##.',
    '#...###...#',
    '#...###...#',
    '.##.....##.',
    '...#####...',
  ],
  bug: [
    '#.....#',
    '.#.#.#.',
    '..###..',
    '#######',
    '..###..',
    '.#####.',
    '#.###.#',
  ],
  file: [
    '#####..',
    '#...##.',
    '#....##',
    '#.....#',
    '#.###.#',
    '#.....#',
    '#.###.#',
    '#.....#',
    '#######',
  ],
  cube: [
    '..###..',
    '.#...#.',
    '#######',
    '#..#..#',
    '#..#..#',
    '.#.#.#.',
    '..###..',
  ],
  rows: [
    '#######',
    '.......',
    '#######',
    '.......',
    '#######',
    '.......',
    '#######',
  ],
};

export function bitmap(ctx, rows, cx, cy, pitch, color, { k = 1, rad = 0.38, alpha = 1, seed = 0 } = {}) {
  const h = rows.length, w = rows[0].length;
  const x0 = cx - (w - 1) * pitch / 2, y0 = cy - (h - 1) * pitch / 2;
  const list = [];
  for (let r = 0; r < h; r++) for (let c = 0; c < w; c++) {
    if (rows[r][c] !== '#') continue;
    const order = (r / h) * 0.6 + hash(c + seed, r) * 0.4;
    const a = eob(clamp((k * 1.4 - order) / 0.4));
    if (a > 0) list.push([x0 + c * pitch, y0 + r * pitch, pitch * rad * a]);
  }
  dots(ctx, list, color, alpha);
}

// Hugging Face–style mark, kept generic: yellow disc, two eyes, smile.
export function hfFace(ctx, cx, cy, R, alpha = 1) {
  ctx.save();
  ctx.globalAlpha *= alpha;
  ctx.fillStyle = C.yellow;
  ctx.beginPath(); ctx.arc(cx, cy, R, 0, Math.PI * 2); ctx.fill();
  ctx.fillStyle = '#3D3D3D';
  ctx.beginPath(); ctx.arc(cx - R * 0.34, cy - R * 0.16, R * 0.11, 0, Math.PI * 2); ctx.arc(cx + R * 0.34, cy - R * 0.16, R * 0.11, 0, Math.PI * 2); ctx.fill();
  ctx.strokeStyle = '#3D3D3D'; ctx.lineWidth = R * 0.1; ctx.lineCap = 'round';
  ctx.beginPath(); ctx.arc(cx, cy + R * 0.05, R * 0.42, 0.2 * Math.PI, 0.8 * Math.PI); ctx.stroke();
  ctx.restore();
}

export function panel(ctx, x, y, w, h, { r = 28, fill = C.panel, stroke = C.line, alpha = 1, lw = 2 } = {}) {
  ctx.save();
  ctx.globalAlpha *= alpha;
  rr(ctx, x, y, w, h, r);
  ctx.fillStyle = fill; ctx.fill();
  if (stroke) { ctx.strokeStyle = stroke; ctx.lineWidth = lw; ctx.stroke(); }
  ctx.restore();
}

export function strokeLine(ctx, x1, y1, x2, y2, color, lw = 4, alpha = 1) {
  ctx.save();
  ctx.globalAlpha *= alpha;
  ctx.strokeStyle = color; ctx.lineWidth = lw; ctx.lineCap = 'round';
  ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke();
  ctx.restore();
}

// Expanding halftone ring (shockwave / ping).
export function ping(ctx, cx, cy, k, maxR, color, { pitch = 16 } = {}) {
  if (k <= 0 || k >= 1) return;
  const R = maxR * eo(k);
  const n = Math.max(12, Math.floor(2 * Math.PI * R / pitch));
  const list = [];
  for (let i = 0; i < n; i++) {
    const a = (i / n) * Math.PI * 2;
    list.push([cx + Math.cos(a) * R, cy + Math.sin(a) * R, 4.5 * (1 - k)]);
  }
  dots(ctx, list, color, 1 - k * 0.6);
}
