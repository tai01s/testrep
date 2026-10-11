# Research findings: answers to your six questions

## What I actually studied

**Read in full:**
- About 60 **GD Creator School** guides (deco 1–3, colour, light, animation, gameplay 1–2, sync, song, BPM, planning,
  playtesting, rating). Source: github.com/GDCreatorSchool/gdcs2, updated Sept 2026.

**Decoded, not guessed:**
- **Your 8 reference levels, object by object.** See `reference-levels.md`.

**Used as primary references:**
- The community level-format spec, GDDocs.
- A database of 3,985 object IDs (gd-info-explorer).
- Geode's 2.2081 bindings (the game's own enums and trigger fields).
- The AREDL list data. See `aredl-600.md`.

**Summaries only:**
- Web-search summaries of the GD wiki, Lumpy's guides on GDForum, and Steam guides.

**Blocked from this environment:**
- YouTube (videos, transcripts, thumbnails), Reddit, Fandom, GDForum and Newgrounds. The network policy denies them.
- So I have **not** watched videos. Where a guide relied on a video or image I couldn't load, I only used the
  surrounding text.

---

## 1. What makes a level objectively good?

There are **no official criteria**. RobTop's FAQ says rating has no specific guidelines, and his rating guide only
lists the tiers. So "objective" here means **checks that can be tested**. GD Creator School's playtesting guide
gives five:

1. **Enjoyability:** is it fun and interesting? Deaths should feel like your fault, not the level's.
2. **Reliability:** does it run as intended? No bugs, skips or secret ways. It behaves the same on 60/144/240 Hz.
3. **Playability:** fair, clear and expected. Transitions are the classic offender.
4. **Balancing:** difficulty *and* deco quality stay consistent throughout. No part is far uglier or far harder than
   the rest.
5. **Presentation:** one cohesive vision. No "onion background in the avocado level".

The guides and the reference data add four more that can also be checked:

6. **Sync:** strong notes get big movements. Gamemode changes land on strong beats.
7. **Readability:** in a greyscale screenshot you can still tell solid from deadly from decoration.
8. **Intent:** every gamemode, speed change and effect has a reason in the music.
9. **Performance:** no lag spikes, plus a Low Detail Mode.

These become the acceptance checklist in the rulebook (§1).

## 2. How can we make a level without replicating GD's physics?

**We don't simulate anything. GD is the physics engine.** I output a real level file (`.gmd`, the same format you
exported with GDShare). You import it and GD runs its own physics on it, so every jump is authentic by construction.
What I control is *where objects are*. I place them using only facts that are exact:

**Exact horizontal speeds.** These are the official values (wiki Portals page), and they're what my tools use:

| Portal | Blocks/s | Units/s |
|---|---:|---:|
| Slow ("0.5x") | 8.372 | 251.16 |
| Normal ("1x") | 10.386 | 311.58 |
| Fast ("2x") | 12.914 | 387.42 |
| Very fast ("3x") | 15.6 | 468.0 |
| Extremely fast ("4x") | 19.2 | 576.0 |

**So sync is pure arithmetic.** A beat at time `t` lands at `x = x_segment + speed × (t − t_segment)`. No
simulation needed.

**Mechanics with fixed geometry:**
- The wave moves at a fixed 45° (mini ≈ 63.4°, a 2:1 slope), and the angle doesn't change with speed.
- The spider snaps straight up or down.
- Ball and spider gravity flips are fixed paths.
- Orbs and pads launch the same way every time *when hit from a platform*.

**Proven geometry.** Spacings measured from verified levels, your 8 included, are physically possible because
someone beat them.

**Then GD itself is the test:**
- Every section gets a **Start Pos**.
- You (or a macro bot, if you use one) play each section and tell me where it breaks.
- I move objects.
- Nothing counts as done until it has been beaten in-game from its start position.

This is exactly how GD Creator School describes building and verifying gameplay: macro + hitbox trail + start pos.

**Honest limit:** I can't run GD in this container. For an extreme demon this testing loop with you is required, not
optional.

## 3. How can we change the song (length, pitch, speed)?

**Inside GD** (works for every player, no extra files):

- **Start offset** (level settings, to 0.1 s), plus fade-in/fade-out, cuts the intro. In your references, Antarctic
  Lights starts at 61.5 s and Thinking Space II at 117 s. Bloodbath starts at 81 s.
- The **Song trigger** (2.2) has:
  - **Start and End** in milliseconds (1 s = 1000).
  - **Fade in/out**, **Volume**, **Loop** and a **Channel**.
  - **Speed** in semitone steps: playback rate = 2^(steps/12). +12 = 2×, −12 = 0.5×, ±1 step ≈ ±5.9%.
- **Mid-level cut:** place a Song trigger at the cut point with Start = the timestamp to jump to. GRIEF does this
  three times. Flamewall even layers a second song on another channel.
- The **Edit Song trigger** changes speed and volume over a duration.

