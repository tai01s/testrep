"""Part 0 gameplay (cut bars 1-6): the bridge approach. Every element is placed from a song timestamp.
See plan/LEVEL_PLAN.md (Part 0 table)."""
from timeline import T, Track

TRACK = Track([(0.0, 'slow'), (T(5, 1), 'normal')])
APEX_T = 0.1945  # s from click to top of a cube jump (11.180032 / 0.958199 frames / 60)


def layout():
    x = TRACK.x
    apex = lambda t: x(t) + {'slow': 251.16, 'normal': 311.58}[TRACK.speed(t)] * APEX_T
    clicks, spikes, solids, notes = [], [], [], []

    def spike_jump(t, base=0.0, why=''):
        clicks.append(t)
        spikes.append((round(apex(t), 2), base))
        notes.append((t, 'jump spike', why))

    spike_jump(T(1, 1), why='first note, A#4 accent')
    spike_jump(T(1, 3))
    # raised deck P1 (1 block): left edge 50 units after the 2.1 click; right edge just after the 3.1 click
    t21 = T(2, 1)
    clicks.append(t21); notes.append((t21, 'jump up onto deck', ''))
    p1_x0 = round(x(t21) + 50, 2)
    n = round((x(T(3, 1)) + 29.2 - p1_x0) / 30)
    p1_x1 = round(p1_x0 + 30 * n, 2)
    solids.append((p1_x0, 0.0, p1_x1, 30.0))
    spike_jump(T(2, 3), 30.0)
    spike_jump(T(2, 4), 30.0, 'C5 melody note')
    t31 = T(3, 1)
    clicks.append(t31); notes.append((t31, 'jump off deck over 1-spike gap', 'A#4 accent'))
    spikes.append((round(p1_x1 + 25.0, 2), 0.0))
    spike_jump(T(3, 3))
    spike_jump(T(4, 1))
    spike_jump(T(4, 2))
    # rising steps on the bass pickup: step 1 (1 block), step 2 (2 blocks), ledge end just past the 5.1 click
    t43, t44 = T(4, 3), T(4, 4)
    s1_x0 = round(x(t43) + 50, 2)
    s2_x0 = round(s1_x0 + 120, 2)          # 4 blocks later (design target x(4.4)+50, within 3 units)
    ledge = round(s2_x0 + 90, 2)
    solids.append((s1_x0, 0.0, ledge, 30.0))
    solids.append((s2_x0, 30.0, ledge, 60.0))
    clicks += [t43, t44]; notes += [(t43, 'step up', 'bass C3'), (t44, 'step up', 'bass F3')]
    t51 = T(5, 1)
    clicks.append(t51); notes.append((t51, 'speed -> normal, jump off 2-block ledge (lands on 5.2)', 'beat drops in'))
    portal = (round(x(t51), 2), 'normal')
    spike_jump(T(5, 3), why='kick')
    spike_jump(T(5, 4), why='kick')
    spike_jump(T(6, 1), why='kick')
    return dict(clicks=clicks, spikes=spikes, solids=solids, portals=[portal], notes=notes,
                end_x=round(x(T(6, 1)) + 200, 2), t_end=T(6, 2) + 0.3)


if __name__ == '__main__':
    from physics_check import simulate, click_windows
    L = layout()
    for s in L['solids']:
        print('solid', s)
    for model in ('conservative', 'nominal'):
        ok, t, xx, _ = simulate(L['clicks'], L['solids'], L['spikes'], L['portals'], 'slow', L['t_end'], model)
        print('%-12s nominal run: %s (t=%.3f, x=%.1f)' % (model, 'ALIVE' if ok else 'DEAD', t, xx))
        w = click_windows(L['clicks'], L['solids'], L['spikes'], L['portals'], 'slow', L['t_end'], model)
        for (tc, what, why), win in zip(sorted(L['notes']), w):
            print('   %6.3fs  x=%7.1f  %-52s window %s' % (tc, L and __import__('part0_gameplay').TRACK.x(tc), what + (' [' + why + ']' if why else ''),
                                                       '%+d..%+d ms' % win if win else 'NONE'))
