# Level Rulebook: blue-black extreme demon (target: around AREDL #600)

This is the contract for building the level. Every rule has a reason and a source. **MUST** rules are never broken.
**SHOULD** rules are only broken with a written reason. **AVOID** lists known failure patterns. Anything marked
**PENDING** waits on your answers (§9).

Evidence and sources are in `research/`:
- `FINDINGS.md` answers your six questions.
- `reference-levels.md` is the decoded data from your 8 levels.
- `aredl-600.md` covers the difficulty target.

Source tags used below:
- `[GDCS]`: GD Creator School guides
- `[REF]`: what your reference levels do (decoded data)
- `[DATA]`: measured numbers
- `[WIKI]`: GD wiki
- `[MINE]`: my own synthesis, flagged so you can push back

---

## 0. The brief (as I understand it)

| | |
|---|---|
| Palette | Blue-black. The background is blue-black and the level follows it. |
| Difficulty | Extreme demon, **around AREDL #600** (Bloodbath / Sapphire Angel / Monstercat tier). **PENDING Q2** |
| Song | Your YouTube link. **PENDING Q1:** I can't open YouTube from here. |
| Length | Cut down unless we go XL. **PENDING Q6** |
| Priority | Deco first, but gameplay must be balanced and fair. |
| Format | A `.gmd` you import with GDShare (the same format you sent me). GD runs the physics. |
| Object limit | None. Your references go up to 414k objects. Performance (active objects on screen) still matters (§6.12). |

---

## 1. Definition of "good": the acceptance checklist

A part is only finished when it passes all nine checks. The full level is finished when every part passes and
full-length runs pass too.

| # | Check | How it's tested |
|---|---|---|
| G1 | **Reliability:** no bugs, skips or secret ways | Play the part from its Start Pos; try to cheese it. Test at 60 Hz and at your highest refresh rate `[GDCS refresh-rates]` |
| G2 | **Fairness/consistency:** every death is explainable, and similar clicks give similar results | Each part beaten from Start Pos with zero "what killed me?" deaths `[GDCS consistent-gameplay]` |
| G3 | **Readability:** solid vs deadly vs decoration is obvious | Greyscale screenshot test; a first-time viewer can tell the path from a single frame `[GDCS backgrounds, light-3]` |
| G4 | **Sync:** strong notes get big events | Every gamemode/speed change sits on beat 1 or 3; the drop starts on a downbeat `[GDCS sync-rhythm]` |
| G5 | **Intent:** everything has a reason | Each part's row in the level plan names *why* this gamemode/speed/effect `[GDCS using-gamemodes]` |
| G6 | **Balance:** difficulty and deco quality stay consistent | Difficulty/intensity chart has no unexplained spikes; no part's deco is visibly weaker `[GDCS playtesting]` |
| G7 | **Cohesion:** one vision | Palette, hazard designs and shape language stay consistent (§6) `[GDCS playtesting "presentation"]` |
| G8 | **Performance:** no lag spikes | Show Info Label check in the heaviest moments; LDM works `[GDCS low-detail-mode]` |
| G9 | **Enjoyability:** fun, not just correct | Your playtest notes; and ideally someone else's `[GDCS playtesting]` |

---

## 2. Authentic gameplay without simulating physics

**P1 (MUST).** I never fake or simulate physics. I place objects and **GD simulates them**. The deliverable is a
real level file.

**P2 (MUST).** All timing comes from the exact speed table `[WIKI Portals]`:

| Portal | Blocks/s | Units/s |
|---|---:|---:|
| Slow | 8.372 | 251.16 |
| Normal | 10.386 | 311.58 |
| Fast | 12.914 | 387.42 |
| Very fast | 15.6 | 468.0 |
| Extremely fast | 19.2 | 576.0 |

Every click target is placed at `x = x₀ + v·(t − t₀)` from the song's beat map. Sync is arithmetic, not
guesswork.

**P3 (SHOULD).** Prefer mechanics whose geometry is fixed `[GDCS using-gamemodes]`:
- **Wave:** 45°, or about 63.4° when mini. It doesn't change with speed.
- **Spider:** snaps straight up or down.
- **Ball/spider gravity flips** follow fixed paths.
- **Orbs and pads hit from a platform** launch the same way every time.
- **Platforms reset momentum.** Use them before anything precise.

