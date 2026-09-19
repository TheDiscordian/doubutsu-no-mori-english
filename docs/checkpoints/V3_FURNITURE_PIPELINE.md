# Automatic furniture pipeline checkpoint

## Shared seasonal ground runtime

The proposed ABI 110 is `build/v3-ground-categories-02/`. Its ROM SHA-256 is
`6a74b1d25eebb647674cf016305051fe0608d47cd0daae911ac197677fc1cc51`,
report SHA-256 is
`9716d233fb4bd829b186dc748a3b48d279987b7d3fdaf830c69adbf55d627e2b`,
and UPS SHA-256 is
`591eb69b927d6164252c9c49a63ac664ee1360261a6698c03cc1082ecad6e1c1`.
The main build lock stays at ABI 109; this proposal is not a validated handoff.

The shared installer integrates all four seasonal ground owners together,
without another artwork conversion or per-item script. Each receives its full
expanded table, nine complete native descriptors, relocated callbacks,
constructor entry, actor-tail index arrays, and matching setter capacity.
The native global category entry resolves installed, selected parents and
delegates other items directly to the existing translated wrapper, avoiding
recursion. All twelve furniture-type windows now resolve the correct seasonal
loaded owner. Saved format 2, all 104 experimental choices, parent profile bits,
ordinary banks, and both served V2 patchers stay unchanged.

The module is 44 KiB with 1,612 bytes of new code and 144 bytes of configuration;
startup remains 952 bytes. Cherry/ordinary/Christmas gain 1,376 bytes of overlay
BSS and 864 bytes of actor indices; winter gains 1,360 and 856 bytes respectively.
Existing common state, matrix nodes, and Christmas light records do not move.
All four setter frames are 264 bytes. Expanded categories number 108, or 107 in
winter. Source numbering and physical artwork pointers are unchanged.

### Defect found and corrected

The initial proposal `build/v3-ground-categories-01/` faulted before the native
probe reached its game-frame breakpoint. The saved checkpoint independently
showed faulted thread `80145630`, PC `80262D84`, and bad address `00000004`.
The live cherry owner was at `8025BCE0`; its native draw-body instruction at
offset `70A4` dereferenced a null part. The native classification had populated
start index 64 with 118. That is the original `NONE` sentinel, previously outside
the copied/drawn range but now inside the extended arrays.

The correction gives every unused extended slot a real 32-byte no-draw
descriptor. It preserves original sentinel values and comparisons, with zero
ordinary/shadow lists rather than borrowed artwork. Host tests check every
unused row and descriptor. Both subsequent corrected-build runs report no
faulted thread and reach the normal game-frame context. Do not use the first
proposal; it is retained only as local failure evidence.

### Verification and exact remaining check

Six focused tests pass in 5.150 seconds: sanitized complete table construction
and reloaded-owner pointers, category bounds/selection, every native edit,
two relocation locations, all allocation/stack contracts, source mutations,
retained artwork/resources, startup bounds, cartridge checksums, and full UPS
reconstruction. Twelve optional-composition tests pass in 10.601 seconds against
the proposed lock, including the exact no-import V2 output and actual save codec.
The first proposal's earlier passing checks are not evidence for its startup bug.

`build/smoke-v3-ground-categories-02/` verified corrected startup and the entire
44-KiB module, then could not allocate the probe's 212,992-byte scratch block.
This was a test-fixture allocation, not a production allocation failure. The
justified setup retry uses 53,248 bytes of native heap for executable owner data,
plus a checked, saved/restored unowned Expansion Pak gap for fixture data.

`build/smoke-v3-ground-categories-03/results.json` contains 31 records,
16 passing assertions, and one failing assertion. Its SHA-256 is
`ccf951700e8cfc1d3102c1a9cf848e72ef0bc94c525c8c26e67fffeaa914b87f`.
It executes selected/disabled/original categories, loads and relocates the full
cherry owner, builds and compares every original/imported table row and part,
executes the four constructor pointer/count writes, and clears the entire
expanded setter array. The matrix-sentinel comparison also succeeds before
the stopping point. It then fails the setter-copy continuation/stack assertion
at loaded entry `802E3598` (owner offset `5E78`).

That record does not include the observed PC/SP, so the cause is unresolved,
not established as a fixture error. The probe now records PC, SP, stop reply,
and expected values on this failure, but that addition has not been rerun.
The native setup retry and 30-minute harness allowance are spent. Do not repeat
the complete prefix or claim that copy/drawing passes. The other seasonal
execution, complete copy, native graphics lists, final guards, verified scratch
restoration, and checkpoint restoration remain unverified. No user save or
hardware audio was used. Keep the potential copy/memory defect open and the
proposal unpromoted while continuing unrelated shared acquisition work.

Saved formats are unchanged from ABI 109; same-profile compatibility is expected
but has no new ordinary save/reload evidence. Import-enabled saves remain
unsuitable for V2. Carry the separate V2 museum-header fix into V3 before its
next handoff, and preserve both V2 patchers.

## Shared police and handover runtime

ABI 109 at `build/v3-category-runtime-03/` installs all nine complete category
objects through the shared importer. Two 71-entry material/geometry tables keep
all 27 original categories, with imported indices derived as `27 + source type`.
The selected-parent reader keeps disabled/missing extended IDs out of the native
36-entry tool table. Police and handover use the new reader and shared tables;
all four seasonal ground consumers remain required work before enabling imports.

The 40-KiB equipment module grows by 12 KiB, with the previous prefix intact.
Police actors grow by 88 bytes; stack capacity, all 70 start indices, 257 matrix
nodes, trailing item-table offsets, actor allocation, and drawing bounds agree.
The handover actor stays unchanged. Every resource sample, vertex, and command
is retained except the three checked physical-resource pointer relocations per
object. Native material/matrix/geometry ordering remains intact.

- ROM SHA-256: `a55c7ebf3d4c59e0987892536e1ba3565b6a50c73c6aecf743b602015b6e0ca0`.
- UPS SHA-256: `3f5bf4eb38e2aedb87780ec641350ae81a1822e2cf674b6a9cddecc16b0aa1cb`.
- Five focused host/cartridge checks pass in 5.510 seconds: sanitizer-backed
  selected/disabled/malformed category lookup, complete artwork retention,
  fixed source numbering, original table preservation, complete owner changes,
  relocation at two heap locations, allocation bounds, UPS reconstruction,
  checksum/startup, unchanged prior equipment, unrelated resources, and profiles.
- Twelve optional-composition checks pass in 8.940 seconds against this exact
  proposed build lock: import-free V2, select-all, dependencies, sparse choices,
  deterministic output, and the real profile/save codec remain intact.
- Native `build/smoke-v3-item-categories-01/results.json` passes on its first
  invocation: 63 records, 44 passing assertions, no failures. Results SHA-256:
  `3708ae8b02336f0d3a72fb9ed71657a497f7307ee17601e21371b91522efcb5a`.

The silent native run checks the complete startup-loaded module, selected and
disabled categories, original fallback, both actual relocated owners, all 70
police start indices and 257 matrix sentinels, rejection of invalid indices,
original and imported material/geometry dispatch through the real drawing loop,
two handover assignment windows and three table-lookup windows. Memory guards,
profile restoration, full checkpoint restoration, and graceful shutdown pass.
The FlashRAM remains erased and no user save is used. The fixture deliberately
uses an empty field for police classification: terrain queries and full item
acquisition are not claimed. It supplies representative linked matrix records
for drawing, not an ordinary lost-and-found playthrough or GPU image comparison.

Build attempts `-01` and `-02` stop before producing a ROM: the first catches a
transfer-width/texture-format distinction while rebasing CI4 pointers, and the
second catches a duplicated Python receipt keyword. The corrected `-03` build
and focused checks use the actual complete assets and consumer paths.

Saved formats, saved identities, all 104 experimental choices, and both served
V2 patchers remain unchanged. V3 cross-version/profile save compatibility and
original-hardware behaviour are not established by these component tests.
Next integrate all four seasonal ground category tables/arrays and the global
type route, using these installed objects. Then finish acquisition,
collection/catalogue, selection, and ordinary gameplay/persistence. Carry the
V2 Museum header correction into V3 before its next private handoff.

## Shared ground and handover artwork

The `item-category-art` category prepares all nine complete ground/police/
handover representations used by the donor's 43 extra handheld parent/state
records. Source category tables select the artwork; no per-item model list or
new native scenario is introduced. Worn axes remain states, and shared resources
do not create multiple logical imports. Source categories are `19`, `33`,
`37..43`; the receipt records every parent identity and official name locator.

Each complete object contains a 32-byte palette, a 512-byte 32×32 CI4 texture,
four vertices, and separately callable material/geometry lists. Nine objects
occupy 7,344 bytes with 9,216 texels, 144 palette entries, 36 vertices, and
18 triangles. Discovery verifies both complete handover/police table pairs,
all four ground descriptor chains, and twelve complete consumer functions.
It retains the source variant-specific ground bases `68/68/68/70` rather than
assuming every seasonal table is identical.

Artifacts:

- Prepared build: `build/v3-item-category-art-02/`.
- Art receipt SHA-256: `ad60ba447b1ab62f7d996bbae8610b874aad56a95cf34f4e473c72563f4bc21e`.
- Inventory receipt SHA-256: `1abc0d0486e63c416dc7c43465bb849a186adcbec4bbf98d988bbaf3d8661284`.
- Format: `AFV3-ITEM-CATEGORY-PREPARED-ASSETS-1`. Existing furniture and held
  resource installers explicitly reject it; native integration is not implied.

The shared converter first validates the complete joined source model, then
splits its decoded commands into material and geometry lists. The source's
paired texture/tile command consumes two words but one decoded row. The initial
`-01` preparation counts raw words instead, incorrectly moving the vertex load
into the material list before the caller's matrix. The independent geometry
test catches that actual converter defect. The corrected decoder-boundary walk
keeps the vertex load with geometry; `-01` is not suitable for installation.
The initial preparation does not install these objects in a ROM; ABI 109's
police/handover integration above installs the corrected `-02` output.

Six focused category checks pass in 3.368 seconds on the corrected `-02`
preparation. They cover every source pixel, palette colour, vertex field,
triangle, retained graphics command, all parent/category/owner relationships,
rejection of changed consumers, shadows, callbacks, mismatched tables, and
unsupported selections. Joining the emitted lists after removing only the
intermediate return exactly reproduces the ordinary full-model conversion.
A seventh focused check passes in 0.350 seconds, retaining the installed
ordinary furniture batch's generated commands and rejecting material commands
in a geometry-only inherited-state list.

The initial test command also discovers unrelated imported test classes and
uses an incorrect held-installer function name. Its full result is not a pass.
The corrected test module imports the shared checks as a module, calls the real
installer entry, and explicitly selects only the intended category classes.
No emulator or hardware test is claimed for this converter-only batch.

The preparation leaves ABI 108 unchanged; the later runtime batch above retains
its preview/runtime evidence. Saved formats, profile bits, selectable choices,
and both served V2 patchers remain unchanged. Remaining integration covers all
native ground variants before enabling the item-type reader globally.
Do not substitute existing tool-bag artwork for the source fan representation.

## Shared inventory equipment previews

ABI 108 installs source-derived preview records for all eight fan parents
through the existing shared refresh. The separate inventory owner retains its
five original kinds and empty sentinel. Eight expanded tables reuse complete
models and holding poses, and a shared dispatcher resolves original tool
callbacks against the currently loaded inventory owner. No per-item installer,
new profile bit, selectable choice, or saved-format change is introduced.

The 540-byte adapter and its immutable tables extend the equipment reservation
from 24 to 28 KiB. Startup remains 952 bytes. Existing model/animation banks,
all earlier equipment-module bytes, source artwork, and player actions remain.
Exactly sixteen obsolete table relocations are removed; the complete owner and
relocation allocations stay unchanged. The specification records the source,
native ownership, entry points, and bounded layout.

Artifacts:

- Build: `build/v3-inventory-equipment-03/`, promoted in the development lock.
- ROM SHA-256: `25f0ee69193c75230b86b1a96e3d760c1cdc469fedc2a4ec39b3cafe7206122c`.
- UPS SHA-256: `57f84c4c11a52b8c5613f3a873a40beb7c00378cabf70e0cf80a2fa1fb63c4ca`.
- Receipt SHA-256: `0a0f83dcf853beab3f87507ebca4ae2f1be2008d5a1afe401d331fcf19377d35`.

Four focused checks pass across the host/source/cartridge commands. The
ASan/UBSan host check passes in 0.261 seconds. Two of three cartridge checks
pass in the initial 4.195-second invocation; the third incorrectly treats the
ROM file directory as immutable when installing relocated resources. Its
corrected focused invocation passes in 4.681 seconds. No cartridge change is
needed. These checks cover source/table relationships, retained owner bytes,
relocation at two bases, selected-only bounds, preserved resources/profiles,
startup, checksums, and original-ROM patch reconstruction.

Twelve candidate-bound composition checks pass in 8.758 seconds. All selected
imports reproduce ABI 108; empty selections reproduce V2-11. Dependencies,
sparse profiles, catalogue packing, and the actual saved-profile codec pass.
These are component checks, not ordinary save/restart evidence.

The first silent native run at `build/smoke-v3-inventory-equipment-01/` passes
104 records and 79 assertions with no failures. It executes eleven actual
inventory selector cases, two complete model transfers, the complete holding
pose transfer, and four native draw-table/dispatch windows: two imported fans,
the original axe, and the original shovel. Loaded owner/BSS, full equipment
module, private memory guards, no-fault status, restored player/profile, and
checkpoint restoration pass.

The same current-cartridge run completes the prior pocket-icon fixture's
unfinished controls. All seven selected/disabled/wrapped/native cases pass,
alongside full-width register preservation, correct resolved artwork pointers,
guards, unchanged module/owner/segments, and restored state. No old cartridge
is replayed. The combined results SHA-256 is
`f8dc835d59c5803c6ad7436973683093a7fbb57d5cedff1a911e8a3654aa3ea6`.
The isolated run shuts down gracefully with erased FlashRAM; it uses no user
save and plays no audio.

Full inventory construction, outer matrix/segment setup, GPU appearance,
ordinary equip/put-away, acquisition, and persistence remain unverified. No fan
is offered as playable. Next connect the remaining category consumers and
source acquisition, context-correct catalogue/collection, and optional profiles.
No more standalone preview or pocket-icon harness work is required without a
concrete changed dependency or observed defect.

Same-profile ABI 107 saves are expected to remain compatible in both directions;
no new ordinary cross-version reload is claimed. Import-enabled V3 saves remain
unsuitable for V2. Both served V2 patchers are unchanged; carry the museum-header
correction into checked V3 composition before the next handoff.

## Shared pocket icons

ABI 107 installs complete donor pocket artwork and a selected-parent reader
through the existing `--refresh-runtime --player-actions` path. Discovery
consumes the installed parent records and complete relocated tool-icon table,
not a maintained item list. All eight fans share one actual donor palette and
texture. Existing conversion retains all 1,024 indices and sixteen colours;
the descriptor table and deduplicated resources occupy 1,024 bytes at `804A6800`.
The combined parent/icon code is 1,284 bytes, with fixed name/price entries.

One native submenu detour replaces the tool-table HI/LO pair and removes only
those two relocations. The 560-byte relocation allocation, owner allocation,
24-KiB equipment module, startup size, models, motions, callbacks, sound, and
saved format 2 remain unchanged. The hook preserves full-width registers and
HI/LO, resolves the currently loaded owner, retains original descriptor paths,
and emits no drawing commands for a disabled extended parent. No fan profile
bit or logical import is enabled; the optional composer still has 104 choices.

Source category 43 is distinct from the menu's ID-derived tool category two.
The source `mTG_select_tag_decide_item_normal` uses the latter for normal action
menus. The native short item-type table and its actual consumers remain work;
they must not be confused with the now-connected pocket-icon lookup.

Artifacts:

- Build: `build/v3-held-pocket-icons-01/`, promoted in the development build lock.
- ROM SHA-256: `66205bfbf644fbfc7bc6e356d3a24d859e4676162e1b4bd3dc04dad5b21c0781`.
- UPS SHA-256: `bc0f44b421e06034c075f6ce89b90ce8c6a396d038b4bea89c262493b4064cdf`.
- Receipt SHA-256: `a906fb48102cc8dc227ad33c1c50c2a10d98897b59579ec77ee3db2f26054590`.

### Verification and bounded follow-up

Four focused checks pass in 5.713 seconds. They cover complete source artwork,
all pixels/colours, shared identities, bad-pointer rejection, selected-only
bounds under ASan/UBSan, exact declared owner edits, relocations, retained module
regions/profile/resources, startup checksum, native ROM checksum, and original
ROM UPS reconstruction. The initial invocation has two fixture errors: a wrong
patch filename and a mutation removing a cached relocation key. Correcting the
filename and changing the mutation to an invalid relocation section produces
the passing invocation without changing the cartridge.

Twelve current optional-composition checks pass in 8.947 seconds, with the
candidate lock bound inside the test process. All selections reproduce ABI 107;
empty selections reproduce exact V2-11. Sparse choices, actual save codec,
dependencies, catalogue packing, and retained identities pass. Neither patcher
is changed. Python syntax compilation and `git diff --check` pass.

The first silent native run, `build/smoke-v3-pocket-icons-01/`, records fifteen
entries and six passing assertions. Actual parent relocation, imported-hook
register preservation, and the first selected fan's complete 27-command drawing
pass. The disabled fan correctly produces no commands, but the fixture attempts
a zero-length debugger read; the debugger rejects that request. This is a
classified fixture failure, not an observed game fault. Result SHA-256:
`ba4583ce2ab0d10b82846bf194aaabb86bf5c69042060f14d398eb0a99edab82`.

