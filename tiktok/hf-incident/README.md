# TikTok: "An AI broke into Hugging Face"

A ~95 second vertical (1080×1920, 30fps) explainer about the July 2026
OpenAI–Hugging Face incident. It has an ElevenLabs narration, a #3D3D3D background, halftone and dot-matrix
graphics, flat 2D UI animations, and Times New Normal as the serif. Music hasn't been chosen yet.

## Make it

```bash
npm install
# fonts/ must contain the serif (Times New Normal Regular.ttf). It's gitignored because its license is unknown.
export ELEVENLABS_API_KEY=sk_...
node tts.mjs          # narration: audio/<scene>.mp3 + word timestamps
node render.mjs       # -> out/hf-incident.mp4
```

Other render modes:

- `node render.mjs --preview`: half resolution, fast.
- `node render.mjs --contact`: one frame per scene in `out/contact.png`.
- `node render.mjs --stills 3,12.5`: PNGs at the given seconds.

Without `audio/`, the renderer estimates word timing and outputs a silent cut, so you can
review the visuals before generating the voice.

## How it fits together

| file | what |
| --- | --- |
| `script.mjs` | Narration, one line per scene. The same text drives the TTS and the captions. |
| `tts.mjs` | ElevenLabs `with-timestamps`, one request per scene, using `previous_text`/`next_text` stitching so the read stays continuous. Caches clips; `--force` or a scene id re-does them. |
| `timeline.mjs` | Scene start times and per-word timings, real or estimated. |
| `scenes.mjs` | One draw function per scene. Animations are cued on spoken words (`S.cue('sandbox')`), so they stay in sync when the voice changes. |
| `lib.mjs` | Palette, easing, halftone fields, 5×7 dot-matrix font, dot-bitmap icons. |
| `render.mjs` | Canvas frames rendered by 4 workers, piped to ffmpeg. Voice clips are placed at their cues, then high-pass, light compression and loudness normalization to -14 LUFS. |

Voice settings (in `tts.mjs`): `eleven_multilingual_v2`, stability 0.42, similarity 0.82,
style 0.22, speaker boost, speed 1.06. Set `EL_MODEL=eleven_v3` to try v3, which is more expressive but has no stitching.

**Music:** add it later as a second input in the final ffmpeg mux in `render.mjs`, around -20 LUFS, ducked under the voice.

## Sources

- OpenAI, "The Hugging Face incident and the road ahead" (Aug 26, 2026)
- Hugging Face, "Anatomy of a Frontier Lab Agent Intrusion" (technical timeline)
- Infosecurity Magazine, CBC, Reuters (via secondary reports) on the "warning shot" framing and the disclosure dates
