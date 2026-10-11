// Renders the video: Canvas frames -> ffmpeg (H.264, 1080x1920, 30fps) with
// the ElevenLabs voice track laid in at each scene's cue.
//
//   node render.mjs                     # full render -> out/hf-incident.mp4
//   node render.mjs --preview           # half-res quick check
//   node render.mjs --stills 3,12.5,40  # PNGs of given seconds -> out/still-*.png
//   node render.mjs --contact           # contact sheet of every scene -> out/contact.png
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import { spawn, execFileSync } from 'node:child_process';
import { Worker, isMainThread, workerData, parentPort } from 'node:worker_threads';
import { fileURLToPath } from 'node:url';
import { createCanvas, GlobalFonts } from '@napi-rs/canvas';
import { W, H, C, CX, SERIF, clamp, prog, eo, eob, text, dm, dots, measure, halftoneBackground } from './lib.mjs';
import { SCENES, CHAPTERS } from './scenes.mjs';
import { buildTimeline, norm } from './timeline.mjs';

const HERE = path.dirname(fileURLToPath(import.meta.url));
if (isMainThread) process.chdir(HERE);
const FPS = 30;

function loadFont() {
  const dir = path.join(HERE, 'fonts');
  const f = fs.existsSync(dir) && fs.readdirSync(dir).find(n => /\.(ttf|otf)$/i.test(n));
  if (!f) throw new Error('Put the serif font (Times New Normal) in fonts/');
  GlobalFonts.registerFromPath(path.join(dir, f), SERIF);
}

// ---------- per-scene helpers ----------
function makeS(scene, t, T) {
  const words = scene.words;
  const find = (n, nth = 0) => {
    let c = 0;
    for (const w of words) if (w.n === n && c++ === nth) return w;
    throw new Error(`[${scene.id}] cue "${n}"#${nth} not in narration`);
  };
  return {
    t, T, dur: scene.dur, words,
    cue: (w, nth = 0) => find(norm(w), nth).s,
    // contiguous phrase -> [{w, t}] for revealLine
    items(phrase, extra = {}) {
      const ps = phrase.split(/\s+/);
      const pn = ps.map(norm);
      for (let i = 0; i + pn.length <= words.length; i++) {
        if (pn.every((n, j) => words[i + j].n === n)) return ps.map((w, j) => ({ w, t: words[i + j].s - 0.06, ...extra }));
      }
      throw new Error(`[${scene.id}] phrase "${phrase}" not in narration`);
    },
  };
}

// Captions: 1–4 word chunks, current word lit, matrix-dot underline.
const chunkCache = new Map();
function chunks(scene) {
  if (chunkCache.has(scene.id)) return chunkCache.get(scene.id);
  const out = [];
  let cur = [];
  const flush = () => { if (cur.length) out.push(cur); cur = []; };
  scene.words.forEach(w => {
    cur.push(w);
    const chars = cur.map(x => x.w).join(' ').length;
    if (/[.?!,:]$/.test(w.w) || cur.length >= 4 || chars >= 17) flush();
  });
  flush();
  chunkCache.set(scene.id, out);
  return out;
}

function captions(ctx, scene, t) {
  const cs = chunks(scene);
  let idx = -1;
  for (let i = 0; i < cs.length; i++) if (t >= cs[i][0].s - 0.08) idx = i;
  if (idx < 0) return;
  const ch = cs[idx];
  const end = idx + 1 < cs.length ? cs[idx + 1][0].s - 0.08 : ch[ch.length - 1].e + 0.35;
  if (t > end + 0.15) return;
  const a = clamp((t - (ch[0].s - 0.08)) / 0.1) * (1 - clamp((t - end) / 0.15));
  const size = 66, y = 1400;
  ctx.font = `${size}px ${SERIF}`;
  const space = ctx.measureText(' ').width;
  const ws = ch.map(w => ctx.measureText(w.w).width);
  const total = ws.reduce((p, c) => p + c, 0) + space * (ch.length - 1);
  let x = CX - total / 2;
  const pop = 1 + 0.04 * (1 - eo(clamp((t - ch[0].s + 0.08) / 0.18)));
  ctx.save();
  ctx.translate(CX, y); ctx.scale(pop, pop); ctx.translate(-CX, -y);
  // exactly one lit word: the latest one that has started and isn't long over
  let cur = -1;
  ch.forEach((w, i) => { if (t >= w.s - 0.04) cur = i; });
  if (cur >= 0 && t > ch[cur].e + 0.25) cur = -1;
  ch.forEach((w, i) => {
    const active = i === cur;
    const said = t >= w.s - 0.04;
    text(ctx, w.w, x, y, size, C.fg, { align: 'left', alpha: a * (said ? 1 : 0.32) });
    if (active) {
      const list = [];
      for (let d = 6; d < ws[i] - 4; d += 12) list.push([x + d, y + 26, 2.6]);
      dots(ctx, list, C.yellow, a);
    }
    x += ws[i] + space;
  });
  ctx.restore();
}

