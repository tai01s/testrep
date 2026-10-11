# GD level project: blue-black extreme demon

A Geometry Dash level built against a written rulebook. It's being made in phases; each phase waits on the
requester's OK.

| Path | What it is |
|---|---|
| `RULEBOOK.md` | The rules the level is built against: acceptance checks, physics/timing approach, song, drop, gameplay balance, deco, process. **Start here.** |
| `research/FINDINGS.md` | Answers to the six research questions, with sources |
| `research/reference-levels.md` | Decoded data from the 8 reference levels (palettes, layers, object vocabulary, sync, song handling) |
| `research/aredl-600.md` | What "top 600" means in difficulty terms |
| `tools/` | Python tools that decode and analyse GDShare `.gmd` exports |

**Status:** song mapped and cut; test v1 (first ~11 s) built. Waiting on your test report.

## Build (Phase 3/4 test)

| Path | What it is |
|---|---|
| `plan/SONG_MAP.md` | Tempo (exactly 128 BPM), sections, and the 105.46 s cut |
| `plan/LEVEL_PLAN.md` | Part-by-part plan + the click map for part 0 |
| `build/` | Generator: `gdlevel.py` (.gmd writer), `art.py` (shapes/triggers), `timeline.py` (song time ↔ x), `part0_gameplay.py`, `scene_part0.py`, `physics_check.py` (sanity check only), `preview.py`, `make_test.py` |
| `out/` | `castle_of_shadows_test_v1.gmd`, preview image, `TEST_v1.md` (how to test) |

To rebuild: `cd build && python3 make_test.py`. The physics check is `python3 part0_gameplay.py`.
