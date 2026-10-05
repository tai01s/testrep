# In-game check (real GD) — Cerebral Cobweb HELL v1

Two files in `out/`:

- `Cerebral_Cobweb_hell_intro.gmd` — your level with the hell deco on the opening (layout untouched). Imports as **Cerebral Cobweb HELL v1**.
- `Cerebral_Cobweb_calibration.gmd` — a 92-object test level. Imports as **CC Deco Calibration**. It confirms the few GD conventions the deco depends on.

Import both the same way you exported them (GDShare / level import).

## A. Main level (about 2 minutes)

Play **from the very start**, not from a start position, up to about 25%. Pause (Esc) and screenshot at each of these points:

| # | When | What should be there |
|---|------|----------------------|
| 1 | First second | The camera rises from a lava sea (glowing line, embers drifting up). |
| 2 | On the first platform (~1–2%) | **Platform:** dark obsidian slab with orange edges, hanging stalactite underneath. **Roof:** dark rock, glowing underside, cracks going up. **Background:** burning web with a molten core top-right, dark spires. |
| 3 | Around the green orb (~7%) | Floating spikes glow red and hang from glowing threads. Rock pillars rise from the lava under the platforms. |
| 4 | ~9% (blue orb, 3.5 s) | A beat flash: the core flares, a light wave runs out along the web, the lava brightens. |
| 5 | ~10–14% (the platform that carries you) | The platform keeps its glow and leaves an ember trail as it dips and rises. A roof slab hangs above. |

Also note:

- **Embers:** do they rise (good) or fall (wrong direction)?
- **Rock shapes:** if they are missing completely, tell me (that means the gradient setup failed).
- **FPS:** turn on Show FPS and say if it drops noticeably compared with your layout.
- **After ~22%:** the deco is unfinished past this point and outlines turn back to white. That's expected for now.

## B. Calibration level (1 minute)

Open **CC Deco Calibration** in the editor with Preview Mode, Preview Particles and Preview Shaders on. Take one screenshot covering stations 1–6, then playtest once.

1. A white 30×30 square on the grey grid, and a thin red line exactly from one grid crossing to another.
2. A green triangle whose corners sit on the three small red squares.
3. Three orange glow circles. I need their size against the 30-unit grid.
4. Green square with a red line visible **on top** of it.
5. White particles **rise** from the red marker. Is the emitter about 3 grid squares wide?
6. On playtest, the blue square drifts across the screen slower than the grid.

Send the screenshots back. Anything that differs from this list, I fix in the generator and rebuild.
