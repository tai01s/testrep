import sys, os
from collections import Counter, defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from render import *

def lum(rgb): return 0.2126*rgb[0]+0.7152*rgb[1]+0.0722*rgb[2]

def cat(name, oid):
    if oid in ORBS or oid in PADS or oid in GAMEMODE_PORTAL or oid in SPEED_PORTAL or oid in OTHER_PORTAL: return 'interactive'
    if ('Spike' in name or 'Saw' in name or 'Hazard' in name) and 'Decorative' not in name: return 'hazard'
    if 'Glow' in name: return 'glow'
    if 'Particle' in name: return 'particle'
    if 'Outline' in name or '3DL' in name or 'Line' in name: return 'line/outline'
    if 'Inner Square' in name or 'Colored Square' in name or 'Colored Block' in name: return 'fill'
    return 'other'

for path in sys.argv[1:]:
    L = load(path)
    objs = L['objs']
    f, _ = x_to_time_fn(objs, KA4_SPEED.get(int(L['header'].get('kA4', 0) or 0), '1x'))
    colors, galpha, ghidden = sim_state(L, 10**9)  # end-state palette approximation
    pal = Palette(L['colors'])
    print('='*90); print(L['name'])
    # layer roles
    roles = defaultdict(Counter)
    lum_by = defaultdict(list)
    for o in objs:
        oid = o['_id']; name = NAMES.get(oid, '')
        if is_trigger(oid): continue
        c = cat(name, oid)
        z = ZLAYER.get(int(o.get('24', 0) or 0), '?')
        roles[c][z] += 1
        cid = int(o.get('21', 0) or 0) or int(o.get('22', 0) or 0) or (1010 if 'Black' in name else 1004)
        rgb, opa, blend = pal.get(cid)
        lum_by[c].append(lum(rgb) * opa)
    total = sum(sum(v.values()) for v in roles.values())
    for c in ('hazard','fill','line/outline','glow','particle','other','interactive'):
        v = roles[c]; n = sum(v.values())
        if not n: continue
        lums = lum_by[c]
        print('  %-13s %5.1f%%  layers: %s' % (c, 100*n/total, ', '.join('%s %d%%' % (k, 100*x//n) for k, x in v.most_common(5))))
    # pulse timing
    ts = sorted(set(round(f(o['_x']), 3) for o in objs if o['_id'] in (1006,) and o.get('62') != '1' and o.get('11') != '1'))
    d = [round(b - a, 2) for a, b in zip(ts, ts[1:]) if 0.15 < b - a < 2.0]
    common = Counter(d).most_common(6)
    print('  position-triggered pulse moments: %d; most common gaps (s): %s' % (len(ts), common))
    if common:
        g = common[0][0]
        print('  -> if that gap is 1 beat: %.0f BPM; if half-beat: %.0f BPM' % (60/g, 30/g))
    bpm = [o for o in objs if o['_id'] == 3642]
    if bpm: print('  BPM trigger(s):', [(o.get('498'), o.get('499'), o.get('500')) for o in bpm][:3])
    # guidelines in header
    g = L['header'].get('kA14', '')
    if g:
        parts = g.split('~')
        ts2 = []
        for i in range(0, len(parts)-1, 2):
            try: ts2.append(float(parts[i]))
            except ValueError: pass
        dd = [round(b-a,3) for a,b in zip(ts2, ts2[1:])]
        print('  editor guidelines: %d marks, common spacing %s' % (len(ts2), Counter(dd).most_common(3)))
