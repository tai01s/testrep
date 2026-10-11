// Re-generates Fish Audio lines that Whisper doesn't transcribe back as the script
// (i.e. mispronounced), keeping the best of up to 4 takes per line.
//   FISH_API_KEY=... LANG_CODE=tr node scripts/retake.mjs hook1 fail ...   (no ids = all lines)
import fs from "node:fs";
import { pipeline } from "@huggingface/transformers";
import wavefile from "wavefile";
const key = process.env.FISH_API_KEY;
const lang = process.env.LANG_CODE ?? "en";
const LANGUAGE = { en: "english", tr: "turkish" }[lang];
// "Paddington": deep, warm British male narrator
const VOICES = { en: "5e79e8f5d2b345f98baa8c83c947532d" };
const lines = JSON.parse(fs.readFileSync(`scripts/lines.${lang}.json`));
const asr = await pipeline("automatic-speech-recognition", "onnx-community/whisper-large-v3-turbo", { dtype: "fp32" });
const norm = (s) => s.toLocaleLowerCase(lang).replace(/[^\p{L}\p{N} ]/gu, " ").split(/\s+/).filter(Boolean);
const score = (a, b) => { // word-level edit distance
  const D = Array.from({ length: a.length + 1 }, (_, i) => [i, ...Array(b.length).fill(0)]);
  for (let j = 1; j <= b.length; j++) D[0][j] = j;
  for (let i = 1; i <= a.length; i++) for (let j = 1; j <= b.length; j++)
    D[i][j] = Math.min(D[i-1][j] + 1, D[i][j-1] + 1, D[i-1][j-1] + (a[i-1] === b[j-1] ? 0 : 1));
  return D[a.length][b.length];
};
const transcribe = (buf) => { const w = new wavefile.WaveFile(buf); w.toBitDepth("32f"); w.toSampleRate(16000); let s = w.getSamples(); if (Array.isArray(s)) s = s[0];
  return asr(Float32Array.from(s), { language: LANGUAGE, task: "transcribe" }).then((r) => r.text.trim()); };
const ids = process.argv.length > 2 ? process.argv.slice(2) : lines.map((l) => l.id);
for (const id of ids) {
  const line = lines.find((l) => l.id === id);
  const targets = [norm(line.text), norm(line.caption ?? line.text)];
  const errOf = (t) => Math.min(...targets.map((g) => score(norm(t), g)));
  const cur = await transcribe(fs.readFileSync(`public/vo/${lang}/${id}.wav`));
  let best = { err: errOf(cur), buf: null, text: cur };
  for (let k = 0; k < 4 && best.err > 0; k++) {
    const res = await fetch("https://api.fish.audio/v1/tts", { method: "POST", headers: { Authorization: `Bearer ${key}`, "Content-Type": "application/json", model: "s2.1-pro-free" },
      body: JSON.stringify({ text: line.text, reference_id: process.env.FISH_VOICE_ID ?? VOICES[lang], format: "wav", latency: "normal" }) });
    const buf = Buffer.from(await res.arrayBuffer());
    const text = await transcribe(buf);
    const err = errOf(text);
    console.log(id, "take", k, "err", err, text);
    if (err < best.err) best = { err, buf, text };
  }
  if (best.buf) fs.writeFileSync(`public/vo/${lang}/${id}.wav`, best.buf);
  console.log("KEEP", id, best.err, best.text);
}
