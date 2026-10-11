"""Very rough renderer: draws each object as a coloured primitive at its initial position.
Ignores triggers/moves, so animated stuff shows at its spawn position. Good enough to study
composition, palette, layering and density."""
import sys, os, math, colorsys
from PIL import Image, ImageDraw, ImageFilter, ImageChops
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gmd import *

ZORDER_RANK = {-5: 0, -3: 1, -1: 2, 1: 3, 3: 4, 0: 5, 4: 5, 5: 6, 7: 7, 9: 8, 11: 9}
P1 = (125, 255, 0)
P2 = (0, 255, 255)


def parse_hsv(s):
    try:
        p = s.split('a')
        return float(p[0]), float(p[1]), float(p[2]), p[3] == '1', p[4] == '1'
    except Exception:
        return 0, 1, 1, False, False


def apply_hsv(rgb, hsv):
    h, s, v, sc, vc = hsv
    r, g, b = [c / 255.0 for c in rgb]
    hh, ss, vv = colorsys.rgb_to_hsv(r, g, b)
    hh = (hh + h / 360.0) % 1.0
    ss = ss + s if sc else ss * s
    vv = vv + v if vc else vv * v
    ss = min(1, max(0, ss)); vv = min(1, max(0, vv))
    r, g, b = colorsys.hsv_to_rgb(hh, ss, vv)
    return (int(r * 255), int(g * 255), int(b * 255))


class Palette:
    def __init__(self, colors):
        self.c = colors
        self.cache = {}

    def get(self, cid, depth=0):
        if cid in self.cache:
            return self.cache[cid]
        res = ((255, 255, 255), 1.0, False)
        if cid == 1010:
            res = ((0, 0, 0), 1.0, False)
        elif cid in (1011, 1012):
            res = ((255, 255, 255), 1.0, False)
        elif cid == 1005:
            res = (P1, 1.0, True)
        elif cid == 1006:
            res = (P2, 1.0, True)
        d = self.c.get(cid)
        if d is not None:
            opa = float(d.get('7', 1) or 1)
            blend = d.get('5') == '1'
            copy = int(d.get('9', 0) or 0)
            pc = d.get('4', '-1')
            if copy and depth < 8:
                base, bo, _ = self.get(copy, depth + 1)
                rgb = apply_hsv(base, parse_hsv(d.get('10', '0a1a1a0a0')))
                if d.get('17') == '1':
                    opa = bo
            elif pc in ('1', '2'):
                rgb = P1 if pc == '1' else P2
            else:
                rgb = (int(float(d.get('1', 255))), int(float(d.get('2', 255))), int(float(d.get('3', 255))))
            res = (rgb, opa, blend)
        self.cache[cid] = res
        return res


def size_for(name):
    n = name
    w = h = 30.0
    if 'Tiny' in n: w = h = 8
    elif 'Small' in n: w = h = 15
    elif 'Medium' in n: w = h = 22
    if 'Half' in n: h = h / 2
    if 'Quarter' in n: w, h = w / 2, h / 2
    if 'One-Sixteenth' in n: w, h = w / 4, h / 4
    if 'Thin Line' in n or n.startswith('Thin'): h = 3
    if 'Straight' in n and 'Glow' in n: h = h * 0.6
    if 'Large Glow Orb' in n: w = h = 60
    if 'Large Cloud' in n: w, h = 120, 60
    if 'Particle' in n: w = h = 10
    if 'Text' == n: w, h = 60, 12
    return w, h


def kind_for(name):
    n = name
    if 'Glow' in n: return 'glow'
    if 'Spike' in n or 'Triangle' in n: return 'tri'
    if 'Slope' in n: return 'slope'
    if 'Orb' in n or 'Circle' in n or 'Saw' in n or 'Round' in n or 'Ball' in n: return 'circle'
    if 'Outline' in n or '3DL' in n or 'Line' in n or 'Chain' in n: return 'line'
    return 'rect'


def sim_state(L, upto_x):
    """Apply position-triggered colour/alpha/toggle triggers left of upto_x."""
    colors = {k: dict(v) for k, v in L['colors'].items()}
    galpha, ghidden = {}, set()
    trig = [o for o in L['objs'] if o['_id'] in (899, 1007, 1049) and o['_x'] <= upto_x
            and o.get('62') != '1' and o.get('11') != '1']
    trig.sort(key=lambda o: o['_x'])
    for o in trig:
        if o['_id'] == 899:
            tgt = int(o.get('23', 1) or 1)
            d = colors.setdefault(tgt, {'6': str(tgt)})
            if o.get('50') and o.get('50') != '0':
                d['9'] = o['50']; d['10'] = o.get('49', '0a1a1a0a0')
            else:
                d.pop('9', None)
                d['1'], d['2'], d['3'] = o.get('7', '255'), o.get('8', '255'), o.get('9', '255')
            d['7'] = o.get('35', '1')
            d['5'] = '1' if o.get('17') == '1' else '0'
            if o.get('60') == '1': d['17'] = '1'
        elif o['_id'] == 1007:
            galpha[int(o.get('51', 0) or 0)] = float(o.get('35', 1) or 1)
        elif o['_id'] == 1049:
            g = int(o.get('51', 0) or 0)
            if o.get('56') == '1': ghidden.discard(g)
            else: ghidden.add(g)
    return colors, galpha, ghidden


