"""Build Fogbound.gmd.

    python3 build.py            # build the level, run the solver on every variant
    python3 build.py --fast     # build only, skip the solver
    python3 build.py --preview  # also draw preview PNGs (needs Pillow)
"""

import argparse
import os
import sys
import time

from gdlevel import Level, SPEED_START_KEY
from layout import Layout
from world import World
import sim

HERE = os.path.dirname(os.path.abspath(__file__))
SONG_ID = 1101957  # "Fog" by HyperCubeRecords on Newgrounds
NAME = "Fogbound"
DESCRIPTION = ("A Moment sequel. Follow the petals through the fog. "
               "Song: Fog by HyperCubeRecords. Extreme Demon.")


def level_time(timeline, x_end):
    t, segs = 0.0, sorted(timeline)
    for k, (x, v) in enumerate(segs):
        nx = segs[k + 1][0] if k + 1 < len(segs) else x_end
        if x < x_end and nx > x:
            t += (min(nx, x_end) - x) / v
    return t


def build_layout():
    L = Level(NAME)
    w = World(L)
    lay = Layout(w, start_speed=2)
    i = 0
    i = lay.intro(i)
    i = lay.cube_fast(i)
    i = lay.ship(i)
    i, row = lay.wave(i)
    i = lay.ball(i, row_in=row)
    i = lay.spider(i)
    i, row = lay.drop(i)
    i = lay.ship_fast(i, row_in=row)
    i = lay.cube_final(i)
    i = lay.outro(i)
    lay.end_col = i
    return L, w, lay


def solve(w, lay, variants, from_col=0, to_col=None):
    ok_all = True
    x_end = (to_col if to_col else lay.end_col) * 30.0 - 60
    for name in variants:
        t0 = time.time()
        s = sim.Sim(w, lay.timeline, sim.VARIANTS[name], from_col * 30.0,
                    (15.0, 0.0, 1, True, "cube", False, -1, 0), x_end)
        ok, x, info = s.run()
        sec = next((d["name"] for d in lay.sections if d["i0"] * 30 <= x < d["i1"] * 30), "?")
        status = "PASS" if ok else f"FAIL at x={x:.0f} (col {x / 30:.1f}, {sec}) last ys={info}"
        print(f"  [{name:9s}] {status}  ({time.time() - t0:.1f}s)")
        ok_all &= ok
    return ok_all


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fast", action="store_true")
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--variants", default=",".join(sim.VARIANTS))
    ap.add_argument("--from-col", type=int, default=0, help="start the solver here (cube on the ground)")
    ap.add_argument("--to-col", type=int, default=None)
    args = ap.parse_args()

    L, w, lay = build_layout()
    for d in lay.sections:
        print(f"  {d['name']:11s} cols {d['i0']:4d}-{d['i1']:4d}  {d['mode']:6s} {d['speed']}x")
    if not args.fast:
        print("solver:")
        if not solve(w, lay, args.variants.split(","), args.from_col, args.to_col):
            print("solver found an unbeatable section; not writing the level")
            sys.exit(1)
        if args.from_col or args.to_col:
            return

    w.render()
    L.start["kA4"] = SPEED_START_KEY[2]
    out = os.path.join(HERE, f"{NAME}.gmd")
    L.write_gmd(out, DESCRIPTION, SONG_ID)
    secs = level_time(lay.timeline, lay.end_col * 30.0)
    print(f"wrote {out}: {len(L.objects)} objects, {secs:.1f}s long")
    if args.preview:
        import preview
        preview.draw(L, w, lay, os.path.join(HERE, "preview"))


if __name__ == "__main__":
    main()
