# Dump sign artwork

Replace both seasonal dump sign atlases with the supplied English GameCube
"Dump" artwork. The native sign says `ゴミ` and `月木` (rubbish, Monday/Thursday).
The GC sign omits those printed days; importing its exact artwork does not alter
the native collection schedule, event code, fenced area, or item handling.

The building type is `28`, palette type `51`. Both native seasons use palette
`D5C1C8`, through `D5D000` table entries `14C`/`2B8`. Native 128×32 CI4 T1 images
are at `D6E4D0`/`D6FAC8`; the supplied GC donors are `.data:5208A0`/`521E00`,
palette `5018C0`, vertices `5218A0`/`522E00`, and models `521CE0`/`523240`.
The donor models' actual texture fixups and all 44 native vertex uses must match.
Native positions, UVs, normals, triangle order, palette colours, display-list
commands, and the separate T2 fence atlas stay unchanged.

For an upright source preview, the sign quad samples U 2944–4096 and V 0–1024:
U increases downward on the sign and V increases from right to left. Read the
whole U 92–127 region; cropping at U 96 would omit part of the red source word.
This differs from Nookington's wall mapping.

Patch both seasonal atlases in the original `D5E000` object and its retained
prefix at `03D00000`, which the current structure loader actually streams.
The two appended Nookington slices must stay unchanged, as must all other
building ranges. Keep every existing resource, allocation, code, save layout,
and previous English edit, and verify complete UPS reconstruction.

The shared counter inventories four Japanese source characters per original
seasonal sign. Additional storage copies do not add source IDs. Credit requires
the complete installed English images, exact native display-list/vertex readers,
seasonal palette selection, and structure range/loader bindings. Earlier builds
retain the source weight without credit. The native weekday labels are replaced
by the source-matching English design, not counted as untranslated fragments.

Use one focused host batch and the existing title-combination check. Inspect
upright sign projections in both seasons. Unchanged native graphics commands
do not require a new emulator scenario; ordinary scene/hardware acceptance
remains explicit playtest work.
