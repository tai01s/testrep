"""Song time <-> level x. Cut song: 128 BPM, bar c starts at c * 1.875 s (see plan/SONG_MAP.md)."""
from gdlevel import SPEED_UPS

BEAT = 60 / 128.0
BAR = 4 * BEAT


def T(bar, beat=1, eighth=0):
    """Time of cut bar `bar`, beat `beat` (1-4), optionally +1 eighth note."""
    return bar * BAR + (beat - 1) * BEAT + eighth * BEAT / 2


class Track:
    """Piecewise-constant speed. segments: list of (start_time, speed_name), first at t=0.
    Assumes the player starts at x=0 when the song starts (offset 0) and portals act at their x."""

    def __init__(self, segments):
        self.seg = []
        x = 0.0
        for i, (t0, sp) in enumerate(segments):
            if i:
                pt, psp = segments[i - 1]
                x += SPEED_UPS[psp] * (t0 - pt)
            self.seg.append((t0, x, sp))

    def x(self, t):
        cur = self.seg[0]
        for s in self.seg:
            if s[0] <= t:
                cur = s
        t0, x0, sp = cur
        return x0 + SPEED_UPS[sp] * (t - t0)

    def speed(self, t):
        cur = self.seg[0]
        for s in self.seg:
            if s[0] <= t:
                cur = s
        return cur[2]

    def t(self, x):
        cur = self.seg[0]
        for s in self.seg:
            if s[1] <= x:
                cur = s
        t0, x0, sp = cur
        return t0 + (x - x0) / SPEED_UPS[sp]
