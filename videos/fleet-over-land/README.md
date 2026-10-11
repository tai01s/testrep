# The Fleet That Sailed Over Land (1453)

A 75-second vertical (1080×1920, 30 fps) TikTok made with [Remotion](https://www.remotion.dev/).
The finished video is **`fleet-over-land.mp4`**. Its audio is normalised to −14 LUFS.

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
- **Narration:** one WAV per line in `public/vo/`, with the script in `scripts/lines.json`.
  - `FISH_API_KEY=... npm run voice:fish` uses Fish Audio. The default voice is "calm woman" (`0f2279f5f3894673a675eb85a61e1e2e`); override it with `FISH_VOICE_ID`. Fish bills **API credit** separately from platform credit.
  - `npm run voice:local` uses the free local Kokoro voice (`af_heart`). The current render uses this one.
  - After regenerating the voice, run `npm run align`. It re-times the captions with Whisper, and the whole timeline re-flows to the new line lengths.
- **SFX:** synthesised by `scripts/make-sfx.py`.

## Build

```bash
npm install
npm run studio                 # preview
npm run render && npm run master
```

On machines where Remotion can't download Chrome, set `REMOTION_CHROME=/path/to/chrome-headless-shell`.

The fonts are Montserrat and Cinzel (SIL OFL), bundled in `public/fonts`. The map is schematic, not to scale.
