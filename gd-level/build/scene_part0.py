"""Part 0 deco: the bridge approach (cut bars 0-6). Moonlit gothic castle, blue-black, no accent colour.

Layers (rulebook 6.3) and parallax (Move trigger, Lock to Camera X with mod m):
  FAR     B5  stars, moon, halo            m=0.96
  HILLS   B4  two hill ranges              m=0.88
  CASTLE  B4  castle on its hill           m=0.78
  MIST    B3  mist bands (blending)        m=0.65
  CHASM   B3  cliffs below the bridge      m=0.40
  near    B2/B1/T1/T2  bridge, stairs, rampart (no parallax)
A parallax object at world x0 shows at player-relative screen offset  x0 - (1 - m) * c  when the player is at c.
"""
import random
from timeline import T
from part0_gameplay import TRACK

FAR, HILLS, CASTLE, MIST, CHASM = 101, 102, 103, 104, 105
MODS = {FAR: 0.96, HILLS: 0.88, CASTLE: 0.78, MIST: 0.65, CHASM: 0.40}

# colour channels (rulebook 6.4 ranges)
C = dict(WHITE=1, BLACK=2, INVIS=3,
         RIM=10, RIM_DIM=11, STONE=12, JOINT=13, STONE_LIT=14,
         HILLS_BACK=20, HILLS_FRONT=21, HILLS_RIM=22, CASTLE=23, CASTLE_LIT=24, WINDOW=25, GLINT=26,
         CLIFF=27, CLIFF_LIT=28, PIER=29, PIER_LIT=30, STAR=31, STAR_DIM=32,
         MOON=40, MOON_SHADE=41, HALO=42, HALO_OUT=43, MIST=44, SKYGLOW=45, ARCHLIGHT=46, MERLON=50, MERLON_LIT=51)

BG = (4, 6, 15)
PALETTE = {
    C['WHITE']: ((255, 255, 255), 1, False), C['BLACK']: ((0, 0, 0), 1, False), C['INVIS']: ((0, 0, 0), 1, True),
    C['RIM']: ((207, 232, 255), 1, False), C['RIM_DIM']: ((96, 132, 196), 1, False),
    C['STONE']: ((6, 9, 18), 1, False), C['JOINT']: ((15, 23, 44), 1, False), C['STONE_LIT']: ((19, 30, 58), 1, False),
    C['HILLS_BACK']: ((11, 18, 40), 1, False), C['HILLS_FRONT']: ((6, 9, 20), 1, False),   # far = lighter (atmosphere)
    C['HILLS_RIM']: ((22, 36, 72), 1, False),
    C['CASTLE']: ((9, 14, 31), 1, False), C['CASTLE_LIT']: ((26, 42, 86), 1, False),
    C['WINDOW']: ((3, 5, 11), 1, False), C['GLINT']: ((52, 86, 160), 1, False),
    C['CLIFF']: ((5, 8, 18), 1, False), C['CLIFF_LIT']: ((13, 21, 43), 1, False),
    C['PIER']: ((5, 8, 16), 1, False), C['PIER_LIT']: ((17, 27, 54), 1, False),
    C['STAR']: ((176, 200, 255), 1, False), C['STAR_DIM']: ((176, 200, 255), 0.45, False),
    C['MOON']: ((226, 238, 255), 1, False), C['MOON_SHADE']: ((188, 208, 242), 1, False),
    C['HALO']: ((36, 84, 196), 0.6, True), C['HALO_OUT']: ((18, 42, 110), 0.55, True),
    C['MIST']: ((24, 44, 96), 0.35, True), C['SKYGLOW']: ((12, 24, 62), 0.7, True),
    C['ARCHLIGHT']: ((22, 44, 104), 0.55, True),
    C['MERLON']: ((11, 17, 36), 1, False), C['MERLON_LIT']: ((24, 38, 76), 1, False),
}


def setup_colors(lv):
    lv.color(1000, BG)
    lv.color(1001, (0, 0, 0)); lv.color(1009, (0, 0, 0))
    lv.color(1002, (0, 0, 0), opacity=0.0)
    lv.color(1013, (0, 0, 0)); lv.color(1014, (0, 0, 0))
    lv.color(1004, (207, 232, 255))          # OBJ: spikes/default objects read in ice
    for ch, (rgb, op, bl) in PALETTE.items():
        lv.color(ch, rgb, opacity=op, blending=bl)


def x0_for(group, screen_offset, at_c):
    return screen_offset + (1 - MODS[group]) * at_c


