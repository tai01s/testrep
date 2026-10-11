import sys, os, json
from collections import Counter, defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gmd import *

LEVELS = sys.argv[1:]


def rgb(d):
    if d.get('9') not in (None, '0', '-1') and d.get('9'):
        return 'copy:%s(hsv %s)' % (d['9'], d.get('10', ''))
    if d.get('4') not in (None, '-1', '0'):
        return 'player%s' % d['4']
    return '#%02x%02x%02x' % (int(float(d.get('1', 255))), int(float(d.get('2', 255))), int(float(d.get('3', 255))))


def analyze(path):
    L = load(path)
    objs, hdr, meta = L['objs'], L['header'], L['meta']
    out = []
    P = out.append
    start_speed = KA4_SPEED.get(int(hdr.get('kA4', 0) or 0), '1x')
    start_mode = KA2_MODE.get(int(hdr.get('kA2', 0) or 0), '?')
    f, sportals = x_to_time_fn(objs, start_speed)
    # level end: furthest gameplay-relevant x (use 99.5 percentile of all objects to drop stray far deco)
    xs = sorted(o['_x'] for o in objs)
    endx = max((o['_x'] for o in objs if o['_id'] in (3600,)), default=None)  # end trigger
    p995 = xs[int(len(xs) * 0.995)] if xs else 0
    P('=' * 100)
    P('LEVEL: %s by %s | song k45=%s k8=%s | objs=%d | desc=%r' % (L['name'], meta.get('k5'), meta.get('k45'), meta.get('k8'), len(objs), L['desc']))
    P('start: mode=%s speed=%s mini=%s dual=%s songOffset=%s fadeIn=%s fadeOut=%s bg=%s ground=%s mg=%s line=%s font=%s platformer=%s' % (
        start_mode, start_speed, hdr.get('kA3'), hdr.get('kA8'), hdr.get('kA13'), hdr.get('kA15'), hdr.get('kA16'), hdr.get('kA6'), hdr.get('kA7'), hdr.get('kA25'), hdr.get('kA17'), hdr.get('kA18'), hdr.get('kA22')))
    P('x-range: min=%.0f max=%.0f p99.5=%.0f endTrigger=%s -> est length %.1fs (p99.5)' % (xs[0], xs[-1], p995, endx, f(endx or p995)))
    # timeline
    events = []
    for o in objs:
        i = o['_id']
        if i in GAMEMODE_PORTAL:
            events.append((o['_x'], GAMEMODE_PORTAL[i]))
        elif i in SPEED_PORTAL:
            events.append((o['_x'], 'speed ' + SPEED_PORTAL[i]))
        elif i in OTHER_PORTAL:
            events.append((o['_x'], OTHER_PORTAL[i]))
        elif i == 31:
            pass
    events.sort()
    P('TIMELINE (time s @ x : event)  [start %s %s]' % (start_mode, start_speed))
    line = []
    last = None
    for x, e in events:
        key = (round(x / 15), e)
        if key == last:
            continue
        last = key
        line.append('%5.1fs %s' % (f(x), e))
    for i in range(0, len(line), 6):
        P('   ' + ' | '.join(line[i:i + 6]))
    # counts
    c = Counter(o['_id'] for o in objs)
    trig = Counter()
    deco_like = 0
    for i, n in c.items():
        if is_trigger(i):
            trig[NAMES.get(i, str(i))] += n
    orbs = Counter(); pads = Counter()
    for i, n in c.items():
        if i in ORBS: orbs[ORBS[i]] += n
        if i in PADS: pads[PADS[i]] += n
    P('orbs: %s' % dict(orbs.most_common()))
    P('pads: %s' % dict(pads.most_common()))
    P('triggers total=%d: %s' % (sum(trig.values()), ', '.join('%s=%d' % kv for kv in trig.most_common(30))))
    P('top 40 objects:')
    for i, n in c.most_common(40):
        P('   %6d x %5d %s' % (n, i, NAMES.get(i, '?')))
    # layers
    zl = Counter(ZLAYER.get(int(o.get('24', 0) or 0), o.get('24')) for o in objs if not is_trigger(o['_id']))
    P('z-layers (non-trigger): %s' % dict(zl.most_common()))
    zo = Counter(int(o.get('25', 0) or 0) for o in objs if not is_trigger(o['_id']))
    P('z-order spread: min=%d max=%d distinct=%d' % (min(zo), max(zo), len(zo)))
    blend_cols = [cid for cid, d in L['colors'].items() if d.get('5') == '1']
    # color usage
    cu = Counter()
    for o in objs:
        if is_trigger(o['_id']):
            continue
        cu[int(o.get('21', 0) or 0)] += 1
        if '22' in o:
            cu[int(o['22'])] += 1
    P('base colour channels (%d defined, blending on: %s):' % (len(L['colors']), blend_cols))
    for cid in sorted(L['colors'], key=lambda k: -cu.get(k, 0))[:28]:
        d = L['colors'][cid]
        P('   ch%-5d %-24s opa=%s blend=%s used_by=%d' % (cid, rgb(d), d.get('7', '1'), d.get('5', '0'), cu.get(cid, 0)))
    # colour trigger targets
    ct = defaultdict(list)
    for o in sorted((o for o in objs if o['_id'] == 899), key=lambda o: o['_x']):
        tgt = int(o.get('23', 1) or 1)
        col = '#%02x%02x%02x' % (int(float(o.get('7', 255))), int(float(o.get('8', 255))), int(float(o.get('9', 255))))
        if o.get('50'):
            col = 'copy%s' % o['50']
        ct[tgt].append((round(f(o['_x']), 1), col, o.get('10', '0.5')))
    P('colour triggers on BG(1000)/G(1001)/MG(1013)/Line(1002): ')
    for tgt in (1000, 1001, 1009, 1013, 1002):
        if ct.get(tgt):
            P('   %d: %s' % (tgt, ' '.join('%ss->%s(%ss)' % e for e in ct[tgt][:40])))
    # hsv usage
    hsv = sum(1 for o in objs if o.get('41') == '1' or o.get('42') == '1')
    P('objects with HSV adjust: %d (%.1f%%)' % (hsv, 100.0 * hsv / max(1, len(objs))))
    scaled = sum(1 for o in objs if float(o.get('32', 1) or 1) != 1 or o.get('128') or o.get('129'))
    rotated = sum(1 for o in objs if float(o.get('6', 0) or 0) % 90 != 0)
    P('scaled objects: %d (%.1f%%)  off-90 rotated: %d (%.1f%%)' % (scaled, 100.0 * scaled / len(objs), rotated, 100.0 * rotated / len(objs)))
    grouped = sum(1 for o in objs if o.get('57'))
    P('objects with groups: %d (%.1f%%)' % (grouped, 100.0 * grouped / len(objs)))
    # density per 5 seconds
    bins = Counter()
    for o in objs:
        if is_trigger(o['_id']):
            continue
        bins[int(f(o['_x']) // 5)] += 1
    P('non-trigger objects per 5s window: ' + ' '.join('%d:%d' % (k * 5, bins[k]) for k in sorted(bins) if k >= 0))
    return '\n'.join(out), L


if __name__ == '__main__':
    for p in LEVELS:
        txt, _ = analyze(p)
        print(txt)
