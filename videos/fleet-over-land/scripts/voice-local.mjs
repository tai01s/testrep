// Stand-in narration with Kokoro (local, free). Use voice-fish.mjs for the real Fish Audio voice.
import fs from "node:fs";
import { KokoroTTS } from "kokoro-js";

// "kokoro" holds respellings Kokoro needs (e.g. Mehmed -> Meh-med)
const lines = JSON.parse(fs.readFileSync(new URL("./lines.en.json", import.meta.url)));
const voice = process.env.KOKORO_VOICE ?? "af_heart";
const tts = await KokoroTTS.from_pretrained("onnx-community/Kokoro-82M-v1.0-ONNX", { dtype: "fp32", device: "cpu" });

fs.mkdirSync("public/vo/en", { recursive: true });
for (const line of lines) {
  const audio = await tts.generate(line.kokoro ?? line.text, { voice, speed: 0.95 });
  await audio.save(`public/vo/en/${line.id}.wav`);
  console.log("wrote", line.id);
}
