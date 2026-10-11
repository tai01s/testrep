// Word-level timings for captions: Whisper transcribes each VO line, then the
// script's own words are aligned to the recognised words (DP), so captions
// always show the script text, not Whisper's spelling.
import fs from "node:fs";
import { pipeline } from "@huggingface/transformers";
import wavefile from "wavefile";

const lang = process.env.LANG_CODE ?? "en";
const lines = JSON.parse(fs.readFileSync(new URL(`./lines.${lang}.json`, import.meta.url)));
const model = lang === "en" ? "onnx-community/whisper-small.en_timestamped" : "onnx-community/whisper-large-v3-turbo_timestamped";
const asr = await pipeline("automatic-speech-recognition", model, { dtype: "fp32" });
const asrOpts = lang === "en" ? {} : { language: { tr: "turkish" }[lang] ?? lang, task: "transcribe" };

const norm = (w) => w.toLocaleLowerCase(lang).normalize("NFD").replace(/[^\p{L}\p{N}]/gu, "");
// split on hyphens so "21-year-old" lines up however Whisper tokenises it
const splitHyphens = (w) => w.split("-").map((p, i, a) => p + (i < a.length - 1 ? "-" : ""));
const scriptWords = (text) => text.split(/\s+/).flatMap(splitHyphens).map((p) => ({ text: p, key: norm(p) }));

function readWav(path) {
  const wav = new wavefile.WaveFile(fs.readFileSync(path));
  const rate = wav.fmt.sampleRate;
  wav.toBitDepth("32f");
  let samples = wav.getSamples();
  if (Array.isArray(samples)) samples = samples[0];
  const dur = samples.length / rate;
  wav.toSampleRate(16000);
  let s16 = wav.getSamples();
  if (Array.isArray(s16)) s16 = s16[0];
  return { audio: Float32Array.from(s16), duration: dur };
}

function align(sw, hw) {
  const n = sw.length, m = hw.length;
  const cost = (a, b) => (a.key === norm(b.text) ? 0 : 1);
  const D = Array.from({ length: n + 1 }, () => new Array(m + 1).fill(0));
  for (let i = 1; i <= n; i++) D[i][0] = i;
  for (let j = 1; j <= m; j++) D[0][j] = j;
  for (let i = 1; i <= n; i++)
    for (let j = 1; j <= m; j++)
      D[i][j] = Math.min(D[i - 1][j - 1] + cost(sw[i - 1], hw[j - 1]), D[i - 1][j] + 1, D[i][j - 1] + 1);
  const match = new Array(n).fill(null);
  let i = n, j = m;
  while (i > 0 && j > 0) {
    if (D[i][j] === D[i - 1][j - 1] + cost(sw[i - 1], hw[j - 1])) { match[i - 1] = j - 1; i--; j--; }
    else if (D[i][j] === D[i - 1][j] + 1) i--;
    else j--;
  }
  return match;
}

const out = [];
for (const line of lines) {
  const { audio, duration } = readWav(`public/vo/${lang}/${line.id}.wav`);
  const r = await asr(audio, { return_timestamps: "word", ...asrOpts });
  const hw = r.chunks.flatMap((c) => {
    const start = c.timestamp[0], end = c.timestamp[1] ?? duration;
    const parts = splitHyphens(c.text.trim());
    return parts.map((p, i) => ({ text: p, start: start + ((end - start) * i) / parts.length, end: start + ((end - start) * (i + 1)) / parts.length }));
  });
  // captions use "caption" (numerals etc.) when the spoken text differs
  const sw = scriptWords(line.caption ?? line.text);
  const match = align(sw, hw);
  // matched words take Whisper times; unmatched ones are interpolated between neighbours
  const words = sw.map((w, k) => (match[k] != null ? { text: w.text, start: hw[match[k]].start, end: hw[match[k]].end } : { text: w.text }));
  for (let k = 0; k < words.length; k++) {
    if (words[k].start != null) continue;
    let a = k - 1; while (a >= 0 && words[a].start == null) a--;
    let b = k; while (b < words.length && words[b].start == null) b++;
    const t0 = a >= 0 ? words[a].end : 0, t1 = b < words.length ? words[b].start : duration;
    const span = b - a - 1;
    for (let q = a + 1; q < b; q++) {
      words[q].start = t0 + ((t1 - t0) * (q - a - 1)) / span;
      words[q].end = t0 + ((t1 - t0) * (q - a)) / span;
    }
  }
  // re-join hyphenated pieces into one caption word
  const joined = [];
  for (const w of words) {
    const prev = joined[joined.length - 1];
    if (prev && prev.text.endsWith("-")) { prev.text += w.text; prev.end = w.end; }
    else joined.push({ ...w });
  }
  out.push({ id: line.id, text: line.caption ?? line.text, duration, words: joined.map((w) => ({ ...w, start: +w.start.toFixed(3), end: +w.end.toFixed(3) })) });
  console.log(line.id, duration.toFixed(2), r.text.trim());
}
fs.writeFileSync(`src/vo.${lang}.json`, JSON.stringify(out, null, 1));
