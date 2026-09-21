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

Do not consume a live English-resource range or relax import-blob growth checks
to store an overlay copy. The checked resource-capacity adapter relocates both
shared English readers/resources before permitting the expanded bound.
Resource-tail reuse still owns only its
three declared catalogue/shop resources. Every complete changed owner must match
the final DMA extraction. This shared storage rule adds no item-specific paths,
saved formats, or browser choices. The wrapped-gift stage uses it for the native
hand owner; its tag owner remains an in-place update.

### Bulk compilation and prepared-artwork reuse

Default discovery includes worksheet `1xxx` entries whose native ID/name/model/
texture correspondence is unresolved, alongside the `3xxx` range and explicit
room aliases. Missing correspondence is a review condition, not proof that the
entry is new furniture. Dummy resources and parent/display representations keep
their actual discovery reasons. No legacy donor number becomes a native ID.

`--assets-only --category legacy-static` prepares complete supported static
models from that range in one compiler batch. The native-correspondence and
additive-destination gate remains ahead of ordinary installation for unreviewed
identities. Prepared
bundles retain full donor name/source records and use the same texture, geometry,
material, and cache-validation machinery as the other categories. Source profile
indices in these prepared records are not assigned N64 destination indices.

### Stable donor and destination records

The registry reserves reviewed ordinary legacy identities in `3C10..3C2C`,
after the balloon displays at `3C00..3C0C`. Existing native IDs, the entire
garment display range, and every previous import reservation remain intact.
Reservations are literal and append-only, not assigned by selection order.
The eight current mappings identify ordinary Gulliver souvenirs; acquisition,
graphics, and behaviour still come from source records, not that registry.
Other legacy entries remain in review until identity and representation are
established. Unresolved worksheet cells alone do not justify a new identity.

Installed records keep `id` as the canonical GameCube identity. `item_id` and
`runtime_index` identify the N64 destination; differing mappings also require
`donor_item_id` and `donor_runtime_index`. Registry version 3 records express
this distinction. `v3_registry.furniture_source` checks the full pair before any
donor-table access. Same-identity records retain their previous representation.

Source indices drive names, prices, action sounds, placement categories, HRA,
feng shui, catalogue framing, and acquisition-list membership. Destination
indices drive native profiles/readers, placement/scoring tables, catalogue
encoding, inventory IDs, and saved selection/ownership bits. Graphics cache keys
and filenames remain source identities. Neither prepared manifests nor same-ID
arithmetic can bypass the mapping check.

The shared ordinary installer consumes these records without another category
installer. Gulliver's existing reward category returns selected destination IDs
and keeps souvenirs non-orderable. Browser/offline options remain source IDs;
catalogue packing and villager-house dependencies resolve those IDs to installed
destinations. Empty profiles retain the pinned translation-only build. New
destinations use existing saved format 3, but older builds lack those items and
cannot accept saves which require them.

Rebuilding the catalogue retains the checked chain of existing submenu pool
increases for inventory joints and the balloon menu. Every before/after word,
positive aligned increment, and final live instruction must agree. The builder
does not reduce those allocations or accept an unexplained larger pool.
Bed validation checks all five complete affected native functions and their
four expanded profile-table bindings; unrelated room-owner updates do not
invalidate unchanged bed code. Changed function contents still reject.

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
Default artwork preparation skips profiles already installed and verified by the
current build's runtime bindings, including inactive staged profiles. Explicit
`--select` requests can regenerate those records when needed. This avoids
recompiling an entire installed category merely to add one newly supported member.

### Shared runtime categories

Loop-audio preparation uses the ordinary `convert --assets-only --representation
audio --category scrolling-material-assets` command with the explicit current
lock. Complete move-function shapes select positioned loops or switch-driven
fades; IDs and names do not select implementations. Checked read-only constants
provide maximum/step values, and complete constructor/destructor bodies preserve
their actual state and persistence semantics. Shared native callbacks implement
both categories, including the sprinkler's on/off clicks. A shared native
placement adapter also preserves its start-disabled interaction.

The same `--refresh-runtime --furniture-audio-art` installer accepts complete
trigger or level-audio bundles. Sustained layers support mode setup before or
after the envelope command, retaining the actual loop restart, note duration,
velocity, decay, and all envelope data. The donor level dispatch contains 96
entries; its following program bytes must not be read as another 32 pointers.
The expanded native table retains 128 entries. Unknown layouts still reject.
Exact native instruments are reused; missing complete instruments and samples
use the same shared font/wave extension as trigger sounds. Interleaved category
batches retain all prior dispatches and current complete-resource receipts.

