# Fogbound (gameplay build)

A Geometry Dash 2.2 level, planned as an Extreme Demon sequel to *Moment* (icedcave) and *Gravity* (Amza & Slayer).

- **Song:** Fog by HyperCubeRecords, Newgrounds ID `1101957`
- **File:** [`Fogbound.gmd`](Fogbound.gmd)
- **Length:** about 62 s

**This is the gameplay-only build.** It has default blocks and colours and no decoration. Decoration comes after the gameplay is playtested and signed off.

## Importing

Use a `.gmd` importer, for example the **GDShare** mod for Geode (Import in *My Levels*), then download the song from the level page.

## Layout

| Section | Starts | Mode | Speed |
| --- | --- | --- | --- |
| intro | 0:00 | cube | 2x |
| cube-3x | 0:06 | cube (blue orbs, gravity portals) | 3x |
| ship | 0:15 | ship (wide slopes, 2-block straight fly) | 2x |
| wave | 0:23 | wave (2- and 4-block gaps, spam bursts) | 3x |
| ball | 0:28 | ball | 3x |
| spider | 0:34 | spider | 3x |
| drop | 0:40 | wave, then a mini-wave burst | 4x then 3x |
| ship-3x | 0:46 | ship | 3x |
| cube-final | 0:52 | cube (orb chain, blue-orb ceiling run) | 3x |
| outro | 0:59 | cube | 1x |

Section start times are guesses because I couldn't listen to the song, so the drop and transitions are not synced to the music yet. `preview/strip_*.png` shows the layout: purple is solid, pink is spikes, rings are orbs and green boxes are portals.

## How it's built

`python3 build.py` regenerates the level:

- `layout.py` places the gameplay on a 30-unit grid.
- `world.py` turns it into GD objects. It works out flips and rotations for each slope.
- `sim.py` checks the result before anything is written. It approximates GD physics and searches every input sequence, tick by tick, to make sure at least one path reaches the end. It uses bigger hitboxes than the game, padded spike boxes, and counts touching any solid as death. The search runs with five physics variants (stronger or weaker jumps, heavier or lighter gravity, ship acceleration and so on). The current layout passes all five.

That check is an approximation of the game, not the game itself, so the level still needs a real playtest. Its inputs are frame-perfect, so it shows that a path exists, not that the level is humanly fair.

Options: `--fast` skips the solver, `--preview` draws the PNGs, `--from-col N --to-col M` checks one stretch.
