# Complete bounded shared choice substitutions

## Installed state

`build/text-choices-pilot` includes complete general, item, character-name,
default-catchphrase, and selected-answer substitutions through the shared choice
formatter at `80065CF8`. The complete output is staged before it reaches the
twenty-byte destination. Unknown/incomplete commands and oversized expansions
leave that destination unchanged. This prevents both the original non-advancing
command loop and unbounded writes through message-sized helpers.

Plain choice text retains every original space. Command padding is detected by
whole tokens, so the day-of-month command `7F20` is not trimmed as a trailing
space. Existing GameCube wording, line/page breaks, timing, native choices,
saved names, and default catchphrase keys remain unchanged. Native random-number
generation retains its state effects if a subsequent field overflows; only the
destination update is atomic. Command-bearing translation imports remain disabled
until their build-time expansion bounds are validated.

The extension uses 3,040 image bytes, 208 relocation bytes, and a 3,263-byte
startup-owned system allocation including alignment. This adds 1,104 bytes to
the baseline extension's allocation. Its loader remains 216 bytes, and the
resident module, font, saved layout, other actor adapters, and actual four-MiB
memory requirement remain unchanged. The [specification](../../specs/CHOICE_SUBSTITUTIONS.md)
records the complete contracts.

```sh
python3 tools/build_text_extension.py --choices --output build/text-choices
python3 tools/build_text_extension.py --choices --output build/text-choices-rebuild
bash tools/build_text_choices_pilot.sh
```

## Artifacts

- ROM: 33,554,432 bytes, SHA-256
  `9bf6c4c98054d22fcf25ddcef967deeae0d9304f4a59a41b634bb947ca7ca25e`.
- UPS: 5,087,751 bytes, SHA-256
  `2ffb35c5d6475db7cd761a74a0ea33ab94049fa4f9fbffbf1c742e65cf884ea5`.
- Extension blob: 3,248 bytes, SHA-256
  `8619a986156563d210eb093ba09b17b2113cb33d4b236d14f4e202cf11230ebd`.
- Loader: 216 bytes, SHA-256
  `3adffb6605041192e135fa11d11b8f5162f5d1795fc54db65ce336f831b91b77`.

The original persistent-field build remains in `build/text-extension-pilot`.
All 13,769 bank edits remain installed. The progress counter verifies the new
choice capability before removing shared choices from pending-reader reasons.
Other character/item readers and default-phrase editing remain pending; this
batch neither invents source records nor gives the same text duplicate credit.

## Bounded verification

Risk and stopping condition: verify complete staged substitutions, no destination
overwrite or command-loop hang, exact source/import/relocation guards, complete
cartridge retention, and representative installed execution. Reuse the existing
native runner and baseline scenario; no exhaustive per-record matrix is needed.

Independent Docker builds agree on image, relocation, loader, and manifest.
The host sanitizer check passes all field slots and legacy command selectors,
combined names/catchphrases, complete selected answers, empty values, spacing,
overflow, recursive/unknown commands, and startup guards. Artifact/dependency
checks reject modified code, layouts, resources, and capability claims without
changing the input patch maps. All five focused checks pass, including complete
cartridge/UPS retention and combined accounting. Nine existing English-choice
runtime tests, twelve counter unit tests, and two baseline field/artifact checks
also pass. These are focused checks, not a full-suite rerun.

```sh
python3 -m unittest discover -s tests -p test_text_choices.py -v
python3 -m unittest discover -s tests -p test_english_runtime.py -v
python3 -m unittest discover -s tests -p test_translation_progress.py -v
```

The first host run exposes the `7F20` raw-padding bug in the new implementation;
token-aware padding fixes it. The incomplete-command fixture places its final
prefix at the actual capacity boundary, because a following padding byte `20`
is a valid day command. The first integration check also rejects the already
installed month/weekday stack growth; the dependency verifier now reproduces
those existing approved patches. Neither failure is waived or treated as a pass.

## Native evidence

The existing silent runner passes all twenty calls and thirty memory assertions
on the installed cartridge. The baseline fields, colours, item bridges, and
overflow checks pass alongside actual full general/item choice fields,
eight-byte names, ten-byte catchphrases, twenty-byte selected answers, invalid
selected lengths, oversized output, unknown commands, and incomplete tokens.
Row/stack guards remain intact, the checkpoint restores, and the emulator exits
gracefully. Isolated FlashRAM remains entirely `FF`; no user saves are used.

```sh
python3 tools/text_extension_scenario.py --build build/text-choices-pilot \
  --output build/text-choices-scenario.json
python3 tools/emulator_smoke.py \
  --rom build/text-choices-pilot/animal-forest-halfwidth.z64 \
  --output build/text-choices-native-01 \
  --scenario build/text-choices-scenario.json --seconds 120 \
  --no-initial-screenshot \
  --xvfb /home/discordian/Games/OpenRSC/headless/vendor/usr/bin/Xvfb
```

Use a fresh output directory when reproducing; the runner preserves existing
isolated save sets. No production code is uploaded by the scenario, and no
screenshots or audio are emitted.

- Results: `build/text-choices-native-01/results.json`, SHA-256
  `f42c43932c57570fb90514cee456315af2c92f969f3929be94989ef4e77091a7`.
- Run provenance: `build/text-choices-native-01/run.json`, SHA-256
  `c39eed504dfd1d2aefc2f7ffb6f92069012cf6f4071922beaed15ad86c942b06`.
- Scenario SHA-256:
  `5b013f8310be74b8f9f545e48963b59826fc6546ec524e90bb97b0bccc713438`.

This proves the installed startup and tested substitutions execute, not ordinary
NPC interactions, new-game progression, normal save/reload, all seasons, or
original-hardware compatibility. Missing gameplay evidence is not labelled a
pass, and no confirmed crash/save/memory defect is waived.

## Next work

Continue the remaining character-name actor preparations, default catchphrase
input/display consumers, other full-item readers, and the existing residual
strings/letters/accent queue. Ordinary gameplay, save/restart, and original
hardware remain outside this focused check. Finish main translation and bounded
v0 handoff before the human playthrough; title/images, GameCube-style keyboard,
and public-release preparation remain in the full goal.
