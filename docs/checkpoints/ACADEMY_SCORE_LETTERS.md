# HRA score-letter integration work record

Twenty complete supported score letters (`0034..0048`, except `003D`) are
installed in `build/academy-score-letters-pilot`. The
[specification](../../specs/ACADEMY_SCORE_LETTERS.md) defines complete numeric,
date, item, and series capture, unchanged scoring/rewards, and delivery-gated
evaluation dates. The score body containing the semicolon remains pending.

## Current evidence

- The integrated ROM build succeeds with `--english-academy-scores` and the
  complete preceding translation/runtime options.
- All 25 corrected host creator tests pass. The first run exposed an accumulated
  item-call counter in the test fixture; resetting that counter for each fixture
  corrects the test without changing production C.
- The corrected AddressSanitizer/UndefinedBehaviorSanitizer batch passes all 25
  tests in 34.812 seconds: `build/academy-score-creator-sanitizers-final.log`.
- Five installer tests pass in 2.762 seconds:
  `build/academy-score-install-tests.log`.
- Independent builds in `build/academy-score-mail-creator` and
  `build/academy-score-mail-creator-repro` produce equal images and relocations.
- Independent assembly passes in `build/academy-score-assembly/report.json`.
- All 1,047 regression tests pass in 589.727 seconds:
  `build/academy-score-regressions.log`.
- The focused native scheduler batch passes at
  `build/smoke-academy-score-scheduler-01`: original evaluated points, complete
  English, failed preparation, actual allocation failure, original alternate
  allocation delivery/retry, date/house flags, duplicate prevention, cleanup,
  checkpoint restoration, and blank isolated saves. It has 70 internal memory
  assertions plus the resumed-checkpoint check. The game-owned system allocation
  returns zero in this checkpoint; successful scheduling uses the original
  NULL-game gameplay-arena path, not a test replacement allocator.
- The final combined native batch passes as `build/smoke-academy-score-03`:
  forty original-selection/metadata/RNG comparisons across all four homes and
  ten slots, forty-four complete delivered readbacks, four real scheduler cases,
  thirteen rejections, and two resource retries. The original empty-room
  evaluation returns 102 points and template `0043`; both the successful and
  failed complete creator preserve that points return. All 159 native calls,
  449 internal memory assertions, and the resumed-checkpoint assertion pass
  (450 total). Live save/globals, heap accounting, guards, and checkpoint
  restoration pass, with blank FlashRAM/Pak and graceful shutdown.
- Two selection-model tests and three full-glyph-scan tests pass separately
  after the regression batch. These five tests are not included in its 1,047.

The first native batch passes forty original-selection/metadata/RNG comparisons
and complete English readbacks, then stops at a fixture expectation that incorrectly
assumes retry selects the zero-points fallback regardless of the original letter
bits. The corrected fixture retains inputs/RNG and models the original selector.
The second batch passes those comparisons and direct original room scoring, then
finds no delivery through the checkpoint's game-owned system allocator. A focused
probe confirms that allocator returns zero, and verifies failure retention plus
the original NULL-game allocation path. Neither partial batch is counted as a
complete native run. No production code changes are made for these fixture issues.

## Artifact and retention checks

- ROM SHA-256:
  `7cb2c435a6a87b88d907bc94ccc5fe757861f78f474de5795fb24264c8e8bb7c`.
- Original-ROM UPS SHA-256:
  `1fdbe6412d5a7d4868566b8289b8977d96158746b9aca42192ca74d7bd1b503d`.
- Creator image SHA-256:
  `00c8cc3e86288e0477de8eea189ad72e2530ea75473f7f90f8383c4fee38cd6a`.
- Creator relocation SHA-256:
  `22d053f5b9b488329c45d6749ebb0028001ed08b7dc35e73a63c40e384491bbb`.
- Installed scoring image SHA-256:
  `88d58f4d38dccb5c77cc7c8f99ef280efcc2113c9e6d0703563be8539f16ec05`.
