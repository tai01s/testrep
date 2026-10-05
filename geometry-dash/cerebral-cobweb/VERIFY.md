# In-game check (real GD) — Cerebral Cobweb HELL v2

Two files in `out/`:

- `Cerebral_Cobweb_hell_intro.gmd` — your level with the hell deco on the opening (layout untouched). Imports as **Cerebral Cobweb HELL v2**.
- `Cerebral_Cobweb_calibration.gmd` — a 92-object test level. Imports as **CC Deco Calibration**. It confirms the few GD conventions the deco depends on.

Import both the same way you exported them (GDShare / level import).

## A. Main level (about 2 minutes)

Play **from the very start**, not from a start position, up to about 25%. Pause (Esc) and screenshot at each of these points:

| # | When | What should be there |
|---|------|----------------------|
| 1 | First second | The camera rises from a lava sea: bubbles pop on the surface, embers rise, ash drifts down. A thin lavafall pours from the overhang on the left. |
| 2 | On the first platform (~1–2%) | **Platform:** brick slab with glowing mortar joints. The block on top has a molten rune. Underneath hangs a faceted stalactite, lit from below. **Roof:** faceted rock with branching molten cracks that have glowing nodes. **Background:** burning web with beads, a molten core top-right. |
| 3 | Around the green orb (~7%) | **Spikes:** dark obsidian core with an orange rim, a molten vein and a white-hot tip. The seam where two spikes meet glows. **Pillars:** rise from the lava with column-like facets. **Debris:** small rock chunks float and bob slowly. |
| 4 | ~9% (blue orb, 3.5 s) | A beat flash: the core flares, a light wave runs along the web, a wave runs through the roof cracks from left to right, and the spike tips flash. |
| 5 | ~10–14% (the platform that carries you) | The platform block keeps its glow and ember trail as it dips and rises. Overhead, the brick slab hangs from a faceted stem. |

Also note:

- **Rock facets:** do they look like sculpted rock (good), or like noisy random triangles (tell me)? A close-up screenshot of the roof helps most.
- **Spikes:** does the dark core sit inside each orange spike with an even rim? If it pokes out or looks shifted, send a close-up.
- **Embers / ash:** embers should rise and ash should fall. If either goes the wrong way, say which.
- **Rock shapes:** if they are missing completely, tell me (that means the gradient setup failed).
- **FPS:** v2 uses about 1,500 gradient triangles (v1: about 570). Turn on Show FPS and say if it drops compared with v1. I can scale the facet density down with one setting.
- **After ~22%:** the deco is unfinished past this point and outlines turn back to white. That's expected for now.

## B. Calibration level (1 minute) — only needed once

Open **CC Deco Calibration** in the editor with Preview Mode, Preview Particles and Preview Shaders on. Take one screenshot covering stations 1–6, then playtest once.

1. A white 30×30 square on the grey grid, and a thin red line exactly from one grid crossing to another.
2. A green triangle whose corners sit on the three small red squares.
3. Three orange glow circles. I need their size against the 30-unit grid.
4. Green square with a red line visible **on top** of it.
5. White particles **rise** from the red marker. Is the emitter about 3 grid squares wide?
6. On playtest, the blue square drifts across the screen slower than the grid.

Send the screenshots back. Anything that differs from this list, I fix in the generator and rebuild.
