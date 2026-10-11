# What cherryteam deco is actually made of

Test v1 was judged "not even close" to the cherryteam standard. Until now I'd only seen levels through an
approximate renderer, so I built `tools/render_real.py`: it draws a level with GD's real sprites, following
GDRWeb's placement and draw order. I then took apart frames of Green Bullet, Waterfall, cytokinesis, KOCMOC and
Penumbral with `tools/dissect.py` (layer by layer, plus a census) and `tools/zoom.py` (one structure, object by
object).

The renderer is approximate in a few ways: it skips object glow sprites, doesn't simulate pulses, rotate or follow
triggers, and guesses the camera height. That's enough to see composition, layering and recipes; the fine colour
detail is not exact.

## 1. The gap, measured (first ~12 s)

| | Test v1 | Cherryteam (5 levels) |
|---|---:|---:|
| Non-trigger objects on one screen | ~60 | 1,500–2,700 |
| Visual objects per second | ~52 | ~450–3,700 |
| Objects in a group (animated or triggered) | ~0% | ~80% |
| HSV-shifted objects | ~0% | 60–67% |
| Hazards in the first 12 s | 11 | 149–1,110 |
| Orbs in the first 12 s | 0 | 3–35 |
| Triggers in the first 12 s | 27 | 160–1,800 |
| Colour channels used on one screen | ~12 | 10–35 |

## 2. Composition: where the deco lives

Test v1 was a background painting (moon, castle silhouettes) with a flat floor in front. None of the references
work like that:

- **The gameplay structures are the deco.** Every screen is a framed corridor: structures with hazards come down
  from the top and up from the bottom, and the player threads between them. There is almost no empty sky.
- **The background is quiet.** It is black or near-black, with faint large shapes (Green Bullet: dim square
  panels and dots; Penumbral: dim bricks; KOCMOC: almost nothing). It supports the foreground and never competes
  with it.
- **The mid-ground is hazard dressing,** not scenery: spinning saws or shurikens, dressed orbs, chains, hanging
  lamps, light shafts.
- **Layers are all used.** On one Penumbral screen: B5 238, B4 131, B3 34, B2 270, B1 141, T1 257, T2 209, T3 179,
  T4 51 objects. On one Green Bullet screen, B1 holds 1,062.

## 3. Recipes found by taking structures apart

### 3.1 Structure block (Penumbral; dark masonry, the closest match to a castle)

- **Fill:** 211 Colored Inner Square on a black channel.
- **Edge:** 468 Outline Top plus 469 Outer Corner, on the OBJ channel with HSV value ×0.48 (a mid grey line).
- **Edge glow:** 503 Straight Medium Glow on a blending channel, on both sides of every edge: outward at value
  ×0.36 and inward at value ×0.68. Corners get rotated copies. This is what makes the edges read as softly lit.
- **Interior:**
  - B5 field of 5 Grid Patterned Inner Square, dark
  - 1825 grid squares
  - 277 Decorative Colored Brick at scale 0.92 with a very low value (faint masonry)
  - 1241 Small Outline Pipe Square accents
  - 503/1292 vertical light shafts with white gradients (windows or skylights)
- **Detail hung off structures:** chains, small hanging lamps (1001 pipes), a 460 pulsing-arrow pair.

### 3.2 Nested spike (Penumbral)

- **Hitbox:** a plain spike (39 Half Black Gradient Spike, or 144/145 invisible spikes).
- **Deco, three layers stacked:**
  - 217 Colored Half Spike at scale 1.0 (B1), a dark outline spike
  - the same at 0.47 on T2 (grey)
  - the same at 0.29 on T3 (white core)
- Big spikes use 216 → 218 at 0.84 → 458 at 0.7 the same way.
- The result is a spike with a lit white core and two outlines: readable at speed, and it matches the block edges.

### 3.3 Structure block (Green Bullet; circuitry)

- Black fill, with a bright outline (468/469/1202 Thick Outline).
- **3D offset:** 507 3DL Top Middle scaled ×3.64, plus a second outline offset up and right (the extruded look).
- **Interior:** a grid of 220 Colored Small Square at 0.5 (hundreds per screen), plus circuit traces (1753 Thin
  Line rotated off-grid, with 1764 Tiny Circle nodes).
- Nested spikes as in 3.2: an outline spike, a 458 Tiny Spike inside, a core.

### 3.4 Dressed orbs and saws

- **Penumbral orb:** a pink orb, a gravity portal at 0.5 on the same spot, 395 Medium Rotating Hexagon at 0.73
  (HSV value 0.34), 1525 Large Rotating Particle at 0.43, and 1886 Medium Glow Orb at 2.16 behind. Every orb gets
  this.
- **Green Bullet:** shuriken saws built from rotated spike sprites around a hub, each with a 1886 glow; the orbs get
  a white ring plus glow.

### 3.5 Painterly custom art (Waterfall)

The creatures and rocks are built from Jagged Rocks sprites (1672, 1679, 1648, 1684, 1773) used as brush strokes:

- scaled ×3 to ×19
- rotated off-grid (98% of them)
- every one HSV-shifted
- spread over ~35 colour channels on a single screen

On top of that: 1888 glows (180 on one screen), 1519 Tiny Sparkle animations, 1528 rotating particles, swirls and
wavy slabs.

### 3.6 HUD and set pieces (cytokinesis)

- Concentric glowing rings around orbs and pads, HUD frame lines, text panels.
- A cinematic opening shot: the player icon sits inside a lit tube before gameplay starts.

## 4. Rules I'm adding for v2 (on top of RULEBOOK §6)

- **R1 Corridor framing.** Gameplay screens are framed top and bottom by detailed structures with hazards. There is
  no open floor-plus-sky screen after the intro.
- **R2 Structure recipe.** Every structure = black fill + lit edge (outline + glow both sides) + interior detail + a
  3D or depth cue. No bare blocks.
- **R3 Hazard recipe.** Every spike is nested (3 layers + a separate hitbox). Every orb or pad is dressed (rotating
  ring + glow + particle). Saws and maces spin.
- **R4 Density target.** 1,200+ visible non-trigger objects per screen in the gameplay layers, and 80%+ of the deco
  grouped and animated (rotate, pulse, move or alpha).
- **R5 Quiet background.** The background stays dark and low-contrast; the theme (moon, castle) shows through set
  pieces and silhouettes that never compete with the corridor.
- **R6 Check before showing.** Every frame is checked with `render_real.py` against the reference frames before it
  goes to the requester.
