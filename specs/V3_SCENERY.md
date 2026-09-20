# V3 shared seasonal scenery

## Scope and workflow

Scenery is an engine dependency, not another item checkbox. The golden shovel
requires the donor's actual gold-tree planting, growth, and shake/drop route.
Prepared artwork does not enable that route or its item choice.

`tools/v3_scenery.py` follows source foreground tables into complete drawing
descriptors, body lists, and shadow dependencies. It feeds the shared model
converter and compiler; there are no per-season converters or item installers.
The initial `gold-tree` category discovers descriptors by source family and
obtains foreground IDs from the complete type tables.

```sh
python3 tools/v3_furniture_pipeline.py scan --representation scenery \
  --output build/scenery-inventory.json
python3 tools/v3_furniture_pipeline.py convert --representation scenery \
  --category gold-tree --assets-only --output build/scenery-assets
```

Use fresh ignored paths. `import`, conversion without `--assets-only`, individual
item selection, and unknown categories reject. Neither this adapter nor its
output edits a cartridge, save, build lock, or served patcher. Furniture and
equipment installers reject the distinct scenery bundle format.

## Complete source graph

The pinned GAFE01-r0 REL and symbols remain mandatory. Source owner order is
cherry, ordinary, winter, Xmas; native order differs and must be matched by
identity during installation. Twelve-byte foreground rows supply the drawing
index and both position arrays. Thirty-two-byte descriptors supply complete
display-list tables, ordered body lists, and optional shadow vertices,
adjustment flags, lengths, and draw lists. Body/shadow callbacks must match the
checked complete consumers. Missing or unused dependencies, unexpected fields,
and unsupported callbacks reject.

The gold-tree category contains fourteen foreground identities per season:
`007B..0081` and `0863..0869`. Ten descriptors per owner represent five growth
sizes, a dead sapling, and four stump sizes. The mature model is shared by its
reward/spent and hidden-content states. The adapter retains all 52 body-list
uses and 24 shadow-list uses, deduplicated to 37 complete material/geometry
pairs. Xmas shares winter graphics. Source positions, shadow adjustments,
callback bindings, and source/output hashes remain in the generated reports.

## Caller-supplied graphics state

The shared converter accepts explicit `render_context` contracts:

- `palette_slot`: the caller loads this palette. CI4 materials must select
  exactly that slot. Missing, overwritten, conflicting, and unused contracts
  reject. Ordinary models retain local palette loading and slot fifteen.
- `external_vertices`: one complete source array, up to 32 vertices, loaded
  by the caller before geometry. Its full contents are converted and preserved;
  every triangle is checked against its bounds. Embedded replacement vertex
  loads reject. Shadow geometry does not load static vertices over the caller's
  adjusted vertices.

Material and geometry validate together, then compile into independent lists.
Body ordering remains material → instance matrix → geometry. Shadow ordering
remains material → shadow colour → instance matrix → adjusted vertices →
geometry. Caller-owned colour, matrices, and adjustments are not guessed.

Gold body materials use palette slot eight. The field palette initializer uses
the original eighteen-term selector and all fourteen sixteen-colour palettes.
All 448 bytes convert from RGB5A3 to RGBA5551; partial alpha rejects instead of
being discarded. Six shadow pairs retain complete four-vertex source arrays,
I4 textures, and wrapping.

## Runtime installation and ownership

`tools/v3_scenery_runtime.py` installs the prepared category through the shared
runtime refresh. It validates the complete source graph and prepared resources;
it does not reconvert the models or add individual-item definitions.

```sh
python3 tools/v3_furniture_install.py --refresh-runtime \
  --scenery-art build/v3-scenery-gold-tree-01 \
  --base-lock build/v3-shared-balloon-menu-04/build-lock.json \
  --output build/scenery-runtime
```

