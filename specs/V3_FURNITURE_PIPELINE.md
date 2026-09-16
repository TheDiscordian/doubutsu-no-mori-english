# Automatic furniture import pipeline

## Workflow

New furniture uses `tools/v3_furniture_pipeline.py`, not a new Python item list,
family installer, catalogue switch, or dedicated native scenario. Extend shared
format/behaviour rules when the donor requires an unsupported feature. Item names
and themes do not determine which graphics converter runs.

The pipeline reads the checked GAFE01-r0 REL, symbol map, and identity worksheet.
`config/v3-import-build.json` pins the current complete development cartridge and
receipt. It is also the offline composer's source selection. Changing this file
does not change either web patcher. Build output includes a proposed next lock;
promote that lock after checking the batch. Never promote a partial/selected-only
cartridge as the full development base.
The output also retains `base-lock.json` and the conversion-directory reference,
so the next batch and its shared tests do not need another hard-coded predecessor.

```sh
python3 tools/v3_furniture_pipeline.py scan --output build/furniture-scan/inventory.json
python3 tools/v3_furniture_pipeline.py import --output build/furniture-import
```

`import` discovers, converts, and installs every supported, uninstalled item in
one invocation. `--select 3248 --select 334C` narrows the batch by canonical donor
ID. `convert` runs the same discovery/conversion without installation. The
standalone installer accepts an existing conversion through `--art`; it performs
the same source and base checks. Use fresh ignored output paths. No ROM, save,
source artwork, served website, or existing generated build is overwritten.

`--representation handheld` selects the
[actual player-equipment adapter](V3_HANDHELD_ITEMS.md). It uses the same
complete model/resource converter and compiler, with source-discovered held
roots instead of furniture profiles. Only `scan` and `convert --assets-only`
are available until player integration is implemented. Its distinct prepared
format cannot enter the furniture installer. Catalogue/collection previews
never substitute for the actual held model or its gameplay.

Shared reader changes use the same installer's `--refresh-runtime` mode. It
updates the checked current cartridge without reconverting or reinstalling any
existing artwork. Ordinary reader refreshes retain the complete DMA directory
and allocations. The optional `--equipment-art` adapter installs the complete
checked held-resource category and its shared loader, moving only the three
unchanged terminal catalogue/shop owners; see [held equipment](V3_HANDHELD_ITEMS.md).
Both paths preserve profiles and saved identities and emit a new build lock and
reconstructible patch. This is a shared runtime update, not a separate installer
for each item.
`--refresh-runtime --player-motion` extends that same resident module with the
complete source-derived player motions and split-body masks. It retains the
native player owner's table relocations and all original animation meanings;
resource availability does not enable item actions or add profile choices.

`--category` selects a discovered shared category without maintaining an item
list. `convert --assets-only` prepares complete artwork while retaining missing
metadata/gameplay/acquisition reasons. It produces a distinct **prepared-assets**
format that the installer rejects. This mode cannot be used with `import`.
The ordinary `convert` and `import` commands still require every eligibility
check. Inventory `asset_ready` describes conversion only; `status: supported`
also requires the supported metadata and acquisition route. Neither field is a
claim of completed playtesting.
An unrestricted `convert --assets-only` prepares all eligible uninstalled
artwork in one batch. Names must identify actual donor entries, and both donor
profile tables must resolve to real models. Entries pointing to the shared
`iam_dummy` profile remain explicit review records with `asset_ready: false`,
even when the name table contains a plausible item name. The English donor's
placeholder is not a substitute for artwork from another edition.

```sh
python3 tools/v3_furniture_pipeline.py convert --assets-only \
  --category indexed-static-model-palette --output build/indexed-palette-assets
```

Each item has one generated descriptor containing profile/model dependencies,
textures, palettes, vertices, native display-list locations, official name,
price, footprint, acquisition list, catalogue position, scoring, source hashes,
and installed resource locations. The installer and tests consume those records.
They do not restate the items in another maintained Python list.

The [browser composition plan](V3_OPTIONAL_COMPOSITION.md) also comes from the
installed records. A new eligible furniture record automatically supplies its
choice, saved-profile bit, enable/scoring writes, and catalogue membership.
Villager requirements come from actual installed outfit and house data. There
is no separate per-item browser list or patch definition. Experimental exports
remain unserved; neither V2 patcher changes without user testing and approval.