function chapterTag(ctx, scene, t, prevScene) {
  const ch = CHAPTERS[scene.id];
  if (!ch) return;
  const [n, label] = ch;
  const isNew = !prevScene || !CHAPTERS[prevScene.id] || CHAPTERS[prevScene.id][0] !== n;
  const k = isNew ? prog(t, 0.05, 0.6) : 1;
  const x = 84, y = 250, p = 5;
  dm(ctx, '0' + n, x, y, p, C.yellow, { k });
  dm(ctx, label, x + 70, y, p, C.fg, { k });
  for (let i = 0; i < 5; i++) {
    const on = i < n - 1 ? 1 : i === n - 1 ? eo(k) : 0;
    const bx = x + i * 30;
    const list = [[bx, y + 62, 4]];
    dots(ctx, list, on > 0.5 ? C.fg : C.off);
  }
}

// ---------- frame ----------
export function drawFrame(ctx, TL, T) {
  const scenes = TL.scenes;
  let si = scenes.findIndex(s => T < s.start + s.dur);
  if (si < 0) si = scenes.length - 1;
  const scene = scenes[si];
  const t = T - scene.start;
  ctx.fillStyle = C.bg;
  ctx.fillRect(0, 0, W, H);
  const wipe = si > 0 && t < 0.8 ? -0.15 + 1.3 * (t / 0.8) : -1;
  const isLast = si === scenes.length - 1;
  const swell = isLast ? 0.9 * eo(prog(t, scene.dur - 1.0, 1.0)) : 0;
  halftoneBackground(ctx, T, wipe, swell);

  const enter = eo(prog(t, 0, 0.28));
  const exit = isLast ? 1 - prog(t, scene.dur - 0.7, 0.7) : 1 - prog(t, scene.dur - 0.2, 0.2);
  const alpha = Math.min(enter, exit);
  const S = makeS(scene, t, T);
  const def = SCENES[scene.id];
  ctx.save();
  ctx.globalAlpha = alpha;
  const sc = 0.985 + 0.015 * enter;
  ctx.translate(CX, 820); ctx.scale(sc, sc); ctx.translate(-CX, -820);
  def.draw(ctx, S);
  ctx.restore();
  ctx.save();
  ctx.globalAlpha = Math.min(1, exit + 0.0);
  chapterTag(ctx, scene, t, scenes[si - 1]);
  ctx.restore();
  if (def.captions !== false) captions(ctx, scene, t);
}

// ---------- worker: render a frame range to raw RGBA on stdout of ffmpeg ----------
async function renderRange(TL, from, to, file, scale) {
  const w = Math.round(W * scale / 2) * 2, h = Math.round(H * scale / 2) * 2;
  const canvas = createCanvas(w, h);
  const ctx = canvas.getContext('2d');
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', `${w}x${h}`, '-r', String(FPS), '-i', '-',
    '-c:v', 'libx264', '-preset', scale < 1 ? 'veryfast' : 'slow', '-crf', scale < 1 ? '23' : '16', '-pix_fmt', 'yuv420p', '-tune', 'animation', file],
    { stdio: ['pipe', 'inherit', 'inherit'] });
  for (let f = from; f < to; f++) {
    ctx.setTransform(scale, 0, 0, scale, 0, 0);
    drawFrame(ctx, TL, f / FPS);
    const buf = Buffer.from(ctx.getImageData(0, 0, w, h).data.buffer);
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (parentPort && (f - from) % 30 === 0) parentPort.postMessage({ progress: f - from });
  }
  ff.stdin.end();
  await new Promise((res, rej) => ff.on('close', c => (c ? rej(new Error('ffmpeg ' + c)) : res())));
}

if (!isMainThread) {
  loadFont();
  const { from, to, file, scale } = workerData;
  const TL = buildTimeline();
  await renderRange(TL, from, to, file, scale);
  parentPort.postMessage({ done: true });
} else {
  await main();
}