**P4 (MUST).** Consistency rules `[GDCS consistent-gameplay]`:
- No orb chains as a main mechanic.
- No click right before a portal. Put the portal *before* the orb.
- Every gamemode entry comes from a predictable path: a platform, pad or slope reset.
- Use J/H blocks or an options-trigger input lock where a held click could double-jump.

**P5 (MUST).** Speed portals:
- Placed where the player's height is predictable.
- Tall enough that they can't be jumped over. The music-line/hit-point issue is in `[GDCS making-sync]`.

**P6 (MUST).** **Start Pos at every part and every transition**, so you can test each piece alone. They get disabled
in the final.

**P7 (MUST).** Nothing is "done" until it's been **beaten in GD from its Start Pos**, by you or by a macro bot if you
use one. I keep a test log (`TESTLOG.md`) of every report and every fix.

**P8 (AVOID).** Frame-perfects, refresh-rate-dependent timings, alignment tricks, and blind or invisible paths.
That's not the #600 style `[GDCS frame-perfects]` `[DATA aredl-600]`.

**P9 (SHOULD).** Where possible, base tricky spacings on geometry from verified levels. Your references are proven
possible.

---

## 3. Song rules

**S1 (MUST).** Before building, make the **beat map**:
- BPM, beats per bar, and downbeat times.
- The section map: intro / build / drop / break / drop 2 / outro.
- An energy curve.

I'll analyse the audio file myself (beat tracking + onset/energy analysis), then put a **BPM trigger** in the level
for editor guides (keys 498/501) `[GDCS bpm]`.

**S2 (MUST).** Cuts:
- Only on **phrase boundaries** (4/8/16 bars) and on **downbeats**.
- Never through a sustained note.
- Never inside a build-up's last 2 bars.
- The tempo grid stays continuous across the cut. `[MINE, standard audio-editing practice]`

**S3.** **Which cutting method** depends on where the song comes from:

**If the song is on Newgrounds or the music library:**
- **Start offset** + fade-in removes the intro, as Antarctic Lights (61.5 s) and Thinking Space II (117 s) do `[REF]`.
- Internal cuts use a **Song trigger** with Start/End in milliseconds (1000 = 1 s) and short fades. GRIEF does this
  `[REF]`.
- Every jump cut must be tested from the Start Pos *and* in practice mode. GRIEF places extra copies of its Song
  triggers, which looks like restart/practice-mode safety `[REF]`.

**If the song is a NONG:**
- The edits are baked into the mp3: cuts with crossfades, tempo-only stretch, pitch-only shift.
- The level description says where to get the file.
- **Warning:** everyone else hears the original unless they install it `[GDCS choosing-a-song]`.

**S4 (MUST).** In-game song **speed** is varispeed: rate = 2^(steps/12), and pitch moves with tempo.
- ±1 step ≈ ±5.9%.
- Only use it if a small, deliberate change sounds right. Never use it to "fix" sync. `[GDCS song-edit-song]`

**S5 (SHOULD).** Target length is **PENDING Q6**.
- Around #600, 57% of extremes are tagged Long; 18% XL; 9% XXL `[DATA]`.
- My default proposal: keep intro-to-final-drop at **~70–110 s**.

---

## 4. Structure and the drop

**D1 (MUST).** One **level plan table** before any building. Each part gets one row:
- time range and song section
- gamemode(s) + why
- speed
- difficulty (1–10)
- intensity (1–10)
- palette state
- transition type
- signature deco idea

`[GDCS planning-a-level, progression]`

**D2 (MUST).** **A drop is contrast.**
- The build's last bars lower or hold *something* (speed, density, brightness, or clicks) so the drop has room.
- Speed reads relative to what came before `[GDCS making-fast-gameplay]`.

**D3 (MUST).** **Drop checklist.** All of these land on beat 1 of the drop bar:
1. A gamemode change **or** a big player movement. Small movement = weak impact `[GDCS sync-rhythm]`.
2. A speed **long burst**: up to +2 steps from the build speed, held `[GDCS creating-gameplay]`.
3. A palette lift: the BG rises a few value points, and the glow family brightens.
4. Deco density rises about 2–4×. References: Society ~1–1.9k → 6.8k, Thinking Space II 11.1k → 28.6k objects per
   5 s `[DATA]`.