The single corrected retry, `build/smoke-v3-pocket-icons-02/`, records 22 entries,
nine passing assertions, and one failed assertion. Complete loaded code/BSS,
equipment resources, profile, full GPR/HI/LO/floating-point preservation, two
independently enabled fan identities, and disabled drawing pass. The unchanged
gift case emits 27 commands, but the fixture incorrectly expects segmented
`0C012400/0C012420` pointers instead of the emitted resolved `00012400/00012420`.
The original drawing consumer calls native `Lib_SegmentedToVirtual` at
`8009ADA8` for both resources; its source uses `SegmentBaseAddress` at
`801458A0`, not a physical-address mask alone. The gift branch is outside the
modified instructions. This establishes a comparison error, not substituted
gift artwork. Result SHA-256:
`8238a2890f9df5d8c1d406eb456b9585c021c0a50a41d3034f76ac674a5ab78d`.

The fixture now resolves original descriptors through the actual segment table
and retains the correct zero-command case. It is not rerun: the setup retry
allowance is exhausted. Native gift/tool/umbrella comparisons, final guards,
restoration assertions, and checkpoint completion remain unverified. The
`finally` cleanup executes on both failed attempts, but that does not substitute
for the omitted full restoration checks. No display list is submitted to the
GPU, no audio plays, no user save is loaded, and no FlashRAM write is requested.
Do not report either partial run as a complete native pass or hardware evidence.

Continue inventory-screen player-item ownership/selection/drawing and remaining
category/acquisition/catalogue/persistence integration. Reuse passing component
evidence and carry the outstanding native control checks into the next relevant
inventory batch; do not repeat standalone harness attempts here. Same-profile
ABI 106 compatibility is expected in both directions because saved formats and
profile requirements are unchanged, not established by a new ordinary reload.
Import-enabled V3 saves remain unsuitable for V2. The V2 museum-header correction
still needs checked V3 integration before a handoff; both served patchers stay V2.

## Shared parent name and price readers

ABI 106 connects the eight implemented fan equipment records to the existing
public name/price paths through the same category importer. `parent_records`
verifies complete donor tables and consumer functions, price sentinel, and
pointer dependencies. The 1,360-byte `AFHI` table preserves official names,
donor prices, source category 43, canonical collection IDs, and equipment kinds.
All eight official names are credited in `translations/provenance.json`, using
`itemName_tool` and their actual indices. No second source catalogue is created.

The parent reader is 512 bytes at `804A6000`; the expanded display wrapper is
696 of 768 bytes. Names require sixteen writable bytes and selected equipment;
prices retain the native sixteen-bit argument convention. Action code, callbacks,
owner relocation, models, motions, sound, allocations, 104 choices, and saved
format 2 remain unchanged. No fan selection bit is enabled. Donor category 43
is recorded, not installed as an unchecked native menu/icon index.

Artifacts and verification:

- Build: `build/v3-held-parent-readers-01/`, promoted in the main build lock.
- ROM SHA-256: `46bfef14b0849f202bc0569408bc8d6337b889a1677c092c85c28111c48f2e7c`.
- UPS SHA-256: `51c815430898783f4d607ce5bc7f92b76261028386ea774b53b31a2fdcac42dd`.
- Build receipt SHA-256: `544bd16e49375135f37487eb554f5524bef0d344f975c6360f3ce9ec0859f48e`.
- Two cartridge checks pass in the initial 5.839-second command: complete source
  records/provenance, mutation rejection, all declared reader/table bytes,
  retained action module/resources/profile, CRC, and UPS reconstruction. The
  accompanying host fixture fails compilation because a sixteen-character
  string initializer would omit its terminator under the host warning policy.
  That command is not wholly green. The fixture explicitly copies sixteen name
  bytes; its corrected ASan/UBSan check passes in 0.159 seconds, without replaying
  the two passing cartridge checks.
- The shared display-wrapper ASan/UBSan check passes in 0.148 seconds, including
  the extended parent range, native argument widths, exact write bounds, and
  existing synthetic display/garment categories. Four focused checks pass across
  these commands.
- Twelve current optional-composition tests pass in 8.920 seconds. The test
  process binds the candidate lock before running the existing suite. Empty
  selections reproduce V2-11; all selections reproduce ABI 106. Actual codec,
  sparse selections, dependency checks, catalogue packing, and collision guards
  pass. Neither patcher is updated.

The first native run at `build/smoke-v3-held-parent-readers-01/` stops at 23
records/13 passing assertions. Its name-call proof incorrectly uses the harness
escape reserved for code outside the translation module. The harness rejects
that call before executing it. This is a fixture error, not a game failure.
Result SHA-256: `d7a42c2b209979dd72e30d2b0f392ab7fcf7a745f01ccc9e9c51516ef37cb9f6`.

The single corrected retry at `build/smoke-v3-held-parent-readers-02/` uses the
ordinary linked-module call after verifying the complete resident name entry.
It runs the same ROM and passes 112 records with 98 passing assertions. It
exercises the real loaded player selector, native switch returns, rejected IDs,
all eight independent selected/unselected fans, actual public English names and
prices, adjacent name guards, and undersized destination rejection. It verifies
passive/all/blocked permissions, hidden/force-visible priority, forbidden scene
rejection, state restoration, heap/module guards, no CPU fault, checkpoint
restoration, erased FlashRAM, and graceful shutdown. The equipment source is the
title-demo field; ordinary pocket/equip gameplay is not claimed.
Result SHA-256: `98390eafcc39ef4cb632f02f24bbee8f68711350f9b8e2df3d01e95b324b342e`.
Probe SHA-256: `ee253e9a8711f2d764aa7242c3ff533836ff8cfe218b8fb8778dad83d1b9c27f`.

This meaningful reader integration also completes the previously pending
selector/visibility checks; ABI 105 is not separately replayed. No physical
audio, user save, ordinary save/restart, or hardware test is involved.
Same-profile ABI 104/105 compatibility is expected in both directions, not newly
verified by ordinary save/reload. Do not use import-enabled V3 saves with V2.

Continue shared inventory/ground category, menu/icon, and inventory-screen
equipment selector/draw integration. The latter is its own owner and is not
covered by world-player drawing. Then connect acquisition, actual collection/
catalogue representations, optional selection, and ordinary lifecycle/persistence.
No fan is selectable or offered for playtesting yet; both V2 patchers stay intact.

## Shared selected-equipment adapter

The same category importer extends actual equipment selection and passive-item
visibility. `selection_records` combines the source item/kind tables, room aliases,
implemented callbacks, and checked model/animation pairs. It produces all eight
fan records in one 752-byte `AFHS` table at `804A8500`, without a per-item list.
Each item uses its canonical collection display's independent saved-profile bit.
No bit is enabled, no inventory reader/acquisition is installed, and no logical
choice is added. The original native 36-item switch stays intact. Two branch
hooks retain original ordinary/title equipment sources and existing scene,
hidden-item, force-visible, and all-items rules. Only the passive-item branch
adds selected category records. Existing fan callbacks, draw, and poll pointers
are rebound to the new compiled symbols. No relocation record changes.

### Candidate and focused checks

- Unpromoted ABI 105: `build/v3-held-selection-01/animal-forest-v3-asset-loader.z64`.
- ROM SHA-256: `111f011b45793a94d770da86ddb1c9055b226110398478d356e13f4a08d24f5e`.
- UPS SHA-256: `89d248e672843d8fc54da0487c919d7c1d5e4f5d3640e546681f49faa7023e4a`.
- Receipt SHA-256: `700014c5bf2eb88a3b2c5449df29dff15525b111b68f24c75f86345d70ed2ed5`.
- Compiled code is 2,504 bytes, inside the existing 8-KiB code reservation.
  The complete 24,576-byte module, 3,517,632-byte blob, startup, models, motions,
  audio, saved format 2, and 104 choices retain their allocations/identities.
- Current promoted lock remains ABI 104. Same-profile compatibility is expected,
  not a newly verified ordinary save/reload result. Do not use V3 saves with V2.
  Both served patchers remain V2; no playtest handoff is made from this candidate.

The selected-equipment host sanitizer passes in 0.164 seconds: all 16-bit input
IDs, individual fan bits, original passive umbrellas, unsupported kinds, malformed
headers/records, invalid masks, readiness, and permission flags. Three candidate
cartridge checks pass in the 5.576-second combined command, checking actual source
relationships, mutation rejection, complete table bytes, two relocation bases,
retained native switch, callback rebinding, profiles/resources, and UPS/CRC.
That command also names a nonexistent control-test method and therefore ends
with an import error, not a fully green command. The corrected control host
method alone passes in 0.183 seconds; the three passing cartridge tests are not
replayed. A focused original-switch/permission fixture check passes in 0.090
seconds. Six tests pass across these commands.

### Bounded native attempts

`build/smoke-v3-held-selection-01/results.json` stops after 12 records because
the probe requests permission value two, absent from the actual table; its
values are zero, one, and three. It has not called the changed selector yet.
Its result SHA-256 is
`bd3b39823c0962dfee7c318d9d9a288b81811842a33305a0d22ae9f814349b6a`.
The one corrected retry, `build/smoke-v3-held-selection-02/results.json`, stops
after 16 records when the probe expects item `2202` to return kind two. The
actual return is 35, exactly matching the original ROM's switch target and
constant-return instruction. The first two native item returns and retained
stack checks pass. This mismatch is not a cartridge defect.
The retry result SHA-256 is
`f57112a4d796baaec05d7d0e547058fabdac4fd9e10a715dc16001dc91ef59a7`.

The probe now derives expected native kinds from the original complete switch,
checking its hash and constant-return branches; the original last item is also
kind 33, not the fixture's guessed 35. The fixture check covers both mistakes.
No third native attempt is made for this batch. Imported positive selection,
passive visibility, final restoration/guards, and the completed scenario remain
unverified; no successful native or ordinary-equipment result is claimed.
The corrected probe is retained for the next meaningful inventory integration.

Continue parent inventory/names/prices/acquisition, context-correct collection/
catalogue, and optional composition from the candidate's explicit build lock.
Retain the promoted ABI-104 artifact until the changed native path is verified.

## Shared fan action activation

The existing action adapter registers the complete source fan callback group:
compiled setup and movement plus native net reset `808BE140`. Source submenu
and settle callbacks remain null. Four ordinary umbrella polls call the shared
umbrella-then-fan helper with unchanged priority and following input checks;
the umbrella's own repeat call remains native. Four obsolete local JAL
relocations are removed, bringing the total action/held removals to 64. All
original actions remain intact, and fifteen unfinished extended actions reject.

The outside-owner audit checks all three native comparisons against 105. One
is a resource byte-length bound. Equipment-change dispatch only returns
`-1, 7, 8, 9, 10`, so its bound needs no expansion. The native out-of-range
event-position result equals the source fan's zero entry. Complete consumer
bodies, callback registration, source dependencies, and the event table are
bound in the receipt; no unrelated core table changes.

The first full native action-cycle check exposed a real game bug: native speed
one crosses source frames 7.5 and 8 together, and an `else` swallowed the release
check. Repeat wrapping also skipped the idle threshold at 8.5. Independent ordered
event checks now handle the first boundary; a virtual crossed-end coordinate
handles the wrap without changing the rendered frame or advancing animation
twice. This is an implementation correction, not a testing-setup retry.

### Build and verification

- ABI 104: `build/v3-fan-action-dispatch-03/animal-forest-v3-asset-loader.z64`.
- ROM SHA-256: `b7a8964f6d8fa323c2c84712086cdb04949f07de230ac794ba3ae4a9d146d620`.
- UPS SHA-256: `9f2342690162bbe8ecc016022a58c4ee8d74ba92e013246bf5b887c5c1928a25`.
- Receipt SHA-256: `afa35cf9a6cba7f32ec8569ff239e7af3bf1835dd9bfe2a265df78287f74de4e`.
- Action code is 1,944 bytes, retaining the 80-byte dispatch prefix. Module is
  24,576 bytes; startup remains 952 of 992 bytes. Blob is 3,517,632 bytes, with
  611,136 free. No allocation, source model/motion, or sound resource changes.
- Saved format 2 and 104 choices remain unchanged. Same-profile ABI-103/104
  compatibility is expected both ways; the current actual-codec checks pass.
  No new ordinary save/restart or hardware result is claimed. V3 saves are not
  for V2. Both served patchers remain V2.

Four focused current-build checks pass in 5.692 seconds: host sanitizers,
held-A repeat and released idle across the wrap, complete source/callback/audit
contracts, owner relocation at two bases, resource retention, and UPS/CRC checks.
Twelve current composition checks pass in 8.667 seconds, covering exact no-import
V2, all-import ABI 104, sparse choices, dependencies, and the actual save codec.

The initial native result `build/smoke-v3-fan-action-dispatch-01/results.json`
contains 42 records and 24 passing assertions before the missing exit request;
SHA-256 is `55ef474cedc8ba13b49f36162376b0b2256c568d2c75955566b52aaa8c95a213`.
Raw requested-action and post-wrap frame values were not logged in that run;
the diagnosis comes from the boundary logic and the corrected execution.

The corrected result `build/smoke-v3-fan-action-dispatch-02/results.json`
passes 60 records and 37 assertions, SHA-256
`cd413a906a714b6ef08d901d87cc7f3d1d65bc6617884b6c32f7f57e0742f58d`.
Probe SHA-256 is `ea04a39f5e58211f837429005b177374156d40488887d69fb43f98c3bf667f98`.
Actual native setup selects animations 270/0, main dispatch advances the live
actor, frame eight requests movement action eight, and the next dispatch exits
the swing. Net reset, disabled-action rejection, full actor/animation-bank
restoration, guards, checkpoint restoration, and no CPU fault pass. Native
stationary idle and positive equipped-fan input are not claimed. FlashRAM stays
all `FF`, SHA-256
`b5a41c3758763bbec72769fab4a2533bf2db0b6312d93d25a695f9e4b9e02260`.
No audio or user save is used.

That run used build `02`; build `03` only clarifies source comments/indentation
and has exactly the same complete ROM and compiled code. The proof is retained
without another native run. Build `01` is not promoted.

Next connect profile-aware equipment selection, scene/special-action permissions,
parent inventory/names/prices/acquisition, context-correct catalogue ownership,
and persistence. No new logical item is enabled by callback activation alone.

## Shared held-item dispatch

The callback converter handles the two complete donor held-item tables using the
same format/reference/relocation rules as player actions. Native main/draw tables
grow from 21 to 24 entries without changing any original callback. Category 23
contains the source fan's static main/draw behaviour; categories 21 and 22 remain
null until balloon and pinwheel rigs are implemented. This does not select an
item, enable action 109, or add a browser choice.

The original zero-return callback supplies the source fan's empty item update.
Its complete 20-byte native body is checked. Drawing emits the checked model's
display list from either active equipment bank and clears the native rod-tip
flag. Missing resources and invalid banks emit no command. The original outer
drawer retains the hand matrix, scale, opaque stream, and segment-six binding.
The donor balloon-start flag has no native storage; no unrelated field is used.
The source net-angle reset is bound to the equivalent native `808BE140` routine,
but its action-table registration remains pending.

### Build and verification

- ABI 103: `build/v3-held-item-dispatch-02/animal-forest-v3-asset-loader.z64`.
- ROM SHA-256: `d9c84c537a1565986de459667e4428d9d0dadcf79a1f1ea7a1904eb03fd99f0b`.
- UPS SHA-256: `b094874d1378dae030b81ea676792453da85e6fe67b3b483dc2fce742c1964a8`.
- Receipt SHA-256: `de2265f41d8d0a54ab2db52452dc0e51e501e30d929eef907ff0a90eeb7f5842`.
- Code: 1,908 bytes in the unchanged 8-KiB reservation. Both existing dispatch
  entries and their 68-byte prefix remain; a `v1` variant supports native held
  main calls. The 208-byte table block starts at `804A8430` inside the module.
- Four held-table address relocations are removed, retaining original callbacks,
  owner dimensions, and other relocations. Current total removals are 60.
  The existing 17,584-byte player-relocation resource is updated in place inside
  the blob; complete blob checksums include those changes before emission.
- No allocations move or grow. Blob remains 3,517,632 bytes, with 611,136 free.
  Startup remains 952 bytes. Sound programs, complete models/motions, 104 choices,
  and saved format 2 are unchanged. Same-profile ABI-102/103 compatibility is
  expected both ways and the actual codec passes; ordinary save/restart and
  hardware are not newly tested. V3 saves are not for V2. Both patchers remain V2.

Four focused checks pass in 5.822 seconds, including host sanitizers, both model
banks, rejected missing/invalid resources, full source/callback tables,
relocated owner references at two bases, resource retention, checksum accounting,
and reconstructible patch. The existing shared native scenario takes the new
held-category branch instead of repeating the unchanged sound/control tests.
Twelve current optional-composition checks pass in 9.120 seconds, including exact
no-import V2, all-import ABI 103, sparse profiles, dependencies, and the real codec.
The native check's single attempt passes 58 records and 40 assertions. Results at
`build/smoke-v3-held-item-dispatch-01/results.json` have SHA-256
`86e2281bedc2fa7694f181f5f38de9a0cde5e9e3a1334e30212c2e261059fa54`;
probe SHA-256 is `315ab11ef745f66b99a42c8605a51104a4114c61151c73f731d3a9c0b7eac2d5`.
Verified: original/imported main dispatch, null/out-of-range results, complete
tables, actual static draw commands in both banks, invalid-resource rejection,
guards, unchanged profile, and checkpoint restoration. FlashRAM remains all
`FF`, SHA-256 `b5a41c3758763bbec72769fab4a2533bf2db0b6312d93d25a695f9e4b9e02260`.
No audio is played. Full scene rendering and ordinary equipped fan use remain
unverified; the direct draw callback is not presented as either result.

