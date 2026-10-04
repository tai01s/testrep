"""Draw the gameplay layout to PNG strips (needs Pillow). Debug aid only."""

import os
from PIL import Image, ImageDraw

S = 0.5          # pixels per unit
H = 360          # y range shown: 0..H units
STRIP = 3600     # units per image


def draw(L, w, lay, outdir, band=None):
    os.makedirs(outdir, exist_ok=True)
    x_end = lay.end_col * 30.0
    n = int(x_end // STRIP) + 1
    rects, tris = w.shapes()
    for k in range(n):
        x0 = k * STRIP
        im = Image.new("RGB", (int(STRIP * S), int(H * S) + 20), (24, 22, 38))
        d = ImageDraw.Draw(im)

        def P(x, y):
            return ((x - x0) * S, (H - y) * S)

        for r in rects:
            if r[2] < x0 or r[0] > x0 + STRIP:
                continue
            a, b = P(r[0], r[3]), P(r[2], r[1])
            d.rectangle([a, b], fill=(70, 60, 110))
        for t in tris:
            if max(p[0] for p in t) < x0 or min(p[0] for p in t) > x0 + STRIP:
                continue
            d.polygon([P(*p) for p in t], fill=(110, 90, 160))
        for h in w.hazards:
            if h[2] < x0 or h[0] > x0 + STRIP:
                continue
            d.rectangle([P(h[0], h[3]), P(h[2], h[1])], fill=(255, 80, 120))
        for o in w.orbs:
            col = {"yellow": (255, 230, 60), "blue": (80, 160, 255), "pink": (255, 120, 220)}[o["kind"]]
            x, y = P(o["x"], o["y"])
            d.ellipse([x - 6, y - 6, x + 6, y + 6], outline=col, width=2)
        for p in w.portals:
            x, y = P(p["x"], p["y"])
            d.rectangle([x - 4, y - 20, x + 4, y + 20], outline=(120, 255, 160), width=1)
            d.text((x - 10, y - 32), str(p["value"]), fill=(200, 255, 200))
        if band:
            for (bx, ylo, yhi) in band:
                if x0 <= bx < x0 + STRIP:
                    a, b = P(bx, ylo), P(bx, yhi)
                    d.line([a, b], fill=(255, 255, 255))
        for sec in lay.sections:
            sx = sec["i0"] * 30
            if x0 <= sx < x0 + STRIP:
                x, _ = P(sx, 0)
                d.line([(x, 0), (x, H * S)], fill=(255, 255, 255))
                d.text((x + 3, 2), f"{sec['name']} {sec['speed']}x", fill=(255, 255, 255))
        im.save(os.path.join(outdir, f"strip_{k:02d}.png"))