Growing wave archives can receive a checked virtual base at `04000000`, with an
eight-MiB reservation, without changing their DMA-directory index or moving
English text. Physical append/relocation remains independently bounded by all
live owners and nonzero data. The native audio initializer and streaming reads
use actual physical addresses; the general virtual-DMA request limit is not
relaxed, and these high virtual identities must not be passed to that path.
Tools resolve the live archive from the checked native physical-base instructions
and its unique uncompressed owner. Every wave header, including external wave
two, remains complete. The shared builder checks virtual destinations, emitted
directory changes, and extraction of the full resulting owner.

The `scrolling-material-assets` category prepares complete custom-drawn objects
with model-local texture scrolling. Discovery verifies entire source draw
functions, every model relocation pair, both matrix calls, dimension wrappers,
and the complete shared `two_tex_scroll_dolphin` generator. Descriptors retain
actual opaque/translucent submission order, source frame selection, signed scroll
rates, the Dolphin coordinate shift, runtime colour fields, and all lifecycle
receipts. Implementation fingerprints select formats; item IDs and artwork
names do not select conversion code.

Use `convert --assets-only --category scrolling-material-assets` with the current
explicit build lock. The complete prepared batch covers Merlion, Manekin Pis,
well model, fireplace, sprinkler, backyard pool, and lawn mower. The draw contract supplies segment eight
or nine only to its actual consuming model. Complete texture dimensions must
match the ordered one/two tile loads; missing, reordered, relocated, or unused
scroll bindings reject. CI4 and I4 use distinct non-overlapping TMEM regions
below palette storage. Eight-pixel rows use tile transfers with padded TMEM
strides, retaining both CI4 layers even when they share a source texture.
Source wrap, mirror, shifts, palette, both-cycle combiners, colour state, every
texel, and geometry are preserved. Unknown dynamic display lists remain refused.

The same resource category accepts verified EVW two-tile animation tables and
the shared parameterised furniture scroll helper. EVW records retain signed
source X rates and negated Y rates, dimensions, segment selection, the final
negative-segment marker, full data relocations, the dispatcher table, and checked
selected handlers. Unimplemented EVW colour/texture-animation types reject;
they are not treated as static decoration. The parameterised helper retains its
negated rates, frame-offset input, and room/preview counter selection.

Drawing descriptors may assign several models to the translucent stream and
bind scrolling to a middle model. The pool retains all three models, its actual
EVW water rates, and both layers of the repeated water texture. Its earlier,
unused scroll allocation is recorded separately and never mistaken for the
active binding. Both primitive/environment colours preserve their actual debug
register dependencies; constants are not substituted for unresolved state.
The mower retains two independent texture layers and actor alpha multiplied by
the verified source `255.0` constant, including actor-state alpha in previews.

The shared renderer supports these additional draw features through 48-byte
records. Ordered opaque and translucent spans preserve every model, including
a scrolling consumer before a later translucent model. Scaled alpha uses actor
state in both room and preview contexts and requires a finite value in `0..1`.
Pool colours read the existing native `Debug_mode` owner at `80138E50`, with the
same register layout, signed additions, and eight-bit component wrapping as the
donor. The complete native allocation/zero-initialization code is checked before
installation. This adds neither a new debug allocation nor shared renderer state.

EVW room animation retains the play counter. A recorded preview adaptation uses
the generic preview counter when the native draw caller supplies no room owner;
the renderer never reads a play-only field from a shorter preview context.
Both colour commands and all remaining translucent models follow the same
frame-owned matrix/scroll allocation. Lifecycle and acquisition dependencies
remain separate requirements. Pipeline/installer version 17 and graphics
converter version 12 retain validated earlier artwork caches.

Preparation does not imply native drawing, lifecycle colour/sound transitions,
or acquisition. `--refresh-runtime --scrolling-materials-art` installs complete
prepared objects and their shared renderer, without ordinary profiles. Metadata
and native profile construction refuse the incomplete lifecycle category,
including forged readiness annotations. Merlion `1FE4` and Manekin Pis `1FE8`
have append-only destinations `3C34`/1805 and `3C38`/1806 after the existing legacy
reservations. The pinned worksheet and approved translation maps contain no
native correspondence for either source. Membership does not enable gameplay.