Continue outside-owner action checks, action 109 registration, four ordinary
polling sites, profile-aware equipment selection, parent inventory/acquisition,
catalogue identity, and persistence. Reuse current category records and passing
evidence; do not add per-item installers or replay the unchanged sound batch.

## Shared sound programs and per-frame actions

The existing player-action refresh adapter installs the fan's complete per-frame
callback and `tools/v3_sound_programs.py`, a reusable batch converter for
explicit-bank, single-layer notes with custom envelopes and optional special-mode
pitch sweeps. The source function supplies sound ID `0167`; no per-item sound
script, copied instrument, or extra sample is needed. The converter checks the
complete native instrument identity, interpreter handlers, priority, pointers,
and permanent-resource budget. Occupied slots and unsupported forms reject.

The player callback retains the donor's movement/input/animation/sound/collision/
item/transition order. Sound occurs at frame `1.5` only if animation advances.
The native WAIT initializer advances the same 33-frame motion at speed `1.0`,
versus donor `0.5`; the fan's retained motion and input threshold use native
speed `1.0`. Event coordinates remain unchanged. Common native braking uses
`0.75`, not the donor's per-update `0.32625001`. The native run verifies one-step
frame and morph advancement through the actual live player's skeleton.

### Build and memory

- ABI 102: `build/v3-player-frame-sound-01/animal-forest-v3-asset-loader.z64`.
- ROM SHA-256: `92bffc4eced4cf170922db9080510d347212d65255538f8c8d828cceaf779cc7`.
- UPS SHA-256: `79579190df6845ba6efb7007ed187fec2509dc97e1f6551ebe9978c0a1c55b46`.
- Receipt SHA-256: `fb8a8256883c9640c999290cde48465e6c5a7dad8adf39bc43ba22dab0660a31`.
- Shared action code: 1,772 bytes, maximum direct stack 64 bytes, original
  68-byte dispatch prefix retained, unchanged 24,576-byte module allocation.
- The complete 20,208-byte sound sequence is appended in ROM; all prior sound
  programs retain their offsets. Only the previously empty dispatch entry and
  sequence header change. The sequence adds 32 loaded bytes. The full permanent
  resource inventory requires 109,344 of 109,568 bytes, leaving 224 bytes spare.
- Blob: 3,517,632 bytes, with 611,136 free before English choice resources.
  The three terminal catalogue/shop owners move without content changes. Models,
  motions, player owner/relocations, callback tables, and profiles remain intact.
- Startup: 952 of 992 bytes. The 104 choices and saved format 2 are unchanged.
  Same-profile ABI-101/102 saves are expected to work in both directions; the
  real codec passes, but this is not another ordinary save/restart or hardware
  playthrough. V3 saves are not for V2. Both served patchers remain V2.

### Verification

Six focused checks pass in 5.625 seconds: sanitizer-covered controller/setup/
transition/per-frame order, once-per-crossing sound, stopped frames, native
timing, complete sound conversion, malformed/occupied-slot rejection, resource
retention, CRCs, and reconstructible patch. Twelve current composition checks
pass in 8.411 seconds, including exact no-import V2 and all-import ABI 102.

The single silent native attempt passes all 119 records with 70 passing
assertions. `build/smoke-v3-player-frame-sound-01/results.json` has SHA-256
`7d16d4d8a260bbe68735811d6d722a3640803a28ade742af4227b234f8f9d209`.
The shared probe SHA-256 is
`5ab3dbd8d5c0f8eb721d5ea2228f7febaa3e6bf93903be1797eb6a430a083cf1`.
It verifies actual sequence loading and dispatch, priority 60, fifteen completed
sample-DMA observations, native heap bounds, real-player animation/collision
callback, private and live bank restoration, saved-profile retention, guards,
and checkpoint restoration. The title-demo movement is `(-0.3934426, 0)` and
correctly produces a walk request. Native idle acceptance remains unexecuted;
the host check covers it. FlashRAM remains 131,072 `FF` bytes, SHA-256
`b5a41c3758763bbec72769fab4a2533bf2db0b6312d93d25a695f9e4b9e02260`.

This is component execution, not an ordinary equipped fan or a hardware result.
No audio reaches speakers/headphones; PCM/listening quality is unverified. The
callback tables and input-poll hooks remain off. Continue the shared held-item
main/draw tables, source fan draw and net reset, four ordinary polling sites,
selected inventory/acquisition/profile handling, and outside-owner action audit.
Do not repeat unchanged passing checks or introduce per-item installers.

## Shared fan control flow

The existing `--refresh-runtime --player-actions` mode installs the donor fan's
press/hold controller, priority-checked request, split-body setup, repeat setup,
and end-of-swing transitions. The implementation resolves the actual loaded
native owner on every call. Fifteen complete donor functions and nineteen
native APIs bind the adapter. All eight fans share these functions. No extra
item script, action table, actor allocation, animation bank, or saved field is
added. Callback tables and ordinary input-poll hooks remain unchanged and off
for imported actions. This is not a selectable/playable fan handoff.

The native standard initializer is `808B4A44`, with ten arguments. The reverse
initializer at `808B4B6C` has a different signature. The source fan uses upper
animation 270, native lower WAIT1 zero, half-frame speed, repeat mode, and
explicit mask four. Its start/repeat lower frames and morph values differ.
The native idle request has four arguments, unlike the donor's five; the
extra donor delay is stored but not consumed by its idle initializer. Flag two
is unused by both. The adapter preserves the effective behaviour without
passing the extra float into the native flags field.

### Build and allocation

- ABI 101: `build/v3-player-fan-controls-01/animal-forest-v3-asset-loader.z64`.
- ROM SHA-256:
  `1763e613b3f080a4cacc26cbfa9d244a742b6e34cff077bbc9e142ac4aeeaa38`.
- UPS SHA-256:
  `06fa46e6bba6721d01958b62f9d63386fd64f38b9cb5a3def9bbbf3bb07857ea`.
- Receipt SHA-256:
  `faa4db40813490033dd2ba7d538c9bcedd9b8eb4639689c8dc3fa25e7dde1abb`.
- Shared action code: 1,436 bytes at `804A5000`, inside its existing 8-KiB span.
  The original 68-byte dispatch prefix and both public entry addresses remain.
- Module: unchanged 24,576-byte allocation at `804A3000`, VROM `0253BD00`.
  Shared refresh updates code in place instead of allocating another copy.
- Blob: unchanged 3,497,424 bytes, retaining 631,344 bytes of free storage.
  All models, motions, tables, owners, relocations, and resource locations remain.
- Startup: 952 of 992 bytes, with the updated complete-module checksum.
  The 104 choices and saved format 2 remain unchanged. Same-profile ABI-100/101
  compatibility is expected in both directions and the profile codec passes;
  this is not a fresh ordinary save/restart or hardware test. Do not use V3 saves
  with V2. Both served V2 patchers stay unchanged.

### Focused verification and classified stopping points

Two current host/cartridge tests pass in 5.622 seconds. Address/undefined-behaviour
sanitizers cover all fan kinds, rejected kinds, title/ordinary press and hold,
permission and priority rejection, unchanged actor bytes on rejection,
walk/run/dash speed thresholds, umbrella/fan polling order, both setups, bee
timing, repeat requests, and walk/idle arbitration. The host priority model
retains the native pending-request and already-settled checks. Cartridge checks
bind complete code, source/native functions, deliberate native API corruption
rejection, unchanged tables/artwork/owners/profiles, unchanged allocations,
checksums, and complete patch reconstruction. Twelve current optional-composition
tests pass in 7.783 seconds, including exact no-import V2, exact all-import ABI
101, dependencies, sparse selection, and the actual saved-profile codec.

The silent native probe extends the existing shared player-motion scenario,
using an isolated full-size actor, fake game context, and two native-sized
animation banks. The first attempt stops at the debugger's low-RAM call guard,
before invoking a new function. The single setup retry uses the established
eight-byte low-RAM jump bridge to the cartridge-loaded Expansion Pak code.
No replacement gameplay function is uploaded.

`build/smoke-v3-player-fan-controls-02/results.json` contains 50 records and 22
passing assertions before the final idle expectation fails. Its SHA-256 is
`ec20b8b90916c5a5ef7f3270e209d8a7024a7102d7c841bc405457a4c8dbcecf`.
Verified components include complete module/code relocation, hidden-item
controller rejection, actual priority/request writes, equal-priority rejection,
full setup, eye pattern, frame control/morph, complete swing DMA, explicit mask,
restored segment-six binding, repeat lower-frame retention, zero repeat morph,
and bee timing. The failing field's observed SHA-256 is
`5be0a01e5257e4c08ac57e3d288893e9cc6f8d6fc2d9aff9eab81c0fbf00c384`,
which independently decodes to `(requested action=8, priority=1, pending=1)`.
That is the valid walk request. The original native priority-settling function
does not clear an existing pending request, so an equal-priority idle request
cannot replace walking. The fixture incorrectly assumed the title-demo stick
was idle; this is an expectation failure, not evidence of a game defect.

The corrected fixture reads actual title/ordinary controller movement and checks
the resulting walk or idle branch. It is **not rerun** in this batch. Final
guard checks, checkpoint restoration, native idle acceptance, and a positively
equipped fan controller remain unverified here. Retain the passing prefix and
include those checks with the next actual callback integration, not a third
setup attempt. The isolated 131,072-byte FlashRAM stays all `FF`, SHA-256
`b5a41c3758763bbec72769fab4a2533bf2db0b6312d93d25a695f9e4b9e02260`.
No user save or hardware is touched, and audio is disabled.

### Next shared dependencies

The donor's complete fan sound program is 32 bytes at main-sequence `0812`.
Its bank-154 instrument 12 matches native bank-140 instrument 12, including
all tuning/envelope/loop/predictor data and the 3,726-byte sample. Both priority
entries are 60. Numeric ID `0167` is still outside the original 97-entry native
group and is not a playable registered sound. Extend shared sequence-program
binding with the complete custom envelope and playback operands; do not append
another copy of the instrument/sample. The [specification](../../specs/V3_HANDHELD_ITEMS.md)
records exact identities. Complete the per-frame action/draw/net reset, the four
ordinary polling sites, native selected equipment, acquisition, and profiles.
Keep all unfinished callback entries disabled until their dependencies exist.

## Shared player action tables

The existing importer installs `--refresh-runtime --player-actions` through one
source-derived adapter. All 22 metadata tables and five callback tables in the
native player owner have complete 121-entry storage. Original indices `0..104`
retain every original value and callback. Extra indices `105..120` retain the
donor's actual metadata, including fan action 109, but their callbacks stay null
until implemented. This is action-table/dispatch integration, not working fan
behaviour, additional item selections, or an import handoff.

The source reader indexes actual `.rodata` relocations. The donor's callback
tables contain zero pointer placeholders before relocation; treating those
bytes as null callbacks would lose real dependencies. The fan needs the donor
net-angle reset callback as well as its setup/main routines. Its submenu and
settle callbacks really are null. The complete function/table/relocation
receipts are retained for the next implementation, without per-item definitions.

Twenty-eight table address pairs move to the extended immutable tables;
exactly 56 obsolete HI/LO relocations are removed. The unrelated spatial-search
loop's reference at `808B99D0/808B99D8` remains: it uses the old address as the
exclusive end of the preceding eight-float array. The 27 action limits increase
only alongside complete arrays. Five indirect calls use two shared register
variants which resolve native linked callbacks against the current loaded
player constructor. Imported resident pointers pass through unchanged. The
original table objects, owner size, other relocations, arguments, and stack
contracts remain intact.

Output: `build/v3-player-action-tables-03/`, ABI 100.

- ROM SHA-256:
  `1cffa6906ac85234ee16e1e81b7b18f20fc92cc118ce477a002d5511c8648273`.
- UPS SHA-256:
  `ca38866d3dca1c10d3612d474312a250a042c6242e2587ca2e5447a0523a951c`.
- Receipt SHA-256:
  `f0b4b6d9b21a720f4004be590cd68170facdca3b6cc8e080288764904b8c098c`.
- Shared equipment/action module: 24,576 bytes at `804A3000`, VROM `0253BD00`.
  The original 8,192-byte equipment region remains unchanged; additional code
  and table space uses 16 KiB before the existing furniture pool.
- Dispatch code: 68 bytes at `804A5000`; tables: 5,164 bytes at `804A7000`.
  Both the old internal guard and new end guard remain.
- Startup: 952 of 992 bytes; one checksum-bound transfer and cache flush cover
  the complete module. No actor, animation buffer, ordinary heap, or save grows.
- Import blob: 3,497,424 bytes; 631,344 bytes remain before English choices.

### Verification and remaining work

Risk: stale relocated callback pointers, incomplete tables or relocation
removal, disturbed unrelated table boundaries, and incomplete startup cache
coverage. Six focused cartridge/startup checks and nine shared handheld/source/
art checks pass. They cover both native relocation bases, all original and
extended table contents, pending callback rejection, complete resource retention,
source/bound mutation rejection, patch reconstruction, module bounds, and the
real startup C under address/undefined-behaviour sanitizers. Twelve prospective
current-build composition checks pass, including exact no-import V2, exact
all-import output, sparse profiles, dependencies, and the actual save codec.

The corrected silent native run at
`build/smoke-v3-player-action-tables-02/results.json` passes 173 records and 143
assertions. Result SHA-256:
`29f8c7994066fa88190b06871d9f1ad2e8c455a0f341dd4cf46d72700cd1213c`.
It verifies the complete module and actual game-loaded player code/relocations;
reads representative native/new/invalid action metadata; rejects five unfinished
or invalid requests without modifying their scratch actor; compares an original
net callback with the same callback reached through shared dispatch; and tests
both dispatch-register variants against native and resident targets. The only
uploaded code consists of 16-byte call bridges in isolated heap scratch, not
replacement callbacks. Existing kind readers, representative transfers, all
five masks, profile retention, guards, checkpoint restoration, and graceful
shutdown also pass. The isolated 131,072-byte FlashRAM remains erased. Audio is
disabled; no user saves are touched. The probe source SHA-256 is
`1eb87d3efece12d9f19ded64fbcb7c143f70570489d6507681e024704d5d82e7`.

The first native attempt expected zero for the priority getter's invalid index;
the original native function returns `-1`. Its instructions and observed return
establish a fixture error. The single corrected retry passes without a ROM
change. The initial build's allocation guard also correctly stopped an attempted
in-place update of a compressed relocation resource. The shared importer now
stores changed compressed owners in checked uncompressed storage, keeping their
logical DMA identity and dimensions. Build `03` corrects the existing motion
receipt's relocation-hash field; its ROM/UPS are identical to the tested build
`02`. The six focused current-cartridge/startup checks cover that final receipt;
unchanged native evidence is retained instead of replayed.

The 104 choices and saved format 2 remain unchanged. Same-profile compatibility
with ABI 99 is expected in both directions; ordinary save/restart and hardware
testing are not claimed by this batch. V3 saves remain unsuitable for V2. Both
served patchers remain untouched. No player-facing text is added, so the single
text provenance catalogue needs no new entry.

Continue actual fan controller/request/setup/main/drawing and source-timed sound
using these shared tables. Audit core-library action checks outside this owner,
then connect kind selection, complete inventory/readers/acquisition, and selected
profiles. Fan swing uses animation 270 and explicit mask four. Other toy rigs,
remaining item/villager gameplay, browser validation, and persistence remain in
the full V3 queue; this infrastructure does not replace that scope.

## Shared equipment kind readers

The existing importer's `--refresh-runtime --equipment-kinds` mode connects all
six kind-indexed native readers through one complete source-derived table.
Seventy-nine donor kinds use stable indices `36 + source kind`; all original
kind meanings, tables, and table relocations remain. Sixteen-bit fields preserve
the fan holding animation index 269 without clipping it to a byte. There is no
per-item definition, installer, or dedicated fan test scenario.

Complete donor functions/tables supply holding pose, item routine, model,
equipment animation, tumble, and get-up. The latter two are actual fall/recovery
consumers, not take-out/put-away readers. Four complete source motions 25–28 add
5,744 bytes, retaining their 17-/32-frame timing and all key data. They fit the
original 3,848-byte animation banks. The original eight imported player motions,
fourteen held models, and sixteen equipment motions remain unchanged.

Output: `build/v3-equipment-kinds-runtime-01/`, ABI 99.

- ROM SHA-256:
  `c4c5e56687edeaa2ae0ce6dfd1bc9471f9a8a22c27f4768f85f522c1fbc12749`.
- UPS SHA-256:
  `b94c92dc4eae3a33ddba7ff952f555730b343e618d9e546fa4fad95e162bfcfc`.
- Build receipt SHA-256:
  `bbf6828e4f29a7ce26436d0326893f2c759d8b2f665dc93126399a2b42e10ac9`.
- Shared module: 1,472 code bytes; existing 8,192-byte allocation and VROM
  `02537DC0` remain. Startup remains 952 of 992 bytes.
- Import blob: 3,455,264 bytes; 673,504 bytes remain before English choices.

The new `AFKD` header/records occupy module offsets `B00..EC3`; code is bounded
below `B00` and the native part-copy bridge remains at `FE0`. Getters at
`808BD668`, `808BD690`, `808BD6B8`, `808BD6E0`, `808C2D4C`, and `808C32CC`
retain native table HI/LO relocations at offsets 12/24. Imported values delegate
to one shared reader with an explicit field index. Invalid indices preserve
the distinct original defaults. Existing motion/resource hooks are rebound to
the compiled helpers without changing their resources or semantics.

All nineteen static item/state resource pairs fit the combined 4,376-byte
equipment-bank limit; the largest is 4,032 bytes. Unsupported skeleton slots
remain missing, not approved substitutes. The actual item selector remains
unchanged and therefore still rejects the extra inventory identities. Source
item-routine values 21–23 are stored as dependencies, not installed dispatchers.

