# Complete English map landmark labels

## Installed state

`build/map-labels-pilot` installs the complete English map landmark and
vacant-house labels, retaining full villager names, opening-guide names, and
every preceding translation layer. [The specification](../../specs/MAP_LABELS.md)
records exact native descriptors, GC reference bindings, line placement,
private storage, and relocation.

Shop and Dump remain single lines. Police/Station, Post/Office, Wishing/Well,
and Train/Station use the supplied GC executable's two-line wording and
coordinates. The redundant native post-office second draw is suppressed.
The vacant-house field contains the complete reference word `free` and native
padding. Player names, resident records, house flags, icons, saved identities,
font, message timing, and the full-name cache remain unchanged.

The map image is 27,072 bytes. The 528-byte label extension adds 512 aligned
bytes to the complete name-cache image. Total aligned map growth over native
is 1,280 bytes; the conservative map branch requires 177,280 of the existing
243,072-byte submenu pool. No permanent reservation or main-code allocation
changes. The actual cartridge still uses four MiB.

## Reproduction and artifacts

```sh
python3 tools/build_map_labels.py
bash tools/build_map_labels_pilot.sh
python3 -m unittest discover -s tests -p test_map_labels.py -v
```

- ROM: 33,554,432 bytes; SHA-256
  `ffc6a207f28e2a4d20f3080ea9e6a15aa81d359f581eacd8ff7d60c933ba4d4b`.
- UPS: 5,118,243 bytes; SHA-256
  `2c27ca53122b66a26b37e04000e5fd629e667b9b5baad38ebeccca477d404547`.
- Appended label suffix SHA-256:
  `279b22d79c45f94e76ddcd97c169a419e7449a4e00fd17bfee4256f6fa075eca`.
- Complete map relocation SHA-256:
  `72b43cb3b62b7eba86a1782913fddb7427188fe5fe44bb13530aa2e8c18ae134`.
- All 13,769 bank edits remain. Only map data/code, its relocation, submenu
  map-owner endpoints, and physical DMA packing change from `guide-name-pilot`.

## Bounded checks

Risk and stopping condition: bind complete donor wording/line positions; keep
the native resident-name cache intact; prevent a repeated post-office line or
overread of the second line; verify the new floating-point constant relocation,
128-byte private frame, ownership, and complete patch reconstruction. No new
emulator harness or per-record native matrix is needed for this batch.

All six focused checks pass: exact line text, positions, all drawing arguments,
eight-byte bounds, sanitizers, source/compiled-image guards, unchanged cache,
two relocation bases, complete retained cartridge, UPS recovery, and combined
accounting. The core and two cartridge checks pass together in 97.721 seconds;
the three artifact checks also pass. Three unchanged base-map artifact checks
and twelve counter tests pass. The retained map/guide cartridge also validates
through the generalized profile verifier.

Independent pinned-toolchain builds in `build/map-labels-overlay` and
`build/map-labels-rebuild` agree. The initial host fixture compile rejects an
intentionally unterminated sixteen-byte test initializer under warnings-as-errors;
its single corrected retry uses an explicit sixteen-byte copy and passes.
No production bounds checks or warnings are disabled. The legacy item fixture
rejection recorded in [the name checkpoint](MAP_GUIDE_NAMES.md) remains pending;
it is not retried or reported as passed here.

Eight distinct native map records add 28 non-whitespace Japanese source
characters to the combined inventory. Both older and current builds use that
same denominator; only the verified label build receives those 28 applied
characters. The combined inventory is 751,284 source characters, with 720,689
applied in this build. English line splits and repeated name consumers do not
create duplicate source IDs. Older-build regression denominators include the
same newly inventoried text without gaining English credit.

Ordinary map opening/navigation, combined v0 save/restart, and original hardware
remain unverified. No screenshot, audio, user-save change, or new native gameplay
run is performed. These limitations remain visible rather than becoming passing
claims from host checks.

## Next work

Connect the fishing-event winner-name display at `80A9031C` using the existing
394 exact aliases and proven NPC PersonalID markers. Preserve the saved six-byte
writer, town field, real player winners, original NPC/random selection, and score
field one. The [map/guide checkpoint](MAP_GUIDE_NAMES.md#next-implementation)
records the verified native layout, resource hash, and exact-key coverage.

Then continue other live identity/catchphrase/item readers, residual general
text/letters, accents, and the bounded combined v0 smoke. The complete English
title/image replacement and GameCube-style keyboard remain v1 work. Do not redo
completed map labels or full-name caches before the remaining implementation.
