# V3 creature parents and room displays
## Connected category

`tools/v3_creature_items.py` connects the carried identity, official name,
price word, item category, room placement, complete room profile, and pickup
identity for all seventeen additive creature records. It consumes the existing
shared prepared graphics; it has no per-species model definitions or installers.
The ordinary `creature-profile-assets` import category schedules this dependency
after embedded motion and creature audio. Partial source requests still install
the shared category; they do not select additional imports.

Native fish `2300..231F` and insects `2D00..2D1F` remain untouched. New carried
IDs are `2320..2328` and `2D20..2D27`. The donor's brook trout `2301` maps to
`2328`; native herabuna remains `2301`, with its existing `1C2C` room display.
The append-only parent registry is independent of selection order. Display
destinations remain the existing `3C98..3CD8` reservations.

Names come directly from the complete donor `itemName_fish` and
`itemName_insect` resources, with their existing entries in the single
`translations/provenance.json` catalogue. Price words come from the complete
sentinel-bounded donor price tables. These are the engine's price words, not
a second hard-coded sale-price list. Source placement/pickup functions establish
each parent relationship. Whole native conversion functions and the original
32-entry item-category tables are checked before hooks change.

## Native readers and room profiles

Five outer entry hooks connect names, item categories, prices, placement, and
pickup. Existing surface, equipment, clothing, and native readers remain the
predecessors. Both carried and displayed forms use the parent's name and price.
Placement resolves the carried ID to its room form; pickup handles all four
rotations and restores the carried ID. Native herabuna never enters this path.
Unknown extended fish/insect IDs and unavailable imported displays return zero
without indexing the native 32-entry tables.

Sixteen complete embedded profiles reuse installed rig resources and callbacks.
The static ant installs all three converted native drawing layers. Source scalar
fields and interactions are preserved, including full-height tanks/cages and
the existing creature audio/motion integration. No simplified replacement model
or independent furniture option is created.

Each profile is installed inactive in its canonical sparse slot. Metadata keeps
the parent relationship. The reader additionally requires readiness and the
selected native profile. Readiness, profile activation, and selection remain off
until carried models/icons, catching/releasing, collection/profile persistence,
and spawn readers are complete. Prepared room support is not a playable species.

## Memory and startup

The immutable 3,840-byte module occupies `804FF100..804FFFFF`, after the console
session reservation ending at `804FF020`, and before model banks at `80500000`.
Existing recorded allocations are checked for overlap. Code has 2,048 bytes;
the 492-byte table starts at `804FF900`. Its header is `AFCI`, version one,
count seventeen, and stride 28. Each row is:

| Offset | Field |
| --- | --- |
| 0 | Carried item, u16 |
| 2 | Display item, u16 |
| 4 | Source price word, u16 |
| 6 | Native category, u8: fish 8, insect 18 |
| 7 | Source species index, u8 |
| 8 | Readiness, u32; zero while gameplay is incomplete |
| 12 | Complete space-padded ASCII name, 16 bytes |

The final sixteen packet bytes contain four `AF435249` guard words. Startup
loads and checks the full packet before the native initialization chain. All
nine shared packet loads use the same DMA/checksum/cache-flush function. A
failed DMA or checksum stops initialization before executing unchecked code.
The bootstrap stays inside its existing 688-byte reservation. No saved layout,
profile bits, or actor sizes change.

## Verification and remaining work

`tests/test_v3_creature_items.py` checks source identities, complete installed
profiles/resources, five hook targets, preservation of the native conversion
bodies, UPS reconstruction, retained saves, and optional all/empty composition.
Sanitized C checks exercise names, prices, categories, placement/pickup with
rotations, readiness/selection rejection, output bounds, native fallbacks, and
the checked startup chain including DMA/checksum failures.

Ordinary native execution of this connected path and original hardware remain
unverified. The scheduler test's unexplained debugger disconnect remains open;
host checks do not classify it. Field/carry model loading, drawing tables, fish
capture identities, and release adapters are installed as described below.
The active queue continues with field behaviours, spawn readers, pocket icons,
and collection/profile persistence, retaining the completed room and sound work.

## Field and carried graphics

