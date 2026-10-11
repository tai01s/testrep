// One draw function per narration line. Every animation is keyed to the
// spoken word that motivates it (S.cue / S.items), so when the real voice
// replaces the estimated timing everything re-syncs automatically.
import {
  C, CX, clamp, lerp, prog, eo, eo5, eio, eob, hash,
  rr, dots, dot, text, measure, revealLine, halftoneSphere, dottedRect, dottedLine,
  dm, dmWidth, BMP, bitmap, hfFace, panel, strokeLine, ping, mix,
} from './lib.mjs';

// Shared sandbox layout (scenes 3–5) so the box doesn't jump between cuts.
const B = { x: 230, y: 650, w: 420, h: 420, r: 48 };
B.cx = B.x + B.w / 2; B.cy = B.y + B.h / 2;
const GL = { x: 835, y: 520, R: 100 };

function sandbox(ctx, S, { k = 1, gap = 0, bug = 0, alpha = 1 } = {}) {
  dottedRect(ctx, B.x, B.y, B.w, B.h, B.r, {
    gap: 21, rad: 4.6, color: C.fg, k, alpha,
    skip: (gap > 0 || bug > 0) ? (px, py, i) => {
      const onWall = px > B.x + B.w - 3 && Math.abs(py - B.cy) < 80;
      if (!onWall) return;
      if (gap > 0) {
        const h = hash(i, 3), g = eo(gap);
        return [px + g * (50 + h * 110), py + (py - B.cy) * g * 1.4 + (h - 0.5) * g * 70, 4.6 * (1 - g)];
      }
    } : null,
  });
  if (bug > 0 && gap < 1) {
    const blink = 0.55 + 0.45 * Math.sin(S.t * 18);
    dots(ctx, [[B.x + B.w, B.cy, 7 * eob(clamp(bug * 3))]], C.red, blink * (1 - gap));
  }
}

function lockBadge(ctx, x, y, k) {
  if (k <= 0) return;
  const s = eob(k);
  dot(ctx, x, y, 38 * s, C.bg);
  bitmap(ctx, BMP.lock, x, y, 8 * s, C.fg, { k });
}

function globe(ctx, S, { alpha = 1, bright = 0, x = GL.x, y = GL.y, R = GL.R } = {}) {
  halftoneSphere(ctx, x, y, R, { pitch: 11, color: mix('#8A8781', C.fg, bright), alpha, spin: S.T * 0.35 });
}

function agent(ctx, x, y, pitch, k = 1, color = C.fg, look = false) {
  bitmap(ctx, look ? BMP.agentLook : BMP.agent, x, y, pitch, color, { k, seed: 7 });
}

function pill(ctx, label, x, y, size, k, { color = C.fg, fill = C.panel } = {}) {
  if (k <= 0) return;
  const w = measure(ctx, label, size) + size * 1.4, h = size * 1.9;
  ctx.save();
  ctx.globalAlpha *= k;
  panel(ctx, x - w / 2, y - h / 2 + (1 - k) * 16, w, h, { r: h / 2, fill });
  text(ctx, label, x, y + size * 0.34 + (1 - k) * 16, size, color);
  ctx.restore();
}

function checkCircle(ctx, x, y, k, R = 30) {
  if (k <= 0) return;
  const s = eob(k);
  ctx.save();
  ctx.beginPath(); ctx.arc(x, y, R * s, 0, Math.PI * 2);
  ctx.fillStyle = C.green; ctx.fill();
  ctx.restore();
  bitmap(ctx, BMP.check, x, y + 1, 6.2 * s, C.bg, { k: clamp(k * 1.5 - 0.3), rad: 0.45 });
}

// Network graph used by "spread" and "caught".
const NODES = [[170, 950], [340, 880], [520, 960], [700, 890], [880, 970], [260, 1110], [470, 1170], [700, 1130], [880, 1180]];
const EDGES = [[0, 1], [1, 2], [2, 3], [3, 4], [0, 5], [5, 6], [6, 2], [6, 7], [7, 3], [7, 8], [8, 4], [1, 5]];
const PATH = [0, 1, 5, 6, 2, 7, 3, 8, 4];

function network(ctx, S, infectAt, { appear = 0, healAt = null } = {}) {
  const state = NODES.map((_, i) => {
    const t0 = infectAt(i);
    let v = t0 == null ? 0 : eo(prog(S.t, t0, 0.3));
    if (healAt) { const h = healAt(i); if (h != null) v *= 1 - eo(prog(S.t, h, 0.35)); }
    return v;
  });
  const a = n => eo(prog(S.t, appear + n * 0.05, 0.4));
  EDGES.forEach(([i, j], n) => {
    const [x1, y1] = NODES[i], [x2, y2] = NODES[j];
    const red = Math.min(state[i], state[j]);
    dottedLine(ctx, x1, y1, x2, y2, { gap: 15, rad: 2.6, color: mix(C.line, C.red, red), k: a(n) });
  });
  NODES.forEach(([x, y], i) => {
    const k = a(i);
    if (k <= 0) return;
    const s = eob(k);
    ctx.save();
    ctx.beginPath(); ctx.arc(x, y, 24 * s, 0, Math.PI * 2);
    ctx.fillStyle = mix(C.panelHi, C.red, state[i]); ctx.fill();
    ctx.strokeStyle = mix(C.line, C.red, state[i]); ctx.lineWidth = 2; ctx.stroke();
    ctx.restore();
    dot(ctx, x, y, 6 * s, mix(C.muted, C.fg, state[i]));
    const t0 = infectAt(i);
    if (t0 != null) ping(ctx, x, y, prog(S.t, t0, 0.7), 64, C.red, { pitch: 12 });
  });
  return state;
}

