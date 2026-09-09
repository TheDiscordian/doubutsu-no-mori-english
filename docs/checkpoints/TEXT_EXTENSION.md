# Persistent complete general dialogue fields

## Installed state

`build/text-extension-pilot` retains every preceding translation resource and
adds complete general-field storage, plain/coloured main-dialogue insertion,
the original item-to-free-field wrapper, and three direct actor connections.
Reproduce the artifacts with:

```sh
python3 tools/build_text_extension.py
python3 tools/build_text_extension.py --output build/text-extension-rebuild
bash tools/build_text_extension_pilot.sh
```

The original twenty ten-byte fields remain compatibility mirrors. Twenty private
sixteen-byte rows hold the full text. The setter stages input, clears old suffixes,
preserves native colour-flag behaviour, and rejects oversized writes. Readers
check the entire insertion against the native 1,024-byte message capacity. Colour
duration covers the full English name, using the original palette; no line/page
breaks or timing controls are rewritten.

The resident module is full, so a separate startup-owned image supplies the new
readers. Its 1,952-byte image and 192-byte relocation use a 2,159-byte system-arena
allocation including alignment. The bootstrap loads, checks, relocates, and
initializes it after the existing heap/font startup. Failure returns through the
existing bootstrap failure path. Only after successful initialization does the
one-shot loader entry become the real field setter. The actual RAM configuration
remains four MiB; the main module, font, and save layout stay unchanged.

Native wrapper `800BB6F0` retains zero-item no-op. New bridges provide explicit
empty-item clearing and coloured insertion. The letter actor at `80919C68`
retains slot two/colour two; reserve `80A09438` and shrine `80A0AA6C` retain slot
zero and their unsigned item expressions. Actor allocations, relocation tables,
BSS, conditions, messages, and all other instructions remain unchanged.
The [specification](../../specs/TEXT_EXTENSION.md) records the ownership contracts.

## Artifacts

- ROM: 33,554,432 bytes, SHA-256
  `d4f8af9922883ebb9e4d7940981f8a17b922278e42606090c1335f6dc72aadf0`.
- UPS: 5,086,476 bytes, SHA-256
  `716f3577c9b3416be2daa4b968684b2292681816b00b684d3ee3a4870e3a88be`.
- Extension blob at VROM `03A00000`: 2,144 bytes, SHA-256
  `3e820846b242ef3f4bd2e74a3253173c45e6dc15ebc1943e810cc901b37ea95a`.
- One-shot loader: 216 bytes, SHA-256
  `aa2599aa864047615d83f06da6799645e40d9b82262df14e0a2fb1835d9d74ae`.

The combined build preserves all 13,769 bank edits. This integration completes
more uses of existing English item IDs, not new independent source records.
The progress counter verifies this installed extension, but keeps resource-only
item IDs pending while shared-choice and other required readers remain incomplete.
The measurement CLI is not refreshed merely to publish an unsolicited percentage.

## Focused checks

```sh
python3 -m unittest discover -s tests -p test_text_extension.py -v
PYTHONPATH=tests:tools python3 -m unittest test_item_fields test_extended_font_cartridge -v
PYTHONPATH=tests:tools python3 -m unittest test_translation_progress -v
python3 tools/text_extension_scenario.py
```

The four artifact/source/cartridge tests pass in 14.117 seconds; the sanitizer
field test also passes. Independent compilation agrees on code, relocation,
loader, and manifest. Independent MIPS assembly agrees on the bootstrap tail and
all three adapters. Source and allocation failures leave the input patch maps
unchanged. Two-base relocation checks retain the fixed bridges and complete
private image. Full cartridge checks retain every preceding decompressed payload,
allow only the specified main-code/actor changes and new DMA row, and reconstruct
the exact ROM from its UPS. Nine existing item-field/font tests and twelve fast
counter tests pass. The combined accounting check also accepts the installed
extension and retains the existing source weights and pending-reader status,
bringing this batch to six focused tests. These are focused checks, not a full
regression-suite rerun.

The initial host assertion incorrectly expected shrinking a message to erase its
abandoned bytes. The native movement helper's flag-zero path leaves those bytes
unchanged. The fixture now compares the complete untouched suffix against its
original contents; the one corrected attempt passes with address/undefined
behaviour sanitizers. No runtime change was needed for that failure.

## Native evidence and limits

The existing silent runner executes the generated scenario without production
code uploads, screenshots, user saves, or audible output:

```sh
python3 tools/emulator_smoke.py \
  --rom build/text-extension-pilot/animal-forest-halfwidth.z64 \
  --output build/text-extension-native-retry \
  --scenario build/text-extension-scenario.json --seconds 120 \
  --no-initial-screenshot \
  --xvfb /home/discordian/Games/OpenRSC/headless/vendor/usr/bin/Xvfb
```

Use a fresh output directory when reproducing; the runner refuses to overwrite
an existing isolated save set. The first attempt fails before emulator launch
because `Xvfb` is absent from PATH. The single corrected retry selects the
existing vendored binary and passes all ten calls and 21 assertions: four-MiB
startup, a full sixteen-byte field, a real cartridge clothing name through the
original wrapper, zero-item no-op and explicit clearing, full colour duration,
oversized insertion rejection, resident/message guards, and checkpoint restore.
The emulator exits gracefully and isolated FlashRAM remains entirely `FF`.

- Native results: `build/text-extension-native-retry/results.json`, SHA-256
  `20512d6f0693c1788822d93b81bf17491cdeb24925309bf1d56d31f1cda3e476`.
- Run provenance: `build/text-extension-native-retry/run.json`, SHA-256
  `0e594c8ac217fbb8c94f0da0fdb6494d1acb76c02a7f5be014900b67dde2c866`.
- Generated scenario SHA-256:
  `e1ecfde4916a2ab46592d4294e7c929e9102d3fc8fe3583cc6a3c6fc778c00de`.

This proves the installed startup and tested field paths execute, not ordinary
actor interactions, new-game progression, normal save/reload, all seasons, or
original-hardware compatibility. The three actors have assembly/relocation and
cartridge evidence, not freshly executed complete gameplay branches. No known
crash/save/memory defect is waived by the test scope. The combined v0 smoke and
human playthrough retain their separate responsibilities.

## Next work

Use the [choice-capable integration](CHOICE_SUBSTITUTIONS.md) for complete bounded
shared choices. Continue remaining character/catchphrase consumers and default input. Retain the residual general
strings, letters, and accented names queue. Preserve GameCube wording, manual
breaks, and timing. Finish main translation and bounded v0 handoff before human
playthrough; title/images, GameCube-style keyboard, and public-release preparation
remain in the full goal.