`v3_furniture_pipeline.py convert --representation creatures --assets-only`
prepares the complete seventeen-species field-frame category through the common
resource parser, material conversion, and one batch compiler invocation.
`tools/v3_creature_field.py` follows the donor's actual model-pointer arrays;
it does not define models by species name. All three fish consumers must agree
on their complete frames. Two-, four-, and six-entry insect frame arrays retain
their repeated poses and ordering. The result contains 59 frame references to
43 distinct models, 25,504 bytes, with no independent creature-display choices.

The common converter supports a different complete vertex array per model in
one object. Each model still requires exactly one bounded vertex array; arbitrary
cross-array loads remain unsupported. Textures and palettes shared by frames
are stored once. The insect colour expression preserves texture alpha multiplied
by environment alpha, primitive colour, and second-cycle shading. This keeps
the drawing caller's fading controls rather than making the insects opaque.

The prepared category retains both independently sourced fish animation selectors,
both complete frame sequences, height corrections, and insect behaviour indices.
Field and release selectors are not interchangeable: jellyfish and several sea
fish use different selectors. The largest converted fish is 2,192 bytes, within
the native 2,560-byte fish buffer; every added insect fits its 3,072-byte buffer.
These sizes describe complete converted objects, not estimates from donor size.
The shared native stage installs these assets without recompiling them. That
integration does not make the species selectable while field behaviours, spawn
readers, pocket icons, and collection/profile persistence remain unfinished.

### Connected native field stage

`tools/v3_creature_field_native.py` installs all seventeen complete frame objects,
field and release lookup tables, source animation selectors and height correction,
fish capture identities, release mapping, size parameters, and bounded XXL
shadows. Added insects retain source held poses and world rotation order,
including mole-cricket Y/X/Z and the spider's frame-specific X/Z path. Original
insects retain their native transforms. Source timing arrays remain independently
bound for field and release; neither is substituted for the other.

Added fish use actor slots `36..44`, corresponding to carried IDs `2320..2328`.
The complete original 36-slot capture mapping, including rubbish and coastal
salmon, is preserved. Brook trout does not replace native herabuna. Added insects
use slots `32..39`. Readiness and selections remain disabled until the complete
gameplay paths can safely consume these identities.

The immutable packet occupies `80647000..80649FFF`: 12,288 bytes, including
1,018 compiled code bytes, 3,830 lookup-table bytes, resource descriptors, and
guards. Expanded pointers target this resident packet; their obsolete overlay
relocations are removed. Five actor owners keep their original code/data/BSS
dimensions and allocation lifetimes. No scene-buffer enlargement or new native
DMA-directory entry is necessary. Shared startup is 532 of its 688 reserved bytes.

Only the 25,504 bytes of added models occupy an externally allocated physical
ROM resource. Original banks stay in place. The checked loader retains native
DMA for original bank spans and uses synchronous PI transfers with exact
descriptor, size, capacity, and CRC checks for added objects. Display-list
segment-six references are rebased to the native bank-offset convention; native
loaders still publish the matching segment base. The complete ordinary import
file has 49,280 bytes remaining below `2800000`.

The source supplies the XXL scale but lacks a seventh release-shadow correction.
The adapter explicitly extends each correction array with its largest defined
entry. This prevents the donor's out-of-bounds read without changing any existing
fish correction; it is a documented safety adaptation, not a selectable bug.

The ordinary category planner schedules field integration after the parent/room
stage, accepts the prepared field cache alongside room caches, and skips installed
stages. No per-species installer or independent furniture choice is added.

`tests/test_v3_creature_field_native.py` covers all resource and relocation changes,
native capture identities, retained golden-rod hooks, save/profile retention,
category planning, UPS reconstruction, and all/empty composition. Sanitized C
covers all seventeen transfers, native fallbacks, CRC/I/O/bounds failures, the
nine-packet startup chain, and original/added insect transforms.

Native execution verifies the complete startup-loaded packet, relocated fish
owner/BSS, and all nine added fish transfers and segment bases. The constructor
register window times out before later assertions. Its cause remains unresolved;
this result does not establish native insect transfers, capture/release execution,
ordinary gameplay, or GPU rendering. Retain the test limits and the independent
unclassified scheduler disconnect. Hardware remains unverified.

### Shared fish world readers