Each seasonal owner owns one 32,864-byte bank appended to its BSS. The nineteen
objects retain complete vertices, textures, material/geometry lists, descriptors,
position arrays, and adjusted-shadow dependencies. Three cartridge banks cover
the four owners; Xmas shares winter. Verified retired module copies supply
cartridge storage, with explicit live reservations preventing subsequent reuse.
The import blob and its DMA identity do not grow or overlap English choices.

The equipment module retains its size and guards. Its
`804ADC90..804ADFEF` range contains an 848-byte bootstrap and native fallback
stubs, bounded before the retained guard at `804ADFF0`. A four-byte cache word
at `804ADFEC` starts clear in the startup-loaded module. The bootstrap transfers
and verifies the 8,544-byte shared code packet into the reserved
`804B5000..804B7FFF` range, flushes the instruction cache, and records the verified
CRC. Constructors then prepare the native/held table and load the active scenery
bank. Tree queries can load the same packet before any seasonal actor exists;
later calls reuse it without repeating the transfer. A missing
or corrupt resource enters the existing fault reporter instead of constructing
an actor with invalid pointers. The five added diagnostic strings are credited
to the assistant in the single text catalogue.

The bank's 128-byte header records separate CPU, graphics, and callback fixups;
all pointers are offsets before loading. CPU pointers acquire the owner's
address; graphics pointers become physical segment-zero addresses. Callback
roles bind to the loaded owner's original shadow loop and the shared body
wrapper. No heap address persists between scene loads. Complete fixup bounds
are checked before relocation. Graphics retain source order and slot-eight
palette selection. The body wrapper follows the native eighteen-term calendar,
refreshing the active 32-byte palette when needed before calling the original
body loop. Caller-adjusted shadow vertices are not replaced by static vertices.

Ten previously unused descriptor slots hold the category: `65..74` for cherry,
ordinary, and Xmas, and `64..73` for winter. Original rows, the NONE sentinel,
all installed held-item rows, actor sizes, stack frames, and existing copy
capacities remain intact. Further category expansion must respect the scenery
owner records' reserved slots; zero category-map entries are not blanket proof
that those drawing indices remain free. Native foreground tables contain 112
low and 84 environmental rows. All fourteen imported IDs lie outside those
existing ranges; no original scenery identity is replaced.

The owner-local classification entry preserves the native routine through a
cache-flushed trampoline. Selected golden-shovel profiles resolve the complete
new type/position records. Original items call the native routine, retaining the
held-category hooks. Disabled imported foreground IDs resolve the native empty
row rather than indexing beyond a native table. Save/profile restrictions still
apply; this fallback does not authorise removing imports from a saved world.

The explicit ABI-154 proposal is `build/v3-shared-tree-interactions-04/build-lock.json`.
It uses a 12,288-byte fixed reservation and 32,864 bytes per loaded seasonal owner.
All existing 128 experimental choices and format-3 saves remain unchanged.
The main ABI-109 lock and both served V2 patchers stay unchanged. Component tests
cover native loading, all seasonal type bindings, actual body-list generation,
guards, and restoration; rendered appearance and ordinary gameplay are not
claimed.

## Shared planting and tree-state rules

The shared installer's `--refresh-runtime --scenery-gameplay` stage consumes the
installed seasonal category. Complete donor growth, stump, and four burial
consumers are hash-bound. Growth and stump records come from the donor's actual
tables, including growth caps and mature/spent stability. No item-specific
installer or selectable scenery identity is added.

All four native burial callers use the shared adapter. A normal shovel (`2202`)
buried in a shining hole (`005D`) becomes a gold-tree sapling (`0863`) and returns
the native planting action, only when the golden-shovel profile is selected.
Other items/holes and unselected profiles use each loaded owner's complete
original burial routine. The call's internal relocation is removed; the native
routine remains intact. Fruit, seed, money, and pitfall processing are retained.
The existing native caller still owns foreground placement and planting animation.

