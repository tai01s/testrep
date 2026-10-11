// Narration with Fish Audio:
//   FISH_API_KEY=sk-... npm run voice:fish && npm run align
import fs from "node:fs";

const key = process.env.FISH_API_KEY;
if (!key) throw new Error("Set FISH_API_KEY");
// "calm woman": young, calm, clear female voice. Override with FISH_VOICE_ID.
const voiceId = process.env.FISH_VOICE_ID ?? "0f2279f5f3894673a675eb85a61e1e2e";
// s2.1-pro-free needs no API credit; paid models (e.g. s1) do
const model = process.env.FISH_MODEL ?? "s2.1-pro-free";

const lines = JSON.parse(fs.readFileSync(new URL("./lines.json", import.meta.url)));
fs.mkdirSync("public/vo", { recursive: true });
for (const line of lines) {
  const res = await fetch("https://api.fish.audio/v1/tts", {
    method: "POST",
    headers: { Authorization: `Bearer ${key}`, "Content-Type": "application/json", model },
    body: JSON.stringify({ text: line.text, reference_id: voiceId, format: "wav", latency: "normal" }),
  });
  if (!res.ok) throw new Error(`${line.id}: ${res.status} ${await res.text()}`);
  fs.writeFileSync(`public/vo/${line.id}.wav`, Buffer.from(await res.arrayBuffer()));
  console.log("wrote", line.id);
}
