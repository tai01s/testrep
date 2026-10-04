"""Gameplay layout for Fogbound, section by section.

Units: cells are 30x30. Cell (i, j) spans x in [30i, 30i+30] and y in
[30j, 30j+30]; the GD ground top is y = 0. Each section method takes the
starting column and returns the column where it ends. Speed changes are
recorded in `timeline` as (x, units per second) so the solver and the
decoration triggers agree on timing.
"""

from gdlevel import SPEED

C = 30.0


def xc(i):
    return i * C + 15.0


class Layout:
    def __init__(self, world, start_speed=2):
        self.w = world
        self.timeline = [(0.0, SPEED[start_speed])]
        self.sections = []   # dicts: name, i0, i1, mode, speed
        self.events = []     # (x, name) moments decor can react to

    # ----------------------------------------------------------- helpers
    def speed(self, i, sp, y):
        x = xc(i)
        self.w.portal("speed", sp, x, y)
        self.timeline.append((x, SPEED[sp]))

    def mark(self, name, i0, i1, mode, sp):
        self.sections.append({"name": name, "i0": i0, "i1": i1, "mode": mode, "speed": sp})

    def zigzag(self, i, start_row, segs, slope=1, lead=6, lead_h=4, tail=6, tail_h=4):
        """Wave corridor around a zigzag centreline starting at column i.

        segs: [(dy_rows, half_gap_rows), ...]; each segment is |dy|/slope
        columns long. Returns (end_column, exit_row).
        """
        floor, ceil = [(lead, start_row - lead_h, start_row - lead_h)], \
                      [(lead, start_row + lead_h, start_row + lead_h)]
        row = start_row
        for dy, h in segs:
            n = abs(dy) // slope
            assert n * slope == abs(dy), "segment must fit the wave angle"
            floor.append((n, row - h, row + dy - h))
            ceil.append((n, row + h, row + dy + h))
            row += dy
            assert h <= row <= 10 - h, f"zigzag leaves the corridor at row {row}"
        floor.append((tail, row - tail_h, row - tail_h))
        ceil.append((tail, row + tail_h, row + tail_h))
        end = self.w.wall(i, floor, below=True)
        self.w.wall(i, ceil, below=False)
        return end, row

    # ============================================================ sections
    def intro(self, i):
        """Cube 2x: readable opener under the title card."""
        w, i0 = self.w, i
        w.spike(i + 16, 0)
        w.spikes(i + 22, 2, 0)
        w.fill(i + 28, i + 33, 0, 1)
        w.spikes(i + 33, 2, 0)
        w.spikes(i + 39, 4, 0)
        w.orb("yellow", xc(i + 40) + 15, 80)
        w.fill(i + 48, i + 52, 0, 1)
        w.fill(i + 52, i + 60, 0, 2)
        w.spike(i + 56, 2)
        w.spikes(i + 60, 2, 0)
        w.fill(i + 67, i + 70, 0, 1)
        w.spikes(i + 70, 3, 0)
        i += 76
        self.mark("intro", i0, i, "cube", 2)
        return i

    def cube_fast(self, i):
        """Cube 3x: orb flips, gravity portals, spike rhythm."""
        w, i0 = self.w, i
        self.speed(i, 3, 15)
        i += 4
        w.spike(i + 3, 0)
        w.spikes(i + 9, 2, 0)
        # blue orb up onto a ceiling run over a spike floor
        w.orb("blue", xc(i + 15), 38)
        w.fill(i + 13, i + 41, 6, 8)
        w.spikes(i + 17, 23, 0)
        w.spike(i + 24, 5, down=True)
        w.spikes(i + 31, 2, 5, down=True)
        w.orb("blue", xc(i + 39), 165)
        i += 42
        w.spike(i + 5, 0)
        w.fill(i + 8, i + 12, 0, 1)
        w.spikes(i + 12, 2, 0)
        w.fill(i + 14, i + 18, 0, 1)
        w.spike(i + 16, 1)
        w.spikes(i + 18, 7, 0)
        w.orb("yellow", xc(i + 21), 90)
        i += 28
        # gravity portals
        w.portal("gravity", "flip", xc(i + 2), 45)
        w.fill(i + 1, i + 27, 6, 8)
        w.spikes(i + 4, 20, 0)
        w.spike(i + 10, 5, down=True)
        w.spikes(i + 16, 2, 5, down=True)
        w.portal("gravity", "normal", xc(i + 23), 150)
        i += 30
        for k in range(4):
            w.spike(i + 3 + 7 * k, 0)
            if k % 2:
                w.spike(i + 4 + 7 * k, 0)
        i += 32
        self.mark("cube-3x", i0, i, "cube", 3)
        return i

    def ship(self, i, sp=2):
        """Ship: wide-slope corridor with spikes and a straight fly."""
        w, i0 = self.w, i
        w.portal("mode", "ship", xc(i), 45)
        self.speed(i + 1, sp, 45)
        # (length, floor_from, floor_to, gap)
        segs = [(6, 0, 0, 6), (8, 0, 4, 4), (8, 4, 4, 3), (4, 4, 2, 3), (8, 2, 2, 3),
                (8, 2, 6, 3), (6, 6, 6, 3), (8, 6, 2, 3), (8, 2, 2, 3), (4, 2, 4, 3),
                (16, 4, 4, 2), (8, 4, 0, 3), (10, 0, 0, 5)]
        c0 = i + 2
        w.wall(c0, [(n, a, b) for n, a, b, g in segs], below=True)
        w.wall(c0, [(n, a + g, b + g) for n, a, b, g in segs], below=False)
        w.spike(c0 + 32, 2)
        w.spike(c0 + 36, 2)
        w.spike(c0 + 46, 8, down=True)
        w.spike(c0 + 49, 8, down=True)
        w.spike(c0 + 62, 2)
        w.spike(c0 + 65, 2)
        i = c0 + sum(s[0] for s in segs)
        self.mark("ship", i0, i, "ship", sp)
        return i

    def wave(self, i, sp=3, row=4):
        """Normal wave 3x: mixed 2-row and 4-row gaps with spam bursts."""
        w, i0 = self.w, i
        w.portal("mode", "wave", xc(i), row * C)
        self.speed(i + 1, sp, row * C)
        segs = [(+3, 2), (-3, 2), (+4, 2), (-2, 2), (+1, 1), (-1, 1), (+1, 1), (-1, 1),
                (-1, 1), (+3, 2), (-4, 2), (+2, 1), (-1, 1), (+2, 1), (-2, 2), (+3, 2),
                (-2, 1), (+1, 1), (-1, 1), (+1, 1), (-3, 2), (+3, 2), (-1, 1), (+1, 1),
                (-1, 1), (+2, 2), (-4, 2), (+3, 2), (-2, 1), (+2, 1), (-1, 1), (+1, 1),
                (-2, 2)]
        i, out = self.zigzag(i + 2, row, segs)
        self.mark("wave", i0, i, "wave", sp)
        return i, out

    def ball(self, i, sp=3, row_in=4):
        """Ball 3x between the floor and a ceiling at row 6."""
        w, i0 = self.w, i
        w.portal("mode", "ball", xc(i), row_in * C)
        n = 96
        w.fill(i + 1, i + n, 6, 8)
        # alternating hazard runs: (surface, start, length)
        runs = [("floor", 9, 6), ("ceil", 19, 5), ("floor", 29, 4), ("ceil", 37, 4),
                ("floor", 45, 5), ("ceil", 54, 3), ("floor", 61, 3), ("ceil", 68, 4),
                ("floor", 77, 5), ("ceil", 87, 8)]
        for surf, s, ln in runs:
            if surf == "floor":
                w.spikes(i + s, ln, 0)
            else:
                w.spikes(i + s, ln, 5, down=True)
        i += n
        self.mark("ball", i0, i, "ball", sp)
        return i

    def spider(self, i, sp=3):
        """Spider 3x: alternating spike lanes, 3-cell click windows."""
        w, i0 = self.w, i
        w.portal("mode", "spider", xc(i), 15)
        n = 100
        w.fill(i + 1, i + n, 5, 7)
        c = i + 6
        lanes = [("floor", 5), ("ceil", 4), ("floor", 3), ("ceil", 6), ("floor", 2),
                 ("ceil", 2), ("floor", 5), ("ceil", 3), ("floor", 4), ("ceil", 5),
                 ("floor", 2), ("ceil", 4), ("floor", 3)]
        gaps = [3, 3, 4, 3, 3, 3, 4, 3, 3, 3, 3, 4]
        for k, (surf, ln) in enumerate(lanes):
            if surf == "floor":
                w.spikes(c, ln, 0)
            else:
                w.spikes(c, ln, 4, down=True)
            c += ln + (gaps[k] if k < len(gaps) else 0)
        # end on the floor: ceiling spikes to the end of the ceiling
        w.spikes(c + 3, i + n - (c + 3), 4, down=True)
        i += n
        self.mark("spider", i0, i, "spider", sp)
        return i

    def drop(self, i):
        """The drop: 4x wave, then a 3x mini-wave burst."""
        w, i0 = self.w, i
        self.events.append((xc(i), "drop"))
        w.portal("mode", "wave", xc(i), 30)
        self.speed(i + 1, 4, 30)
        segs = [(+4, 2), (-2, 2), (+3, 2), (-4, 2), (+2, 2), (+2, 2), (-3, 2), (+2, 2),
                (-2, 2), (+4, 2), (-1, 1), (+1, 1), (-3, 2), (+3, 2), (-2, 2), (+2, 2),
                (-4, 2), (+3, 2), (-1, 2), (+2, 2), (-3, 2), (+3, 2), (-3, 2)]
        i, row = self.zigzag(i + 2, 2, segs, lead_h=2, tail_h=3)
        # mini wave burst
        w.portal("size", "mini", xc(i + 1), row * C)
        self.speed(i + 2, 3, row * C)
        self.events.append((xc(i + 1), "mini"))
        segs = [(+2, 3), (-4, 3), (+2, 3), (+2, 3), (-2, 3), (-2, 3), (+4, 3), (-2, 3),
                (-2, 3), (+2, 3), (+2, 3), (-4, 3), (+4, 3), (-2, 3), (-2, 3), (+2, 3)]
        i, row = self.zigzag(i, row, segs, slope=2, lead=4, lead_h=3, tail=4, tail_h=3)
        w.portal("size", "normal", xc(i - 2), row * C)
        self.mark("drop", i0, i, "wave", 4)
        return i, row

    def ship_fast(self, i, row_in=5):
        w, i0 = self.w, i
        w.portal("mode", "ship", xc(i), row_in * C)
        segs = [(6, 2, 2, 6), (4, 2, 4, 3), (8, 4, 4, 3), (8, 4, 0, 3), (6, 0, 0, 3),
                (8, 0, 4, 3), (4, 4, 6, 3), (10, 6, 6, 2), (8, 6, 2, 3), (6, 2, 2, 3),
                (4, 2, 4, 3), (8, 4, 4, 3), (8, 4, 0, 3), (10, 0, 0, 5)]
        c0 = i + 2
        w.wall(c0, [(n, a, b) for n, a, b, g in segs], below=True)
        w.wall(c0, [(n, a + g, b + g) for n, a, b, g in segs], below=False)
        w.spike(c0 + 13, 4)
        w.spike(c0 + 16, 6, down=True)
        w.spike(c0 + 28, 0)
        w.spike(c0 + 30, 2, down=True)
        w.spike(c0 + 62, 2)
        w.spike(c0 + 64, 4, down=True)
        w.spike(c0 + 66, 4)
        i = c0 + sum(s[0] for s in segs)
        self.mark("ship-3x", i0, i, "ship", 3)
        return i

    def cube_final(self, i):
        w, i0 = self.w, i
        w.portal("mode", "cube", xc(i), 45)
        i += 4
        w.spikes(i + 4, 3, 0)
        w.fill(i + 11, i + 15, 0, 1)
        w.spikes(i + 15, 2, 0)
        w.fill(i + 17, i + 21, 0, 1)
        w.fill(i + 19, i + 21, 1, 2)
        w.spikes(i + 21, 4, 0)
        # yellow orb chain over a long pit
        w.spikes(i + 32, 16, 0)
        w.orb("yellow", xc(i + 35), 75)
        w.orb("yellow", xc(i + 40), 80)
        w.orb("yellow", xc(i + 45), 80)
        i += 52
        # ceiling run with blue orbs
        w.orb("blue", xc(i + 2), 38)
        w.fill(i, i + 26, 6, 8)
        w.spikes(i + 4, 21, 0)
        w.spike(i + 9, 5, down=True)
        w.spikes(i + 15, 2, 5, down=True)
        w.orb("blue", xc(i + 22), 165)
        i += 30
        w.spike(i + 2, 0)
        w.spikes(i + 8, 3, 0)
        w.spike(i + 15, 0)
        i += 22
        self.mark("cube-final", i0, i, "cube", 3)
        return i

    def outro(self, i):
        i0 = i
        self.speed(i, 1, 15)
        i += 34
        self.mark("outro", i0, i, "cube", 1)
        return i