Core growth at `800A5970` and stump conversion at `800A56F0` dispatch through the
lazy loader. Gold stages use the actual six growth records and four stump sizes;
hidden mature states use the full-sized stump. All other families execute their
complete original routines through fixed prologue stubs at `804ADFC0` and
`804ADFD0`. Negative elapsed days do not grow the tree; zero means one growth
step, matching the donor helper's inclusive loop. Stable states stop immediately
instead of iterating over unchanged days. The stump flag retains its signed
sixteen-bit semantics.

The planting/state stage consumes existing packet and bootstrap reservations.
It adds no RAM, scene allocation, save/profile field, public diagnostic text, or
browser choice. The daily-growth stage below extends the shared code reservation.
Host sanitizer tests cover boundaries, all native fallback IDs, and output
guards. Cartridge checks cover original code retention, complete donor tables,
relocation, storage, optional composition, and UPS reconstruction. A silent native
component check verifies lazy loading without an actor, actual core dispatch,
all four relocated burial helpers, native fallbacks, guards, and restoration.
It does not execute the full ordinary planting interaction or establish daily
growth, collision, rendering, save/restart, or hardware behaviour.

## Daily growth, death, and overcrowding

The subsequent `--refresh-runtime --scenery-gameplay` stage connects the actual
daily owner, `m_all_grow_ovl` at VROM `00970920`, relocation `009754A0`, linked RAM
`80AB07C0`, and loaded pointer `80100C5C`. The native loader and owner dimensions
remain intact. Its renewal entry loads/verifies the shared packet, then resumes
the exact displaced prologue. Every existing imported-house protection remains.

Nine complete donor functions and seven native functions bind the rules and
calling conventions. Five native call/table references use shared adapters:
neighbour checking, the ordinary plant callback, initial sapling recording,
surviving-candidate counting, and acre thinning. Their internal relocation
records are removed; the original native functions remain for fallback. Native
families keep original growth, flower, and environment processing. The donor's
gold-family condition is independent of its added island/cedar height fields;
those unrelated subsystems are not imported implicitly.

Gold stages grow through the existing source table, die on plant condition zero,
clear on condition minus one, and clear as dead saplings on the next applicable
update. Source elapsed-day semantics and stable mature/spent forms remain.
Saplings check four orthogonal neighbours, including provided adjacent-acre
arrays. Odd/even cell rules govern adjacent saplings. Native trees and gold
trees/stumps block each other without changing a neighbour's identity. The
original acre-pointer setup and native non-gold neighbour behaviour remain.

The same pre-growth sapling bitfield includes gold saplings. Dead gold entries
leave that candidate set; surviving gold candidates count with other non-ordinary
trees. The 32-tree acre limit includes all gold growth/hidden states, keeps
ordinary-tree removal priority, and uses the actual native random generator for
each removal. Gold candidates become the gold dead-sapling identity. The source's
eight-bit tree/candidate counters, including their full-acre wrap, remain intact.
Existing native routines handle unselected profiles.

Daily growth requires an 8,192-byte reservation, 4 KiB beyond tree-state loading.
The daily-growth stage uses 8,192 bytes; the interaction stage extends that
reservation to 12,288 bytes for its complete 8,232-byte packet.
The bootstrap still occupies 848 bytes. All complete scenery banks, daily owner
and relocation sizes, equipment module, save/profile fields, and choices remain
unchanged. Existing reserved retired cartridge storage holds the larger packet;
no import-blob or seasonal allocation grows.

Host sanitizer checks cover growth/death, day/cap boundaries, all four neighbour
directions and acre boundaries, native fallback, recording/counting, removal
priority, RNG selection, source counter width, and bounded writes. Cartridge
checks cover complete source contracts, retained native code/house protections,
actual relocation, storage, UPS reconstruction, and optional composition.
The native component check executes the real renewal dispatch with its non-field
early return, then the daily consumers on isolated acres. It verifies loading,
growth/death, mixed native/imported neighbours, cross-acre rules, actual RNG
thinning, guards, and restoration. Full live-town renewal, ordinary acquisition,
save/restart, rendered appearance, and original hardware remain unverified.

## Hidden contents and daily refilling

