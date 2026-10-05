"""Reusable rock / block styles (applied to every section of the level).

facet_fill    : fills a polygon with a conforming triangle mesh (mesh.py) and
                shades every facet like sculpted obsidian: facets close to a lit
                edge pick up lava light (more when they face it), the interior
                stays near-black. Facet size grows away from the lit edges, so
                detail sits where the light is (GDCS: details at edges/corners).
masonry_slab  : forged brickwork fitted exactly to an axis-aligned gameplay slab.
block_face    : a single gameplay cell: bevelled face + optional molten rune.
basalt_columns: columnar jointing on pillars that rise from the lava.
neural_crack  : branching molten crack with glowing nodes at the forks (the
                level's "cerebral" motif: rock veins grow like dendrites).

Layering contract (z layer / order):
  rock gradients     -> gradient layer b3 (renders above every B3 object)
  bricks/block faces -> B3 z-order 20-28 (above the mid-ground's B3 rims and the
                        lava body), kept outside rock polygons (never under a gradient)
  seams, rims, veins -> B2 (non-blending)  /  their glows -> B1 (blending)
"""
import math
import random

from gdobj import B1, B2, B3
from mesh import build_mesh

# 8 steps from shadow to lava-lit. The level BG is (8,2,6): unlit rock sits
# just below it, so silhouettes stay readable; lit facets stay well below the
# brightness of the gameplay outlines (255,96,32).
ROCK_SHADES = [(5, 1, 3), (9, 2, 5), (14, 3, 7), (20, 5, 9), (29, 7, 10), (41, 10, 11),
               (58, 14, 12), (80, 20, 14)]
# mid-ground: lower contrast, a little lighter and cooler (atmospheric perspective)
MID_SHADES = [(11, 3, 7), (14, 4, 8), (18, 5, 9), (23, 6, 10), (30, 8, 11), (40, 10, 12)]
# far: lighter still, very low contrast
FAR_SHADES = [(19, 5, 10), (22, 6, 11), (26, 7, 12), (31, 8, 13), (37, 10, 14)]


def shades(sc, name="rock", table=ROCK_SHADES):
    return [sc.chan(f"{name}{i}", c) for i, c in enumerate(table)]


def rock_palette(sc):
    return shades(sc, "rock", ROCK_SHADES)


# ------------------------------------------------------------- helpers
def _hash(ix, iy, seed):
    h = (ix * 374761393 + iy * 668265263 + seed * 982451653) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFF) / 65535.0


def noise(x, y, seed=0):
    """Smooth value noise in [0,1]."""
    ix, iy = math.floor(x), math.floor(y)
    fx, fy = x - ix, y - iy
    u, v = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    a, b = _hash(ix, iy, seed), _hash(ix + 1, iy, seed)
    c, d = _hash(ix, iy + 1, seed), _hash(ix + 1, iy + 1, seed)
    return a + (b - a) * u + (c - a) * v + (a - b - c + d) * u * v


def closest(p, a, b):
    (px, py), (ax, ay), (bx, by) = p, a, b
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L2))
    q = (ax + t * dx, ay + t * dy)
    return math.hypot(px - q[0], py - q[1]), q


def point_in_poly(p, poly):
    x, y = p
    inside = False
    n = len(poly)
    for i in range(n):
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % n]
        if (y1 > y) != (y2 > y):
            if x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
                inside = not inside
    return inside


# ------------------------------------------------------------ facets
def facet_fill(sc, poly, layer="b3", groups=(), lit_edges=(), near=40.0, growth=0.65, far=260.0,
               lit_range=110.0, seed=0, palette=None, ambient=0.6, gain=(4.2, 2.6), jitter=0.35,
               coarse=None, max_tris=1500, aniso=None):
    """Fill `poly` with shaded facets.

    lit_edges: segments (a, b) or (a, b, weight) that receive light; a larger
               weight reaches further.
    coarse(p): optional multiplier (>1) for facet size where the rock is rarely
               on screen.
    aniso    : (sx, sy) stretches the facets, e.g. (1, 2.5) gives tall
               column-like facets (basalt) - the mesh is built in a squashed space.
    Returns the triangles."""
    rng = random.Random(seed)
    pal = palette or rock_palette(sc)
    edges = [(e[0], e[1], e[2] if len(e) > 2 else 1.0) for e in lit_edges]

    def lit_info(p):
        best, q = 1e9, None
        for a, b, w in edges:
            d, cp = closest(p, a, b)
            d /= w
            if d < best:
                best, q = d, cp
        return best, q

    def size(p):
        d, _ = lit_info(p)
        s = near + growth * min(d, 1e5)
        if coarse is not None:
            s *= coarse(p)
        return min(far, s)

    if aniso:
        ax, ay = aniso
        m = build_mesh([(x / ax, y / ay) for x, y in poly],
                       lambda q: size((q[0] * ax, q[1] * ay)) / ax, rng, jitter=0.18,
                       max_tris=max_tris)
        tris = [tuple((x * ax, y * ay) for x, y in t) for t in m.triangles()]
    else:
        m = build_mesh(poly, size, rng, jitter=0.18, max_tris=max_tris)
        tris = m.triangles()
    for t in tris:
        c = ((t[0][0] + t[1][0] + t[2][0]) / 3, (t[0][1] + t[1][1] + t[2][1]) / 3)
        d, q = lit_info(c)
        lit = max(0.0, 1.0 - d / lit_range) ** 1.4
        # pseudo surface normal from a smooth field -> neighbouring facets form planes
        theta = 4 * math.pi * noise(c[0] / 120.0, c[1] / 120.0, seed) + rng.gauss(0, 0.45)
        facing = 0.0 if q is None else math.cos(theta - math.atan2(q[1] - c[1], q[0] - c[0]))
        amb = ambient + 0.9 * (noise(c[0] / 200.0 + 7.3, c[1] / 200.0 - 2.1, seed + 1) - 0.5)
        v = amb + lit * (gain[0] + gain[1] * facing) + rng.uniform(-jitter, jitter)
        idx = int(max(0, min(len(pal) - 1, round(v))))
        sc.gtri(t[0], t[1], t[2], pal[idx], layer, groups)
    return tris


