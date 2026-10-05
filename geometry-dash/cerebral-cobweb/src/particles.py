"""Particle string builder for the Custom Particles object (ID 2065, key 145).

Field order follows gddocs particle-string.md (72 'a'-separated values).
Starts from GD's own default particle string and overrides named fields.
Unit notes (GD Creator School particle guide): size 30 = 1 block,
speed 15 = 1 block/s, PosVar 15 = 1 block. Angle 90 = up (cocos2d convention,
supported by real level data: ground-level smoke emitters in Society use 90).
These are listed in the in-game verification checklist.
"""
FIELDS = [
    "max_particles", "duration", "lifetime", "lifetime_var", "emission",
    "angle", "angle_var", "speed", "speed_var", "posvar_x", "posvar_y",
    "grav_x", "grav_y", "accel_rad", "accel_rad_var", "accel_tan", "accel_tan_var",
    "start_size", "start_size_var", "start_spin", "start_spin_var",
    "start_r", "start_r_var", "start_g", "start_g_var", "start_b", "start_b_var",
    "start_a", "start_a_var",
    "end_size", "end_size_var", "end_spin", "end_spin_var",
    "end_r", "end_r_var", "end_g", "end_g_var", "end_b", "end_b_var",
    "end_a", "end_a_var",
    "fade_in", "fade_in_var", "fade_out", "fade_out_var",
    "start_rad", "start_rad_var", "end_rad", "end_rad_var", "rot_sec", "rot_sec_var",
    "mode", "mode2", "additive", "start_spin_eq_end", "start_rot_is_dir",
    "dynamic_rotation", "texture", "uniform_obj_color",
    "friction_p", "friction_p_var", "respawn", "respawn_var", "order_sensitive",
    "start_size_eq_end", "start_rad_eq_end", "start_rgb_var_sync", "end_rgb_var_sync",
    "friction_s", "friction_s_var", "friction_r", "friction_r_var",
]
assert len(FIELDS) == 72

GD_DEFAULT = ("30a-1a1a0.3a30a90a90a29a0a11a0a0a0a0a0a0a0a2a1a0a0a1a0a1a0a1a0a1a0a1a1a0a0a1a0"
              "a1a0a1a0a1a0a0a0a0a0a0a0a0a0a0a0a0a2a1a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0")

# Particle textures: index = (particle-shape object ID) - 3800 for the 38xx/39xx
# objects (e.g. 3802 Circle Particle -> 2, 3958 Glow Particle -> 158), 0 = square.
TEX = {"square": 0, "circle": 2, "triangle": 3, "glow_ball": 25, "flame": 26,
       "glow_point": 28, "smoke_ball": 29, "droplet": 30, "line": 33, "glow": 158,
       "thick_glow": 159, "very_thick_glow": 160, "smoke_cloud_1": 181, "smoke_cloud_3": 183}


def _num(v):
    if isinstance(v, float):
        s = f"{v:.4f}".rstrip("0").rstrip(".")
        return "0" if s in ("-0", "") else s
    return str(v)


def particle_string(**kw) -> str:
    vals = GD_DEFAULT.split("a")
    assert len(vals) == 72, len(vals)
    for k, v in kw.items():
        if k not in FIELDS:
            raise KeyError(k)
        vals[FIELDS.index(k)] = _num(v)
    return "a".join(vals)


def describe(s: str) -> dict:
    vals = s.split("a")
    return dict(zip(FIELDS, vals))
