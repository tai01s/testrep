"""Take one frame of a level apart: full render, then one render per Z layer (alone), plus a census of what is on
screen (object types, layers, channels, scale/rotation/HSV use, groups, triggers nearby).

  python3 dissect.py level.gmd out_prefix t [S]
"""
import collections
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render_real as R  # noqa: E402
from gmd import load, x_to_time_fn, KA4_SPEED, NAMES, is_trigger  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

LAYER_NAME = {-5: 'B5', -3: 'B4', -1: 'B3', 1: 'B2', 3: 'B1', 5: 'T1', 7: 'T2', 9: 'T3', 11: 'T4'}


def zl(o):
    v = int(o.get('24', 0) or 0)
    if v in LAYER_NAME:
        return v
    info = R.OBJ.get(str(o['_id']), {})
    return info.get('defaultZLayer', 3)


def main(path, prefix, t, S=1):
    L = load(path)
    tfn, _ = x_to_time_fn(L['objs'], KA4_SPEED.get(int(L['header'].get('kA4', 0) or 0), '1x'))
    xmax = max(o['_x'] for o in L['objs'])

    def xfn(tt):
        lo, hi = -300.0, xmax + 60
        for _ in range(40):
            m = (lo + hi) / 2
            lo, hi = (m, hi) if tfn(m) < tt else (lo, m)
        return lo
    c = xfn(t)
    cy = R.cam_y_for(L, c)
    xl = c - 160
    full = R.render(L, t, tfn, xfn, cam_y=cy, S=S)
    full.save(prefix + '_full.png')
    on = [o for o in L['objs'] if xl - 30 <= o['_x'] <= xl + 600 and cy - 30 <= o['_y'] <= cy + 350
          and not is_trigger(o['_id'])]
    layers = sorted({zl(o) for o in on})
    tiles = []
    for lv in layers:
        img = R.render(L, t, tfn, xfn, cam_y=cy, S=S, filt=lambda o, lv=lv: zl(o) == lv)
        ImageDraw.Draw(img).text((6, 4), '%s only (%d objs)' % (LAYER_NAME.get(lv, lv), sum(zl(o) == lv for o in on)),
                                 fill=(255, 255, 0))
        tiles.append(img)
    if tiles:
        w, h = tiles[0].size
        cols = 3
        rows = (len(tiles) + cols - 1) // cols
        sh = Image.new('RGB', (w * cols, h * rows), (25, 25, 25))
        for i, im in enumerate(tiles):
            sh.paste(im, ((i % cols) * w, (i // cols) * h))
        sh.save(prefix + '_layers.png')
    # census
    cnt = collections.Counter(o['_id'] for o in on)
    print('%s t=%.2f x=%.0f..%.0f y=%.0f..%.0f  on-screen objects: %d' % (L['name'], t, xl, xl + 570, cy, cy + 320,
                                                                          len(on)))
    print('by layer:', {LAYER_NAME.get(k, k): v for k, v in sorted(collections.Counter(zl(o) for o in on).items())})
    print('top objects:')
    for oid, n in cnt.most_common(30):
        objs = [o for o in on if o['_id'] == oid]
        sc = collections.Counter(round(float(o.get('32', 1) or 1) * float(o.get('128', 1) or 1), 2) for o in objs)
        ch = collections.Counter(o.get('21', '-') for o in objs)
        rot = sum(1 for o in objs if float(o.get('6', 0) or 0) % 90)
        hsv = sum(1 for o in objs if o.get('41') == '1' or o.get('42') == '1')
        grp = sum(1 for o in objs if o.get('57'))
        print('  %5d x%-4d %-28s scales %s | ch %s | offgrid-rot %d | hsv %d | grouped %d' % (
            oid, n, NAMES.get(oid, '?')[:28], dict(sc.most_common(4)), dict(ch.most_common(4)), rot, hsv, grp))
    trig = [o for o in L['objs'] if is_trigger(o['_id']) and xl - 600 <= o['_x'] <= xl + 600]
    print('triggers within +-600 units:', dict(collections.Counter(NAMES.get(o['_id'], o['_id']) for o in trig)
                                               .most_common(12)))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], float(sys.argv[3]), int(sys.argv[4]) if len(sys.argv) > 4 else 1)