- Installed scoring relocation SHA-256:
  `a53d04cb5992a96bff77aa8cb9f022aff02764821f659c5578763b61fc6e39a5`.

Independent reconstruction of the original-ROM UPS matches the complete pilot.
Comparison of all 3,382 DMA resources with the advice pilot finds exactly six
changed resources: DMA metadata, main code, the scoring overlay, its adjacent
relocation table, resident configuration, and the creator. All 13,383 ordinary
text edits, other resources, approved font metrics, and native atlas remain.

Evidence SHA-256 values:

- Full regressions: `0f6c3ed4f2ac254d45fde79ec8783df932b66ff4586c932e6f6489f6282a4f05`.
- Sanitizers: `6aab049b23adc5c64e43c3c18b156483f51763f41a6f4714f03bec60c20ffd23`.
- Installer tests: `d6a63f7af3773b5e964f6e136960306338ce8c47204332f81ba63caa62a5db4d`.
- Focused native scheduler: `6eb2cef8ef3258b12d1117452119b5e3531327315fdb57e4d1cb57330fb7e2f7`.
- Complete native batch: `deed1717bdcedb6f9343732abc9420e598c45e86fe0d42e938c5b81e60403c66`.
- Independent assembly report: `e03a0e6fab00c73ec439858b0db551beaf530160954feb256cdb3fe614cd0f4e`.
- Complete source glyph audit: `bb467ef8951665c421a9fb4e80a7bb3dda8c8e3b93faf4e9cc935e4a71714b62`.

## Reproduction

Build the optional creator with `--mother-letters --departed-letters
--villager-events --academy-letters --academy-scores`, using
`build/academy-score-mail-creator` as output. Use the complete advice ROM recipe,
select this creator, and add `--english-academy-scores`. Generate the native
scenario with `tools/academy_score_scenario.py --output
build/academy-score-scenario.json`, then execute the silent runner with a fresh
output directory, a 900-second bound, and `--no-initial-screenshot`.

The executed integrated build uses the existing verified resource outputs:

```sh
python3 tools/build.py \
  --rom 'local/rom/Doubutsu no Mori (Japan).z64' \
  --translations build/native-credits-candidates/translations.json \
  --english-keyboard --english-runtime --runtime-module build/runtime-module \
  --english-fortunes --english-resetti-replies --english-shop-units \
  --english-resident-words --english-shared-npc-words --english-credits \
  --english-dialogue-dates --extended-items build/mapped-items-final-resource \
  --display-names build/display-names --catchphrases build/catchphrases \
  --mail-catalog build/fortune-slip-resources \
  --english-mail-layout --english-mail-snapshots \
  --english-mail-grading build/mail-grading-npc \
  --npc-mail-generation build/academy-score-mail-creator \
  --extended-font build/extended-font-cartridge \
  --english-fortune-slips build/fortune-recovery-actor \
  --english-leaflet-dates build/leaflet-dates \
  --english-renewal-letters build/renewal-actor \
  --english-event-letters build/event-actor \
  --english-mother-letters --english-departed-letters \
  --english-villager-event-letters --english-academy-letters \
  --english-academy-scores --output build/academy-score-letters-pilot
```

The native fixture loads the replacement scoring overlay, complete creator,
and all resources from the cartridge. It uploads only the independently relocated
original scoring image for comparison. Owned synthetic save/game structures
exercise actual code; this is not ordinary gameplay or original-hardware proof.

## Next work

Implement [missing mail glyphs](../../specs/MAIL_GLYPHS.md) and other native
text consumers; retain all normal gameplay/save, review, release, title-first
artwork, and GameCube-style keyboard requirements.

The native batch does not establish successful game-owned system allocation,
ordinary gameplay scheduling, real save/reload, editorial presentation, or
original-hardware compatibility. Exact selected-template persistence across
failed score attempts is not added; original eligibility survives for reevaluation.
