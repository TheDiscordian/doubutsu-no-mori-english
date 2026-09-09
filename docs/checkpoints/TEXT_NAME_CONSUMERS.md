# Town, shop, and player name consumers

## Installed

The complete combined build is `build/player-item-names-pilot`. It includes:

- The exact GameCube English omission of the Japanese town-name suffix, with
  the six-byte saved town name and native formatting routines unchanged.
- Complete sixteen-byte item-name preparation in all five Nook shopkeeper
  variants and Redd's in-shop actor, covering eighteen helper entry calls.
- Complete special insect/fish capture and dug-up item fields in the player
  actor, including empty-item clearing without enlarged native temporaries.

The [town suffix](../../specs/TOWN_SUFFIX.md),
[shop names](../../specs/SHOP_ITEM_NAMES.md), and
[player names](../../specs/PLAYER_ITEM_NAMES.md) specifications record the
source bindings and exact installation contracts. The item resource, English
wording, font pixels, manual line/page breaks, and timing commands are retained.
The source suffix omission is the only new bank edit; these reader connections
make existing full English names reach additional player-facing paths.

The player bridge reuses seventy-two inactive main-code bytes behind an already
installed unconditional entry jump. Both entry and tail are guarded, and native
references into the reused span are rejected. The bridge has the same zero-safe
argument behaviour as the shop helpers. No new allocation, module growth, actor
size increase, or saved-field change is introduced. The build retains its current
four-MiB memory configuration; original hardware is not certified.

## Retained artifacts

All ROMs are 33,554,432 bytes. Generated assets stay ignored and local.

| Build | ROM SHA-256 | UPS bytes | UPS SHA-256 |
| --- | --- | ---: | --- |
| `town-suffix-pilot` | `87ee432f639bbe11134e46fcfbb27d89a14f3ccaadf60b378e4834277dbbb3c7` | 4,610,853 | `8061d4ce3715e46ed3abdae7ef62786f82aaeb48b54ef4db24769c6281db4dd5` |
| `shop-item-names-pilot` | `c2af08199cdea57598439456705f61c9e0dbd88e802f517354957b90e34a326a` | 4,720,104 | `8413dd1af6a0a9e6bf41a652d23d443c11192bfc3632c65f96dd74c4037d2e00` |
| `player-item-names-pilot` | `eb8d09b49f50409082bb33c95aea9c6ff28e66b9b2651b9c55f81d6bcf832a6a` | 4,924,869 | `821b62cbb9cd97f0d7c1c60d9ca504a3fc2ec4ac1667b76ba11908ebd46361a6` |

The shared seventy-two-byte helper has SHA-256
`4171f5f750aeb37e0ff8f20e0c65cbb843c8d6f178211c1a9751dad1cdba4b79`.
The three player call sequences total 84 bytes, SHA-256
`dfa32da6b51ba62f78d8bf3c575054aac7ee934b012163d60047404a2abd653b`.
They are independently assembled and linked with the existing pinned Docker image.

The complete player actor has SHA-256
`744033c6a585ab8edf1e7c0372360a5101baec0ea7f36d0a97cb3bd115dd914d`.
Its unchanged relocation is
`e6b56c2ee8e9df512c619f0e58da7883246039d245238b41e68b845fa06ea4c1`.
The resident module, configured font, item resource, letters, inventory,
catalogue, and editor match the retained world-label integration.

## Reproduction and checks

With the retained world-label prerequisites:

```sh
bash tools/build_player_item_names_pilot.sh
python3 tools/check_shop_item_assembly.py
python3 tools/check_player_item_assembly.py
python3 -m unittest discover -s tests -p test_town_suffix.py -v
python3 -m unittest discover -s tests -p test_shop_item_names.py -v
python3 -m unittest discover -s tests -p test_player_item_names.py -v
python3 -m unittest discover -s tests -p test_item_fields.py -v
python3 -m unittest discover -s tests -p test_translation_progress.py -v
```

The four town checks pass, including exact empty-reference/source checks,
independent import, neighbouring entries, full-cartridge retention, patch
reconstruction, and explicitly approved omission accounting. Twelve fast
counter tests pass; arbitrary empty entries receive no automatic credit.

The four final six-actor shop checks pass: bounded argument/delay-slot paths,
empty-item handling, source/dependency rejection without partial writes,
relocation at two bases, complete actor/resource retention, and UPS reconstruction.
Five existing resident item-field tests pass, including full-name insertion,
shorter/empty replacement, native fallback, invalid inputs, and message limits.

All five player checks pass, covering the three original item expressions, shared bridge
arguments, entry/tail guards, no partial writes, actor relocation at two bases,
whole-ROM/UPS retention, and current combined accounting. Physical ROM file addresses change when the patched
actors are appended; retention checks permit only those DMA address pairs while
requiring all virtual identities, sizes, and unrelated payloads to remain.

## Remaining implementation and acceptance

Continue the existing remaining reader inventory, especially other item-to-message
preparers, free-string/choice paths, house and character-name displays, and default
catchphrase input/readers. The audited item-loader calls still include Police2
(`809C28BC`), the opening shopkeeper (`80A6D054`), Redd outside his shop
(`809D7F74`), Saharah (`809DA8F4`), and the fishing-event actor (`809D608C`).
Their original names longer than ten bytes need complete connections; do not
patch them by increasing an unreviewed write length. The two home-room item
preparers also require review. Existing complete letter owners may bypass some
old handbill callers; an unchanged dormant instruction alone is not proof of a
missing live translation.

Remaining general text, letters, accents, and name/input consumers stay in v0.
Use the completed zero-safe bridge where its item/slot/window contract matches.
Do not redo source matching, name-resource construction, or exhaustive loader
tests for unchanged data. A combined silent v0 smoke must still cover normal
shops/captures/digging, menus, mail, and save/restart. No native gameplay scenario
or original-hardware test is claimed for this batch. Confirmed game defects
remain release blockers. The full goal, public-release preparation, human
playthrough, and v1 title/keyboard work remain open.