New official name entries are generated as `provenance.patch` if missing from
`translations/provenance.json`. Apply the generated patch through `apply_patch`
and build with the updated catalogue before promoting a build. Existing human
attribution is never overwritten; conflicting attribution stops the build for
review. The patch is a proposed edit to the single catalogue, not another text
source catalogue. The receipt states whether attribution is complete.

## Room-display aliases

`tools/v3_room_aliases.py` supplies the shared identity relationship for extra
donor room representations: balloons, diaries, fans, pinwheels, and tools.
Complete placement, pickup, and both furniture-index functions are hash-bound;
unexpected code, relocations, ranges, or inverse mappings fail. Category ranges,
parent IDs, and display IDs come from their actual compiled instructions, not
a maintained list of individual items. Both directions must agree. Balloon
models cross the `1xxx`/`3xxx` boundary and remain one parent item each.

Each alias records the parent's official name and source hash, all four room
rotations, accepted conversion IDs, pickup ID, and the donor's
`no_convert_tools` condition. The seven worn-axe inputs share the axe model;
the inverse display conversion returns the ordinary axe ID. This is a
collection representation, not the result of an ordinary room drop. Native
parent identity and gameplay remain unreviewed until independently established.

Format `AFV3-DONOR-ROOM-ALIASES-2` verifies the complete three donor consumers,
their relocation dependencies, and all four direct calls to the conversion.
Both ordinary and bulk `mTG_room_put_proc` calls pass `no_convert_tools=1`;
collection recording and checking pass zero. Unknown direct callers, changed
arguments, branches, code, or relocations reject before classification. The
whole-executable call scan is cached by immutable input bytes, not repeated per
item; caller and relocation validation still runs for each discovery.

Each record has `conversion_inputs` and matching `context_outputs` for room
placement, collection recording, and collection checking. Eight balloons use
display IDs in every context. The other forty representations are catalogue/
collection models: tools, golden tools, fans, pinwheels, and diaries retain their
parent IDs on ordinary room drops. All seven worn-axe inputs retain their actual
wear-state ID on room drops, although collection conversion maps them to one axe
display. Never apply the collection conversion unconditionally to room placement
or infer that dropping an axe repairs it. `room_placement_uses_display` exposes
that distinction to shared import/category code without item-specific switches.

The full donor inventory, furniture scan, prepared-asset descriptors, and browser
review data use these same records. Aliases stay unavailable as standalone
furniture; installation rejects them before ordinary acquisition metadata can
approve them, including when supplied through an older asset report. Artwork
may still be prepared, with parent/placement/pickup dependencies retained.
Unsupported graphics are separately recorded as `conversion_reason`; classifying
an identity does not claim its artwork or runtime behaviour is implemented.
Add native parent support and context-correct collection/catalogue integration
before enabling the corresponding logical item; add room conversion only where
the donor uses it. Do not offer both a parent and its display model as unrelated
choices or substitute shop stock for parent acquisition.

### Native alias records

`tools/v3_display_aliases.py` generates native relationships from installed
parent/display descriptors. The three installed garments use this shared path;
the prepared tool/fan/pinwheel parents still require their actual inventory and
gameplay support. No prepared alias becomes enabled or selectable automatically.
Existing garment profile owners and the original mannequin renderer stay intact.

One immutable forward index occupies verified unused package space
`804A0010..804A00FF`, after the preserved `804A0000` guard and before campsite
code at `804A0100`. Its `AFD1` magic and 32-bit count precede up to 58 sorted
four-byte parent/display pairs. Capacity, duplicate identities, cycles, source
bindings, and occupied destinations are checked before installation. The current
one-parent/one-display format does not yet implement worn-tool state aliases.

Each display's canonical 32-byte sparse item slot stores its runtime index and
display identity, with its parent at bytes 28–29 and optional native footprint
equivalent at bytes 30–31. Display-only records remain disabled as independent
furniture. They introduce no second name, price, ownership bit, or browser option.
Zero footprint means use the display's own generated footprint; only a checked
category equivalent delegates to an original native item. Ordinary furniture
records keep these four bytes zero.

Forward conversion checks the bounded index and selected inverse relationship.
Inverse conversion, names, prices, collection, and category readers share direct
canonical-slot lookup. The garment roster consumes the same parent field,
retaining original garment indices and the actual selected clothing dependency.
All four room orientations and the native argument-width conventions remain.
Unselected/missing relationships fall through to the unchanged original paths.

