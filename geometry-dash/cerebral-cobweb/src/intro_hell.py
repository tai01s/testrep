"""Hell deco for the opening of Cerebral Cobweb (x -400 .. ~2700).

Concept: an infernal cavern above a lava sea. A burning cobweb hangs in the
abyss around a molten "cerebral core" that fires synapse-like pulses along its
strands on the beats the layout already marks. Gameplay structures become
obsidian slabs with molten edges; floating hazards hang from glowing threads.

Depth planes (back to front):
  B5  far web + core + haze glows        (parallax 0.90 / 0.85, lock camera)
  B5g far spires (gradient fill)
  B4  far spire rims
  B4g mid spires (gradient fill)       (parallax 0.55 / 0.45)
  B3  mid rims / mid glows
  B3g near rock + lava body (gradient fill, gameplay depth)
  B2  cracks, molten edges, hazard glows, threads, lava surface, embers
  (layout objects on their default layers above B2)
  T2  sparks
  T3g foreground silhouettes             (parallax -0.30 / screen-locked y)
"""
import math
import random

from deco_lib import Scene, jitter_line, triangulate
from gdobj import (B5, B4, B3, B2, B1, T1, T2, T3, Obj, TARGET, OPACITY, DURATION,
                   HIGH_DETAIL, SPAWN_TRIG, MULTI_TRIG)
from particles import particle_string, TEX

# ----------------------------------------------------------------- timing
SPEED_PORTALS = [(789.0, 387.42), (3405.0, 468.0)]  # inside this section
V0 = 311.58


def x_to_t(x):
    t, cx, v = 0.0, 0.0, V0
    for px, pv in SPEED_PORTALS:
        if px <= cx:
            continue
        if px >= x:
            break
        t += (px - cx) / v
        cx, v = px, pv
    return t + (x - cx) / v


def t_to_x(t):
    cx, v, ct = 0.0, V0, 0.0
    for px, pv in SPEED_PORTALS:
        dt = (px - cx) / v
        if ct + dt >= t:
            break
        ct += dt
        cx, v = px, pv
    return cx + (t - ct) * v


# Camera assumptions (only used to place parallax content; see VERIFY.md)
C0 = (135.0, 65.0)          # camera centre at level start (player on ground at x=0)
CAM_OPEN = (195.0, 650.0)   # camera centre while running the start platform


def world_from_screen(m, s):
    """World position (at activation) of a parallax object that should appear at
    screen offset s (from camera centre) during the opening shot."""
    mx, my = m
    return (s[0] + mx * C0[0] + (1 - mx) * CAM_OPEN[0],
            s[1] + my * C0[1] + (1 - my) * CAM_OPEN[1])


FAR_M = (0.90, 0.85)
MID_M = (0.55, 0.45)
FG_M = (-0.30, 1.00)

LAVA_Y = 60.0


def lava_y(x):
    return LAVA_Y + 5.0 * math.sin(x / 53.0) + 3.0 * math.sin(x / 23.0 + 1.3)


# ------------------------------------------------------------- palette
def palette(sc: Scene):
    C = sc.chan
    C("far_rock", (21, 5, 10))
    C("far_rim", (122, 24, 16))
    C("mid_rock", (12, 3, 7))
    C("mid_rim", (205, 52, 22))
    C("near_rock", (7, 2, 4))
    C("crack", (255, 104, 34))
    C("crack_core", (255, 214, 150))
    C("rim_hot", (255, 120, 40))
    C("glow_o", (255, 84, 22), 0.50, True)
    C("glow_r", (190, 22, 10), 0.55, True)
    C("glow_hot", (255, 170, 90), 0.45, True)
    C("glow_deep", (120, 10, 8), 0.60, True)
    C("violet", (90, 22, 150), 0.22, True)
    C("web", (72, 14, 14))
    C("web_halo", (255, 60, 20), 0.12, True)
    C("core_w", (255, 236, 200))
    C("core_o", (255, 116, 30), 0.80, True)
    C("core_r", (200, 24, 12), 0.60, True)
    C("spike_glow", (255, 34, 14), 0.40, True)
    C("thread", (110, 20, 16))
    C("thread_halo", (255, 56, 18), 0.22, True)
    C("lava_deep", (110, 14, 8))
    C("lava_mid", (200, 40, 12))
    C("lava_top", (255, 150, 60))
    C("crust", (26, 5, 5))
    C("fg", (3, 1, 2))
    C("orb_back", (0, 0, 0), 0.65, False)
    C("plat_glow", (255, 90, 24), 0.70, True)


# --------------------------------------------------------------- spires
def spire(rng, base, height, width, lean=0.0, jag=0.10, spurs=2, rows=6):
    """Jagged spire polygon. height>0 rises, height<0 hangs."""
    bx, by = base
    tip = (bx + lean, by + height)
    n = max(3, rows)
    left, right = [], []
    spur_at = set(rng.sample(range(1, n - 1), min(spurs, max(0, n - 2)))) if n > 3 else set()
    for i in range(n + 1):
        t = i / n
        half = width / 2 * (1 - t) ** 0.85
        cx = bx + lean * t ** 1.6
        cy = by + height * t
        jl = rng.uniform(-jag, jag) * width
        jr = rng.uniform(-jag, jag) * width
        if i in (0, n):
            jl = jr = 0
        lx, rx = cx - half + jl, cx + half + jr
        left.append((lx, cy))
        right.append((rx, cy))
        if i in spur_at and half > 8:
            side = rng.choice((-1, 1))
            L = rng.uniform(0.5, 1.1) * half + 8
            sy = cy + height * rng.uniform(0.03, 0.07)
            if side < 0:
                left.append((lx - L, sy))
                left.append((lx - 2, cy + height * 0.09))
            else:
                right.append((rx + L, sy))
                right.append((rx + 2, cy + height * 0.09))
    pts = left[:-1] + [tip] + right[::-1][1:]
    return pts, tip


