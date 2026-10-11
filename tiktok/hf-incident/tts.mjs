// Generates the narration with ElevenLabs, one clip per scene, plus
// character-level timestamps so the animations and captions sync to the voice.
//
//   ELEVENLABS_API_KEY=... node tts.mjs            # all scenes (skips cached)
//   ELEVENLABS_API_KEY=... node tts.mjs --force    # regenerate everything
//   ELEVENLABS_API_KEY=... node tts.mjs warning    # just one scene
//
// Each scene is generated separately (so pauses between beats are exact), but
// with previous_text / next_text request stitching so the delivery still flows
// like one continuous read instead of 14 disconnected sentences.
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { LINES, VOICE_ID } from './script.mjs';

const KEY = process.env.ELEVENLABS_API_KEY;
if (!KEY) { console.error('Set ELEVENLABS_API_KEY'); process.exit(1); }

const args = process.argv.slice(2);
const force = args.includes('--force');
const only = args.filter(a => !a.startsWith('--'));
const MODEL = process.env.EL_MODEL || 'eleven_multilingual_v2';

// Tuned for this voice (a soft, slow professional clone fine-tuned on
// multilingual_v2): stability near its 0.5 default so it keeps its calm
// timbre but still varies intonation; similarity high to stay on the clone;
// only a touch of style (PVCs get unstable with more); sped up a little so
// the meditative delivery still moves at TikTok pace.
const VOICE_SETTINGS = {
  stability: 0.48,
  similarity_boost: 0.85,
  style: 0.08,
  use_speaker_boost: true,
  speed: 1.1,
};

const DIR = path.resolve('audio');
fs.mkdirSync(DIR, { recursive: true });

async function tts(i, format) {
  const line = LINES[i];
  const body = {
    text: line.text,
    model_id: MODEL,
    voice_settings: VOICE_SETTINGS,
    seed: 4207 + i,
    apply_text_normalization: 'auto',
  };
  // Request stitching: context on both sides keeps intonation continuous.
  if (i > 0) body.previous_text = LINES.slice(Math.max(0, i - 2), i).map(l => l.text).join(' ');
  if (i < LINES.length - 1) body.next_text = LINES[i + 1].text;
  // eleven_v3 doesn't support stitching or speed the same way.
  if (MODEL === 'eleven_v3') { delete body.previous_text; delete body.next_text; delete body.voice_settings.speed; }

  const url = `https://api.elevenlabs.io/v1/text-to-speech/${VOICE_ID}/with-timestamps?output_format=${format}`;
  for (let attempt = 0; attempt < 4; attempt++) {
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'xi-api-key': KEY, 'content-type': 'application/json', accept: 'application/json' },
      body: JSON.stringify(body),
    });
    if (res.ok) return res.json();
    const msg = await res.text();
    // Higher-bitrate formats need a paid tier; fall back to 128k.
    if ((res.status === 403 || res.status === 400) && format !== 'mp3_44100_128' && /output_format|tier|subscription/i.test(msg)) return null;
    if (res.status === 429 || res.status >= 500) { await new Promise(r => setTimeout(r, 2000 * 2 ** attempt)); continue; }
    throw new Error(`ElevenLabs ${res.status}: ${msg}`);
  }
  throw new Error('ElevenLabs: too many retries');
}

for (let i = 0; i < LINES.length; i++) {
  const line = LINES[i];
  if (only.length && !only.includes(line.id)) continue;
  const mp3 = path.join(DIR, `${line.id}.mp3`);
  const meta = path.join(DIR, `${line.id}.json`);
  if (!force && fs.existsSync(mp3) && fs.existsSync(meta) && JSON.parse(fs.readFileSync(meta)).text === line.text) {
    console.log(`= ${line.id} (cached)`);
    continue;
  }
  let out = await tts(i, 'mp3_44100_192');
  if (!out) out = await tts(i, 'mp3_44100_128');
  fs.writeFileSync(mp3, Buffer.from(out.audio_base64, 'base64'));
  const a = out.alignment;
  const dur = parseFloat(execFileSync('ffprobe', ['-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', mp3]).toString());
  fs.writeFileSync(meta, JSON.stringify({
    text: line.text, model: MODEL, voice: VOICE_ID, settings: VOICE_SETTINGS, duration: dur,
    words: wordsFromAlignment(a),
  }, null, 1));
  console.log(`+ ${line.id}  ${dur.toFixed(2)}s`);
}

// Character alignment -> [{w, s, e}] using the same whitespace split as the script.
function wordsFromAlignment(a) {
  const words = [];
  let cur = null;
  a.characters.forEach((ch, k) => {
    if (/\s/.test(ch)) { if (cur) words.push(cur); cur = null; return; }
    if (!cur) cur = { w: '', s: a.character_start_times_seconds[k], e: 0 };
    cur.w += ch;
    cur.e = a.character_end_times_seconds[k];
  });
  if (cur) words.push(cur);
  return words.map(w => ({ w: w.w, s: +w.s.toFixed(3), e: +w.e.toFixed(3) }));
}