### Verification and next work

Risk: incorrect kind offsets, narrowed animation indices, changed native table
relocation, or oversized combined resources. The existing player-motion suite
now covers source-bound records, mutation rejection, every table field, all four
new complete animations, retained resources, exact cartridge ownership, two
relocation bases, source/ROM checksums, and reconstructible patches. The real C
readers pass address/undefined-behaviour sanitizers, including indices above
255, negative/missing resources, both kind bounds, and malformed headers.
All six checks pass on the first run.

The twelve current-build optional-composition checks pass, including exact V2
for no imports, exact ABI 99 for all imports, sparse selections, dependency
rejection, and save-profile codec. The first invocation stops before executing
tests because the temporary prospective-build override omitted `REPORT_SHA`.
The corrected invocation supplies all four existing pins and passes; no ROM or
composer change is needed. This is the single corrected setup retry.

The first native run, `build/smoke-v3-equipment-kinds-01/results.json`, passes
126 records and 106 assertions, SHA-256
`afea974561fd0498d7f7d764f754c8e54522646bab1953371a846965cbe4442e`.
The shared player-motion probe reuses the actual loaded owner, verifies its
complete relocated code, and calls all six getters for original tools, three
extended categories, and invalid bounds. Four representative animation
transfers cover tumble/get-up and two original indices, with full data and
untouched-tail comparisons. All five masks, equipment fallbacks, guards,
saved-profile retention, checkpoint restore, and graceful shutdown pass.
Isolated FlashRAM remains erased; there is no audio or user-save write.

The 104 choices and saved format 2 remain unchanged. Same-profile compatibility
with ABI 98 is expected in both directions; this batch does not claim another
ordinary save/restart or hardware playthrough. V3 saves remain unsuitable for
V2. Both served patchers stay unchanged.

Continue actual equipment selection, category/scene permissions, item drawing,
and the fan controller/request/action. Audit native action dispatch and all
action-indexed permission tables before adding a fan action; do not repurpose
an existing action or widen bounds over short tables. Preserve source swing
animation 140/native 270, explicit mask four, and frame-timed sound.
`Player_actor_sound_uchiwa` is donor `.text:16FA00`, calling
`Player_actor_set_sound_common2` with `NA_SE_UCHIWA`; the actual native sound
resource still needs identification/conversion, not an unrelated substitution.
Fan inventory, names/prices, acquisition, catalogue/collection, selected profiles,
ordinary take-out/put-away, and persistence remain. Balloon joint-work capacity,
net/rod graphics matrices, and pinwheel rig packing remain separate shared
category dependencies. No new handheld item is selectable or claimed playable.

## Native player motion and part masks

The existing importer's `--refresh-runtime --player-motion` mode extends the
shared held module with eight complete player motions: six equipment holding
poses, fan idle, and fan swing. Each is independently packed for the native
player-animation DMA. Their 2,256 bytes fit the existing 3,848-byte banks.
Indices are `130 + donor animation index`; all 130 original indices and tables
remain intact. No per-item installer or alternate simplified motion is used.

The source-derived default-part table and complete mask-copy function bind the
split-body conventions. All four original masks match their donor equivalents.
The fifth mask is copied from the donor, preserving all 27 entries. The fan's
action initializer explicitly selects mask four; its default animation-to-part
table returns three. The implementation retains both facts rather than
rewriting the default table to impersonate the action.

Output: `build/v3-player-motion-runtime-01/`, ABI 98, pinned by
`config/v3-import-build.json`.

- ROM SHA-256:
  `88106989dc341f554ba0979079539c96b05bba60550be2999994bf7b1eb0739c`.
- UPS SHA-256:
  `01a85334ad6c9ca80875065857e2bcf29cd9630d9a780492d75ff327455ddecf`.
- Build receipt SHA-256:
  `13050814fc10d39b25cd124df74c07f39b3bda66f4cc2bc8ab91b9ebcf9aaaae`.
- Shared module code: 1,304 bytes; module allocation remains 8,192 bytes at
  `804A3000`, VROM `02537DC0`. Startup remains 952 bytes.
- Import blob: 3,449,520 bytes; 679,248 bytes remain before English choices.

Core size/origin/VROM getters and mask copying support the additions. The
native player owner's pointer and default-part getters retain every original
HI/LO relocation and delegate only non-native indices. Actual DMA, segment
bias, native mask copying, player actor size, and bank allocations remain
unchanged. The guarded native mask-copy prologue bridge occupies module offset
`FE0`; the sparse `AFPM` table and extra mask use previously empty data space.
Existing held models/motions retain their exact resource locations and data.
Only the three unchanged terminal catalogue/shop owners move to make ROM space.

### Verification and remaining work

Risk: the new readers must preserve relocated native tables, animation banks,
mask lengths, and original equipment. The bounded checks cover actual C under
sanitizers, full source objects, two host relocation bases, cartridge ownership,
checksums/patch reconstruction, current optional composition, and one corrected
native category run. Player actions and ordinary graphical animation playback
are not inferred from these resource checks.

Seventeen distinct focused tests pass: five current motion/owner checks and
twelve existing optional-composition checks bound to ABI 98. The initial host
run passes three and exposes two fixture issues: comparing JSON-normalised
relocation dictionaries against Python tuples/integer keys, and directly
indexing an optional absent receipt field. Both corrected fixture checks pass
on their focused retry; production data/code are unchanged by that correction.
Empty/full/subset composition and saved-profile requirements pass.

The first native attempt verifies the resident module, then fails its test-only
221,184-byte allocation for a second player overlay. It does not enter an
animation test. The corrected probe derives the real loaded owner from
`Player_actor_ct_func`, verifies all 175,872 code bytes against expected
relocation, and allocates only 4,352 bytes for guarded animation scratch. Getter
calls use independently checked, function-sized code proofs. The live owner is
`80394490`, constructor `803BEE88`; the probe never overwrites that owner.

`build/smoke-v3-player-motion-02/results.json` passes 102 records with 79
assertions, SHA-256
`10c13dbdfb0f028b28f9695bb655f8b4491adb83785e58268f72e6cca3e98ba5`.
Seven representative transfers cover source-derived constant/animated categories
and original animation indices. All five masks, original equipment fallbacks,
invalid indices, untouched transfer tails, guards, and saved-profile retention
pass. Checkpoint restoration, fault status, and graceful shutdown pass; isolated
FlashRAM remains blank. No user save is used and no hardware test is claimed.

The 104 choices and saved format 2 remain unchanged. Same-profile ABI-97
compatibility is expected in both directions; no additional ordinary save/reload
cycle is claimed. V3 saves remain unsuitable for V2 and profiles must include
saved imported identities. Neither served patcher changes.

Next: native kind selection and dependent readers, real fan controller/request/
action flow and its explicit part mask/timing/sound, take-out/put-away/drawing,
inventory/acquisition, and optional profile selection. Net/rod joint matrices,
balloon textures and joint-work capacity, pinwheel rig packing, and combined
model/animation bank bounds remain actual dependencies. Imported animation
indices remain outside original footstep/event tables; new actions need their
own source timing, not enlarged bounds over short native tables. No new item
becomes playable or selectable solely from this batch.

## Native held-resource loading

`--refresh-runtime --equipment-art` installs one source-derived category through
the existing importer: fourteen complete static held models and sixteen complete
equipment animations. It reuses the prepared graphics, packs each animation for
independent native DMA, and reserves stable indices `17 + source index` in a
fifty-slot table. Unsupported skeleton slots remain empty. The eight prepared
player animations are not installed by this batch. No item choice or action is
enabled merely because its resource can load.

Output: `build/v3-equipment-resources-runtime-03/`, ABI 97, pinned by
`config/v3-import-build.json`.

- ROM SHA-256:
  `2ae396a32a1fbd86411c2dec5420fb45c702fdfb048828b8ddabce84185a4e3a`.
- UPS SHA-256:
  `1e175606802ef57eb4233f8a4e3f90faa5edc6f189acac9d24b5b5ffb778e743`.
- Build receipt SHA-256:
  `90068e8fa585961789f63638827f624039c837ebfe78e9538fd9b3d06dc74580`.
- Resources: 31,584 bytes; shared resident module: 8,192 bytes, 644 code bytes.
- Module RAM: `804A3000..804A4FFF`; VROM: `02537DC0`.
- Startup: 952 of 992 reserved bytes. Import blob: 3,447,264 bytes;
  681,504 bytes remain before the English-choice resource.

Five shared native getters provide pointers, types, sizes, segment origins, and
VROMs. Original indices, lookup tables, DMA, and segment-bias routines retain
their semantics. The original player bank switch and menu-close reload both
call those DMA routines; they are not separately reimplemented. The importer
moves only the three unchanged terminal catalogue/shop owners to append these
resources. All existing graphics, owner data, catalogue content, profiles, and
save code remain unchanged.

Initial linking exposed a 52-byte startup overflow. Sharing CRC-checked transfer
code and consolidating package instruction-cache coverage resolves it without
expanding the reservation or consuming configuration/scratch space. The complete
equipment module, including its header/footer, is bound by a compiled CRC.
No failed build is promoted. Intermediate local output directories remain intact.

### Verification and limits

Risk: changed startup and native equipment readers must not corrupt the resident
packages, original tools, or existing imports. Stop after shared reader/startup
sanitizers, current cartridge ownership/source checks, optional composition,
and one bounded representative native DMA pass. Do not add individual item tests
or infer playable actions from successful transfers.

All eighteen focused tests pass: six in `test_v3_equipment_runtime` and twelve
existing optional-composition tests directed at the new cartridge. Coverage
includes native-index fallback, malformed/empty records, all four startup
transfers and failure paths, complete source artwork/motion comparison, retained
unrelated owners, future terminal-tail reuse, code bounds, CRCs, N64 checksums,
UPS reconstruction, and optional/profile handling. Empty selection reproduces
the exact stable V2 cartridge; full selection reproduces ABI 97.

The first silent native run, `build/smoke-v3-equipment-resources-01/`, completes
115 records with 96 assertions. `results.json` SHA-256:
`0aa9746def1cbf54783a9b83be923983a9f60c3b71a4541e1ef5cd0f8510365f`.
The existing shared batch probe selects the largest object in each of five
imported resource categories and four original resources. All nine complete
transfers, untouched tails, pointers/types/origins, segment-base calculation,
invalid indices, allocation guards, resident guards, and unchanged saved profile
pass. The checkpoint restores, CPU fault status remains clear, shutdown is
clean, and isolated FlashRAM retains its blank hash. No user save is opened.

The 104 choices and saved format 2 remain unchanged. Same-profile compatibility
with ABI 96 is expected in both directions; no new ordinary save/restart or
hardware playthrough is claimed. V3 saves remain unsuitable for V2, and profiles
must include any imported identities already saved. Both served patchers remain
unchanged and this build is not a new playtest/release handoff.

Next: actual native kind selection and indexed readers, player holding/action
animations, fan waving with source timing/part masks, inventory/acquisition,
and selected-only profiles. Native player arrays contain seven work vectors,
while the donor has eight; balloon rigs need explicit buffer work. The bank
switch places animation after model, so paired sizes require separate validation.
Ordinary take-out/put-away, menu-close reload, model drawing, and player actions
remain untested. Resource loading alone is not a completed handheld import.

## Held-motion dependencies

`tools/v3_keyframes.py` implements shared complete rotational-skeleton and
keyframe parsing/packing. Source-derived equipment and player selectors feed it;
there is no maintained per-item animation list. All twenty held skeletons retain
their actual joint hierarchy, translations, streams, and model roots. The
sixteen equipment animations and eight equipment-related player animations
produce one 7,760-byte native-format object containing 84 complete arrays and
24 relocated headers. The fan swing comes from the complete donor setup
function's actual initializer argument, not a guessed animation name.

Output: `build/v3-held-motion-prepared-01/`.

- `held-motion.n64obj.bin` SHA-256:
  `e17c8d6251ee37845c3c693b2b226e2e911aba5043b6e493270ee8e70289663c`.
- `art.json` SHA-256:
  `09bac790415a75834fbfad6f58413e43a70c573e3e9c5beb96149928e0eae9d8`.

The same `v3_furniture_pipeline.py convert --representation handheld
--assets-only` command accepts `--category held-motion`. This is a complete
dependency bundle, not a selected gameplay profile. Individual gameplay
selection remains native/profile integration work. No alternate installer,
prepared furniture substitution, or public output is introduced.

Fourteen distinct focused checks pass: eight keyframe/source/packing checks and
six existing held-source checks. Complete source arrays and header pointers are
compared independently; root translation and every joint rotation consume
exactly the expected constants and keyframe tracks. Topology, source/player
bindings, preserved null pointers, malformed flags/counts/frames, stale
descriptions, and changed source selectors/setup reject as intended. The
initial run passes thirteen and exposes a stale cached relocation-address list
in one mutation fixture. Updating both fixture indexes gives a passing focused
retry; production source parsing is unchanged by that fixture correction.

The initial conversion identifies constant-only player poses with null key/count
pointers. Shared format handling preserves those nulls and validates their full
constant arrays; it does not create fake animation tracks. The prepared bundle
contains six such poses plus the fan's seventeen-frame idle and nine-frame swing.
No movement is resampled or shortened.

Native rig/model ownership and buffers, player actions, part masks, sound,
inventory readers, acquisition, and profile integration remain unfinished.
Net/rod graphics require joint-matrix commands; balloon graphics require wider
texture support. Pinwheel graphics pass existing preflight but have no complete
native rig/model installation. ABI 96, its 104 choices, saves, and both served
V2 patchers remain unchanged. No emulator or hardware result is claimed.

## Actual held-model batch

The shared converter prepares fourteen actual handheld models for nineteen
donor item/state IDs: eight fans, the ordinary/golden shovel, and four axe
appearances. Complete source discovery follows item-to-kind, kind-to-shape/
animation, resource-pointer, and resource-type functions and their full tables.
It classifies 79 equipment records: nineteen static, twenty animated, and forty
using separate umbrella ownership. Thirteen rejected item IDs remain rejected.
The full donor inventory attaches these records to its existing identities.

`prepare_models` and `compile_models` are shared with the furniture path;
no second graphics converter or per-item integration script is introduced.
The batch retains all 25,888 artwork bytes, 334 vertices, and 244 triangles.
It is prepared-only: native selection/actions/animation, model ownership,
readers, acquisition, catalogue/collection, and save-profile integration remain.
The distinct prepared format is rejected by the furniture installer. Static
models are not substituted for skeletons, and ordinary tools are not new choices.

Generated outputs:

- `build/v3-handheld-static-prepared-02/art.json`, SHA-256
  `a7f97f5ef8ecf6c8c4df3b1961a1f38cf5974b5696e8e0c4904897a6cfd724e6`.
- `build/v3-handheld-static-prepared-02/inventory.json`, SHA-256
  `8af47296a224e1d524108e71b16c8526be4d2adc6811b468a76587a9d3434ab4`.
- `build/v3-handheld-source-02/donor-catalogue.json`, SHA-256
  `956a4d7305b97ab8489061613234c2a44f0db8f21cb49e6616d68f7f91d4942f`.

Eleven distinct focused checks pass: nine in `test_v3_handheld_items`, plus
the existing static-linker and complete-current-furniture-artwork checks.
Coverage includes full source functions/tables/relocations, correct wear-state
shapes, single-inventory identity/name binding, unsupported-selection and
installation rejection, and every model's complete texels, vertices, triangles,
material state, bounds, and native commands. Recompiling the two current
constant-model-sequence assets through the factored compiler reproduces their
complete objects and receipts. This is not an old-cartridge emulator replay.

The initial seven-test run passes six checks and finds an incorrect custom-
umbrella range in one new test: the actual donor accepts `2224..222B`, not
through `2230`. Production discovery already has the correct bounds. The
corrected focused check and two existing checks pass; two further CLI/type
rejection checks also pass. No inconclusive or failed game result is hidden.

The original and ABI-96 native equipment selector agree over all 396 bytes at
`808BD3F8..808BD583`, SHA-256
`3e1e9584685cef3dcb81e6fe99ef412ddc49fd4a8df74901f55b1742f234258b`.
It only accepts ordinary IDs `2200..2223`; new held graphics therefore require
actual player integration. The donor fan draw/action and player-animation
entries are identified in [the equipment spec](../../specs/V3_HANDHELD_ITEMS.md).
The current cartridge/ABI, 104 installed choices, saved format, and both served
patchers remain unchanged. No new ordinary gameplay or hardware claim is made.

## Parent display contexts

The donor's conversion flag has different values in ordinary room placement
and collection recording/checking. This changes the integration plan for forty
of the forty-eight extra display representations: tools, golden tools, fans,
pinwheels, and diaries keep their inventory IDs when dropped indoors. Their
furniture models are catalogue/collection representations. The eight balloons
use furniture IDs in both contexts. The earlier generic placement terminology
must not be interpreted as an unconditional room conversion.

`tools/v3_room_aliases.py` now verifies complete `mTG_room_put_proc`,
`mPr_SetItemCollectBit`, and `mSP_CollectCheck` implementations and their complete
relocation dependencies. It checks each conversion branch and flag-setting
instruction independently, and finds exactly four direct callers in the donor
executable: two room drops with flag one and two collection calls with flag zero.
Unknown consumers and changed code/relocations fail before item classification.
The call scan is cached against immutable complete source bytes to avoid repeating
an executable scan for each candidate; consumer verification remains uncached.

