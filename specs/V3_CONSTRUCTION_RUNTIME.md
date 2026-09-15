# V3 construction runtime tables

## Installed scope

`tools/v3_construction_runtime.py` installs all seven
[construction furnishings](V3_CONSTRUCTION_ITEMS.md) into the ABI 61 integration
cartridge. Their fixed IDs, complete native profiles/models, English names,
prices, 1×1 placement readers, and selected save-profile bits are present.
The original barrel/drum, animated speed bag, three imported garments, and
garment displays retain their identities and readers.

This runtime-only stage is not a playable handoff. The
[catalogue integration](V3_CATALOGUE_CAPACITY.md) supplies expanded pages,
ordinary stock, and scoring installation. Optional composition and ordinary
placement/persistence still need completion. Both web patchers remain V2 until the user tests and explicitly
approves V3. The local optional composer remains pinned to the preceding
26-entry integration cartridge and rejects the seven uninstalled options there.
Registry reservations do not themselves enable an option in an older cartridge.

## Fixed storage and ownership

The existing CRC-checked accessory/audio package contains sufficient unused
space after the complete melody payload. It already loads these addresses at
startup, before furniture-table initialization. No additional RAM allocation,
native heap growth, DMA-directory row, or cartridge-size increase is needed.

| RAM | Contents |
| --- | --- |
| `80481500..804817CF` | Nine 80-byte static import rows: original two, then seven new |
| `80481800..8048193F` | Ten 32-byte item records: original barrel/drum/speed bag, then seven new |
| `80481FF0..80481FFF` | Existing final package guard, unchanged |

Each import row retains index, item, enabled word, 68-byte native profile, and
padding. The static finder verifies its selected row against the independent
expanded profile table. The speed bag and clothing-display profiles keep their
separate callback-aware paths. The old two static row copies remain unused ROM
data; all actual profile seeds point to the new checked rows.

| Item | Index | Object VROM | Profile RAM |
| --- | --- | --- | --- |
| haz-mat barrel | 1161 | unchanged | `80481508` |
| oil drum | 1198 | unchanged | `80481558` |
| wet roadway sign | 1149 | `02334000` | `804815A8` |
| detour sign | 1150 | `02335000` | `804815F8` |
| men at work sign | 1151 | `02336000` | `80481648` |
| flagman sign | 1155 | `02337000` | `80481698` |
| jersey barrier | 1157 | `02338000` | `804816E8` |
| speed sign | 1158 | `02339000` | `80481738` |
| saw horse | 1163 | `0233A000` | `80481788` |

Each object fits its separate 4,096-byte ROM slot and the native 5,120-byte
model bank. All objects remain inside the existing `02200000..02400000` virtual
storage reservation. The physical cartridge remains 64 MiB; all unrelated
physical resources and original compressed house data remain untouched.

## Shared code and compatibility

The expanded static helper occupies 1,364 bytes at `80465800`, within its existing
2,048-byte reservation. Eight fixed public forwarding entries point to the
compiled functions. Native room initialization, model-bank selection, DMA,
reuse, original-profile allocation, and cleanup remain the actual game routines.

The active item readers are the clothing-aware copies in the extra save/item
resource at VROM `0220F400`, RAM `8046D000`. That resource retains its 2,972-byte
code and 2,976-byte aligned transfer. Exactly three installed instructions change:
the metadata table's high address, low address, and end pointer. All public
function addresses, save-code instructions, complete-roster clothing bridge,
and five applied clothing name/price fixes remain intact. The obsolete unwrapped
item-reader bodies in the main prefix do not become the active path again.

The builder checks original cartridge/report/artifact hashes, empty table space,
complete source metadata, fixed IDs, object bounds, profile seeds, code sizes,
public symbols, applied clothing fixes, source descriptors, virtual/physical
storage, both resource CRCs, startup-prefix CRC, N64 checksums, and UPS
reconstruction. It writes a fresh ignored output directory only.

Saved format 2 and existing item/villager IDs remain unchanged. The selected
profile gains seven furniture bits, so saves produced with this profile require
those imports. Actual codec checks accept preceding-profile saves in ABI 61 and
reject ABI-61-profile saves in the preceding profile without altering buffers.
Do not load imported saves in V2. Ordinary cross-build reload with these items
is not established by the codec checks; preserve backups.

## Remaining integration

Use the capacity-expanded integration cartridge for further work. Its 446-row
furniture list, 248-row clothing list, stock, and scoring data are installed.
Connect optional composition to the package-resident enabled words and package
CRC, and complete ordinary acquisition/placement/persistence. Do not add these
options to either served web patcher during experimental work.

The [native checkpoint](../docs/checkpoints/V3_CONSTRUCTION_RUNTIME.md) records
the passing current checks and their exact limits.
