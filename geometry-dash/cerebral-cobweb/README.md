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

## v2 detail pass

- **Faceted rock.** Every rock mass is a triangle mesh with no gaps. Each facet takes one of 8 rock
  shades. Facets near a lit edge get lava light, more when they face it; the inside stays
  near-black. Facets are small where the light is and large where the rock is rarely on screen.
  Pillars use tall facets, so they read as basalt columns.
- **Blocks.** Every layout cell has a design fitted to its exact bounds. Slabs get forged bricks
  with a warm bevel on the lit side and glowing mortar joints. Single blocks get a bevelled face,
  a recessed panel and a molten rune.
- **Cracks** branch like dendrites, with a glowing node at each fork. This ties the rock to the
  "cerebral" web. On the big beats a light wave runs through them from left to right.
- **Spikes.** Coloured spikes get a dark obsidian core drawn over them, so the layout colour shows
  as a molten rim. Every spike gets a vein and a white-hot tip that flashes on the beat.
  Diamond seams glow. Saws get a molten ring, a hub and a bolt.
- **Atmosphere.** Floating debris bobs at gameplay and mid-ground depth. A lavafall pours from the
  overhang. Bubbles pop on the lava and ash falls. Out-of-focus embers sit in front of everything,
  and fog separates the depth planes. The core's neural knot turns slowly, and the web has molten
  beads that catch every pulse.

The styles are reusable modules (`style_rock.py`, `style_hazards.py`, `style_atmos.py`,
`mesh.py`), so the same look can be applied to the rest of the level.

## Depth planes (back to front)

| Layer | Content | Parallax (x / y) |
|-------|---------|------------------|
| B5 | Web, beads, core, haze | 0.90 / 0.85 |
| B5 (gradients) | Far spires (faceted) | 0.90 / 0.85 |
| B4 | Far spire rims, depth fog | 0.90 / 0.85 |
| B4 (gradients) | Mid spires and mid debris (faceted) | 0.55 / 0.45 |
| B3 | Mid rims and veins; bricks and block faces (z-order 20–28) | mid / 0 |
| B3 (gradients) | Near rock, debris, lavafall | 0 (gameplay depth) |
| B2 | Cracks, molten edges, rims, threads, lava surface, embers, rune and seam glows | 0 |
| B1 | Crack nodes, spike base glows | 0 |
| (default) | Layout objects | — |
| T1 (gradients) | Obsidian cores inside coloured spikes | 0 |
| T2 | Spike veins and tips, saw housings, sparks | 0 |
| T3 | Out-of-focus embers | 0 |
| T3 (gradients) | Foreground silhouettes | −0.30 / screen-locked |

## Technical notes

- **Shapes:** solid triangles made with Gradient triggers in vertex mode. Each triangle repeats
  one corner group and uses a single colour, so it can't depend on vertex order or gradient
  direction. Every gradient gets its own ID, because triggers that share an ID edit the same
  effect.
- **Colours:** layout outlines use channel 32, which only exists in the intro, so its colour is set
  in the level settings. Channels 1 and 1004 continue later in the level, so they are set by
  trigger at the start and reverted at x 3300.
- **Setup triggers** sit at x 2–8, so they fire on the first frame. Gradient triggers stack in
  columns of 400 (x 4.0, 4.5, 5.0, 5.5).
- **Loops** (debris bobbing, the turning core) are spawn loops. A Stop trigger at x 3300 ends
  them once the intro is off screen.
- **Budget:** about 1,500 gradient triangles and 6,500 deco objects. Facet density is set per
  rock mass in `intro_hell.py` (`near` and `growth` in each `facet_fill` call).
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