The scroll extension owns `804BA000..804BBFFF`, after the unchanged 8-KiB room
packet and below furniture banks at `80500000`. Code has 4 KiB; the remaining
4 KiB contains `AFC2`, count, stride 48, zero, and up to 64 complete records.
Records carry identity/size, model order, segment, one/two dimensions and signed
rates, source colour commands, preview colour, and private native state offset.
An explicit opaque-model count, second colour command, and bounded debug-register
offset cover the extended draw forms. Earlier installed records are regenerated
from their source descriptors; every original field and asset is retained.
Prepared bundles may include already installed objects: complete record/resource
identity is checked, and only new objects are appended. Different cache receipts
do not trigger duplicate installation or artwork recompilation.
The bootstrap uses cache word `804B1E04` and vtable `804B1E30`. DMA, CRC,
writeback/invalidation, and startup-reset cache semantics match the existing
room packet, but the extension has its own checked code/data identity. Further
room packet publication retains both vtables and reload contracts.

Drawing reserves both OPA/XLU command streams and aligned frame scratch before
writing either. One matrix is shared by the two draw streams; one/two native
tile-scroll pairs and termination follow it. All submitted scratch is immutable
and written back for the RSP. Native counters are doubled to source counters;
the source's doubled 14-bit tile origin is reduced from sixteenth-texel to
quarter-texel units with explicit unsigned wrapping. Preview context never reads
the larger play-context frame field. Colour state maps donor float offset `834`
to private native `1A4`; the shared lifecycle initialises and maintains it.
NaNs, invalid colour values, malformed records, and insufficient arenas produce
no partial draw. Maximum scratch is 104 bytes plus eight alignment bytes.

The complete artwork is reused without compilation. The native model banks,
ordinary heap, old room packet, selections, and saved formats remain unchanged;
the additional fixed resident reservation is 8 KiB. Lifecycle/audio, ordinary
profiles, acquisition, and native GPU/gameplay verification remain required.
Do not freeze textures or discard translucent models to enable an import.

#### Shared switch/fade and positioned-loop lifecycle

The scroll packet's remaining table space at `804BBC10` contains `AFL1`, count,
stride 12, zero, and up to 64 records. Each record carries native index, mode,
persist-on-destroy flag, loop sound, optional on/off clicks, maximum, and step.
The code reservation remains 4 KiB and the complete packet remains 8 KiB.
The existing bootstrap supplies constructor, move, draw, and destroy dispatch
through the same checked lazy loader. Draw-only records have no lifecycle entry
and consequently no new actor writes or sounds.

Mode one refreshes the source positioned sound on native updates. Mode two maps
the source private switch to native `1A8` and colour float to `1A4`, retaining
the native saved switch/changed fields at `12C`/`12D`. Construction interprets
only saved value one as on. Each native move performs two source fade updates;
only the first half sees the switch edge, and only at the current target. Edges
during a fade remain ignored. Neither callback clears the parent's changed flag.
Loop sounds are suppressed in native states 12–15. Source click events retain
their independent rule. Destruction writes the private switch back only when
the source actually has that destructor; no persistence callback is invented
for Manekin Pis. Invalid records, switches, and non-finite/out-of-range colour
state produce no callback writes or sounds.

Ordinary binding rechecks full source callbacks/helpers/constants, actual native
sound programs, bank selectors, complete instruments/samples, drawing resources,
packed lifecycle records, packet identity, and vtable. Sprinkler clicks use the
complete two-note native programs, including their instrument change, note timing,
and priorities. Each channel/layer has its own checked termination; a later
dispatch pointer is not assumed to delimit the program.

Merlion, Manekin Pis, and fireplace use the shared ordinary profile/acquisition
pipeline. Sprinkler's `1000` start-disabled profile flag requires the shared
native placement binding as well as its complete move/draw/audio callbacks.
It uses its source C-stock acquisition and supports catalogue reordering.
The mower's separate contact/floor-driven state remains unfinished.

#### Shared contact and floor lifecycle preparation

The [bulk room-surface pipeline](V3_ROOM_SURFACES.md) prepares both missing and
additional donor floors/wallpapers with stable identities. Runtime application,
persistence, sound, and acquisition are required before contact bindings can
consume those identities. Preserve the separate room-owner movement sounds;
source `aMR_SetMoveSE` supplies mower and stone-coin behaviour outside their
individual callbacks.

`convert --assets-only --representation lifecycle --category contact-floor-alpha`
uses the current explicit build lock and discovers complete source callback
shapes, not item IDs. The preparation report retains source constructor, move,
draw, contact getter, easing helper, all constants, both floor predicates, and
the actual four push states. It compiles the shared renderer/lifecycle module
with contact support without changing a cartridge or enabling a parent.

