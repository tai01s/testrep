# What the 8 reference levels actually contain

Decoded object by object from the `.gmd` exports you sent (GDShare format; the `k4` level string, gzip). Tools are in
`../tools/`. Lengths are estimates from object x-positions and speed portals: teleports, time warps and arrow
triggers make them approximate.

All eight are current top-list extreme demons. Their level IDs (119M to 150M) are newer than my AREDL data snapshot
(May 2025), so I can't give their exact positions. What matters: **they are far harder than AREDL #600**, so their
gameplay density is not a target for our level. Their **deco systems** are what we're studying.

| Level | Creator(s) | Objects | ~Length | Colour channels | HSV-shifted | Scaled | Grouped (animated) | Triggers |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Society | Neomarbilan | 167,383 | ~105–128 s | 202 | 40% | 57% | 89% | 5,743 |
| Green Bullet | cherryteam (host MinaY) | 197,825 | ~110 s | 327 | 63% | 50% | 91% | 9,799 |
| Thinking Space II | CairoX + CoCy team, deco host DrCuber | 139,568 | ~66 s | 55 | 45% | 69% | 75% | 3,946 |
| Artemis 13 | mvngo | 51,879 | ~70 s | 95 | 28% | 35% | 34% | 3,048 |
| GRIEF | IcEDCave | 189,605 | ~165 s | 118 | 29% | 56% | 89% | 11,142 |
| Antarctic Lights | declanlc, SkyJax, Tolstyh, Arcturus | 54,900 | ~58 s | 139 | 40% | 28% | 84% | 3,518 |
| Flamewall | UNarwall | 413,736 | ~400 s | 100 | 35% | 36% | 51% | 16,832 |
| ORBIT | MindCap | 310,486 | ~140 s | 247 | 41% | 53% | 81% | 90,055 (38k keyframes) |

## Colour

- **The background is near-black in every level.** Colour comes from objects, mostly blending glow, which adds light and
  so shows up perfectly on black.
- The **blue references**, closest to our brief:
  - **Antarctic Lights:** BG `#0a0a16` / `#04080f`, later `#010111`. OBJ colour is ice blue `#c2ebff`, with a violet
    accent `#8e8dff` (blending, 90% opacity). In the intro (2–16 s) the BG swaps between three near-black tints
    (`#0a0a16`, `#130609`, `#04080f`) roughly every beat. You barely notice it, but it makes the background breathe.
  - **ORBIT:** BG `#090d1a`, then `#001931` / `#001124` / `#1a1536`. Ground `#0066ff`, middleground `#287dff`.
  - **Society:** BG `#030029`, `#180161`, `#110f20`. Main fill channel `#05008d`.
- **Palette systems, not loose colours.** Every level defines a few base colours and dozens of **copy-colour channels
  with HSV offsets** (for example "copy of OBJ, brightness ×2, blending"). One colour trigger then re-grades a whole
  family of objects at once.
- **Strobe moments are rare and short.** Society flips the BG between `#180161` and `#4f1787` about every 0.05–0.1 s
  for under a second (79.4–80.1 s), right before a section change. GRIEF does the same with its line colour around
  118–122 s.

## Object vocabulary (what the deco is made of)

- The most-used objects across all eight: **Large Glow Orb** (1888), **Straight Large/Medium/Small Glow** (1011/503/1292),
  **Thin Line Glow** (1754), **Colored Inner Square** (211), **3DL Top Middle / Half Top Middle** (507/508),
  **Outline Top** (468).
- **Glow plus line/outline work is 36–53% of all objects in every level.** The object count goes into light and line
  work, not hazards.
- Real hazards are only **3–15%** of objects.

## Layers (Z-layer use by role)

| Role | Where it lives |
|---|---|
| Orbs, pads, portals | Default layer in 7 of 8 levels (84–95%). ORBIT is the exception (45%). |
| Hazards | Default / T1 / T2, above most deco |
| Glow | Split: B1/B2 behind structures, and T2/T3 as overlays |
| Fill blocks | Mostly B layers (B1, B3, B4) |
| Particles | High layers (T3/T4) |

Z-order: creators space orders out (Society goes from −100 to 9999 with 112 distinct values; Flamewall uses 3,040
distinct values).

## Motion and sync

- 34–91% of objects are grouped, meaning they're moved, pulsed or faded by triggers. These levels are alive, not
  static.
- Position-triggered **pulse triggers fire in gaps of about 0.16–0.36 s**: deco syncs to 8th/16th-note drums, not just
  to the beat.
