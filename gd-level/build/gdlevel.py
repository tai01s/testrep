"""Write Geometry Dash 2.2 levels as GDShare-compatible .gmd files.

Formats follow GDDocs and the exports in research/ (header keys, kS38 colour string, object key layout, plist
wrapper). Nothing here simulates gameplay; GD does that when the level is imported.
"""
import base64
import gzip
from collections import OrderedDict
from xml.sax.saxutils import escape

# Z layers as stored in the level string (Geode ZLayer enum)
Z = dict(B5=-5, B4=-3, B3=-1, B2=1, B1=3, DEFAULT=0, T1=5, T2=7, T3=9, T4=11)

# Horizontal speeds, units/second (wiki Portals page: 8.372 / 10.386 / 12.914 / 15.6 / 19.2 blocks/s)
SPEED_UPS = {'slow': 251.16, 'normal': 311.58, 'fast': 387.42, 'faster': 468.0, 'fastest': 576.0}
SPEED_KA4 = {'normal': 0, 'slow': 1, 'fast': 2, 'faster': 3, 'fastest': 4}
SPEED_PORTAL_ID = {'slow': 200, 'normal': 201, 'fast': 202, 'faster': 203, 'fastest': 1334}

# Level-start keys copied from a 2.2 level export (Society), so compatibility flags match the current game.
HEADER_TEMPLATE = ('kA13,0,kA15,0,kA16,0,kA6,13,kA7,10,kA25,0,kA17,1,kA18,0,kS39,0,kA2,0,kA3,0,kA8,0,kA4,0,'
                   'kA9,0,kA10,0,kA22,0,kA23,0,kA24,0,kA27,1,kA40,1,kA48,0,kA41,1,kA42,1,kA28,0,kA29,0,kA31,1,'
                   'kA32,1,kA36,0,kA43,0,kA44,0,kA45,1,kA46,0,kA47,0,kA33,1,kA34,1,kA35,0,kA37,1,kA38,1,kA39,1,'
                   'kA19,0,kA26,0,kA20,0,kA21,0,kA11,0')

# Friendly names for object keys (GDDocs level-string table + gd-info-explorer schema)
KEYS = dict(
    id=1, x=2, y=3, flip_x=4, flip_y=5, rot=6, red=7, green=8, blue=9, duration=10, touch=11, checked=13,
    blending=17, editor_layer=20, color=21, color2=22, target_color=23, z_layer=24, z_order=25, move_x=28,
    move_y=29, easing=30, scale=32, opacity=35, interactible=36, hsv_on=41, hsv=43, fade_in=45, hold=46,
    fade_out=47, pulse_hsv_on=48, pulse_hsv=49, copy_color=50, target=51, target_type=52, activate=56,
    groups=57, lock_player_x=58, lock_player_y=59, editor_layer2=61, spawn_trig=62, dont_fade=64,
    dont_enter=67, multi=87, ease_rate=85, exclusive=86, high_detail=103, no_touch=121, scale_x=128,
    scale_y=129, hide=135, lock_cam_x=141, lock_cam_y=142, mod_x=143, mod_y=144, opt_hide_ground=161,
    opt_hide_mg=195, zoom=371, bpm=498, bpm_speed=499, bpm_disable=500, bpb=501,
)


def fmt(v):
    if isinstance(v, bool):
        return '1' if v else '0'
    if isinstance(v, int):
        return str(v)
    if isinstance(v, float):
        s = ('%.4f' % v).rstrip('0').rstrip('.')
        return s if s not in ('', '-0') else '0'
    if isinstance(v, (list, tuple)):
        return '.'.join(str(int(g)) for g in v)
    return str(v)


class Level:
    def __init__(self, name, song_id, start_speed='normal', start_mode=0, description=''):
        self.name = name
        self.song_id = song_id
        self.description = description
        self.header = OrderedDict()
        p = HEADER_TEMPLATE.split(',')
        for k, v in zip(p[0::2], p[1::2]):
            self.header[k] = v
        self.header['kA4'] = str(SPEED_KA4[start_speed])
        self.header['kA2'] = str(start_mode)
        self.colors = OrderedDict()
        self.objects = []

    # ---- colours -------------------------------------------------------------------------------
    def color(self, ch, rgb=(255, 255, 255), opacity=1.0, blending=False, copy=None, hsv=None):
        self.colors[ch] = dict(rgb=rgb, opacity=opacity, blending=blending, copy=copy, hsv=hsv)

    def _color_string(self):
        parts = []
        for ch, c in self.colors.items():
            r, g, b = c['rgb']
            e = ['1', r, '2', g, '3', b, '11', 255, '12', 255, '13', 255, '4', -1, '6', ch]
            if c['blending']:
                e += ['5', 1]
            e += ['7', fmt(float(c['opacity'])), '15', 1, '18', 0, '8', 1]
            if c['copy']:
                e += ['9', c['copy'], '10', c['hsv'] or '0a1a1a0a0']
            parts.append('_'.join(str(x) for x in e))
        return '|'.join(parts) + '|'

    # ---- objects -------------------------------------------------------------------------------
    def add(self, oid, x, y, **kw):
        o = OrderedDict([(1, oid), (2, x), (3, y)])
        for k, v in kw.items():
            if v is None:
                continue
            if k in KEYS:
                key = KEYS[k]
            elif isinstance(k, int) or str(k).isdigit():
                key = int(k)
            else:
                key = k  # start-pos keys such as kA4 are stored by name
            o[key] = v
        self.objects.append(o)
        return o

    def level_string(self):
        head = 'kS38,' + self._color_string() + ',' + ','.join('%s,%s' % kv for kv in self.header.items())
        body = ';'.join(','.join('%s,%s' % (k, fmt(v)) for k, v in o.items()) for o in self.objects)
        return head + ';' + body + ';'

    def encoded(self):
        raw = self.level_string().encode('utf-8')
        return base64.urlsafe_b64encode(gzip.compress(raw, mtime=0)).decode('ascii')

    def save_gmd(self, path):
        desc = base64.urlsafe_b64encode(self.description.encode('utf-8')).decode('ascii')
        items = [('kCEK', 'i', 4), ('k2', 's', self.name), ('k4', 's', self.encoded()), ('k3', 's', desc),
                 ('k21', 'i', 2), ('k16', 'i', 1), ('k17', 'i', 22), ('k45', 'i', self.song_id),
                 ('k13', 't', True), ('k47', 't', True), ('k48', 'i', len(self.objects)), ('k50', 'i', 47),
                 ('k80', 'i', 0)]
        out = ['<?xml version="1.0"?><plist version="1.0" gjver="2.0"><dict>']
        for k, t, v in items:
            out.append('<k>%s</k>' % k)
            out.append('<t />' if t == 't' else '<%s>%s</%s>' % (t, escape(str(v)), t))
        out.append('</dict></plist>')
        with open(path, 'w', encoding='utf-8') as f:
            f.write(''.join(out))
