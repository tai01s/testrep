# Cerebral Cobweb — hell decoration (generator)

Hell-themed decoration for the opening of *Cerebral Cobweb* (layout by ArdaIstGute), generated as a
.gmd you import into Geometry Dash. The original 1,622 layout objects are copied byte-for-byte; the
build fails if any of them changes.

```
python3 src/build.py          # -> out/Cerebral_Cobweb_hell_intro.gmd
python3 src/calibration.py    # -> out/Cerebral_Cobweb_calibration.gmd
```

See `VERIFY.md` for the in-game check.

## What is decorated

From the level start to about x 2450, which covers 10% whether GD counts percentage by time
(x ≈ 1370; the level is 40.27 s) or by distance (x ≈ 1835). Atmosphere layers continue a little further.

## Concept

An infernal cavern above a lava sea. A burning cobweb hangs in the abyss around a molten
"cerebral core". The core fires pulses along the web on the beats the layout already marks: the
BG pulse at 3.49 s, the platform moves at 4.12 s and 4.82 s, and the launch at 7.43 s.

- **Blocks:** obsidian slabs with molten edges, fitted to the exact layout cells.
- **Supports:** stalactites under platforms, and pillars rising from the lava under the floor pieces.
  None are placed where the moving platform carries the player.
- **Hazards:** floating spikes and saws hang from glowing threads, have red danger glows, and the
  saws throw sparks.

## Depth planes (back to front)

| Layer | Content | Parallax (x / y) |
|-------|---------|------------------|
| B5 | Web, core, haze | 0.90 / 0.85 |
| B5 (gradients) | Far spires | 0.90 / 0.85 |
| B4 | Far spire rims | 0.90 / 0.85 |
| B4 (gradients) | Mid spires | 0.55 / 0.45 |
| B3 | Mid rims and veins | 0.55 / 0.45 |
| B3 (gradients) | Near rock and lava body | 0 (gameplay depth) |
| B2 | Cracks, molten edges, hazard glows, threads, lava surface, embers | 0 |
| (default) | Layout objects | — |
| T2 | Sparks | 0 |
| T3 (gradients) | Foreground silhouettes | −0.30 / screen-locked |

## Technical notes

- **Shapes:** solid triangles made with Gradient triggers in vertex mode. Each triangle repeats
  one corner group and uses a single colour, so it can't depend on vertex order or gradient
  direction. Every gradient gets its own ID, because triggers that share an ID edit the same
  effect.
- **Colours:** layout outlines use channel 32, which only exists in the intro, so its colour is set
  in the level settings. Channels 1 and 1004 continue later in the level, so they are set by
  trigger at the start and reverted at x 3300.
- **Setup triggers** sit at x 2–8, so they fire on the first frame.
- **No pop-in:** long strands are split into ≤90-unit pieces, and big glows keep their centres near
  the screen. GD culls scaled objects by their centre.
- **Groups and channels:** deco groups start at 200 (the layout uses 1–15); deco colour channels
  are 100–127.

## Sources

- Technique: GD Creator School guides (github.com/GDCreatorSchool/gdcs2, MIT).
- Level format: gddocs (Wyliemaster), gd-info-explorer (object names and 2.2 property keys).
- Default object strings: gmdkit (MIT).
- Real-level conventions (parallax keys, z-layer encoding, gradient corners): your reference level
  Society.
