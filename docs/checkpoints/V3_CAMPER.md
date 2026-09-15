# Independent camper Animal and native attachment

## Installed work

ABI 74 provides complete separately owned visitor state, registration using
the existing optional roster/outfit checks, full native/imported defaults,
current-player greeting-memory reconstruction, and the native NPC-info detour.
No resident is replaced and no town slot, heap allocation, or model bank is used.
The native alias table remains five twelve-byte entries. Duplicate registration
preserves an existing camper's memory and rejects replacement by a different
animal while the alias remains registered.

The 1,376-byte owner at `804A1A00` contains a complete 1,320-byte Animal at
`804A1A20`, separate greeting state, and a sixteen-byte guard. The 200-byte reader
at `804A29A0` and 448-byte registration routine at `804A2D00` use checked unused
reservations in the unchanged 196,608-byte package. The original NPC-info
prologue executes through a sixteen-byte trampoline at `804A1F60`. Startup
is 912 bytes and invalidates the expanded code range through `804A2FFF`.

## Current artifacts

- Full: `build/v3-camper-runtime-02/animal-forest-v3-asset-loader.z64`.
- Full SHA-256: `bd2fd28f02f1b667c1038e4ffc1121026d4660d94847afa53eaa03d53c35849f`.
- UPS SHA-256: `7e24f4df72f67411995fa835cca2c721a0f7e4c689f3f2760b7f2b958a7d5265`.
- Build report SHA-256: `c41c4b3e21cb13ffe3b44232844de7211092a32a7da5ee73a8c3727024bdb3c1`.
- Package SHA-256: `17414c1bca2df15adcd99942715e447b223eb3aee6ffa0d69b6c4c08f5c6c3bf`.
- Registration SHA-256: `3b2894fdb1f7b9992881dbc5de0380e25ae64b2850e96f0099f8181957b452cd`.
- Reader SHA-256: `29070f91ddb0404fcb1d0b676e5503add58a8b7e15aed9f2742f832881ca563a`.
- Ten-item camping subset: `build/v3-optional-camper-01/animal-forest-v3-asset-loader.z64`.
- Subset SHA-256: `f8b195a408f04ac1e04cd6895d053b6fde11af000c50bd7247aeefdc9e5283e6`.

The offline composer retains 59 experimental choices. All selections reproduce
the full integration cartridge; no selections reproduce exact V2. Neither local
nor public served patcher changes. Generated ROMs, patches, saves, and extracted
assets remain ignored. This is not a complete-import playtest handoff.

## Bounded verification

`python3 -m unittest tests.test_v3_camper tests.test_v3_optional_composition -v`
passes all fifteen checks on the current artifact. These cover complete owner
and hook placement, exact retention of other bytes/allocations, package/startup
CRC and N64 checksums, sanitized registration/reader/cache behaviour, enabled
identities/dependencies, and all/empty/subset composition. Saved-profile codec
checks remain distinct from ordinary cross-profile reload.

The silent current native check is `tests/scenarios/v3_camper.json`, using a
2,560-byte heap fixture and a restored emulator checkpoint. Its results live in
`build/v3-camper-native-02/results.json`: **144 records, 89 native calls,
70 passing assertions, and zero failed assertions**. Results SHA-256:
`4b6ddfd32febf1d276d96421b1ceb5cffa24de7aae214e0f14612a6370873cac`.
The run restores its checkpoint, resumes without a faulted thread, and exits
cleanly. It verifies complete default Animals for a native villager, Maelle,
Cheri, and Punchy; actual English actor names and masked draw records; separate
Animal/null-list attachment; duplicate/conflicting/full/disabled alias paths;
current-player memory and native friendship; original resident attachment;
the whole unchanged 64-KiB native save, all town NpcLists, import save runtime,
and allocation/package guards. The emulator's blank save files are not a
FlashRAM persistence test or the user's save.

The first native run exercised registration/defaults, separate NPC-info
attachment, English actor names, imported masked draw records, duplicate/conflict
handling, disabled/test IDs, and full alias capacity. It then exposed an incorrect
greeting-memory offset. `Animal_c`'s source comment says `+0C`, but the original
native initializer uses `+10` for the aligned memory array. Registration is fixed
to use `+10`. The test also uses the actual sixteen-byte personal ID and memory
friendship offset `28`, not the misleading field comments. The failed
`build/v3-camper-native-01/` evidence and old local artifact remain preserved;
neither is the current composer base.

## Remaining work

Bind selection/start/stop and greeting transitions to the native event manager,
finish the remaining masked NPC/conversation readers, English conversation/reward
states, tent lighting, and floor sounds. Preserve the camper's actual donor
acquisition route and only award enabled camping rewards. Then test ordinary
entry, conversation/reward handover, exit, appearance, and persistence together.

Native default/reader calls are not a complete NPC constructor or GPU test.
Emulated RAM checks do not prove FlashRAM write/restart/reload. The unresolved
exterior field-background allocation result remains documented in the
[exterior checkpoint](V3_CAMPSITE_EXTERIOR.md), not waived by these checks.
Unchanged old builds are not re-tested.

Saved format 2 and the selected profile do not change. The codec accepts equal
or larger profiles and rejects missing dependencies; ordinary cross-profile
reload remains unverified. Imported saves must not be loaded in V2. The full
V3 goal, including other donor content and browser composition, remains open.

## Native review notes for the next batch

The original NPC overlay's mask readers at `8097F27C`, `80980168`, and their
NPC2 equivalents use an explicit nonzero alias outfit without searching town
animals. Registration always supplies that outfit. Native draw-index resolution
at `80980014` uses the alias texture ID; `80980624` selects the existing masked
allocation class when the alias exists. The `8097F830` constructor branch stores
the alias and sets its `exists` byte. These are instruction-review findings,
not completed constructor execution.

The event manager's status dispatcher at `80961004` takes `(manager, control)`;
the control starts with event type, start callback, and stop callback at offsets
`0`, `4`, and `8`. It calls start when status bit `1` is set and bit `10` is clear,
sets bit `10` unless bit `20` suppresses it, and calls stop/clears bit `10` when
inactive. A zero callback result retains the pending transition for retry. The
manager loops over the pointer directory at linked `809623D8`, count `80962458`,
from `80961A04` and `80961B40`; the second dispatcher is `80961100`. Complete the
control/directory ownership and placement-failure policy before enabling type 70.
