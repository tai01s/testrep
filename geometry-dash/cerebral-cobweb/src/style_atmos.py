"""Reusable atmosphere / animation pieces: lavafall, floating debris, bob loops,
foreground bokeh embers."""
import math
import random

from gdobj import (B1, B2, B3, T2, T3, Obj, TARGET, DURATION, EASING, MOVE_X, MOVE_Y,
                   SPAWN_TRIG, MULTI_TRIG, SPAWN_DELAY, SECOND_TARGET, DEGREES, EDITOR_L1)
from particles import particle_string, TEX
from style_rock import facet_fill

SMALL_STEP = 393
EASE_SINE_IN_OUT = 13


# ------------------------------------------------------------- loops
def move_trigger(sc, x, target, dx, dy, dur, easing=0, spawn=False, groups=()):
    o = sc._trig(901, x)
    o.set(TARGET, target)
    o.set(MOVE_X, int(round(dx))); o.set(MOVE_Y, int(round(dy)))
    o.set(SMALL_STEP, 1)                 # 1 unit = 1 world unit (GD Creator School)
    o.set(DURATION, dur)
    o.set(EASING, easing)
    if spawn:
        o.set(SPAWN_TRIG, 1); o.set(MULTI_TRIG, 1)
    if groups:
        o.add_groups(*groups)
    return o


def bob_loop(sc, target, amp, period, start_x=6.0, phase=0.0, x_loop=-40.0):
    """target drifts up and down by `amp` world units forever (sine easing)."""
    up, down = sc.group(), sc.group()
    # loop A: move up, then (after half a period) spawn loop B; A respawns itself
    move_trigger(sc, x_loop, target, 0, amp, period / 2, EASE_SINE_IN_OUT, spawn=True, groups=(up,))
    s = sc.spawn(x_loop, down, delay=period / 2, spawn=True); s.add_groups(up)
    s = sc.spawn(x_loop, up, delay=period, spawn=True); s.add_groups(up)
    move_trigger(sc, x_loop, target, 0, -amp, period / 2, EASE_SINE_IN_OUT, spawn=True, groups=(down,))
    sc.spawn(start_x, up, delay=phase)
    return up, down


def rotate_loop(sc, target, center, period, start_x=6.0, x_loop=-40.0):
    loop = sc.group()
    o = sc._trig(1346, x_loop)
    o.set(TARGET, target); o.set(SECOND_TARGET, center); o.set(DEGREES, 360)
    o.set(DURATION, period); o.set(EASING, 0)
    o.set(SPAWN_TRIG, 1); o.set(MULTI_TRIG, 1); o.add_groups(loop)
    s = sc.spawn(x_loop, loop, delay=period, spawn=True); s.add_groups(loop)
    sc.spawn(start_x, loop)
    return loop


def stop_groups(sc, x, groups):
    for g in groups:
        o = sc._trig(1616, x)
        o.set(TARGET, g)


# ------------------------------------------------------------- debris
def debris(sc, center, size, rng, groups=(), seed=0, layer="b3", z=B2, palette=None, rim=True,
           rim_ch="rim_hot"):
    """Floating obsidian chunk: faceted body lit from below, hot rim on the
    underside, a molten crack and a soft glow under it."""
    cx, cy = center
    n = rng.randint(7, 10)
    pts = []
    for k in range(n):
        a = 2 * math.pi * k / n + rng.uniform(-0.22, 0.22)
        r = size * rng.uniform(0.6, 1.0) * (1.2 if math.sin(a) < -0.3 else 1.0)  # heavier bottom
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a) * 0.78))
    lit = [(pts[k], pts[(k + 1) % n]) for k in range(n)
           if (pts[k][1] + pts[(k + 1) % n][1]) / 2 < cy - size * 0.15]
    facet_fill(sc, pts, layer, groups, lit_edges=lit, near=max(20.0, size * 1.0), growth=0.8,
               far=size * 1.4, lit_range=size * 1.1, seed=seed, palette=palette)
    if rim:
        for a, b in lit:
            sc.seg(a, b, 1.6, sc.ch(rim_ch), z, -5, groups, "rim", extend=1.2)
        p = (cx + rng.uniform(-size * 0.3, size * 0.3), cy - size * 0.4)
        q = (cx + rng.uniform(-size * 0.2, size * 0.2), cy + size * 0.2)
        sc.seg(p, q, 1.3, sc.ch("crack"), z, -4, groups, "rim")
        sc.glow(cx, cy - size * 0.75, size * 1.7, sc.ch("glow_o"), z, -9, groups, "glow", kind="S")
    return pts