The helpers remain in their existing reservations: conversion
`80466270..8046637F`, roster/bridge `80466380..8046653F`, and metadata readers
`80466C00..80466EFF`. Their compiled lengths are 260, 360, and 640 bytes.
Linker limits, complete previous code hashes, and unused tails are checked.
No permanent allocation, heap, saved format, or saved-profile bit grows.
Future shared furniture installations reuse these verified records and code;
they do not rebuild an unchanged alias adapter.

## Discovery and supported categories

Both actual donor `furniture_quality` tables must identify the same complete
profile. The REL relocation stream and symbol spans are indexed once and reused
across the scan. Dependencies come from actual profile/model pointers, including
interior vertex-array references. Missing, ambiguous, external, truncated, or
unaccounted dependencies are rejected.

The shared static-material category supports:

- All four native opaque/translucent model slots, complete 16-colour palettes,
  one complete vertex array, and multiple textures/palettes.
- Complete CI4 and I4 textures up to 2,048 bytes, untiled from GX blocks without
  resizing. Pure I4 objects need no palette. Each resource records its format;
  native texture-LUT mode follows each material, including mixed-format lists.
  The shared `static-4bit` category covers both; `static-ci4` selects CI4-only
  objects, and `intensity-materials` selects objects with I4 layers.
- Complete RGBA16 textures up to 2,048 bytes, using source-verified GX RGB5A3
  four-by-four blocks and native RGBA5551. Opaque and fully transparent alpha
  survive exactly. Partial alpha is rejected, never thresholded; it requires
  a wider native renderer. No resizing or texture reduction is used. Upper TMEM
  stays available for CI palettes when materials switch. `rgba16-materials`
  selects these objects; `static-materials` includes all supported formats.
  The donor executable's `fmtxtbl__5emu64` at `800AAFC0` supplies the verified
  RGBA/16-to-RGB5A3 mapping, not a guess from the texture's symbol name.
- Native vertex conversion preserving position, UVs, and colours, clearing only
  donor flag fields; complete triangle conversion and bounded vertex loads.
- Source primitive colours and the supported material/geometry commands.
  The unlit texture/primitive category preserves texture RGBA in cycle one,
  multiplies RGB by primitive colour in cycle two, and preserves texture alpha.
  Its symbolic native combiner compiles to the exact checked donor command;
  no theme/item switch or extra texture dependency is required.
  Primitive/environment interpolation, alpha, and texture-generated or linear
  reflection coordinates retain their checked native commands. Positive S/T
  scales and four-bit S/T tile shifts remain independent; zero/zero source scale
  retains the established full-scale native conversion. Clamp, wrap, and mirror
  combinations are decoded by their actual bit fields; repeated axes require
  power-of-two texture dimensions. Unknown state fails.
- Static profiles with supported shape, collision, lighting, and rotation
  fields. Footprint follows **shape**, as in donor `aMR_GetFurnitureUnit`, not
  collision: shape 4 is 1×1, shape 3 is 2×1, and shape 5 is 2×2.
  The square collision category `5` is supported. Shape `5` retains native
  four-cell placement in all rotations. The build verifies the complete installed
  four-cell item reader and actual original/donor footprint tables before
  accepting square records.
- Ordinary A/B/C, event, train, and lottery acquisition, existing scoring categories,
  and source-indexed catalogue framing. Names and prices come from actual donor tables.
- Optional NPC souvenir categories use the shared selected-profile reward reader.
  Gulliver uses his existing native conversation and handover, with selected
  `ftr_listJonason` imports supplying his donor souvenir route. These items stay
  non-orderable and never enter ordinary shop lists. Empty selections retain the
  original native reward route. Other NPC/event categories still require their
  own verified call contracts, not new per-item implementations.
- Winter and summer camping use the same reward records, with donor categories
  19 and 23. The shared camper adapter preserves the winter 10% and summer 20%
  special-list rolls, subsequent 10% house-furniture chance, exclusions, and
  carpet/wall fallbacks. Winter selections opt into the donor route; no selected
  winter imports means the unchanged original native trade body.
- Soft- and hard-chair action sounds, selected from the donor's actual category
  table. Matching complete sound programs, timing, instruments, and samples use
  the existing native audio; no replacement sample or new audio allocation is
  needed. The shared reader also covers previously installed furniture.
- Native `NO_COLLISION` interaction flag `0010`, preserved in the complete
  profile. The native registration/placement behaviour and shop exceptions
  remain; this is not a substitute for a diary's separate gameplay system.