`tools/v3_creature_fish.py` installs both complete field parameter tables and
source-sized river/coastal readers as one category stage. Native owner dimensions
and all original golden-rod hooks remain intact. Every native river size array
gets the donor XXL entry; existing effect switches map XXL to their largest
defined effect, which matches the source's XXL splash/ripple values.

Added coastal fish use source approach/nibble speeds, touch distances/counts,
backing speeds, shadow scales, bobber offsets, rubbish classes, splash radii,
and splash/ripple arguments. Full river and coastal donor arrays must agree
before shared values are installed. Complete donor callback receipts bind the
two source switches and the consumers. Native timers retain the N64 30-Hz units.

The fish constructor writes an imported-origin marker in unused transient
padding at `1DA`, immediately after the size halfword at `1D8`. Checked native
owners must leave that byte unused. The marker survives a fish's substitution
with rubbish, so its original size-dependent behaviour remains available.
Original fish retain native coastal values; source-sized parameters do not
silently rebalance them. This is not the complete source coastal patrol/shoreline
port. That substantial shared behaviour difference still requires both runtime
alternatives and the explicit WebUI choice, not a nonfunctional toggle.

Both native fish-to-release actor creation calls translate actor indices through
the installed capture-identity table. Original rubbish slots `32..34` become
their real carried IDs `250E..2510`, while added fish `36..44` become `2320..2328`.
The release constructor reverses those identities without confusing a can with
a crawfish. Coastal salmon and native herabuna retain their original identities.

The 1,500-byte code occupies `80647400..806479DB`, inside the field packet's
reserved code padding. The 428-byte table region begins at `80649400`. No new
resident packet, scene allocation, DMA entry, model resource, or saved field is
introduced. Native data pointers retained inside rewritten constructor code keep
their relocations; references to resident tables and hooks do not.

`tests/test_v3_creature_fish.py` covers sanitized position/approach execution,
all native fallbacks and size bounds, source table bindings, complete owner
changes and relocation removal/retention, unchanged golden-rod hooks, category
planning, UPS reconstruction, and optional all/empty composition. Assembly-hook
execution is not inferred from those host checks. The native constructor timeout
remains unresolved, and creature selection stays disabled until the remaining
world, icon, and collection readers are complete.

### Connected fish world implementation

The same `--creature-fish` builder continues the category into a shared world
packet at `8064A000..80654FFF`, including the shared creature-save extension.
The ordinary dependency planner installs missing reader, world, and save code
in order within the same category task. Existing installed
stages and prepared models are reused. Ten startup loads fit the retained
bootstrap reservation; the full new packet is checked before any callback runs.

`v3_creature_spawns.py` follows all river, coastal, pond, tournament, and island
calendar pointers in the verified donor. The 296 time/half-month descriptors
retain every source weight and spawn area, with shared lists stored once.
The 3,340-byte packed calendar includes native herabuna's independent monthly
weights, including late September. Brook trout maps to added actor 44, not to
herabuna. Retaining both is an explicit additive-identity adaptation. Island
calendar extraction does not add an island to N64 or enable island-only spawns.

`creature_spawns.c` implements source five-day seasonal blending, time periods,
selected-only weights, environment-rank selection with source rejection/retry,
and bounded candidate-position scanning. GAFE01-r0's river-mouth rule is retained,
not the later Australian rule. Both terms plus the extra herabuna records fit
the 64-row plan; the converter checks the complete category maximum. Invalid
calendar/state inputs reject rather than truncating to the native twenty-row
buffer. The native caller persists both season fields, without redrawing the
transition offset on each visit.

`creature_water.c` binds native collision/field APIs for waterfall, pond, river,
and marine placement, donor sand/depth exclusion, and four-direction shoreline
checks. `creature_patrol.c` uses native actor fields for all four donor swimming
states, waiting, approaching a bobber, and escape. Counters/phase increments use
30-Hz units; source movement is half-scaled at 60 Hz. Three action and three
initializer pointers in the coastal owner select shared wrappers. Their original
functions and program dimensions remain intact, with only those six absolute
pointer relocations removed. The fallback thunks use the actor's actual relocated
program pointer at `244`, not a fixed heap address.