# ------------------------------------------------------------- lavafall
def lavafall(sc, top, bottom_y, rng, width=9.0):
    tx, ty = top
    bw = width * 1.9
    core = [(tx - width / 2, ty), (tx + width / 2, ty), (tx + bw / 2, bottom_y), (tx - bw / 2, bottom_y)]
    sc.gpoly(core, sc.ch("lava_top"), "b3")
    # hot seam + darker skin on both sides
    sc.seg((tx, ty - 2), (tx, bottom_y + 2), 2.0, sc.ch("crack_core"), B2, -20, (), "lava")
    sc.seg((tx - width / 2 - 1, ty), (tx - bw / 2 - 1, bottom_y), 2.4, sc.ch("lava_mid"), B2, -21, (),
           "lava")
    sc.seg((tx + width / 2 + 1, ty), (tx + bw / 2 + 1, bottom_y), 2.4, sc.ch("lava_mid"), B2, -21, (),
           "lava")
    y = ty - 20
    while y > bottom_y + 10:
        sc.glow(tx + rng.uniform(-3, 3), y, rng.uniform(46, 70), sc.ch("glow_o"), B2, -24, (), "lava",
                kind="S")
        y -= rng.uniform(40, 60)
    sc.glow(tx, ty - 4, 60, sc.ch("glow_hot"), B2, -18, (), "lava", kind="S")
    sc.glow(tx, bottom_y + 14, 200, sc.ch("glow_hot"), B2, -25, (), "lava")
    # falling droplets along the stream
    sc.particles(tx, ty - 6, particle_string(
        max_particles=40, lifetime=2.6, lifetime_var=0.4, emission=16, angle=270, angle_var=2,
        speed=40, speed_var=10, posvar_x=2.5, posvar_y=0, grav_x=0, grav_y=-120,
        start_size=3.2, start_size_var=1, end_size=2.0, end_size_var=0.5,
        start_r=1, start_g=0.85, start_b=0.45, start_a=1, end_r=1, end_g=0.35, end_b=0.08, end_a=0.6,
        fade_in=0.05, fade_out=0.25, mode=0, mode2=0, additive=1, texture=TEX["circle"]), B2, -19)
    # splash at the impact + steam
    sc.particles(tx, bottom_y + 6, particle_string(
        max_particles=26, lifetime=0.7, lifetime_var=0.2, emission=30, angle=90, angle_var=55,
        speed=55, speed_var=25, posvar_x=6, posvar_y=0, grav_x=0, grav_y=-200,
        start_size=3, start_size_var=1, end_size=1, end_size_var=0.3,
        start_r=1, start_g=0.8, start_b=0.4, start_a=1, end_r=1, end_g=0.25, end_b=0.05, end_a=0,
        fade_in=0, fade_out=0.2, mode=0, mode2=0, additive=1, texture=TEX["circle"]), B2, -17)
    sc.particles(tx, bottom_y + 20, particle_string(
        max_particles=14, lifetime=3.0, lifetime_var=0.8, emission=4, angle=90, angle_var=18,
        speed=14, speed_var=5, posvar_x=10, posvar_y=4, grav_x=0, grav_y=4,
        start_size=14, start_size_var=4, end_size=34, end_size_var=8, start_spin=0, start_spin_var=180,
        start_r=0.22, start_g=0.07, start_b=0.06, start_a=0.45, end_r=0.1, end_g=0.03, end_b=0.03,
        end_a=0, fade_in=0.4, fade_out=1.2, mode=0, mode2=0, additive=0, texture=TEX["smoke_ball"]),
        B2, -26)


# ------------------------------------------------------------- bokeh
def bokeh(sc, x, y, w, h):
    sc.particles(x, y, particle_string(
        max_particles=5, lifetime=8, lifetime_var=2, emission=0.6, angle=90, angle_var=35,
        speed=5, speed_var=3, posvar_x=w, posvar_y=h, grav_x=0, grav_y=0.5,
        start_size=26, start_size_var=12, end_size=34, end_size_var=10,
        start_r=1, start_g=0.45, start_g_var=0.1, start_b=0.12, start_a=0.16, start_a_var=0.06,
        end_r=1, end_g=0.25, end_b=0.06, end_a=0, fade_in=1.5, fade_out=2.5,
        mode=0, mode2=0, additive=1, texture=TEX["circle"]), T3, 0)
