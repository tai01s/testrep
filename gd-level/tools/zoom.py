"""Render a small world rectangle of a level at high zoom and list the objects in it (for taking structures apart).

  python3 zoom.py level.gmd out.png t x0 y0 w h S [max_rows]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render_real as R  # noqa: E402
from gmd import load, x_to_time_fn, KA4_SPEED, NAMES, is_trigger  # noqa: E402

KEYS = ['_id', '_x', '_y', '6', '32', '128', '129', '4', '5', '21', '22', '24', '25', '41', '43', '57']


def main(path, out, t, x0, y0, w, h, S, rows=80):
    L = load(path)
    tfn, _ = x_to_time_fn(L['objs'], KA4_SPEED.get(int(L['header'].get('kA4', 0) or 0), '1x'))
    xmax = max(o['_x'] for o in L['objs'])

    def xfn(tt):
        lo, hi = -300.0, xmax + 60
        for _ in range(40):
            m = (lo + hi) / 2
            lo, hi = (m, hi) if tfn(m) < tt else (lo, m)
        return lo
    R.render(L, t, tfn, xfn, cam_x=x0 + 160, cam_y=y0, W=int(w), H=int(h), S=S).save(out)
    on = [o for o in L['objs'] if x0 - 15 <= o['_x'] <= x0 + w + 15 and y0 - 15 <= o['_y'] <= y0 + h + 15
          and not is_trigger(o['_id'])]
    on.sort(key=lambda o: (int(o.get('24', 0) or 0), int(o.get('25', 0) or 0)))
    for o in on[:rows]:
        print(' '.join('%s=%s' % (k, o[k]) for k in KEYS if k in o), '|', NAMES.get(o['_id'], '?'))
    print(len(on), 'objects')


if __name__ == '__main__':
    a = sys.argv
    main(a[1], a[2], float(a[3]), float(a[4]), float(a[5]), float(a[6]), float(a[7]), int(a[8]),
         int(a[9]) if len(a) > 9 else 80)
