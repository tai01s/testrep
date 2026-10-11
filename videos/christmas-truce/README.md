# The Christmas Truce (1914)

A vertical (1080×1920, 30 fps) TikTok made with [Remotion](https://www.remotion.dev/).
The finished video is **`christmas-truce.mp4`**, with audio normalised to −14 LUFS.

> "Christmas Eve, 1914. Along parts of the Western Front, the guns fall silent. And nobody ordered it."

## Story beats

| Line | Visual |
|---|---|
| Hook | Night panorama of both trench lines: rifle flashes, shell bursts and a drifting star shell. The guns stop, snow starts, and the music comes in |
| Setup | Map of the Western Front, drawn from the Belgian coast to Switzerland with Ypres marked. Then a cross-section showing the British trench, the German trench and no man's land (< 100 m) |
| Trees / singing | Candle-lit Christmas trees appear along the German parapet. Music notes rise as "Stille Nacht" is sung, and the British answer with "O Come, All Ye Faithful" |
| Morning | Dawn on 25 December. A church bell rings and the first men climb out, unarmed |
| Nobody shoots | The music drops out and a full-screen title appears |
| Meeting | Both sides walk out, shake hands and swap cigarettes, chocolate, buttons and beer |
| Burial / football | Colours wash out for the joint burial. Then a kick-about, with caps as goalposts |
| Aftermath | Calendar flips (25 Dec → Boxing Day → 1 Jan 1915), a "No more truces" stamp, and the war returning (1915 → 1918) |
| Outro | One candle tree in the snow, the title card and the channel logo |

Uniforms match 1914: British soldiers wear soft service caps (steel helmets came in 1915–16), and German soldiers wear the Pickelhaube.

## Audio

- **Music:** "lilacs (slowed)" by velours & azrxel. It isn't committed. The YouTube upload you linked is region-blocked here, so I took the same track from SoundCloud:
  `yt-dlp -o public/music/lilacs.m4a "https://api.soundcloud.com/tracks/soundcloud%3Atracks%3A2108390433"`
- **Narration:** Fish Audio voice "Paddington" (`5e79e8f5d2b345f98baa8c83c947532d`), a deep, warm British male narrator, on the free `s2.1-pro-free` model. The script is in `scripts/lines.en.json`.
  `FISH_API_KEY=... npm run voice:fish && npm run voice:retake && npm run align`
- **SFX:** gunfire, artillery, a flare, wind, a bell, kicks, a page flip and a stamp, all synthesised by `scripts/make-sfx.py`.

## Build

```bash
npm install
npm run studio
npm run render && npm run master
```

Set `REMOTION_CHROME=/path/to/chrome-headless-shell` if Remotion can't download Chrome.