def edges_facing(pts, cond):
    """Yield edges (a,b) of polygon whose outward normal satisfies cond(nx, ny)."""
    # ensure CCW so outward normal = (dy, -dx)
    area = sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1]
               for i in range(len(pts)))
    if area < 0:
        pts = pts[::-1]
    for i in range(len(pts)):
        a, b = pts[i], pts[(i + 1) % len(pts)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy)
        if L < 1e-6:
            continue
        nx, ny = dy / L, -dx / L
        if cond(nx, ny):
            yield a, b


# ----------------------------------------------------------- far layer
def far_layer(sc: Scene, g_far, g_core, g_web, wave_groups):
    rng = random.Random(11)
    ch = sc.ch
    core = world_from_screen(FAR_M, (150.0, 95.0))
    cx, cy = core

    # ---- haze
    # (glow centres kept near the screen edge so they are not culled)
    for sx in range(-560, 1000, 190):
        x, y = world_from_screen(FAR_M, (sx + rng.uniform(-30, 30), -200))
        sc.glow(x, y, 500, ch("glow_deep"), B5, -40, (g_far,), "far")
    for sx in (-360, -60, 300, 620, 900):
        x, y = world_from_screen(FAR_M, (sx, 175))
        sc.glow(x, y, 400, ch("violet"), B5, -39, (g_far,), "far", high_detail=True)

    # ---- web
    n_rad = 18
    angles = sorted((i * 360.0 / n_rad + rng.uniform(-6, 6)) % 360 for i in range(n_rad))
    rad_len = [rng.uniform(560, 780) for _ in angles]
    rings = []
    k = 0
    while True:
        r = 80 + 26 * k * (1 + 0.035 * k)
        if r > 700:
            break
        rings.append(r)
        k += 1
    band_edges = [80, 150, 240, 340, 450, 570, 800]

    def band_of(r):
        for b in range(len(band_edges) - 1):
            if r < band_edges[b + 1]:
                return b
        return len(band_edges) - 2

    def pt(a_deg, r):
        a = math.radians(a_deg)
        return (cx + r * math.cos(a), cy + r * math.sin(a))

    broken = {i for i in range(n_rad) if rng.random() < 0.18}
    for i, a in enumerate(angles):
        Lr = rad_len[i] * (0.55 if i in broken else 1.0)
        cuts = [r for r in band_edges if r < Lr] + [Lr]
        prev = 34.0
        for r in cuts:
            if r <= prev:
                continue
            b = band_of((prev + r) / 2)
            p, q = pt(a + rng.uniform(-0.6, 0.6), prev), pt(a + rng.uniform(-0.6, 0.6), r)
            sc.seg(p, q, 2.2, ch("web"), B5, -20, (g_far, g_web, wave_groups[b]), "far")
            sc.seg(p, q, 7.0, ch("web_halo"), B5, -25, (g_far, g_web, wave_groups[b]), "far",
                   high_detail=True)
            prev = r
        if i in broken:  # dangling torn end
            end = pt(a, Lr)
            droop = (end[0] + rng.uniform(-30, 30), end[1] - rng.uniform(40, 90))
            sc.seg(end, droop, 1.6, ch("web"), B5, -20, (g_far, g_web), "far")
    for r in rings:
        b = band_of(r)
        for i in range(n_rad):
            j = (i + 1) % n_rad
            if r > rad_len[i] * (0.55 if i in broken else 1.0) or \
               r > rad_len[j] * (0.55 if j in broken else 1.0):
                continue
            if rng.random() < 0.08:
                continue  # torn
            a1, a2 = angles[i], angles[j] + (360 if j == 0 else 0)
            p, q = pt(a1, r), pt(a2, r)
            mid = pt((a1 + a2) / 2, r * 0.955)       # inward sag
            sc.seg(p, mid, 1.6, ch("web"), B5, -21, (g_far, g_web, wave_groups[b]), "far")
            sc.seg(mid, q, 1.6, ch("web"), B5, -21, (g_far, g_web, wave_groups[b]), "far")

    # ---- cerebral core
    for d, c, zo in ((520, "glow_deep", -12), (300, "core_r", -11), (160, "core_o", -10)):
        sc.glow(cx, cy, d, ch(c), B5, zo, (g_far, g_core), "far")
    sc.glow(cx, cy, 74, ch("glow_hot"), B5, -9, (g_far, g_core), "far", kind="M")
    sc.glow(cx, cy, 34, ch("core_w"), B5, -2, (g_far, g_core), "far", kind="S")
    # neural knot: molten arcs + dendrites
    for k in range(9):
        r = rng.uniform(22, 46)
        a0 = rng.uniform(0, 360)
        span = rng.uniform(50, 110)
        pts = [(cx + r * math.cos(math.radians(a0 + span * s / 4)),
                cy + r * math.sin(math.radians(a0 + span * s / 4)) * 0.85) for s in range(5)]
        sc.polyline(pts, 2.4, ch("crack"), B5, -5, (g_far, g_core), "far")
        if k % 3 == 0:
            sc.polyline(pts[1:4], 1.0, ch("crack_core"), B5, -4, (g_far, g_core), "far")
    for k in range(7):
        a = math.radians(rng.uniform(0, 360))
        p = (cx + 40 * math.cos(a), cy + 40 * math.sin(a))
        q = (cx + rng.uniform(75, 110) * math.cos(a + 0.12), cy + rng.uniform(75, 110) * math.sin(a + 0.12))
        sc.seg(p, q, 1.6, ch("crack"), B5, -6, (g_far, g_core), "far")
        br = (q[0] + 22 * math.cos(a + 0.9), q[1] + 22 * math.sin(a + 0.9))
        sc.seg(q, br, 1.1, ch("crack"), B5, -6, (g_far, g_core), "far")

    # ---- far spires (gradient fill on B5, rims on B4)
    bottoms = [(-480, 340, 170, 20), (-250, 250, 130, -10), (20, 190, 110, -8),
               (300, 300, 150, 25), (540, 380, 170, -20), (790, 300, 150, -15),
               (1010, 270, 140, 12)]
    tops = [(-400, -250, 150, 10), (-120, -170, 110, 8), (480, -240, 130, 15),
            (720, -290, 160, -10), (980, -230, 130, -6)]
    for sx, H, W, lean in bottoms:
        base = world_from_screen(FAR_M, (sx, -330))
        poly, tip = spire(rng, base, H + 30, W, lean, jag=0.09, spurs=1, rows=5)
        sc.gpoly(poly, ch("far_rock"), "b5", (g_far,))
        # rim on the side facing the core
        side = 1 if base[0] < cx else -1
        for a, b in edges_facing(poly, lambda nx, ny, s=side: nx * s > 0.55):
            sc.seg(a, b, 1.3, ch("far_rim"), B4, -10, (g_far,), "far", extend=1.0)
    for sx, H, W, lean in tops:
        base = world_from_screen(FAR_M, (sx, 330))
        poly, tip = spire(rng, base, H - 30, W, lean, jag=0.09, spurs=1, rows=5)
        sc.gpoly(poly, ch("far_rock"), "b5", (g_far,))
        for a, b in edges_facing(poly, lambda nx, ny: ny < -0.25):
            sc.seg(a, b, 1.6, ch("far_rim"), B4, -10, (g_far,), "far", extend=1.0)
        sc.glow(tip[0], tip[1] - 6, 46, ch("glow_o"), B4, -12, (g_far,), "far", kind="S")
    return core


