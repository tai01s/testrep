import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from render import *
from PIL import Image, ImageDraw
path, tag, outdir = sys.argv[1], sys.argv[2], sys.argv[3]
times = [float(t) for t in sys.argv[4].split(',')]
L = load(path)
f, _ = x_to_time_fn(L['objs'], KA4_SPEED.get(int(L['header'].get('kA4', 0) or 0), '1x'))
# invert time->x by sampling
xs = list(range(-300, int(max(o['_x'] for o in L['objs'])) + 30, 15))
def t2x(t):
    for x in xs:
        if f(x) >= t: return x
    return xs[-1]
tiles = []
for t in times:
    x = t2x(t)
    ys = sorted(o['_y'] for o in L['objs'] if x - 150 <= o['_x'] <= x + 450 and not is_trigger(o['_id']))
    if ys:
        lo, hi = ys[int(len(ys) * .1)], ys[int(len(ys) * .9)]
        mid = (lo + hi) / 2
    else:
        mid = 150
    y0 = mid - 200
    img = render(L, x - 150, x + 570, y0, y0 + 405, scale=1.0)
    d = ImageDraw.Draw(img)
    d.text((6, 4), '%s  t=%.1fs  x=%d  y=%d..%d' % (tag, t, x, y0, y0 + 405), fill=(255, 255, 0))
    tiles.append(img)
W = tiles[0].width
sheet = Image.new('RGB', (W * 2, tiles[0].height * ((len(tiles) + 1) // 2)), (40, 40, 40))
for i, t in enumerate(tiles):
    sheet.paste(t, ((i % 2) * W, (i // 2) * t.height))
sheet.save(os.path.join(outdir, tag + '.png'))
print('ok', sheet.size)
