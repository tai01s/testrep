"""Gameplay geometry on a 30-unit cell grid.

Everything the player can collide with goes through `World`, which keeps
two views of it in sync:
  * the GD objects that get written to the level, and
  * exact collision shapes (rects / triangles) used by `sim.py` to search
    for a winning input path before the level is exported.

Slopes: every GD slope sprite in its default orientation is a right
triangle with the solid half at the bottom-right (a ramp rising to the
right). Instead of hard-coding flip/rotation tables, `slope_transform`
searches flips and 90-degree rotations for the one that maps that base
triangle onto the triangle we want.
"""

import math
from gdlevel import B4, B3, B2, B1, T1, T2

CELL = 30.0

# Object IDs (verified against gd-info-explorer objects.csv).
SQUARE = 211          # Colored Inner Square (solid, single colour)
SLOPE = 1906          # Colored Gradient Slope (solid)
WIDE_SLOPE = 1907     # Colored Gradient Wide Slope (solid)
DECO_SLOPE = 693      # Decorative Colored Slope
DECO_WIDE_SLOPE = 694
OUTLINE_TOP = 468     # Outline Top
OUTLINE_SLOPE = 1338
OUTLINE_WIDE_SLOPE = 1339
GLOW_STRAIGHT = 1011  # Straight Large Glow
GLOW_SLOPE = 1762     # Large One Block Slope Glow
GLOW_WIDE_SLOPE = 1763
SPIKE = 8
# Gameplay-test build uses the default block set, which is solid for sure.
TEST_SQUARE = 1       # Black Gradient Square (the default block)
TEST_SLOPE = 371      # Black Gradient Slope
TEST_WIDE_SLOPE = 372 # Black Gradient Wide Slope
SMALL_GLOW = 1887
MED_GLOW = 1886

ORB_IDS = {"yellow": 36, "blue": 84, "pink": 141}
PAD_IDS = {"yellow": 35, "blue": 67, "pink": 140}
MODE_PORTAL = {"cube": 12, "ship": 13, "ball": 47, "wave": 660, "spider": 1331}
GRAV_PORTAL = {"flip": 11, "normal": 10}
SIZE_PORTAL = {"mini": 101, "normal": 99}

# Colour channels shared with decor.py
CH_FILL, CH_INNER, CH_EDGE, CH_LINE = 1, 2, 3, 4
CH_SPIKE, CH_SPIKE_GLOW, CH_ORB_GLOW = 5, 6, 13


def _rot(p, deg):
    """GD rotation: positive degrees are clockwise."""
    a = math.radians(deg)
    x, y = p
    return (x * math.cos(a) + y * math.sin(a), -x * math.sin(a) + y * math.cos(a))


def _transform(pts, fx, fy, deg):
    out = []
    for x, y in pts:
        if fx:
            x = -x
        if fy:
            y = -y
        x, y = _rot((x, y), deg)
        out.append((round(x, 4), round(y, 4)))
    return out


def _same_tri(a, b):
    return sorted(a) == sorted(b)


def slope_transform(base_w, base_h, tri_local):
    """Find (flip_x, flip_y, rotation) mapping the base ramp onto tri_local.

    base ramp: bottom-left -> bottom-right -> top-right, centred on origin.
    tri_local: target triangle vertices relative to the object centre.
    """
    w, h = base_w / 2.0, base_h / 2.0
    base = [(-w, -h), (w, -h), (w, h)]
    target = [(round(x, 4), round(y, 4)) for x, y in tri_local]
    for deg in (0, 90, 180, 270):
        for fx in (0, 1):
            for fy in (0, 1):
                if _same_tri(_transform(base, fx, fy, deg), target):
                    return fx, fy, deg
    raise ValueError(f"no transform for triangle {tri_local}")