The same daily-owner refresh connects recording, counting, and random replacement
through eight existing calls/table references. Four internal relocation records
are removed; calls to original core helpers have no internal relocation. Original
record wrappers retain native `GrowInfo` offsets, and both daily callback arrays
use the new Bell-tree counter. The complete bee, furniture, and Bell schedulers
remain native, preserving the five-column town layout, five bee trees, two
furniture trees, thirty Bell trees, occupied-column records, and random draws.

Thirteen complete donor functions and all four three-family tables bind source
identities and selection rules. Nine complete native owner functions plus the
complete core count/change helpers bind native consumers. Only ordinary trees
and selected spent gold trees (`0868`) are eligible. Replacements preserve their
family, with gold Bell/furniture/bee identities `007F/0080/0081`. Shovel-bearing
trees (`0867`), saplings, dead trees, and existing hidden contents are not refill
candidates. The GameCube cedar column remains documented source data; this
gold-tree dependency does not implicitly change native cedar behaviour.

Existing hidden gold contents contribute to the native records and totals.
Refilling uses the source's one random choice per changed tree, retaining native
eight-bit acre counts. Unselected profiles and unrelated target kinds use native
behaviour. Core helpers themselves remain untouched, preserving holiday users.
No additional memory, owner allocation, save/profile field, or choice is added.

Host sanitizer tests cover every sixteen-bit identity, selected/unselected
records, guarded writes, mixed-family selection, protected trees, null acreage,
counter widths, and fallback. Cartridge checks cover actual references and
relocations, full native scheduler retention, memory reservations, unchanged
artwork/saves, optional composition, and original-ROM patch reconstruction.
The silent native component check executes actual recording and refill routines
on a temporary mixed grove. It verifies native quotas/distribution, both tree
families, duplicate prevention, native RNG, source identity retention, guards,
and complete world/RNG/profile/checkpoint restoration. No user save is modified.
Full renewal, ordinary shaking/drop, rendered appearance, and hardware remain
unverified.

## Collision, removal, and NPC walkability

The shared scenery gameplay refresh connects three complete native core entries:
collision at `8006C980`, shovel-removal eligibility at `8008C964`, and NPC
walkability at `8008D7B0`. Three complete donor consumers and actual source
dimension constants bind the adaptation. Original core functions remain intact
beyond their displaced prologues, with checked incoming branches and packet-local
fallback stubs. Existing core callers and the removal callback table stay native.

One resident assembly gate retains all four argument registers and the original
stack arguments across lazy loading, then tail-dispatches into the packet. The
native collision API has five arguments; it does not use the donor's callback
and coordinate API. Its inclusive exclusion range is checked against the real
foreground identity before mapping geometry. A temporary complete 48-byte unit
copy selects matching native dimensions and terrain processing for twelve solid
gold-tree/stump states. The real unit and saved foreground are never rewritten.
Sapling and dead-sapling states have no trunk column. Native and unselected
identities retain their original routine and exclusion semantics.

Selected gold saplings, dead saplings, and four stump sizes are removable with
the shovel; solid growth and mature states are not. Only the first sapling state
adds NPC walkability. Position arguments and native fallbacks are retained.
The world-query stage occupies 7,516 of its reserved 8,192 bytes. The bootstrap remains
848 bytes, with unchanged cache/guard/fallback addresses. Seasonal and daily
references are rebound to current code without changing owner sizes, resources,
scene allocations, saved formats, or choices.

Host sanitizer checks cover every sixteen-bit identity, selection, exclusions,
original-unit preservation, argument forwarding, and bounds. Cartridge checks
bind complete source/core functions, displaced prologues, owner rebindings,
relocations, memory limits, full patch reconstruction, retained save data, and
exact V2-12 import-free output. The first silent native run uses actual terrain
calculation and core entries, verifies all twelve solid states against complete
native geometry, and checks removal, walkability, exclusions, lazy loading,
guards, and full state/checkpoint restoration. No terrain or gameplay helper is
stubbed in that fixture. It does not establish ordinary player interactions,
rendered appearance, save/restart, or original-hardware behaviour.