5. The pulse layer switches to 8th/16th notes. References pulse at about 0.16–0.36 s gaps `[DATA]`.
6. **At most one** impact effect, under a second: shake, shockwave, or radial blur + black lens circle
   `[GDCS using-shaders]`.

**D4 (SHOULD).** **Build-up toolkit:**
- Speed easing: 1-step increases, spaced wider as speed rises `[GDCS creating-gameplay]`.
- Rising click density.
- Pulse rate doubling.
- A slow camera zoom-in.
- An optional glitch ramp.
- The last beat is a **breath**: a short darkening or freeze, then a hard cut into the drop.

**D5 (MUST).** **Macro flow:**
- Intensity and difficulty must keep changing.
- After a peak: hold briefly, then break or escalate.
- No 16-bar stretch with the same mode, speed and pattern density, unless the music is literally static.

`[GDCS progression, intensity]`

**D6 (SHOULD).** Part transitions are chosen per song moment from five types `[GDCS animation-5-transitions]`:

| Type | Use it for |
|---|---|
| Hard cut | Sudden song changes, glitch hits |
| Fade | Slow or gentle moments; needs time |
| Screen wipe | Has a direction; good inside a drop |
| Match cut (shape / momentum / colour) | Changing part *and* keeping continuity |
| Continuous | Seamless; the most work and the most lag |

---

## 5. Gameplay balance

**B1 (MUST).** Every gamemode is chosen **for the music** `[GDCS using-gamemodes]`:

| Gamemode | Character | Use it when |
|---|---|---|
| Cube | Versatile, snappy | Default for rhythmic parts |
| Ship | Floaty, air control | Flowing/long notes; orbs give punch |
| Ball | Controlled repetition | Repeating riffs |
| UFO | Floaty but snappy | Repetitive, slower patterns |
| Wave | Sharp, no physics, "most limiting path" | Intense, angular phrases. Strong notes = sharp turns |
| Robot | Long holds | Long notes |
| Spider | Click emphasis, high CPS | Snappy repeated hits |
| Swing | Smooth flow | Calm-ish, curvy phrases |

**B2 (MUST).** **Intensity ladder** `[MINE, from GDCS mode properties and "speed is relative"]`:

| Rung | What sits there |
|---:|---|
| 1 | Cube, robot or ball at slow/normal speed |
| 2 | UFO, ship, spider or swing at normal/fast; cube at fast |
| 3 | Anything at very fast; ship with orbs at fast/very fast; wave at normal/fast |
| 4 | Wave at very fast/extremely fast; **mini wave**; dual wave; extremely fast anything |

The rules for moving on the ladder:
- Adjacent parts move **at most 1 rung**.
- At a real musical gear-change (a drop or hard break) they may move **2**.
- **Rung 4 only after the level has already reached rung 3**, and only for the song's peak.

This is the rule that bans "goofy cube → max-speed mini wave".

**B3 (MUST).** Speed changes:
- Normally 1 step.
- A drop's long burst is up to 2 steps.
- Never slow→extremely fast in one portal unless the song itself shifts gears, and then only after a breath beat.

**B4 (MUST).** Gamemode changes land on **strong beats** (beat 1 or 3 in 4/4), never offbeats. The movement before a
portal sets up a clean entry `[GDCS sync-rhythm, creating-gameplay]`.

**B5 (MUST).** **Sound division:** each important instrument gets a mechanic and keeps it. For example:
- Kick/snare = clicks.
- Off-drums = pads, no click.
- Leads = player path direction.
- Pads/strings = slow structure movement.

`[GDCS sync-rhythm]`

**B6 (MUST).** **Motifs:**
- Repeated phrases get repeated click patterns (A-B-A-C).
- Variation only where the music varies.
- Syncopation only if it's consistent.

`[GDCS sync-rhythm]`

