# Test v1: first ~11 s (intro + beat drop-in)

**Files:**
- `castle_of_shadows_test_v1.gmd`: the level.
- `castle_of_shadows_cut.mp3`: the NONG. It was sent in chat; it isn't in the repo because it's the artist's music.
- `preview_test_v1.png`: my approximate render of the level, not an in-game screenshot.

## Setup (PC + Geode)

1. **Import:** GDShare → import `castle_of_shadows_test_v1.gmd`. It appears in your created levels as
   "Castle Of Shadows (test v1)".
2. **Song:** the level is set to Newgrounds song **467339** as a placeholder. In the level's song info, open
   **Jukebox** and add `castle_of_shadows_cut.mp3` as a NONG for that song. Leave the song offset at 0.
   The cut has one silent bar at the start; the first note lands on the first click.

## What to test

**Bot** (proves it's possible): run from the start to the end trigger (~11.9 s). There are no frame-perfect or tight
timings.

**You** (feel and fairness):
- 15 clicks, all on the music:
  - bars 1–3: spikes, a raised deck, off the deck
  - bar 4: two step-ups on the rising bass
  - bar 5 downbeat: jump off the gate ledge; speed goes up and you land on beat 2
  - bar 5–6: three kick jumps
- Two disabled start positions are in the level (bar 4, and after the ledge) if you want to practise a bit.

## Please report

1. Did it import and play? Does the NONG play from Jukebox?
2. **Sync:** do the clicks land on the notes, or is everything consistently early or late (by roughly how much)?
   I assumed the player starts at x = 0 when the song starts. A constant offset is a one-number fix.
3. Any death that felt unfair: where (time or %), what killed you.
4. **Look** (a screenshot helps a lot). Specifically:
   - moon size and halo
   - whether the background drifts at sensible speeds
   - whether the default spikes fit the ice palette
   - whether anything looks bigger or smaller than intended. Glow orb size is an estimate.

## Known approximations in v1

- **Gameplay check:** gameplay was checked with GD's published cube constants and conservative hitboxes, not with
  GD itself. Your bot run is the real test.
- **Glow size:** the glow orb's base size is an estimate (sky glow, mist, moon halo).
- **Spikes:** they use the default spike, coloured through the OBJ channel. Iron-styled spikes come later.
- **Camera framing:** I assumed a 16:9 screen. Wider or narrower screens may show more sky or more of the
  under-bridge.