- Source-derived placement layers: ordinary floor items, surfaces that hold
  other items, and objects that may be placed on those surfaces.
- Single- and double-bed contact actions `0x08` and `0x10`. Complete models and
  profile scalars feed the existing native bed positioning, contact, entry,
  and exit routines through the expanded profile table. No new bed callback, per-item behaviour switch,
  or animation replacement is needed. The build checks the current room engine
  and its four bed-profile bindings before accepting this category. Separate
  island/holiday acquisition requirements still prevent installation; bed
  support never substitutes ordinary shop stock for the actual donor route.
- Constant identity-indexed model/palette selection. A reviewed complete draw
  implementation selects two opaque models and one sixteen-colour palette from
  a complete relocated table. The converter derives the index base, row stride,
  model pointers, and palette from the donor, not per-item definitions. The
  selected palette replaces the fixed segment-eight reference in both models.
  All create/move/destroy callbacks must be complete no-ops, DMA must be absent,
  and every draw-code relocation must match the reviewed dependency pattern.
  Changed code, additional effects, incomplete tables, ambiguous bindings, and
  out-of-range indices fail. The descriptor retains function hashes, code/data
  relocations, the selector row, and palette binding. This removes only a
  constant draw selector, never animation or gameplay behaviour.

The `constant-model-sequence` category recognises reviewed draw-only callbacks.
Null lifecycle slots are allowed; any present create/move/destroy callback must
be a complete no-op. DMA callbacks remain unsupported. The shared code verifier
checks every instruction, model-address relocation pair, and matrix-helper call.
It supports fixed one- and three-model opaque sequences without item definitions.
Other draw operations, transformations, state changes, and lifecycle effects fail.

The converter retains every complete source list and appends one small native
display list that calls those lists in their original order. The sequence record
contains every target, native offset, size, arena, and hash. All lists stay on the
opaque stream; their own material modes remain unchanged. The profile uses the
normal native opaque model slot and no callback. The installer regenerates and
checks the complete sequence bytes, bounds, targets, and profile binding, alongside
the ordinary graphics and acquisition checks. No runtime code or allocation grows.
This linking method is independent of an item's identity or theme. A constant
draw callback is removed only after its complete lack of additional effects is
verified; this is not a mechanism for stripping animations.

The `indexed-model-sequence` category supports constant identity-indexed draws
with one or two ordered opaque lists and an optional conditional translucent
pair. Complete reviewed instructions, all relocations, matrix-helper targets,
full pointer tables, bounded index masks, and the conditional selector establish
the rule. The table origin and conditional identity are checked parameters, not
per-item code. Every lifecycle callback must still be a complete no-op. Changed
effects, missing pointers, unsupported branches, or out-of-range selection fail.

Material-only and geometry-only lists are joined in their actual call order for
each command stream. Only intermediate final-return commands are removed; all
state, resources, and geometry remain. Complete per-part source offsets, sizes,
hashes, and joined positions are retained in `source_parts`. The usual strict
material/triangle parser processes the resulting list, so an incomplete state
setup, bad termination, nested unsupported call, or unaccounted relocation still
fails. Opaque and translucent lists stay separate native profile slots; the
fishing rods' conditional translucent pieces are not omitted or drawn opaque.
No runtime callback or new allocation is needed for this constant selection.

This shared category prepares all eight fans, eight pinwheels, four golden-tool
displays, and four ordinary-tool displays with one conversion command. These
remain parent-item aliases requiring actual parent gameplay and room conversion;
prepared graphics do not make them standalone furniture imports.

The `switch-palette-fade` category discovers the complete shared building-model
callbacks. It checks all four compiled functions, normalising only verified
address relocations and local call displacements. Every call target, paired
palette/model relocation, and remaining instruction must match the shared
behaviour. Item names and model-name suffixes do not select the category.
Three display lists stay in their actual opaque-arena submission order;
the material commands inside each list retain their original rendering modes.
The exact two endpoint palettes and segment-eight loads remain dynamic.
Changing entries must use opaque RGB5A3 at both endpoints. Unchanged transparent
entries retain their colour and alpha; partial alpha is rejected.

Each converted object starts with a 32-byte immutable `AFP1` layout: magic,
16-bit complete object length, 16-bit model count, two 32-bit palette offsets
(on, off), and four segmented display-list pointers. Three pointers are used;
the fourth is zero. The converter derives these fields from the complete
compiled object. The installer regenerates and checks the header with all
other resource bytes. Generic profile model/rig/animation pointers stay null;
the native toggle flag and shared callback table supply the behaviour.