- **Drops show up as deco-density jumps**, counting non-trigger objects per 5 s window:
  - Society: about 1,000–1,900 → 6,819 at the 3x ship (~15.6 s)
  - Green Bullet: 8,638 → 17,658 (~40 s)
  - Thinking Space II: 11,135 → 28,649 (~55 s)
  - GRIEF: 5,129 → 12,214 (~120 s)

## Shaders

- Society and Green Bullet use many short shader moments: edit colour, glitch, chromatic, motion/radial blur,
  lens circle.
- **Antarctic Lights, Thinking Space II, Flamewall and GRIEF use essentially none.** Shaders are optional. A level can
  reach the top of the list without them.

## Song handling

| Level | What it does with the song |
|---|---|
| Antarctic Lights | Start offset **61.5 s**, fade in |
| Thinking Space II | Start offset **117 s**, fade in |
| Artemis 13 | Start offset 6 s, fade in |
| GRIEF | **Song triggers** jump the song forward mid-level: about 49.4 s, 73.5 s and 129.2 s into the track, at level times of roughly 48 s, 71 s and 128 s. The extra copies look like practice-mode/restart safety. |
| Flamewall | An Edit Song trigger stops the default song at the start, a Song trigger starts it, and at ~175 s a **second song is layered on channel 1** at volume 2 |

## Gamemode/speed pacing (why these aren't our gameplay template)

- Top-list levels pile portal events on top of each other. Artemis 13 has 179 portal events (gamemode, speed,
  gravity, size, dual, mirror, teleport) and 34 gamemode changes in ~70 s. The median gap between gamemode changes is
  0.6 s. Antarctic Lights has 155 portal events in ~58 s.
- For AREDL ~#600 that's far too dense. See `aredl-600.md`.

## Custom-art construction (the 3 most hand-built references)

These numbers count only deco objects, leaving out triggers and gameplay objects.

| Level | Off the 7.5-unit grid | Rotated off 90° | Warped |
|---|---:|---:|---:|
| Thinking Space II | 99.6% | 53% | 0.3% |
| GRIEF | 90% | 42% | 1% |
| Society | 87% | 30% | 15% |
| ORBIT | 86% | 21% | 13% |
| Flamewall | 94% | 21% | 0% |
| Artemis 13 | 91% | 12% | 7% |
| Green Bullet | 83% | 10% | 7% |
| Antarctic Lights | 57% | 24% | 0.6% |

What their non-glow shapes are built from:

**Thinking Space II:**
- Jagged Rocks outlines (1679/1666): median scale 1.8×, 79–97% rotated, 69–76% HSV-shifted.
- Colored Inner Square (211): about 1.8×, 42% rotated.
- 3DL lines (507/508), mostly rotated.
- Large Cloud (130), industrial blocks, dot clusters, drips, chains, grass connectors.
- The detail objects are repurposed for their shape: scaled, rotated, shaded with HSV.

**GRIEF:**
- Black pit spikes (1715): 84% rotated, used as shape pieces.
- 3DL lines; Colored Inner Square.
- Fire animation at 0.25× (84% HSV-shifted).
- Decorative spikes, wide slopes (688/694), tiny triangles, grass toppers, bricks.

**Society:**
- **3DL Half Top Middle (508) ×27.9k and 3DL Top Middle (507) ×11.7k**, 72–79% rotated. Line art is the
  backbone.
- Colored Inner Square ×12.5k.
- Beveled bricks, sixteenth blocks, slopes (693/698), wooden planks, pixel-art objects, text objects.

## Primitive sizes (measured from edge-to-edge tiling across all 8 levels)

| ID | Object | Pitch (units) | Notes |
|---:|---|---|---|
| 211 | Colored Inner Square | 30 × 30 (13k+ gaps of 30 on each axis) | The standard fill block |
| 207 | Colored Square | 30 × 30 | |
| 916 | Quarter Colored Block | 15 × 15 | |
| 917 | One-Sixteenth Colored Block | 7.5 × 7.5 | |
| 220 | Colored Small Square | ~15 | |
| 693 | Decorative Colored Slope | 30 × 30 triangle | |
| 507 | 3DL Top Middle | 30 long | Thickness not measurable from placements |
| 468 | Outline Top | 30 long | |
| 1753 | Thin Line | 30 long | |

Tiling pitch proves the *cell* size, not the exact painted edge or line thickness. Before the art pipeline converts
vector shapes into objects, a **calibration test level** places each primitive at known transforms over a grid. You
screenshot it in-game and I fit the exact sprite bounds and pivots. That's the first step of Phase 4 (rule C10).
