"""Minimal Geometry Dash 2.2 level writer.

Objects are written in the standard level-string format
(`1,<id>,2,<x>,3,<y>,...;`), the level string is gzipped and URL-safe
base64 encoded, and everything is wrapped in the plist dictionary that
GDShare / Geode level import expect for a .gmd file.

Property keys used here (see gddocs `level-string.md` and
flowvix/gd-info-explorer `schema.txt`):
  1 id, 2 x, 3 y, 4 flip x, 5 flip y, 6 rotation (CW), 21/22 main/detail
  colour, 24 z layer, 25 z order, 32 scale, 128/129 scale x/y, 57 groups,
  121 no touch, 64 don't fade, 67 don't enter, 96 no glow, 103 high detail.
"""

import base64
import gzip
from xml.sax.saxutils import escape

# Z layers (key 24).
B5, B4, B3, B2, B1, T1, T2, T3, T4 = -5, -3, -1, 1, 3, 5, 7, 9, 11

# Player speeds in units per second (30 units = 1 block).
SPEED = {0.5: 251.16, 1: 311.58, 2: 387.42, 3: 468.0, 4: 576.0}
SPEED_PORTAL = {0.5: 200, 1: 201, 2: 202, 3: 203, 4: 1334}
SPEED_START_KEY = {1: 0, 0.5: 1, 2: 2, 3: 3, 4: 4}  # kA4 enum

# Key order GD uses when it saves, so the output looks like an editor save.
_KEY_ORDER = [1, 2, 3, 4, 5, 6, 155, 156, 13, 20, 61, 21, 22, 24, 25, 32,
              128, 129, 41, 42, 43, 44, 57, 64, 67, 96, 103, 116, 121]


def _fmt(v):
    if isinstance(v, bool):
        return "1" if v else "0"
    if isinstance(v, float):
        if abs(v - round(v)) < 1e-9:
            return str(int(round(v)))
        s = f"{v:.4f}".rstrip("0").rstrip(".")
        return s if s not in ("-0", "") else "0"
    if isinstance(v, (list, tuple)):
        return ".".join(str(int(g)) for g in v)
    return str(v)


def b64(s):
    return base64.urlsafe_b64encode(s.encode("utf-8")).decode("ascii")


class Obj(dict):
    """A level object: a dict of property key -> value."""

    def encode(self):
        keys = [k for k in _KEY_ORDER if k in self]
        keys += sorted(k for k in self if k not in _KEY_ORDER)
        return ",".join(f"{k},{_fmt(self[k])}" for k in keys)


class Channel:
    def __init__(self, cid, rgb, opacity=1.0, blending=False, copy=None, hsv=None):
        self.cid, self.rgb, self.opacity = cid, rgb, opacity
        self.blending, self.copy, self.hsv = blending, copy, hsv

    def encode(self):
        r, g, b = self.rgb
        parts = [1, r, 2, g, 3, b, 11, 255, 12, 255, 13, 255, 4, -1, 6, self.cid,
                 7, _fmt(float(self.opacity)), 15, 1, 18, 0, 8, 1]
        if self.blending:
            parts += [5, 1]
        if self.copy is not None:
            parts += [9, self.copy]
            if self.hsv:
                parts += [10, self.hsv]
        return "_".join(str(p) for p in parts)