The native callback maps source alpha at `834` to private float `1A4`. Its
constructor clears only that float; it adds no destructor or saved state. Move
resolves the nullable native room clip at `80136F2C`, its owner at offset zero,
and first-layer contact direction at owner `178+28`. Signed floor identity comes
from `80137655`. Back contact and states one through four set target one only
for the two completely bound floor records; otherwise target is zero. Two
source `add_calc` updates per native frame preserve `.04/.1/.001` easing and its
minimum-step tail. NaN/out-of-range actor values reject without writes. The
native helper at `8009A570` retains its complete verified implementation.

The category fits the existing 12-byte lifecycle record as mode three: the two
16-bit fields used for click IDs by mode two hold native floor indices. Flags,
sound, maximum, and step must be zero; floor indices must be distinct in `0..127`.
There is no missing-floor sentinel and no numerical fallback. Complete contact
support compiles within the existing 4-KiB code allowance and adds no heap or
fixed RAM. Without its compile-time definition, existing callbacks are unchanged.
Ordinary profile binding still refuses this category until complete surface
dependencies and installation are connected.

Floor binding compares every decoded pixel of the complete converted donor
surface against the native room-floor bank. Zero matches require an additive
surface import; multiple matches require identity resolution. An equal numeric
index is not evidence. GameCube backyard lawn at 26 has no native artwork match:
native 26 is old plank floor, independently recorded in the translation catalogue.
Daisy meadow at 48 matches all 16,384 pixels. The prepared mower remains inactive
until both source floor identities have complete native bindings. Missing room
surfaces need the general item/artwork/house/catalogue/save pipeline, not a
special-case mower substitution or replacement of original content.

#### Shared initial-switch placement

The complete donor `aMR_SetSwitchStepData` supplies the start-disabled rule.
The native owner function at `80937FB0..809380EB` retains original gyroid,
loaded-switch, and null-profile paths. Only the fresh non-gyroid branch changes:
twenty bytes at `809380A0` pass actor/profile to a shared resident helper and
resume the existing epilogue. The fixed helper call has no overlay relocation;
all existing relocation data and owner bytes outside that span are retained.
The branch-delay profile argument is harmless on reload because the next native
instructions replace it before use.

The helper starts imported indices `1024..2047` off when profile interaction
bit `1000` is set. All other indices keep the original on default, including
original furniture with a coincident flag. The native step field still receives
`FF`; the changed flag, actor position, and private state remain untouched.
It reads the actual profile flags, not an item-ID list or a new mutable table.
The helper shares `80483D00..80483FBF` with the seating-sound reader. No heap,
fixed RAM, or saved layout grows. Subsequent bulk imports retain the helper's
checked entry and recompile the same complete reservation.

`--furniture-profiles` installs this category when a complete source lifecycle
requires it. Ordinary binding verifies source code, the full current helper,
complete native initializer, patch instructions, and relocation exclusion.
The native profile writer requires the resulting placement binding; merely
marking a prepared source flag as supported cannot enable the item.

The `material-frame-assets` category prepares complete custom-drawn models and
their texture/palette frame tables independently of unfinished lifecycle code.
Discovery verifies the entire draw implementation, paired data relocations,
matrix helper, source frame selector, full pointer table, and actual model order.
Bounded internal branches retain their exact instructions in the checked digest;
they are not mistaken for helper calls or removed from verification. No item ID
or artwork name selects a conversion rule.

Every material frame is converted, including frames which appear briefly.
Repeated table entries retain their positions and timing even when the stored
resource is shared. Dynamic texture/palette loads retain segment eight or nine;
they are not replaced with the first frame. Resource type, complete extent,
texture dimensions, alpha, and absence of conflicting relocations are checked.
The same native command emitter preserves explicit texture-off/on transitions
and the primitive-times-shade, opaque untextured combiner.

This shared category prepares the coin, ? block, starman, fire flower, festive
candle, and Mouth of Truth together. Descriptors distinguish room/preview
counters, division/modulo timing, switch-dependent stopping, and an actor-state
selector. Source lifecycle receipts remain attached and pending. The artwork
does not implement sounds, surprise/rumble, player colour changes, or switch
coordination. Ordinary metadata and the
native profile writer both reject this category, including a forged runtime
annotation. Use `convert --assets-only --category material-frame-assets` with the
current explicit build lock; reuse the resulting complete objects through
`--refresh-runtime --material-frames-art <prepared-directory>`.

