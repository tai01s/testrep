# .gmd analysis tools

These decode GDShare `.gmd` exports and measure how a level is built.

**Requirements:**
- Python 3 and Pillow.
- The object-name table from [gd-info-explorer](https://github.com/flowvix/gd-info-explorer):

```
git clone --depth 1 https://github.com/flowvix/gd-info-explorer ../ref/gd-info-explorer
# or point GD_OBJECTS_CSV at its src/lib/objects.csv
```

`../ref/` is git-ignored.

| Script | Usage | Output |
|---|---|---|
| `gmd.py` | library | Loads a `.gmd`: header (`kA*`), colour channels (`kS38`), objects. Holds the speed constants (units/s) and the portal, orb, pad and Z-layer tables. |
| `analyze.py` | `python3 analyze.py LEVEL.gmd [...]` | Timeline of gamemode/speed/size/gravity portals in song seconds; orb/pad/trigger counts; top objects; Z-layer use; colour channels; BG/ground colour triggers; HSV/scale/group shares; density per 5 s |
| `deep.py` | `python3 deep.py LEVEL.gmd [...]` | Z-layer use per role (hazard, fill, line, glow, particle, interactive); pulse-trigger timing gaps |
| `render.py` / `shots.py` | `python3 shots.py LEVEL.gmd TAG OUTDIR t1,t2,...` | Rough screenshot sheets at given song times |

**Notes:**
- Run them with `python3 -I` when the input file isn't yours.
- The renderer draws each object as a coloured primitive at its starting position. It applies position-based
  colour/alpha/toggle triggers, but not moves.
- It's a composition and colour map, not a real screenshot. It has no game sprites.
- Time estimates come from speed portals. Teleports, time warp and arrow triggers are ignored.