## Seasonal shake/drop and axe-hit initialization

The subsequent shared gameplay refresh extends the native drop routine instead
of replacing its landing engine. All four complete donor drop/bee/cut consumers
and complete source tables are bound. The native thirteen-row drop prefix matches
the donor exactly; four added records supply gold Bells (`007F`), furniture
(`0080`), bees (`0081`), and the shovel-bearing state (`0867`). Every gold drop
has count one and leaves the spent gold-tree identity (`0868`). The shovel drop
is the actual installed golden shovel (`223B`), not a substitute acquisition.

A selected-profile table span exposes seventeen rows; unselected profiles retain
the original thirteen. The original loop, random furniture selection, placement
routine, coordinates, and foreground setter remain. Existing held-item landing
hooks remain intact. Gold Bell trees share native money-luck upgrading, while
other Bell-tree counts retain their original treatment. The bee predicate includes
selected gold bees and preserves the argument register needed by the native
fallthrough. The original actor-creation, failed-creation position, and failed-
landing deletion branches retain their ordering and actual actor profile.

Nine original cut-count initialization calls use the shared adapter: two for
cherry, two for ordinary, two for Xmas, and three for winter. Each runs the full
native initializer, then overlays only the source's eight gold-tree records in
the transient 256-cell hit-counter array. Native counters and real foreground
identities remain unchanged. Source counts are one, two, and three for growing
trees, and three for mature/reward/spent/hidden states. Stumps and saplings do
not acquire axe-hit counters. Native hit decrement and core stump conversion
remain installed. Only corresponding internal relocation records are removed.

The packet is 8,232 bytes, requiring a 12-KiB reservation, 4 KiB beyond world
queries. Existing retired cartridge storage holds it without growing the import
blob. All shared seasonal/daily/core references bind the new packet addresses.
Bootstrap, equipment module, seasonal banks, owner sizes, scene allocations,
saved formats, source text, and browser choices do not grow or change.

Four focused checks cover sanitized rules across all sixteen-bit IDs, profile
selection, luck, immutable cells, native-count retention, complete source and
native consumers, all nine calls, relocation at two addresses, allocations,
complete patch reconstruction, saved formats, and exact V2-12 import-free output.
Native evidence is partial: the first fixture requests more contiguous heap
space than is available; a smaller bounded retry loads the packet and cherry
owner, checks selected/unselected cut counts, and executes all four gold drop
types plus money luck. Its actor recorder overlaps the deletion recorder, so a
subsequent assertion fails on the actor's recorded `-1.0` coordinate. The corrected
fixture is not rerun after the batch's setup-retry allowance is exhausted.
Field access, landing, furniture selection, terrain height, foreground commits,
and actor creation/deletion use explicit fixture doubles. This is not ordinary
acquisition, real actor/landing execution, complete seasonal native coverage,
final guard/checkpoint verification, or a hardware result.

## Remaining gameplay integration

Reuse the installed renderer, planting conversion, tree-state helpers, and daily
growth/death/neighbour/thinning, hidden-content, and world-query consumers.
Seasonal drop/cut counts and player targeting/shaking/bee predicates are installed.
Final stump acceptance and conversation-camera consumers are connected. Planting
sparkle, complete gold-tree leaf/cut effects, and remaining field/insect consumers
still precede full ordinary acquisition. The final axe routine accepts selected
gold stumps without changing their real saved identity. The donor
effect owner has gold-specific variants, status, resources, and leaf types;
do not pass unsupported variant indices to the native owner or substitute its
ordinary-tree artwork. The source plants an ordinary shovel in a shining hole; do not
substitute shop stock, arbitrary letters, recoloured ordinary trees, or seeded
pockets for this route. Existing celebration and collection consumers remain
installed, but all four golden choices stay disabled until their routes work.

## Shared player tree queries

