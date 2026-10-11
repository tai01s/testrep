// Narration with Fish Audio:
//   FISH_API_KEY=sk-... LANG_CODE=tr npm run voice:fish && LANG_CODE=tr npm run align
import fs from "node:fs";

const key = process.env.FISH_API_KEY;
if (!key) throw new Error("Set FISH_API_KEY");
const lang = process.env.LANG_CODE ?? "en";
// en: "calm woman" (young, calm, clear); tr: "Genç Türk Kadın" (young, gentle, calm). Override with FISH_VOICE_ID.
const VOICES = { en: "0f2279f5f3894673a675eb85a61e1e2e", tr: "fe96529b852c415d869158a54098ca90" };
const voiceId = process.env.FISH_VOICE_ID ?? VOICES[lang];
// s2.1-pro-free needs no API credit; paid models (e.g. s1) do
const model = process.env.FISH_MODEL ?? "s2.1-pro-free";

const lines = JSON.parse(fs.readFileSync(new URL(`./lines.${lang}.json`, import.meta.url)));
fs.mkdirSync(`public/vo/${lang}`, { recursive: true });
for (const line of lines) {
  const res = await fetch("https://api.fish.audio/v1/tts", {
    method: "POST",
    headers: { Authorization: `Bearer ${key}`, "Content-Type": "application/json", model },
    body: JSON.stringify({ text: line.text, reference_id: voiceId, format: "wav", latency: "normal" }),
  });
  if (!res.ok) throw new Error(`${line.id}: ${res.status} ${await res.text()}`);
  fs.writeFileSync(`public/vo/${lang}/${line.id}.wav`, Buffer.from(await res.arrayBuffer()));
  console.log("wrote", line.id);
}
