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

Each profile has its canonical sparse slot and parent relationship. The reader
requires both carried readiness and the selected native display profile. All
nine fish have connected private composition; the eight insect profiles remain
inactive pending field behaviours and spawning. Prepared room support alone is
not a playable species, and private selection does not establish hardware testing.

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
The active queue retains unresolved fish gameplay verification and continues the
eight insects' shared field behaviours and spawning. Complete room, sound, field
art, collection, text, composition, and creature transport consumers are retained.

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
The shared native stage installs these assets without recompiling them. Graphics
alone do not make a species selectable: the connected gameplay consumers below
are required too. Insect field behaviours and spawning remain unfinished.

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
use slots `32..39`. Fish have experimental selections; insects remain inactive
until their field gameplay paths can consume these identities.

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
remains unresolved. World, icon, collection, and selection readers are connected;
that does not turn the timeout into a passed native test.

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
per-species composition uses the same fixed identities. A separate
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
Browser/offline resolution, collection UI, and official catch-message routing
are connected. Ordinary native gameplay verification remains unfinished.

The 9,564-byte world code and complete calendars share the 48-KiB reservation
with creature persistence and passport transport; source data begins at `8064D000`.
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
collection API. Collection UI and creature passport transport use these same
identities; other imported travel records remain separate unfinished consumers.

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
Unselected additions do not count toward completion. Foreign private blocks use
the separate identity-bound visitor record described below, never a resident's
slot. An unknown foreign identity still rejects through the save-error path.

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
ordinary travel, and hardware remain unverified.

### Per-species optional composition

`v3_creature_selection.py` binds each of the nine fish choices to its fixed
carried identity and room display. A selection controls the parent table's
readiness word, display enable word, and existing sparse saved-profile bit.
The four-byte creature mask uses bits 0..8 for fish and 9..16 for insects.
All nine fish are `ff010000`; inactive insects contribute no selected bits.
The parent reader already gates spawning, names, prices, placement, pickup,
collection, and icons through this same availability check. No per-fish
installer or second browser list is introduced.

The parent-packet CRC is an editable bootstrap constant. Both composers update
it before the world and enclosing equipment/package/prefix checksums. Browser
options contain both required enable writes and the explicit creature mask;
validation checks category, disjoint identities, and the complete mask union.
The receipt records the resolved mask/hash. All 176 choices reproduce the full
cartridge; empty/default choices reproduce stable V2. The private experimental
selector is not a deployed patcher or a gameplay certification.

Sanitized checks use actual selected parent/display tables through the item,
catch, and save readers. All-fish and partial profiles preserve fixed identities;
removing either half of a saved fish's availability rejects without changing
the input bank or destination. Six browser/offline profiles agree, including
all fish, brook trout alone, mixed villagers/fish, and GameCube behaviours.
Artwork, world behaviour, icons, text, and canonical save code remain unchanged.

Room scoring uses the ordinary `v3_furniture_install.scoring` writer, not a
separate fish evaluator. Complete donor HRA and feng shui tables are hash-checked;
all seventeen display identities retain their exact series, birth-category
mapping, surface bits, and colours. The nine available fish receive active rows;
eight insects retain prepared records until field gameplay is implemented.
Native herabuna and all other original scoring rows remain unchanged. Disabled
fish receive the same inert HRA row as other deselected imports, including in
browser builds, so they cannot enter group searches or recommendations.
Current source/installed comparisons and all six composition cases check this
path; native house evaluation is not claimed.

### Creature passport transport

`creature_travel.c` connects native clear/save/load/private-copy entry points at
`80079080`, `800793B8`, `8007942C`, and `800B7F48`. The complete original Pak
implementation and each replaced function are checked against the verified
retail cartridge. The native `1200`-byte note, `BD0`-byte private structure,
`528`-byte animal, all letters, and nonce at `1100` retain their layouts.

Unused passport header bytes `2..7` contain `AFV3CT`. A 48-byte capsule at
`11C0` contains magic `AFCT`, version one, size, the full sixteen-byte native
player/town identity, four profile bytes, four catch bytes, CRC32, its complement,
and eight reserved zero bytes. Native whole-note checksum validation and capsule
validation precede private/animal copies or collection changes. The independent
header marker prevents a damaged capsule magic from becoming a legacy record.
Original passports initialize an empty visitor collection; returning legacy
records never erase an existing resident's added catches.