The shared native material renderer uses a checked 40-byte record containing
stable destination index, complete object size, selector mode, segment, counts,
division, complete frame size, four model offsets, eight frame offsets, native
private-state offset, and material kind. All unused fields are zero. The table
at `804B9E20` holds eleven records and fits the unused end of the existing 8-KiB
room packet. Its header is `AFM1`, count, stride, and zero. Code uses the existing
4-KiB code half; no new allocation or object header is needed. The stable vtable
at `804B1E10` routes drawing through the same checked packet loader and caches.
Other refresh operations retain this table and vtable.

Modes are unsigned timed selection, signed timed selection stopped by an off
room switch, and the low bit of a private signed halfword. A non-null native room
argument selects gameplay frame `1EA0`; a preview uses generic frame `A0` and
never reads beyond that smaller game context. Counters advance at native 30 Hz
and are doubled before the original donor division/modulo. Unsigned wrapping and
signed division toward zero are explicit. The switch is at native offset `12C`.
The private selector uses `1A4` in non-rig actors, not the out-of-bounds donor
offset `82C`; an eventual lifecycle must initialize and own that field.

Complete frame bounds, eight-byte alignment, segment eight/nine, model order,
and packet limits are validated before any graphics writes. Drawing reserves
one matrix and all commands together, binds an immutable complete palette or
texture, then submits every model in donor order. Crowded or malformed arenas
produce no partial draw. Ordinary profiles require a checked complete lifecycle
binding, not just an installed renderer or a forged readiness annotation.
Material objects with complete installed switch-trigger moves use the shared
profile staging path; other lifecycles remain refused. Acquisition stays
independent. Mouth of Truth's reviewed legacy source `1FD8` has the append-only
destination `3C30`, runtime index 1804; the native worksheet correspondence and
approved translation map contain no existing native identity for that source.

The `static-models-pending-move` resource category separates ordinary profile
drawing from an unfinished move-only callback. It requires complete direct model
slots and exactly one move callback; create, custom draw, destroy, DMA, dynamic
texture, and other profile resource dependencies cannot enter this category.
Known switch-sound implementations retain their checked implemented category.
Other callback code retains its complete source identity and relocations without
being represented as understood or ported behaviour.

`convert --assets-only --category static-models-pending-move` prepares all matching
complete graphics in one normal compiler batch. The source profile's scalar,
contact, and interaction fields are preserved. Unimplemented fields are recorded
in `pending_profile_fields`; this exception applies only to the prepared-only
category. Invalid finite/bounds/structural values still reject, and implemented
categories retain their stricter semantics checks. Both metadata generation and
native profile construction reject the prepared-only category regardless of
alleged runtime bindings. Future behaviour adapters can reuse validated artwork
while regenerating current eligibility. No smoke, sound, money, or other effect
is silently discarded to make an item selectable.

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
- Complete IA16 textures up to 2,048 bytes, untiled from GX IA8 four-by-four
  blocks. Each pixel swaps the donor's alpha/intensity bytes into native
  intensity/alpha order; all 256 levels of both channels survive. No threshold,
  palette reduction, or resizing is used. The pinned donor format table maps
  IA/16 to GX format 3, and its complete `texconv_tile` implementation confirms
  the byte swap. Native tile stride is two bytes per pixel, texture LUT is
  disabled for IA16 and restored for subsequent CI4, and upper TMEM palettes
  remain untouched. `ia16-materials` selects this shared format category.
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
  The `translucent-combiners` category adds two complete two-cycle forms:
  texture/primitive/shade RGB with primitive-modulated texture alpha, and
  texture-alpha interpolation between environment/primitive RGB followed by
  shade multiplication. Both retain source alpha and use one texture only.
  Native symbolic compilation must reproduce the actual complete donor words;
  changed operands, TEXEL1 dependencies, and unknown formulas still reject.
  The compatible fog/antialiased-depth-tested translucent render mode retains
  its complete native command. Existing blend modes remain unchanged.
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
The same complete move verifier serves material-frame objects with exactly
move/draw callbacks. Audio discovery inspects a copy of that move receipt so it
does not mutate the independent prepared-artwork descriptor. Other lifecycle
functions retain their own pending dependencies and cannot enter this adapter.

`convert --representation audio --assets-only --category switch-trigger-sound`
uses these source-derived records to prepare the whole category's audio in one
batch. The shared `v3_sound_programs` converter retains complete explicit-font,
single-layer note sequences, including repeated notes and optional custom
envelopes. Durations, velocities, pitches, tuning, and envelope data remain exact;
only verified instrument/selector/internal-address bindings change. Unsupported
commands, ambiguous boundaries, and unaccounted bytes reject. Full trigger words
retain their single-instance flag separately from the source dispatch identity.
Using `--category material-frame-assets` prepares matching material triggers
through the same path. Already installed furniture audio is excluded by the
current source-bound manifest, without an item-specific exclusion list.

