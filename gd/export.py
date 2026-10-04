import base64, gzip, math
from gen import B, PORTAL_ID, SPEED_ID

PALETTES = {
    'violet':  ((22, 8, 44),  (190, 120, 255), (235, 215, 255)),
    'cyan':    ((4, 24, 42),  (60, 220, 255),  (210, 250, 255)),
    'pink':    ((40, 6, 32),  (255, 90, 200),  (255, 215, 240)),
    'orange':  ((40, 18, 4),  (255, 160, 60),  (255, 230, 200)),
    'green':   ((4, 34, 20),  (90, 255, 150),  (215, 255, 230)),
    'blue':    ((6, 10, 46),  (90, 140, 255),  (215, 225, 255)),
    'red':     ((46, 4, 12),  (255, 70, 95),   (255, 210, 215)),
    'yellow':  ((38, 32, 4),  (255, 225, 80),  (255, 248, 210)),
    'white':   ((6, 6, 8),    (255, 255, 255), (255, 255, 255)),
    'cyan2':   ((0, 30, 34),  (0, 255, 225),   (200, 255, 248)),
    'magenta': ((34, 0, 40),  (240, 80, 255),  (248, 210, 255)),
    'orange2': ((40, 10, 0),  (255, 120, 40),  (255, 220, 195)),
    'end':     ((12, 6, 26),  (200, 160, 255), (240, 230, 255)),
}
# channels: 1 block edge, 2 spikes, 3 block fill, 4 title text
CH_EDGE, CH_SPIKE, CH_FILL = 1, 2, 3


def obj(**kw):
    return kw


def fmt(o):
    parts = []
    for k, v in o.items():
        k = k.lstrip('k')
        if isinstance(v, float):
            v = ('%.3f' % v).rstrip('0').rstrip('.')
        parts.append(f'{k},{v}')
    return ','.join(parts)


def col_entry(ch, rgb, opacity=1.0, blend=False):
    r, g, b = rgb
    s = f'1_{r}_2_{g}_3_{b}_11_255_12_255_13_255_4_-1_6_{ch}_7_{opacity}_15_1_18_0_8_1'
    if blend:
        s = s.replace('_7_', '_5_1_7_')
    return s


def dim(rgb, f):
    return tuple(int(c * f) for c in rgb)


def build_string(L, PAL, title='INERTIA'):
    W = L.W
    objs = []
    cells = W.cells
    # blocks: exposed -> outlined block (1), interior -> plain fill (211)
    for (c, r) in sorted(cells):
        x, y = c * B + 15, r * B + 15
        exposed = any((c + dc, r + dr) not in cells for dc, dr in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        if r == 9 and (c, 10) not in cells:
            exposed = exposed or False
        if exposed:
            objs.append({'1': 1, '2': x, '3': y, '21': CH_EDGE})
        else:
            objs.append({'1': 211, '2': x, '3': y, '21': CH_FILL})
    for (x, y, rot) in W.spikes:
        o = {'1': 8, '2': x, '3': y, '21': CH_SPIKE}
        if rot:
            o['6'] = 180
        objs.append(o)
    # portals
    for d in W.portals:
        k = d['kind']; x = d['x']; y = round(d['y'], 2)
        if k in PORTAL_ID:
            objs.append({'1': PORTAL_ID[k], '2': x, '3': y})
        elif k == 'speed':
            objs.append({'1': SPEED_ID[d['val']], '2': x, '3': y})
        elif k == 'grav':
            objs.append({'1': 10 if d['val'] > 0 else 11, '2': round(x, 2), '3': y})
        elif k == 'mini':
            objs.append({'1': 101 if d['val'] else 99, '2': x, '3': y})
    # colour triggers per section + flash pulse
    for i, (x, name) in enumerate(PAL):
        bg, edge, spike = PALETTES[name]
        tx = max(0, x - 60)
        dur = 0.0 if i == 0 else 0.4
        for ch, rgb in ((1000, bg), (1001, dim(bg, 0.55)), (1009, dim(bg, 0.55)), (1002, edge),
                        (CH_EDGE, edge), (CH_SPIKE, spike), (CH_FILL, dim(bg, 0.45)), (4, edge)):
            objs.append({'1': 899, '2': tx, '3': 345 + (ch % 7) * 30, '36': 1, '7': rgb[0], '8': rgb[1], '9': rgb[2],
                         '10': dur, '35': 1, '23': ch})
        if i > 0:
            # bright flash of the background on every mode change
            objs.append({'1': 1006, '2': x - 15, '3': 600, '36': 1, '7': edge[0], '8': edge[1], '9': edge[2],
                         '45': 0, '46': 0.05, '47': 0.45, '51': 1000, '52': 0})
    # title + ending text
    def text(x, y, s, sc):
        return {'1': 914, '2': x, '3': y, '31': base64.urlsafe_b64encode(s.encode()).decode(), '32': sc, '21': 4}
    objs.append(text(165, 165, title, 1.6))
    objs.append(text(285, 120, 'moment / gravity  III', 0.5))
    endx = L.sections[-1][1]
    objs.append(text(endx - 200, 150, 'GG', 1.6))
    # header
    p0 = PALETTES[PAL[0][1]]
    colors = '|'.join([
        col_entry(1000, p0[0]), col_entry(1001, dim(p0[0], 0.55)), col_entry(1009, dim(p0[0], 0.55)),
        col_entry(1002, p0[1], blend=True), col_entry(1004, (255, 255, 255)),
        col_entry(CH_EDGE, p0[1]), col_entry(CH_SPIKE, p0[2]), col_entry(CH_FILL, dim(p0[0], 0.45)),
        col_entry(4, p0[1], blend=True)]) + '|'
    hdr = (f'kS38,{colors},kA13,0,kA15,0,kA16,0,kA14,,kA6,0,kA7,0,kA25,0,kA17,0,kA18,0,kS39,0,kA2,0,kA3,0,'
           f'kA8,0,kA4,2,kA9,0,kA10,0,kA22,0,kA23,0,kA24,0,kA27,1,kA40,1,kA41,1,kA42,1,kA28,0,kA29,0,kA31,1,'
           f'kA32,1,kA36,0,kA43,0,kA44,0,kA45,1,kA33,1,kA34,1,kA35,0,kA37,1,kA38,1,kA39,1,kA19,0,kA26,0,'
           f'kA20,0,kA21,0,kA11,0')
    s = hdr + ';' + ';'.join(fmt(o) for o in objs) + ';'
    return s, len(objs)


def write_gmd(path, name, desc, levelstr, nobj, song=1101957):
    comp = base64.urlsafe_b64encode(gzip.compress(levelstr.encode(), mtime=0)).decode()
    d64 = base64.urlsafe_b64encode(desc.encode()).decode()
    xml = ('<?xml version="1.0"?><plist version="1.0" gjver="2.0"><dict>'
           f'<k>kCEK</k><i>4</i><k>k2</k><s>{name}</s><k>k3</k><s>{d64}</s><k>k4</k><s>{comp}</s>'
           '<k>k5</k><s></s><k>k13</k><t /><k>k21</k><i>2</i><k>k16</k><i>1</i><k>k23</k><i>3</i>'
           f'<k>k45</k><i>{song}</i><k>k48</k><i>{nobj}</i><k>k50</k><i>45</i><k>k66</k><i>10</i>'
           f'<k>k104</k><s>{song}</s><k>kI1</k><r>0</r><k>kI2</k><r>150</r><k>kI3</k><r>1</r></dict></plist>')
    open(path, 'w').write(xml)
