# Complete fishing-record winner names

## Installed state

`build/fishing-name-pilot` installs the save-preserving winner-name reader and
retains the English map labels, full map/guide names, and every preceding
translation layer. The [specification](../../specs/FISHING_NAME.md) records the
saved identity layout, NPC-only markers, exact alias lookup, hook, and ownership.

All 216 native villagers resolve through 394 exact Japanese or fitting English
saved-name aliases. The complete eight-character English literal is copied into
dialogue field zero. A matching visible player name is not enough to trigger
translation: both numeric IDs and the complete dummy-town marker must match.
Unknown keys keep the native six-character result. Saved records, winner
selection, scores, number formatting, and all name-writing code remain unchanged.

Only one original actor instruction changes, at `80A9031C`. The actor image is
10,048 bytes, including its original sixteen BSS bytes, 360 helper-code bytes,
alignment, and the immutable 6,368-byte alias table. Its allocation grows by
6,736 bytes over the original loaded image/BSS. The helper uses a 24-byte stack
frame; the lookup uses none. No additional permanent reservation or saved
storage is introduced. The actual cartridge configuration remains four MiB.

## Artifacts and reproduction

```sh
python3 tools/build_fishing_name.py
bash tools/build_fishing_name_pilot.sh
python3 -m unittest discover -s tests -p test_fishing_name.py -v
```

- ROM: 33,554,432 bytes, SHA-256
  `a9b1969217e2372a48b5f412e55c8918b8e2b6e52479c85fce4e303164241b04`.
- UPS: 5,129,568 bytes, SHA-256
  `28123eb2f04fd2efe54c0ab18c9cd91e6e22cfd6202fd6aef91528a69cf443f7`.
- Actor: SHA-256
  `1b24b4166dd58c18f2c24fc4841242f0c4628b97cca080e0ecf94400e31f66cd`.
- Relocation: 416 bytes, SHA-256
  `91e9826db52f2e6d7b8b970ecd4be0ed56adb57ed7bf8e692e5c6b0c3435fffe`.

Independent pinned-toolchain builds in `build/fishing-name-overlay` and
`build/fishing-name-rebuild` agree. Extracted alias data and game assets remain
local and ignored.

## Bounded verification

All six focused tests pass in 74.757 seconds. Host ASAN/UBSAN checks exercise
the exact alias set, every NPC-marker byte, full names, player-name collisions,
unknown/prefix keys, length guards, preserved inputs, and exact setter arguments.
Artifact checks preserve every original writer and score instruction, original
BSS offsets, fixed imports, and relocation at two allocation bases. Rehashed
code/resource damage and changed profiles are rejected.

Complete cartridge checks verify the fishing reader, existing guide, complete
dialogue fields, map/notice/inventory ownership, retained prior payloads, and UPS
reconstruction. Twelve combined-counter tests also pass. The counter verifies
this reader without duplicating the original villager-name records; unfinished
name readers still withhold their family-only credit.

No testing-setup retry or new native harness is needed. The unchanged complete
general-field setter reuses its recorded native execution evidence. Ordinary
fishing interaction, allocation alongside live actors, and save/restart remain
in the combined v0 smoke. Original-hardware compatibility is not claimed. The
legacy item test-fixture rejection remains recorded in the map/guide checkpoint;
this batch neither reruns it nor declares it passed.

## Next implementation

Continue remaining identity/item readers and residual text/letters/accents.
The catchphrase editor at `80884B30` uses a blank four-byte temporary, not the
saved default. It clears that temporary through `8009992C` at `80884C38`, opens
the editor at `80884C68`, and copies four edited bytes at `8088445C`. Do not add
a default-prefill translation or widen the saved field based on the stale
assumption that this screen displays Japanese defaults.

The real catchphrase application gap is borrowed-key ambiguity. In the pinned
resource, one key (`D0 90 20 20`, Japanese `グー`) has two complete English
values: Dozer (`E014`), `zzzzzz`, and Bea (`E0C5`), `bingo`. Own-identity lookup
works; an unrelated animal holding those saved bytes cannot reveal which source
supplied them, so the resident loader currently falls back to Japanese. Native
greeting copies preserve only the four saved bytes. Address that ambiguity
explicitly; do not claim an exact donor identity from bytes that do not contain
it. Other keys have only one English variant. Wider custom input remains a
separate storage/compatibility enhancement, not untranslated default display.
