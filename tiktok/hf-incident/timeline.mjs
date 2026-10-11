// Builds the master timeline: when each scene starts, where its voice clip
// sits, and per-word timings. Uses the real ElevenLabs timestamps from
// audio/*.json when present; otherwise estimates timing so the visuals can be
// previewed silently.
import fs from 'node:fs';
import path from 'node:path';
import { LINES } from './script.mjs';

export const LEAD = 0.22; // visuals start this long before the voice in each scene

export const norm = w => w.toLowerCase().replace(/[^a-z0-9]/g, '');

function estimateWords(text) {
  const wps = 2.85;
  let t = 0.05;
  return text.split(/\s+/).map(w => {
    const len = 1 / wps * (0.55 + 0.45 * Math.min(w.length, 10) / 5);
    const o = { w, s: +t.toFixed(3), e: +(t + len * 0.92).toFixed(3) };
    t += len + (/[.?!:]$/.test(w) ? 0.38 : /[,;]$/.test(w) ? 0.18 : 0);
    return o;
  });
}

export function buildTimeline(dir = 'audio') {
  let t = 0;
  let voiced = 0;
  const scenes = LINES.map((line, i) => {
    const metaPath = path.join(dir, `${line.id}.json`);
    let words, audio = null, clipDur;
    const meta = fs.existsSync(metaPath) ? JSON.parse(fs.readFileSync(metaPath)) : null;
    if (meta && meta.text === line.text && fs.existsSync(path.join(dir, `${line.id}.mp3`))) {
      words = meta.words;
      audio = path.join(dir, `${line.id}.mp3`);
      clipDur = meta.duration;
      voiced++;
    } else {
      words = estimateWords(line.text);
    }
    const speechEnd = words[words.length - 1].e;
    const dur = LEAD + speechEnd + line.tail;
    // Scene-local word times (include the lead-in).
    const local = words.map(w => ({ w: w.w, n: norm(w.w), s: w.s + LEAD, e: w.e + LEAD }));
    const s = { id: line.id, index: i, text: line.text, start: t, dur, audio, audioAt: t + LEAD, clipDur, words: local };
    t += dur;
    return s;
  });
  return { duration: t, scenes, voiced: voiced === LINES.length, partial: voiced > 0 && voiced < LINES.length };
}