The behaviour word defaults to zero (N64); one selects GameCube patrol for
imported-origin coastal actors. Native fish always retain their existing path.
The private composers resolve these settings from the installed bindings below;
per-species composition and remaining gameplay work stay unfinished. A separate
spawn-mode word selects the additive native policy or source calendar path.
The native policy gives the unmodified native manager a weight of 100 against
the sum of selected added species' actual current-half-month/time weights.
If the native opportunity wins, its complete original calendar, tournament,
weather, frame-counter selection, and placement execute. Native species retain
their relative distribution; their total share changes when additions compete.
Added fish use donor terrain and current-term weights without seasonal blending
or environment-rank penalties. A pond without a native spawning opportunity
does not receive an artificial 100-weight no-fish outcome. No eligible additions
means direct original fallback without an extra random draw. Only the winning
manager changes acre history; native mode leaves saved transition state intact.
Browser/offline resolution, collection UI, official catch-message routing, and
ordinary gameplay remain unfinished.

The 9,564-byte compiled world code and its complete calendars share one 44-KiB
reservation with creature persistence; source data begins at `8064D000`.
Original room/frame resources, actor sizes, and the stable translation output
remain unchanged. The native manager hook preserves its two overwritten
instructions in the fallback and derives the actual relocated program from
`Set_Manager+178`. Native make-fish uses that same program's retained creation
function. Repeated-acre protection is retained; the N64 engine has no donor
island/offing location, and the adapter does not enable those retained calendars.
The normal GameCube path uses selected-only spawn weights, native event/weather
and terrain queries, saved seasonal blending, and the existing actor allocator.
`test_v3_creature_spawns.py` checks the complete source calendar, sanitizer-bound
selection/terrain/patrol paths and fallbacks, installed pointers/relocations,
source/output binding, startup arguments, unchanged persistence, UPS, planning,
and all/empty composition. Native execution and hardware remain unverified;
these checks do not classify the earlier constructor or scheduler failures.

### Shared creature persistence

`creature_save.c` derives the seventeen readiness/profile bits from the installed
parent readers: fish bits 0..8, insect bits 9..16. Four independent collection
records and the town's seasonal transition live in a 32-byte extension. Native
player deletion clears only that player's new collection, retaining other players
and town season state. Native capture and completion consumers call the added
collection API; collection UI and foreign-player transport remain required.

| Extension offset | Meaning |
| --- | --- |
| `0..3` | Selected creature profile, LSB-first stable identities |
| `4..19` | Four players' collected bits, four bytes each |
| `20..22` | Saved term `0..23`, transition offset `0..5`, initialization flag |
| `23..31` | Reserved zero bytes |

The extension begins at working offset 1200 and canonical capsule offset `4D0`.
Working state is 1,232 bytes; the complete runtime is 1,264 bytes at `8046C000`,
with guards at `8046C4E0`. Existing furniture, clothing, rewards, surfaces, console
data, and native town bytes keep their offsets. The canonical codec uses format
six/registry four. Its compressed two-bank envelope uses format seven, distinct
from the canonical format so corrupted envelope fields cannot be mistaken for
an uncompressed bank. Both banks remain 64 KiB; capacity is checked before writes.

Valid older saves migrate forward with empty added-creature collections and
uninitialized seasonal state. Missing creature profiles, invalid collection
bits, malformed seasons, damaged checksums, and insufficient capacity reject
without committing live state or beginning save I/O. V2 and older V3 readers
reject new saves; preserve backups. Native ordinary save/reload is unverified.

The new canonical codec is at `8064E000`, storage runtime at `80650000`, and
profile/season helpers at `80654000`/`80654600`. Every previously published console
and save entry retains its address through a checked tail jump, including the
indirect `require_state` entry used by older adapters. Complete predecessor
packets are verified before these changes. Startup loads and verifies the entire
world/save packet before entering initialization. No existing console scratch,
player record, or native manager buffer is borrowed for persistent creature data.

`tests/test_v3_creature_connected.py` reuses the existing save-I/O host fixture
with the new extension, rather than replaying old cartridges. Sanitized checks
cover all seventeen identities, independent players/deletion, forward migration,
season stability, invalid data/profile/capacity rejection, and the source calendar
through the native-bound manager. Cartridge checks cover relocated hook targets,
all stable save entries, complete code/packets, unchanged graphics resources,
patch reconstruction, and all/empty private composition. Native engine calls are
stubbed in the host fixtures; native execution and hardware are not established.

