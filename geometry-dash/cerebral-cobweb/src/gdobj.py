"""Minimal Geometry Dash object model.

Objects start from the exact default string GD writes for that object ID
(gd_defaults.py) and get properties overridden by key number. Keys follow
gddocs / gd-info-explorer schema (see ../DESIGN.md for the key table used).
"""
from collections import OrderedDict

from gd_defaults import OBJECT_DEFAULT

# --- documented property keys -------------------------------------------------
ID, X, Y = 1, 2, 3
FLIP_X, FLIP_Y, ROT = 4, 5, 6
RED, GREEN, BLUE, DURATION = 7, 8, 9, 10
TOUCH_TRIG = 11
BLENDING = 17
EDITOR_L1, EDITOR_L2 = 20, 61
COLOR1, COLOR2 = 21, 22
TARGET_COLOR = 23
Z_LAYER, Z_ORDER = 24, 25
MOVE_X, MOVE_Y, EASING, EASE_RATE = 28, 29, 30, 85
TEXT = 31
SCALE = 32
OPACITY = 35
HSV1_ON, HSV1 = 41, 43
FADE_IN, HOLD, FADE_OUT = 45, 46, 47
PULSE_HSV_MODE, PULSE_HSV = 48, 49
COPY_COLOR = 50
TARGET = 51
PULSE_TARGET_TYPE = 52
GROUPS = 57
SPAWN_TRIG = 62
SPAWN_DELAY = 63
DONT_FADE, DONT_ENTER = 64, 67
DEGREES, TIMES360, LOCK_ROT = 68, 69, 70
SECOND_TARGET = 71
FOLLOW_XMOD, FOLLOW_YMOD = 72, 73
EXCLUSIVE = 86
MULTI_TRIG = 87
NO_GLOW = 96
HIGH_DETAIL = 103
NO_TOUCH = 121
SCALE_X, SCALE_Y = 128, 129
HIDE = 135
LOCK_CAM_X, LOCK_CAM_Y, MOD_X, MOD_Y = 141, 142, 143, 144
PARTICLE_DATA = 145
USE_OBJ_COLOR = 146
QUICK_START = 211
# gradient trigger
GRAD_BLEND, GRAD_LAYER = 174, 202
GRAD_BL, GRAD_BR, GRAD_TL, GRAD_TR = 203, 204, 205, 206
GRAD_VERTEX, GRAD_DISABLE, GRAD_ID = 207, 208, 209
GRAD_PREVIEW_OPACITY, GRAD_DISABLE_ALL = 456, 508
NO_PARTICLE = 507
NO_AUDIO_SCALE = 372

# Z layers (odd encoding, confirmed by Society's data: -5..11 used)
B5, B4, B3, B2, B1, T1, T2, T3, T4 = -5, -3, -1, 1, 3, 5, 7, 9, 11
# Gradient trigger layer enum (1-based, inferred from Society: 1 bg, 9 T1, 12 T4, 15 max)
GL = {"bg": 1, "mg": 2, "b5": 3, "b4": 4, "b3": 5, "b2": 6, "b1": 7, "p": 8,
      "t1": 9, "t2": 10, "t3": 11, "t4": 12, "g": 13, "ui": 14, "max": 15}


def fmt(v) -> str:
    if isinstance(v, bool):
        return "1" if v else "0"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, float):
        if v != v:  # NaN guard
            raise ValueError("NaN property value")
        s = f"{v:.4f}".rstrip("0").rstrip(".")
        return "0" if s in ("-0", "") else s
    if isinstance(v, (list, tuple)):
        return ".".join(str(int(g)) for g in v)
    return str(v)


class Obj:
    __slots__ = ("kv", "tag")

    def __init__(self, oid: int, x: float, y: float, tag: str = ""):
        base = OBJECT_DEFAULT.get(oid, f"1,{oid},2,0,3,0;").rstrip(";").split(",")
        self.kv = OrderedDict()
        for i in range(0, len(base) - 1, 2):
            self.kv[int(base[i])] = base[i + 1]
        self.kv[ID] = oid
        self.kv[X] = float(x)
        self.kv[Y] = float(y)
        self.tag = tag

    def set(self, key: int, val):
        self.kv[key] = val
        return self

    def get(self, key, default=None):
        return self.kv.get(key, default)

    def add_groups(self, *groups):
        cur = list(self.kv.get(GROUPS, []) or [])
        for g in groups:
            if g and g not in cur:
                cur.append(int(g))
        if len(cur) > 10:
            raise ValueError(f"object has more than 10 groups: {cur}")
        self.kv[GROUPS] = cur
        return self

    def to_str(self) -> str:
        return ",".join(f"{k},{fmt(v)}" for k, v in self.kv.items())

    @property
    def x(self):
        return float(self.kv[X])

    @property
    def y(self):
        return float(self.kv[Y])