Format `AFV3-DONOR-ROOM-ALIASES-2` renames ambiguous `placement_inputs` to
`conversion_inputs` and generates actual `context_outputs` for every accepted
input. The seven worn-axe states map to one collection display, but each keeps
its wear-state ID on ordinary and bulk room drops. Inverse display conversion
returning an ordinary axe does not mean ordinary dropping repairs an axe.
The full donor inventory, furniture scan, and browser review records inherit
the correct context and pending reason from this one discovery implementation.

Eight focused tests pass, covering all 48 aliases/55 accepted inputs, context
outputs, ordinary/bulk call modes, complete code and relocation mutation,
unreviewed direct callers, worn-state retention, all 2,333 donor inventory
identities, and rejection of standalone furniture installation. Existing current
converted furniture still passes source/asset verification. The first run takes
69.483 seconds; after adding the immutable call-scan cache, the final-source run
passes in 26.649 seconds. These are host/source checks, not emulator gameplay.

Generated outputs:

- `build/v3-alias-contexts-01/inventory.json`, SHA-256
  `3593bdd48e5411d24e5bb0a712cced4517dd24c6eae0a7e56f2b69d3c4fc7ecf`.
- `build/v3-alias-contexts-01/donor-catalogue.json`, SHA-256
  `63f9d9f1e9d9b4b4fa1d1e5b8eff62039289cab3817b9278b4293ed1bcba3611`.

The scan retains 76 converter-supported and 166 review entries, with no new
fully eligible furniture. ABI 96, its pinned cartridge, 104 installed choices,
saved format 2, and both served V2 patchers remain unchanged. No emulator replay
is required for this source-discovery change. Next: actual parent inventory/
player actions/acquisition and context-correct catalogue/collection integration,
reusing the complete prepared artwork. Do not add a global tool-to-furniture
room conversion, duplicate original tools, or claim prepared graphics as usable
parent items.

## Shared native display aliases

ABI 96 replaces the conversion/readers/garment-roster lists with generated
relationships from the actual installed parent and display records. The same
metadata serves placement, pickup, full names, prices, ownership, footprints,
and garment resources. All three existing garments retain their actual profile
owners, selected dependencies, and native mannequin drawing. No item identity,
artwork, acquisition route, logical option, or saved format changes.

The existing furniture installer supplies `--refresh-runtime`, which updates
shared readers without reconverting artwork or installing another item batch.
Normal furniture installation uses the same adapter and reuses unchanged code.
The forward index consumes 240 verified unused bytes inside the existing
package; canonical display records use the last four bytes of their existing
sparse slots. Permanent RAM reservations and the entire DMA directory remain.
The compiled conversion, roster/bridge, and metadata readers are 260, 360, and
640 bytes, each within its checked original reservation.

Output: `build/v3-shared-display-runtime-01/`, pinned by the active build lock.

- ROM SHA-256: `76d148124f4f2e3f4b7157608feb69c9a329612f814f1dffde320287e75ba406`.
- Receipt SHA-256: `c601ec56e93a35e035589a0a5c7ec2835e88715ca233f7308d8fe258b280a50c`.
- UPS SHA-256: `fe0c878a2abb0590e169c3e4dc9c51133cdf90a5abf1741307895f5e2a7dad62`.

Six dedicated shared-alias checks pass, including sanitizer execution with
synthetic identities absent from the installed list, both footprint behaviours,
malformed/recursive/duplicate records, all rotations, strict argument handling,
selection rejection, complete unrelated-resource retention, current CRCs,
reconstruction, and repeat-install reuse. Twelve current-cartridge selection/
save-profile checks pass; all-selected reproduces the new cartridge and empty
selection reproduces stable V2. Two targeted legacy-wrapper host checks pass.
One host test invocation used the wrong class name; the correctly named targeted
check passes. No old-build native scenario is replayed.

The first current native attempt stops at the first metadata-reader call because
the fixture requests a direct upper-memory entry, which the debugger deliberately
forbids. The failure occurs before dispatch, not inside game code. The one
justified retry uses the normal installed low-memory native entries for names,
types, prices, and footprints. It passes 187 records and 177 assertions at
`build/v3-shared-display-native-02/results.json`, SHA-256
`f5faf5a000150db6fa27d984a146896460fd45234e7f5dd172c124e91b897856`.
All three pairs, four rotations, full-width conversion arguments, complete
English names, prices, native footprint cells, independent clothing/display
selection flags, original category fallbacks, restored profile, stack and buffer
guards, clean return, and shutdown pass. The existing scenario omits unchanged
HRA/feng-shui runs instead of replaying unrelated evidence.

The 104 installed choices, all artwork, complete save codec/profile, and saved
format 2 remain unchanged. Same-profile ABI-95/96 compatibility is expected in
both directions, without claiming a new ordinary save/restart or hardware run.
The original 48 extra donor aliases are still pending actual parent inventory/
gameplay integration. The bounded index supports one parent per display; worn-axe
placement states still need their many-input mapping. No new tool/fan/pinwheel
gameplay is claimed, and neither served V2 patcher changes.

The current-lock scan also completes at
`build/v3-shared-display-scan-01/inventory.json`: 76 converter-supported entries,
166 review entries, and no uninstalled fully eligible furniture. This adapter
does not misclassify prepared parent displays as newly usable imports.

## Indexed model-sequence conversion

Converter/installer revision 9 adds the shared `indexed-model-sequence` category.
The complete donor draw instructions, actual pointer-table relocations, bounded
index masks, and matrix-helper calls identify three draw shapes. The ordinary
and golden-tool callbacks use one normalised implementation with checked base
and conditional-index parameters. All create/move/destroy callbacks remain
verified no-ops. No item-specific model list, converter, or native scenario is
added.

The shared converter retains complete material-only and geometry-only lists in
their original order. It removes only intermediate final returns when joining
lists on the same command stream. Every original part retains its source offset,
size, hash, and joined position. The ordinary strict graphics parser then checks
the complete joined list. The fishing rods retain both their opaque sequence
and conditional translucent sequence in separate native profile slots.
No runtime callback, source resizing, model simplification, or new allocation
is introduced.

One unrestricted category conversion completes all 24 display models at
`build/v3-furniture-indexed-sequence-prepared-01/`: eight fans, eight pinwheels,
four ordinary tools, and four golden tools. They retain 46,832 bytes, 852 vertices,
and 566 triangles. Forty-four original source parts become 26 complete native
lists. All source-derived parent relationships and pending placement/pickup
requirements remain attached to the prepared records. They are not selectable
standalone furniture or completed parent-item gameplay.

- Art receipt SHA-256: `fca095571099332fc5c451a2e578bd26095418aba76bc5d23d06af27c73ad436`.
- Inventory SHA-256: `ca0ee62b46cfad05d5e012e10ca35ea180c024bb68c3966e99870ddab0b30680`.

The donor's display names differ from the actual parent name for two entries:
`gold pinwheel` represents `striped pinwheel`, and `bug net` represents `net`.
The parent source records retain the correct inventory names; these are not
additional items or grounds to replace the actual parent wording.

The focused donor/alias suite runs 26 tests: 24 pass, one palette-only prepared
test is inapplicable to this batch, and one deliberately damaged-pointer test
has an inconsistent fixture index. Updating the fixture's address index with its
modified relocation dictionary resolves the test setup error; its targeted
retry passes. A targeted extension of the prepared-artwork check also passes,
verifying all native opaque/translucent profile bindings and null runtime
callbacks. Across these runs, 25 distinct checks pass and one is skipped.

Checks cover every complete texture sample, vertex, triangle, material command,
source part and relocation, all actual selector rows, both conditional layers,
changed code/effects, missing table pointers, malformed/relocated returns,
out-of-range selectors, parent dependencies, and installer rejection of
prepared-only output. The current revision-7 installed batch still passes the
current complete source/asset checks; unchanged palette/static categories retain
their passing donor checks. No native emulator replay is needed for this
converter-only change.

The ABI-95 build lock, 104 installed choices, runtime, saved format, and both
served V2 patchers remain unchanged. Reuse this prepared batch for shared native
parent-item and room-conversion work; do not redo the artwork per item or claim
hardware/playability evidence from conversion checks.

## Parent-item and room-display discovery

Converter/installer revision 8 adds `tools/v3_room_aliases.py`, shared by the
full donor inventory, furniture pipeline, and browser review generator. Complete
donor placement, pickup, and both item/index functions are checked before their
actual range constants supply the records. No per-item identity list, converter,
installer, or scenario is added.

The six categories contain 48 room-display models: eight balloons, sixteen
diaries, eight fans, eight pinwheels, four golden tools, and four ordinary tools.
Four balloon models fall in `1xxx`; the other 44 entries occur in the `3xxx`
queue. Every record retains the official parent name/source hash, parent ID,
all four rotations, pickup ID, and the actual `no_convert_tools` condition.
Seven worn-axe inputs share the ordinary axe's model and return the ordinary
axe ID on pickup. That donor asymmetry is explicit, not seven new furnishings.

Aliases cannot install as standalone furniture, including through older asset
reports. Prepared artwork retains the parent relationship; unsupported graphics
keep a separate `conversion_reason`. The full 2,333-name donor inventory keeps
its original identities and links each parent/display pair; the worn states
also link to their canonical parent. Classification does not approve a native
identity, complete room conversion, or implement the parent's actual gameplay.
No new selectable option is claimed. Both served patchers remain V2.

Actual supplied-disc/N64 inventory generation succeeds at
`build/v3-room-alias-discovery-01/donor-catalogue.json`, SHA-256
`29b575ef4705816d90b70298628e47d05336e6edd3cc65fdfeda323142901363`.
The final current scan is `build/v3-room-alias-discovery-02/inventory.json`,
SHA-256 `771dd65a627aec167e3844ab64fd7ba9788cb2e1e40fae30c2a4cc1db2366f6b`.
It records 76 converter-supported and 166 review rows, with no supported new
uninstalled furniture. Those statuses describe converter eligibility, not the
larger installed set or completed gameplay. Of the 54 uninstalled entries in
the existing bulk-prepared batch, sixteen are diary aliases, thirteen retain
unknown acquisition, twelve require Tortimer gifts, six harvest acquisition,
five island acquisition, and two native identity review.

The focused run executes 44 tests: 41 pass, two optional prepared-asset tests
are skipped, and one assertion still expects the old diary acquisition reason.
Its correction verifies the actual parent-support rejection. The targeted run
passes seven tests, including the corrected assertion, the six alias tests,
and current revision-7 artwork acceptance through complete current validation.
Across both runs, 43 distinct checks pass and two are skipped. Coverage includes
all ranges/rotations, cross-range balloons, every parent name, worn-state
canonicalisation, changed complete code/helpers/relocations, full inventory
links and repeat annotation, shared scan/metadata rejection, rejection before
conversion creates files, installed-alias refusal, and generated browser review
data. Existing graphics/parser/material checks also pass. No emulator is replayed
for a discovery-only change.

The ABI-95 cartridge retains SHA-256
`01c7da7f945f02a4eebb1bafdc258b0485db5dd9240cf2254a51f3eefaccd68c`.
Its build lock, 104 installed choices, saved format, and runtime are unchanged.
The private browser interface export is not regenerated or served.
Next work is native parent identity/gameplay and shared placement/pickup support,
plus the still-missing graphics categories; these dependencies are not waived
by recognising the aliases.

## Constant model-sequence imports

Converter/installer revision 7 adds the shared `constant-model-sequence`
category. Complete compiled draw functions, actual model-pointer relocations,
and the one matrix-helper call establish fixed one-/three-model submission.
Null lifecycle slots are supported, but present lifecycle callbacks must be
complete no-ops. Extra code, calls, DMA callbacks, changed relocation pairs,
and effects are rejected. The same checked-code normaliser serves the existing
palette-fade category without changing its source receipts or runtime.

The converter links complete native lists in donor order with a generated
display list, recorded separately from the original model lists. The normal
opaque profile slot points to that sequence; generic rigs, animations, and the
callback pointer remain null. Lady Liberty retains all three material layers
on the opaque command stream, including their original internal material modes.
The tanabata palm retains its complete single list. Source scalars are unchanged.
No per-item integration script, runtime callback, scenario, or allocation is added.

The unrestricted category conversion at
`build/v3-furniture-static-sequence-assets-01/` discovers both eligible records:
Lady Liberty `3010` (6,736 bytes) and tanabata palm `3054` (4,416 bytes).
Together they retain 11,152 bytes, 248 vertices, and 179 triangles. Generated
links occupy 32 and 16 bytes respectively. The installer regenerates their
exact order, target addresses, bounds, hash, and normal profile binding.
Official names are credited in `translations/provenance.json`. Lady Liberty
uses the existing selected Gulliver reward category and remains non-orderable;
tanabata palm uses the donor event-stock list and actual catalogue policy.

The ABI-95 cartridge is
`build/v3-furniture-static-sequence-runtime-01/animal-forest-v3-asset-loader.z64`.
Automatic additions total 42. The offline composer contains 104 installed
choices: 81 furniture, three shirts, and twenty villagers. The model bank,
item-rendering code, saved format, and existing assets remain unchanged. Blob size
is 3,407,488 bytes, leaving 721,280 before English choices. The catalogue's
conservative memory requirement remains 280,384 of 280,704 bytes.

- ROM SHA-256: `01c7da7f945f02a4eebb1bafdc258b0485db5dd9240cf2254a51f3eefaccd68c`.
- UPS SHA-256: `2d893591aa7f6b49f5e27f1749cfc8a19ae51d8f998eb232143e4428aebdbaf3`.
- Build receipt SHA-256: `0f3991f6e27f59cd9698bbffe7dbe618b528e719773efd5906905b469bd75c9a`.
- Art receipt SHA-256: `aaf6e06e8d3cec9cc705d016dbf86e932703aa8e70a5fb066c12b1f3bb4006a8`.

The combined pipeline/composition suite runs 60 tests: 59 pass, and the
scoring-alias test is skipped because these two records need no alias. The
prepared palette batch is supplied to check that shared code normalisation
retains that category. Complete texels, vertices, triangles, material state,
ordered links, invalid source rejection, retained assets/code, names/credits,
stock/rewards, scoring, catalogue, profile subsets, and exact V2/no-import output
pass. The first silent current-build native run at
`build/v3-furniture-static-sequence-native-01/results.json` passes 124 records
and 85 assertions, SHA-256
`82491eb4dda46a75c9e32bfda38a32bef6d70a7d93b6e8add3d4753b014d31f9`.
It covers actual owner loading/relocation, both complete model transfers,
source framing, selected Gulliver rewards, event stock, acquisition/ownership,
restored state, and guards. Unchanged palette callback evidence is retained;
that scenario is not replayed. The emulator exits cleanly.

Ordinary appearance, interaction, complete catalogue construction, save/restart,
and hardware acceptance remain open. Saved format 2 is unchanged, but saves
containing these new identities must not load older builds or V2. Both served
patchers remain V2, and the private interface export is not regenerated.

The follow-up source review identifies the tools/fans/pinwheels/diaries as
room-display aliases of parent items, not independently acquirable furniture.
The donor forward function is `.text:0760E4`, 640 bytes, SHA-256
`5228a779089eca94c3f751a814e169f74ff085a57626673c86d7d789fadd6c66`;
the inverse is `.text:076364`, 664 bytes, SHA-256
`a948f3ad02dcf0d9f967363bb22203091447edbb416345498564bb18efda353e`.
Their source is `local/ac-decomp/src/game/m_room_type.c`. The native equivalents
in `upstream/af/src/code/m_room_type.c` lack those extra categories. Parent
identity classification and room-conversion implementation remain work; this
finding does not declare those aliases supported or discard their dependencies.

## Shared switchable-palette category

Converter/installer revision 6 discovers eight complete building-model callback
sets without an item allowlist. Normalised complete PowerPC implementations,
exact local call targets, all relocation pairs, both endpoint palettes, and
actual draw order identify one reusable behaviour. All three layers remain on
the donor's opaque command stream, retaining each list's own material mode.
Constant transparent colours survive; changing colours require opaque endpoints.
Roof-colour selection and clocked station models are not silently flattened.

One category conversion produces all eight objects at
`build/v3-furniture-palette-fade-prepared-02/`: 29,664 bytes, 555 vertices, and
346 triangles. Each generated 32-byte header describes its complete size,
palettes, and ordered model pointers. Source callbacks and dependencies are
recorded in each descriptor. Post model requires `ftr_listPostoffice`; police,
museum, market, Katrina's tent, shop, and tailor models have no identified
acquisition list. Those seven remain prepared-only, not selectable gameplay.

The ordinary converter/installer discovers igloo model `31A4` and installs its
complete 2,944-byte object, official name, price, preview, scoring, canonical
profile, and winter-camping reward metadata. There is no dedicated item script,
browser entry, or native scenario. The installed name is credited in the single
provenance catalogue. Automatic additions total 40; the offline composer supplies
102 installed choices: 79 furniture, three shirts, and twenty villagers.

The shared callback compiles to 988 bytes, including reserved table/layout holes,
inside the existing 1,024-byte tent allocation. `80483700` retains the legacy
tent table; `80483720` is the generated-layout table. Creation, float-0.1 movement,
destruction, and drawing are shared; an immutable compatibility layout preserves
the installed tent object unchanged. The current item loader is 1,920 of 2,048
reserved bytes. It accepts the category by callback contract, not by a new item
ID case, and validates the complete loaded header before bank registration.
Startup already invalidates this complete code range; no new startup range,
heap, saved format, or permanent reservation is needed.

ABI 94 is pinned at
`build/v3-furniture-palette-fade-runtime-02/animal-forest-v3-asset-loader.z64`.
The `runtime-01` and `runtime-02` ROMs have the same SHA-256; the second receipt
also binds the legacy tent's current shared code/table correctly. No second
emulator replay is needed for that receipt-only correction.