Eight complete donor/native functions bind axe target selection, nearby-tree
search, touch sound, shovel reactions, shaking, axe drops, and common bee release.
The native category is extracted from the original complete predicates into
three-word bitmaps; all sixty original solid-tree identities and ten small-tree
identities remain. Selected gold stages extend the solid/shakeable predicates,
excluding saplings, dead trees, and stumps. Small gold trees remain solid without
acquiring the larger trees' touch sound. Bee predicates recognise native bees and
selected gold bees only. Unsupported donor palm/cedar families are not enabled.

Eleven call sites share one 364-byte gate inside a replaced player predicate.
Each delay slot is an inert `ori zero,zero,metadata`, identifying input register,
output register, and query kind. The gate preserves the other live integer
registers, HI/LO, and floating-point registers/control, and uses the existing
verified lazy loader before dispatching into the packet. Relative branches skip
the reclaimed code. Eleven new jump relocations append after the unchanged
original sequence: HI16/LO16 ordering must never be sorted by relocation type.
No actor/owner allocation grows, and the gate has a bounded 256-byte stack frame.

Existing target coordinates, height/distance/angle filters, original-item stores,
animation checks, callback permission checks, and five-frame bee timers remain.
Common bee and axe callbacks receive the real gold foreground identity. Axe
decrement/drop and core stump conversion return correctly; the final felling
predicate is extended by the following stage. The new packet fits
the existing 12-KiB reservation without changing resources, saves, or choices.

Four focused checks cover all sixteen-bit identities under both profiles,
complete source/native retention, exact relocation at two addresses, all eleven
call descriptors, storage, unchanged resources/saves, complete patch rebuilding,
and exact V2-12 import-free output. Native component evidence covers all actual
query sites and register preservation, lazy loading, common bee/axe consumers,
original identities, permission-controlled timer initialization, and restored
memory/guards/checkpoint. Drop and cut-count callbacks are isolated test stubs;
ordinary target selection, complete felling/acquisition, rendered effects,
save/restart, and original-hardware behaviour remain unverified. The checkpoint
records the partial initial fixture and focused corrected consumer retry.

## Final stump acceptance and conversation-camera limits

The shared gameplay refresh consumes the installed player-query receipt, verifies
every retained instruction and relocation, and rebinds the existing gate to the
new packet. Original relocation ordering remains intact. The additional query
at `808CA548` accepts native stump IDs `1..4` or selected gold IDs `007B..007E`.
It preserves `v0` as the real stump and returns the predicate in `a0`; the retained
native code carries that identity into its foreground update. The twelfth jump
relocation fits existing relocation padding. Owner and actor sizes do not change.

The complete donor and native height consumers and three twelve-byte records
are checked. Both already return the same neutral record for these stump IDs.
Core `800A5AC8` and table `8010B478` stay untouched; mapping gold IDs to substitute
native IDs is unnecessary. Terrain mutation and the native foreground setter
retain their original callers and argument order.

Four complete donor camera predicates bind the seasonal adaptation. Each native
predicate and complete move function is preserved except for the callback's
HI16/LO16 reference. The shared wrapper includes only the selected medium,
large, and full gold descriptors at `first_index+2..4`; every other index uses
the unchanged native predicate in its current loaded owner. The complete
prepared descriptor ordering supplies those indices. Two internal relocation
records per season are removed when binding the fixed shared callback.
Source cedar/palm families are not implicitly enabled.

Five focused checks cover sanitized predicates across every sixteen-bit ID,
camera selection and fallback argument forwarding, complete source/native
retention, player/seasonal relocation at two addresses, unchanged heights,
resource/save retention, exact UPS reconstruction, all experimental selections,
and the pinned V2-12 no-import output. Code occupies 8,824 of the existing 12,288
bytes. The checkpoint records bounded native execution and its limits; full
ordinary felling/effects/acquisition and hardware remain separate verification.

The [checkpoint](../docs/checkpoints/V3_FURNITURE_PIPELINE.md#shared-seasonal-scenery-preparation)
records resources and focused checks. Component checks do not establish
gameplay, rendered appearance, persistence, or original-hardware verification.
