# Automatic furniture import pipeline

## Workflow

### Changed-owner storage

The shared runtime refresh retains each changed overlay's logical DMA identity.
Uncompressed, same-sized owners can be updated in place; owners inside the
import blob also update that blob's authoritative contents and checksums.
Compressed or explicitly permitted resized owners use complete uncompressed
copies in verified unused physical cartridge-tail space. `owner_tail_storage`
checks the 64-MiB bound, sixteen-byte alignment, zero destination, and every live
physical DMA extent, including the proposed new end of the import blob. Old
compressed bytes remain untouched but are no longer referenced by that owner.

Do not consume the protected English-choice VROM range or relax import-blob
growth checks to store an overlay copy. Resource-tail reuse still owns only its
three declared catalogue/shop resources. Every complete changed owner must match
the final DMA extraction. This shared storage rule adds no item-specific paths,
saved formats, or browser choices. The wrapped-gift stage uses it for the native
hand owner; its tag owner remains an in-place update.

### Bulk compilation and prepared-artwork reuse

Furniture `convert` and `import` preflight the entire selected batch, then compile
all missing display lists in one existing toolchain container. Every object has
separate sections and exact checked lengths. The compiler has no network and
can write only the fresh output directory. Empty compilation batches start no
container. The single-object API remains available to other representations.

Repeat `--reuse-assets <directory>` to consume existing ready or prepared artwork
bundles. Reuse checks the exact donor REL/symbol identities, complete regenerated
resource bytes, emitter source, every model span/hash, draw sequence, skeleton,
and animation suffix. The reconstructed complete object must match the cached
object. Conflicting or changed caches fail; unknown formats and escaping paths
are rejected. Earlier manifest revisions are usable only when all current
artwork checks pass. Cache receipts retain the source manifest/object hashes.

Eligibility, identity, names, behaviour, and acquisition are regenerated using
the current rules. A prepared bundle cannot be installed directly or use its old
metadata to bypass missing gameplay. An item whose category is now complete can
reuse its verified graphics while receiving fresh installation records. The
output `batch` receipt records object, reuse, compilation, and container counts.
Use a fresh ignored output path and the explicit current proposal lock.

### Shared runtime categories

The `scenery` representation follows complete seasonal foreground descriptors
and feeds body/shadow lists into the shared converter. Its gold-tree category
prepares growth sizes, dead saplings, stumps, seasonal palettes, and adjusted
shadows through explicit inherited render contracts. This is an acquisition
dependency, not a selectable item or completed acquisition. Use
`convert --representation scenery --category gold-tree --assets-only`;
the shared `--refresh-runtime --scenery-art` installer connects owner-local
banks, descriptors, palette updates, and classification to all four native
renderers. The subsequent `--refresh-runtime --scenery-gameplay` stage connects
shared source-table growth/stump helpers and selected shovel planting conversion
to all four seasons, with lazy code loading before a seasonal actor exists.
Its next shared stage connects the daily owner, growth/death, cross-acre neighbours,
sapling records, and source-priority thinning. Native routines/house protections
remain; only the shared code reservation grows by 4 KiB. The next refresh reuses
that installer to connect hidden bee/furniture/Bell recording and refilling.
Complete donor tables supply the gold-family identities while original native
acre scheduling, quotas, random selection, and unrelated holiday callers remain.
This fits existing memory without reconverting assets or adding an item-specific
installer. The subsequent refresh connects core collision, shovel-removal, and
NPC-walkability queries through one ABI-preserving lazy-loading gate. Real item
exclusions precede temporary geometry mapping; saved foreground data is never
rewritten for collision. This also fits existing reservations. The seasonal
interaction refresh extends native drop records and cut-count initialization,
preserving actual native landing, furniture luck, bee spawning, and all native
rows. It uses source category records once for all four seasons, including all
nine initialization callers, and adds 4 KiB fixed code reservation. The player
query refresh binds complete source/native consumers and replaces eleven
axe/shovel/shake/bee sites through one register-preserving lazy-loading gate.
It reuses replaced inline code and existing packet space, retaining native
target filters, timing, identities, and all allocations/saves. Its next refresh
extends the final stump predicate and four seasonal conversation-camera callbacks,
retaining original height geometry and real foreground identities. It fits the
same reservation and adds no item-specific installer. The field/insect refresh
extends the existing clearing helper and both native tree-habitat consumers,
preserving the N64 entrance layout, original ranges, candidate selection, and
bee-tree exclusion. It also fits existing memory and uses complete category
rules. The planting-completion refresh adds all four source-positioned sapling
sparkles through the native effect and unchanged bounce/cleanup timing. It
rebinds existing field/insect consumers without repeating their relocation.
Complete gold-tree leaf/cut effects still precede ordinary acquisition. See
[seasonal scenery](V3_SCENERY.md).