- ROM SHA-256: `8dcb481ce08eb7bacbc4661cb06ec910bf3ec41d3eb6d3bb753ab0ebcfb6e358`.
- UPS SHA-256: `65d3bda763c7949146fb08d71a0dad11f6bdc73f8d6a51a2bd4c461d0cd5f972`.
- Build receipt SHA-256: `cfc62b59db3b27343a4bba5ce768cd878b6b0c7d09bb439c79176888b8a4ca0d`.
- Complete callback reservation SHA-256: `d9d7f05fe744e0e74ae712e1f53e09bd8372dc69af08001de9c9e40e2b189d5c`.

Blob size is 3,396,336 bytes, leaving 732,432 before English choices. Catalogue
memory is 280,384 of 280,704 reserved bytes. Every previously installed model
retains its VROM and data; only the declared helper/code tables change.

The combined focused suite executes 56 tests. Fifty-five pass; one old blanket
assertion incorrectly disallows the intentional furniture-loader change. Its
targeted correction verifies the exact declared helper/public jumps and proves
the rest of the resident prefix unchanged. That corrected test and a new complete
code/layout/vtable-binding test both pass: 57 distinct checks covered. Sanitizers
execute the shared C with all eight converted objects and the legacy tent,
covering independent instances, mid-fade reversals, submitted-frame lifetime,
all model commands, every palette colour, malformed headers, crowded graphics
arenas, and actor/arena guards. Complete texel/vertex/triangle/material checks,
source rejection, official credit, catalogue/scoring, optional subsets, full
profile, exact no-import V2 output, and saved-profile rules also pass.

The initial native invocation mistakenly omits the required Expansion Pak and
uses the short default timeout; the emulator disconnects before the startup
assertion. It supplies no gameplay result. The one corrected invocation uses
the explicit eight-MiB setting, 180-second bound, and existing Xvfb executable.
`build/v3-furniture-palette-fade-native-02/results.json` completes 190 records with
114 passing assertions, SHA-256
`5ed7848e5a353f5e0fff69f47d85106a8463c32eeb68d18192de1a87b8d474c8`.
The shared representative scenario verifies actual new/legacy model DMA,
all four callbacks, both draw layouts, full interpolated colours, surviving
submitted palettes, actor preservation, full seasonal trade preparation,
acquisition/ownership, restoration, and guards. The emulator exits cleanly.

Ordinary appearance, interaction, full catalogue construction, save/restart,
and original-hardware acceptance remain unverified. Saved format 2 is unchanged,
but saves using the new item must not load earlier builds or V2. Both served
patchers remain V2; the recorded private UI export stays at its earlier snapshot.
Continue remaining shared acquisition/callback categories, not per-item scripts.

## Shared seasonal reward records

Converter/installer revision 5 installs snowy tree model `31A8`, snow bunny
`31D4`, and sleigh `31E0` through the unrestricted automatic conversion and shared
installer. Their complete models contain 13,728 bytes, 322 vertices, and 275
triangles. No item-specific converter, integration script, or native scenario is
added. The three names use the official donor records in the single provenance
catalogue. Automatic additions total 39. The offline composer contains 101
installed development options: 78 furniture, three shirts, and twenty villagers.

The complete ABI-93 cartridge is
`build/v3-furniture-camping-runtime-01/animal-forest-v3-asset-loader.z64`, pinned
by `config/v3-import-build.json`. Artwork is in
`build/v3-furniture-camping-assets-01/`. The catalogue has 514 furniture and 248
clothing rows. Conservative menu memory remains 280,320 of 280,704 bytes. Blob
growth is exactly the 13,728 artwork bytes, to 3,393,376 bytes, leaving 735,392
bytes before English choices. Existing owner allocations and model VROMs remain.

Winter acquisition uses actual `ftr_listKamakura`, donor list type 19. The donor
normal-trade function at `.text:122B8C` rolls `random(100) >= 90` in scene 31;
the separate 10% house-gift roll follows it. The native body lacks this winter
special-list roll. The shared trade adapter enables it only when winter imports
are selected; otherwise the original native body runs without another RNG draw.
Summer scene 35 retains its `>= 80` roll and list type 23. Carpet/wall donor
descriptors have neither special-list pointer and retain physical-A fallback.

Both seasons and Gulliver share the same source-derived item metadata. The ten
summer items no longer live in a hand-maintained runtime array. All seventeen
installed reward records carry their actual category in byte 27. The 948-byte
resident reader preserves rare/existing-item exclusions, the donor's small-list
duplicate allowance, and exhausted-profile fallback. It exports a checked count
entry at `80474EFC`, used without randomness to select winter's original-body
fallback. Code and guards fit the same `80474BB0..80474FEF` reservation.

The dependent camper suffix compiles to 1,152 bytes, down from 1,344, with 192
zero padding bytes. Its complete normal owner remains 20,736 bytes and its
relocation file remains 2,272 bytes, with 558 entries. The original prefix outside
the two entry hooks, native state, quest descriptors, callbacks, and shared
conversation allocation remain unchanged. Both relocated bases are checked.
Future automatic batches rebuild the suffix against the actual resident count
entry rather than assuming a stale compiled address.

HRA donor category 33 maps to native scoring category 3, using the same verified
412-point equivalence as summer category 37. The actual donor point table,
installed native weights, expanded evaluator patches, and all three native
five-bit consumers are checked. This changes scoring metadata only, not the
reward route. Native counters, point weights, and stack allocation stay intact.

- ROM SHA-256: `fe9b175801c5b1d7eb00b7ddf23d01d4fd164643cd01d9f2f6270d7e89f8598e`.
- UPS SHA-256: `e80813e4d538cfe5d117afbc07e6d2ca90d3dc1bd01704a092aa3e4c881669ad`.
- Build receipt SHA-256: `4973f7d2705be2c280c321d29b7c51daddfa2e708b949db5c6cfd6153a5ec1c3`.
- Art receipt SHA-256: `463e19c092235b63f907b12a8493e799e6d2561268c2b4c16a404f6a8ebb26cf`.
- Blob SHA-256: `f4301306b6245a24b59d62225f34ded2d44545b615699f1224eaf2ad43d2e91c`.
- Shared reward code SHA-256: `193943c60d253c8eacc76250d2960a902ff8e79d648efa10587a61b36fd430b1`.
- Trade owner SHA-256: `1a6571128da3e3c8171a347af5a829eb8acaf3246362c0fcb5b7a5074056037e`.
- Trade relocation SHA-256: `f4a0fffe3564208ccd2ec1e95d65c8703a7f5efc54c62bbfbccad237bb5246bd`.

The combined suite runs 52 tests: 51 pass and the optional prepared-only artifact
check is skipped. Sanitizers execute the actual shared selector and camper C,
including all ten summer identities, sparse profiles, both seasonal thresholds,
house override/empty-house fallthrough, duplicate/exclusion rules, and unchanged
ordinary trades. Complete source texels/vertices/triangles, material commands,
owner-prefix retention, fixed allocations, scoring equivalence/rejection,
catalogue, source credits, profile composition, and exact V2/no-import output pass.

The first silent native run completes all 162 records with 118 passing assertions
at `build/v3-furniture-camping-native-01/results.json`, SHA-256
`c2cff0b14ccb4f61b7b2e95c37715fbe4ac3cf52fee77a80c06c6c90c1cfc92d`.
It covers actual current owner loading/relocation, complete model DMA, readers,
preview, ownership, all three selected reward categories, sparse first/last
choices, no-selection native stock fallback, and complete seasonal trade calls.
Real RNG seed 7 produces the selected winter reward; disabling winter imports
executes the original native trade body. Seed 6 checks the unchanged summer
threshold through the shared reader. Input identity/slot, carpet/wall candidates,
pitfall mode, state restoration, guards, and clean shutdown pass. No native retry
is needed, and no old build is rerun.

These results do not establish ordinary camper conversations, handover animation,
GPU appearance, full catalogue construction, save/restart, or original-hardware
playtesting. Saved format 2 and permanent allocations remain unchanged, but saves
using the three new IDs must not load older builds or V2. Both served patchers
remain V2 pending the user's testing and explicit approval.

The post-scan at `build/v3-furniture-camping-post-scan-01/inventory.json` identifies
73 supported entries, all installed, and 169 review entries. This includes seven
already-installed summer models now recognised by the shared metadata path.
Fifty-four additional real models pass artwork preparation but retain their
actual requirements: 29 unidentified acquisition routes, twelve Tortimer gifts,
six harvest, five island, and two identity reviews. Sixteen diary models also
need diary gameplay. Continue shared acquisition/callback categories and the
remaining V3 gameplay/browser integration; prepared assets are not playable imports.

## Shared acquisition categories

Converter/installer revision 4 discovers, converts, and installs five further
objects without an item list: Arc De Triomphe `3014`, mermaid statue `301C`,
plate armor `3034`, Chinese lion `3050`, and festive flag `327C`. Complete artwork
totals 20,128 bytes, 487 vertices, and 401 triangles. The four souvenirs use the
actual `ftr_listJonason`; the flag uses `ftr_listTrain`. Every name has official
source attribution in `translations/provenance.json`. Automatic additions total
36, with 98 installed offline development options: 75 furniture, three shirts,
and twenty villagers.

The complete ABI-92 cartridge is
`build/v3-furniture-acquisition-runtime-01/animal-forest-v3-asset-loader.z64`, pinned
by `config/v3-import-build.json`. The artwork is in
`build/v3-furniture-acquisition-assets-01/`. The shared catalogue has 511 furniture
and 248 clothing rows, using a conservative 280,320 of 280,704 menu-pool bytes.
The blob is 3,379,648 bytes, leaving 749,120 bytes before English choices.

The train gift uses native list 4 and its catalogue-orderability mask. Gulliver
already exists in the N64 game: actor `A8`, owner `00958220`, RAM `80A97FB0`.
The original gift function at `80A983B4` selects native rare furniture; the donor
selects souvenir list type 12. Only its list argument at `80A983BC` and selection
call at `80A983D8` change. Native conversations, inventory checks, demo requests,
pocket insertion, and event completion remain. The complete owner and unchanged
304-byte relocation resource are checked. The 3,712-byte compressed owner moves
once to uncompressed blob storage before the three regenerable terminal owners;
future batches can update it in place without accumulating copies.

One shared 700-byte reader at `80474BC0` uses canonical item metadata byte 27 and
enabled profiles, not per-item switches. Encoded route `0C02` supplies donor
category 12 with native fallback 2. Selected souvenirs retain the donor's random
rare-item rejection; empty/all-excluded selections use the original native route.
Souvenirs stay non-orderable and absent from ordinary shop lists. The code and
guards fit the checked gap between preview data and accessory artwork. Startup
is 924 bytes and explicitly invalidates the helper's code range. No permanent
RAM reservation, item-record width, saved format, or original identity changes.
Saved format 2 remains; saves containing these new IDs must not load older builds
or V2. Ordinary cross-version save/restart compatibility is not newly claimed.

- ROM SHA-256: `ffe996df066c4bfb85f8a438ffef852691e1e2ea4a58bda81d3816c2f3b92252`.
- UPS SHA-256: `4bf6a6e7d039dc431f7e81b21198ad4f75cce98edf7c67f5e8ba0da7c797bb5d`.
- Build receipt SHA-256: `5c99e5d37918f14f0af315eeaf77e6899300acf1acd922e9de2b0a023521db3d`.
- Art receipt SHA-256: `d02e0c22a1badb5dd11afc4a76ad7613add19004499c4d713099a9b5557c6a77`.
- Blob SHA-256: `066fefd4aba0bf5026b1866fb70b6c2a1dfab18d5954b7feb19b562513042679`.

The combined focused suite runs 49 tests: 48 pass and the optional prepared-only
artifact test is skipped. Complete conversion/material checks cover the new
installed batch. Host sanitizers cover multiple reward categories, sparse and
disabled records, canonical identity validation, random endpoints/rejection,
rare-only fallback, and all seven native arguments. Cartridge checks verify the
complete owner with exactly two instruction changes, retained relocations,
non-orderability, repeated helper installation, safe terminal reuse, source text
credits, scoring, subsets, select-all, and exact import-free V2 composition.

The first native run passes 87 assertions in 104 records, then the harness rejects
a direct upper-memory helper call before executing it. This is the debugger's
explicit below-4-MiB proof restriction, not an observed game failure. Its evidence
is retained at `build/v3-furniture-acquisition-native-01/results.json`, SHA-256
`08637abdc036b6dc2ac34dd0f56be9bf40edd445c564232635eb4cec67c582d4`.
The test reuses its existing checked low-memory jump bridge; no cartridge change
or debugger-permission expansion is needed. The one corrected retry passes all
131 records with 104 assertions at
`build/v3-furniture-acquisition-native-02/results.json`, SHA-256
`81bd7f935c9c901e334b3b54ac5cb5b85727df1d7dcc611566f63e6065838dc8`.
Representatives are selected by category (`3034`, `301C`, `327C`), not separate
scenarios. Actual owner loading/relocation, installed call instructions, complete
model DMA, native readers/footprints, preview, stock/catalogue rules, acquisition,
ownership, two isolated sparse souvenir selections, empty-selection native reward
fallback, restored state, and all final guards pass.

These checks do not establish ordinary NPC conversations/gift animation, train
gift delivery, GPU appearance, full catalogue construction, save/restart, or
hardware playtesting. Both served patchers remain V2. Source may be pushed;
switching either patcher still requires the user's testing and explicit approval.

The post-scan at `build/v3-furniture-acquisition-post-scan-01/inventory.json`
contains 63 supported entries, all installed, and 179 review entries. Fifty-seven
uninstalled real models pass artwork preparation: 29 unidentified acquisition
routes, 12 Tortimer gifts, six harvest, five island, three winter-camper, and two
identity reviews. Diary gameplay remains an additional dependency for sixteen.
Continue shared acquisition and animated callback categories; do not restart
per-item conversion, installers, or tests. Prepared assets remain distinct from
completed playable imports.

## Direct-colour category and bulk prepared assets

Converter/installer revision 3 adds shared RGBA16 materials and prepares every
eligible uninstalled static model in one command:

```sh
python3 tools/v3_furniture_pipeline.py convert --assets-only \
  --output build/v3-furniture-all-static-prepared-02
```

The resulting 62 non-placeholder objects contain 211,136 bytes, 5,065 vertices,
and 3,720 triangles. The art receipt SHA-256 is
`0cf956288f7c323d5d0571fd9b8426fd93105a070d4bcb205a3fb1b06d2dffad`.
No individual item list or specialised graphics description is used. The shared
RGBA16 category includes Diver Dan `31D0`, retaining all 5,120 bytes, 107 vertices,
102 triangles, CI4 body materials, direct-colour helmet, and I4 reflection layer.
Its actual island acquisition remains required.

The supplied executable SHA-256 is
`e3166b15b810ff20397784fc83b2eb053db5d0c2a9e22ac2ead63a645881d150`.
Its complete 64-byte `fmtxtbl__5emu64` at `800AAFC0` has SHA-256
`7ae4019ff69d72ee09dd42b8b1c5a4c7a3a236d07aa238e2acdb93c97302fe30`.
The actual RGBA/16 entry is GX format 5, RGB5A3, not RGB565. The matching source
is `src/static/libforest/emu64/emu64.c` in the pinned donor checkout. Conversion
untile uses complete four-by-four blocks and native RGBA5551. Opaque and fully
transparent alpha are retained exactly; partial alpha fails instead of being
thresholded. Textures remain bounded to 2,048 bytes so switching back to CI4
cannot lose palettes in upper TMEM. Native 16-bit loads retain source scales,
wrapping, and shifts. No texture is resized or dropped.

Bulk discovery identifies sixteen entries using the same `iam_dummy` profile at
donor `.data:00092D6C`; fifteen have plausible item names. Both actual profile
tables select that placeholder. The converter now excludes this category by
its source pointer, not a maintained item-name/ID list. These entries retain
`asset_ready: false` and an explicit missing-artwork reason. An initial prepared
collection at `build/v3-furniture-all-static-prepared-01/` exposed the placeholders;
it is retained but not the current prepared collection. Unknown/dummy names also
remain excluded. A missing model in this English donor is not proof that the
item is unused in other editions.

The final collection retains actual missing dependencies:

| Dependency | Prepared objects |
| --- | ---: |
| No identified acquisition list | 29 |
| Tortimer holiday gifts | 12 |
| Harvest rewards | 6 |
| Island rewards | 5 |
| Gulliver rewards | 4 |
| Winter-camper rewards | 3 |
| Native identity/artwork correspondence | 2 |
| Train reward route | 1 |

Acquisition is not the only possible requirement: the sixteen diary display
models also need their actual diary gameplay. Prepared output is a separate
format and cannot pass installation. No prepared object is added to the offline
selection catalogue or counted as a completed playable import.

Forty-six focused pipeline/composition checks pass with the new direct-colour
artifact; the additional actual-executable format-table check and updated shared
placeholder-discovery check also pass. The shared complete-artwork and compiled-
material checks pass again against all 62 final prepared objects. Thus forty-seven
distinct focused checks pass across this batch. Independent comparisons cover
every source sample, vertex, triangle, model layer, material state, native load
format, palette mode, stride, texture scale, wrap, and shift. Partial-alpha and
incomplete-block rejection are covered without a new native scenario.

The current cartridge, build pin, 93 installed development options, saves, and
both served patchers remain unchanged. ABI-91 native results below are retained;
no old cartridge or unchanged emulator path is rerun. The newer converter source
does not relabel the ABI-91 build receipt as produced by revision 3. The scan still
has 58 supported and 184 review records; placeholder classification improves the
reason rather than hiding those records. Continue shared acquisition and animated
callback implementation using these prepared assets.

## Current shared intensity materials and resource reuse