**The catch:** GD's song speed is **varispeed**. Tempo and pitch move together. GD can't change *only* pitch or *only*
tempo of a song. The SFX trigger has a separate pitch control, but that's for sound effects.

**Outside GD** (edit the audio file):
- You can cut at bar lines with tiny crossfades, time-stretch without pitch change, and pitch-shift without tempo
  change.
- I can do all of this here with ffmpeg/librosa once I have the audio file.

**The catch:**
- An edited file only works as a **NONG**: everyone has to install it (for example with the Jukebox mod), or they hear
  the original.
- Newgrounds songs must be whitelisted.

Around #600, 15% of extremes are NONG levels.

**Editing rules** (rulebook §3):
- Cut on phrase boundaries (4/8/16 bars) and on downbeats.
- Never cut through a sustained note or the build-up.
- Keep the tempo grid continuous across a cut.

## 4. How do you make a good drop?

**A drop is contrast.** Speed and intensity are *relative*: "a 2x speed part after a 0.5x part feels much faster than
one which is just 2x". So a drop is built from two halves.

**Before (the build):**
- Lower energy, then raise it:
  - **Speed easing:** small 1-step speed-ups, spaced wider as speed rises.
  - Rising click density.
  - Pulses doubling up.
- The last beat before the drop is a **breath**: a short hold, darkening or freeze.
- Use transitions that suit the moment: a hard cut, a quick black fade, or a screen wipe (fade, wipe and match-cut
  types from the transitions guide).

**At the drop (beat 1 of the drop bar):**
- A **gamemode change on the strong beat**. Changing gamemode on an offbeat "feels weird".
- A **big player movement**, because small movement = weak impact.
- A **long-burst speed change**: 2+ steps, held.
- **One** impact effect: shake, shockwave, or radial blur + black lens circle as a "shader pulse".
  - Shaders belong at drops and transitions only, in short controlled bursts.
- A **palette lift**.
- **Deco density jumps.** In your references it rises roughly 2–4× at the drop. Society goes from about 1,000–1,900
  objects per 5 s to 6,819, Thinking Space II from 11,135 to 28,649.
- **Pulses switch to 8th/16th notes.** References pulse in gaps of about 0.16–0.36 s.

**After:**
- Intensity has to keep changing (macro flow). Hold, drop back for a break, or escalate again. A flat line bores
  the player.

## 5. How do you make balanced gameplay?

What made your example (goofy cube → max-speed mini-wave) bad is an **unexplained intensity jump**. The guides give
these tools to avoid it:

- **Every gamemode needs a reason in the music:**
  - Cube: versatile, snappy.
  - Ship: floaty; for flowing sections and long notes.
  - Ball: controlled repetition.
  - UFO: floaty but snappy.
  - Wave: sharp; no physics; easily repetitive.
  - Robot: long holds.
  - Spider: click emphasis; high CPS.
  - Swing: smooth flow.
- Don't switch to a mode for one click. Don't switch modes so fast that none of them gets to shine.
- **Assign instruments to mechanics ("sound division").** For example: kicks = clicks, secondary drums = pads,
  long strings = sweeping structure movement.
- **Repeated phrases get repeated patterns.** If a phrase comes back, its pattern comes back (A-B-A-C form). Breaking
  your own pattern without a musical reason feels random.
- **Strong beats get the strong events.** In 4/4 the strength order is 1, 3, 2, 4.
- **Set up every transition.** Arrive at a portal on a predictable path, ideally from a platform. Avoid orb chains and
  clicking right before a portal. Place the portal *before* the orb, not after.
- **Keep difficulty and intensity inside a "flow band"** between boredom and anxiety. Plan them per part on a chart.
- **Introduce a mechanic before testing it.** Start simpler; escalate.
- **Make speed changes relative and gradual** unless the song itself hard-cuts.
- **Fairness tools:** coyote-time-ish platform extensions, slightly bigger orb hitboxes, smaller hazard hitboxes
  (No Touch + inner hitbox), J/H blocks, options-trigger input locks during transitions.

## 6. How do you make good deco? (most important)

The short version. Rulebook §6 has the full rules.

**Deco is a value-structure problem first.**
- The eye is most sensitive to value (light/dark), then proximity, then colour, shape, direction, line weight,
  proportion and texture.
- Gameplay gets **high contrast and a wide value range**. The background gets **low contrast and a narrow value
  range**.
- Check it with the greyscale ("123") test.

**Blue-black is near-monochromatic**, which GD Creator School calls the hardest scheme: "requires a good grasp of
values".
- So the palette needs a clear value ladder.
- Add *one* sparing accent (an analogous or complementary colour at ≤10%).
- Pulses stay inside the blue range so the mood holds.

**Blending glow is what makes dark levels glow.** Blending adds RGB, so it shows perfectly on black. That's why all 8
references use a near-black background. Glow plus line work is 36–53% of their objects; hazards are only 3–15%.