Code starts at `80655000` in a 4-KiB extension of the existing world packet.
The separate 28-byte visitor state at `80655FC0` is zero on startup; the final
guard stays at `80655FF0`. A checked jump at the old collection-reader entry
preserves all existing capture/completion/UI bindings. Native residents still
use their own format-seven working records. Visitors require the exact native
foreign-private address and matching identity; successful captures update only
the visitor record. Return copies merge into the matched resident, never another
player. Export includes the full selected creature profile because pockets and
letters can contain creatures without a catch event.

Smaller receiving profiles reject before committing private/animal/collection
data. Device errors return failure and do not claim successful persistence.
V2 and older V3 passport readers do not understand the extension; use compatible
V3 profiles and preserve Pak backups. Other import categories' catalogue/console
travel remains unfinished. No native travel, new FlashRAM cycle, or original
hardware result is claimed by this creature-specific adapter.

`test_v3_creature_travel.py` checks the current installed hooks, complete unchanged
resources, patch reconstruction, six browser/offline profiles, and sanitized
transport of all seventeen records across four residents. The host fixture uses
the actual adapter and collection reader with memory-backed device calls; it
does not execute libultra, an emulator, or hardware.

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

## Added-insect behaviour programs

`tools/v3_creature_insects.py` converts the entire eight-species behaviour category
from the pinned GAFE01-r0 source in one compiler batch. It retains all 122 complete
donor functions across six programs and records the corresponding actual donor
function hashes/relocations. Source file hashes reject unreviewed edits. Generated
donor C and compiled objects stay under ignored `build/`; committed files contain
the converter, native ABI declarations, platform adapters, and original fixtures.
Existing artwork, official names/text, prices, room displays, icons, collection
storage, and provenance are reused; this is not another graphics importer.

| Added species | Donor program | Included behaviour |
| --- | --- | --- |
| Snail | `tentou` | Flower movement, flower removal, escape, and release |
| Mole cricket | `kera` | Hidden sound requests, digging, emergence, escape, burrowing, and drowning |
| Pond skater | `amenbo` | Water-surface movement, rest, ripple requests, and release |
| Bagworm | `mino` | Tree hiding, shaking, suspension, retraction, falling, and release |
| Pill bug | `dango` | Rock strikes, emergence, stress response, escape, and drowning |
| Spider | `mino` | Species-specific tree movement, falling, backward escape, and release |
| Ant | `dango` plus ground colony | Carried/released insect, food colony, net handoff, and fading |
| Mosquito | `ka` | Flying, player pursuit, attack timing, sting requests, demo avoidance, and release |

The source version is explicitly GAFE01-r0, with the later Australian conditionals
and optional source bugfixes disabled. The source snail's caught-state escape
choice is retained and documented, not silently attributed to a different donor.
Necessary native layout/timing adaptations do not change the source action bodies.

### Native layout and lifecycle

The native controller is `8F8` bytes: the `174`-byte actor, three `280`-byte insect
slots, and its native object-bank field. The GameCube's nine `288`-byte slots are
not compatible. Five complete native constructor/movement functions are checked
against the input cartridge before preparation. MIPS compile-time assertions cover
the controller size, actor size, stride, and actual offsets for movement, animation,
speed, stress, collisions, items, lifetime, and alpha. In particular, donor
`_1E0` names the animation field at native `1DC`; casting to GC structs is unsafe.

`creature_insect_state.c` keeps the added tile coordinates and collision radius
outside native slots and their collider/light/program storage. The native
`ClObjPipe` occupies `1F8..213` (28 bytes), followed by height at `214`. There is
no spare radius field at `210`. Donor initialisation must not alter those final
collider bytes. Constructor/destructor ownership binds exactly
three slots. Foreign pointers reject; no unchecked slot arithmetic or shared
per-insect scratch state is used. The player-action latch is shared across all
slots and both substeps, and resets after the complete controller update, not
after the first insect. All eight added species use the donor's eight-unit catch
range, with its action-controlled uncatchable flag.

`creature_insects.c` dispatches the complete source programs by fixed species
identity and runs two ordered source substeps per native tick. This retains both
60-Hz integer timers and source half-speed movement/gravity/animation increments.
Held-object movement suppression, lifetime, fade, and destruction remain part of
that shared path. The native controller hook must bypass its original updates
for imported objects; otherwise movement and timers would run twice. Original
species continue through their original native paths.