### Catch records, completion, and inventory icons

`creature_collection.c` connects fish and insect catch events to their own native
or extended collection identities. The native player windows at `808CF704`,
`808CCE18`, and `808CD568` preserve the full-pocket path: collection is recorded
when caught, not inferred from successfully inserting an item into inventory.
Fish actor slots `36..44` map to added indices `32..40`; rubbish remains excluded,
and coastal salmon retains ordinary salmon identity. Insects use indices `32..39`.
No shift by an added index reaches the native 32-bit collection fields.

Native final-catch flags consider the prospective catch without writing early,
require every native species and every selected addition, and do not trigger
again for duplicates. The three original completion/start/talk functions use
the same predicate. Their original flag meanings and offsets remain unchanged.
Unselected additions do not count toward completion. Foreign private blocks may
retain native records, but cannot write added records into a resident's slot;
the existing explicit save-error path stops such writes. Controller Pak transport
must be completed before declaring the full travel/save path supported.

The shared converter reads actual donor fish/insect icon-pointer tables and
category bindings for all seventeen added parents. Each icon retains the full
32-by-32 CI4 texture and both sixteen-colour palettes. Palette conversion and
untile/packing reuse the existing inventory-art tooling. The complete 9,792-byte
resource set and 152-byte descriptor table occupy verified unused gaps in the
world/save packet. Each descriptor/resource has source/output hashes and exact
bounds in the build report; no original texture, table, calendar, or codec is
overwritten. Future world-code changes must repack these gaps, not assume that
padding below the calendar or after a codec is still free.

The default native descriptor window at `8085C968` routes only extended fish and
insects through the readiness/profile-aware lookup. Gifts and tools retain their
existing branches. Original species retain their native descriptors. The native
palette selection still adds 32 bytes for collection rendering; the second
palette is not discarded. Disabled or invalid added IDs skip drawing without
indexing past the native table. The original drawing function is checked in full,
normalizing its two existing hooks; unrelated menu-allocation metadata remains
unchanged. Exactly two obsolete descriptor-table relocations are removed.

Sanitized checks cover all seventeen catch/icon identities, four independent
players, native high bits, duplicate/final catches, completion dialogue,
disabled records, and foreign-write rejection. Current-cartridge checks compare
all icon resources with the donor, verify both palettes, hooks/relocations,
retained code/assets, UPS reconstruction, and unchanged all/empty composition.
These are not native icon-rendering, ordinary gameplay, or hardware results.

### Collection UI, official text, and behaviour composition

`creature_ui.c/.S` occupies `80654800..80654B6F` in the existing loaded packet.
The 240-byte table at `80654F00` ends before its final guard. No saved field,
actor, packet allocation, or original creature resource grows for this path.
The table carries complete fish/insect ordering, nine column coordinates,
five row coordinates, and seventeen message IDs. Native herabuna keeps index one;
brook trout uses added index forty. Empty cells use `FF` and resolve to no item.

The inventory's common collection lookup serves both drawing and names. It checks
collection/profile readiness, including independent added records, instead of
shifting an added index into the original 32-bit native field. Drawing iterates
45 cells at 0.875 icon scale. Navigation uses nine columns and five rows; side
entry sets column eight without changing collection table ID seven. The native
generic cursor movement remains intact. Original ordering matches both games.
Added insect ordering and vertical coordinates come from GAFE01-r0; horizontal
positions fit within the native range. Native visual fit remains unverified.

The constructors retain their animation, message window, camera, fanfare, and
delay-slot paths. Their final message calls redirect added identities through the
shared reader; native, rubbish, and disabled cases preserve the original message.
Final-catch text uses the existing full-name bridge. Normal added catches use
native messages `2EEF..2EFF`, sourced from donor fish `2FC9..2FD0`, brook trout
`1328`, and insects `2FC1..2FC8`. Complete donor selector functions establish
these mappings. Wording, manual line/page breaks, pauses, colours, and effects
remain; maximum expansion is 264 bytes. The single provenance catalogue owns
every source/output identity. Both native message-count readers advance together.

