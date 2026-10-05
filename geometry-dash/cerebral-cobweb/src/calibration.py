"""Small test level that checks, in real GD, every convention the deco relies on.

Open it in the editor (Preview Mode ON, Preview Particles ON) and take one
screenshot of each labelled station, then playtest once.  Each station is
labelled with a number that matches VERIFY.md.
"""
import base64
import os

from deco_lib import Scene
from gdobj import Obj, B2, B3, B5, T1, T3, TEXT, COLOR1, Z_LAYER, SCALE_X, SCALE_Y, EDITOR_L1
from particles import particle_string, TEX
import gdlevel as gl

HERE = os.path.dirname(os.path.abspath(__file__))


def text(sc, x, y, s, scale=0.5):
    o = Obj(914, x, y)
    o.set(TEXT, base64.urlsafe_b64encode(s.encode()).decode())
    o.set(SCALE_X, scale)
    o.set(SCALE_Y, scale)
    o.set(Z_LAYER, T3)
    return sc.add(o)


def build_calibration():
    sc = Scene(group_start=200, channel_start=100)
    white = sc.chan("white", (255, 255, 255))
    red = sc.chan("red", (255, 40, 30))
    green = sc.chan("green", (40, 220, 60))
    blue = sc.chan("blue", (60, 120, 255))
    glow = sc.chan("glow", (255, 110, 30), 0.6, True)
    grid = sc.chan("grid", (90, 90, 90))

    # 30-unit reference grid behind everything (stations 1-6)
    for x in range(0, 1201, 30):
        sc.rect(x, 300, 1.0, 600, grid, B5, 0)
    for y in range(0, 601, 30):
        sc.rect(600, y, 1200, 1.0, grid, B5, 0)

    # 1: 211 square + thin rotated line (exact 30x30 and 2-unit line from (60,420) to (180,480))
    text(sc, 120, 560, "1 square 30x30 + line")
    sc.rect(75, 435, 30, 30, white, B2)
    sc.seg((60, 480), (180, 420), 2.0, red, B2)
    # 2: gradient triangle with corners at (240,420) (330,420) (285,510)
    text(sc, 285, 560, "2 gradient triangle")
    sc.gpoly([(240, 420), (330, 420), (285, 510)], green, "b2")
    for p in ((240, 420), (330, 420), (285, 510)):
        sc.rect(p[0], p[1], 4, 4, red, T1)
    # 3: glow orbs at scale 1 (large / medium / small) centred on grid crossings
    text(sc, 480, 560, "3 glow L / M / S scale 1")
    for x, k in ((420, "L"), (510, "M"), (570, "S")):
        o = Obj({"L": 1888, "M": 1886, "S": 1887}[k], x, 450)
        o.set(COLOR1, glow)
        o.set(Z_LAYER, B2)
        sc.add(o)
    # 4: layer order: B3 gradient square vs B2 red line vs B3 blue square object
    text(sc, 720, 560, "4 layers: green grad B3, red B2 above it")
    sc.gpoly([(660, 420), (780, 420), (780, 510), (660, 510)], green, "b3")
    sc.rect(720, 465, 140, 4, red, B2)
    # 5: particles: should rise (angle 90) from the marker; emitter width +-45 units
    text(sc, 900, 560, "5 particles rise, 90 units wide")
    sc.rect(900, 400, 90, 2, red, T1)
    sc.particles(900, 400, particle_string(
        max_particles=40, lifetime=2, lifetime_var=0, emission=20, angle=90, angle_var=0,
        speed=15, speed_var=0, posvar_x=22.5, posvar_y=0, start_size=6, start_size_var=0,
        end_size=6, end_size_var=0, start_r=1, start_g=1, start_b=1, start_a=1, end_r=1, end_g=1,
        end_b=1, end_a=1, mode=0, mode2=0, additive=0, texture=TEX["square"]), T1, 0,
        quick=True, high_detail=False)
    # 6: lock-to-camera parallax: the blue square should drift slower than the grid when playing
    text(sc, 1080, 560, "6 parallax 0.5 (playtest)")
    g = sc.group()
    sc.rect(1080, 450, 30, 30, blue, B2, groups=(g,))
    sc.lock_camera(3.0, g, 0.5, 0.0)
    return sc


def main():
    src = os.path.join(HERE, "..", "input", "Cerebral_Cobweb_layout.gmd")
    dst = os.path.join(HERE, "..", "out", "Cerebral_Cobweb_calibration.gmd")
    gmd = gl.GmdFile(src)
    header, _ = gl.split_level(gmd.level)
    sc = build_calibration()
    from build import apply_colors
    header = apply_colors(header, sc, {})
    level = header + ";" + ";".join(o.to_str() for o in sc.objs) + ";"
    xml = gmd.xml
    gmd.xml = xml.replace("<k>k2</k><s>Cerebral Cobweb</s>", "<k>k2</k><s>CC Deco Calibration</s>", 1)
    gmd.write(dst, level, len(sc.objs))
    print("wrote", os.path.abspath(dst), len(sc.objs), "objects")


if __name__ == "__main__":
    main()
