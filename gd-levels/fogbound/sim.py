"""Reachability check for the generated gameplay.

This is not GD's exact physics engine. It is a conservative approximation
(bigger hitboxes than the game, death on any solid contact the game would
forgive, padded spike boxes) used to search every input sequence tick by
tick (breadth first, deduplicated states) and confirm at least one path
reaches the end. Running it with several physics variants (stronger or
weaker jumps and gravity, ship acceleration and so on) guards against
the parts where the constants are only approximately known.
"""

import math
import random

DT = 1.0 / 240.0
CELL = 30.0

BASE = {
    "g": 2794.0, "vj": 603.7, "vfall": 900.0,
    "orb_yellow": 1.0, "orb_pink": 0.72, "blue_v": 0.5, "grav_v": 0.3,
    "ball_g": 0.6, "ball_v": 0.35, "spider_g": 0.6,
    "ship_au": 1300.0, "ship_ad": 1300.0, "ship_vu": 380.0, "ship_vd": 430.0,
    "wave_hw": 7.0, "mini_wave_hw": 5.0,
}

VARIANTS = {
    "base": {},
    "low-jump": {"vj": 603.7 * 0.95, "g": 2794.0 * 1.04},
    "high-jump": {"vj": 603.7 * 1.05, "g": 2794.0 * 0.96},
    "heavy": {"g": 2794.0 * 1.08, "ball_g": 0.7, "spider_g": 0.7, "blue_v": 0.8,
              "ship_au": 1700.0, "ship_ad": 1700.0, "ship_vu": 460.0, "ship_vd": 520.0},
    "floaty": {"g": 2794.0 * 0.93, "ball_g": 0.5, "spider_g": 0.5, "blue_v": 0.2,
               "ship_au": 1000.0, "ship_ad": 1000.0, "ship_vu": 330.0, "ship_vd": 380.0},
}

HALF = {"cube": (15, 15), "ship": (15, 13), "ball": (15, 15), "spider": (15, 15)}


