"""Reusable hazard styles, applied automatically to every layout hazard in a range.

Spike geometry (base offset from object centre, tip offset, half width),
inferred from how the layout butts spikes together (full spikes base-to-base
30 apart, small spikes 18 apart, half spikes 6 units off the block face):
  216/8 full spike : base -15, tip +15
  218 small spike  : base -9,  tip +6
  217 half spike   : base -6,  tip +8
Details never change a hazard's silhouette:
  - Colored spikes (216/217/218, one flat colour) get a dark obsidian core
    drawn on top at ~2/3 size, so the layout colour remains as a molten rim.
  - Every spike gets a molten vein, a white-hot tip and an ember glow at the
    base; where two spikes meet base to base (diamonds) the seam glows.
  - Saws get a molten ring, a dark hub and a hot bolt over the blade.
"""
import math

from gdobj import B1, T2

SPIKES = {  # id: (base_offset, tip_offset, half_width)
    "216": (15.0, 15.0, 13.0), "8": (15.0, 15.0, 13.0), "9": (15.0, 15.0, 13.0),
    "218": (9.0, 6.0, 12.0), "217": (6.0, 8.0, 6.0),
}
COLORED = {"216": 0.64, "218": 0.6, "217": 0.55}     # core scale
SAWS = {"1735": 38.0, "187": 36.0, "680": 24.0, "679": 32.0, "1709": 38.0}


def spike_dir(o):
    r = math.radians(float(o.get("6", 0)))
    dy = -1.0 if o.get("5") == "1" else 1.0
    # GD rotation is clockwise-positive: local (0, dy) rotated clockwise by r
    return (dy * math.sin(r), dy * math.cos(r))


def spike_geom(o):
    b, t, w = SPIKES[o["1"]]
    s = float(o.get("128", o.get("32", 1)))
    x, y = float(o["2"]), float(o["3"])
    d = spike_dir(o)
    base = (x - d[0] * b * s, y - d[1] * b * s)
    tip = (x + d[0] * t * s, y + d[1] * t * s)
    return base, tip, d, w * s


def _lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def spike_details(sc, layout, x0, x1, groups=(), tip_group=None, core=True):
    spikes = [o for o in layout if o.get("1") in SPIKES and x0 <= float(o["2"]) <= x1]
    geoms = [(o, *spike_geom(o)) for o in spikes]
    paired = set()
    tg = (tip_group,) if tip_group else ()
    # diamonds: two spikes whose bases meet with opposite directions
    for i, (oi, bi, ti, di, wi) in enumerate(geoms):
        for j in range(i + 1, len(geoms)):
            oj, bj, tj, dj, wj = geoms[j]
            if di[0] * dj[0] + di[1] * dj[1] < -0.95 and math.hypot(bi[0] - bj[0], bi[1] - bj[1]) < 4:
                paired.update((i, j))
                c = ((bi[0] + bj[0]) / 2, (bi[1] + bj[1]) / 2)
                px, py = -di[1], di[0]
                w = min(wi, wj) * 0.7
                a, b = (c[0] - px * w, c[1] - py * w), (c[0] + px * w, c[1] + py * w)
                sc.seg(a, b, 1.6, sc.ch("crack"), T2, 6, groups, "rim")
                sc.seg(_lerp(a, c, 0.5), _lerp(b, c, 0.5), 0.8, sc.ch("crack_core"), T2, 7, groups,
                       "rim")
                sc.glow(c[0], c[1], 40, sc.ch("glow_hot"), B1, -1, groups, "glow", kind="S")
                sc.glow(c[0], c[1], 10, sc.ch("tip_glow"), T2, 4, tuple(groups) + tg, "glow",
                        kind="S")
    for i, (o, base, tip, d, w) in enumerate(geoms):
        L = math.hypot(tip[0] - base[0], tip[1] - base[1])
        px, py = -d[1], d[0]
        a1, a2 = (base[0] + px * w, base[1] + py * w), (base[0] - px * w, base[1] - py * w)
        if core and o["1"] in COLORED and str(o.get("21", "")) not in ("", "0"):
            s = COLORED[o["1"]]
            g = ((a1[0] + a2[0] + tip[0]) / 3, (a1[1] + a2[1] + tip[1]) / 3)
            c1, c2, ct = _lerp(g, a1, s), _lerp(g, a2, s), _lerp(g, tip, s)
            sc.gtri(c1, c2, ct, sc.ch("spike_core"), "t1", groups)
            cb = _lerp(g, base, s)
            vb, vt = _lerp(cb, ct, 0.12), _lerp(cb, ct, 0.86)
        else:
            vb, vt = _lerp(base, tip, 0.1), _lerp(base, tip, 0.86)
        if L > 10:
            sc.seg(vb, vt, 1.1 if L > 20 else 0.8, sc.ch("spike_vein"), T2, 5, groups, "rim")
            sc.seg(vb, _lerp(vb, vt, 0.5), 0.6, sc.ch("crack_core"), T2, 6, groups, "rim")
        sc.glow(tip[0] - d[0] * 2.0, tip[1] - d[1] * 2.0, 12 if L > 20 else 8, sc.ch("tip_glow"), T2,
                3, tuple(groups) + tg, "glow", kind="S")
        if i not in paired:
            sc.glow(base[0], base[1], 2.0 * w, sc.ch("glow_o"), B1, -2, groups, "glow", kind="S")
    return len(geoms), len(paired) // 2


def saw_details(sc, layout, x0, x1, groups=()):
    done = set()
    out = []
    for o in layout:
        if o.get("1") not in SAWS:
            continue
        x, y = float(o["2"]), float(o["3"])
        if not (x0 <= x <= x1) or (x, y) in done:
            continue
        done.add((x, y))
        R = SAWS[o["1"]] * float(o.get("128", o.get("32", 1)))
        # static housing over the spinning blade: molten ring + dark hub + hot bolt
        n = 14
        ring = [(x + 0.46 * R * math.cos(2 * math.pi * k / n), y + 0.46 * R * math.sin(2 * math.pi * k / n))
                for k in range(n)]
        sc.polyline(ring, 1.3, sc.ch("crack"), T2, 5, groups, "rim", closed=True)
        sc.glow(x, y, 0.62 * R, sc.ch("orb_back"), T2, 4, groups, "glow", kind="S")
        sc.glow(x, y, 7, sc.ch("tip_glow"), T2, 6, groups, "glow", kind="S")
        out.append((x, y, R))
    return out