The shared text installer recognizes the relocated English choice resource at
`029E0000` and can move the complete four-file text region into verified free
physical space. Virtual identities, all old messages/choices, and unrelated
directory entries remain. Allocation checks physical-only resources and the
reserved import-growth range, not just zero-looking bytes. The complete
2,166,256-byte region does not overwrite the owner after its original location.

`v3_creature_choices.py` supplies shared installed definitions for
`fish-population` and `coastal-fish-movement`. Both offer N64 and GameCube, with
explicit N64 defaults. Population applies to original and imported fish;
coastal movement applies only to imported coastal fish and has no effect without
one. Runtime mode words remain separate from import enable words. Offline
`--behaviour SETTING=VALUE` and experimental browser controls resolve these same
definitions, reject unknown names/values, and record resolved values in receipts.
Defaults plus empty imports return pinned V2; a changed behaviour uses V3.

Composition updates mode data, the world-packet CRC, its enclosing equipment CRC,
and existing startup/package checksums in dependency order. The world CRC is an
explicit read-only bootstrap field, not a patched instruction immediate. Original
assets and saved identities remain. Switching modes retains saved seasonal state
and changes rules, not the layout; native switch/reload remains unverified and
the interface says so. These controls do not enable unfinished species or
authorize deployment.

`tests/test_v3_creature_ui.py` covers all 81 identities and seventeen catch routes,
native/disabled/final-catch cases, official text preservation, complete installed
owners/relocations, and UPS reconstruction. Its unchanged evidence is retained
across the behaviour-binding build. `test_v3_creature_choices.py` checks both
mode words, five browser/offline compositions, ordered checksums, invalid settings
and receipts, and unchanged UI/art/save resources. Actual field execution,
Controller Pak transport, and hardware remain unfinished or unverified.

### Native integration constraints

- Native fish actor indices `0..31` are ordinary fish, `32..34` are rubbish,
  and `35` selects the coastal salmon path. New carried IDs `2320..2328` must
  not become those existing actor indices. Preserve the original actor slots;
  map added fish to separate actor indices at capture and release boundaries.
  The prepared `native_index` field describes the carried-item index only.
- The field fish owner is VROM `922A10`, relocation `924590`, RAM `80A5AF70`;
  its start/end/model arrays are `80A5C568`, `80A5C5F8`, and `80A5C82C` (36
  entries), with animation selectors at `80A5C984` and height at `80A5CA14`.
  The fish graphics bank is VROM `1871000`, 61,344 bytes. The native loader
  skips each object's eight-byte header and subtracts its bank offset when
  publishing segment six. Converted lists need that same address convention.
- The release owner is VROM `93A920`, relocation `93BBC0`, RAM `80A7A680`;
  its start/end/model arrays are `80A7B444`, `80A7B4D4`, and `80A7B708`.
  The constructor at `80A7A934` directly subtracts `2300` from the carried ID;
  this boundary needs the explicit actor mapping. Its size table at `80A7B324`
  and animation table at `80A7B7C8` also need extended readers.
- The insect owner is VROM `8DEEC0`, relocation `8E0870`, RAM `80A10210`;
  start/end/model arrays are `80A116B8`, `80A11738`, and `80A119B8` (32 entries).
  Its graphics bank is VROM `113D000`, 39,248 bytes. Behaviour dispatch and the
  added insects' orientation rules are required alongside the graphics readers.
- The donor release-shadow code itself has only six correction entries despite
  adding XXL arapaima. The port must supply bounded XXL handling, not reproduce
  that out-of-bounds read. The separate native `Gyo_Kage` actor (`85`) also
  needs its size reader extended. Existing fish timing and golden-rod hooks
  must survive the category integration.
- Retain the external added-model resource and resident lookup tables. Copying
  both complete native graphics banks or materializing enlarged actor BSS inside
  the nearly full ordinary import file is unnecessary. Do not repeat that
  capacity investigation or replace the installed shared loading path.

`tests/test_v3_creature_field.py` checks every source/frame binding, differing
field/release timing, missing/disagreeing-pointer rejection, complete converted
resources and command bounds, and reuse of all seventeen existing room objects.
The native integration tests above cover cartridge installation; neither set
claims ordinary carried/field execution or original-hardware verification.
