# Festival-stall choices

## Installed state

The current combined build is `build/stall-choices-pilot`, reproduced by
`bash tools/build_stall_choices_pilot.sh`. It retains the complete
[event/home integration](EVENT_ITEM_NAMES.md) and every earlier translation
resource, adding `--english-stall-choices`. Generated game data and patches
remain ignored and local.

All four stall rows hold sixteen-byte item names. The name loop keeps the native
goods IDs and selection order, uses the complete resident loader, and retains
the native next-item index. Both three-choice browsing and four-choice setup
remain. The supplied English cancellation labels are installed in full:
`I'm not buying! ` and `I don't want it!`. The first label's trailing space,
message selection, prices, item transfers, line/page boundaries, and timing stay.

The [specification](../../specs/STALL_CHOICES.md) records the source, stack, and
relocation contracts. Four local rows grow from forty to sixty-four bytes; the
frame grows from 168 to 192 bytes and the live pointer above the array moves
with it. Saved registers and the row-pointer array remain in place. Appended
labels add 32 actor bytes, with complete actor-table/DMA extents. No resident
module, saved field, or configured heap boundary changes. The build retains its
four-MiB configuration; original hardware is not certified.

## Artifacts

- ROM: 33,554,432 bytes, SHA-256
  `4d28832e4ef92541c84f459e9e71b192755cb262d76986d8dc87d618d645ca48`.
- UPS: 5,059,444 bytes, SHA-256
  `032b134c4cae82fc8303470b8f3fbd5934774b98227711333e20f3d56a3bde3e`.
- Actor: 4,720 bytes at VROM `03990000`, SHA-256
  `62723bac0721644b1d323a21b7c12cef07f382448b3d64c5995e0d5bac061ee7`.
- Relocation: 336 bytes at VROM `03998000`, SHA-256
  `fda2471c89e9d466ed70afe2cb59bdc7d4887a1e99e7a10ca0e462e3220aaef0`.
- Independently assembled 32-byte name-loop replacement, SHA-256
  `f3cc83c7e8f2e8a1eda7e15af908d94aa5399d3bba1b863435777a5f5bfc5ae9`.

The 13,769 existing bank edits are unchanged. Both newly inventoried embedded
Japanese labels share the combined text denominator and receive installed-route
credit. Item-name IDs remain shared with their other readers; this feature alone
does not remove pending status from partially connected item-name resources.

## Checks and limits

```sh
python3 -m unittest discover -s tests -p test_stall_choices.py -v
python3 -m unittest discover -s tests -p test_english_runtime.py -v
python3 -m unittest discover -s tests -p test_translation_progress.py -v
```

All six stall checks pass: four core checks in 6.983 seconds and two cartridge/
accounting checks in 33.897 seconds. The core checks bind the actual GC function
and labels, the original actor and relocation, every changed stack/row/length
instruction, untouched saved-register storage, unchanged branch instructions,
and both legal three/four-row callers. Independent Docker assembly checks the
actual unsigned item/capacity/pointer sequence. Relocation checks at two bases
resolve both complete labels and retain the absolute resident call. Missing
dependencies, conflicting actor data, and occupied DMA targets fail atomically.

Cartridge checks verify the updated allocation row, both relocated DMA records,
every unrelated decompressed payload, complete previous feature reports, N64
checksum, and UPS reconstruction. The counting check requires installed labels
and consumers; the prior build inventories the same twelve Japanese source
characters without credit. No user-facing percentage is refreshed unasked.

Nine existing choice-runtime tests pass. The initial run passed eight and
rejected a stale `build/runtime-module` fixture before game-code validation.
The fixture uses the current `build/notice-seasonal-runtime` (or explicit
`AF_TEST_RUNTIME`); the one affected test passes its single corrected retry in
2.240 seconds. The fixture correction changes neither runtime code nor build
safeguards. Twelve fast counter tests also pass. No new native harness
or emulator scenario is needed for this batch.

Ordinary stall browsing, purchase/cancel, scene transitions, and normal save/restart
remain in the combined v0 smoke. This checkpoint does not claim native gameplay
or original-hardware validation. Confirmed crashes, memory corruption, and save
damage remain v0 blockers.

## Next implementation

Continue the remaining native item free-string paths, shared dynamic-choice
substitutions, character/display names, default catchphrase input/readers,
general/letter text, and accented names. The free setter at `8009D6D0` owns twenty
ten-byte rows and flag side effects for slots one, two, and five. Widening these
requires complete storage and reader integration, not larger unreviewed writes.
Native wrapper `800BB6F0` and actors at `80919C68`, `80A09438`, and `80A0AA6C`
are the existing next caller inventory. Keep the completed shop, capture/dig,
event/home, and stall paths; do not redo their source matching or broad tests.

The complete goal remains open. Finish main translation/application and bounded
v0 checks before human playthrough; retain public-release preparation and v1
English title/image and keyboard work.
