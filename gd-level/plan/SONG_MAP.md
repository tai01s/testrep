# Song map: "Castle Of Shadows" (Instrumental), SlyphStorm

**Source:** the instrumental you sent (4:15, 44.1 kHz, ~124 kbps YouTube rip). It's used as a **NONG**.

## Tempo: exactly 128.000 BPM

- One beat = 0.46875 s. One bar (4/4) = 1.875 s. One 8-bar phrase = 15.0 s.
- The automatic beat tracker said 129.07 BPM. That's wrong, and it would drift by almost a whole bar by the end of
  the song.
- The true tempo comes from cross-correlating sections that repeat in the song. Every repeated pair agreed on
  +3.875 ms/beat once whole-beat wrap-around is allowed for, which is exactly 128 BPM.
- At 128 BPM, all repeated pairs line up within ±1 ms (correlation 0.79–0.97).
- **Downbeat:** the first note (2.9135 s in the original) is beat 1 of bar 1. The big entrances (beat in, break,
  return) all land on beats ≡ 0 (mod 16), i.e. every 4 bars from the first note.

## Original structure

Each letter is an 8-bar section; matching letters correlate strongly.

| Bars | Section | Time |
|---|---|---|
| 1–4 | Intro: pulsing F4 8ths, A♯4 accents on bars 1 and 3, C5 on bar 2 beat 4. Bass pickup on bar 4, beats 3–4 | 2.9 s |
| 5–12 | A: beat and bass in | 10.4 s |
| 13–20 | B (sub-heavy). Crash/fill on bar 12 | 25.4 s |
| 21–28 | A′ (dense) | 40.4 s |
| 29–36 | B | 55.4 s |
| 37–44 | C | 70.4 s |
| 45–52 | D | 85.4 s |
| 53–60 | B | 100.4 s |
| 61–68 | A′ | 115.4 s |
| 69–76 | **Break**: a hit on bar 69, near-silence 70–75, pre-drop fill on bar 76 | 130.4 s |
| 77–84 | **C: the big return** | 145.4 s |
| 85–92 | D | 160.4 s |
| 93–108 | B B | 175.4 s |
| 109–124 | C D | 205.4 s |
| 125–126 | Outro hit + decay, silence from ~238.7 s | 235.4 s |

## The cut (105.46 s) → `castle_of_shadows_cut.mp3`

| Cut segment | Original bars | Why |
|---|---|---|
| 0.000 s | 0–28 (1 silent lead-in bar, intro, A, B, A′) | |
| 54.375 s | 69–92 (break, C, D) | In the original, the break follows A′ (bar 68), so jumping from A′ (bar 28) to bar 69 is the same musical transition |
| 99.375 s | 125 → end (outro hit, decay, 1.5 s fade) | In the original, the outro follows D (bar 124); ours follows D (bar 92) |

How the joins were made and checked:
- 30 ms equal-power crossfades, ending exactly on the bar line.
- Verified afterwards: the beat pattern carries across both seams with 0 ms phase shift, with no clicks.

**In the cut, bar c starts at exactly c × 1.875 s:**

| Cut bar | Time | What |
|---:|---:|---|
| 0 | 0.000 | Silent lead-in |
| 1 | 1.875 | Intro |
| 5 | 9.375 | Beat entry |
| 13 | 24.375 | B |
| 21 | 39.375 | A′ |
| 29 | 54.375 | Break |
| 36 | 67.500 | Pre-drop fill |
| 37 | 69.375 | **Drop (C)** |
| 45 | 84.375 | D (climax) |
| 53 | 99.375 | Outro hit |
| — | ~105.5 | End |