**B7 (MUST).** **Difficulty target** (**PENDING Q2**): consistent "overall" difficulty, extreme but fair.
- No single choke point far above the level's average. Choke points are a common complaint at this tier
  `[DATA tags]`.
- Mechanics are introduced before they're tested `[GDCS progression, fairness]`.

**B8 (SHOULD).** Fairness tools where needed `[GDCS fairness]`:
- Slightly extended platform edges.
- Slightly larger orb/portal hitboxes.
- Hazards with No Touch + a smaller inner hitbox.

**B9 (AVOID).**
- Switching to a mode for one click.
- Mode changes every half-second (fine for top-list chaos, wrong here).
- Unexplained direction changes: the path turning when the player didn't click.
- Fake paths.
- Transitions that hide the next obstacle.

`[GDCS using-gamemodes, sync-rhythm; Lumpy transitions]`

**B10 (SHOULD).** Duals only where the music really has two voices. Unlink gravity or lock P2 input when one icon
shouldn't react `[GDCS consistent-gameplay]`.

---

## 6. Deco (the most important section)

### 6.1 Value structure first (MUST)

- **Value is the main tool.** Visual weight ranks value > proximity > colour > shape > direction > line weight >
  proportion > texture `[GDCS deco-elements]`.
- **Gameplay layer:** highest contrast, widest value range.
  - Every solid surface the player can touch gets a **bright rim/outline**, value ≥ 80%.
  - Hazards have their own bright edge.
- **Background:** low contrast, narrow value range.
  - **Value ≤ ~35%. No bright rims in the background, ever.** That's what keeps "deco" from looking like
    "gameplay".
- **Test:** greyscale screenshot (the "123" process). If the path doesn't read in grey, fix the values, not the hues
  `[GDCS light-3, backgrounds]`.

### 6.2 Palette (proposal, PENDING Q5 for the accent)

| Role | Proposed colour | Value | Notes |
|---|---|---:|---|
| BG base (1000) | `#04060f` (range `#02040c`–`#070b1c`) | ~6% | Like Antarctic Lights `#04080f`/`#0a0a16` and ORBIT `#090d1a` `[REF]` |
| BG lift at drops | `#08102a` | ~16% | Briefly, on the drop |
| Far BG shapes | `#0a1124` | ~14% | |
| Near BG shapes | `#111c3a` | ~23% | |
| Block fill | `#000000` | 0% | Glow-design style: black body, light edge |
| Gameplay rim / OBJ (1004) | `#cfe8ff` (ice white) | 100% | Antarctic Lights uses `#c2ebff` `[REF]` |
| Glow A (blending) | `#1d4fd6` | — | Main light colour; shows on black `[GDCS blending]` |
| Glow B (blending) | `#3fa8ff` | — | Highlights, drops |
| Accent | **PENDING Q5**: none / violet `#8a7dff` / amber `#ffb347` | — | ≤ 10% of screen colour `[GDCS colour 2–4]` |

- **Hue window: 205°–235°** for about 90% of colour. Hue-shift slightly cooler (cyan) in highlights and warmer
  (indigo) in shadows `[GDCS colour 2]`.
- Proportions: about 60:30:10 for dark body : mid blues : bright/accent `[GDCS evenness, colour 4]`.
- **Pulses stay in the blue range and in the level's brightness range.** A cold level gets blue pulses
  `[GDCS colour 4]`.

### 6.3 Z-layer plan (MUST)

`[GDCS creating-decoration]` `[REF layer roles]`

| Layer | Content | Parallax (Lock to Camera mod) |
|---|---|---|
| B5 | Far BG: big shapes, gradient-trigger skies | ~0.1–0.2 |
| B4 | Mid BG | ~0.3–0.4 |
| B3 | Near BG | ~0.5–0.6 |
| B2 | Connectors and structure backing (no hitbox) | 1.0 |
| B1 | Glow behind blocks (blending) | 1.0 |
| Default | **Gameplay:** blocks, hazards, orbs, pads, portals | 1.0 |
| T1 | Block body details (edges/corners) | 1.0 |
| T2 | Rims, outlines, 3DL | 1.0 |
| T3 | Overlay glow (blending), particles | 1.0 / varies |
| T4 | Flashes, transition wipes | screen |

