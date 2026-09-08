# HRA welcome/advice integration work record

Twenty complete supported letters (`01DC..01EF`) use the existing snapshot
framework. Membership and evaluation date update only after a complete letter
reaches the original mailbox. The [specification](../../specs/ACADEMY_LETTERS.md)
defines native selection, descriptor, frame, and caller gates.

## Current artifacts

- Integrated ROM: `build/academy-letters-pilot/animal-forest-halfwidth.z64`,
  SHA-256 `1c1a1d782b63c7405cf415f9cac7765af127526abe2bb4b235c9163369230d33`.
- Original-ROM UPS SHA-256:
  `679163559679c6db9da5e85859bc0e0d15d0f6338f6584e2d63280fc1930b610`.
- Creator: 29,232 bytes, SHA-256
  `fda577a8311431531f124af1a67ae5ca31a3d5b371d2e57e514b0dda409726dc`.
- Relocations: 464 bytes, SHA-256
  `7330332baac86691ccd8e1f949496229f4cf9c5fb38b0ea5c70dd7484f16686a`.
- Native results: `build/smoke-academy-02/results.json`, SHA-256
  `2559fb9420453bced2b3cb7b07f99d2e30aaa520c6d946571952a9091ddc1d93`.
- Full regression: `build/tests-academy-regression.log`, SHA-256
  `5107a551045c37abf1a4a339c969e3cde22084a1c6c27d209f2f42e84a1ef0ff`.

Independent creator images, relocation data, and manifests agree. The complete
blob is 29,696 bytes; each call requests 35,055 temporary bytes including the
unchanged 5,344-byte workspace and alignment. The dispatcher frame is 88 bytes,
and the native mailbox wrapper frame is 240 bytes. The resident module remains
24,288 linked bytes; no saved structure grows. All 13,383 ordinary edits remain.
Independent comparison of all 3,382 DMA resources against the villager-event
pilot finds changes only in code, resident configuration, creator, and DMA metadata.

## Executed checks

All 1,013 regression tests pass in 526.163 seconds.
Four additional [score-reference tests](../../specs/ACADEMY_SCORE_LETTERS.md)
pass in 25.696 seconds after that suite, covering all 63 parts, 55 series names,
and 2,200 full-field snapshot/format combinations. Score publication is not yet
installed or credited by the translation counter.

All 21 host creator tests pass in 17.362 seconds, including the inherited NPC,
Mom, departed-villager, and event contracts. New cases compare every complete
HRA template in both capitalization states, full metadata/snapshot/text, each
catalogue read failure, resource recovery, descriptor bounds, and aliases.
The same tests pass with AddressSanitizer/UndefinedBehaviorSanitizer in 26.141
seconds. Five installer tests pass in 3.226 seconds, including the actual ROM,
all sixty original/English parts, three permitted code ranges, conditional
membership/date branches, and atomic dependency/source rejection.

Independent assembly matches the 276-byte entry, eighty-byte welcome/gate region,
and four-byte hint call. Assembly SHA-256:
`ba1d8fcf924c6eb4f106802d0d1ce0d54f9236246c51fe075a03b97b14520b84`.
An initial host failure identified the unset received-font byte after native
clear; the corrected creator explicitly sets font zero before publication.

The native batch passes forty original metadata comparisons and forty-four
complete resident-reader reconstructions. Forty direct cases cover every
template in both capitalization states and every combination of four homes and
ten mailbox slots. Six actual scheduler cases cover welcome/advice success,
disabled catalogue, and full mailbox. Five additional invalid home/template
cases reject without writes. Both disabled-resource cases retry successfully;
both successful scheduler cases reject a same-day duplicate. The 152 native calls
pass 435 internal memory assertions and the resumed-checkpoint assertion
(436 total). Original save/globals and heap accounting are restored. Graceful
shutdown and blank FlashRAM/Controller Pak hashes pass.

`build/smoke-academy-01` terminates before any game checks when the diagnostic
startup screenshot command fails. The successful memory-only batch explicitly
uses `--no-initial-screenshot`; this skips no game or scenario assertions.
The runner records that option in provenance and includes screenshot error
details when image capture is requested. No display is presented to the user.

## Reproduction and remaining work

Build the creator with `--mother-letters --departed-letters --villager-events
--academy-letters`. Use the complete villager-event ROM recipe, change the
creator to `build/academy-mail-creator`, add `--english-academy-letters`, and use
`build/academy-letters-pilot` as output. Generate `build/academy-scenario.json`
with `tools/academy_scenario.py`, then execute the silent runner with a fresh
output directory, `--seconds 420`, and `--no-initial-screenshot`.

Complete score-letter capture and
publication, missing mail glyphs, other text consumers, and review. Normal
gameplay, save/reload, original hardware, patch-only release preparation,
title-first artwork, and the GameCube-style keyboard remain in the full scope.