class Collider:
    def __init__(self, rects, tris, hazards):
        self.solid_cols = {}
        self.haz_cols = {}
        for r in rects:
            self._put(self.solid_cols, r, ("r", r))
        for t in tris:
            xs = [p[0] for p in t]
            ys = [p[1] for p in t]
            self._put(self.solid_cols, (min(xs), min(ys), max(xs), max(ys)), ("t", t))
        for h in hazards:
            self._put(self.haz_cols, h, ("r", h))

    @staticmethod
    def _put(table, bb, item):
        for c in range(int(bb[0] // CELL) - 1, int(bb[2] // CELL) + 2):
            table.setdefault(c, []).append((bb, item))

    def _query(self, table, x0, y0, x1, y1):
        out = []
        seen = set()
        for c in range(int(x0 // CELL), int(x1 // CELL) + 1):
            for bb, item in table.get(c, ()):
                if id(item) in seen:
                    continue
                if bb[0] < x1 and bb[2] > x0 and bb[1] < y1 and bb[3] > y0:
                    if item[0] == "r" or tri_box(item[1], x0, y0, x1, y1):
                        seen.add(id(item))
                        out.append(item)
        return out

    def solids(self, x0, y0, x1, y1):
        return self._query(self.solid_cols, x0, y0, x1, y1)

    def hazard(self, x0, y0, x1, y1):
        return bool(self._query(self.haz_cols, x0, y0, x1, y1))


def tri_box(tri, x0, y0, x1, y1):
    """Separating-axis test: triangle vs axis-aligned box (strict overlap)."""
    box = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    axes = [(1, 0), (0, 1)]
    for k in range(3):
        a, b = tri[k], tri[(k + 1) % 3]
        axes.append((-(b[1] - a[1]), b[0] - a[0]))
    for ax in axes:
        p1 = [ax[0] * p[0] + ax[1] * p[1] for p in tri]
        p2 = [ax[0] * p[0] + ax[1] * p[1] for p in box]
        if max(p1) <= min(p2) + 1e-6 or max(p2) <= min(p1) + 1e-6:
            return False
    return True


class Sim:
    def __init__(self, world, timeline, params, x_start, start_state, x_end, cap=2500):
        rects, tris = world.shapes()
        self.col = Collider(rects, tris, world.hazards)
        self.world = world
        self.timeline = timeline   # sorted list of (x, speed)
        self.P = dict(BASE)
        self.P.update(params)
        self.x_start, self.x_end = x_start, x_end
        self.start_state = start_state
        self.cap = cap
        self.portals = sorted(world.portals, key=lambda p: p["x"])
        self.orbs = world.orbs

    def speed_at(self, x):
        v = self.timeline[0][1]
        for px, sp in self.timeline:
            if x >= px:
                v = sp
        return v

    # state: (y, vy, grav, grounded, mode, mini, used_orb, hold)
    def run(self, rng_seed=1):
        rng = random.Random(rng_seed)
        P = self.P
        x = self.x_start
        states = {self._key(self.start_state): self.start_state}
        portal_idx = 0
        while portal_idx < len(self.portals) and self.portals[portal_idx]["x"] < x:
            portal_idx += 1
        best_front = x
        last_alive = None
        while x < self.x_end:
            v = self.speed_at(x)
            nx = x + v * DT
            new = {}
            for s in states.values():
                for ns in self._step(s, x, nx, v):
                    k = self._key(ns)
                    if k not in new:
                        new[k] = ns
            # portals crossed this tick
            while portal_idx < len(self.portals) and self.portals[portal_idx]["x"] <= nx:
                p = self.portals[portal_idx]
                portal_idx += 1
                passed = {}
                for k, s in new.items():
                    ns = self._portal(s, p)
                    if ns is not None:
                        passed[self._key(ns)] = ns
                new = passed
            if not new:
                return False, x, last_alive
            if len(new) > self.cap:
                keys = list(new.keys())
                rng.shuffle(keys)
                # keep diversity: sort by y and sample evenly, plus random
                vals = sorted(new.values(), key=lambda s: (s[4], s[0], s[1]))
                step = len(vals) / (self.cap * 0.7)
                keep = {self._key(vals[int(i * step)]): vals[int(i * step)]
                        for i in range(int(self.cap * 0.7))}
                for k in keys[: int(self.cap * 0.3)]:
                    keep[k] = new[k]
                new = keep
            states = new
            last_alive = (nx, sorted(set(round(s[0]) for s in states.values()))[:12])
            x = nx
            best_front = x
        return True, best_front, last_alive

    @staticmethod
    def _key(s):
        y, vy, grav, grounded, mode, mini, used, hold = s
        if mode == "wave":
            return (round(y * 2), grav, mode, mini, hold)
        if mode == "ship":
            return (round(y), round(vy / 12), grav, mode, mini, hold)
        return (round(y * 2), round(vy / 6), grav, grounded, mode, mini, used)

    def _half(self, mode, mini):
        if mode == "wave":
            h = self.P["mini_wave_hw"] if mini else self.P["wave_hw"]
            return h, h
        hw, hh = HALF[mode]
        return (hw / 2, hh / 2) if mini else (hw, hh)

    def _portal(self, s, p):
        y, vy, grav, grounded, mode, mini, used, hold = s
        if abs(y - p["y"]) > 42:
            return None  # missed the portal: treat as a failed attempt
        k, val = p["kind"], p["value"]
        if k == "mode":
            if val != mode:
                vy *= 0.5
                grounded = False
            mode = val
        elif k == "gravity":
            ng = -1 if val == "flip" else 1
            if ng != grav:
                grav = ng
                vy = -grav * self.P["grav_v"] * self.P["vj"]
                grounded = False
        elif k == "size":
            mini = val == "mini"
        return (y, vy, grav, grounded, mode, mini, used, hold)

    # ------------------------------------------------------------------
    def _step(self, s, x, nx, v):
        mode = s[4]
        if mode == "wave":
            return self._step_wave(s, nx, v)
        if mode == "ship":
            return self._step_ship(s, nx)
        return self._step_ground(s, x, nx)

    def _alive_box(self, x, y, hw, hh, allow_bounds):
        x0, y0, x1, y1 = x - hw, y - hh, x + hw, y + hh
        if self.col.hazard(x0, y0, x1, y1):
            return False
        if self.col.solids(x0, y0, x1, y1):
            return False
        return True

    def _step_wave(self, s, nx, v):
        y, vy, grav, grounded, mode, mini, used, hold = s
        h = self._half(mode, mini)[0]
        slope = 2.0 if mini else 1.0
        out = []
        for hold_ in (0, 1):
            dirn = (1 if hold_ else -1) * grav
            ny = y + dirn * slope * v * DT
            ny = min(max(ny, h), 300 - h)
            if self._alive_box(nx, ny, h, h, True):
                out.append((ny, 0.0, grav, False, mode, mini, used, hold_))
        return out

    def _step_ship(self, s, nx):
        y, vy, grav, grounded, mode, mini, used, hold = s
        P = self.P
        hw, hh = self._half(mode, mini)
        out = []
        for hold_ in (0, 1):
            a = (P["ship_au"] if hold_ else -P["ship_ad"]) * grav
            nvy = vy + a * DT
            nvy = max(-P["ship_vd"], min(P["ship_vu"], nvy)) if grav > 0 else \
                max(-P["ship_vu"], min(P["ship_vd"], nvy))
            ny = y + nvy * DT
            if ny < hh:
                ny, nvy = hh, max(nvy, 0.0)
            if ny > 300 - hh:
                ny, nvy = 300 - hh, min(nvy, 0.0)
            if self._alive_box(nx, ny, hw, hh, True):
                out.append((ny, nvy, grav, False, mode, mini, used, hold_))
        return out

    def _step_ground(self, s, x, nx):
        """cube / ball / spider: branch on every useful click."""
        y, vy, grav, grounded, mode, mini, used, hold = s
        P = self.P
        hw, hh = self._half(mode, mini)
        options = [s]
        if grounded:
            if mode == "cube":
                options.append((y, grav * P["vj"], grav, False, mode, mini, used, 0))
            elif mode == "ball":
                ng = -grav
                options.append((y, -ng * P["ball_v"] * P["vj"], ng, False, mode, mini, used, 0))
            elif mode == "spider":
                t = self._spider_target(x, y, grav, hw, hh)
                if t is not None:
                    options.append((t, 0.0, -grav, True, mode, mini, used, 0))
        for idx, o in enumerate(self.orbs):
            if idx == used:
                continue
            if abs(o["x"] - x) < hw + 14 and abs(o["y"] - y) < hh + 14:
                k = o["kind"]
                if k in ("yellow", "pink"):
                    f = P["orb_yellow"] if k == "yellow" else P["orb_pink"]
                    options.append((y, grav * f * P["vj"], grav, False, mode, mini, idx, 0))
                elif k == "blue":
                    ng = -grav
                    options.append((y, -ng * P["blue_v"] * P["vj"], ng, False, mode, mini, idx, 0))
        out = []
        g = P["g"] * (P["ball_g"] if mode == "ball" else P["spider_g"] if mode == "spider" else 1.0)
        for (y, vy, grav, grounded, mode, mini, used, hold) in options:
            if grounded:
                ny, nvy = y, 0.0
            else:
                nvy = vy - grav * g * DT
                nvy = max(-P["vfall"], min(P["vfall"], nvy))
                ny = y + nvy * DT
            res = self._resolve(nx, y, ny, nvy, grav, hw, hh)
            if res is None:
                continue
            ny, nvy, ng = res
            if ny > 900 or ny < -50:
                continue
            out.append((ny, nvy, grav, ng, mode, mini, used, 0))
        return out

    def _resolve(self, x, py, y, vy, grav, hw, hh):
        """Land on surfaces; return (y, vy, grounded) or None on death."""
        tol = abs(vy) * DT + 4.0
        grounded = False
        if grav > 0 and y - hh < 0:
            y, vy, grounded = hh, 0.0, True
        hits = self.col.solids(x - hw, y - hh, x + hw, y + hh)
        for kind, sh in hits:
            if kind != "r":
                return None
            x0, y0, x1, y1 = sh
            if grav > 0 and vy <= 0 and (py - hh) >= y1 - tol:
                y, vy, grounded = y1 + hh, 0.0, True
            elif grav < 0 and vy >= 0 and (py + hh) <= y0 + tol:
                y, vy, grounded = y0 - hh, 0.0, True
            else:
                return None
        if hits and self.col.solids(x - hw, y - hh + 0.01, x + hw, y + hh - 0.01):
            return None
        if self.col.hazard(x - hw, y - hh, x + hw, y + hh):
            return None
        if not grounded:
            # standing on something exactly? (walking along a surface)
            probe = -1.0 if grav > 0 else 1.0
            if grav > 0 and abs(y - hh) < 0.01:
                grounded = True
            elif self.col.solids(x - hw, y - hh + probe, x + hw, y + hh + probe) and vy * grav <= 0:
                grounded = True
        return y, vy, grounded

    def _spider_target(self, x, y, grav, hw, hh):
        best = None
        for c in range(int((x - hw) // CELL), int((x + hw) // CELL) + 1):
            for bb, (kind, sh) in self.col.solid_cols.get(c, ()):
                if not (bb[0] < x + hw and bb[2] > x - hw):
                    continue
                if grav > 0 and bb[1] >= y + hh - 0.5:
                    cand = bb[1] - hh
                    if best is None or cand < best:
                        best = cand
                if grav < 0 and bb[3] <= y - hh + 0.5:
                    cand = bb[3] + hh
                    if best is None or cand > best:
                        best = cand
        if best is None and grav < 0:
            best = hh  # GD ground
        return best