The font builder grows its pointer table once, relocates all original live bank
pointers, and preserves every existing instrument. Wave offsets and tuning words
are not mistaken for bank pointers. Complete envelopes, samples, loops, predictor
books, and all three instrument ranges are retained; identical dependencies are
reused. Source records are sorted independently of request order. This is a
general instrument batch, not an item-specific sound implementation.

Prepared output contains a full expanded font/wave pair, relocatable programs,
source/callback receipts, current-cartridge identity, and aligned font-capacity
requirements. It does not assign native sound IDs, change audio headers, allocate
memory, or install callbacks. Native dispatch/priority and allocation integration
are mandatory: the same donor sound number can be out of bounds or select a
different native program. Neither shrinking samples nor dropping sounds is an
acceptable substitute.

`--refresh-runtime --furniture-audio-art <prepared-directory>` installs the
complete prepared category through the shared resource allocator. It reconstructs
and compares every program, instrument, sample, and source callback before use.
Complete group-one/group-four tables grow to 128 entries, retaining every existing
pointer. New identities use vacant appended slots with the source's priority;
the priority table itself is shared across groups and must not change. Source
single-instance flags stay in the mapped word. The original N64 dispatcher does
not implement that flag, so the category callback checks all six actual live
trigger slots before dispatch. It preserves native actor state and the owner's
switch-change flag. No per-object behaviour script is required.
Later batches validate the full existing dispatch tables and original table
prefixes, every installed program, priorities, and native identities. They fill
only verified vacant slots and retain the current tables instead of appending
another pair. Identical existing source programs are reused only when complete
current instrument/program bindings agree. One sound callback serves ordinary
and material drawing; the material vtable gains that move entry only after its
complete prepared artwork and checked move category are installed. Ordinary
profiles and acquisition remain independent requirements.

The complete new sequence and font use the import resource. The wave group keeps
its complete existing prefix. Its checked in-place append can relocate
only declared, hash-verified DMA owners blocking the extension; those owners keep
their complete contents and virtual identities. Unknown owners and nonzero
unowned gaps reject. The normal cartridge-tail allocator places the blockers
outside the expanded wave group and all other live owners.
If an in-place append is unavailable, the complete archive can move to a
sixteen-byte-aligned, fully zero, unmapped cartridge gap beyond the import
reservation. Logical VROM identity is retained; all six wave headers and the
actual native base-load instruction pair are rebound together. External wave
resources retain their absolute physical locations using the verified unsigned
header addition. Existing copies remain untouched, and unclaimed nonzero data
is never silently reclaimed. Final cartridge extraction verifies the complete
changed archive. Neither this relocation nor a sample append inherently grows
resident RAM.

Permanent audio capacity accounts for every actual permanent header with native
alignment. Required growth rounds upward to 1 KiB and updates both malloc
arguments and all three total/fixed/permanent settings together, retaining the
session pool and fixed remainder. The five-object batch adds 2 KiB, with 864
conservative spare bytes. Shared sound rows and the move-only vtable use checked
free space in the existing room packet/bootstrap reservations. Audio installation
does not enable incomplete profiles or acquisition routes.

Subsequent ordinary furniture imports resolve retained chair sounds through the
actual installed sequence table, font header, and wave binding. They compare
complete original/donor instrument semantics, timing, selection mapping, and
program pointers. A relocated dispatch table or expanded pointer table is not a
sound change; a mismatched program or instrument remains a rejected import.

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

The clock runtime accepts fixed as well as indexed bindings. A fixed constructor
with the complete clock drawer is promoted only after its move loop, no-op
destroy callback, and repeat initializer code/relocations/constants are checked.
The donor initializer already supplies speed `0.5`; the native initializer uses
`1.0`, so the existing runtime explicitly sets `0.5` before initial playback.
This preserves the donor's evaluated first frame even when its constructor
assigns the same `0.5` again after playback. Both bindings share two source motion
steps per native update and the same live hour/minute joint callbacks. No new
per-item runtime branch or additional resident allocation is required.

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

The `fixed-keyframe-rig-assets` category separates resource preparation from
unfinished interaction code. It recognises a shared fixed skeleton/motion
constructor by complete normalised instructions, paired resource relocations,
actual keyframe helper calls, and finite initial speed. Stop/repeat mode and
the source's initial-play-before-speed ordering are recorded, not substituted
with an existing runtime's ordering. Its complete standard drawer has no joint
effects; the clock drawer additionally retains verified hour/minute callbacks.
Unknown drawing, billboard, or extra material dependencies still reject.