Source accesses to GC global/game/player fields are explicit adapter calls.
`creature_insect_environment.c` supplies player distance/angle, nearby-actor stress,
source-rate movement, catch requests through the relocated player's callback,
projection, culling, and native collider cleanup. Other actors' full-frame movement
is halved for source stress sampling. Native nature callbacks run once per native
tick, object-collision displacement is split across both substeps, and source frame
queries include substep phase. The native game-view offsets have MIPS assertions.

`creature_insect_collision.c` supplies directed-tile collision and source acre
bounds. A scoped tile filter wraps native column generation, removes only the
matching cylinder, and restores its previous scope after the check. It does not
change foreground items or terrain. The real native terrain/ground response is
retained. Intro-demo acre-inset detection reads native mode getter `800741F4`
and player-acre mask one, matching the complete native wall consumer. Complete
intro functions verify the mode's producer/reset. The intro and train-arrival
actors establish and clear the first demo clip at `80136F4C`. The GameCube's
second demo clip is not an assumed adjacent native field; its binding remains open.

`creature_insect_hooks.S` supplies constructor/destructor ownership, imported
initialisation, per-slot dispatch, and one event reset after the full controller
loop. It derives native continuations/tables from the relocated return address,
not a fixed heap address. The original path replays complete table-address pairs;
added species bypass the original 32-entry program lookup. Invalid imported
ownership/identity halts instead of entering an out-of-range native lookup.
`install_controller` composes the five owner hooks and column call-site hook,
removing the complete replaced relocation records and preserving unrelated
graphics hooks. Runtime placement/startup and remaining services must be completed
before applying this composer to a deliverable ROM.

The bindings file supplies native primitive functions, checked against complete
bodies in the hash-verified original N64 ROM. Native actor creation retains the
installed campsite/balloon descriptor chain, checked against its existing receipts;
it still delegates original actor IDs to the native table. Unresolved second-demo,
season, and mosquito-player bindings remain undefined symbols in the prepared object;
no dummy engine routines satisfy them. Controlled host services are test fixtures,
not evidence of native gameplay or completed mosquito stings.

### Complete spawning and native manager adapter

`insect_calendars` in the existing shared calendar converter follows all 72 town
month/time lists and six island lists in the actual donor REL. The 2,394-byte
pointer-free packet retains every weight, explicit no-spawn row, all three
candy/spoiled-turnip extras, and complete group-size data. Wisp's event actor is
not an ordinary imported insect; retained island data does not supply an island.
The greatest adjacent-month blend has 45 rows, including extras. The common
64-row plan preserves all of them without copying into either the native
twenty-row buffer or the donor's undersized 43-row buffer.

`creature_insect_spawns.c` implements all six time bands and monthly five-day
blending, including December/year and leap-day boundaries. Its shared habitat
path covers all fourteen areas, native foreground IDs, two-unit acre margins,
buried-item eligibility, rain/snow rules, pond-acre restrictions, field rank,
explicit no-spawn mass, and source-order flower-to-flight fallback. Candy and
spoiled turnips suppress other weights as in the donor. Position selection retains
the source's separate eligibility and final tile checks, consumes group-size RNG
even for one birth, removes every chosen tile, and stops on creation failure.
The final attempt's result is separate from the number already created; a partial
group must not be reported as a successful final attempt. Cockroach tree/spoiled
turnip states and ant-colony creation remain distinct from ordinary creation.

`creature_insect_manager.c` connects that path to the native manager's acre fields
at `4180`, complete native foreground/deposit/collision queries, weather, field
rank, coordinate conversion, and the relocated insect clip at `80136F28`.
The native 24-byte creation record and 16-byte clip have MIPS layout assertions;
the clip is not enlarged over adjacent state. The constructor resets the shared
transient calendar cache. Source mode refreshes the calendar on month/time/area
or profile changes, not on every acre visit. Its live-acre test excludes the
release slot and includes the background-actor colony query. Native-population mode gives
the unchanged original manager a 100-weight opportunity alongside enabled added
species' real filtered weights. Both alternatives still require selector binding
and their population-capacity implementations before a playable claim.

`spawn_contract` checks complete original creation/manager bodies and entry
instructions against the verified ROM. Its composer changes only `8092AF0C`'s
eight-byte entry; existing gold-tree hooks and relocation records remain intact.
The assembly fallback resumes at the actual manager-owned overlay buffer plus
the original function offset, replaying its stack/return-address prologue.
No fixed heap address is assumed. This composer and the controller/column
composer must be installed with the complete resident runtime and loaded data.