# ------------------------------------------------------------ cracks
def neural_crack(sc, rng, origin, direction, length, groups=(), z=B2, inside=None, depth=0,
                 thick=2.0, nodes=True, layer="rim"):
    """Dendrite-like molten crack: wanders, forks, and lights a small node at
    each fork. inside(p) keeps it in its rock (it stops at the border)."""
    pts = [origin]
    ang = direction
    n = max(2, int(length / 11))
    for _ in range(n):
        ang += rng.uniform(-20, 20)
        ang = direction + max(-38, min(38, ang - direction))
        p = pts[-1]
        step = length / n
        q = (p[0] + step * math.cos(math.radians(ang)), p[1] + step * math.sin(math.radians(ang)))
        if inside is not None and not inside(q):
            break
        pts.append(q)
    if len(pts) < 2:
        return pts
    sc.polyline(pts, thick, sc.ch("crack"), z, -4, groups, layer)
    if depth == 0:
        sc.polyline(pts[:max(2, len(pts) // 2 + 1)], thick * 0.42, sc.ch("crack_core"), z, -3,
                    groups, layer)
    if depth < 2 and len(pts) > 3:
        for _ in range(2 if depth == 0 else 1):
            k = rng.randrange(1, len(pts) - 1)
            p = pts[k]
            a = direction + rng.choice((-1, 1)) * rng.uniform(30, 65)
            sub = neural_crack(sc, rng, p, a, length * rng.uniform(0.3, 0.5), groups, z, inside,
                               depth + 1, thick * 0.65, nodes, layer)
            if nodes and len(sub) > 1:
                sc.glow(p[0], p[1], 14 if depth == 0 else 10, sc.ch("glow_hot"), B1, -3, groups,
                        "glow", kind="S", high_detail=True)
    return pts


# ------------------------------------------------------------ masonry
def masonry_slab(sc, x0, y0, x1, y1, rng, lit="top", groups=(), brick=(36, 64), courses=None,
                 face=(2, 3), rune_every=0):
    """Forged bricks for a gameplay slab [x0,x1]x[y0,y1] (exact cell bounds).
    lit = side facing the light ("top" or "bottom")."""
    pal = rock_palette(sc)
    h = y1 - y0
    courses = courses or max(1, int(round(h / 30.0)))
    chh = h / courses
    for k in range(courses):
        cy0, cy1 = y0 + k * chh, y0 + (k + 1) * chh
        cuts = [x0]
        x = x0 + (rng.uniform(brick[0] * 0.45, brick[1] * 0.75) if k % 2 else rng.uniform(*brick))
        while x < x1 - 16:
            cuts.append(x)
            x += rng.uniform(*brick)
        cuts.append(x1)
        for a, b in zip(cuts, cuts[1:]):
            w = b - a
            cx, cy = (a + b) / 2, (cy0 + cy1) / 2
            sc.rect(cx, cy, w, cy1 - cy0, pal[rng.choice(face)], B3, 20, groups=groups,
                    layer="rock")
            # warm bevel on the lit side, deep inner shadow on the other
            hy = cy1 - 1.7 if lit == "top" else cy0 + 1.7
            sy = cy0 + 2.6 if lit == "top" else cy1 - 2.6
            sc.rect(cx, hy, max(2.0, w - 4), 1.6, sc.ch("bevel_warm"), B3, 22, groups=groups,
                    layer="rock")
            sc.rect(cx, sy, max(2.0, w - 4), 3.0, pal[0], B3, 22, groups=groups, layer="rock")
            # chipped corner / hairline fracture on some bricks
            if w > 30 and rng.random() < 0.45:
                fx = rng.uniform(a + 8, b - 8)
                sc.seg((fx, cy0 + 3), (fx + rng.uniform(-6, 6), cy1 - 4), 1.0, pal[0], B3, 24,
                       groups, "rock")
        for x in cuts[1:-1]:
            sc.rect(x, (cy0 + cy1) / 2, 1.6, cy1 - cy0 - 1, sc.ch("mortar"), B3, 26,
                    groups=groups, layer="rim")
            gy = cy1 - 3 if lit == "top" else cy0 + 3
            sc.glow(x, gy, 14, sc.ch("seam_glow"), B2, -30, groups, "glow", kind="S",
                    high_detail=True)
        if k > 0:
            sc.rect((x0 + x1) / 2, cy0, x1 - x0 - 2, 1.6, sc.ch("mortar"), B3, 26, groups=groups,
                    layer="rim")
    if rune_every:
        n = int((x1 - x0) // 30)
        for i in range(n):
            if i % rune_every == rune_every // 2:
                glyph(sc, x0 + 15 + 30 * i, (y0 + y1) / 2, rng, groups, small=True)


def block_face(sc, cx, cy, rng, groups=(), rune=True, size=30.0, lit="top"):
    """Single gameplay cell: shaded face, bevel, inner shadow, optional rune."""
    pal = rock_palette(sc)
    sc.rect(cx, cy, size, size, pal[rng.choice((2, 3))], B3, 20, groups=groups, layer="rock")
    hy = cy + size / 2 - 1.7 if lit == "top" else cy - size / 2 + 1.7
    sy = cy - size / 2 + 2.6 if lit == "top" else cy + size / 2 - 2.6
    sc.rect(cx, hy, size - 4, 1.6, sc.ch("bevel_warm"), B3, 22, groups=groups, layer="rock")
    sc.rect(cx, sy, size - 4, 3.0, pal[0], B3, 22, groups=groups, layer="rock")
    # recessed inner panel
    sc.rect(cx, cy, size - 10, size - 10, pal[1], B3, 21, groups=groups, layer="rock")
    if rune:
        glyph(sc, cx, cy, rng, groups)


GLYPHS = [
    [((0, -7), (0, 7)), ((-5, 2), (0, 7)), ((5, 2), (0, 7))],                 # arrow
    [((-5, -6), (5, 6)), ((5, -6), (-5, 6)), ((-6, 0), (6, 0))],             # star cross
    [((0, -7), (0, 7)), ((-5, -3), (5, -3)), ((-3, 4), (3, 4))],             # double bar
    [((-5, -6), (0, 6)), ((0, 6), (5, -6)), ((-2.5, 0), (2.5, 0))],          # A-shape
    [((0, -7), (0, 7)), ((0, 0), (5, 5)), ((0, -3), (-5, 2))],               # branch (dendrite)
    [((-5, -5), (-5, 5)), ((-5, 5), (5, 5)), ((5, 5), (5, -5)), ((0, -6), (0, 2))],  # gate
]


def glyph(sc, cx, cy, rng, groups=(), small=False):
    g = rng.choice(GLYPHS)
    s = rng.uniform(0.8, 0.95) * (0.75 if small else 1.0)
    for (ax, ay), (bx, by) in g:
        sc.seg((cx + ax * s, cy + ay * s), (cx + bx * s, cy + by * s), 1.3, sc.ch("rune"), B3, 28,
               groups, "rim", extend=1.0)
    sc.glow(cx, cy, 26 if not small else 18, sc.ch("rune_glow"), B2, -28, groups, "glow", kind="S")


# ------------------------------------------------------------ basalt
def basalt_columns(sc, poly, x_left, x_right, y_bottom, y_top, rng, groups=(), width=(15, 22),
                   lit_below=150.0):
    """Columnar jointing over a pillar: dark joints, warm rims low on the pillar."""
    x = x_left + rng.uniform(*width) * 0.6
    while x < x_right - 6:
        pts = []
        y = y_bottom + 4
        while y < y_top:
            p = (x + rng.uniform(-1.5, 1.5), y)
            if point_in_poly(p, poly):
                pts.append(p)
            elif pts:
                break
            y += 26
        if len(pts) >= 2:
            sc.polyline(pts, 1.4, sc.ch("joint"), B2, -12, groups, "rim")
            low = [p for p in pts if p[1] < y_bottom + lit_below]
            if len(low) >= 2:
                sc.polyline([(p[0] + 1.8, p[1]) for p in low], 1.0, sc.ch("rim_hot"), B2, -11,
                            groups, "rim")
            for p in pts[1:-1]:
                if rng.random() < 0.35:
                    w = rng.uniform(6, 13)
                    sc.seg(p, (p[0] + w, p[1] + rng.uniform(-2, 2)), 1.0, sc.ch("joint"), B2, -12,
                           groups, "rim")
        x += rng.uniform(*width)