The same source records discover tiger bobblehead, stone coin, harvest clock,
and judge's bell without an item-specific definition. Harvest clock's complete
verified lifecycle promotes to the existing clock category; the other three
retain their pending callbacks. Every visible model,
texture, palette, skeleton joint, and animation array is compiled by the ordinary
bulk pipeline. Remaining move/destroy callback hashes and dependencies stay in
the descriptor, with explicit pending status. This describes complete constructor
rig resources, not ported gameplay or any dynamically spawned effects. In
particular, seven-joint resources can be prepared even though the current room
runtime's six-joint work area cannot yet serve them.

`RESOURCE_CATEGORIES` includes this prepared-only category; `RIG_CATEGORIES`
contains implemented room categories only. Both ordinary metadata generation
and native profile construction reject the prepared-only category, even with a
forged installed-runtime annotation. The room-resource installer also rejects
it. Once a complete behaviour adapter exists, unchanged graphics/keyframes can
be reused from the validated cache without another model compiler or installer.
Use `convert --assets-only --category fixed-keyframe-rig-assets` with the current
explicit build lock. Neither prepared resources nor source callback receipts
make a playable import or a browser choice.

The switch-driven category prepares all eight room balloons in one command:

```sh
python3 tools/v3_furniture_pipeline.py convert --assets-only \
  --category indexed-switch-rig \
  --base-lock build/v3-balloon-inventory-02/build-lock.json \
  --output build/room-rig-assets
```

The source-only furniture index decoder handles both `1xxx` and `3xxx` ranges.
The ordinary worksheet scan includes unresolved legacy correspondence alongside
the `3xxx` entries and reviewed room aliases. It does not classify the entire
legacy range as new imports. Names use the matching official source
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
categories, not static substitutions. Clocked rigs have complete installed assets
and a shared native lifecycle; ordinary profiles/acquisition remain separate
requirements.

Other dynamic texture/palette pointers, animation rigs, custom callbacks, unsupported
contact/interaction flags, other action sounds or acquisition routes, oversized
or different-format artwork, and framing outside the checked source table remain explicit review
categories. Unsupported does not mean unused or unimportant. A successfully
converted object is not automatically evidence of complete gameplay.

## Shared installation

### Shared holiday reward preparation

`convert --representation rewards --assets-only --category holiday` prepares
the donor's complete 28-event gift program and a relocatable N64 o32 selector/
handover kernel. The actual `mSC_trophy_item` code, station selector, index-to-item
conversion, give/pre-give functions, relocations, complete branch table, fixed
gifts, calendar identities, and floating-point random bounds are checked.
Selectors retain all 65 candidate entries, including the source's fifteen-diary
New Year's range, fifteen stations, nine flowers, and gender-dependent Toy Day.
No manually maintained item-name list determines event membership.

The `AFHG` table contains a 16-byte header, 28 eight-byte event records, and
complete big-endian donor item IDs. Source IDs are not presumed native IDs.
The shared runtime accepts a pure checked resolver that returns an installed,
selected native item or zero. Complete selection preserves donor variant order
and distribution; sparse selection chooses uniformly among available variants
using a bounded index supplied by the caller. Missing identity/artwork/behaviour
must resolve to zero, never to a native item with the same numerical ID.

Transient offers preserve event, original variant, donor ID, native ID, and
gender. Handover rechecks the complete source record, current mapping/selection,
and active player's trophy before delivery. Only successful native inventory
insertion may mark the receipt; full pockets, changed selection, duplicate
delivery, and malformed offers cannot consume the reward. Caller operations
bind to the validated active player, normal possession conditions, existing
catalogue-registration insertion, and format-3 trophy state. The source NPC
demo completion signal remains the required delivery trigger.

The kernel is prepared as a relocatable object, not linked to an invented RAM
address. The existing ordinary importer must continue refusing these acquisition
routes until the complete NPC, calendar, dialogue, identity resolution, and
delivery bindings are installed. In particular, the gift program includes
legacy `1xxx` furniture and diary parents: a `3xxx`-only inventory does not cover
all donor additions. Legacy room/display aliases must remain distinct from
new ordinary furniture. Prepared selectors are not playable imports or web
choices, and do not replace missing holidays with unrelated shop stock.