async function main() {
  loadFont();
  const args = process.argv.slice(2);
  const opt = n => { const i = args.indexOf(n); return i >= 0 ? args[i + 1] : null; };
  const TL = buildTimeline();
  fs.mkdirSync('out', { recursive: true });
  fs.mkdirSync('build', { recursive: true });
  console.log(`timeline ${TL.duration.toFixed(2)}s, ${TL.voiced ? 'ElevenLabs voice' : TL.partial ? 'PARTIAL voice' : 'no voice (estimated timing)'}`);

  if (args.includes('--stills') || args.includes('--contact')) {
    const canvas = createCanvas(W, H), ctx = canvas.getContext('2d');
    let times;
    if (args.includes('--contact')) times = TL.scenes.map(s => s.start + Math.min(s.dur - 0.3, s.words[s.words.length - 1].e));
    else times = opt('--stills').split(',').map(Number);
    const files = [];
    for (const T of times) {
      drawFrame(ctx, TL, T);
      const f = `out/still-${T.toFixed(2)}.png`;
      fs.writeFileSync(f, canvas.toBuffer('image/png'));
      files.push(f);
    }
    if (args.includes('--contact')) {
      const cols = 7, tw = 270, th = 480, rows = Math.ceil(files.length / cols);
      const sheet = createCanvas(cols * tw, rows * th), sx = sheet.getContext('2d');
      const { loadImage } = await import('@napi-rs/canvas');
      for (let i = 0; i < files.length; i++) sx.drawImage(await loadImage(files[i]), (i % cols) * tw, Math.floor(i / cols) * th, tw, th);
      fs.writeFileSync('out/contact.png', sheet.toBuffer('image/png'));
      files.forEach(f => fs.unlinkSync(f));
      console.log('out/contact.png');
    } else console.log(files.join('\n'));
    return;
  }

  const preview = args.includes('--preview');
  const scale = preview ? 0.5 : 1;
  const total = Math.ceil(TL.duration * FPS);
  const nW = Math.max(1, Math.min(os.cpus().length, 4));
  const per = Math.ceil(total / nW);
  const parts = [];
  const t0 = Date.now();
  let doneFrames = 0;
  await Promise.all(Array.from({ length: nW }, (_, i) => new Promise((res, rej) => {
    const from = i * per, to = Math.min(total, from + per);
    const file = path.resolve(`build/part-${i}.mp4`);
    parts.push(file);
    const wk = new Worker(fileURLToPath(import.meta.url), { workerData: { from, to, file, scale } });
    let last = 0;
    wk.on('message', m => {
      if (m.progress != null) { doneFrames += m.progress - last; last = m.progress; process.stdout.write(`\r${doneFrames}/${total} frames`); }
      if (m.done) res();
    });
    wk.on('error', rej);
  })));
  console.log(`\nframes in ${((Date.now() - t0) / 1000).toFixed(1)}s`);
  fs.writeFileSync('build/parts.txt', parts.map(p => `file '${p}'`).join('\n'));
  execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', 'build/parts.txt', '-c', 'copy', 'build/video.mp4']);

  const out = opt('--out') || (preview ? 'out/preview.mp4' : 'out/hf-incident.mp4');
  const voiced = TL.scenes.filter(s => s.audio);
  if (voiced.length) {
    // Lay each clip at its cue, then gentle cleanup + loudness for phone speakers
    // (-14 LUFS integrated, -1.5 dBTP: TikTok-friendly, no clipping).
    const inputs = [], filters = [];
    voiced.forEach((s, i) => {
      inputs.push('-i', s.audio);
      const ms = Math.round(s.audioAt * 1000);
      filters.push(`[${i}:a]aresample=48000,adelay=${ms}|${ms}[a${i}]`);
    });
    filters.push(`${voiced.map((_, i) => `[a${i}]`).join('')}amix=inputs=${voiced.length}:normalize=0:dropout_transition=0,` +
      `highpass=f=70,equalizer=f=3200:t=q:w=1.2:g=1.5,acompressor=threshold=-20dB:ratio=2.5:attack=8:release=120:makeup=2,` +
      `loudnorm=I=-14:TP=-1.5:LRA=9,apad,atrim=0:${TL.duration.toFixed(3)}[voice]`);
    execFileSync('ffmpeg', ['-y', '-loglevel', 'error', ...inputs, '-filter_complex', filters.join(';'), '-map', '[voice]', '-ar', '48000', '-ac', '2', 'build/voice.wav']);
    execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-i', 'build/video.mp4', '-i', 'build/voice.wav', '-map', '0:v', '-map', '1:a',
      '-c:v', 'copy', '-c:a', 'aac', '-b:a', '256k', '-shortest', '-movflags', '+faststart', out]);
  } else {
    execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-i', 'build/video.mp4', '-c', 'copy', '-movflags', '+faststart', out]);
  }
  console.log(out);
}