How the layers behave:
- **Blending renders below non-blending on the same layer**, so glow gets its own layer `[GDCS polishing]`.
- **No deco on T1–T4 may overlap an orb, pad, portal or hazard hitbox.**
- Z-order steps of 5 (5, 10, 15…) so things can be slotted in later `[GDCS creating-decoration]`.
- Parallax numbers are `[MINE]` starting points; GDCS gives the method (Lock to Camera with mod < 1).

### 6.4 Colour channel plan (MUST)

`[GDCS creating-decoration, planning]` `[REF palette systems]`

| Channels | Purpose |
|---|---|
| 1 | Pure white |
| 2 | Pure black |
| 3 | Black + blending (invisible) |
| 10–19 | Gameplay: block fill, rims, hazard body, hazard rim, orb backing |
| 20–39 | Background families (far → near) |
| 40–59 | Glow families: **copies of 2–3 base glows with HSV offsets**, so one trigger re-grades them all |
| 60–79 | Pulse targets |
| 80–99 | Effects/overlays |
| 100+ | Per-part variants, 20 channels per part |

### 6.5 Blocks (MUST)

`[GDCS making-blocks, creating-details]` `[REF]`

- **Structure follows gameplay hitboxes.** There's always a clear surface the player can land on.
- **Base first:** few colours, few details. Then details.
- **Details sit at edges and corners.** Interiors stay simpler and quieter.
- Build reusable **custom assets** (block bodies, corners, caps) and recombine them. RobTop works this way; it's
  faster, and it keeps the look consistent.
- **Only 2–3 hazard designs per part**, consistent across the part `[GDCS evenness]`.

### 6.6 Background (MUST)

`[GDCS making-backgrounds, parallax]`

- It's a *different interpretation* of the part's idea, not filler.
- Lower detail, lower contrast and **bigger shapes** than the foreground (small foreground ↔ large background).
- Depth comes from parallax layers (more layers look more natural), scale variety and overlap.
- **AVOID** high detail in both foreground and background. It kills focus and depth.

### 6.7 Glow, light and gradients

`[GDCS fill-2, light-1, optimizing]` `[REF]`

- **MUST:** blending glow goes on dark backgrounds only. Use it for exterior gradients (rims, halos) and interior
  colour transitions.
- **MUST:** set the hard edge first, then soften it with glow.
- **SHOULD:** rim light on structure edges; occlusion where surfaces meet.
- **AVOID:**
  - Over-scaled glow (visible dithering): build big gradients from several pieces, or use a gradient trigger, which
    is also cheaper.
  - Gradients everywhere, which looks hazy.

### 6.8 Composition and evenness (SHOULD)

`[GDCS evenness, deco-elements]`

- No 50/50 splits or equal lengths/sizes. Use **70:30** and **60:30:10**.
- **Rest areas:** calm zones so the eye isn't always being pulled.
- The **focal point is the player's path**. Detail concentrates near it; contrast falls off away from it.
- **Variety** (midtones) keeps high contrast from looking "deep-fried".
- **Less is more:** every detail has a purpose (functional > narrative > aesthetic) `[GDCS creating-details]`.

### 6.9 Animation and pulses (SHOULD)

`[GDCS timing-easing, making-animations]` `[DATA]`

- Default easing is in/out for natural motion. Use None only for very fast or robotic motion.
- Keep motion alive: references animate 34–91% of objects. We aim for most of the background and glow being driven.
- **Pulse mapping (sound division for deco):**

| Sound | Pulse |
|---|---|
| Kick | BG/glow-family lift |
| Snare | Rim flash |
| Hats | Small glows/particles |
| Builds | Pulse rate doubles |

- Fade-in short and fade-out longer, so it feels like a hit, not a blink.

### 6.10 Effects and shaders

`[GDCS using-shaders, making-effects]` `[REF]`

- **MUST:** shaders only at drops, transitions and intensity changes. **Short and controlled.**
- **MUST:** no screen-distorting shader (bulge, pinch, shockwave, radial blur) during a hard timing. `[MINE, fairness]`
- **AVOID:** split-screen shaders (lag), constant shaders, more than one shader idea at a time.
- 4 of your 8 references use almost no shaders `[DATA]`. Deco carries the level; effects are seasoning.