The complete development cartridge is ABI 91:
`build/v3-furniture-intensity-runtime-01/animal-forest-v3-asset-loader.z64`.
The shared `intensity-materials` category discovers G logo `31E8` and bird bath
`3240`, retaining complete CI4/I4 textures, all opaque/translucent model layers,
reflection/water material state, and actual stock A acquisition. Their 6,880 bytes
contain all 202 vertices and 126 triangles. No item-specific model definition,
installer, runtime code, or native scenario is added. Automatic additions total
thirty-one; the offline composer contains 93 installed development options:
70 furniture, three shirts, and twenty villagers.

Converter revision 2 supports complete four-bit CI and intensity textures without
resizing. Pure I4 objects do not require a palette. Mixed lists select native
TLUT state at every actual format transition. Independent positive S/T scales,
four-bit shifts, wrapping, primitive/environment colours, and reviewed generated
reflection coordinates retain their source values. Unknown formats/state still
fail. The earlier CI4-only category remains available; `static-4bit` covers both.
The same category prepares miniature car `3094`: 7,104 bytes, 170 vertices,
and 98 triangles. Its acquisition is unresolved, so this prepared-only artifact
cannot be installed. Harvest mirror passes graphics discovery but still needs
the harvest acquisition adapter. No unsupported callback or acquisition is waived.

The installer reuses exactly the preceding automatic batch's terminal catalogue,
relocation, and shop resources. Complete hashes, DMA mappings, aligned contiguous
extents, zero padding, terminal boundary, resident boundary, every other DMA
resource, and all canonical profile extents are checked before reuse. Changed
receipts or live overlaps fail. The 64,496-byte prior tail starts at blob offset
3,284,400. Its retained prefix SHA-256 is
`0bb5766df6d034e6fca7acbed4efe8b7213db38808110f5ccac0df1663d429ac`.
New art precedes the regenerated owners; their fixed VROM identities and all
previous model VROMs remain unchanged. Reuse affects only the fresh output, not
input ROMs, previous builds, or saves. It prevents new redundant copies; it does
not compact older superseded data elsewhere in the retained prefix.

The catalogue has 506 furniture and 248 clothing rows. Conservative menu memory
remains 280,320 of 280,704 bytes. The import blob is 3,355,776 bytes, leaving
772,992 bytes before English choices. Growth is exactly the new 6,880 artwork
bytes, rather than another catalogue/shop copy. No runtime code or permanent
allocation grows. Saved format 2 remains; saves containing either new item must
not be loaded by older builds or V2. Forward ordinary cross-version reload is
not newly claimed. Both served patchers remain V2.

- ROM SHA-256: `ad194977b9083764c0efe8636614ba45d69b9370d6322514e2fd0b24aff2c1e3`.
- UPS SHA-256: `419588ce3dbf295f27ce96c8647f9042ed7111645fb84560f1d19f1aed89a2cd`.
- Build receipt SHA-256: `cbd63fe09ae8661bf4f9490e7f9ab3adcfb1e014c5d7932408322fce4203809b`.
- Art receipt SHA-256: `53659935e7ba271730ff1cb7b5cc5fe89ed290c9d40a3ab5af7975fa97c5e035`.
- Import blob SHA-256: `1c125a28cb24537db05e4f81e5703050d910a4542291586e5acbb71d1959383d`.
- Prepared car receipt SHA-256: `d9235377ce673ab0119b5cb025e5df3abc68d4f6cd06889b56b9ed3698966077`.

All forty-four focused pipeline/composition checks pass, with no skips. Material
tests independently decode compiled format, palette mode, stride, S/T scale,
wrapping, and shifts against source commands. Complete sample/vertex/triangle
checks also cover the prepared car. Palette-free I4, CI4 palette rejection,
mixed LUT transitions, changed tail data/receipts, and retained-profile overlap
are covered. Every previous complete model stays unchanged; tail reuse is
verified again from the new receipt. Existing sanitizer, stock/scoring,
official-text attribution, original-code, optional-subset, full, and exact V2
composition checks pass. All twenty current build-source hashes match the receipt.

The first silent native run passes 88 records with 68 assertions:
`build/v3-furniture-intensity-native-01/results.json`, SHA-256
`0153c9a523feb3316d5ce3d809f06e195e08c43a2149d0e0b4c7ad4dd51118cb`.
Both items represent distinct model-layer configurations. Complete native owner
loading/relocation, model DMA and bank tails, names/prices, footprint, catalogue
framing/fallbacks, relocated owners, stock, acquisition, ownership, restoration,
guards, and clean exit pass. No retry is needed. This is not GPU appearance,
full catalogue construction, ordinary gameplay, save/restart, or hardware proof.
No old cartridge is rerun.

The post-scan at `build/v3-furniture-intensity-post-scan-01/inventory.json` has
58 supported entries, all installed, and 184 review entries. These include
aliases and special imports, not a completion percentage. Continue shared
callback/acquisition categories and verified RGBA16 conversion; miniature car,
holiday gifts, island items, harvest items, and diaries retain their actual
unresolved dependencies.

## Square-furniture and double-bed batch

The complete development cartridge is ABI 90:
`build/v3-furniture-square-runtime-01/animal-forest-v3-asset-loader.z64`.
One `convert --category 2x2` batch discovers picnic table `32DC`, neutral corner
`333C`, red corner `3340`, and blue corner `3344`. The shared installer supplies
their complete models, profiles, names/prices, catalogue/scoring records, and
stock C/A/event/lottery routes respectively. No item-specific converter,
installer, gameplay code, or native scenario is added. The 15,568 bytes of
new artwork retain all 330 vertices and 182 triangles. Automatic additions
total twenty-nine; the offline composer has 91 installed development options:
68 furniture, three shirts, and twenty villagers.

Square collision category `5` and shape `5` remain distinct profile fields.
The existing four-cell reader supplies the same clockwise, upper-left-anchored
footprint in every rotation. The build rechecks the actual original/donor
footprint tables and the complete installed 1,020-byte reader at `80483000`,
SHA-256 `baf6957601fea4fc0829382bbc21604ade478479e9f0f6375c6e4d49e2f0317d`.
The three ring corners keep contact action `0x10` and the existing native
double-bed routines; they are not flattened into decorative furniture or
single beds. The complete checked room engine and expanded profile bindings
remain unchanged. No permanent allocation, saved structure, or native code
reservation grows.

The catalogue contains 504 furniture rows and retains 248 clothing rows.
Conservative menu memory is 280,320 of 280,704 bytes. The import blob is
3,348,896 bytes, leaving 779,872 bytes before English choices. Saved format 2
remains, but saves containing the new four items require this build or a
compatible profile superset; older builds and V2 must not load those saves.
Ordinary cross-version save/reload is not newly claimed. Neither served patcher
changes.

- ROM SHA-256: `91be4e2ccd1fc9bb3be77f16c11eff74a7b387582475deed575d3a316ea02277`.
- UPS SHA-256: `935651090a5a5b62ac99ddb37a9871951b8b3eaa9813bca90e3bfb06603bc0cd`.
- Build receipt SHA-256: `bdbeb14058d69b704de14865b5b2bb47048636345d34eccb76887265fcbffdfe`.
- Art receipt SHA-256: `bec4490afaca0b848c3d8fb4b4d5bd5e5a22a3773e1befb034ba2847f4291d74`.
- Import blob SHA-256: `02b36fbc1e93a002ca5c3f9db66f46c260aae3853b24d8a7eb9b291562b0eaa5`.

Thirty-eight focused pipeline/composition checks pass; one optional prepared-
assets check is not requested. New checks cover shared square/double-bed
discovery, intact donor scalars, unknown collision rejection, changed native
reader rejection, and the existing four-cell host fixture under address and
undefined-behaviour sanitizers. Complete texture/vertex/material conversion,
installed records, official text credits, retained native code, stock/scoring,
and optional-profile composition also pass.

The first silent native run passes 180 records with 158 assertions:
`build/v3-furniture-square-native-01/results.json`, SHA-256
`208149336a2def36a3647f23eb8aa1bc3450527ef25c89e93824c020c297ba9e`.
All four items are representatives because their stock categories differ.
Their complete model DMA, names/prices, four-cell footprints in all rotations,
catalogue framing/eligibility, stock, acquisition, ownership, restoration,
and guards pass. One double-bed representative exercises the actual native
head-direction and both side-position functions in every rotation, retaining
the wider side span and half-cell pillow offset. Inactive-bed rejection and
complete temporary-actor preservation also pass. No retry is needed.

The shared probe checks bed geometry once per changed contact category and
tests imported chair sounds for the new batch rather than every previous
chair. Full source audio/code checks remain in the build contract; earlier
passing native evidence remains recorded. No old candidate is rerun.
These checks do not establish ordinary bed entry/rolling/exit, complete room
appearance, catalogue construction, save/restart, or original-hardware play.

The post-scan has 55 supported entries, all installed, and 187 review entries.
It includes aliases and special imports and is not a completion percentage.
The next shared storage improvement is safe reuse of the regenerated
catalogue/relocation/shop tail (64,496 bytes in this build), preserving every
retained resource and previous output. Shared mixed CI4/I4 material handling
also remains: miniature car, G logo, and bird bath have I4 layers, while Diver
Dan additionally has RGBA16. Keep acquisition/callback dependencies explicit.

## Single-bed batch

The complete development cartridge is ABI 89:
`build/v3-furniture-bed-runtime-02/animal-forest-v3-asset-loader.z64`.
The shared `single-bed` category discovers and installs hammock `329C` and
weight bench `3358` without per-item model definitions, installers, gameplay
code, or native scenarios. Both retain stock C, their complete two-layer
models, two-cell footprints, donor profile scalars, official names, prices,
scoring, and preview framing. Total new art is 8,416 bytes, 196 vertices, and
108 triangles. The automatic pipeline has installed twenty-five additions;
the offline composer contains 87 development options: 64 furniture, three
shirts, and twenty villagers.

The category uses native contact action `08`, not a decorative approximation.
The checked native room engine already handles bed positioning, contact, entry,
and exit through the expanded profile table. The build verifies the complete
owner SHA-256 `ca540a6f48fa15fb8bfad4d36abf77bb3d318799732d965f278063207f64b74a`
and the four reviewed profile bindings at `809404D0/809404DC`,
`809407BC/809407C8`, `80940FA8/80940FB8`, and `809419D0/809419E0`, all addressing
`80470010`. No gameplay code or permanent memory is added. Native timing and
player animations remain unchanged.

Beach chair and harvest bed pass this category's model/dependency discovery
but are not installed. Their actual `ftr_listIsland` and `ftr_listHarvest`
acquisition routes still need shared adapters. Their presence in a supported
bed category does not waive those requirements or replace them with shop stock.

The catalogue contains 500 furniture rows and retains all 248 clothing rows.
Conservative menu memory is 280,320 of 280,704 reserved bytes. The import blob
is 3,268,832 bytes, leaving 859,936 bytes before English choices. Model-bank
allocations and saved format 2 are unchanged. Saves containing the new items
must not load in older cartridges or V2. Ordinary cross-version reload is not
newly claimed; both served patchers remain V2.

- ROM SHA-256: `e460ec11ba2eb2abebcc7aa15c8060728a5c986ddfb0c3f67078689c1a0d9dff`.
- UPS SHA-256: `7020d093e96bb510a36e46383bb715d7a8b4e5757f4eda476bfc65636a478232`.
- Build receipt SHA-256: `ad8cc4af55fae0da16115b5d251ff6a07372b84abcbb70bdf734278b3d2ffb16`.
- Art receipt SHA-256: `56d48e0b812717e4368abb986813d89223920e896ac9b4152fc96d52a8b9205a`.
- Import blob SHA-256: `0dbf4c68f6f5bc46c105887be5d268816cbcff90ecc26c1b5d3af832cc5d489b`.

Thirty-five focused pipeline/composition checks pass; the optional prepared-
assets check is not requested in this batch. They include complete conversion,
source credits, shared category discovery with acquisition rejection, changed
native-engine/table-binding rejection, complete installation, retained native
code, stock, scoring, and selected-profile composition.

The first silent native run passes 112 records with 93 assertions:
`build/v3-furniture-bed-native-01/results.json`, SHA-256
`6fc9749bd4f071050ee9f506c3347f13c88c7a4ead97f6c7dce110f00804fe9f`.
The shared selector chooses the larger weight-bench model to represent the
same stock, footprint, material layers, preview, sound, and bed category.
Actual head-direction (`80940304`), foot-side (`80940498`), and pillow-side
(`80940784`) functions pass all four rotations through the installed imported
profile. Inactive beds return no positions; the complete temporary actor stays
unchanged. Complete owner loading, model DMA, shared item/catalogue/stock
readers, acquisition, ownership, restoration, and guards also pass. No retry
is needed. The final recipe receipt refreshes a source comment and reproduces
the exact native-tested cartridge; no emulator rerun follows that comment edit.

These checks do not establish ordinary climbing onto/leaving a bed, full
catalogue construction, GPU appearance, save/restart, or original-hardware
behaviour. Continue shared callback, graphics, and acquisition categories;
use the same representative batch scenario rather than adding an item scenario.
The post-scan at `build/v3-furniture-bed-post-scan-01/inventory.json` has 51
supported entries, all installed, and 191 review entries. Those entries include
aliases and special imports; these counts are not a completion percentage.

## Material and catalogue-framing batch

The complete development cartridge is ABI 88:
`build/v3-furniture-material-preview-runtime-02/animal-forest-v3-asset-loader.z64`.
Shared discovery installs bug zapper `3234`, coffee machine `323C`, candy machine
`3254`, and steam roller `328C`, with 15,104 complete object bytes, 258 vertices,
and 153 triangles. The first two retain stock A, candy machine retains stock C,
and steam roller retains event acquisition and its two-cell footprint. All names
have official-source credits in the single provenance catalogue. Automatic
additions total twenty-three; the offline composer contains 85 installed
development options: 62 furniture, three shirts, and twenty villagers.

All four use the same unlit texture/primitive material command. Its two cycles
pass texture RGBA through, then multiply RGB by primitive colour while retaining
alpha. The symbolic native `gsDPSetCombineLERP` compiles to donor words
`FCFFFE60 FFFCF3F8`; complete compiled material/geometry checks pass. The coffee
machine's environment-lighting flag is also retained. There is no item-specific
graphics description or installer.

Catalogue framing is now source-indexed for all 62 installed furnishings. Byte
26 of the existing 32-byte item record stores the donor framing index plus one.
The complete 328-byte/41-entry table and its guards occupy
`80474A30..80474B9F`, with table data at `80474A40`. It fits after the placement
table and before accessory artwork, without increasing any permanent allocation.
The general native helper changes only model Y and scale after native
construction; clothing aliases keep their existing presentation. It replaces
the installed per-item Western, bike, and campfire overrides. The steam roller
and campfire both obtain the donor's mode 19 (`0.86`, `-3.0`) through records.
Disabled, absent, invalid-selector, and original-native cases retain their input.

The complete catalogue suffix is 3,408 bytes, and its 498 furniture rows retain
all 248 clothing rows. Conservative menu memory is 280,256 of 280,704 reserved
bytes. The import blob is 3,195,952 bytes, with 932,816 bytes before English
choices. Model-bank allocation and saved format 2 are unchanged. The required
saved profile is a superset of ABI 87. Saves using the four new items must not
be loaded in older builds or V2; ordinary cross-version reload is not newly
claimed. Both served patchers remain V2.

- ROM SHA-256: `5644a08760b63a396747adf2d5926340255667309152c7d9d0e4290263945319`.
- UPS SHA-256: `ed9c1c5b54e57d7414cc6b1f2b4dca39e9b5e284925222b999f54249e809c74e`.
- Build receipt SHA-256: `c8181c0ccb92625fb8d031317f8b83df5be29d9a09a5e5bddff64340105f5cfe`.
- Art receipt SHA-256: `e0e93177e8b011b6f73d571ce6e805317f4d13797adf03eefd2ee70ba4598a57`.
- Import blob SHA-256: `76032e58970f9e296b3d8054b09220662ef571a20339b345034ca9e8a172521a`.
- Preview table SHA-256: `fa6592f8af1ebb2ddb984e59b39649c36afeb85bdd4f9127dbcae26ba62a2a98`.
- Preview reservation SHA-256: `44d06f4df2fca8da04bb6c6a4ee48f131d9a2e1d22dce012027f077cb32b71bb`.

Thirty-four focused pipeline/composition checks pass against this candidate
before promoting its lock. They include the shared native combiner expression,
complete resource/geometry comparisons, all source-derived framing selectors,
guarded repeat-batch reuse, source credits, installed metadata, and selected/save
profile composition. The catalogue's host address/undefined-behaviour checks
cover the complete framing-table range and invalid boundaries. The fixture
preserves the distinct clothing-display stock route when enabling the full
catalogue wrapper. An initial build catches the old seating helper's reserved-
byte check; the corrected check recognises byte 26 as framing metadata while
retaining zero checks on bytes 27–31. That partial build has no promoted ROM.

The first silent native run passes 146 records with 124 assertions:
`build/v3-furniture-material-preview-native-01/results.json`, SHA-256
`3ae031b8643fbcd3a029b4387e2a7e5fde499f4b1157e4d687878e159a20b777`.
The shared representative selector covers all four new records because their
stock, footprint, preview, and lighting categories differ. Actual owner loads,
complete model DMA, source framing with every other preview field unchanged,
disabled/invalid/native framing fallbacks, names, prices, rotations, stock,
acquisition, ownership, restoration, and guards pass. The emulator exits cleanly;
no native retry is needed. This is not proof of full catalogue initialization,
GPU appearance, ordinary gameplay/save-restart, or original-hardware execution.

The post-scan in `build/v3-furniture-material-preview-post-scan-01/inventory.json`
has 49 supported entries, all installed, and 193 entries needing review. That
inventory includes aliases and unused records and is not a remaining-content
percentage. Continue shared behaviour/format/acquisition categories.