# ----------------------------------------------------------- mid layer
def mid_layer(sc: Scene, g_mid):
    rng = random.Random(23)
    ch = sc.ch
    rising = [(-260, 210, 170, 18), (60, 330, 170, 22), (380, 290, 220, -16),
              (690, 370, 190, 10), (1010, 300, 210, -18), (1330, 360, 200, 14),
              (1640, 310, 210, -14)]
    hanging = [(-150, 570, 190, -10), (210, 610, 200, -8), (540, 650, 180, 12),
               (870, 590, 210, -16), (1190, 640, 190, 10), (1520, 600, 210, -12)]
    for x, tip_y, W, lean in rising:
        base = (x, -160.0)
        poly, tip = spire(rng, base, tip_y + 160, W, lean, jag=0.08, spurs=2, rows=6)
        sc.gpoly(poly, ch("mid_rock"), "b4", (g_mid,))
        # lava light on the lower part of both flanks
        for a, b in edges_facing(poly, lambda nx, ny: abs(nx) > 0.6):
            if max(a[1], b[1]) < 150:
                sc.seg(a, b, 2.0, ch("mid_rim"), B3, -10, (g_mid,), "mid", extend=1.5)
        # vein
        if rng.random() < 0.7:
            vx = x + rng.uniform(-W * 0.12, W * 0.12)
            pts = [(vx + rng.uniform(-6, 6), y) for y in range(-60, int(tip_y * 0.55), 34)]
            sc.polyline(pts, 1.7, ch("crack"), B3, -8, (g_mid,), "mid")
            for p in pts[1:-1:2]:
                d = rng.choice((-1, 1))
                sc.seg(p, (p[0] + d * rng.uniform(10, 22), p[1] + rng.uniform(8, 20)), 1.2,
                       ch("crack"), B3, -8, (g_mid,), "mid")
    for x, tip_y, W, lean in hanging:
        base = (x, 1260.0)
        poly, tip = spire(rng, base, tip_y - 1260, W, lean, jag=0.08, spurs=2, rows=6)
        sc.gpoly(poly, ch("mid_rock"), "b4", (g_mid,))
        for a, b in edges_facing(poly, lambda nx, ny: ny < -0.2):
            sc.seg(a, b, 2.2, ch("mid_rim"), B3, -10, (g_mid,), "mid", extend=1.5)
        sc.glow(tip[0], tip[1] - 4, 70, ch("glow_o"), B3, -12, (g_mid,), "mid", kind="M")
    # lava-lit haze in front of the mid spire bases
    for x in range(-300, 1900, 380):
        sc.glow(x + rng.uniform(-60, 60), 20 + rng.uniform(-20, 20), 520, ch("glow_r"), B3, -20,
                (g_mid,), "mid", high_detail=True)


