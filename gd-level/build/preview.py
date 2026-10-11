"""Preview frames of a generated level by decoding the .gmd (round trip) and drawing the primitives this project
uses with their measured geometry. Approximate (no real sprites); good for composition, value and sync checks."""
import math
import os
import sys
from PIL import Image, ImageDraw, ImageFilter, ImageChops

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', 'tools'))
os.environ.setdefault('GD_OBJECTS_CSV', os.path.join(HERE, '..', 'ref', 'gd-info-explorer', 'src', 'lib', 'objects.csv'))
from gmd import load  # noqa: E402

RANK = {-5: 0, -3: 1, -1: 2, 1: 3, 3: 4, 0: 5, 5: 6, 7: 7, 9: 8, 11: 9}


def channels(L, t_x):
    cols = {}
    for ch, d in L['colors'].items():
        cols[ch] = [(int(float(d.get('1', 255))), int(float(d.get('2', 255))), int(float(d.get('3', 255)))),
                    float(d.get('7', 1) or 1), d.get('5') == '1']
    for o in sorted((o for o in L['objs'] if o['_id'] == 899), key=lambda o: o['_x']):
        if o['_x'] <= t_x:
            ch = int(o['23'])
            cols[ch] = [(int(o.get('7', 255)), int(o.get('8', 255)), int(o.get('9', 255))),
                        float(o.get('35', 1)), o.get('17') == '1']
    return cols


def world_poly(o):
    oid = o['_id']
    s = float(o.get('32', 1) or 1)
    sx, sy = float(o.get('128', 1) or 1) * s, float(o.get('129', 1) or 1) * s
    w, h = 30 * sx, 30 * sy
    fx, fy = o.get('4') == '1', o.get('5') == '1'
    if oid == 211:
        pts = [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]
    elif oid == 693:
        pts = [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2)]          # solid bottom-right
        pts = [((-px if fx else px), (-py if fy else py)) for px, py in pts]
    elif oid == 1837:                                                          # top-left quadrant, centre at cell BR
        pts = [(w / 2, -h / 2)] + [(w / 2 - w * math.cos(a), -h / 2 + h * math.sin(a))
                                   for a in [i * math.pi / 2 / 16 for i in range(17)]]
    elif oid == 8:
        pts = [(-15, -15), (15, -15), (0, 15)]
    else:
        return None
    rot = -math.radians(float(o.get('6', 0) or 0))                            # GD stores clockwise-positive
    c, sn = math.cos(rot), math.sin(rot)
    return [(o['_x'] + px * c - py * sn, o['_y'] + px * sn + py * c) for px, py in pts]


def frame(L, mods, track, t, path=None, W=570, H=340, ybot=-100, scale=2, label=''):
    c = track.x(t)
    xl = c - 190
    cols = channels(L, c)
    img = Image.new('RGB', (W * scale, H * scale), cols.get(1000, [(0, 0, 0)])[0])

    def S(px, py):
        return ((px - xl) * scale, (H - (py - ybot)) * scale)

    objs = [o for o in L['objs'] if o['_id'] in (211, 693, 1837, 1888, 8) and o.get('135') != '1']
    def keyf(o):
        ch = int(o.get('21', 0) or 0)
        bl = cols.get(ch, [0, 0, False])[2]
        return (RANK.get(int(o.get('24', 0) or 0), 5), 0 if bl else 1, int(o.get('25', 0) or 0))
    for o in sorted(objs, key=keyf):
        gs = [int(g) for g in o.get('57', '').split('.') if g]
        dx = sum(mods.get(g, 0) for g in gs) * c
        ch = int(o.get('21', 0) or 0) or 1004
        rgb, op, bl = cols.get(ch, [(255, 255, 255), 1, False])
        if op <= 0:
            continue
        if o['_id'] == 1888:
            s = float(o.get('32', 1) or 1)
            rx, ry = 30 * s * float(o.get('128', 1) or 1), 30 * s * float(o.get('129', 1) or 1)
            cx, cy = S(o['_x'] + dx, o['_y'])
            R = int(max(rx, ry) * scale) + 2
            if cx + R < 0 or cx - R > W * scale:
                continue
            m = Image.new('L', (2 * R, 2 * R), 0)
            d = ImageDraw.Draw(m)
            for k in range(20, 0, -1):
                f = k / 20
                a = int(255 * op * (1 - f) ** 1.6)
                d.ellipse((R - rx * scale * f, R - ry * scale * f, R + rx * scale * f, R + ry * scale * f), fill=a)
            layer = Image.new('RGB', m.size, rgb)
            box = (int(cx - R), int(cy - R))
            if bl:
                base = img.crop((box[0], box[1], box[0] + 2 * R, box[1] + 2 * R))
                add = Image.composite(layer, Image.new('RGB', m.size, (0, 0, 0)), m)
                img.paste(ImageChops.add(base, add), box)
            else:
                img.paste(layer, box, m)
            continue
        poly = world_poly(o)
        if not poly:
            continue
        pts = [S(px + dx, py) for px, py in poly]
        if max(p[0] for p in pts) < 0 or min(p[0] for p in pts) > W * scale:
            continue
        m = Image.new('L', img.size, 0)
        ImageDraw.Draw(m).polygon(pts, fill=int(255 * op))
        if bl:
            add = Image.composite(Image.new('RGB', img.size, rgb), Image.new('RGB', img.size, (0, 0, 0)), m)
            img = ImageChops.add(img, add)
        else:
            img.paste(Image.new('RGB', img.size, rgb), (0, 0), m)
        if o['_id'] == 8:                                                     # spike outline in OBJ colour
            ImageDraw.Draw(img).line(pts + [pts[0]], fill=cols.get(1004, [(255, 255, 255)])[0], width=2)
    d = ImageDraw.Draw(img)
    if path:
        p = min(path, key=lambda q: abs(q[0] - t))
        x0, y0 = S(p[1] - 15, p[2] + 30)
        x1, y1 = S(p[1] + 15, p[2])
        d.rectangle((x0, y0, x1, y1), fill=(125, 255, 0), outline=(0, 255, 255), width=3)
        trail = [S(q[1], q[2] + 15) for q in path if t - 1.2 <= q[0] <= t]
        if len(trail) > 1:
            d.line(trail, fill=(0, 255, 255), width=1)
    d.text((8, 6), label or 't=%.2fs  x=%.0f' % (t, c), fill=(255, 255, 0))
    return img


def sheet(gmd_path, mods, track, times, out, path=None, cols_n=2, label_fn=None):
    L = load(gmd_path)
    frames = [frame(L, mods, track, t, path, label=label_fn(t) if label_fn else '') for t in times]
    w, h = frames[0].size
    rows = (len(frames) + cols_n - 1) // cols_n
    S = Image.new('RGB', (w * cols_n, h * rows), (30, 30, 30))
    for i, f in enumerate(frames):
        S.paste(f, ((i % cols_n) * w, (i // cols_n) * h))
    S.save(out)
    return out
