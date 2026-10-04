import sys, math, random, json
from gen import *
from phys import SPEED

L = Level()
W, C = L.W, L.C
PAL = []   # (x, name)

def portals(x, y, mode=None, speed=None, mini=None, grav=None):
    if mode: W.portal(x, y, mode)
    if speed: W.portal(x, y, 'speed', speed)
    if mini is not None: W.portal(x, y, 'mini', mini)
    if grav is not None: W.portal(x, y, 'grav', grav)

def ship_pts(spec):
    """spec: list of (blocks_step, y) -> cumulative"""
    out = []; b = 0
    for st, y in spec:
        b += st; out.append((b, y))
    return out

# ============ 1. cube 2x  (intro)  =========================================
PAL.append((0, 'violet'))
portals(45, 15, speed=2)
f, x = build_cube(L, 0, None, 2, 0, [
    ('W', 8), ('J', 1, 1), ('J', 1, 1.5), ('J', 2, 1), ('U', 1, 1, 1), ('J', 2, 0.5), ('U', 1, 1, 1),
    ('J', 3, 0.5), ('D', 1, 2), ('J', 2, 0.5), ('D', 1, 1), ('J', 1, 0.5), ('J', 3, 1), ('W', 2)])
assert f == 0, f
# ============ 2. ship 2x ===================================================
x = round(x / B) * B + 15
portals(x, 30, mode='ship')
PAL.append((x, 'cyan'))
pts = ship_pts([(0, 15), (4, 45), (5, 150), (6, 105), (6, 200), (5, 150), (6, 230), (7, 90), (6, 150),
                (5, 75), (6, 210), (6, 120), (5, 170), (6, 75), (6, 45)])
yc = build_track(L, x, x + pts[-1][0] * B + 60, 2, pts, 'ship', tol=30)
x = x + pts[-1][0] * B + 60
# ============ 3. wave 3x ===================================================
y = yc(x)
portals(x, y, mode='wave', speed=3)
PAL.append((x, 'pink'))
segs = [(2, 1), (2, -1), (3, 1), (3, -1), (2, 1), (1, -1), (2, 1), (4, -1), (2, 1), (2, -1), (2, 1), (2, -1),
        (4, 1), (1, -1), (1, 1), (1, -1), (1, 1), (4, -1), (2, 1), (2, -1), (3, 1), (2, -1), (1, 1), (3, -1),
        (2, 1), (2, -1), (1, 1), (1, -1), (2, 1), (3, -1), (1, 1)]
x, y, ywv = build_wave(L, x - 32, 3, y, segs, yend=80)
# ============ 4. ball 2x ===================================================
x = x + 15
portals(x, ywv(x), mode='ball', speed=2)
PAL.append((x, 'orange'))
x = build_ball(L, x, 2, [3, 6, 5, 6, 5, 7, 5, 6, 5, 6, 5, 6], f_row=2, c_row=6)
# ============ 5. cube 3x ===================================================
x = round(x / B) * B + 15
portals(x, 90, mode='cube', speed=3)
PAL.append((x, 'green'))
f, x = build_cube(L, x - 30, None, 3, 2, [
    ('W', 3), ('J', 2, 1), ('D', 1, 2), ('J', 3, 1), ('D', 1, 1), ('J', 2, 0.5), ('U', 1, 1, 2),
    ('J', 3, 0.5), ('D', 1, 1), ('J', 2, 0.5), ('U', 1, 1, 2), ('J', 3, 0.5), ('D', 1, 1), ('J', 2, 0.5), ('W', 2)])
assert f == 0, f
# ============ 6. ship 3x with gravity ======================================
x = round(x / B) * B + 15
portals(x, 30, mode='ship')
PAL.append((x, 'blue'))
pts = ship_pts([(0, 15), (5, 75), (6, 165), (7, 120), (7, 210), (8, 150), (7, 90), (7, 150), (6, 225),
                (8, 135), (7, 195), (7, 105), (8, 165), (7, 90), (6, 45), (4, 45)])
yc = build_track(L, x, x + pts[-1][0] * B + 60, 3, pts, 'ship', tol=32,
                 gravs=[(33, -1), (62, 1)])