`tools/v3_furniture_palette.py` installs the shared callback in the existing
`80483400..804837FF` reservation. The legacy tent table remains at `80483700`;
generated-layout profiles use `80483720`. An immutable compatibility layout at
`80483740` describes the unchanged installed tent artwork. Both tables share
creation, movement, destruction, and drawing code; only the layout entry differs.
The N64 code approaches the switch target by the donor's float `0.1`, draws all
model layers, and allocates a 32-byte interpolated palette with a 64-byte matrix
in the current graphics frame. Submitted palettes survive actor changes and
destruction. No heap or permanent reservation grows. Invalid layouts or crowded
graphics arenas produce no draw or arena writes. The complete-object DMA reader
checks the generated header's magic, actual length, and three-model count before
recording a loaded bank. There is no per-item DMA case for this category.

Acquisition remains independent: an eligible winter-camping model can install
through the existing reward category; models needing other source routes remain
prepared-only. Model conversion never substitutes shop stock for an unknown
reward. Roof-colour selectors, clocked station rigs, and additional effects
remain separate unsupported categories, not static substitutions.

Other dynamic texture/palette pointers, animation rigs, custom callbacks, unsupported
contact/interaction flags, other action sounds or acquisition routes, oversized
or different-format artwork, and framing outside the checked source table remain explicit review
categories. Unsupported does not mean unused or unimportant. A successfully
converted object is not automatically evidence of complete gameplay.

## Shared installation

`tools/v3_furniture_install.py` binds the complete base ROM/report and source
data, regenerates the metadata/dependency description, and checks the converted
assets. It installs full profiles and item records, names/prices/footprints,
stock, catalogue entries, HRA/feng-shui rows, and selected-profile bits together.
Missing native scoring-series definitions require a category adapter. Existing
documented theme adapters retain their unavailable matching-surface policy.
Donor HRA birth categories 33 and 37 map to native scoring category 3 only after
checking their equal 412-point weights and all three actual native bitfield
consumers. This is scoring metadata only: winter/summer acquisition remains
independent in byte 27. Native weights, counters, and stack sizes do not change.

Canonical furniture identity version 2 is independent of conversion order,
checkbox selection, and resource placement:

```text
saved item ID = canonical donor 3xxx ID
runtime index = 1024 + (saved item ID - 0x3000) / 4
```

Existing native items, old explicit reservations, and display aliases remain.
The checked build manifest records each new object's VROM; it is not a saved
identity. Object storage is appended at 16-byte alignment with complete physical
and virtual overlap checks, the 9,216-byte model-bank limit, ROM boundary checks,
CRC updates, and full patch reconstruction. No new DMA-directory entry is needed.

Converter/installer revision 9 retains reuse of the preceding automatic batch's terminal
catalogue, relocation, and shop resources, because all three are regenerated.
`reuse_resource_tail` verifies the exact three-owner inventory, complete hashes,
DMA mappings, contiguous aligned extents, zero padding, terminal boundary,
resident-data boundary, other DMA resources, and every retained furniture profile.
Changed receipts, live overlaps, and non-terminal resources fail rather than
being discarded. New art starts at that checked boundary, followed by the rebuilt
owners and updated DMA mappings. Existing model VROMs and saved identities do
not move. The receipt records the reused range and source hashes. Only the fresh
output changes; input ROMs, earlier builds, and saves remain untouched.
Revision-7/8 artwork uses the same model format and remains accepted only after
all current source, identity, metadata, and complete-asset checks pass.

Stock and catalogue builders accept verified records without family switches.
Catalogue eligibility uses byte 24 of each existing 32-byte sparse item record:
`7` for ordinary A/B/C, `8` for event, `16` for train, `32` for lottery, and `0` for non-orderable
items. Byte 25 stores the donor action-sound category: `0` for none, `1` for
soft chairs, and `2` for hard chairs. Byte 26 holds the donor catalogue framing
index plus one; zero means no furniture-framing override. Byte 27 holds an
optional NPC reward route, using the actual donor list-type number; zero means
no shared NPC reward. Ordinary furniture keeps the remaining four bytes zero;
display-only aliases use the parent/footprint fields described above.
The builder populates masks for **all** installed furniture, retaining existing
non-orderable rewards and
the separate clothing-display route. Native gameplay IDs and saved formats do
not change. Profile selection still rejects absent dependencies.

