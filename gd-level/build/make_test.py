"""Build the first-10% test level: out/castle_of_shadows_test_v1.gmd"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gdlevel import Level
from art import Art
from part0_gameplay import layout
import scene_part0 as sc

PLACEHOLDER_SONG = 467339   # any whitelisted Newgrounds ID works; the NONG mp3 is attached to it with Jukebox

DESC = ('Castle Of Shadows - test build v1 (first 10%). Song: SlyphStorm - Castle Of Shadows (Instrumental), '
        'cut to 1:45 - use the NONG mp3.')


def build():
    L = layout()
    lv = Level('Castle Of Shadows (test v1)', PLACEHOLDER_SONG, start_speed='slow', description=DESC)
    sc.setup_colors(lv)
    gameplay = Art(lv, editor_layer=0)
    deco = Art(lv, editor_layer=1)
    trig = Art(lv, editor_layer=2)
    # gameplay first (hidden solids, spikes, portal)
    for (x0, y0, x1, y1) in L['solids']:
        gameplay.solid(x0, y0, x1, y1)
    for (cx, base) in L['spikes']:
        gameplay.spike(cx, base)
    for (px, sp) in L['portals']:
        lv.add(201, px, 75, checked=1)
    sc.build(deco, L)
    sc.triggers(trig, L)
    return lv, L


if __name__ == '__main__':
    lv, L = build()
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'out', 'castle_of_shadows_test_v1.gmd')
    lv.save_gmd(out)
    print('objects:', len(lv.objects), ' level string chars:', len(lv.level_string()), ' ->', os.path.abspath(out))