def build(art, L):
    rnd = random.Random(1306)
    end_c = L['end_x']

    # ---------------------------------------------------------------- FAR: sky glow, moon, stars
    g = [FAR]
    mx, my, mr = x0_for(FAR, 262, 0), 168, 46
    art.glow(mx, my, 420, C['HALO_OUT'], 'B5', 0, g)
    art.glow(mx, my, 230, C['HALO'], 'B5', 1, g)
    art.glow(mx, my, 130, C['HALO'], 'B5', 2, g)
    art.disc(mx, my, mr, C['MOON'], 'B5', 10, g, hd=False)
    for dx, dy, r in ((-14, 12, 11), (12, -10, 7), (-4, -20, 5), (20, 14, 4)):     # craters (uneven sizes)
        art.disc(mx + dx, my + dy, r, C['MOON_SHADE'], 'B5', 12, g)
    span = (-260, x0_for(FAR, 470, end_c))
    for i in range(70):
        sx = rnd.uniform(*span); sy = rnd.uniform(105, 340)
        if (sx - mx) ** 2 + (sy - my) ** 2 < 95 ** 2:
            continue
        s = rnd.choice((2.0, 2.0, 2.5, 3.0, 3.5))
        art.rect(sx - s / 2, sy - s / 2, sx + s / 2, sy + s / 2, C['STAR'] if rnd.random() < 0.35 else C['STAR_DIM'],
                 'B5', 5, g, hd=True)
    for i in range(6):                         # horizon sky glow band
        art._deco(1888, span[0] + i * (span[1] - span[0]) / 5, 30, C['SKYGLOW'], 'B5', -5, g, True,
                  scale_x=round(rnd.uniform(5.5, 7.5), 3), scale_y=round(rnd.uniform(1.6, 2.2), 3))

    # ---------------------------------------------------------------- HILLS: two ranges built from slopes
    def ridge(group, ch, rim_ch, z, zo, x_from, x_to, y_base, peaks, seed):
        r = random.Random(seed)
        x = x_from
        k = 0
        while x < x_to:
            k += 1
            zk = zo + 2 * k                                            # each hill covers the one behind it
            w1, w2 = r.uniform(70, 150), r.uniform(60, 170)            # uneven flanks (no 50/50)
            h = r.uniform(*peaks)
            art.tri(x, y_base, x + w1, y_base + h, 'br', ch, z, zk, group)
            art.tri(x + w1, y_base, x + w1 + w2, y_base + h, 'bl', ch, z, zk, group)
            # moonlit right flank edge (moon is upper-right): thin lit line along the right slope
            if rim_ch:
                f = r.uniform(0.35, 0.6)                 # lit stretch from the summit down the right flank
                art.line(x + w1, y_base + h, x + w1 + w2 * f, y_base + h * (1 - f), 1.6, rim_ch, z, zk + 1, group, hd=True)
            x += w1 + w2 * r.uniform(0.45, 0.8)
        art.rect(x_from, y_base - 260, x_to + 200, y_base + 0.5, ch, z, zo + 2 * k + 2, group)
    hx1 = x0_for(HILLS, 520, end_c)
    ridge([HILLS], C['HILLS_BACK'], None, 'B4', 0, -330, hx1, -10, (60, 125), 11)
    ridge([HILLS], C['HILLS_FRONT'], None, 'B4', 100, -300, hx1, -25, (35, 70), 12)

    # ---------------------------------------------------------------- CASTLE on its hill
    g = [CASTLE]
    cx = x0_for(CASTLE, 330, 1000)          # centred on screen around c=1000; keep crosses the moon near bar 4
    hill_y = 26
    art.tri(cx - 360, -30, cx - 120, hill_y, 'br', C['HILLS_FRONT'], 'B4', 6, g)
    art.tri(cx + 200, -30, cx + 420, hill_y, 'bl', C['HILLS_FRONT'], 'B4', 6, g)
    art.rect(cx - 120, -30, cx + 200, hill_y, C['HILLS_FRONT'], 'B4', 6, g)

    def tower(x0, x1, y_top, roof_w, roof_h, zo, windows=()):
        art.rect(x0, hill_y, x1, y_top, C['CASTLE'], 'B4', zo, g)
        art.rect(x1 - 2.4, hill_y, x1, y_top, C['CASTLE_LIT'], 'B4', zo + 1, g)            # lit right edge
        mid = (x0 + x1) / 2
        art.tri(mid - roof_w / 2, y_top, mid, y_top + roof_h, 'br', C['CASTLE'], 'B4', zo + 2, g)
        art.tri(mid, y_top, mid + roof_w / 2, y_top + roof_h, 'bl', C['CASTLE_LIT'], 'B4', zo + 2, g)  # lit half
        art.rect(mid - roof_w / 2 - 1, y_top - 3, mid + roof_w / 2 + 1, y_top + 1.5, C['CASTLE'], 'B4', zo + 3, g)
        for (wx, wy, ww, wh) in windows:
            art.arch_window(mid + wx, wy, ww, wh, C['WINDOW'], 'B4', zo + 4, g)
            art.rect(mid + wx + ww * 0.12, wy + 2, mid + wx + ww * 0.32, wy + wh * 0.42, C['GLINT'], 'B4', zo + 5, g, hd=True)

    # curtain wall with uneven crenellations
    wx0, wx1, wtop = cx - 205, cx + 185, 74
    art.rect(wx0, hill_y, wx1, wtop, C['CASTLE'], 'B4', 8, g)
    x = wx0 + 3
    while x < wx1 - 8:
        w = rnd.choice((7.0, 8.0, 9.5))
        art.rect(x, wtop, x + w, wtop + 8.5, C['CASTLE'], 'B4', 8, g)
        x += w + rnd.choice((6.0, 7.0, 8.5))
    tower(cx - 178, cx - 128, 134, 60, 52, 14, windows=[(-6, 92, 9, 22)])
    tower(cx + 128, cx + 166, 118, 46, 44, 14, windows=[(-4, 82, 8, 18)])
    tower(cx + 4, cx + 92, 172, 104, 64, 20, windows=[(-22, 102, 12, 34), (6, 112, 10, 30), (-8, 58, 9, 20)])
    tower(cx - 40, cx - 14, 150, 32, 36, 22)            # slim turret beside the keep (70:30 against the keep)
    # gate in the curtain wall
    art.arch_window(cx - 70, hill_y, 30, 40, C['WINDOW'], 'B4', 12, g)

    # ---------------------------------------------------------------- MIST bands (blending)
    mx1 = x0_for(MIST, 520, end_c)
    for i in range(9):
        art._deco(1888, -250 + i * (mx1 + 250) / 8 + rnd.uniform(-40, 40), rnd.uniform(-15, 25), C['MIST'], 'B3', 0,
                  [MIST], True, scale_x=round(rnd.uniform(4.0, 6.5), 3), scale_y=round(rnd.uniform(0.35, 0.6), 3))

    # ---------------------------------------------------------------- CHASM cliffs below the bridge
    g = [CHASM]
    cx1 = x0_for(CHASM, 520, end_c)
    x = -300
    while x < cx1:
        w = rnd.uniform(40, 110); top = rnd.uniform(-95, -48)
        art.rect(x, -330, x + w, top, C['CLIFF'], 'B3', 10, g)
        art.tri(x, top, x + w * rnd.uniform(0.3, 0.7), top + rnd.uniform(8, 22), 'bl', C['CLIFF'], 'B3', 10, g)
        art.rect(x + w - 2, -330, x + w, top, C['CLIFF_LIT'], 'B3', 11, g, hd=True)
        x += w
    for i in range(6):
        art._deco(1888, -200 + i * (cx1 + 200) / 5, -150, C['MIST'], 'B3', 12, g, True,
                  scale_x=round(rnd.uniform(5, 7), 3), scale_y=0.5)
    # moonlight falling into the chasm: what shows through the arch openings, so the arches read as holes
    for i in range(7):
        art._deco(1888, -250 + i * (cx1 + 250) / 6 + rnd.uniform(-30, 30), -95, C['ARCHLIGHT'], 'B3', 13, g, True,
                  scale_x=round(rnd.uniform(4.2, 5.6), 3), scale_y=round(rnd.uniform(1.1, 1.5), 3))

    build_bridge(art, L, rnd)