### 6.11 Air deco (SHOULD)

`[GDCS making-air-deco]`

- Minor, simple, added last: arrows, connectors, particles, overlays.
- Particles move at varied speeds.
- If a space needs filling, use bigger shapes, not air deco.

### 6.12 Polish, performance and LDM (MUST)

`[GDCS polishing, low-detail-mode, optimizing]`

**Polish checks:**
- Layering bugs.
- Group conflicts after copy-paste.
- Screen edges at 16:9, 4:3 and ultrawide.
- Culling of huge scaled objects.
- Pixel misalignment of moving lines.

**LDM:** tick High Detail on aesthetic detail only: background art, air deco, heavy effects, area-trigger setups.
Never on functional detail.

**Optimisation:**
- Remove fully covered objects.
- Scale/warp instead of stacking.
- Default objects over custom assets.
- Gradient triggers instead of giant glow.
- Alpha/hide do **not** reduce active objects.

### 6.13 Deco anti-patterns (AVOID)

- **Spike spam.**
  - Hazards exist only where the path needs them.
  - **Decorative triangles near the path are banned**: triangles read as spikes `[GDCS deco-elements]`.
  - Decorative spikes, if any, live in the background, at low value, in a visibly different design.
- Bright background details that compete with the path.
- Orbs or portals sitting on same-colour backgrounds. Put a contrasting shape behind them `[GDCS backgrounds]`.
- Random hue pulses that break the blue mood.
- "High detail, low contrast" mush `[GDCS polishing]`.

---

## 7. Build process and deliverables

| Phase | What I do | What you get | Gate |
|---|---|---|---|
| 0 | Research + this rulebook | Rulebook, findings | **Your answers (§9)** |
| 1 | Song analysis: BPM grid, sections, energy curve, cut proposal | Song map + cut timestamps (and the edited mp3 if NONG) | Your OK on the cut |
| 2 | Level plan table (D1) + palette swatches + channel/layer sheet | Plan doc | Your OK |
| 3 | Gameplay layout v1: blocks/hazards in placeholder grey, Start Pos per part, BPM guides | `.gmd` v0.x | **Each part beaten from Start Pos** (P7) |
| 4 | Deco part by part: blocks → BG → glow → animation/pulses → air deco → effects | `.gmd` per part | Your review + G3/G7 |
| 5 | Polish, LDM, performance, full runs | Release candidate | All of G1–G9 |
| 6 | Final: Start Pos disabled, description, credits | Final `.gmd` (+ NONG note) | Done |

**Test report format** (what I need from you after each playtest):
- Part.
- Start Pos.
- Pass/fail.
- If fail: % or time, what killed you, and whether it felt *unfair* or just *hard*.

---

## 8. Things I will not do

- Claim gameplay works before it's been played in GD.
- Mock up or guess the song structure without the audio.
- Copy other creators' structures or art 1:1. Studying is fine; the deco is ours.
- Ignore the intensity ladder or the readability rules for the sake of "cool".

---

## 9. PENDING: questions blocking Phase 1

**Q1. Song.**
- I can't open YouTube from this environment.
- Please give me the **title + artist**, and if you can, **attach the audio file** here (mp3/ogg/wav).
- Is it on **Newgrounds / the GD music library** (ID?), or would it be a **NONG**?

**Q2. "Top 600".** Does it mean:
- **(a)** place *around* #600 (Bloodbath tier, my reading), or
- **(b)** anywhere *inside* the top 600 (harder is fine)?

And who verifies it: you? What's your hardest beaten demon?

**Q3. Testing loop.** Can you playtest each part from its Start Pos and send short reports? Do you use a macro bot?

**Q4. Setup.** Confirm: PC, Geode + GDShare import, GD 2.2081? Do you have an object-limit bypass mod (your refs
need one)?

**Q5. Deco direction.**
- Style: glow-design (Antarctic Lights-like), modern/effects (Society/ORBIT-like), custom art, or a mix?
- Accent: none / violet / amber?
- Any theme or story (space, deep sea, night city, ice, abstract…)?

**Q6. Length.** Long (about 60–120 s) or XL (2 min+)?