`tools/v3_furniture_behaviours.py` installs the shared sound reader at `80483D00`
within the existing package. Its reservation ends at `80483FC0`, before the fire
vtables. The original sound-reader entry at `800BED5C` delegates native indices
to its unchanged body; imported indices require complete, enabled item/profile
records and a supported mode/category. Invalid imported requests return no sound.
The build verifies complete source audio, current audio resources, original
function bytes, existing fire code, and unclaimed helper padding. Linker limits
separate the shared item, tent, fire, and behaviour code reservations.

`tools/v3_furniture_placement.py` provides a complete 2,051-entry placement-layer
table at `80474200`. Native entries 0–946 remain unchanged; imported furniture
uses its canonical donor entry, and clothing display aliases use their verified
mannequin source. Uninstalled slots are zero. The immutable table and its two
guards occupy `804741F0..80474A1F`, between the twenty accessory records ending
at `80474140` and artwork starting at `80475000`. Nothing is taken from a live
object or an unselected future item slot; no resident reservation grows.

All five native table references are redirected together. The builder resolves
the actual relocation pairs, rejects shared unrelated high halves, removes
exactly ten obsolete relocations, and leaves all other owner bytes intact.
The complete native collision-registration function is checked against the
original after accounting for its changed table address. Future batches update
the same table from their records, with the installed reservation and bindings
verified first. Neither the existing item records nor saved formats grow.

The shared preview builder in `tools/v3_catalogue.py` installs the complete
41-entry donor framing table at `80474A40`. Its table, padding, and two guards
occupy `80474A30..80474B9F`, after the placement table and before accessory artwork
at `80475000`. All installed furnishings use source-derived selectors; display
aliases retain their separate native presentation. New batches reuse the same
table and reject changed prior selectors or occupied reservations.

`af_v3_catalogue_frame` keeps ordinary native construction and changes only scale
and model Y for an enabled imported furniture record with a bounded selector.
It replaces the installed item-specific Western/camping/fire preview cases.
Native items, missing/disabled records, and invalid selectors are unchanged.
The native catalogue still uses mode zero during construction, then receives
the actual source floats; donor mode numbers are never mistaken for N64 indices.
No item-record, saved-format, or permanent allocation grows.

## Shared optional NPC rewards

`tools/v3_furniture_rewards.py` verifies one call contract per acquisition
category. Complete donor gift/selection implementations and source lists are
checked. The native actor descriptor, complete owner, unchanged relocation
resource, and exact argument/call instructions are verified before installation.
The Gulliver category changes only the list argument and selection call in the
native gift function at `80A983B4`. Conversation state, inventory capacity checks,
gift animation requests, actual pocket insertion, and event completion remain
native. The selector's encoded argument contains the donor route in its high
byte and the original native fallback list in its low byte.

The shared resident reader at `80474BC0` scans enabled, canonical item/profile
records. It supports the checked single-furniture-gift call shape, including up
to fifteen existing-item exclusions, and delegates other requests to the original
seven-argument selector. Random selection retains rare/existing-item rejection
and the donor's small-list duplicate allowance. Empty or exhausted optional sets
fall back instead of looping forever. There is no per-item selection switch or generated
reward list to rebuild when checkboxes change. Sparse and non-prefix selections
use the same record flags as the existing offline composer.

The exported reward-count entry lets winter camping retain the exact native
trade body when its optional category is absent, without consuming randomness.
`tools/v3_camper_trade.py:install_shared` recompiles the dependent camping suffix
against that checked entry. It keeps the complete existing owner/relocation
allocations, rebuilds only suffix relocations, and verifies that original code
and state outside the two entry hooks remain unchanged at two relocation bases.
The ten summer items come from source-derived records, not a runtime item array.
Both camping categories stay non-orderable and outside ordinary shop stock.

The code and guards occupy `80474BB0..80474FEF`, between catalogue framing and
accessory artwork. Startup explicitly invalidates this new code range after its
existing checked package transfer. Permanent RAM reservations do not grow.
An originally compressed NPC owner gets one uncompressed blob mapping before
the three regenerable terminal resources. Its VROM and relocation identities
remain unchanged; future batches update this verified owner in place. Separate
`owner_moves` receipts keep the three-resource tail-reuse contract intact.