def build_bridge(art, L, rnd):
    """Near layer: bridge deck, raised deck P1, stairs + gate ledge, rampart walkway. Gameplay surfaces get bright
    rims (rulebook 6.1); bodies stay near-black."""
    (p1_x0, _, p1_x1, _), (s1_x0, _, ledge, _), (s2_x0, _, _, _) = L['solids']
    deck_end = s1_x0
    x_start = -300

    # deck face (top of deck is the floor y=0)
    art.rect(x_start, -38, deck_end, 0, C['STONE'], 'B1', 0)
    art.rect(x_start, -2.6, deck_end, 0, C['RIM'], 'T1', 20)                      # moonlit top edge of the path
    art.rect(x_start, -38, deck_end, -35.5, C['STONE_LIT'], 'B1', 5)              # lower moulding
    # stone joints: uneven block lengths (no evenness), two courses
    for (y0, y1) in ((-35.5, -19.5), (-19.5, -2.6)):
        x = x_start + rnd.uniform(0, 30)
        while x < deck_end:
            art.rect(x, y0, x + 1.4, y1, C['JOINT'], 'B1', 6)
            x += rnd.choice((42, 47, 55, 61, 66))
    art.rect(x_start, -19.5, deck_end, -18.3, C['JOINT'], 'B1', 6)

    # piers + pointed arches under the deck
    piers = [-150, 205, 540, 905, 1290, 1640, 2020]
    for i, px in enumerate(piers):
        w = (52, 44, 58, 47, 61, 49, 55)[i]
        art.rect(px - w / 2, -340, px + w / 2, -38, C['PIER'], 'B2', 0)
        art.rect(px + w / 2 - 3, -340, px + w / 2, -38, C['PIER_LIT'], 'B2', 1)  # lit right side
        art.rect(px - w / 2 - 4, -64, px + w / 2 + 4, -56, C['PIER'], 'B2', 2)    # string course
    for a, b in zip(piers, piers[1:]):
        wa, wb = 26, 26
        left, right = a + wa, b - wb
        mid = left + (right - left) * 0.5
        spring, apex = -118, -56
        art.rect(left, apex, right, -38, C['STONE'], 'B2', 3)                     # spandrel band above apex
        art.tri(left, spring, mid, apex, 'tl', C['STONE'], 'B2', 3)               # fills above the left arch side
        art.tri(mid, spring, right, apex, 'tr', C['STONE'], 'B2', 3)
        art.line(mid, apex, right, spring, 2.0, C['PIER_LIT'], 'B2', 4)           # lit side of the arch (faces moon)
        art.line(left, spring, mid, apex, 1.4, C['JOINT'], 'B2', 4)               # shadow side, dimmer

    # raised deck P1 (gameplay, 1 block)
    art.rect(p1_x0, 0, p1_x1, 30, C['STONE'], 'B1', 10)
    art.rect(p1_x0, 27.4, p1_x1, 30, C['RIM'], 'T1', 20)
    art.rect(p1_x0, 0, p1_x0 + 2, 27.4, C['RIM_DIM'], 'T1', 19)                   # wall face the cube must not hit
    art.rect(p1_x1 - 2, 0, p1_x1, 27.4, C['RIM_DIM'], 'T1', 19)
    x = p1_x0 + 23
    while x < p1_x1 - 10:
        art.rect(x, 3, x + 1.3, 25, C['JOINT'], 'B1', 11)
        x += rnd.choice((52, 57, 63, 71))

    # stairs to the gate ledge (gameplay, 1 and 2 blocks), gatehouse wall below
    art.rect(s1_x0, -340, ledge, 30, C['STONE'], 'B1', 10)
    art.rect(s2_x0, 30, ledge, 60, C['STONE'], 'B1', 10)
    art.rect(s1_x0, 27.4, s2_x0, 30, C['RIM'], 'T1', 20)
    art.rect(s2_x0, 57.4, ledge, 60, C['RIM'], 'T1', 20)
    for (x0, y0, y1) in ((s1_x0, 0, 27.4), (s2_x0, 30, 57.4)):
        art.rect(x0, y0, x0 + 2, y1, C['RIM_DIM'], 'T1', 19)
    art.rect(ledge - 2, -340, ledge, 57.4, C['RIM_DIM'], 'T1', 19)                # ledge drop face
    for y in (-38, -71, -118, -170, -231):
        art.rect(s1_x0, y, ledge, y + 1.4, C['JOINT'], 'B1', 11)
    for (y0, y1, xa) in ((-36.6, 0, s1_x0), (-69.6, -38, s1_x0), (3, 27.4, s1_x0), (33, 57.4, s2_x0)):
        x = xa + rnd.uniform(18, 34)
        while x < ledge - 12:
            art.rect(x, y0, x + 1.3, y1, C['JOINT'], 'B1', 11)
            x += rnd.choice((38, 44, 53, 59))
    # gate tower rising behind the ledge (background: darker, no bright rim)
    gx0, gx1 = s2_x0 + 6, ledge - 22                                            # slim tower over the ledge
    gmid, gtop = (gx0 + gx1) / 2, 196
    art.rect(gx0, 60, gx1, gtop, C['MERLON'], 'B2', 0)
    art.rect(gx1 - 2.4, 60, gx1, gtop, C['MERLON_LIT'], 'B2', 1)
    art.rect(gx0 - 4, gtop - 4, gx1 + 4, gtop + 3, C['MERLON'], 'B2', 2)          # corbel band
    art.tri(gmid - (gx1 - gx0) / 2 - 6, gtop + 3, gmid, gtop + 58, 'br', C['MERLON'], 'B2', 3)
    art.tri(gmid, gtop + 3, gmid + (gx1 - gx0) / 2 + 6, gtop + 58, 'bl', C['MERLON_LIT'], 'B2', 3)
    art.arch_window(gmid - 3, 120, 9, 30, C['WINDOW'], 'B2', 4)
    art.rect(gmid - 3 + 1.5, 123, gmid - 3 + 3.5, 136, C['GLINT'], 'B2', 5, hd=True)

    # rampart walkway after the ledge (floor y=0): wall face + merlons behind (background)
    r0, r1 = ledge, L['end_x'] + 450
    art.rect(r0, -340, r1, 0, C['STONE'], 'B1', 0)
    art.rect(r0, -2.6, r1, 0, C['RIM'], 'T1', 20)
    for y in (-26, -60, -97, -140):
        art.rect(r0, y, r1, y + 1.3, C['JOINT'], 'B1', 6)
    x = r0 + 14
    while x < r1:
        w = rnd.choice((24.0, 27.0, 30.0))
        art.rect(x, 0, x + w, 46, C['MERLON'], 'B2', 4)
        art.rect(x + w - 2, 20, x + w, 46, C['MERLON_LIT'], 'B2', 5)
        x += w + rnd.choice((15.0, 17.0, 20.0))
    art.rect(r0, 0, r1, 20, C['MERLON'], 'B2', 3)                                 # parapet wall behind the walk