# ---------------------------------------------------------------- lava
def lava(sc: Scene, x0=-650, x1=3350):
    rng = random.Random(31)
    ch = sc.ch
    # body (batched objects, no gradients): a 44-unit hot band whose top edge
    # follows the wavy surface, then the deep body as big rectangles below it
    pts = [(x, lava_y(x)) for x in range(x0, x1 + 1, 40)]
    for p, q in zip(pts, pts[1:]):
        dx, dy = q[0] - p[0], q[1] - p[1]
        L = math.hypot(dx, dy)
        nx, ny = -dy / L, dx / L                     # upward normal
        cx, cy = (p[0] + q[0]) / 2 - nx * 21, (p[1] + q[1]) / 2 - ny * 21
        sc.rect(cx, cy, L + 2.0, 44, ch("lava_mid"), B3, -30,
                rot=-math.degrees(math.atan2(dy, dx)), layer="lava")
    for x in range(x0, x1 + 1, 150):
        sc.rect(x + 75, -72.5, 152, 195, ch("lava_deep"), B3, -31, layer="lava")
    # surface line + white-hot seam
    sc.polyline(pts, 4.0, ch("lava_top"), B2, -14, (), "lava")
    sc.polyline([(x, y - 4.5) for x, y in pts], 1.4, ch("crack_core"), B2, -13, (), "lava",
                high_detail=True)
    # crust plates drifting on the surface
    x = x0
    while x < x1:
        x += rng.uniform(70, 130)
        w = rng.uniform(26, 70)
        sc.rect(x, lava_y(x) - 1.5, w, rng.uniform(4.5, 7.5), ch("crust"), B2, -12,
                rot=rng.uniform(-4, 4), layer="lava")
    # glow above the surface
    for x in range(x0, x1 + 1, 110):
        sc.glow(x, lava_y(x) + 38, 250, ch("glow_o"), B2, -30, (), "lava")
    for x in range(x0, x1 + 1, 300):
        sc.glow(x + 60, 110, 620, ch("glow_r"), B2, -31, (), "lava", high_detail=True)


# ----------------------------------------------------------- structures
CEILING_LINE = [(120, 870), (480, 690), (540, 720), (840, 570), (870, 570), (1110, 690)]