## Shared identity-indexed model and palette conversion

The converter handles the complete nine-entry flower selector through one
`indexed-static-model-palette` rule. No item list, separate graphics converter,
installer, runtime helper, or native test scenario is added. The source's fixed
actor identity selects two opaque models and a palette. Both models retain
their full material/geometry commands, and their segment-eight palette loads
become direct loads of the selected native palette.

The checked donor has `fNFL_dw` at `.text:2D0768`, 192 bytes, SHA-256
`612998bdab7cb941114e08d66db7100ded74894f8c1ccfdbdffe4bb9fbb44917`.
Its four code relocations bind the save/restore helpers and the complete
`fNFL_model_data` table at `.data:092BE0`, 108 bytes. The actual instructions
subtract runtime index 1246 and multiply by a twelve-byte row stride. All three
lifecycle callbacks are four-byte returns; the DMA slot is null. The verifier
checks those facts and dependencies, not merely function names. The donor room
renderer's `aMR_DrawRegistModel` uses the same current matrix and opaque0/opaque1
order; the special callback adds only the constant palette selection. Catalogue
rendering also retains that model order. Native execution of these new assets
is not yet claimed.

One command prepares all nine variants:

```sh
python3 tools/v3_furniture_pipeline.py convert --assets-only \
  --category indexed-static-model-palette \
  --output build/v3-furniture-indexed-palette-art-01
```

The output contains 19,152 object bytes, 555 vertices, and 288 triangles across
all three pansies, three cosmos, and three tulips (`3378..3398`). Each object has
its actual official donor name/source index and its selected palette. The
complete prepared receipt SHA-256 is
`6e173ac1c9c1889389779d93b63fd7ac6589d5644bd6d0afa9387dfe72711e83`;
the inventory SHA-256 is
`20df1500755bc29f67ffcb923f84a34244430e79a758bc718eb6e89b4e61f522`.
Individual object/resource hashes are in that receipt.

All nine remain **prepared, not installed**. The donor's
`ftr_listEventPresentChumon` contains these nine flowers, two tree models, and
weed model. `mCL_furniture_init` and `mMpswd_check_present_user` treat this category as
orderable/password-eligible, but that does not establish a working native initial
acquisition route. The N64 has no matching stock-list slot. Do not put the objects
in ordinary shop stock or claim acquisition is complete. Shared acquisition and
catalogue handling must cover the twelve source records together.

The actual initial acquisition comes from `mSC_trophy_item`, not a random shop
list. Its 244-byte donor function at `.text:07C31C` has SHA-256
`48321dd6e22de9f11751b89f9557c5be837f142f70b36bbe5cbd8ff933ea8234`.
The 56-byte `soncho_item_table$582` at `.data:010714` has SHA-256
`2bf4a655de09672b8c202cad690e6595cae1859656b5f379e9b9347822ea2fd9`.

| Donor event | Source reward rule |
| --- | --- |
| Founder's Day, index 1 | Weed model `3080` |
| Cherry Blossom Festival, index 7 | Pink tree model `307C` |
| Nature Day, index 9 | Tree model `3078` |
| Groundhog Day, index 13 | Uniform random runtime index `1246 + RANDOM(9)` |

The gift list at `.data:698630` is 26 bytes including its terminator, SHA-256
`07391eb07d67a5f92dfcd3300ac0586bc3908bb470e8ff2257cd7e39e1a8040f`.
`aES2_talk_before_give` checks pocket space; `aES2_talk_give` performs the normal
handover, inserts the actual item, and records the event trophy. Their complete
function hashes are respectively
`a3129746c1e60b877ecd74ae82f6861db8ef00509f0f15bfebe097324683bacc`
and `adb99cc52df75acb980d5f865c3c20f9778e223011b86d6f0b00d59aeec0d699`.
This requires the donor Tortimer event actor, English conversations, calendar
integration, selected-reward eligibility, and reviewed per-player trophy/calendar
persistence; the N64 actor/profile inventory has no corresponding Tortimer
implementation. Donor private-data offsets are not native saved fields. Implement
the shared event route without turning these rewards into ordinary stock, and
continue unrelated conversion categories while that larger dependency is open.

Thirty-two focused pipeline/composition checks pass with
`V3_FURNITURE_PREPARED_ART=build/v3-furniture-indexed-palette-art-01`. The reused
asset checks compare complete texels, vertices, triangles, materials, and palette
load targets. New checks cover every actual selector row, independent relocation
resolution, unknown/changed callback rejection, extra DMA effects, bad indices,
ambiguous palette bindings, and refusal to install prepared-only output. No
native emulator run is repeated: ABI 87, the ROM, import lock, saves, and both
served V2 patchers are unchanged. The 81 installed options do not include these
nine prepared objects.

Callback inspection also identifies useful next shared categories: fifteen
station models with one animated clock/skeleton implementation; eight building
models using palette-fade callbacks; tool, fan, and pinwheel display selectors;
and move-only sound callbacks. These are category candidates, not approved static
substitutions. In particular, station clock hands and animated parts must remain.

## Collision and placement categories

The collision/placement cartridge is ABI 87:
`build/v3-furniture-placement-runtime-01/animal-forest-v3-asset-loader.z64`.
The same importer installs grass model `30E8`, dirt model `30F0`, and boxing
mat `3348`, retaining all 2,768 object bytes, 44 vertices, 24 triangles, textures,
and the donor's `0010` no-collision flag. Official name credits are in the single
provenance catalogue. Automatic additions total nineteen; the offline composer
contains 81 installed options: 58 furniture, three shirts, and twenty villagers.

Inspection identifies five native readers still indexing the original 947-entry
placement-layer table with imported indices. This can read unrelated data and
lose surface behaviour. The shared fix preserves the original prefix and adds
source-derived rows for every installed furnishing and all three clothing display
aliases. Four imported surfaces (teacher's desk, orange box, chess table, and
ringside table) and five surface-placeable objects (garden gnome, cow skull,
lantern, Luigi trophy, and Mario trophy) now have explicit correct categories.
Other imported furniture has category zero. No item-specific runtime branch is
added. The complete native collision-registration routine is unchanged except
for its corrected table address, preserving its ordinary-room/shop distinction.

The 2,051-entry table and guards occupy `804741F0..80474A1F` in the unused
registry-to-artwork gap. The five actual HI/LO pairs are at
`8093825C/80938268`, `80943878/8094387C`, `80943978/8094397C`,
`80943A34/80943A40`, and `809462C8/809462D4`. Ten obsolete relocations are
removed. All other native owner bytes and accessory records/artwork remain.
There is no added executable code, resident allocation, or saved-format growth.

- ROM SHA-256: `004a1173c51cdea009c3a5e291067469675d40809002bf8fd41d99f28f671c1d`.
- UPS SHA-256: `df73ad1e2f7c8f010bd6016356a2d03b333d4295de4bb8d04c44cc286906c999`.
- Receipt SHA-256: `64805f9215d264303347fc40842f5fa6b15d2c549453f3e6c5b7ac654b1e85ec`.
- Import-resource SHA-256: `c328b130c6bb338de7582f24ceb6f3b741769427477e5c237a7a9b5c53665a58`.
- Placement-table SHA-256: `9f6d51793f058d2b8ebe8952a4369fd4a7b5d48eb19c9998333b885aac89ef01`.
- Native owner SHA-256: `ca540a6f48fa15fb8bfad4d36abf77bb3d318799732d965f278063207f64b74a`.
- Relocation SHA-256: `c97bc9e48c97a6830145218f5fcdcaa664a7611167b2f013bc93d75f4e493bc5`.

The blob contains 3,116,400 bytes, with 1,012,368 bytes remaining before English
choices. The catalogue has 494 furniture rows and 248 clothing rows; conservative
menu memory remains 280,384 of 280,704 reserved bytes. All 28 focused pipeline/
composition tests pass. They include every converted texel/vertex/triangle,
unknown interaction/placement rejection, source-derived table entries, all five
retargeted references, complete relocation comparisons at two load addresses,
unrelated-owner retention, repeat-batch reuse, and save-profile composition.
The first silent native run passes 125 records and 107 assertions, including
the complete placement table/guards, native owner loading/relocation, actual
no-collision registration for all three new objects, complete model DMA,
one-/two-cell rotated footprints, names, prices, stock, catalogue eligibility,
acquisition, ownership, restored state, and guards. The existing four sound
routes also pass. The emulator exits cleanly; no native setup retry is needed.
Results are in `build/v3-furniture-placement-native-01/results.json`, SHA-256
`5757a4b7580348303195455ae9c1b5b17e425a3bafa18cfc19c549673a7e733a`.

Ordinary room appearance, table use, walking across the collision-less objects,
and save/restart remain unverified. Saved format 2 is unchanged and the profile
extends ABI 86; no ordinary cross-version reload is newly claimed. Saves using
the three new objects must not be loaded in older builds or V2. Neither served
patcher changes.

## Shared seating category

The seating-category cartridge is ABI 86:
`build/v3-furniture-seats-runtime-02/animal-forest-v3-asset-loader.z64`.
The automatic pipeline adds lawn chair `324C` and teacher's chair `3288`
without an item definition, dedicated installer, or separate native scenario.
Their 7,872 bytes retain all 163 vertices and 81 triangles. This brings the
automatic additions to sixteen and the offline composer to 78 installed options
(55 furniture, three shirts, and twenty villagers).

The category extension also supplies the donor's correct soft-chair sounds for
lawn chair and hard-chair sounds for teacher's chair, lefty desk, and righty desk.
Byte 25 of each existing item record stores its source-derived category. All
installed furniture is populated from the actual donor table, including entries
with no action sound. No per-item runtime branch or separate audio import is
needed. Full sound programs, timing, complete instruments, envelopes, samples,
loops, and predictors match native audio; matching sound numbers alone are not
the verification. Original native items retain their original reader body.

The helper is 208 bytes at `80483D00`, before the fire vtables at `80483FC0`.
The installer verifies the existing fire code and empty intervening bytes;
linker limits also prevent shared item/tent/fire/behaviour overlap. The helper
uses a bounded 32-byte stack frame and no new permanent RAM or audio resources.
The catalogue contains 491 furniture rows and 248 clothing rows. The resource is
3,049,104 bytes, with 1,079,664 bytes remaining before the English-choice region.

- ROM SHA-256: `e6f334027c352039fededafe8672d7ff480b5234bad914646b4beeffad00d1ab`.
- UPS SHA-256: `b20ac5cf1f0bc6452a3ec38b76d15ab76d5e215e9112fd81d0c912af42ce6d40`.
- Receipt SHA-256: `b3f9a540d3426a87dad66cc7eec0732fef38283b72de4fc312b87fd75eee4b54`.
- Import-resource SHA-256: `2963fa39c0886ac784b3b6ed842e8dc6a8c88cef65c7b4909868a7debbeefff5`.
- Native result: `build/v3-furniture-seats-native-01/results.json`, SHA-256
  `33895a6070a9e352a7fc663f22c4fc5b1e45d84eaed84919005199c897733f4c`.

All 26 focused pipeline/composition checks pass. The shared sound implementation
passes address/undefined-behaviour sanitizers for original delegation, complete
import index bounds, modes, categories, metadata identity, and disabled records.
The first silent native run passes 88 records and 73 assertions: complete helper
loading, original fallbacks, both modes for all four imported sound routes,
disabled-profile rejection, invalid indices/modes, complete chair model DMA,
names, prices, stock, catalogue eligibility, acquisition, ownership, restoration,
and guards. No audio is played through the user's speakers/headphones.

The initial installer attempt stops at a missing shared compiler-entry mapping;
the mapping is added and the completed build passes. There is no native setup
retry. Ordinary sitting, audible playback, GPU appearance, transactions, and
save/restart are not established by these component checks. Saved format 2 is
unchanged; the new profile is a superset of ABI 85, but ordinary cross-version
reload is not newly tested. Saves containing the new chairs must not be loaded
in an older cartridge or V2. Neither served patcher changes.

## Initial automatic batch

Source revision `7149f9c` discovers and installs fourteen new items in one
batch, without an item-specific converter definition, stock/catalogue switch,
installer, or test scenario. The complete command is:

```sh
python3 tools/v3_furniture_pipeline.py import \
  --base-lock tests/fixtures/v3-furniture-pipeline-base.json \
  --output build/furniture-reproduction
```

The recorded run used the same pinned input through the current-build lock
before that lock was promoted. The final output is
`build/v3-auto-furniture-final-01/animal-forest-v3-asset-loader.z64`, ABI 85.
The one-command output in `build/v3-auto-furniture-02/cartridge/` has the same
complete ROM and patch hashes. The final rebuild adds reusable predecessor/art
locations to the receipt; it does not change any cartridge bytes or require
another native run. The folder name identifies this implementation batch,
not a finished V3 release.

- ROM SHA-256: `571e849108cf36983c7129a38d08bfc3b47dd71db5c4347cfe16b7425b1ed35c`.
- UPS SHA-256: `d9283d2908b779694ee584889d5f1559523159bbc3f8ae4512d368bf11d664f5`.
- Final build receipt SHA-256: `9f1df24e3e98f4972afc7c38720f91947afe6417082a79d13bdeee3959b80166`.
- Appended import resource: 2,976,720 bytes, ending at VROM `024D6BD0`,
  leaving 1,152,048 bytes before the reserved English-choice resource.
- Models: 50,064 bytes, 1,038 vertices, and 570 triangles, with complete textures
  and palettes. No donor artwork is truncated or replaced with a placeholder.
- Catalogue: 489 furniture rows and 248 clothing rows. The compiled suffix is
  3,424 bytes; conservative menu memory is 280,384 of 280,704 reserved bytes.
- No additional permanent RAM, model-bank allocation, or saved-format growth.

Imported records: track model `30EC`, train car model `30F4`, orange box `30F8`,
merge sign `31EC`, radiator `3248`, chess table `3250`, cement mixer `325C`,
jackhammer `3260`, potbelly stove `326C`, flip-top desk `3278`, Luigi trophy
`32C8`, Mario trophy `32CC`, boxing barricade `3338`, and ringside table `334C`.
Names have generated official-source entries in `translations/provenance.json`.

The offline composer resolves 76 installed development options. The concrete
subset `build/v3-optional-auto-furniture-01/` selects radiator, Mario trophy,
and ringside table without other new furniture, ROM SHA-256
`a973cee3a9e2f24adca32dd95e766c6a94e5d965da52805a8562aff558ab6453`.
Empty selection reproduces V2; all selection reproduces the complete cartridge.
Neither served patcher changes, and this is not a public-release handoff.

### Initial batch verification

Seven shared format/donor tests, five current-cartridge tests, and twelve
composition tests pass: **24 focused tests**. Checks cover every new texel,
vertex, and triangle, actual source relocations, retained material commands,
complete installed assets/profiles, official names, stock membership, scoring,
catalogue order, ROM checksums, full/empty/subset selection, and saved-profile
requirements. The shared catalogue reader passes address/undefined-behaviour
sanitizers across its bounded index/list/category/rotation cases.

The initial native attempt stops before emulation because `Xvfb` is not on PATH.
The one corrected retry explicitly uses the existing executable:

```sh
python3 tools/emulator_smoke.py \
  --rom build/v3-auto-furniture-final-01/animal-forest-v3-asset-loader.z64 \
  --output build/furniture-native-reproduction \
  --scenario tests/scenarios/v3_furniture_batch.json \
  --xvfb /home/discordian/Games/OpenRSC/headless/vendor/usr/bin/Xvfb \
  --seconds 180 --expansion-pak --no-initial-screenshot
```

`build/v3-auto-furniture-native-02/results.json` passes **148 records and 133
assertions**, SHA-256
`d97bcd43bf3a6665c0e63f1d87a3e9cb99b7500d5c394acb6887e40f286e44f7`.
The manifest chooses train car model, Luigi trophy, Mario trophy, flip-top desk,
jackhammer, and ringside table to cover A/B/C, event, lottery, one-/two-cell,
and model-layer categories. Actual owner loading/relocation, names, prices,
rotated footprints, complete upper-memory model DMA and untouched tails, bank
assignment, stock membership, catalogue eligibility/rejection, acquisition,
saved ownership, restored state, and guards pass. The emulator exits cleanly.
No existing save is used and no test FlashRAM write is requested.

Ordinary room appearance, GPU rendering of these new models, transactions,
interactions, and save/restart remain unverified. The preceding full profile is
a subset of this profile; the codec accepts equal/superset requirements, but
ordinary cross-version reload is not newly tested. Do not load saves using the
new items in an older build or V2.

## Category queue

The donor worksheet contains 242 canonical 3xxx entries. This converter supports
43 under its present complete category rules, all installed. The post-install
scan identifies no remaining supported,
uninstalled entries. This is **not** a whole-project completeness percentage.
The other 199 entries include already-installed special adapters and explicit
identity/unused cases as well as genuinely missing imports.

Continue through shared feature categories, not individual item queues:

1. Shared callback families: 102 uninstalled entries stop on custom callback
   tables. Classify the actual callback/dependency patterns and implement shared
   behaviour adapters; never discard callbacks to fit the static category.
2. The supported `0010` flag exposes further dependencies: sixteen diary display
   models need diary identity/gameplay/acquisition; weed model needs the shared
   `ftr_listEventPresentChumon` reward route. Neither is a completed static import.
3. Acquisition categories, special preview framing, and graphics variants:
   extend reusable adapters for the inventory's explicit reasons. Some items
   need combined features; clearing one reason need not make the item complete.

No more bespoke furniture installers or item-by-item metadata definitions are
the default development path. The legacy scripts remain as reproducibility
records; new supported items flow through the shared pipeline.