`tools/v3_furniture_install.py` binds the complete base ROM/report and source
data, regenerates the metadata/dependency description, and checks the converted
assets. It installs full profiles and item records, names/prices/footprints,
stock, catalogue entries, HRA/feng-shui rows, and selected-profile bits together.
Missing native scoring-series definitions require a category adapter. Existing
documented theme adapters retain their source-bound surface mappings, including
stable additive pairs where installed and explicit missing pairs otherwise.
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

The current packet contains the eight existing balloon rows, both Harvest
storage rows, and all fifteen clock rows. The installer reuses verified retired
storage when available; otherwise it appends complete assets within the checked
import reservation and rebuilds the shared terminal resources. No additional
resident allocation is needed for the clock batch. Complete assets can cross the
legacy storage bound only after `v3_resource_capacity.checked_limit` validates
both relocated English resources, offset tables, and complete native consumers.
Ordinary clock/storage profiles use the shared staging adapter below. Acquisition
remains required; these records are not selectable merely because their lifecycle
and resources are installed.

### Shared ordinary profile staging

`--refresh-runtime --furniture-profiles <prepared-directory>` accepts repeated
complete prepared bundles for implemented clock, storage, sound, and
material/trigger categories, plus draw-only and complete loop/fade scrolling objects.
Source identity, complete artwork, callback bindings, and installed audio are
checked before writing ordinary 80-byte profile and 32-byte item records into
their fixed canonical slots. Official English names retain individual entries
in `translations/provenance.json`. Existing rig assets are reused at their
original VROMs; complete sound models are appended within the checked reservation.
No additional resident memory or saved fields are needed. Material/trigger
profiles reuse their installed objects and the shared material vtable, leaving
the native engine's generic model/rig fields null to avoid duplicate drawing.
Both the material and sound rows retain the profile binding. The complete move
category and sound word are checked again when the ordinary importer resolves
runtime readiness. Prepared material objects without an installed lifecycle
remain explicitly deferred in the staging receipt, not silently promoted.

Draw-only scrolling eligibility checks every non-draw callback: each must be
absent or exactly the complete source return instruction, with no relocations.
Actor-state colour inputs, unsupported scalars, contact actions, and interaction
flags still prevent this classification. The native profile writer repeats the
receipt checks and requires the installed scroll vtable. `bind_profiles` checks
the full scroll packet, code, table, dispatch, artwork, and source callbacks.
Neither a readiness flag nor an empty-looking function name bypasses these rules.

Well model and backyard pool satisfy this category and reuse existing graphics
with null generic model/animation slots, so the engine does not draw duplicate
geometry. The normal metadata path admits the pool's actual `ftr_listEvent`
route and existing event stock/catalogue/scoring adapters. The well model has no
supported acquisition-list binding and remains staged, not shop-stocked.
The loop/fade category additionally supplies the two fountains and fireplace.
Sprinkler additionally requires the installed start-disabled placement binding;
mower keeps its missing contact/floor-driven lifecycle.
Staging merges pending resources across categories, preserving material gaps.
Subsequent resource batches validate and retain both staged and activated
profiles without resetting completed lifecycle status or duplicating objects.
Prepared staging bundles may contain those verified existing profiles; they are
reused rather than rejected as duplicates. Donor and destination identities are
resolved through the shared registry. Prices and source profiles use donor
indices, while native slots, saved selections, and item records use destinations.
Bindings and promotion match on canonical donor identity, including legacy IDs.
The older scrolling format exposes no ordinary profiles; upgrading its renderer
remains a prerequisite for this category.

Both enabled flags remain zero, along with the saved selection bit at
`blob[0x20 + 32 + slot/8]`. The native profile-table initializer consequently
leaves these entries null, and item readers refuse them. Saved selection bits
alone are not a sufficient gate: both native record flags must stay inactive
until full category integration. Inactive profiles cannot enter ordinary gifts.

`staged_furniture` records complete installed profiles/assets and separately
retains pending acquisition, catalogue, and scoring. These records are not
browser choices. `bind_profiles` validates the current cartridge's complete
runtime, table, artwork, record, and profile bindings before discovery accepts
the installed lifecycle. Discovery still applies ordinary acquisition, scoring,
and catalogue rules; missing routes remain explicit rather than being replaced
with shop stock.

When those prerequisites are implemented, the normal bulk installer promotes
checked inactive records and reuses their complete assets in place. It rejects
changed records, prices, names, model data, callback pointers, and active slots.
One complete prepared-artwork validator handles both static objects and rig
suffixes; the importer does not omit motions when calculating object size.
Promotion enables records through the existing shared acquisition/catalogue/
scoring flow and removes them from the staged list. No item-specific installer
or checkbox-dependent identity assignment is needed.

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
