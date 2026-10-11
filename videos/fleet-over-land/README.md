# The Fleet That Sailed Over Land (1453)

A vertical (1080×1920, 30 fps) TikTok made with [Remotion](https://www.remotion.dev/), in two languages:

- **`fleet-over-land.mp4`**: English (74 s), composition `FleetOverLand`
- **`fleet-over-land-tr.mp4`**: Turkish (81 s), composition `FleetOverLand-TR`. The hook uses the Turkish idiom *gemileri karadan yürütmek*.

Audio is normalised to −14 LUFS.

> "How do you get a navy past an unbreakable chain? You take it for a walk."

## Story beats

| Line | Visual |
|---|---|
| Hook | Close-up of the chain across the Golden Horn, then a galley walking over a hill on cartoon legs |
| Setup | Wide map: Constantinople, Galata, the Bosphorus, the Ottoman camp and fleet, Mehmed II card |
| Chain / fail | The Horn lights up, the chain draws across its mouth, Ottoman ships hit it and bounce off ("FAILED") |
| Twist / road | The map darkens, then a plank road is laid over the hills behind Galata and greased |
| Drag | **First music drop.** Ships stream over the hill on rollers while a counter climbs to ×70 |
| Oars | Side view of a galley hauled uphill on greased rollers, oars rowing through the air |
| Reveal | Sunrise on 22 April: the Ottoman fleet sits inside the harbour, behind the intact chain |
| Stretch | Defenders move off the land walls to the newly threatened sea walls |
| Fall | **Second music drop** on "Constantinople falls" (29 May 1453), and Ottoman flags go up |
| Outro | The galley strolls off past the skyline, then the title card |

## Audio

- **Music:** "Тусовщица" by ftshsm (YouTube `eF6LRJiqIpo`). The file isn't committed. Download it first:
  `yt-dlp -x -f m4a -o public/music/tusovshchitsa.m4a "https://www.youtube.com/watch?v=eF6LRJiqIpo"`
  `src/Soundtrack.tsx` lines up the track's drops (30.95 s and 107.75 s) with the "drag" line and the word "falls". It also ducks the music under the narration.
- **Narration:** one WAV per line in `public/vo/<lang>/`, with the script in `scripts/lines.<lang>.json`. Set `LANG_CODE=tr` on the voice, retake and align commands to work on Turkish.
  - `FISH_API_KEY=... npm run voice:fish` uses Fish Audio. The current render uses this one. The default voices are "calm woman" for English (`0f2279f5f3894673a675eb85a61e1e2e`) and "Genç Türk Kadın" for Turkish (`fe96529b852c415d869158a54098ca90`); override either with `FISH_VOICE_ID`. The default model is `s2.1-pro-free`, which needs no API credit. Paid models such as `s1` (set with `FISH_MODEL`) need API credit, which Fish bills separately from platform credit.
  - `npm run voice:local` uses a free offline Kokoro voice (`af_heart`) as a fallback.
  - `npm run voice:retake` transcribes every line with Whisper large-v3-turbo. Any line that doesn't match the script, which usually means a mispronounced word, is regenerated until it does, with up to 4 takes.
  - After regenerating the voice, run `npm run align`. It re-times the captions with Whisper, and the whole timeline re-flows to the new line lengths.
- **SFX:** synthesised by `scripts/make-sfx.py`.

## Build

```bash
npm install
npm run studio                 # preview
npm run render && npm run master        # English
npm run render:tr && npm run master:tr  # Turkish
```

All on-screen text is in `src/i18n.ts`. The animation cues are tied to spoken words, and `i18n.ts` maps each English cue word to its Turkish equivalent.

On machines where Remotion can't download Chrome, set `REMOTION_CHROME=/path/to/chrome-headless-shell`.

The fonts are Montserrat and Cinzel (SIL OFL), bundled in `public/fonts`. The map is schematic, not to scale.
