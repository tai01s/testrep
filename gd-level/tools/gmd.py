"""Decode GDShare .gmd exports into object lists, and a few shared constants."""
import base64, gzip, re, zlib, csv, os
from collections import OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
OBJ_CSV = os.environ.get('GD_OBJECTS_CSV', os.path.join(HERE, '..', 'ref', 'gd-info-explorer', 'src', 'lib', 'objects.csv'))

NAMES = {}
with open(OBJ_CSV) as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        i, n = line.split(',', 1)
        NAMES[int(i)] = n

# units per second at each speed (30 units = 1 block)
SPEED_UPS = {'0.5x': 251.16, '1x': 311.58, '2x': 387.42, '3x': 468.0, '4x': 576.0}
SPEED_PORTAL = {200: '0.5x', 201: '1x', 202: '2x', 203: '3x', 1334: '4x'}
KA4_SPEED = {0: '1x', 1: '0.5x', 2: '2x', 3: '3x', 4: '4x'}
GAMEMODE_PORTAL = {12: 'cube', 13: 'ship', 47: 'ball', 111: 'ufo', 660: 'wave', 745: 'robot', 1331: 'spider', 1933: 'swing'}
KA2_MODE = {0: 'cube', 1: 'ship', 2: 'ball', 3: 'ufo', 4: 'wave', 5: 'robot', 6: 'spider', 7: 'swing'}
OTHER_PORTAL = {99: 'size-normal', 101: 'size-mini', 286: 'dual', 287: 'single', 10: 'grav-normal', 11: 'grav-flip',
                2926: 'grav-toggle', 45: 'mirror-on', 46: 'mirror-off', 747: 'teleport', 2902: 'teleport'}
ORBS = {36: 'yellow orb', 84: 'blue orb', 141: 'pink orb', 1022: 'green orb', 1330: 'black orb', 1333: 'red orb',
        1594: 'toggle orb', 1704: 'green dash orb', 1751: 'pink dash orb', 3004: 'spider orb', 3027: 'teleport orb'}
PADS = {35: 'yellow pad', 67: 'blue pad', 140: 'pink pad', 1332: 'red pad', 3005: 'spider pad'}
ZLAYER = {-5: 'B5', -3: 'B4', -1: 'B3', 1: 'B2', 3: 'B1', 0: 'default', 5: 'T1', 7: 'T2', 9: 'T3', 11: 'T4', 4: 'portal'}


def _b64(s):
    s = s.replace('-', '+').replace('_', '/')
    s += '=' * (-len(s) % 4)
    return base64.b64decode(s)


def decode_level_string(k4):
    raw = _b64(k4)
    try:
        return gzip.decompress(raw).decode('utf-8', 'replace')
    except Exception:
        return zlib.decompress(raw, 15 + 32).decode('utf-8', 'replace')


def parse_plist(path):
    txt = open(path, encoding='utf-8', errors='replace').read()
    meta = OrderedDict()
    for k, t, v in re.findall(r'<k>([^<]+)</k><(\w+)(?: ?/>|>([^<]*)</\w+>)', txt):
        meta[k] = v if v else ('1' if t == 't' else '')
    return meta


def parse_header(h):
    parts = h.split(',')
    d = OrderedDict()
    for i in range(0, len(parts) - 1, 2):
        d[parts[i]] = parts[i + 1]
    return d


def parse_colors(s):
    out = {}
    for c in s.split('|'):
        if not c:
            continue
        p = c.split('_')
        d = {p[i]: p[i + 1] for i in range(0, len(p) - 1, 2)}
        if '6' in d:
            out[int(d['6'])] = d
    return out


def parse_objects(body):
    objs = []
    for o in body.split(';'):
        if not o:
            continue
        p = o.split(',')
        d = {}
        for i in range(0, len(p) - 1, 2):
            d[p[i]] = p[i + 1]
        if '1' in d:
            try:
                d['_id'] = int(d['1'])
                d['_x'] = float(d.get('2', 0))
                d['_y'] = float(d.get('3', 0))
            except ValueError:
                continue
            objs.append(d)
    return objs


def load(path):
    meta = parse_plist(path)
    ls = decode_level_string(meta['k4'])
    head, _, body = ls.partition(';')
    hdr = parse_header(head)
    colors = parse_colors(hdr.get('kS38', ''))
    objs = parse_objects(body)
    name = meta.get('k2', os.path.basename(path))
    try:
        desc = base64.urlsafe_b64decode(meta.get('k3', '') + '==').decode('utf-8', 'replace')
    except Exception:
        desc = ''
    return dict(name=name, meta=meta, header=hdr, colors=colors, objs=objs, desc=desc, raw=ls)


def is_trigger(oid):
    n = NAMES.get(oid, '')
    return 'Trigger' in n or oid in (3032,)


def x_to_time_fn(objs, start_speed):
    """Return f(x)->seconds using speed portals (ignores non-checked/ordering subtleties)."""
    portals = sorted((o['_x'], SPEED_PORTAL[o['_id']]) for o in objs if o['_id'] in SPEED_PORTAL)
    segs = []  # (x_start, t_start, ups)
    x0, t0, sp = 0.0, 0.0, start_speed
    for px, s in portals:
        segs.append((x0, t0, SPEED_UPS[sp]))
        t0 += (px - x0) / SPEED_UPS[sp]
        x0, sp = px, s
    segs.append((x0, t0, SPEED_UPS[sp]))

    def f(x):
        best = segs[0]
        for s in segs:
            if s[0] <= x:
                best = s
            else:
                break
        return best[1] + (x - best[0]) / best[2]
    return f, portals