The manager intentionally retains the unresolved native season service.
The current saved creature capsule uses bytes 20..22 for fish seasons
and rejects nonzero bytes 23..31; an insect season reader cannot safely start
writing that padding without the matching codec and compatibility work.
`af_v3_creature_profile_byte` is an existing installed shared export that the
final linker must resolve from its checked build report. The current controller
still has two wild slots and one release slot; the GameCube eight-wild-slot
alternative is required work, not supplied by the larger spawn plan.

### Ground colony and catch handoff

`creature_insect_colony.c` connects the source's separate ground actor to ordinary
native allocation, actor lists, movement/drawing, and destruction. Actor slot
`B5` must be unused; the composer checks the entire empty descriptor before
binding its resident profile. The actor uses native background part four and
the existing keep bank, with a `188`-byte allocation. It replaces no native actor.
All thirteen complete donor colony/creation/query functions and the pinned
source file have receipts in the prepared report.

The native controller's end callback processes the source's deferred colony
request and retries an allocation failure on the next update. Constructor and
destructor hooks clear that pending state; the native sixteen-byte insect clip
is not enlarged. Candy/spoiled-turnip removal, acre culling, forced/ordinary net
requests, two source-rate action steps, carried-slot creation, label transfer,
scale/fade, and destruction are connected. Catch requests are registered once
per native tick so the two source steps do not duplicate entries in the native
eight-request list. Missing players during scene teardown are not dereferenced.
If carried creation fails, destruction clears a still-owned catch label instead
of leaving the native player with a pointer to freed colony storage.

The guarded `808CCDFC..808CCE17` replacement identifies the colony as ant index
38 while the catch is waiting for its background update. Native bee swarms keep
index eight. Complete relocated net callbacks and their constructor assignments
are checked; existing official catch-message and collection hooks are untouched.

The shared material converter retains the complete twelve-triangle model,
intensity texture, both scrolling layers, alpha combiner, and cloud-surface render
mode in a 944-byte object. Rates come from the donor EVW table; the current frame
supplies both immutable tile command lists. Native matrix, lighting, and cache
writeback bindings are checked. The draw reserves command/scratch capacity before
either lighting helper writes. Prepared artwork is cached under
`build/v3-creature-insects-work-01/colony-assets/`; existing seventeen-creature
artwork is not rebuilt. The profile, catch hook, and resident artwork must be
installed with the complete insect runtime, not independently enabled.

### Complete field sound and effect services

`v3_creature_insect_audio.py` resolves every sound call across the six pinned
programs. Shared loops `25` and `26` retain their complete native channels after
checking all relocated pointers and full instrument/sample identities against
the donor. Added loops `45` and `4F` use the ordinary complete-program converter.
Its timed-layer parser retains continuous-note mode followed by a repeating
rest, including every envelope and duration; it does not replace that channel
with a generic sustained tone.

The two triggers use the existing priority-preserving slot allocator. Against
ABI 305, source `006A` maps to native `006E`, and source `0438` maps to `0450`.
Native `006A` already belongs to a different imported sound and is preserved.
The generated four-byte binding table is linked into the same insect object.
Complete loop instruments are checked against the final shared trigger font;
existing font indices, addressed samples, and retained programs remain intact.
Preparation writes the full sequence, font, wave archive, fragments, and binding
table under the program output's `field-audio/` directory. The shared audio
installer accepts this category and updates the existing resource/dispatch
records without changing furniture callbacks or selecting an insect.

`creature_insect_audio.c` routes hidden-cricket `44` to the already installed
per-instance randomized chirp scheduler. Exposed-cricket `45` uses positioned
loop playback. Mosquito `CF` retains its high-bit mode through the native queue,
which stores that mode before masking to program `4F`. Native coordinate,
queue, trigger, and scheduler consumers are checked, not inferred from sound IDs.
No audio is played during preparation or host checks.