x = x + pts[-1][0] * B + 60
# ============ 7. mini wave 2x ==============================================
y = yc(x)
portals(x, y, mode='wave', speed=2, mini=True)
PAL.append((x, 'red'))
segs = [(1, 1), (1, -1), (1, 1), (1, -1), (2, 1), (1, -1), (1, 1), (2, -1), (1, 1), (1, -1), (1, 1), (1, -1),
        (2, 1), (2, -1), (1, 1), (1, -1), (1, 1), (1, -1), (2, 1), (1, -1), (1, 1), (2, -1), (1, 1), (1, -1),
        (1, 1), (1, -1), (2, 1), (1, -1), (1, 1), (1, -1), (1, 1), (2, -1), (1, 1), (1, -1)]
x, y, ywv = build_wave(L, x - 32, 2, y, segs, mini=True, clr=16, yend=120)
# ============ 8. ufo 2x ====================================================
x = x + 15
portals(x, ywv(x), mode='ufo', mini=False)
PAL.append((x, 'yellow'))
pts = ship_pts([(0, 120), (5, 140), (6, 100), (6, 170), (6, 120), (6, 180), (6, 110), (6, 160), (6, 90), (6, 45), (4, 45)])
yc = build_track(L, x, x + pts[-1][0] * B + 60, 2, pts, 'ufo', tol=44)
x = x + pts[-1][0] * B + 60
# ============ 9. cube 1x (the moment) ======================================
x = round(x / B) * B + 15
portals(x, 30, mode='cube', speed=1)
PAL.append((x, 'white'))
f, x = build_cube(L, x - 30, None, 1, 0, [
    ('W', 3), ('J', 1, 1), ('J', 1, 1), ('U', 1, 1, 1), ('J', 1, 1), ('D', 1, 1), ('J', 2, 1), ('W', 1)])
assert f == 0, f
# ============ 10. wave 4x ==================================================
x = round(x / B) * B + 15
portals(x, 30, mode='wave', speed=4)
PAL.append((x, 'cyan2'))
segs = [(3, 1), (2, -1), (2, 1), (3, -1), (2, 1), (1, -1), (1, 1), (3, -1), (4, 1), (2, -1), (2, 1), (4, -1),
        (2, 1), (1, -1), (1, 1), (1, -1), (3, 1), (2, -1), (2, 1), (3, -1), (2, 1), (2, -1), (4, 1), (3, -1),
        (2, 1), (2, -1), (1, 1), (1, -1), (2, 1), (3, -1), (2, 1), (2, -1)]
x, y, ywv = build_wave(L, x - 32, 4, 15, segs, ylo=45, yend=120)
# ============ 11. ship 4x ==================================================
x = x + 15
y = ywv(x)
portals(x, y, mode='ship')
PAL.append((x, 'magenta'))
pts = ship_pts([(0, y), (6, 150), (8, 105), (8, 180), (9, 120), (8, 195), (9, 135), (8, 90), (8, 150), (8, 75), (6, 75)])
yc = build_track(L, x, x + pts[-1][0] * B + 60, 4, pts, 'ship', tol=34)
x = x + pts[-1][0] * B + 60
# ============ 12. ball 3x ==================================================
portals(x, yc(x), mode='ball', speed=3)
PAL.append((x, 'orange2'))
x = build_ball(L, x, 3, [3, 6, 6, 5, 6, 6, 5, 6, 6, 6], f_row=2, c_row=6)
# ============ 13. outro cube 1x ============================================
x = round(x / B) * B + 15
portals(x, 90, mode='cube', speed=1)
PAL.append((x, 'end'))
f, x = build_cube(L, x - 30, None, 1, 2, [('W', 3), ('J', 1, 1), ('D', 1, 1), ('J', 1, 1), ('D', 1, 1), ('W', 12)])

if __name__ == '__main__':
    from verify import verify, render
    end = x
    fails, res = verify(L, end)
    print('fails', len(fails), 'of', len(res))
    W.index()
    trajs = []
    for vi in (0, 2, 3, 5):
        p, tr, t, mc = simulate(W, C, vi, None, until=end, record=True)
        trajs.append(tr); print('vi', vi, 'dead', p.dead, 'minclr', round(mc, 1))
    for i in range(0, int(end), 3000):
        render(L, i, min(i + 3000, end + 60), f'out_{i // 3000}.png', 0.5, trajs)
    print('end', end, L.notes)

    from export import build_string, write_gmd
    s, n = build_string(L, PAL)
    open('level.txt', 'w').write(s)
    write_gmd('Inertia.gmd', 'Inertia', 'The third part of Moment and Gravity. Song: same as Fogbound.', s, n)
    print('objects', n)