def molten_line_glow(sc, a, b, spacing, diam, ch_name, z=B2, zo=-6, offset=(0, 0),
                     groups=(), layer="glow"):
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    n = max(1, int(L // spacing))
    for i in range(n + 1):
        t = i / n
        sc.glow(a[0] + (b[0] - a[0]) * t + offset[0], a[1] + (b[1] - a[1]) * t + offset[1],
                diam, sc.ch(ch_name), z, zo, groups, layer, kind="S")


def roof_y(x):
    pts = CEILING_LINE
    if x <= pts[0][0]:
        return pts[0][1]
    for a, b in zip(pts, pts[1:]):
        if a[0] <= x <= b[0]:
            return a[1] + (b[1] - a[1]) * (x - a[0]) / (b[0] - a[0])
    return pts[-1][1]


def cracks_from(sc, rng, origin, direction, length, groups=(), z=B2, layer="rim",
                core=True, branches=2, inside=None):
    """Branching molten crack starting at origin, heading in direction (deg).
    `inside(point)` keeps the crack inside its rock mass (it is cut where it would leave)."""
    pts = [origin]
    ang = direction
    seg_n = max(2, int(length / 12))
    for i in range(seg_n):
        ang += rng.uniform(-22, 22)
        ang = direction + max(-40, min(40, ang - direction))
        L = length / seg_n
        p = pts[-1]
        q = (p[0] + L * math.cos(math.radians(ang)), p[1] + L * math.sin(math.radians(ang)))
        if inside is not None and not inside(q):
            break
        pts.append(q)
    if len(pts) < 2:
        return
    sc.polyline(pts, 2.2, sc.ch("crack"), z, -4, groups, layer)
    if core:
        sc.polyline(pts[:max(2, len(pts) // 2 + 1)], 0.9, sc.ch("crack_core"), z, -3, groups, layer)
    for _ in range(branches):
        if len(pts) < 3:
            break
        p = pts[rng.randrange(1, len(pts) - 1)]
        a = direction + rng.choice((-1, 1)) * rng.uniform(35, 70)
        L = length * rng.uniform(0.25, 0.45)
        q = (p[0] + L * math.cos(math.radians(a)), p[1] + L * math.sin(math.radians(a)))
        if inside is not None and not inside(q):
            continue
        sc.seg(p, q, 1.4, sc.ch("crack"), z, -4, groups, layer, extend=1.2)


def structures(sc: Scene):
    rng = random.Random(41)
    ch = sc.ch
    rock = ch("near_rock")

    # ---- ceiling mass above the sloped roof
    left_under = [(-380, 905), (-330, 900), (-290, 840), (-262, 772), (-240, 840), (-205, 905),
                  (-160, 892), (-128, 846), (-108, 812), (-92, 850), (-70, 894), (-30, 884),
                  (10, 892), (40, 862), (52, 846), (66, 866), (90, 880), (120, 870)]
    right_edge = [(1110, 690), (1124, 712), (1140, 748), (1162, 780), (1196, 808), (1236, 880),
                  (1262, 960), (1286, 1060), (1300, 1150), (1310, 1400)]
    ceiling = left_under + CEILING_LINE[1:] + right_edge[1:] + [(-380, 1400)]
    sc.gpoly(ceiling, rock, "b3")
    # molten underside: glow just below the roof line + veins going up into the rock
    for a, b in zip(CEILING_LINE, CEILING_LINE[1:]):
        molten_line_glow(sc, a, b, 34, 44, "glow_o", offset=(0, -6))
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        n = int(L // 70)
        for i in range(n):
            t = (i + rng.uniform(0.2, 0.8)) / max(n, 1)
            p = (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t + 3)
            cracks_from(sc, rng, p, 90 + rng.uniform(-25, 25), rng.uniform(26, 70),
                        inside=lambda q: q[1] > roof_y(q[0]) + 4)
    # stalactite tips of the overhang: hot tips + rim on downward faces
    for i in range(1, len(left_under) - 1):
        p = left_under[i]
        if p[1] < left_under[i - 1][1] and p[1] < left_under[i + 1][1]:
            sc.glow(p[0], p[1] + 4, 40, ch("glow_o"), B2, -6, (), "glow", kind="S")
            sc.seg(left_under[i - 1], p, 1.8, ch("rim_hot"), B2, -5, (), "rim", extend=1.5)
            sc.seg(p, left_under[i + 1], 1.8, ch("rim_hot"), B2, -5, (), "rim", extend=1.5)
    for a, b in zip(right_edge, right_edge[1:5]):
        sc.seg(a, b, 1.8, ch("rim_hot"), B2, -5, (), "rim", extend=1.5)

    # ---- small block hanging under the roof at x=607 + its stub
    sc.gpoly([(592, 630), (622, 630), (622, 660), (592, 660)], rock, "b3")
    sc.gpoly([(600, 658), (614, 658), (612, 690), (602, 692)], rock, "b3")
    sc.seg((607, 662), (607, 688), 1.6, ch("crack"), B2, -4, (), "rim")

    # ---- start platform: obsidian slab over a floating stalactite
    p0 = [(14, 600), (254, 600), (254, 570), (238, 548), (226, 520), (210, 506), (196, 476),
          (182, 456), (168, 418), (156, 384), (146, 352), (138, 330), (128, 360), (116, 396),
          (102, 430), (86, 456), (70, 478), (56, 502), (40, 526), (26, 548), (14, 570)]
    sc.gpoly(p0, rock, "b3")
    sc.gpoly([(186, 600), (216, 600), (216, 630), (186, 630)], rock, "b3")
    for a, b in edges_facing(p0, lambda nx, ny: ny < -0.15):
        if a[1] < 569 and b[1] < 569:
            sc.seg(a, b, 2.0, ch("rim_hot"), B2, -5, (), "rim", extend=1.5)
    sc.glow(138, 336, 60, ch("glow_o"), B2, -6, (), "glow", kind="M")
    for x in (62, 118, 172, 226):
        cracks_from(sc, rng, (x + rng.uniform(-8, 8), 572), -90 + rng.uniform(-25, 25),
                    rng.uniform(40, 90), branches=1,
                    inside=lambda q: q[1] < 596 and point_in_poly(q, p0))
    molten_line_glow(sc, (16, 600), (252, 600), 22, 40, "glow_o", offset=(0, 5))

    # ---- L-structure (x 780-870) on a pillar rising from the lava
    f1 = [(780, 510), (870, 510), (870, 390), (874, 340), (884, 290), (896, 240), (905, 190),
          (915, 140), (932, 96), (962, lava_y(962) + 2), (788, lava_y(788) + 2), (810, 96),
          (824, 150), (832, 220), (837, 300), (840, 360), (840, 480), (780, 480)]
    sc.gpoly(f1, rock, "b3")
    pillar_details(sc, rng, f1, x_center=872)
    molten_line_glow(sc, (782, 510), (868, 510), 22, 40, "glow_o", offset=(0, 5))

    # ---- floating block at 959,525
    sc.gpoly([(944, 510), (974, 510), (974, 540), (944, 540)], rock, "b3")
    molten_line_glow(sc, (946, 540), (972, 540), 26, 34, "glow_o", offset=(0, 4))

    # ---- block at 1165 on a stalk + floor platform 1215-1305 on its own support
    f2 = [(1150, 588), (1180, 588), (1180, 558), (1179, 500), (1182, 440), (1190, 390),
          (1203, 345), (1214, 380), (1210, 420), (1204, 455), (1200, 480), (1200, 510),
          (1320, 510), (1320, 480), (1316, 445), (1310, 400), (1306, 350), (1308, 300),
          (1316, 250), (1330, 200), (1350, 150), (1372, 100), (1400, lava_y(1400) + 2),
          (1040, lava_y(1040) + 2), (1068, 100), (1092, 150), (1110, 200), (1124, 250),
          (1134, 300), (1141, 350), (1146, 400), (1149, 450), (1150, 500), (1150, 558)]
    sc.gpoly(f2, rock, "b3")
    pillar_details(sc, rng, f2, x_center=1220)
    molten_line_glow(sc, (1202, 510), (1318, 510), 22, 40, "glow_o", offset=(0, 5))
    molten_line_glow(sc, (1152, 588), (1178, 588), 26, 34, "glow_o", offset=(0, 4))

    # ---- structure 1668-1998: roof slab with hanging column (mass above only)
    # slab hangs from a stem that narrows upward, leaving windows to the far web/core
    roof = [(1668, 508), (1698, 508), (1698, 568), (1998, 568), (2000, 600), (1978, 628),
            (1946, 652), (1918, 690), (1898, 740), (1886, 800), (1880, 880), (1884, 980),
            (1892, 1100), (1900, 1400), (1756, 1400), (1764, 1100), (1772, 980), (1776, 880),
            (1770, 800), (1756, 742), (1732, 694), (1704, 656), (1680, 628), (1668, 600)]
    sc.gpoly(roof, rock, "b3")
    for a, b in zip(roof[4:9], roof[5:10]):
        sc.seg(a, b, 1.8, ch("rim_hot"), B2, -5, (), "rim", extend=1.5)
    for a, b in zip(roof[18:23], roof[19:24]):
        sc.seg(a, b, 1.8, ch("rim_hot"), B2, -5, (), "rim", extend=1.5)
    molten_line_glow(sc, (1700, 568), (1996, 568), 34, 44, "glow_o", offset=(0, -6))
    for x in range(1720, 1990, 70):
        cracks_from(sc, rng, (x + rng.uniform(-10, 10), 571), 90 + rng.uniform(-25, 25),
                    rng.uniform(30, 70), inside=lambda q: q[1] > 572)
    sc.seg((1668, 509), (1698, 509), 2.0, ch("rim_hot"), B2, -5, (), "rim")
    # floor tower: only its own cells (the dip path may pass underneath)
    sc.gpoly([(1668, 360), (1728, 360), (1728, 450), (1698, 450), (1698, 390), (1668, 390)],
             rock, "b3")
    sc.seg((1669, 361), (1727, 361), 2.0, ch("rim_hot"), B2, -5, (), "rim")

    # ---- hanging rock chunk above x 2100-2200 that the last hazards hang from
    chunk = [(2080, 1400), (2085, 980), (2100, 900), (2118, 852), (2138, 820), (2152, 846),
             (2170, 830), (2188, 860), (2206, 920), (2220, 1000), (2226, 1400)]
    sc.gpoly(chunk, rock, "b3")
    for i in (4, 6):
        sc.glow(chunk[i][0], chunk[i][1] + 3, 40, ch("glow_o"), B2, -6, (), "glow", kind="S")
    for a, b in zip(chunk[2:9], chunk[3:10]):
        sc.seg(a, b, 1.8, ch("rim_hot"), B2, -5, (), "rim", extend=1.5)


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


def pillar_details(sc, rng, poly, x_center):
    ch = sc.ch
    # rim light from the lava on the lower flanks
    for a, b in edges_facing(poly, lambda nx, ny: abs(nx) > 0.55):
        if max(a[1], b[1]) < 300:
            sc.seg(a, b, 2.0, ch("rim_hot"), B2, -5, (), "rim", extend=1.5)
    # contact glow where the pillar meets the lava
    sc.glow(x_center, lava_y(x_center) + 20, 200, ch("glow_o"), B2, -7, (), "glow")
    # veins rising from the lava
    for k in range(3):
        x = x_center + rng.uniform(-50, 30)
        cracks_from(sc, rng, (x, lava_y(x) + 6), 90 + rng.uniform(-14, 14), rng.uniform(70, 150),
                    branches=2, inside=lambda q: point_in_poly(q, poly))


# ---------------------------------------------- hazard glows + threads
HAZARD_DIAM = {"216": 54, "8": 54, "218": 38, "217": 36, "458": 28, "9": 54}
SAW_DIAM = {"1735": 130, "187": 120, "680": 90, "679": 120, "1709": 130}
ORBS = {"36", "84", "141", "1022", "1330", "1333", "1704", "1751"}


def hazards(sc: Scene, layout_objs, x0=-50, x1=2700):
    ch = sc.ch
    seen_saws = set()
    for o in layout_objs:
        oid = o.get("1")
        x, y = float(o["2"]), float(o["3"])
        if not (x0 <= x <= x1):
            continue
        if oid in HAZARD_DIAM:
            sc.glow(x, y, HAZARD_DIAM[oid], ch("spike_glow"), B2, -2, (), "glow", kind="S")
        elif oid in SAW_DIAM and (x, y) not in seen_saws:
            seen_saws.add((x, y))
            sc.glow(x, y, SAW_DIAM[oid] * 1.1, ch("spike_glow"), B2, -2, (), "glow", kind="L")
            sc.glow(x, y, 26, ch("glow_hot"), B2, -1, (), "glow", kind="S")
        elif oid in ORBS:
            s = float(o.get("128", 1))
            sc.glow(x, y, 64 * s, ch("orb_back"), B2, 2, (), "glow", kind="M")
    return seen_saws


THREADS = [
    # (hazard anchor point, far anchor point)
    ((575, 494), (556, 40)),          # gear blade under the roof funnel
    ((645, 525), (664, 40)),          # spike diamond
    ((1005, 480), (1032, 40)),        # spike diamond
    ((1065, 562), (1088, 40)),        # small spike diamond
    ((1185, 698), (1190, 806)),       # spike diamond -> ceiling overhang
    ((1999, 504), (1994, 568)),       # spike diamond -> roof slab
    ((2133, 542), (2140, 822)),       # spike diamond -> hanging chunk
    ((2185, 512), (2170, 832)),       # spike blade -> hanging chunk
    ((1109, 683), (1124, 712)),       # outline blade -> overhang edge
]


def threads(sc: Scene):
    rng = random.Random(53)
    ch = sc.ch
    for a, b in THREADS:
        sc.seg(a, b, 2.0, ch("thread"), B2, -8, (), "thread")
        sc.seg(a, b, 7.0, ch("thread_halo"), B2, -9, (), "thread", high_detail=True)
        # molten beads sliding on the thread
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        for k in range(int(L // 90)):
            t = rng.uniform(0.15, 0.9)
            sc.glow(a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, 12, ch("glow_hot"), B2, -7,
                    (), "thread", kind="S")


# ------------------------------------------------------------ particles
def ember_string(width, height, life=5.0, up_speed=34, size=4.0, emission=7, maxp=40):
    return particle_string(
        max_particles=maxp, duration=-1, lifetime=life, lifetime_var=life * 0.3,
        emission=emission, angle=90, angle_var=22, speed=up_speed, speed_var=up_speed * 0.45,
        posvar_x=width, posvar_y=height, grav_x=0, grav_y=6, accel_tan=0, accel_tan_var=14,
        start_size=size, start_size_var=size * 0.45, start_spin=0, start_spin_var=0,
        start_r=1, start_g=0.55, start_g_var=0.2, start_b=0.16, start_b_var=0.06, start_a=1,
        end_size=1, end_size_var=0.5, end_r=1, end_g=0.14, end_b=0.04, end_a=0,
        fade_in=0.4, fade_in_var=0.2, fade_out=1.0, fade_out_var=0.3,
        mode=0, mode2=0, additive=1, texture=TEX["circle"])


def particles(sc: Scene, saws, g_plat):
    rng = random.Random(61)
    # rising embers over the lava and through the cavern (behind gameplay)
    for x in range(-300, 3101, 300):
        sc.particles(x + rng.uniform(-40, 40), LAVA_Y + 20, ember_string(80, 10), B2, -20)
    for x in range(-150, 2901, 380):
        sc.particles(x + rng.uniform(-60, 60), 470 + rng.uniform(-60, 60),
                     ember_string(90, 70, life=4.0, up_speed=22, size=3.2, emission=4, maxp=24),
                     B2, -20)
    for x in range(0, 2801, 520):
        sc.particles(x + rng.uniform(-60, 60), 860 + rng.uniform(-60, 60),
                     ember_string(110, 80, life=4.0, up_speed=18, size=2.8, emission=3, maxp=18),
                     B2, -20)
    # sparse embers in front of gameplay
    for x in range(100, 2701, 650):
        sc.particles(x, 300, ember_string(70, 120, life=6.0, up_speed=30, size=2.4, emission=1.4,
                                          maxp=12), T2, 0)
    # molten drip from the start platform's stalactite tip
    drip = particle_string(max_particles=6, duration=-1, lifetime=1.8, lifetime_var=0.3,
                           emission=1.2, angle=270, angle_var=0, speed=0, speed_var=2,
                           posvar_x=0, posvar_y=0, grav_x=0, grav_y=-260,
                           start_size=3.4, start_size_var=0.6, end_size=2.2, end_size_var=0.3,
                           start_r=1, start_g=0.7, start_b=0.3, start_a=1,
                           end_r=1, end_g=0.2, end_b=0.05, end_a=0.2,
                           fade_in=0.1, fade_out=0.3, mode=0, mode2=0, additive=1,
                           texture=TEX["circle"])
    sc.particles(138, 328, drip, B2, -10)
    # sparks off every saw
    spark = particle_string(max_particles=14, duration=-1, lifetime=0.35, lifetime_var=0.15,
                            emission=26, angle=90, angle_var=180, speed=70, speed_var=30,
                            posvar_x=6, posvar_y=6, grav_x=0, grav_y=-180,
                            start_size=2.4, start_size_var=0.8, end_size=0.6, end_size_var=0.2,
                            start_r=1, start_g=0.85, start_b=0.45, start_a=1,
                            end_r=1, end_g=0.3, end_b=0.05, end_a=0,
                            fade_in=0, fade_out=0.12, mode=0, mode2=0, additive=1,
                            texture=TEX["circle"])
    for (x, y) in saws:
        sc.particles(x, y, spark, T2, 2)
    # ember trail behind the moving platform (free mode so particles stay behind)
    trail = particle_string(max_particles=30, duration=-1, lifetime=0.8, lifetime_var=0.25,
                            emission=26, angle=90, angle_var=180, speed=8, speed_var=6,
                            posvar_x=8, posvar_y=6, grav_x=0, grav_y=10,
                            start_size=5, start_size_var=1.5, end_size=1, end_size_var=0.4,
                            start_r=1, start_g=0.5, start_b=0.12, start_a=1,
                            end_r=1, end_g=0.12, end_b=0.03, end_a=0,
                            fade_in=0.05, fade_out=0.3, mode=0, mode2=0, additive=1,
                            texture=TEX["circle"])
    sc.particles(1405, 488, trail, B2, -3, (g_plat,))


# ------------------------------------------------------ moving platform
def moving_platform(sc: Scene, g_plat):
    ch = sc.ch
    # the layout's group-1 outline square at (1405,495) is the platform
    sc.gpoly([(1390, 480), (1420, 480), (1420, 510), (1390, 510)], ch("near_rock"), "b3",
             (g_plat,))
    sc.glow(1405, 495, 90, ch("plat_glow"), B2, -6, (g_plat,), "plat", kind="L")
    sc.glow(1405, 512, 40, ch("glow_hot"), B2, -5, (g_plat,), "plat", kind="S")
    sc.seg((1391, 481), (1419, 481), 2.0, ch("rim_hot"), B2, -4, (g_plat,), "plat")
    # follow the layout's own platform movement (group 1) - starts before its move
    sc.follow(1330.0, g_plat, 1, 7.0)


# -------------------------------------------------------------- foreground
def foreground(sc: Scene, g_fg):
    rng = random.Random(71)
    ch = sc.ch
    # screen-locked vertically, faster than gameplay horizontally
    for i, sx0 in enumerate(range(-200, 3700, 560)):
        sx = sx0 + rng.uniform(-80, 80)
        # hanging tip peeking ~40-60 units into the top edge
        W = rng.uniform(70, 120)
        top = world_from_fg((sx, 230))
        poly, tip = spire(rng, top, -(rng.uniform(95, 115)), W, rng.uniform(-15, 15), jag=0.1,
                          spurs=1, rows=4)
        sc.gpoly(poly, ch("fg"), "t3", (g_fg,))
        if i % 2 == 0:
            bot = world_from_fg((sx + 280, -240))
            poly, tip = spire(rng, bot, rng.uniform(95, 112), rng.uniform(110, 170),
                              rng.uniform(-20, 20), jag=0.1, spurs=1, rows=4)
            sc.gpoly(poly, ch("fg"), "t3", (g_fg,))


def world_from_fg(s):
    mx, my = FG_M
    return (s[0] + mx * C0[0] + (1 - mx) * CAM_OPEN[0], s[1] + my * C0[1] + (1 - my) * CAM_OPEN[1])


# -------------------------------------------------------------- sync
BIG = [3.487, 7.426]                          # layout BG pulse, platform launch
SMALL = [1.107, 1.589, 1.878, 2.359, 2.532, 2.935, 3.245, 4.122, 4.819, 5.103, 9.207]


def sync(sc: Scene, wave_groups, g_core, g_web):
    ch = sc.ch
    # opening: core and web ignite while the camera rises
    a = sc._trig(1007, 5.0); a.set(TARGET, g_core); a.set(DURATION, 0); a.set(OPACITY, 0)
    a = sc._trig(1007, 5.0); a.set(TARGET, g_web); a.set(DURATION, 0); a.set(OPACITY, 0)
    g_ign = sc.group()
    sc.spawn(6.0, g_ign, delay=0.12)
    for tgt, d in ((g_core, 1.1), (g_web, 1.8)):
        o = sc._trig(1007, 7.0)
        o.set(TARGET, tgt); o.set(DURATION, d); o.set(OPACITY, 1)
        o.set(SPAWN_TRIG, 1); o.set(MULTI_TRIG, 1); o.add_groups(g_ign)
    sc.pulse(8.0, ch("glow_r"), (255, 70, 20), 0.4, 0.2, 1.2)

    for t in SMALL:
        x = t_to_x(t)
        sc.pulse(x, ch("core_o"), (255, 196, 120), 0.02, 0.04, 0.28)
        sc.pulse(x, ch("core_r"), (255, 64, 24), 0.02, 0.04, 0.32)
        sc.pulse(x, wave_groups[0], (255, 120, 44), 0.02, 0.03, 0.3, group=True)
        sc.pulse(t_to_x(t + 0.06), wave_groups[1], (220, 80, 30), 0.02, 0.03, 0.3, group=True)
    for t in BIG:
        x = t_to_x(t)
        sc.pulse(x, ch("core_w"), (255, 255, 255), 0.02, 0.06, 0.5)
        sc.pulse(x, ch("core_o"), (255, 220, 160), 0.02, 0.08, 0.6)
        sc.pulse(x, ch("core_r"), (255, 90, 30), 0.02, 0.08, 0.7)
        sc.pulse(x, ch("glow_deep"), (220, 30, 14), 0.03, 0.05, 0.9)
        sc.pulse(x, ch("glow_r"), (255, 80, 24), 0.03, 0.05, 0.9)
        sc.pulse(x, ch("lava_top"), (255, 230, 170), 0.03, 0.05, 0.7)
        for b, g in enumerate(wave_groups):
            sc.pulse(t_to_x(t + 0.07 * b), g, (255, 132, 48), 0.03, 0.05, 0.45, group=True)
    # slow lava breathing between the beats
    t = 0.7
    while t < 9.2:
        sc.pulse(t_to_x(t), ch("glow_o"), (255, 120, 40), 0.55, 0.1, 0.65)
        t += 1.35


def layout_colors_on(sc: Scene):
    # channels 1 / 1004 are also used later in the level -> set here, revert after the intro
    sc.color_trigger(2.0, 1004, (255, 96, 32), 0)
    sc.color_trigger(2.0, 1, (34, 8, 10), 0)
    sc.options(2.0, {161: 1})            # hide ground (lava sea replaces it)
    sc.color_trigger(3300.0, 1004, (255, 255, 255), 0.5)
    sc.color_trigger(3300.0, 1, (255, 255, 255), 0.5)
    sc.options(3350.0, {161: -1})          # ground back for the rest of the level


# ------------------------------------------------------------------ main
def build(sc: Scene, layout_objs):
    palette(sc)
    g_far, g_mid, g_fg, g_plat = sc.group(), sc.group(), sc.group(), sc.group()
    g_core, g_web = sc.group(), sc.group()
    wave_groups = [sc.group() for _ in range(6)]

    far_layer(sc, g_far, g_core, g_web, wave_groups)
    mid_layer(sc, g_mid)
    lava(sc)
    structures(sc)
    saws = hazards(sc, layout_objs)
    threads(sc)
    moving_platform(sc, g_plat)
    particles(sc, saws, g_plat)
    foreground(sc, g_fg)

    # parallax locks start on the first frame (camera still at its initial position C0)
    sc.lock_camera(3.0, g_far, *FAR_M)
    sc.lock_camera(3.0, g_mid, *MID_M)
    sc.lock_camera(3.0, g_fg, *FG_M)
    sync(sc, wave_groups, g_core, g_web)
    layout_colors_on(sc)
    return dict(g_far=g_far, g_mid=g_mid, g_fg=g_fg, g_plat=g_plat, g_core=g_core,
                g_web=g_web, waves=wave_groups)