`creature_insect_effects.c` routes ripples and splashes to native effects 69/70,
and donor digging effect 84 to native 85. The complete water owners already
handle the required size-one ripple and size-four splash with ordinary native
lifetime, subeffects, and rendering. The digging owner lacks donor flag `4000`.
A guarded resident-call bridge at `80A2736C` strips only that size flag before
the ordinary constructor and sets the returned effect's three scale axes to
`0.005`. Normal variants and the separate `8000` flag are preserved. The ordinary
request loads the effect code before the bridge runs; direct creation without
that loader is not used. Both games discard the late-life scale-adjust result,
so the bridge retains that behaviour. Native 30-Hz effect lifetimes/movement and
existing artwork remain; there is no new pool, effect identity, or saved field.
Complete source callback receipts come from profile relocations, avoiding the
unrelated donor effect that shares local `eTM_*` function names.

The combined host check covers every field sound route, mode-bit preservation,
null services, both water calls, all nine normal/small digging variants with and
without the mole flag, and effect-allocation failure. The resource/composition
check uses the current cartridge, verifies actual prepared bytes, exercises the
shared audio installer in memory, retains all previous triggers, checks audio
capacity, and composes the mud call-site hook. These are not native synthesis or
gameplay evidence. Final placement must install the complete prepared resources,
binding table, and mud hook together with the insect runtime.

### Current prepared output and remaining connections

Prepared output: `build/v3-creature-insects-work-01/programs-17/`.
The current cartridge remains ABI 305. No new ROM, save layout, browser choice,
or deployment is produced by preparation. Reproduce against the explicit input:

```sh
python3 tools/v3_creature_insects.py \
  --base-lock build/v3-creature-world-work-01/connected-15/build-lock.json \
  --output build/v3-creature-insects-work-01/programs-new
V3_INSECT_PROGRAMS=build/v3-creature-insects-work-01/programs-new \
  python3 -m unittest discover -s tests -p 'test_v3_creature_insects.py' -v
```

The combined test covers all eight release/despawn paths, two-substep timing,
correct/wrong-tile shovel and rock events, both tree species, tree cutting, snail
flower removal, pond-skater rest/ripple cycles, drowning, mosquito pursuit and
sting requests, catchability, controller ownership, and invalid identities.
Address/undefined-behaviour sanitizers pass. A second host check covers actual
shared environment/slot logic, source phase, native-rate nature/displacement,
stress, directed collision restoration, acre walls, catch requests, held/caught
objects, lifetime, cleanup, and original/foreign ownership rejection. A third
check composes hooks against the current cartridge in memory and checks preservation,
relocation removal, and invalid targets. It uses synthetic resident addresses only
to test composition: it does not build a ROM or execute synthetic code.
MIPS compilation verifies native layouts and assembles all controller bridges;
host pointer sizes are not treated as the cartridge ABI.
The spawning check compares 99 complete-calendar/blend/selection cases against
the extracted donor data and exercises all eight added species through habitat
selection and their appropriate creation callback, groups, source RNG ordering,
weather, deposits, field rank, no-spawn mass, bounds, and invalid data. The native
manager host check verifies real shared calendar-to-manager execution, cache
lifetime, source season requests, native creation parameters, optional masks,
colony routing, live-acre suppression, and original-manager fallback. Native
engine, colony, and save services in that fixture are controlled test callbacks;
these checks do not establish native gameplay or implement the missing services.
The colony host check uses the actual lifecycle and draw adapters with controlled
engine callbacks. It covers pending allocation/retry, food conditions, forced and
ordinary net requests, single-ant label transfer, failed creation, fading, scene
cleanup, native bee preservation, scrolling coordinates, and graphics bounds.
The current composition check also verifies the unused profile slot and catch
span while preserving unrelated installed code. All eight focused checks pass;
native colony gameplay, visual appearance, and hardware remain unverified.

Remaining connections belong to the same creature importing task:

- Finish the second demo-state binding and the mosquito
  player sting response. Reuse the prepared native environment/terrain/controller.
- Connect the digging, axe/shovel rock-strike, and tree-shake event producers.
  The latch/reset and donor consumers are prepared; no producer is claimed wired.
- Complete the persistent insect-season reader/codec using the prepared
  calendar-to-native-manager path. Retain the complete colony implementation.
  Implement the actual
  native/GameCube population-capacity alternatives; group creation is bounded by
  available slots until the larger source pool and its consumers are installed.
- Place the complete runtime through the existing owner-storage machinery, retain
  overlap guards, install its prepared field audio/effect consumers, connect
  startup loading, and promote per-insect selection only
  when the gameplay dependencies are implemented.
- Verify the connected current cartridge/save path and fix actual defects. Keep
  the unresolved fish constructor timeout and scheduler disconnect open; the
  existing exhausted native harness budget does not reset for these source files.
