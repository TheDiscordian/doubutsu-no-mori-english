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
and verifies the 6,812-byte shared code packet into the reserved
`804B5000..804B6FFF` range, flushes the instruction cache, and records the verified
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

The explicit ABI-153 proposal is `build/v3-shared-tree-world-02/build-lock.json`.
It uses an 8,192-byte fixed reservation and 32,864 bytes per loaded seasonal owner.
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
The current packet includes hidden-content and world queries and occupies 7,516 bytes.
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
The packet occupies 7,516 of its reserved 8,192 bytes. The bootstrap remains
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

## Remaining gameplay integration

Reuse the installed renderer, planting conversion, tree-state helpers, and daily
growth/death/neighbour/thinning, hidden-content, and world-query consumers.
Full cutting/shaking, the planting sparkle, and the selected shovel drop remain
required. The source plants an ordinary shovel in a shining hole; do not
substitute shop stock, arbitrary letters, recoloured ordinary trees, or seeded
pockets for this route. Existing celebration and collection consumers remain
installed, but all four golden choices stay disabled until their routes work.

The [checkpoint](../docs/checkpoints/V3_FURNITURE_PIPELINE.md#shared-seasonal-scenery-preparation)
records resources and focused checks. Component checks do not establish
gameplay, rendered appearance, persistence, or original-hardware verification.
