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
The real alternatives are installed, but no browser choice is exposed until its
composition and complete playable-import dependencies are connected. A separate
spawn-mode word selects the preserved original manager or source calendar path.
Its N64 value currently has no additive fish support; that alternative remains
unfinished, not an advertised supported choice. Icons, catch/collection UI,
behaviour composition, and ordinary gameplay remain unfinished.

The 6,908-byte compiled world code and its complete calendars share one 44-KiB
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
and town season state. Native capture/UI consumers still need to call the added
collection API before species become selectable.

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