def render(L, x0, x1, y0, y1, scale=1.0, layer_filter=None, draw_gameplay=True, sim=True):
    if sim:
        colors, galpha, ghidden = sim_state(L, x0 + 150)
    else:
        colors, galpha, ghidden = L['colors'], {}, set()
    pal = Palette(colors)
    W, H = int((x1 - x0) * scale), int((y1 - y0) * scale)
    bg, _, _ = pal.get(1000)
    img = Image.new('RGB', (W, H), bg)
    objs = [o for o in L['objs'] if x0 - 120 <= o['_x'] <= x1 + 120 and y0 - 120 <= o['_y'] <= y1 + 120]
    objs.sort(key=lambda o: (ZORDER_RANK.get(int(o.get('24', 0) or 0), 5), int(o.get('25', 0) or 0)))
    for o in objs:
        oid = o['_id']
        name = NAMES.get(oid, '')
        if is_trigger(oid) or oid in (31, 146, 1816, 3640, 3643) or 'Invisible' in name or 'Particle' in name and 'Custom' in name:
            continue
        if layer_filter and not layer_filter(o):
            continue
        cid = int(o.get('21', 0) or 0)
        if not cid:
            cid = int(o.get('22', 0) or 0)
        if not cid:
            cid = 1010 if ('Black' in name and 'Gradient' not in name) else 1004
        rgb, opa, blend = pal.get(cid)
        if o.get('41') == '1' and o.get('43'):
            rgb = apply_hsv(rgb, parse_hsv(o['43']))
        gs = [int(g) for g in o.get('57', '').split('.') if g]
        if any(g in ghidden for g in gs):
            continue
        for g in gs:
            if g in galpha: opa *= galpha[g]
        if opa <= 0.01:
            continue
        w, h = size_for(name)
        sc = float(o.get('32', 1) or 1)
        sx = float(o.get('128', 1) or 1) * sc
        sy = float(o.get('129', 1) or 1) * sc
        w, h = w * abs(sx) * scale, h * abs(sy) * scale
        rot = float(o.get('6', 0) or 0)
        cx = (o['_x'] - x0) * scale
        cy = H - (o['_y'] - y0) * scale
        kind = kind_for(name)
        if oid in GAMEMODE_PORTAL or oid in SPEED_PORTAL or oid in OTHER_PORTAL:
            if not draw_gameplay:
                continue
            kind, rgb, opa, blend, w, h = 'rect', (255, 0, 255), 0.9, False, 10 * scale, 90 * scale
        if oid in ORBS or oid in PADS:
            if not draw_gameplay:
                continue
            kind, rgb, opa, blend = 'circle', (255, 220, 0), 1.0, False
            w = h = 26 * scale
        draw_obj(img, kind, cx, cy, w, h, rot, rgb, opa, blend, o.get('4') == '1', o.get('5') == '1')
    return img


def poly_rect(cx, cy, w, h, rot):
    pts = [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]
    return rotate(pts, cx, cy, rot)


def rotate(pts, cx, cy, rot):
    a = math.radians(rot)
    ca, sa = math.cos(a), math.sin(a)
    return [(cx + x * ca - y * sa, cy + x * sa + y * ca) for x, y in pts]


def draw_obj(img, kind, cx, cy, w, h, rot, rgb, opa, blend, fx, fy):
    pad = int(max(w, h) * (1.6 if kind == 'glow' else 0.8)) + 2
    bx0, by0 = int(cx - pad), int(cy - pad)
    size = (2 * pad, 2 * pad)
    if bx0 > img.width or by0 > img.height or bx0 + size[0] < 0 or by0 + size[1] < 0:
        return
    m = Image.new('L', size, 0)
    d = ImageDraw.Draw(m)
    lcx, lcy = cx - bx0, cy - by0
    a = int(255 * max(0, min(1, opa)))
    if kind == 'rect':
        d.polygon(poly_rect(lcx, lcy, w, h, rot), fill=a)
    elif kind == 'line':
        pts = poly_rect(lcx, lcy, w, h, rot)
        d.line(pts[:2], fill=a, width=max(1, int(min(w, h) * 0.15)))
    elif kind == 'tri':
        pts = [(-w / 2, h / 2), (w / 2, h / 2), (0, -h / 2)]
        if fy: pts = [(x, -y) for x, y in pts]
        d.polygon(rotate(pts, lcx, lcy, rot), fill=a)
    elif kind == 'slope':
        pts = [(-w / 2, h / 2), (w / 2, h / 2), (w / 2, -h / 2)]
        if fx: pts = [(-x, y) for x, y in pts]
        if fy: pts = [(x, -y) for x, y in pts]
        d.polygon(rotate(pts, lcx, lcy, rot), fill=a)
    elif kind == 'circle':
        r = min(w, h) / 2
        d.ellipse((lcx - r, lcy - r, lcx + r, lcy + r), fill=a)
    elif kind == 'glow':
        d.polygon(poly_rect(lcx, lcy, w * 0.7, h * 0.5, rot), fill=int(a * 0.35))
        m = m.filter(ImageFilter.GaussianBlur(max(1, min(w, h) * 0.4)))
    region = (bx0, by0, bx0 + size[0], by0 + size[1])
    color = Image.new('RGB', size, rgb)
    if blend:
        col = Image.composite(color, Image.new('RGB', size, (0, 0, 0)), m)
        base = img.crop(region)
        img.paste(ImageChops.add(base, col), region)
    else:
        img.paste(color, region, m)