class World:
    def __init__(self, level):
        self.L = level
        self.full = set()          # (i, j) full solid cells
        self.slopes = []           # dicts: tri (world pts), cells, kind
        self.partial = {}          # (i, j) -> slope index
        self.hazards = []          # (x0, y0, x1, y1)
        self.orbs = []             # dicts: kind, x, y
        self.portals = []          # dicts: kind, value, x, y
        self.deco_extra = []
        self.minimal = True        # gameplay-only build: no glow/deco layers

    # ------------------------------------------------------------------ cells
    def block(self, i, j):
        self.full.add((i, j))

    def fill(self, i0, i1, j0, j1):
        """Fill cells i0 <= i < i1, j0 <= j < j1."""
        for i in range(i0, i1):
            for j in range(j0, j1):
                self.full.add((i, j))

    def clear(self, i0, i1, j0, j1):
        for i in range(i0, i1):
            for j in range(j0, j1):
                self.full.discard((i, j))

    def slope(self, tri_cells):
        """Add a solid triangle given in cell coordinates (corner points)."""
        xs = [p[0] for p in tri_cells]
        ys = [p[1] for p in tri_cells]
        x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
        w, h = x1 - x0, y1 - y0
        cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
        local = [((x - cx) * CELL, (y - cy) * CELL) for x, y in tri_cells]
        if (w, h) == (1, 1):
            kind, bw, bh = "1x1", CELL, CELL
        elif {w, h} == {1, 2}:
            kind, bw, bh = "2x1", 2 * CELL, CELL
        else:
            raise ValueError("unsupported slope size")
        fx, fy, deg = slope_transform(bw, bh, local)
        idx = len(self.slopes)
        cells = [(i, j) for i in range(int(x0), int(x1)) for j in range(int(y0), int(y1))]
        self.slopes.append({
            "tri": [(x * CELL, y * CELL) for x, y in tri_cells],
            "center": (cx * CELL, cy * CELL), "kind": kind,
            "fx": fx, "fy": fy, "rot": deg, "cells": cells,
        })
        for c in cells:
            self.partial[c] = idx

    # --------------------------------------------------------------- hazards
    def spike(self, i, j, down=False, glow=True):
        """Spike sitting in cell (i, j); down=True hangs from a ceiling."""
        x, y = i * CELL + 15, j * CELL + 15
        self.L.add(SPIKE, x, y, flip_y=1 if down else None, color=CH_SPIKE,
                   color2=CH_LINE, z=B1, zorder=2)
        if glow and not self.minimal:
            self.L.add(SMALL_GLOW, x, y + (4 if down else -4), color=CH_SPIKE_GLOW,
                       z=B2, scale=1.5)
        # GD's spike hitbox is ~6x12 in the middle of the cell; use a
        # padded box so the solver keeps a safety margin.
        base = j * CELL
        if down:
            self.hazards.append((x - 5, base + 6, x + 5, base + 28))
        else:
            self.hazards.append((x - 5, base + 2, x + 5, base + 24))

    def spikes(self, i0, n, j, down=False):
        for k in range(n):
            self.spike(i0 + k, j, down)

    # ---------------------------------------------------------- interactives
    def orb(self, kind, x, y):
        self.L.add(ORB_IDS[kind], x, y, z=T1)
        if not self.minimal:
            self.L.add(MED_GLOW, x, y, color=CH_ORB_GLOW, z=B1, scale=2.2)
        self.orbs.append({"kind": kind, "x": x, "y": y})

    def portal(self, kind, value, x, y):
        if kind == "mode":
            oid = MODE_PORTAL[value]
        elif kind == "speed":
            from gdlevel import SPEED_PORTAL
            oid = SPEED_PORTAL[value]
        elif kind == "gravity":
            oid = GRAV_PORTAL[value]
        elif kind == "size":
            oid = SIZE_PORTAL[value]
        else:
            raise ValueError(kind)
        self.L.add(oid, x, y, checked=1, z=T1)
        self.portals.append({"kind": kind, "value": value, "x": x, "y": y})

    # ------------------------------------------------------------- corridors
    def wall(self, i0, segs, below, top=11, bottom=0):
        """Build a floor (below=True) or ceiling wall from line segments.

        segs: [(length_in_columns, row_start, row_end), ...] laid end to end
        from column i0. Within a segment the line is straight; a segment may
        be flat, 45 degrees (|dy| == length), steep (|dy| == 2 * length) or
        wide (|dy| == length / 2, even length). Consecutive segments may
        start at a different row, which makes a vertical step.
        Returns the column after the last segment.
        """
        c = i0
        for n, ya, yb in segs:
            d = yb - ya
            if d == 0:
                for k in range(n):
                    self._column_fill(c + k, ya, ya, below, top, bottom)
            elif abs(d) * 2 == n:
                step = d / (n / 2)
                for k in range(0, n, 2):
                    a = ya + step * (k // 2)
                    b = a + step
                    self._column_fill(c + k, min(a, b), max(a, b), below, top, bottom)
                    self._column_fill(c + k + 1, min(a, b), max(a, b), below, top, bottom)
                    self._ramp(c + k, c + k + 2, a, b, below)
            elif abs(d) == n or abs(d) == 2 * n:
                step = d / n
                for k in range(n):
                    a = ya + step * k
                    b = a + step
                    lo, hi = min(a, b), max(a, b)
                    self._column_fill(c + k, lo, hi, below, top, bottom)
                    if below and hi <= bottom:
                        continue  # line is under the GD ground
                    if not below and lo >= top:
                        continue  # line is above the top of the wall
                    assert lo >= bottom and hi <= top, f"ramp clipped at column {c + k}"
                    self._ramp(c + k, c + k + 1, a, b, below)
            else:
                raise ValueError(f"bad wall segment {(n, ya, yb)}")
            c += n
        return c

    def _column_fill(self, i, lo, hi, below, top, bottom=0):
        if below:
            for j in range(bottom, int(lo)):
                self.full.add((i, j))
        else:
            for j in range(int(math.ceil(hi)), top):
                self.full.add((i, j))

    def _ramp(self, xa, xb, ya, yb, below):
        """Triangle between the wall line (xa,ya)-(xb,yb) and the solid side."""
        lo, hi = min(ya, yb), max(ya, yb)
        if below:
            # solid below the line inside the box [xa,xb] x [lo,hi]
            corner = (xb, lo) if yb > ya else (xa, lo)
        else:
            corner = (xa, hi) if yb > ya else (xb, hi)
        self.slope([(xa, ya), (xb, yb), corner])

    # ------------------------------------------------------------ rendering
    def side_solid(self, cell, side):
        """True if `side` (n/s/e/w) of `cell` is fully solid."""
        if cell in self.full:
            return True
        idx = self.partial.get(cell)
        if idx is None:
            return False
        tri = self.slopes[idx]["tri"]
        i, j = cell
        x0, y0, x1, y1 = i * CELL, j * CELL, (i + 1) * CELL, (j + 1) * CELL
        pts = {
            "n": [(x0 + f * CELL, y1 - 0.5) for f in (0.1, 0.5, 0.9)],
            "s": [(x0 + f * CELL, y0 + 0.5) for f in (0.1, 0.5, 0.9)],
            "e": [(x1 - 0.5, y0 + f * CELL) for f in (0.1, 0.5, 0.9)],
            "w": [(x0 + 0.5, y0 + f * CELL) for f in (0.1, 0.5, 0.9)],
        }[side]
        return all(point_in_tri(p, tri) for p in pts)

    def render(self, groups=None):
        L = self.L
        nbr = {"n": (0, 1, "s"), "s": (0, -1, "n"), "e": (1, 0, "w"), "w": (-1, 0, "e")}
        # outline orientation: Outline Top drawn on top edge, rotate CW for others
        rot = {"n": 0, "e": 90, "s": 180, "w": 270}
        boundary = set()
        for (i, j) in self.full:
            exposed = []
            for side, (di, dj, opp) in nbr.items():
                n = (i + di, j + dj)
                if n[1] < 0:
                    continue  # GD ground below
                if not self.side_solid(n, opp):
                    exposed.append(side)
            if exposed:
                boundary.add((i, j))
            x, y = i * CELL + 15, j * CELL + 15
            for side in exposed:
                if self.minimal:
                    break
                L.add(OUTLINE_TOP, x, y, rot=rot[side] or None, color=CH_LINE, z=T1,
                      zorder=3, no_touch=1, groups=groups)
                # inner edge glow: glow sprite is bright at its bottom edge,
                # so turn it to face the exposed side, inside the block.
                L.add(GLOW_STRAIGHT, x, y, rot=(rot[side] + 180) % 360 or None,
                      color=CH_EDGE, z=T1, zorder=1, no_touch=1, groups=groups)
        # solids: boundary cells individually, interior merged into columns
        cols = {}
        for (i, j) in self.full:
            if (i, j) in boundary:
                if self.minimal:
                    L.add(TEST_SQUARE, i * CELL + 15, j * CELL + 15, color=CH_FILL,
                          color2=CH_LINE, groups=groups)
                else:
                    L.add(SQUARE, i * CELL + 15, j * CELL + 15, color=CH_FILL, groups=groups)
            else:
                cols.setdefault(i, []).append(j)
        for i, js in cols.items():
            js.sort()
            runs, start, prev = [], js[0], js[0]
            for j in js[1:]:
                if j != prev + 1:
                    runs.append((start, prev))
                    start = j
                prev = j
            runs.append((start, prev))
            for a, b in runs:
                n = b - a + 1
                L.add(SQUARE, i * CELL + 15, (a + n / 2.0) * CELL, color=CH_FILL,
                      sy=float(n), no_touch=1, groups=groups)
        # slopes
        for s in self.slopes:
            cx, cy = s["center"]
            wide = s["kind"] == "2x1"
            kw = dict(flip_x=s["fx"] or None, flip_y=s["fy"] or None, rot=s["rot"] or None)
            if self.minimal:
                L.add(TEST_WIDE_SLOPE if wide else TEST_SLOPE, cx, cy, color=CH_FILL,
                      color2=CH_LINE, groups=groups, **kw)
                continue
            L.add(WIDE_SLOPE if wide else SLOPE, cx, cy, color=CH_FILL, groups=groups, **kw)
            L.add(DECO_WIDE_SLOPE if wide else DECO_SLOPE, cx, cy, color=CH_FILL, z=B1,
                  zorder=1, groups=groups, **kw)
            L.add(OUTLINE_WIDE_SLOPE if wide else OUTLINE_SLOPE, cx, cy, color=CH_LINE,
                  z=T1, zorder=3, no_touch=1, groups=groups, **kw)
            L.add(GLOW_WIDE_SLOPE if wide else GLOW_SLOPE, cx, cy, color=CH_EDGE, z=T1,
                  zorder=1, no_touch=1, groups=groups, **kw)
        return boundary

    # ------------------------------------------------------- collision export
    def shapes(self):
        rects = [(i * CELL, j * CELL, (i + 1) * CELL, (j + 1) * CELL) for (i, j) in self.full]
        tris = [s["tri"] for s in self.slopes]
        return rects, tris


def point_in_tri(p, tri):
    (x, y), (a, b, c) = p, tri

    def sgn(p1, p2, p3):
        return (p1[0] - p3[0]) * (p2[1] - p3[1]) - (p2[0] - p3[0]) * (p1[1] - p3[1])

    d1, d2, d3 = sgn((x, y), a, b), sgn((x, y), b, c), sgn((x, y), c, a)
    neg = d1 < 0 or d2 < 0 or d3 < 0
    pos = d1 > 0 or d2 > 0 or d3 > 0
    return not (neg and pos)