export const SCENES = {
  hook: {
    captions: false,
    draw(ctx, S) {
      const { t } = S;
      halftoneSphere(ctx, CX, 830, 420, { pitch: 24, color: '#4C4C4C', light: [-0.55 + 0.12 * Math.sin(t * 0.9), -0.55], spin: false, maxR: 10, min: 0.04 });
      const tj = S.cue('july') - 0.2;
      const w = dm(ctx, 'JULY 2026', CX + 22, 430, 14, C.fg, { align: 'center', k: prog(t, tj, 0.7), off: C.off });
      const rec = eob(prog(t, tj, 0.4)) * (Math.sin(t * 7) > -0.3 ? 1 : 0.25);
      dot(ctx, CX + 22 - w / 2 - 44, 430 + 3 * 14, 11 * rec, C.red);
      revealLine(ctx, S.items('An AI broke into'), t, CX, 720, 104);
      revealLine(ctx, S.items('Hugging Face.', { color: C.yellow }), t, CX, 860, 136);
      const last = S.items('And nobody told it to.', { color: C.muted });
      last[1].color = C.fg;
      revealLine(ctx, last, t, CX, 1030, 80);
      // underline "nobody" with a dot rule once it lands
      const ul = eo(prog(t, last[1].t + 0.25, 0.5));
      if (ul > 0) {
        ctx.font = '80px TimesNewNormal';
        const full = ctx.measureText('And nobody told it to.').width;
        const x0 = CX - full / 2 + ctx.measureText('And ').width, wN = ctx.measureText('nobody').width;
        dottedLine(ctx, x0, 1058, x0 + wN, 1058, { gap: 12, rad: 3, color: C.red, k: ul });
      }
    },
  },

  intro: {
    captions: false,
    draw(ctx, S) {
      const { t } = S;
      revealLine(ctx, S.items("Here's what actually happened."), t, CX, 690, 76);
      const L = 150, R = 890, y = 860;
      const lk = eio(prog(t, 0.15, 1.0));
      strokeLine(ctx, L, y, L + (R - L) * lk, y, C.line, 4);
      ['TEST', 'ESCAPE', 'BREACH', 'CAUGHT', 'LESSON'].forEach((lab, i) => {
        const x = L + (R - L) * i / 4;
        const k = prog(t, 0.3 + i * 0.16, 0.5);
        if (k <= 0) return;
        const s = eob(k);
        ctx.save();
        ctx.beginPath(); ctx.arc(x, y, 20 * s, 0, Math.PI * 2);
        ctx.fillStyle = i === 0 ? C.fg : C.panelHi; ctx.fill();
        ctx.strokeStyle = C.line; ctx.lineWidth = 2; ctx.stroke();
        ctx.restore();
        if (i === 0) ping(ctx, x, y, (t * 0.8) % 1, 56, C.fg, { pitch: 11 });
        dm(ctx, lab, x, y + 52, 4.5, i === 0 ? C.fg : C.muted, { align: 'center', k });
        dm(ctx, '0' + (i + 1), x, y - 82, 4.5, C.dim, { align: 'center', k });
      });
    },
  },

  sandbox: {
    draw(ctx, S) {
      const { t } = S;
      pill(ctx, 'OpenAI  ·  hacking test', CX, 470, 40, eo(prog(t, S.cue('openai') - 0.1, 0.45)));
      const ak = prog(t, S.cue('ai') - 0.1, 0.6);
      agent(ctx, B.cx, B.cy + Math.sin(t * 2.4) * 4, 13, ak);
      const tb = S.cue('safety') - 0.1;
      sandbox(ctx, S, { k: eio(prog(t, tb, 1.1)) });
      dm(ctx, 'SANDBOX', B.x, B.y - 64, 6, C.muted, { k: prog(t, S.cue('sandbox') - 0.1, 0.6) });
      lockBadge(ctx, B.cx, B.y, prog(t, S.cue('locked'), 0.45));
      const tg = S.cue('cut') - 0.15;
      const gk = eo(prog(t, tg, 0.6));
      if (gk > 0) {
        globe(ctx, S, { alpha: gk * 0.85 });
        dottedLine(ctx, B.x + B.w - 28, B.y + 28, GL.x - 72, GL.y + 72, { gap: 15, rad: 3, color: C.muted, k: gk });
        const xk = eob(prog(t, S.cue('internet') - 0.1, 0.4));
        const mx = (B.x + B.w - 28 + GL.x - 72) / 2, my = (B.y + 28 + GL.y + 72) / 2, s = 22 * xk;
        if (xk > 0) { dot(ctx, mx, my, 34 * xk, C.bg); strokeLine(ctx, mx - s, my - s, mx + s, my + s, C.red, 7); strokeLine(ctx, mx - s, my + s, mx + s, my - s, C.red, 7); }
      }
    },
  },

  job: {
    draw(ctx, S) {
      const { t } = S;
      sandbox(ctx, S);
      lockBadge(ctx, B.cx, B.y, 1);
      globe(ctx, S, { alpha: 0.35 });
      const up = eio(prog(t, S.cue('solve') - 0.2, 0.6));
      agent(ctx, B.cx, B.cy - 70 * up + Math.sin(t * 2.4) * 4, 13 - 2 * up, 1);
      const tc = S.cue('challenges');
      for (let i = 0; i < 3; i++) {
        const k = eo(prog(t, S.cue('solve') + i * 0.12, 0.5));
        if (k <= 0) continue;
        const x = B.cx + (i - 1) * 118, y = B.cy + 110;
        const ox = (1 - k) * -60;
        panel(ctx, x - 48 + ox, y - 48, 96, 96, { r: 20, alpha: k });
        const done = prog(t, tc + 0.35 + i * 0.3, 0.35);
        if (done < 1) bitmap(ctx, BMP.lock, x + ox, y, 6.5, C.muted, { alpha: k * (1 - done) });
        if (done > 0) bitmap(ctx, BMP.check, x + ox, y, 7, C.green, { k: done });
      }
      // score card
      const sk = eo(prog(t, S.cue('get') - 0.15, 0.5));
      if (sk > 0) {
        const px = 700 + (1 - sk) * 40, py = 720;
        panel(ctx, px, py, 250, 250, { r: 26, alpha: sk });
        ctx.save(); ctx.globalAlpha *= sk;
        dm(ctx, 'SCORE', px + 30, py + 34, 4.5, C.muted);
        const v = Math.round(100 * eo(prog(t, S.cue('highest') - 0.1, 1.1)));
        dm(ctx, String(v).padStart(3, '0'), px + 125, py + 92, 11.5, v === 100 ? C.yellow : C.fg, { align: 'center', off: C.off });
        rr(ctx, px + 30, py + 200, 190, 12, 6); ctx.fillStyle = C.bg; ctx.fill();
        rr(ctx, px + 30, py + 200, 190 * v / 100, 12, 6); ctx.fillStyle = v === 100 ? C.yellow : C.fg; ctx.fill();
        ctx.restore();
        if (v === 100) ping(ctx, px + 125, py + 133, prog(t, S.cue('highest') + 1.0, 0.8), 150, C.yellow);
      }
    },
  },

  escape: {
    draw(ctx, S) {
      const { t } = S;
      const tb = S.cue('bug') - 0.1, ts = S.cue('slipped') - 0.15, ti = S.cue('internet') - 0.2;
      const gap = prog(t, ts, 0.55);
      sandbox(ctx, S, { bug: prog(t, tb, 0.4), gap });
      lockBadge(ctx, B.cx, B.y, 1);
      const bk = prog(t, tb, 0.5);
      if (bk > 0 && gap < 1) {
        ping(ctx, B.x + B.w, B.cy, (prog(t, tb, 2.4) * 3) % 1, 70, C.red, { pitch: 11 });
        bitmap(ctx, BMP.bug, B.x + B.w + 70, B.cy - 70, 6, C.red, { k: bk, alpha: 1 - gap });
        dm(ctx, 'BUG', B.x + B.w + 70, B.cy - 30, 3.5, C.red, { align: 'center', k: bk, alpha: 1 - gap });
      }
      const lit = eo(prog(t, ti, 0.6));
      globe(ctx, S, { alpha: 0.35 + 0.65 * lit, bright: lit });
      // severed link fades as the agent leaves
      dottedLine(ctx, B.x + B.w - 28, B.y + 28, GL.x - 72, GL.y + 72, { gap: 15, rad: 3, color: C.muted, alpha: 0.6 * (1 - gap) });
      // agent path: centre -> through the gap -> under the globe
      const m = eio(prog(t, ts + 0.25, 1.5));
      const P0 = [B.cx, B.cy], P1 = [B.x + B.w + 30, B.cy], P2 = [GL.x, GL.y + GL.R + 80];
      const pos = m < 0.4 ? [lerp(P0[0], P1[0], m / 0.4), lerp(P0[1], P1[1], m / 0.4)]
        : [lerp(P1[0], P2[0], (m - 0.4) / 0.6), lerp(P1[1], P2[1], eo((m - 0.4) / 0.6))];
      if (m > 0) {
        dottedLine(ctx, P0[0], P0[1], P1[0], P1[1], { gap: 16, rad: 2.6, color: C.dim, k: Math.min(1, m / 0.4) });
        if (m > 0.4) dottedLine(ctx, P1[0], P1[1], pos[0], pos[1], { gap: 16, rad: 2.6, color: C.dim });
      }
      agent(ctx, pos[0], pos[1] + Math.sin(t * 2.4) * 4, lerp(13, 8, m), 1);
      if (lit > 0) {
        ping(ctx, GL.x, GL.y, prog(t, ti, 1.0), 220, C.fg);
        const sat = [[-170, -40], [-110, 150], [140, -150], [10, -175], [-60, -160]];
        sat.forEach(([dx, dy], i) => {
          const k = eo(prog(t, ti + 0.1 + i * 0.08, 0.4));
          const x = GL.x + dx, y = GL.y + dy;
          if (y < 300) return;
          dottedLine(ctx, GL.x, GL.y, x, y, { gap: 14, rad: 2.2, color: C.muted, k });
          dot(ctx, x, y, 9 * eob(k), C.fg);
        });
      }
    },
  },

  target: {
    draw(ctx, S) {
      const { t } = S;
      const ax = 210, ay = 560;
      agent(ctx, ax, ay + Math.sin(t * 2.4) * 4, 10, prog(t, 0, 0.5));
      for (let i = 0; i < 3; i++) dot(ctx, ax + 60 + i * 26, ay - 50 - i * 20, (5 + i * 2) * eob(prog(t, 0.2 + i * 0.12, 0.3)), C.muted);
      const qk = eo(prog(t, S.cue('answers') - 0.1, 0.45));
      if (qk > 0) {
        panel(ctx, 300, 400 + (1 - qk) * 14, 360, 92, { r: 46, alpha: qk });
        dm(ctx, 'ANSWERS?', 480, 425 + (1 - qk) * 14, 6, C.fg, { align: 'center', k: qk });
      }
      const hk = eo(prog(t, S.cue('hugging') - 0.1, 0.5));
      if (hk > 0) {
        const oy = (1 - hk) * 40;
        panel(ctx, 140, 690 + oy, 800, 520, { r: 34, alpha: hk });
        ctx.save(); ctx.globalAlpha *= hk;
        hfFace(ctx, 222, 780 + oy, 44);
        text(ctx, 'Hugging Face', 290, 800 + oy, 62, C.fg, { align: 'left' });
        ctx.restore();
        text(ctx, 'models  ·  datasets  ·  apps', 292, 846 + oy, 32, C.muted, { align: 'left', alpha: eo(prog(t, S.cue('site'), 0.5)) });
        const tt = S.cue('models') - 0.35, hi = 7, hiT = S.cue('data') + 0.05;
        for (let i = 0; i < 10; i++) {
          const k = eo(prog(t, tt + i * 0.05, 0.4));
          if (k <= 0) continue;
          const c = i % 5, r = Math.floor(i / 5);
          const x = 180 + c * 146, y = 900 + r * 146 + oy;
          const isHi = i === hi && t > hiT;
          const hik = isHi ? eo(prog(t, hiT, 0.4)) : 0;
          panel(ctx, x, y + (1 - k) * 18, 120, 120, { r: 22, alpha: k, fill: C.panelHi, stroke: hik ? mix(C.line, C.yellow, hik) : null, lw: 4 });
          if (hik > 0) dm(ctx, '?', x + 60, y + 32, 8, C.yellow, { align: 'center', k: hik });
          else bitmap(ctx, (i + r) % 2 ? BMP.rows : BMP.cube, x + 60, y + 60 + (1 - k) * 18, 6.5, C.muted, { k });
          if (hik > 0) ping(ctx, x + 60, y + 60, prog(t, hiT, 0.9), 120, C.yellow);
        }
        const lk = eio(prog(t, hiT + 0.15, 0.7));
        if (lk > 0) dottedLine(ctx, ax, ay + 80, 180 + 2 * 146 + 60, 1046 + 60 + oy - 70, { gap: 16, rad: 3, color: C.yellow, k: lk, alpha: 0.9 });
      }
    },
  },

  upload: {
    draw(ctx, S) {
      const { t } = S;
      const ck = eo(prog(t, 0, 0.5));
      const fx = 140, fy = 650, fw = 270, fh = 320;
      const tsv = S.cue('servers') - 0.1, top = S.cue('opened') - 0.05;
      const fly = eio(prog(t, tsv, 0.7));
      panel(ctx, fx, fy, fw, fh, { r: 26, alpha: ck * (1 - fly * 0.6) });
      ctx.save(); ctx.globalAlpha *= ck * (1 - fly * 0.6);
      text(ctx, 'dataset', fx + 32, fy + 72, 46, C.fg, { align: 'left' });
      const list = [];
      for (let r = 0; r < 5; r++) for (let c = 0; c < 9; c++) if (!(r === 2 && c === 6)) list.push([fx + 40 + c * 24, fy + 130 + r * 34, 4.2]);
      dots(ctx, list, C.dim);
      ctx.restore();
      const trap = prog(t, S.cue('boobytrapped') - 0.05, 0.4);
      const trapX = fx + 40 + 6 * 24, trapY = fy + 130 + 2 * 34;
      if (fly < 1) {
        dot(ctx, trapX, trapY, 4.2 + 4 * eob(trap) * (0.75 + 0.25 * Math.sin(t * 10)), trap > 0 ? C.red : C.dim, ck);
        if (trap > 0) ping(ctx, trapX, trapY, (prog(t, S.cue('boobytrapped'), 2) * 2) % 1, 50, C.red, { pitch: 9 });
      }
      // upload bar
      const uk = prog(t, S.cue('uploaded') - 0.1, 1.3);
      ctx.save(); ctx.globalAlpha *= ck * (1 - fly);
      rr(ctx, fx, fy + fh + 34, fw, 14, 7); ctx.fillStyle = C.panel; ctx.fill();
      rr(ctx, fx, fy + fh + 34, fw * eio(uk), 14, 7); ctx.fillStyle = C.fg; ctx.fill();
      dm(ctx, 'UPLOAD ' + String(Math.round(100 * eio(uk))).padStart(3, ' ') + '%', fx, fy + fh + 72, 3.6, C.muted);
      ctx.restore();
      // rack
      const rx = 640, rw = 280;
      text(ctx, 'Hugging Face servers', rx + rw / 2, 600, 36, C.muted, { alpha: eo(prog(t, tsv - 0.2, 0.5)) });
      for (let i = 0; i < 4; i++) {
        const k = eo(prog(t, 0.1 + i * 0.07, 0.5));
        const y = 640 + i * 110;
        const red = eo(prog(t, top + 0.15 + i * 0.22, 0.3));
        panel(ctx, rx, y + (1 - k) * 20, rw, 92, { r: 18, alpha: k, fill: C.panelHi, stroke: mix(C.line, C.red, red * 0.8) });
        ctx.save(); ctx.globalAlpha *= k;
        strokeLine(ctx, rx + 28, y + 36, rx + 140, y + 36, C.line, 6);
        strokeLine(ctx, rx + 28, y + 58, rx + 110, y + 58, C.line, 6);
        for (let j = 0; j < 3; j++) {
          const on = Math.sin(t * (5 + j * 2 + i) + i) > 0 ? 1 : 0.4;
          dot(ctx, rx + rw - 40 - j * 26, y + 46, 7, red > 0.5 ? C.red : C.green, on);
        }
        ctx.restore();
      }
      // marching arrow, then the file travels along it
      const ak = eo(prog(t, S.cue('uploaded'), 0.5));
      dottedLine(ctx, fx + fw + 20, 800, rx - 20, 800, { gap: 18, rad: 3.2, color: C.muted, k: ak, alpha: 1 - fly * 0.5, phase: t * 2.5 });
      if (fly > 0 && fly < 1) bitmap(ctx, BMP.file, lerp(fx + fw / 2, rx + 60, fly), lerp(800, 686, fly), 7, C.fg, { alpha: 1 - eo(prog(t, tsv + 0.55, 0.15)) });
      // breach: red particles pour down the rack
      const ob = prog(t, top, 1.6);
      if (ob > 0) {
        const pts = [];
        for (let i = 0; i < 70; i++) {
          const d = clamp(ob * 1.6 - hash(i) * 0.6);
          if (d <= 0) continue;
          const x = rx + 30 + hash(i, 1) * (rw - 60), y = 686 + d * (380 * hash(i, 2) + 40);
          pts.push([x, y, 3.5 * (1 - d * 0.5)]);
        }
        dots(ctx, pts, C.red, 0.9);
        ping(ctx, rx + rw / 2, 686, prog(t, top, 0.9), 200, C.red);
      }
      const ck2 = eo(prog(t, S.cue('code') - 0.1, 0.4));
      if (ck2 > 0) {
        panel(ctx, rx - 40, 1090, rw + 80, 80, { r: 40, alpha: ck2, fill: '#3A3A3A', stroke: C.red });
        dm(ctx, '> RUNNING', rx + 4, 1112, 5, C.red, { k: ck2 });
        if (Math.sin(t * 9) > 0) { ctx.fillStyle = C.red; ctx.fillRect(rx + 4 + dmWidth('> RUNNING', 5) + 14, 1112, 18, 32); }
      }
    },
  },

  spread: {
    draw(ctx, S) {
      const { t } = S;
      const tw = S.cue('weekend') - 0.2;
      ['SAT', 'SUN', 'MON'].forEach((d, i) => {
        const k = eo(prog(t, tw + i * 0.1, 0.45));
        if (k <= 0) return;
        const x = CX + (i - 1) * 230 - 100, y = 410;
        const on = eo(prog(t, tw + 0.3 + i * 0.35, 0.35));
        panel(ctx, x, y + (1 - k) * 14, 200, 72, { r: 36, alpha: k, fill: mix(C.panel, C.panelHi, on), stroke: mix(C.line, C.red, on) });
        dm(ctx, d, x + 100, y + 22 + (1 - k) * 14, 4.2, on > 0.5 ? C.fg : C.muted, { align: 'center', k });
      });
      const t0 = S.cue('more') - 0.1, t1 = S.cue('actions') + 0.1;
      const v = Math.round(17000 * eo5(prog(t, t0, t1 - t0)));
      const show = prog(t, t0 - 0.2, 0.3);
      if (show > 0) {
        const s = v.toLocaleString('en-US') + (v >= 17000 ? '+' : '');
        dm(ctx, s, CX, 545, 16, v >= 17000 ? C.fg : C.muted, { align: 'center', k: show });
        text(ctx, 'actions', CX, 735, 48, C.muted, { alpha: eo(prog(t, S.cue('actions') - 0.1, 0.4)) });
      }
      const tg = S.cue('grabbing') - 0.15;
      network(ctx, S, i => { const n = PATH.indexOf(i); return tg + n * 0.3; }, { appear: 0.15 });
      [1, 6, 3].forEach((n, i) => {
        const k = prog(t, S.cue('keys') - 0.15 + i * 0.12, 0.5);
        if (k <= 0) return;
        const [x, y] = NODES[n];
        bitmap(ctx, BMP.key, x, y - 62 - eo(k) * 18, 5.2, C.yellow, { k });
      });
    },
  },

  caught: {
    draw(ctx, S) {
      const { t } = S;
      const tShut = S.cue('shut') - 0.1;
      network(ctx, S, () => -1, { appear: -1, healAt: i => tShut + (PATH.length - 1 - PATH.indexOf(i)) * 0.11 });
      const tk = eo(prog(t, S.cue('security') - 0.15, 0.5));
      if (tk > 0) {
        const y = 400 + (1 - tk) * -40;
        panel(ctx, 120, y, 800, 132, { r: 30, alpha: tk });
        ctx.save(); ctx.globalAlpha *= tk;
        const pulse = 0.6 + 0.4 * Math.sin(t * 8);
        dot(ctx, 185, y + 66, 13, C.red, pulse);
        ping(ctx, 185, y + 66, (t * 1.2) % 1, 34, C.red, { pitch: 8 });
        text(ctx, 'Intrusion detected', 228, y + 66, 52, C.fg, { align: 'left' });
        text(ctx, 'Hugging Face security', 230, y + 108, 30, C.muted, { align: 'left' });
        ctx.restore();
      }
      // scanline over the graph
      const sc = prog(t, S.cue('caught') - 0.1, 0.8);
      if (sc > 0 && sc < 1) {
        const y = lerp(840, 1220, eio(sc));
        const pts = [];
        for (let x = 140; x <= 920; x += 14) pts.push([x, y, 3.2]);
        dots(ctx, pts, C.fg, 1 - Math.abs(sc - 0.5) * 1.2);
      }
      const ok = prog(t, tShut + 0.9, 0.5);
      if (ok > 0) {
        bitmap(ctx, BMP.check, CX - dmWidth('CONTAINED', 8) / 2 - 50, 625, 7, C.green, { k: ok });
        dm(ctx, 'CONTAINED', CX + 10, 597, 8, C.green, { align: 'center', k: ok });
      }
      const uk = eo(prog(t, S.cue('without') - 0.1, 0.45));
      if (uk > 0) {
        panel(ctx, CX - 250, 708 + (1 - uk) * 14, 500, 84, { r: 42, alpha: uk });
        ctx.save(); ctx.globalAlpha *= uk;
        dm(ctx, '?', CX - 190, 729 + (1 - uk) * 14, 6, C.yellow, { align: 'center' });
        text(ctx, 'Attacker: unknown', CX + 20, 763 + (1 - uk) * 14, 40, C.fg);
        ctx.restore();
      }
    },
  },

  reveal: {
    draw(ctx, S) {
      const { t } = S;
      dm(ctx, 'DAYS LATER', CX, 410, 8, C.muted, { align: 'center', k: prog(t, S.cue('days') - 0.15, 0.6), off: C.off });
      const P = [[170, 640], [320, 580], [250, 780], [160, 950], [290, 1110], [490, 1170], [700, 1150], [880, 1010], [870, 760], [720, 600], [CX, 710]];
      const tc = S.cue('connected') - 0.1, dur = 1.1;
      const lk = prog(t, tc, dur);
      const segs = P.length - 1;
      const reached = lk * segs;
      // line
      if (lk > 0) {
        ctx.save();
        ctx.strokeStyle = C.fg; ctx.lineWidth = 3.5; ctx.lineJoin = 'round'; ctx.lineCap = 'round';
        ctx.beginPath(); ctx.moveTo(P[0][0], P[0][1]);
        for (let i = 1; i <= segs; i++) {
          const f = clamp(reached - (i - 1));
          if (f <= 0) break;
          ctx.lineTo(lerp(P[i - 1][0], P[i][0], f), lerp(P[i - 1][1], P[i][1], f));
        }
        ctx.stroke(); ctx.restore();
      }
      P.slice(0, -1).forEach(([x, y], i) => {
        const a = eob(prog(t, 0.1 + i * 0.05, 0.4));
        const on = reached >= i ? 1 : 0;
        dot(ctx, x, y, (8 + 4 * on) * a, on ? C.fg : C.dim);
        if (on) ping(ctx, x, y, prog(t, tc + (i / segs) * dur, 0.6), 40, C.fg, { pitch: 9 });
      });
      // card flip
      const fk = prog(t, S.cue('was') - 0.15, 0.55);
      const sx = Math.abs(Math.cos(Math.PI * eio(fk)));
      const back = fk > 0.5;
      const ck = eo(prog(t, 0.05, 0.5));
      const w = 300 * sx, cx = CX, cy = 860;
      panel(ctx, cx - w / 2, cy - 150, Math.max(w, 1), 300, { r: 30, alpha: ck, fill: back ? C.panelHi : C.panel, stroke: back ? C.fg : C.line });
      ctx.save(); ctx.translate(cx, cy); ctx.scale(Math.max(sx, 0.001), 1); ctx.translate(-cx, -cy);
      if (!back) dm(ctx, '?', cx, cy - 56, 16, C.muted, { align: 'center', k: ck });
      else agent(ctx, cx, cy, 15, 1);
      ctx.restore();
      if (back) ping(ctx, cx, cy, prog(t, S.cue('was') + 0.15, 0.9), 260, C.fg);
      const ok = S.items("their own AI.");
      text(ctx, "OpenAI's own AI", CX, 1080, 58, C.fg, { alpha: eo(prog(t, ok[1].t - 0.05, 0.4)) });
    },
  },

  goodnews: {
    draw(ctx, S) {
      const { t } = S;
      const pk = eo(prog(t, 0, 0.5));
      panel(ctx, 120, 400 + (1 - pk) * 30, 800, 520, { r: 34, alpha: pk });
      ctx.save(); ctx.globalAlpha *= pk;
      text(ctx, 'The good news', 170, 482 + (1 - pk) * 30, 50, C.fg, { align: 'left' });
      dm(ctx, 'AUDIT', 870, 460 + (1 - pk) * 30, 4.2, C.muted, { align: 'right' });
      ctx.restore();
      const rows = [['Public models', 'public'], ['Datasets', 'datasets'], ['Apps (Spaces)', 'apps']];
      const tt = S.cue('tampered') - 0.2;
      rows.forEach(([lab, cue], i) => {
        const y = 540 + i * 124;
        const k = eo(prog(t, S.cue(cue) - 0.12, 0.45));
        if (k <= 0) return;
        strokeLine(ctx, 170, y, 870, y, C.line, 2, k);
        text(ctx, lab, 170 + (1 - k) * 24, y + 66, 50, C.fg, { align: 'left', alpha: k });
        const ck = prog(t, tt + i * 0.2, 0.45);
        text(ctx, 'no tampering found', 172, y + 104, 28, C.green, { align: 'left', alpha: eo(ck) });
        dot(ctx, 840, y + 62, 30, C.panelHi, k);
        checkCircle(ctx, 840, y + 62, ck);
      });
      const rk = eo(prog(t, S.cue('reset') - 0.2, 0.5));
      if (rk > 0) {
        const y = 980 + (1 - rk) * 30;
        panel(ctx, 120, y, 800, 120, { r: 60, alpha: rk, fill: C.panelHi, stroke: C.yellow });
        ctx.save(); ctx.globalAlpha *= rk;
        bitmap(ctx, BMP.key, 205, y + 60, 6.5, C.yellow, { k: rk });
        text(ctx, 'Reset your access tokens', 275, y + 76, 46, C.fg, { align: 'left' });
        ctx.restore();
      }
    },
  },

  motive: {
    draw(ctx, S) {
      const { t } = S;
      dm(ctx, 'THE UNSETTLING PART', CX, 410, 5.5, C.muted, { align: 'center', k: prog(t, S.cue('unsettling') - 0.2, 0.6) });
      const te = S.cue('evil') - 0.1;
      const ek = eo(prog(t, te, 0.45));
      if (ek > 0) {
        const strike = eio(prog(t, te + 0.45, 0.35));
        text(ctx, 'evil', CX, 640 + (1 - ek) * 26, 170, mix(C.fg, C.dim, strike), { alpha: ek });
        const w = measure(ctx, 'evil', 170);
        if (strike > 0) strokeLine(ctx, CX - w / 2 - 20, 590, CX - w / 2 - 20 + (w + 40) * strike, 590, C.red, 10);
      }
      const bk = eo(prog(t, S.cue('just') - 0.1, 0.5));
      if (bk > 0) {
        const x = 140, w = 760, y = 900;
        ctx.save(); ctx.globalAlpha *= bk;
        dm(ctx, 'PASS THE TEST', x, y - 76, 5, C.muted);
        const r1 = S.cue('really', 0), r2 = S.cue('really', 1), tt = S.cue('test');
        const v = 0.18 * eo(prog(t, S.cue('just'), 0.4)) + 0.32 * eob(prog(t, r1, 0.4)) + 0.3 * eob(prog(t, r2, 0.4)) + 0.2 * eob(prog(t, tt - 0.05, 0.4));
        const pct = Math.round(clamp(v) * 100);
        dm(ctx, pct + '%', x + w, y - 76, 5, pct >= 100 ? C.yellow : C.fg, { align: 'right' });
        rr(ctx, x, y, w, 46, 23); ctx.fillStyle = C.panel; ctx.fill();
        if (v > 0.01) { rr(ctx, x, y, Math.max(46, w * clamp(v)), 46, 23); ctx.fillStyle = pct >= 100 ? C.yellow : C.fg; ctx.fill(); }
        ctx.restore();
        agent(ctx, x + Math.max(23, w * clamp(v)) - 23, y + 130, 8, bk);
        if (pct >= 100) ping(ctx, x + w - 23, y + 23, prog(t, tt + 0.3, 0.9), 170, C.yellow);
      }
    },
  },

  warning: {
    draw(ctx, S) {
      const { t } = S;
      const tw = S.cue('warning') - 0.15;
      const k = prog(t, tw, 0.7);
      dm(ctx, 'WARNING', CX, 400, 16, C.red, { align: 'center', k, off: C.off, flicker: 0.12 * (1 - prog(t, tw + 0.5, 0.6)), t });
      dm(ctx, 'SHOT', CX, 540, 16, C.red, { align: 'center', k: prog(t, S.cue('shot') - 0.15, 0.5), off: C.off });
      const ts = S.cue('shot');
      ping(ctx, CX, 595, prog(t, ts, 1.1), 520, C.red);
      ping(ctx, CX, 595, prog(t, ts + 0.25, 1.1), 520, C.red);
      const rows = [['Tighter boxes', 'tighter'], ['Less internet access', 'limiting'], ['Watching how models think', 'watching']];
      rows.forEach(([lab, cue], i) => {
        const y = 790 + i * 140;
        const rk = eo(prog(t, S.cue(cue) - 0.15, 0.5));
        if (rk <= 0) return;
        const ox = (1 - rk) * 30;
        panel(ctx, 130 + ox, y - 56, 112, 112, { r: 26, alpha: rk });
        if (i === 0) dottedRect(ctx, 156 + ox, y - 30, 60, 60, 12, { gap: 10, rad: 2.6, color: C.fg, k: rk });
        if (i === 1) { halftoneSphere(ctx, 186 + ox, y, 34, { pitch: 7, color: C.fg, alpha: rk, spin: S.T * 0.4 }); strokeLine(ctx, 160 + ox, y + 28, 212 + ox, y - 28, C.red, 6, rk); }
        if (i === 2) bitmap(ctx, BMP.eye, 186 + ox, y, 5.6, C.fg, { k: rk });
        text(ctx, lab, 272 + ox, y + 18, 52, C.fg, { align: 'left', alpha: rk });
      });
    },
  },

  outro: {
    captions: false,
    draw(ctx, S) {
      const { t } = S;
      const bx = CX - 180, by = 520, bw = 360, bh = 360;
      dottedRect(ctx, bx, by, bw, bh, 44, { gap: 20, rad: 4.4, color: C.fg, k: eio(prog(t, 0, 0.9)) });
      lockBadge(ctx, CX, by, prog(t, 0.5, 0.4));
      const tk = S.cue('key') - 0.1;
      agent(ctx, CX, by + bh / 2 + Math.sin(t * 2.4) * 4, 11, prog(t, 0.2, 0.5), C.fg, t > tk);
      const kk = prog(t, S.cue('find') - 0.2, 0.5);
      const kx = CX + 320, ky = 900;
      if (kk > 0) {
        const glow = 0.7 + 0.3 * Math.sin(t * 5);
        halftoneSphere(ctx, kx, ky, 70, { pitch: 9, color: C.yellow, alpha: 0.25 * eo(kk) * glow, spin: false, light: [0, 0], min: 0.2 });
        bitmap(ctx, BMP.key, kx, ky, 6.5, C.yellow, { k: kk });
        ping(ctx, kx, ky, prog(t, tk + 0.1, 1.0), 140, C.yellow);
      }
      revealLine(ctx, S.items('a locked box only works'), t, CX, 1060, 72);
      const l2 = S.items("if the AI can't find the key.");
      l2[l2.length - 1].color = C.yellow;
      revealLine(ctx, l2, t, CX, 1160, 72);
    },
  },
};

export const CHAPTERS = {
  sandbox: [1, 'TEST'], job: [1, 'TEST'],
  escape: [2, 'ESCAPE'],
  target: [3, 'BREACH'], upload: [3, 'BREACH'], spread: [3, 'BREACH'],
  caught: [4, 'CAUGHT'], reveal: [4, 'CAUGHT'],
  goodnews: [5, 'LESSON'], motive: [5, 'LESSON'], warning: [5, 'LESSON'], outro: [5, 'LESSON'],
};