The train category appends source-identified items to the already existing
native list 4; it needs no new runtime adapter. Catalogue orderability follows
that actual list, while Gulliver souvenirs remain non-orderable.

## Verification policy

`tests/test_v3_furniture_pipeline.py` checks shared parser rules, source
relocations, independent complete texel/triangle comparisons, metadata/provenance,
current cartridge installation, retained data/code, and subset composition.
The catalogue mask and seating-sound readers have address/undefined-behaviour
sanitizer checks.
Material checks decode the compiled texture format, palette mode, line stride,
S/T scale, wrapping, and independent shifts against the donor commands. Complete
sample, vertex, triangle, and material checks also cover prepared-only objects.
Direct-colour checks independently compare every RGB/alpha sample after untile,
reject partial alpha and incomplete blocks, and verify the actual donor
executable's complete format table. Shared placeholder-profile discovery is
checked against both actual profile tables, not a manually maintained item list.
Storage tests reject changed tail receipts/data and live-profile overlaps, check
every previous model unchanged, and verify reuse again from the newly built receipt.

`tools/v3_furniture_batch_smoke.py` and
`tests/scenarios/v3_furniture_batch.json` are reusable across future batches.
The manifest selects representatives by stock group, footprint, model layers,
action sound, placement/interaction flags, contact behaviour, preview mode, and lighting category,
preferring larger assets. The check exercises actual
native owner loading,
model DMA, item readers, placement, catalogue eligibility, acquisition, ownership,
state restoration, and guards. The sound check executes the actual native entry,
including original fallbacks, imported modes, disabled profiles, and invalid
indices. It checks returned sound IDs without playing audio through hardware.
Placement checks cover the complete resident table/guards, all five bindings
after relocation, and the actual native no-collision registration routine.
It does not create a new scenario per item.
Framing checks compare every preview field after the actual native helper runs,
including source floats, unchanged surrounding fields, disabled imports, invalid
selectors, native fallbacks, and the complete resident table/guards. Calling this
helper does not establish complete catalogue construction or GPU appearance.
The bed categories exercise the actual native head-direction and both side-position
functions with one representative per changed contact category in all four rotations,
check inactive-bed rejection, and preserve the complete temporary actor. Double
beds retain their wider side span and half-cell pillow offset. Four-cell footprint
checks retain the same upper-left anchor and clockwise cells in every rotation.
The shared sound check selects new batch records, not all previously installed
chairs; unchanged audio/code evidence stays in the checked build contract. This does
not establish an ordinary player climbing onto or leaving the bed.
GPU appearance, ordinary interactions, and save/restart require the gameplay pass;
memory-reader checks do not claim them. Retain passing unchanged evidence.

Reward checks use the same representative batch probe: actual owner loading and
relocation, installed hook instructions, isolated sparse selections, no-selection
native fallback, and reservation guards. A checked low-RAM bridge reaches the
actual upper-memory helper without widening the debugger's call permissions.
Host sanitizer checks additionally cover multiple route values, malformed or
disabled records, rare-only fallback, random rejection, and all seven fallback
arguments. These checks do not claim an ordinary Gulliver conversation or gift
animation has been played through.
The same batch probe exercises complete native winter/summer trade preparation,
using the real RNG with verified seeds, one selected reward, and winter's
no-selection fallback. Input names/slots, carpet/wall candidates, and pitfall mode
are retained. Host checks cover both seasonal thresholds, house override and
empty-house fallthrough, all ten summer candidates, and duplicate/exclusion rules.
Ordinary camper conversations, handover animation, and save/restart remain
separate gameplay verification.

Set `V3_FURNITURE_PREPARED_ART` to a prepared-asset output directory to run the
same complete texture/vertex/triangle/material checks on that batch. The shared
test also checks source identities, retained pending reasons, and refusal by the
installer. No new test scenario is needed for another prepared category. A
converter-only change does not call for another native run of an unchanged ROM.

Palette-category batches also run the actual shared C callbacks under address/
undefined-behaviour sanitizers with every prepared object's source-derived
palettes. Checks cover complete draw order, independent fade state, mid-fade
reversal, frame lifetime, malformed layouts, crowded arenas, and actor guards.
The existing representative native batch probe checks one new category record
and the changed legacy-tent compatibility path together, including actual model
DMA and callback execution. It does not create a separate scenario per building.

See [the implementation checkpoint](../docs/checkpoints/V3_FURNITURE_PIPELINE.md)
for actual outputs, counts, and verification results.
