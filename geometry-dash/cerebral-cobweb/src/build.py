"""Build the decorated level: original layout + generated hell deco.

usage: python3 build.py [input.gmd] [output.gmd]

The original objects are copied as their exact original text. The build
fails if any original object string differs in the output.
"""
import os
import sys
from collections import Counter

import gdlevel as gl
from deco_lib import Scene
from gdobj import (GROUPS, NO_TOUCH, Z_LAYER, GRAD_BL, GRAD_BR, GRAD_TL, GRAD_TR,
                   TARGET, SECOND_TARGET)
import intro_hell

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_IN = os.path.join(HERE, "..", "input", "Cerebral_Cobweb_layout.gmd")
DEFAULT_OUT = os.path.join(HERE, "..", "out", "Cerebral_Cobweb_hell_intro.gmd")

LAYOUT_GROUPS = set(range(1, 16))


def color_entry(cid, rgb, opacity=1.0, blending=False):
    kv = [["1", rgb[0]], ["2", rgb[1]], ["3", rgb[2]], ["11", 255], ["12", 255], ["13", 255],
          ["4", -1], ["6", cid]]
    if blending:
        kv.append(["5", 1])
    op = f"{opacity:.3f}".rstrip("0").rstrip(".")
    kv += [["7", op], ["15", 1], ["18", 0], ["8", 1]]
    return [[str(k), str(v)] for k, v in kv]


def apply_colors(header, sc, overrides):
    pairs = gl.parse_header(header)
    for p in pairs:
        if p[0] == "kS38":
            cols = gl.parse_colors(p[1])
            by_id = {dict(c).get("6"): c for c in cols}
            for cid, (rgb, op, bl) in overrides.items():
                entry = color_entry(cid, rgb, op, bl)
                if str(cid) in by_id:
                    idx = cols.index(by_id[str(cid)])
                    cols[idx] = entry
                else:
                    cols.append(entry)
            for name, c in sc.channels.items():
                if str(c["id"]) in by_id:
                    raise ValueError(f"deco channel {c['id']} collides with an existing channel")
                cols.append(color_entry(c["id"], c["rgb"], c["opacity"], c["blending"]))
            p[1] = gl.build_colors(cols)
            break
    else:
        raise ValueError("no kS38 colour string in header")
    return gl.build_header(pairs)


def validate(orig_raw, out_raw, deco):
    # 1) layout untouched, same order, exact text
    assert out_raw[:len(orig_raw)] == orig_raw, "original layout objects changed!"
    # 2) deco never joins layout groups, never collides
    all_groups = Counter()
    for o in deco:
        gs = o.get(GROUPS) or []
        bad = set(gs) & LAYOUT_GROUPS
        assert not bad, f"deco object uses layout group {bad}: {o.to_str()}"
        assert len(gs) <= 10
        for g in gs:
            all_groups[g] += 1
        if o.get(1) == 211:
            assert str(o.get(NO_TOUCH)) == "1", "211 without NoTouch"
    # 3) every gradient corner group exists and holds exactly one object
    for o in deco:
        if o.get(1) == 2903:
            for k in (GRAD_BL, GRAD_BR, GRAD_TL, GRAD_TR):
                g = int(o.get(k))
                assert all_groups[g] == 1, f"gradient corner group {g} has {all_groups[g]} objects"
    # 4) trigger targets exist (follow group 1 is the layout platform)
    for o in deco:
        oid = o.get(1)
        if oid in (1006,) and str(o.get(52)) != "1":
            continue  # colour-channel pulse
        if oid in (1007, 1268, 901, 1347, 1006):
            t = int(o.get(TARGET))
            assert all_groups[t] > 0, f"trigger {oid} targets empty group {t}"
        if oid == 1347:
            assert int(o.get(SECOND_TARGET)) == 1
    return all_groups


def main(src=DEFAULT_IN, dst=DEFAULT_OUT):
    gmd = gl.GmdFile(src)
    header, orig_raw = gl.split_level(gmd.level)
    layout = [gl.parse_obj(r) for r in orig_raw]

    sc = Scene(group_start=200, channel_start=100)
    info = intro_hell.build(sc, layout)

    overrides = {
        1000: ((8, 2, 6), 1.0, False),     # BG: near-black wine (layout BG pulses still play on it)
        32: ((255, 96, 32), 1.0, False),   # layout outlines/spikes in the intro (only used x 29-2634)
        2: ((255, 86, 28), 1.0, False),    # front blade of the layered saws (only used at 2045/2185)
        3: ((34, 8, 10), 1.0, False),      # back blade
    }
    new_header = apply_colors(header, sc, overrides)
    deco_raw = [o.to_str() for o in sc.objs]
    out_raw = orig_raw + deco_raw
    level = new_header + ";" + ";".join(out_raw) + ";"

    groups = validate(orig_raw, out_raw, sc.objs)
    # round trip check
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    # distinct name so the import does not get confused with the original layout
    gmd.xml = gmd.xml.replace("<k>k2</k><s>Cerebral Cobweb</s>",
                              "<k>k2</k><s>Cerebral Cobweb HELL v1</s>", 1)
    gmd.write(dst, level, len(out_raw))
    back = gl.GmdFile(dst)
    h2, raw2 = gl.split_level(back.level)
    assert raw2[:len(orig_raw)] == orig_raw
    assert len(raw2) == len(out_raw)

    ids = Counter(o.get(1) for o in sc.objs)
    print(f"layout objects: {len(orig_raw)} (unchanged)")
    print(f"deco objects:   {len(sc.objs)}  gradients: {sc.grad_count}  groups used: {len(groups)}"
          f"  channels: {len(sc.channels)}")
    print("by id:", dict(ids.most_common()))
    print("wrote", os.path.abspath(dst))
    return sc


if __name__ == "__main__":
    main(*sys.argv[1:])