def triggers(art, L):
    """Setup, parallax, music sync (pulses), BPM guides, start positions, end."""
    x = TRACK.x
    art.hide_ground(-15)
    for grp, m in MODS.items():
        art.parallax(-15, grp, m, 14.0, y=-405 - 30 * (grp - 100))
    art.bpm_guide(x(T(1, 1)), 128, 4, 1, 7.5)
    art.bpm_guide(x(T(5, 1)), 128, 4, 0, 4.0)

    def pulse_at(t, ch, rgb, fin, hold, fout, row=0):
        art.pulse(x(t), ch, rgb, fin, hold, fout, y=-555 - 30 * row)

    # intro: halo breathes on the A#4 accents, stars on the C5 note, soft rim glints on each first beat
    for t in (T(1, 1), T(3, 1)):
        pulse_at(t, C['HALO'], (80, 140, 255), 0.05, 0.15, 1.2, 0)
    pulse_at(T(2, 4), C['STAR_DIM'], (230, 240, 255), 0.03, 0.1, 0.6, 1)
    for b in (1, 2, 3, 4):
        pulse_at(T(b, 1), C['RIM'], (255, 255, 255), 0.02, 0.05, 0.35, 2)
    # bass pickup (4.3-4.4): the sky darkens = the breath before the beat drops in
    art.color_trigger(x(T(4, 3)), 1000, (2, 3, 8), dur=0.45, y=-525)
    art.color_trigger(x(T(4, 3)), C['HALO'], (20, 48, 120), dur=0.45, opacity=0.6, blending=True, y=-495)
    # 5.1 beat drops in: sky lifts, halo flashes; then kick pulses each beat
    art.color_trigger(x(T(5, 1)), 1000, (6, 10, 24), dur=0.0, y=-525)
    art.color_trigger(x(T(5, 1)) + 1, 1000, BG, dur=0.9, y=-465)
    art.color_trigger(x(T(5, 1)), C['HALO'], (36, 84, 196), dur=0.0, opacity=0.6, blending=True, y=-495)
    pulse_at(T(5, 1), C['HALO'], (120, 180, 255), 0.0, 0.1, 0.8, 0)
    pulse_at(T(5, 1), C['RIM'], (255, 255, 255), 0.0, 0.08, 0.5, 2)
    for k in range(1, 8):
        tb = T(5, 1) + k * 60 / 128
        pulse_at(tb, C['SKYGLOW'], (30, 60, 150), 0.0, 0.05, 0.35, 3)
        pulse_at(tb, C['RIM'], (255, 255, 255), 0.0, 0.04, 0.25, 2)

    art.start_pos(x(T(4, 1)) - 60, 15, 1, disabled=True)
    art.start_pos(L['solids'][1][2] + 90, 15, 0, disabled=True)
    art.end(L['end_x'])