**Separate the roles:**
- **Blocks:** show where the gameplay is. Details go at **edges and corners**; interiors stay quieter.
- **Background:** a *different interpretation* of the theme, lower contrast, bigger shapes, parallax.
- **Air deco:** minor, added last.
- **Effects:** used at moments only.

**Spike spam is a design-language error.**
- Triangles read as spikes, so decorative triangles near the path lie to the player.
- Use only 2–3 hazard designs per part, and keep decorative shapes visibly different.

**Avoid evenness:**
- No 50/50 splits, equal lengths or equal sizes.
- Use 70:30 and 60:30:10 ratios.
- Leave rest areas so the eye isn't constantly pulled.

**Detail: less is more.** Every detail needs a purpose (functional > narrative > aesthetic). Concentrate detail where
it matters.

**Organisation is a skill:**
- One Z-layer per deco role.
- Z-order gaps of 5.
- Reserved colour channels (white, black, invisible black-blend).
- Copy-colour hierarchies, so one trigger re-grades a whole part.
- Editor layers per detail level.

**Polish:**
- Layering bugs: blending always renders below non-blending on the same Z layer.
- Screen-edge and aspect-ratio checks.
- Culling of huge scaled objects.
- Overscaled glow dithering. Use gradient-trigger overlays instead, which are also cheaper.

**LDM:** mark aesthetic detail as High Detail. Never mark functional detail.

## Sources

**GD Creator School guides** (source: github.com/GDCreatorSchool/gdcs2):

- Deco 1: [how to decorate](https://www.gdcreatorschool.com/docs/guides/deco-1/how-to-decorate/),
  [making backgrounds](https://www.gdcreatorschool.com/docs/guides/deco-1/making-backgrounds/),
  [fill 1](https://www.gdcreatorschool.com/docs/guides/deco-1/fill-1/),
  [fill 2](https://www.gdcreatorschool.com/docs/guides/deco-1/fill-2/),
  [making effects](https://www.gdcreatorschool.com/docs/guides/deco-1/making-effects/),
  [using shaders](https://www.gdcreatorschool.com/docs/guides/deco-1/using-shaders/),
  [low detail mode](https://www.gdcreatorschool.com/docs/guides/deco-1/low-detail-mode/)
- Deco 2 and 3: [timing and easing](https://www.gdcreatorschool.com/docs/guides/deco-2/animation-1-timing-easing/),
  [light 4: reflections](https://www.gdcreatorschool.com/docs/guides/deco-2/light-4-reflections/),
  [elements of decoration](https://www.gdcreatorschool.com/docs/guides/deco-3/elements-of-decoration/)
- Gameplay and editor: [creating gameplay](https://www.gdcreatorschool.com/docs/guides/gameplay-1/creating-gameplay/),
  [using gamemodes](https://www.gdcreatorschool.com/docs/guides/gameplay-1/using-gamemodes/),
  [level design](https://www.gdcreatorschool.com/docs/guides/gameplay-2/game-design-1-level-design/),
  [camera controls](https://www.gdcreatorschool.com/docs/guides/gameplay-2/game-design-5-camera-controls/),
  [song triggers](https://www.gdcreatorschool.com/docs/guides/triggers-1/song-edit-song/),
  [choosing a song](https://www.gdcreatorschool.com/docs/guides/the-editor/choosing-a-song/)

**Level format and game data:**

- GDDocs (level format): https://github.com/Wyliemaster/gddocs
- Object ID database: https://github.com/flowvix/gd-info-explorer
- Geode bindings (2.2081 enums and trigger fields): https://github.com/geode-sdk/bindings
- AREDL list data: https://github.com/All-Rated-Extreme-Demon-List/AREDL

**Wiki and official pages** (search summaries only):

- [GD wiki: Portals](https://geometrydash.wiki.gg/wiki/Portals) (speed values)
- [GD wiki: Update 2.2](https://geometrydash.wiki.gg/wiki/Update_2.2)
- [RobTop FAQ: rating](https://www.robtopgames.com/faq/en/answers/level)
- [RobTop rating guide (PDF)](https://robtopgames.com/files/GDRating.pdf)
- [AREDL](https://aredl.net/)
- [AREDL wiki page](https://geometrydash.wiki.gg/wiki/All_Rated_Extreme_Demons_List)

**Community guides** (search summaries only):

- [Lumpy's guide: improving decoration with contrast](https://gdforum.freeforums.net/thread/29930/improving-decoration-contrast-lumpys-guide)
- [Lumpy's guide: fun and fair transitions](https://gdforum.freeforums.net/thread/28937/fun-fair-transitions-lumpys-guide)
- [Steam guide: how to build good levels](https://steamcommunity.com/sharedfiles/filedetails/?id=2879624746)
- [Steam guide: how to properly sync levels](https://steamcommunity.com/sharedfiles/filedetails/?id=792172526)