class Level:
    def __init__(self, name):
        self.name = name
        self.objects = []
        self.channels = {}
        self.start = {"kA2": 0, "kA3": 0, "kA4": 0, "kA6": 0, "kA7": 0,
                      "kA17": 0, "kA18": 0, "kA25": 0, "kA11": 0, "kA8": 0}
        self._next_group = 1

    # -- groups ---------------------------------------------------------
    def new_group(self):
        g = self._next_group
        self._next_group += 1
        return g

    # -- colours --------------------------------------------------------
    def channel(self, cid, rgb, opacity=1.0, blending=False, copy=None, hsv=None):
        self.channels[cid] = Channel(cid, rgb, opacity, blending, copy, hsv)
        return cid

    # -- objects --------------------------------------------------------
    def add(self, oid, x, y, **props):
        o = Obj()
        o[1] = oid
        o[2] = float(x)
        o[3] = float(y)
        for k, v in props.items():
            if v is None:
                continue
            o[_prop_key(k)] = v
        self.objects.append(o)
        return o

    # -- output ---------------------------------------------------------
    def level_string(self):
        colours = "|".join(c.encode() for _, c in sorted(self.channels.items())) + "|"
        start = dict(self.start)
        header = [("kS38", colours), ("kA13", 0), ("kA15", 0), ("kA16", 0), ("kA14", ""),
                  ("kA6", start["kA6"]), ("kA7", start["kA7"]), ("kA25", start["kA25"]),
                  ("kA17", start["kA17"]), ("kA18", start["kA18"]), ("kS39", 0),
                  ("kA2", start["kA2"]), ("kA3", start["kA3"]), ("kA8", start["kA8"]),
                  ("kA4", start["kA4"]), ("kA9", 0), ("kA10", 0), ("kA22", 0),
                  ("kA23", 0), ("kA24", 0), ("kA27", 1), ("kA40", 1), ("kA41", 1),
                  ("kA42", 1), ("kA28", 0), ("kA29", 0), ("kA31", 1), ("kA32", 1),
                  ("kA36", 0), ("kA43", 0), ("kA44", 0), ("kA45", 1), ("kA33", 1),
                  ("kA34", 1), ("kA35", 0), ("kA37", 1), ("kA38", 1), ("kA39", 1),
                  ("kA19", 0), ("kA26", 0), ("kA20", 0), ("kA21", 0), ("kA11", start["kA11"])]
        head = ",".join(f"{k},{v}" for k, v in header)
        body = ";".join(o.encode() for o in sorted(self.objects, key=lambda o: o[2]))
        return head + ";" + body + ";"

    def encoded_level_string(self):
        raw = self.level_string().encode("utf-8")
        return base64.urlsafe_b64encode(gzip.compress(raw, 9, mtime=0)).decode("ascii")

    def write_gmd(self, path, description, song_id, creator="", length=3, stars=10):
        entries = [
            ("kCEK", "i", 4),
            ("k2", "s", self.name),
            ("k3", "s", b64(description)),
            ("k4", "s", self.encoded_level_string()),
            ("k5", "s", creator),
            ("k13", "t", None),
            ("k21", "i", 2),
            ("k16", "i", 1),
            ("k23", "i", length),
            ("k45", "i", song_id),
            ("k48", "i", len(self.objects)),
            ("k50", "i", 45),
            ("k66", "i", stars),
            ("k104", "s", str(song_id)),
            ("kI1", "r", 0),
            ("kI2", "r", 150),
            ("kI3", "r", 1),
        ]
        out = ['<?xml version="1.0"?><plist version="1.0" gjver="2.0"><dict>']
        for k, t, v in entries:
            out.append(f"<k>{k}</k>")
            if t == "t":
                out.append("<t />")
            else:
                out.append(f"<{t}>{escape(str(v))}</{t}>")
        out.append("</dict></plist>")
        with open(path, "w", encoding="utf-8") as f:
            f.write("".join(out))


_NAMED = {
    "flip_x": 4, "flip_y": 5, "rot": 6, "r": 7, "g": 8, "b": 9, "duration": 10,
    "touch": 11, "checked": 13, "player1": 15, "blending": 17, "layer": 20,
    "color": 21, "color2": 22, "target_color": 23, "z": 24, "zorder": 25,
    "move_x": 28, "move_y": 29, "easing": 30, "text": 31, "scale": 32,
    "opacity": 35, "hsv_on": 41, "hsv": 43, "fade_in": 45, "hold": 46,
    "fade_out": 47, "copy_color": 50, "target": 51, "target_type": 52,
    "activate": 56, "groups": 57, "lock_px": 58, "lock_py": 59, "spawn": 62,
    "delay": 63, "dont_fade": 64, "dont_enter": 67, "degrees": 68, "x360": 69,
    "center": 71, "strength": 75, "easing_rate": 85, "multi": 87,
    "interval": 84, "no_glow": 96, "high_detail": 103, "no_effects": 116,
    "no_touch": 121, "sx": 128, "sy": 129, "mod_x": 143, "mod_y": 144,
    "particles": 145, "zoom": 371,
}


def _prop_key(k):
    if isinstance(k, int):
        return k
    if k.startswith("k") and k[1:].isdigit():
        return int(k[1:])
    return _NAMED[k]
