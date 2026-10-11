"""Shape and trigger helpers on top of gdlevel.Level.

Primitive geometry, measured from the reference levels (research/reference-levels.md):
  211 Colored Inner Square   30x30 solid fill, colour on key 21
  693 Decorative Colored Slope  30x30 right triangle; unflipped = solid bottom-right (ramp rising to the right),
                             flipX mirrors horizontally, flipY vertically
  1837 Large Quarter Circle  quadrant of a radius-30 disc; four copies at rotations 0/90/180/270 (clockwise),
                             placed on a 30x30 square, form a full disc centred on that square
All deco gets No Touch so it can never collide with the player.
"""
import math
from gdlevel import Z

SQUARE, SLOPE, QUARTER, GLOW_ORB, SPIKE, BLOCK = 211, 693, 1837, 1888, 8, 1


class Art:
    def __init__(self, lv, editor_layer=0):
        self.lv = lv
        self.el = editor_layer

    def _deco(self, oid, x, y, ch, z, zo, groups=None, hd=False, **kw):
        return self.lv.add(oid, round(x, 3), round(y, 3), color=ch, z_layer=Z[z], z_order=zo,
                           groups=groups, no_touch=1, dont_fade=1, dont_enter=1,
                           high_detail=1 if hd else None, editor_layer=self.el or None, **kw)

    # ---- shapes ---------------------------------------------------------------------------------
    def rect(self, x0, y0, x1, y1, ch, z='B2', zo=0, groups=None, hd=False):
        w, h = abs(x1 - x0), abs(y1 - y0)
        if w < 0.05 or h < 0.05:
            return None
        return self._deco(SQUARE, (x0 + x1) / 2, (y0 + y1) / 2, ch, z, zo, groups, hd,
                          scale_x=round(w / 30, 4), scale_y=round(h / 30, 4))

    def rrect(self, cx, cy, w, h, angle_deg, ch, z='B2', zo=0, groups=None, hd=False):
        """Rectangle rotated counter-clockwise by angle_deg (GD stores clockwise-positive)."""
        return self._deco(SQUARE, cx, cy, ch, z, zo, groups, hd, scale_x=round(w / 30, 4),
                          scale_y=round(h / 30, 4), rot=round(-angle_deg, 3) or None)

    def line(self, x0, y0, x1, y1, t, ch, z='T2', zo=0, groups=None, hd=False):
        L = math.hypot(x1 - x0, y1 - y0)
        ang = math.degrees(math.atan2(y1 - y0, x1 - x0))
        return self.rrect((x0 + x1) / 2, (y0 + y1) / 2, L, t, ang, ch, z, zo, groups, hd)

    def tri(self, x0, y0, x1, y1, corner, ch, z='B2', zo=0, groups=None, hd=False):
        """Right triangle filling box (x0,y0)-(x1,y1) with its right angle at corner br/bl/tr/tl."""
        w, h = abs(x1 - x0), abs(y1 - y0)
        fx = corner in ('bl', 'tl')
        fy = corner in ('tr', 'tl')
        return self._deco(SLOPE, (x0 + x1) / 2, (y0 + y1) / 2, ch, z, zo, groups, hd,
                          scale_x=round(w / 30, 4), scale_y=round(h / 30, 4),
                          flip_x=1 if fx else None, flip_y=1 if fy else None)

    def spire(self, cx, y0, w, h, ch, z='B3', zo=0, groups=None, hd=False):
        """Isosceles triangle (pointed roof / spire): base from cx-w/2..cx+w/2 at y0, apex at y0+h."""
        self.tri(cx - w / 2, y0, cx, y0 + h, 'br', ch, z, zo, groups, hd)
        self.tri(cx, y0, cx + w / 2, y0 + h, 'bl', ch, z, zo, groups, hd)

    def disc(self, cx, cy, r, ch, z='B5', zo=0, groups=None, hd=False):
        s = round(r / 30, 4)
        for rot, dx, dy in ((0, -1, 1), (90, 1, 1), (180, 1, -1), (270, -1, -1)):
            self._deco(QUARTER, cx + dx * r / 2, cy + dy * r / 2, ch, z, zo, groups, hd, scale=s, rot=rot or None)

    def glow(self, cx, cy, size, ch, z='B4', zo=0, groups=None, hd=True):
        return self._deco(GLOW_ORB, cx, cy, ch, z, zo, groups, hd, scale=round(size / 60, 4))

    def arch_window(self, cx, y0, w, h, ch, z, zo=0, groups=None, rim=None, rim_t=1.5, hd=False):
        """Gothic window: rectangle body + pointed top (the top is 0.75w tall)."""
        top = h - 0.75 * w
        self.rect(cx - w / 2, y0, cx + w / 2, y0 + top, ch, z, zo, groups, hd)
        self.spire(cx, y0 + top, w, 0.75 * w, ch, z, zo, groups, hd)
        if rim:
            self.rect(cx + w / 2 - rim_t, y0, cx + w / 2, y0 + top, rim, z, zo + 1, groups, hd)

    # ---- gameplay -------------------------------------------------------------------------------
    def solid(self, x0, y0, x1, y1, groups=None):
        """Hidden solid blocks (standard 30x30 block 1 with Hide) tiling the box. Box must be on the 30 grid
        relative to x0/y0; deco is drawn separately on top."""
        nx, ny = int(round((x1 - x0) / 30)), int(round((y1 - y0) / 30))
        for i in range(nx):
            for j in range(ny):
                self.lv.add(BLOCK, round(x0 + 15 + 30 * i, 3), round(y0 + 15 + 30 * j, 3), hide=1, groups=groups)

    def spike(self, x, y_base, ch=None, groups=None):
        return self.lv.add(SPIKE, round(x, 3), round(y_base + 15, 3), color=ch, groups=groups)

    # ---- triggers -------------------------------------------------------------------------------
    def _trig(self, oid, x, y=-345, **kw):
        return self.lv.add(oid, round(x, 3), y, interactible=1, dont_fade=1, dont_enter=1, **kw)

    def color_trigger(self, x, ch, rgb, dur=0.0, opacity=1.0, blending=False, y=-345):
        r, g, b = rgb
        return self._trig(899, x, y, red=r, green=g, blue=b, duration=float(dur), opacity=float(opacity),
                          blending=1 if blending else None, target_color=ch)

    def pulse(self, x, ch, rgb, fin, hold, fout, y=-375):
        r, g, b = rgb
        return self._trig(1006, x, y, target=ch, fade_in=float(fin), hold=float(hold), fade_out=float(fout),
                          red=r, green=g, blue=b)

    def parallax(self, x, group, mod, duration, y=-405):
        """Lock a group to the camera X by `mod` (0 = static world, 1 = glued to camera)."""
        return self._trig(901, x, y, target=group, move_x=0, move_y=0, duration=float(duration),
                          lock_cam_x=1, mod_x=float(mod))

    def hide_ground(self, x, y=-435):
        return self._trig(2899, x, y, opt_hide_ground=1, opt_hide_mg=1)

    def bpm_guide(self, x, bpm, bpb, speed_code, duration, y=-465):
        return self.lv.add(3642, round(x, 3), y, bpm=bpm, bpb=bpb, bpm_speed=speed_code or None,
                           duration=float(duration), dont_fade=1, dont_enter=1)

    def shake(self, x, strength, interval, duration, y=-495):
        return self._trig(1520, x, y, duration=float(duration), **{'75': float(strength), '84': float(interval)})

    def end(self, x, y=-345):
        return self._trig(3600, x, y)

    def start_pos(self, x, y, speed_code, mode=0, disabled=True):
        kv = dict(kA2=mode, kA3=0, kA8=0, kA4=speed_code, kA9=1, kA10=0, kA22=0, kA23=0, kA24=0, kA27=1,
                  kA40=1, kA48=0, kA41=1, kA42=1, kA28=0, kA29=0, kA31=1, kA32=1, kA36=0, kA43=0, kA44=0,
                  kA45=1, kA46=0, kA47=0, kA33=1, kA34=1, kA35=0, kA37=1, kA38=1, kA39=1, kA19=0, kA26=0,
                  kA20=0, kA21=1 if disabled else 0, kA11=0)
        return self.lv.add(31, round(x, 3), y, **kv)