The shared flying-balloon category installs one complete donor state machine
for all eight shapes, reusing complete converted resources. Its additive actor,
private model/motion banks, player creation, physics, and native drawer preserve
the existing gift balloon and all original actor descriptors. Code and the
descriptor fit checked unused module suffixes; only transient scene allocations
grow. The shared consumer stage connects release/look, exchange, and fall/get-up
with native creature fallbacks and no further allocation. The ordinary inventory
stage appends the donor `Let Go` menu for all eight shapes, retains all original
menu rows, and grows the shared menu reservation by 384 bytes. See
[flying balloons](V3_BALLOON_RELEASE.md).

The shared inventory exchange stage carries the source reward condition through
native normal-drop, empty-hand, burying, and fish/insect release routes. Existing
transient unions hold the deferred flag; ordinary setters clear it, rejected
requests preserve it, and actual native setup/animation precedes celebration.
Two checked unused code suffixes hold the implementation without module/save/
allocation growth. Balloon exchange and the ordinary inventory option use the
shared flight action; source acquisition remains unfinished;
the golden-tool choices stay disabled. See
[deferred exchange](V3_REWARD_ACTIONS.md#inventory-exchange-and-deferred-completion).

The shared collection stage connects all four source non-exchange collection
tails through one reward adapter and one active-player completion query. It
preserves source priority ordering, original item transfers, animation timing,
early returns, and full-pocket branches. Complete native action bindings handle
the donor/native Putaway ordering difference explicitly. The new code fits the
existing reward reservation; no item-specific installer, save change, or option
is added. The exchange stage connects normal/bury/fish/insect consumers; the
shared flight stage connects balloon release. Ordinary acquisition remains required. See
[reward collection](V3_REWARD_ACTIONS.md#collection-consumers).

The shared reward-action stage registers all complete callbacks for source
actions 118–120, retaining other actions and all metadata. Shared requests keep
native permissions and donor priorities; the axe delay preserves idle animation
continuity and uses the native interval. Both code groups fit unused existing
module space. The actual registered native transitions and persistent settlement
have passing component evidence. Ordinary acquisition remains required before
enabling golden-tool choices. See [reward actions](V3_REWARD_ACTIONS.md).

The shared player-action reward-state stage follows the control stage. It
installs independent per-player trophy/celebration flags, persistent settlement,
and explicit format-3 migration through `tools/v3_save_rewards.py`. Existing
catalogue/profile offsets, public entry addresses, item-reader suffix, source
identities, and permanent reservations remain intact. Offline and private browser
exports use the actual build's save warning; neither served patcher is updated.
The action stage connects registration/requests; ordinary acquisition remains required.
See [reward persistence](V3_REWARD_SAVE.md).

The shared player-action reward-control stage follows the installed message
phase. It connects source setup/main behaviour and native fanfare requests in
checked unused icon-reservation space, preserving resources, action registration,
saved formats, and selections. Its complete source/native audio audit reuses
existing native sequences, fonts, and samples. The action stage supplies complete
registration; ordinary acquisition remains required before enabling tool choices. See
[reward controls](V3_HANDHELD_ITEMS.md#shared-reward-controls-and-fanfares).

The player-action refresh installs complete reward motions and generic eye/mouth
timelines through the existing player-resource category. It discovers source
indices from the donor setup, preserves complete animation/frame arrays, retains
the native banks and module size, and uses checked unreferenced retired storage
before appending. Native indices and tables remain intact; resource installation
does not enable reward actions or item choices. See
[reward motions](V3_HANDHELD_ITEMS.md#shared-reward-motions-and-player-faces).

For installed handheld categories, the shared `--refresh-runtime --player-actions`
stages also connect source behaviour. The golden-net capture stage preserves the
native candidate/forced-capture algorithms and supplies the donor's normal or
golden dimensions through unused outgoing argument words. It retains source
assets, fixed identities, selections, and save formats; geometry installation
does not enable unfinished tool choices. See
[golden-net capture](V3_HANDHELD_ITEMS.md#shared-golden-net-capture).
The next stage uses shared source-derived angle/timing readers for both native
fish behaviours. Normal fishing stays unchanged; selected golden rods use the
donor differences in native timing units. The existing resource-tail allocator
handles the compressed fish owner without extra resident memory. See
[golden-rod response](V3_HANDHELD_ITEMS.md#shared-golden-rod-response).
The shovel stage uses the actual player's kind, retained native digging, and
source position/RNG rules to generate the 100-Bell bonus. It reclaims a verified
4-KiB portion of a retired audio sequence, retaining the live relocated sequence
and every existing code/state address. See
[golden-shovel digging](V3_HANDHELD_ITEMS.md#shared-golden-shovel-digging).
The inventory stage discovers all four golden tools through shared parent aliases
and source preview tables. It reuses complete installed equipment resources and
native static/skeleton consumers, adding the complete native-format donor bobber
through a strict native-reference graphics adapter. Existing allocations, choices,
and saves remain unchanged; parent/acquisition integration is still required.
See [golden-tool previews](V3_HANDHELD_ITEMS.md#golden-tool-previews).

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

Within that representation, `--category animated-held-model` prepares complete
supported rigs through the same graphics compiler and checked skeleton packer.
It preserves every joint/model binding, uses the actual motion dependencies,
and records combined model/animation sizes. All eight pinwheel rigs convert;
the two oversized variants require shared native-bank work, not reduced art.
The separate prepared-rig format is rejected by the static/furniture consumers.
The same shared runtime installer accepts it explicitly through
`--refresh-runtime --equipment-rigs <prepared-directory>`, retains complete
artwork, expands both native banks and their containing scene allocation, and
invalidates cached animations when a model change moves their addresses.
Other prepared animated categories require explicit runtime category and joint
capacity contracts; broader converter support does not expand an installed
runtime category. This installs resources, not selectable pinwheel gameplay. See
[animated-held preparation](V3_HANDHELD_ITEMS.md#complete-animated-held-preparation).

Within the handheld representation, `--category item-category-art` prepares
the separate ground/police/handover graphics through shared material/geometry
conversion. All extra equipment parents are grouped from actual source type
tables, not an item list. Complete six-owner source relationships and split
lists are retained; neither furniture nor equipment-resource installation
accepts this distinct prepared format as gameplay support. See
[category preparation](V3_HANDHELD_ITEMS.md#shared-category-preparation).

`--refresh-runtime --item-category-art <prepared-directory>` on the shared
installer consumes the complete category bundle explicitly. It installs the
actual artwork and selected-parent lookup, shares extended police/handover
tables, and grows the police stack and actor capacities together. It retains
original categories and does not enable imports before seasonal ground and
acquisition support are ready. See
[category runtime](V3_HANDHELD_ITEMS.md#shared-police-and-handover-runtime).

Shared reader changes use the same installer's `--refresh-runtime` mode. It
updates the checked current cartridge without reconverting or reinstalling any
existing artwork. Ordinary reader refreshes retain the complete DMA directory
and allocations. The optional `--equipment-art` adapter installs the complete
checked held-resource category and its shared loader, moving only the three
unchanged terminal catalogue/shop owners; see [held equipment](V3_HANDHELD_ITEMS.md).
Both paths preserve profiles and saved identities and emit a new build lock and
reconstructible patch. This is a shared runtime update, not a separate installer
for each item.
`--refresh-runtime --translation-updates` carries the checked Museum-header
correction, expanded letter-name bounds, and an explicit corrected import-free
translation pin through the same resource-tail, startup, checksum, and lock
machinery. Existing imported artwork, profiles, and behaviour code stay intact.
See [translation integration](MUSEUM_LETTER_HEADERS.md#v3-integration).
`--refresh-runtime --event-acquisition` consumes the donor's shared event stock
categories and adds separate selected-only stock while preserving native wares.
It requires the ground-enabled base explicitly and does not enable imports.
On a stock-enabled base, the same adapter installs the shared route selector,
purchase/payment/handover code, and source-correct dialogue without replacing
original merchandise. The same handheld scan records acquisition on the existing
parent identities. Collection/catalogue and ordinary gameplay remain required. See
[event stock](V3_HANDHELD_ITEMS.md#shared-event-stock).
`--refresh-runtime --held-collection` connects those installed parent records to
native acquisition, the four-player collection query, and existing saved
ownership without another allocation or enabled choice. Its complete donor-list
audit records the actual umbrella-tab membership and position. See
[held collection](V3_COLLECTION.md#shared-held-parent-collection).
`--refresh-runtime --held-catalogue-art <prepared-directory>` consumes those same
records and the complete prepared models to extend the umbrella list and native
preview readers. Tagged sparse profiles require the parent's selection; inverse
aliases provide its full name/price without changing ordinary room drops. The
shared catalogue rebuilder retains this category in subsequent furniture batches.
No standalone representation choices or new profile bits are introduced. See
[held catalogue](V3_CATALOGUE.md#shared-handheld-representations).
On a catalogue-equipped build, the same command expands complete implemented
equipment categories in one refresh. It verifies and retains all existing parent
identities, rebuilds the selection/name/price/icon/collection tables, appends only
missing prepared catalogue models, and extends the experimental profile. No
per-item installer, repeated first-install stages, or new action code is needed.
Animated room categories reuse their already installed complete resources.
Source catalogue indices remain separate from fixed N64 destination indices;
the older donor range does not reuse native furniture. Shared sparse profiles
bind the room vtable, and the forward alias index includes only categories whose
donor room placement really converts the parent. Inverse pickup and collection
continue to share one parent selection and one saved ownership bit.
The source-derived inventory bindings must already match. See
[category expansion](V3_HANDHELD_ITEMS.md#shared-parent-category-expansion).
`--refresh-runtime --held-selection` prepares the full experimental parent profile
after these adapters are installed. Offline/browser composition derives each
equipment choice and its representation from the checked records, including
selected umbrella counts. Use an explicit proposal lock; this does not promote
an unresolved build or update either patcher. See
[equipment selections](V3_OPTIONAL_COMPOSITION.md#shared-equipment-selections).
`--refresh-runtime --player-motion` extends that same resident module with the
complete source-derived player motions and split-body masks. It retains the
native player owner's table relocations and all original animation meanings;
resource availability does not enable item actions or add profile choices.
`--refresh-runtime --equipment-kinds` connects the six dependent kind-indexed
readers and source-selected tumble/get-up animations in that module. It retains
the original equipment selector until actual category actions and profile-aware
inventory/acquisition are ready. These shared records do not create per-item
installers or independent options for worn states and catalogue models.
`--refresh-runtime --player-actions` extends the player's shared metadata and
callback tables while preserving all 105 native actions. Full donor metadata
does not enable unimplemented callbacks; the shared dispatch resolves the live
player owner instead of retaining stale relocated pointers. The same module's
checked startup transfer covers its additional 16-KiB reservation. See
[held equipment](V3_HANDHELD_ITEMS.md#extended-action-tables).
On a cartridge with those tables, the same adapter installs the donor fan's
controls/setup/transitions into unused action-code space. The shared refresh
supports in-place code updates without growing or relocating unchanged ROM
resources. The same adapter adds the per-frame callback and shared single-layer
sound-program conversion, retaining the source pitch sweep/envelope and reusing
an equivalent native instrument/sample. Native frame speed and braking use the
corresponding N64 timing. It registers complete implemented callback groups,
including the fan's setup/main/native net reset, and redirects its four ordinary
input polls through the shared umbrella-then-fan helper. The source/owner audit
retains unrelated core limits and umbrella repeat behaviour; obsolete local JAL
relocations are removed for resident calls. Crossed and wrapped frame events
retain release/repeat transitions at the native update interval. Other incomplete
action groups remain disabled. The same adapter installs source-derived selected
equipment records and extends passive-item visibility without replacing the
native switch or bypassing scene/hidden-item checks. Each parent uses its actual
collection identity's profile bit; preparing records does not enable that bit.
Parent inventory/readers/acquisition and optional composition remain required
before choices are enabled.
The same refresh adds parent name/price records from installed equipment
descriptors. It uses the existing metadata wrapper and reserved equipment memory,
without shifting action callbacks or creating item-specific scripts. Official
name credits retain their actual donor table/index in the single provenance
catalogue. The source inventory category is recorded but is not installed as an
unchecked native category index. The same refresh discovers complete pocket
icons from those installed parent records, deduplicates and converts their donor
artwork, and connects the selected-only native tool-icon reader. It preserves
gift/umbrella priority and original descriptors without growing any allocation.
Source category 43 is distinct from the ID-derived tool menu category two;
remaining category consumers and acquisition still require integration.
The same refresh connects the separate inventory-screen equipment owner through
source-derived preview records, preserving all original tool kinds and the
native empty sentinel. Shared model/pose tables and owner-relative draw dispatch
reuse installed resources; the complete module grows by 4 KiB without enlarging
ordinary model/animation banks. No fan is enabled by that integration. See
[inventory previews](V3_HANDHELD_ITEMS.md#shared-inventory-equipment-previews).
The table converter also extends the two held-item main/draw tables, preserving
all original tools. Source static-held drawing uses the existing equipment
resources and native outer draw setup. Unimplemented rig categories retain null
callbacks. Refreshes account for changed uncompressed owners already stored
inside the blob before computing the complete blob receipt.
After complete animated resources are installed, the same `--player-actions`
route connects shared pinwheel setup, movement/wind, animation, and drawing.
It grows the actual player allocation for transient state and retains every
original callback/resource. On an action-enabled base, the same route adds the
complete source sustained loop through the shared level-sound converter and
native speed-dependent volume consumer. The subsequent refresh connects complete
animated inventory records, native skeleton drawing, and donor preview timing,
retaining existing banks and original tool behaviour. Parent readiness remains
required; these refreshes do not enable choices.
With both joint work areas expanded, the same route installs complete source
balloon setup, hand tracking, physics, animation, and reflected drawing through
shared category 21. It retains existing resources/choices and saved formats.
The adjacent sound sequence moves intact to allow the 60-KiB module; its actual
native header and startup transfer are updated. The next shared refresh adds
complete balloon inventory records, source idle-animation remapping, and native
reflection drawing without changing existing entries or allocations. Parent
integration and actual animated room placement remain required before selection.
See [animated-held actions](V3_HANDHELD_ITEMS.md#shared-animated-held-actions)
[balloon actions](V3_HANDHELD_ITEMS.md#shared-balloon-actions), and
[loop sound](V3_HANDHELD_ITEMS.md#shared-held-loop-sound).

On a complete animated-parent build, the same route connects shared native tool
input predicates, then action animation/moving setup and rod lifetime. It maps
actual source families and complete motion resources while preserving original
tools and matching native renderers. These stages use existing code space and
do not enable tool choices before golden effects, remaining action checks,
inventory, and acquisition are connected. See
[tool animation setup](V3_HANDHELD_ITEMS.md#shared-tool-animation-setup).
The following stage connects net request/transition predicates and shared fall/
get-up setup while retaining actual tool identities, native priorities, and
all earlier code. Golden effects and the donor's separate balloon-release
behaviour remain explicit dependencies; see
[tool recovery](V3_HANDHELD_ITEMS.md#shared-net-transitions-and-tool-recovery).

The same route installs complete reward motions and shared facial timelines,
then the source-backed reward-message phase and all four official messages.
The text adapter extends the checked native bank and source catalogue through
the existing text-region repacker, without consuming the bounded import blob.
Later refreshes preserve those resources. Installing these components does not
register incomplete reward actions or enable golden-tool choices. See
[reward messages](V3_HANDHELD_ITEMS.md#shared-reward-messages).

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
category equivalent delegates to an original native item. Real room forms also
store their source size code at byte six and footprint eligibility at byte
seven. The selected parent's sparse profile still gates access. Catalogue-only
forms retain zero eligibility; using that zero for a room form makes the native
footprint reader treat it as absent. Neither eligibility nor the source size
creates an independent name, price, ownership bit, or selection. Ordinary
furniture records keep the final four bytes zero.

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
- Complete IA8 textures up to 2,048 bytes, untiled from GX IA4 eight-by-four
  blocks with intensity/alpha nibbles swapped into native order. Every alpha
  level survives; texture-LUT disabling, eight-bit line stride, wrapping, and
  independent shifts are retained. `ia8-materials` selects these objects.
  The same verified donor format table maps IA/8 to GX IA4; `texconv_tile`
  in the donor source documents the inverse nibble conversion.
- Animated-held descriptors additionally supply each visible joint's matrix
  availability. Model-view loads may address only current/earlier matrices in
  segment `0D`. Partial vertex loads preserve cache destinations and previous
  transformed vertices; unloaded triangle indices and future matrices reject.
  Static descriptors do not gain permission to read an unspecified matrix bank.
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
It supports fixed one-, two-, and three-model opaque sequences without item definitions.
Other draw operations, transformations, state changes, and lifecycle effects fail.

The two-model form additionally binds a complete constant sixteen-colour palette
through the checked segment-eight assignment. Its palette and both model
addresses come from paired code relocations, not item IDs. The normal converter
resolves palette loads into each object's private resources and retains the
complete cup/base submission order. `constant-palette-model-sequence` selects
this subset. Fishing-trophy acquisition remains a separate required adapter;
converting both donor colour variants does not enable their imports.

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

The `switch-trigger-sound` category retains ordinary profile model slots alongside
a checked move-only callback. The two complete source instruction forms differ
only in loading a normal or singleton-tagged sound word. Every instruction,
constant field, helper target, and absence of other lifecycle/draw/DMA callbacks
is checked. Source excluded actor states, switch flag/value, position field, and
the full sound word remain in the descriptor. The converter does not mistake a
callback-bearing object for silent decoration. Artwork can be prepared as a
batch; native audio correspondence, callback integration, and acquisition remain
required before metadata can permit installation. Additional particles, movement,
or instrument behaviour reject rather than passing through this category.

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

The `indexed-switch-rig` category retains complete animated room objects selected
by a checked callback index. `tools/v3_furniture_rigs.py` verifies complete create,
move, draw, and destroy instructions, every relocated dependency, the actual
local keyframe/matrix calls, both full skeleton/animation tables, source float
constants, and both effect-free joint callbacks. Unknown lifecycle effects or
incomplete dependencies reject. The source selector supplies the origin and
bounded table position; no maintained per-item list chooses models or motions.

The shared keyframe model descriptor feeds all visible joint roots into the same
material/vertex/triangle converter used by handheld rigs. Each compiled object
appends its complete skeleton and animation, including every keyframe array and
relocated pointer. The animation packer accepts an aligned object offset; its
default zero-offset format and all existing held resources remain unchanged.
No animation is flattened into a decorative model.

The `indexed-loop-clock-rig` category uses the same complete model, skeleton,
motion, and batch compiler. Its three checked sixteen-entry tables select a rig,
animation, and constant palette together. Both create/draw selectors must agree;
every lifecycle instruction, relocated dependency, helper call, speed constant,
and joint callback is verified. The last source table entry duplicates the
fifteenth variant; table padding does not create another selectable item.

This category prepares all fifteen station models in one invocation. Each keeps
five joints, three visible lists, the complete 100-frame animation, and its own
palette. Source repeat speed is `0.5`; the before-draw callback subtracts the live
hour/minute angles from joints three/four about Z. The descriptor retains those
rules and the exact source clock owner/fields for runtime integration. The
prepared object includes all graphics and keyframe data, not a frozen decorative
substitute. The shared room engine supports the live clock callback. Installing
the complete clock resources and source acquisition route remains required;
prepared resources do not enable these records.

The `open-close-storage-rig` category shares the same complete graphics and
keyframe conversion. Verified create/move/draw/destroy instructions supply the
actual skeleton, stop-mode motion, initial zero speed, opening limits, and nullable
shared room callback. Drawers, wardrobes, and closets retain their source
interaction flags; those flags cannot enter unrelated callback categories.
The Harvest bureau and dresser retain five/three joints and complete twelve/ten
frame motions respectively. Non-finite or out-of-motion limits, changed helpers,
extra lifecycle effects, or missing dependencies reject. Prepared objects remain
disabled until actual acquisition and ordinary item profiles are connected.
The shared runtime installs their complete resources and storage callback.

The switch-driven category prepares all eight room balloons in one command:

```sh
python3 tools/v3_furniture_pipeline.py convert --assets-only \
  --category indexed-switch-rig \
  --base-lock build/v3-balloon-inventory-02/build-lock.json \
  --output build/room-rig-assets
```

The source-only furniture index decoder handles both `1xxx` and `3xxx` ranges.
The ordinary worksheet scan remains restricted to its existing `3xxx` entries
plus older-range IDs proven by shared room aliases; it does not offer the entire
native furniture range as new imports. Names use the matching official source
table and retain the parent identity. Source IDs/indices do not assign N64
destination IDs, enable items, or create independent furniture choices.

Room balloons have six joints, five visible lists, and a 61-frame motion, unlike
their held models. The retained source behaviour starts at zero speed, approaches
0.5 by 0.01 per source update, targets 1.25 after interaction, and returns toward
0.5 after reaching that target. The shared runtime implements two source steps
per native update, consuming the switch pulse once. Complete prepared assets are
4,656 or 7,040 bytes each and fit the existing 9,216-byte room bank. They require
44,400 bytes of ROM storage together. Context-correct placement/pickup and
profile/collection readers come from the shared parent-category adapter, not
asset preparation. The ordinary installer rejects
prepared data and unsupported animated lifecycle metadata. See the
[conversion checkpoint](../docs/checkpoints/V3_FURNITURE_PIPELINE.md#shared-indexed-room-rig-preparation).

`--refresh-runtime --room-rigs-art <prepared-directory>` installs this complete
category through the existing resource-tail and build-lock machinery. It verifies
every prepared source binding, model, skeleton, animation, and command source;
it does not recompile artwork. The checked retired-module allocator supplies
the full 44,400 bytes without extending into English choices or moving live data.

The initial lifecycle code occupies `804B1800..804B1DFF`, with immutable descriptors at
`804B1E00..804B1F9F` and a five-entry vtable at `804B1FA0`. Existing held code,
loop-volume state, the module guard, and the 60-KiB resident allocation retain
their bounds. Twenty-four descriptors fit; actual room rigs use six joints and
five visible lists. The native actor's seven used morph vectors end at `204`;
eight of the remaining twelve morph-work bytes hold per-instance speed/target.
No native tail field, saved field, or joint matrix is borrowed for this state.
Drawing uses the actor's current matrix bank and the actual parent transform,
checking opaque and translucent command capacity before submission. Native
graphics allocations require eight-byte alignment. A valid matrix-allocation
tail ending in eight must render; requiring sixteen-byte alignment incorrectly
suppresses the entire model in ordinary rooms. Misaligned tails and insufficient
space still reject before writing commands.

Registry version one reserves source `1FF0/1FF4/1FF8/1FFC` as destination
`3C00/3C04/3C08/3C0C`, beyond the complete `3800..3BFC` garment range. Source
`3000..300C` retains its canonical destinations. These fixed reservations do not
install profiles, set save-profile bits, or create selectable imports. The
parent-category refresh connects those consumers before enabling records. The
same lifecycle lookup handles a real catalogue actor's index, which is 1024
above its imported room index; the native catalogue retains its own animation
update and preview timing. See the
[runtime checkpoint](../docs/checkpoints/V3_FURNITURE_PIPELINE.md#shared-room-rig-runtime).

Three complete pocket-icon families use the existing descriptor/texture area
and a checked 96-byte palette bank at `804A67A0..804A67FF`. All original palette
and texture bytes survive. Parent code ends before the palette bank; the reader
accepts only complete palettes in that bank or its original range, and textures
remain inside the original range. A shared reader refresh preserves fixed public
entries and updates the actual menu hook if the private assembly entry moves.
No resident allocation grows. Catalogue rebuilding retains the verified
inventory-work pool increase and accounts for it in both required and reserved
memory, instead of replacing a newer menu allocation with the stable baseline.

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
reward. Roof-colour selectors and additional effects remain separate unsupported
categories, not static substitutions. Clocked rigs have complete prepared assets
but still require their native clock/lifecycle adapter.

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

### Shared room-category runtime

The extended installer accepts repeated `--room-rigs-art` prepared bundles through
the same complete-art validator. Source category records determine behaviour:
switch-driven repeat, clock-driven repeat, or native storage opening/closing.
No item-specific callback or installer is needed. Actual profile/acquisition
eligibility remains separate; installing resources does not enable items.

The current runtime owns `804B8000..804B9FFF`: 4 KiB for code and 4 KiB for a
header, up to 128 twenty-four-byte descriptors, and zero padding. This sits after
the gold-tree code's `804B5000..804B7FFF` reservation and before the fixed model
pool. Future reservation growth must preserve both owners. It adds 8 KiB of
fixed Expansion Pak space without growing scene actors or model banks.

Each descriptor contains the canonical index, complete object length, skeleton
and animation pointers, joint/visible counts, category, zero reserved byte, and
two category parameters. Switch rigs require zero parameters. Clocks supply
distinct hour/minute joint indices; storage supplies finite start/end frames
within the complete source motion. Current native work supports at most six
joints. The existing complete-object and pointer bounds remain mandatory.

The stable vtable at `804B1FA0` dispatches through a bootstrap in the old code
reservation. The bootstrap loads and verifies the complete packet, updates both
caches, and records its checksum at `804B1E00`. Startup reloads that word as zero,
so a soft reset cannot trust stale upper-memory code. Packet/compiler bounds,
checksum failures, changed old code/resources, occupied identities, and lack of
verified cartridge storage reject. Existing balloon assets/profiles stay intact.

Clocks play two source half-speed updates per native frame. Their joint callback
uses native hour/minute fields `80136FC6`/`80136FC4`, retaining sixteen-bit angle
wrapping and subtracting about Z. Storage starts stopped and calls the existing
nullable room clip at `80136F2C`, callback offset `34`, with source opening limits.
The complete native state machine, sounds, and interaction timing remain native;
only its already installed expanded-profile table differs from original code.
Catalogue drawing without a room owner cannot advance storage interactions.

The current packet contains the eight existing balloon rows and both Harvest
storage rows. All fifteen clocks are converter/descriptor-ready but not installed
or selectable. Complete clock assets require the next general cartridge-storage
expansion. Do not overwrite protected English resources or relax storage bounds.

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
