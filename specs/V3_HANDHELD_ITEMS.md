# V3 held equipment

## Representation and scope

The player's held model, the dropped inventory item, and its catalogue preview
are distinct representations. Use the donor's actual selectors for each one.
The room/collection context records in [the shared pipeline](V3_FURNITURE_PIPELINE.md)
govern drop semantics; a prepared catalogue model is not a usable handheld item.

`tools/v3_handheld_items.py` discovers equipment dependencies from five complete
GAFE01-r0 functions: item-to-equipment-kind, kind-to-shape, kind-to-animation,
resource-pointer lookup, and resource-type lookup. Function code, paired table
relocations, complete table spans, pointer ownership, switch-return targets, and
index bounds are checked. Counts and mappings come from those functions/tables,
not a maintained list of tools. Names and hashes come from `itemName_tool`.

The 92-entry item switch selects 79 equipment identities/states and rejects
`222C..2238`. Thirty-six ordinary tool/umbrella IDs occupy `2200..2223`;
eight custom umbrellas occupy `2224..222B`. The remaining selectors cover golden
tools, worn axes, balloons, pinwheels, and fans. The complete shape/animation
tables have 80 bytes each, including the donor sentinel; the resource pointer
and type tables contain 50 records each. Preserve animation indices even where
the selected static model does not consume an animation.

The shared donor inventory attaches these dependencies to its existing item
records, without adding duplicate identities or enabling import choices.
Worn axe IDs select three different ordinary-axe appearances. They remain
states of one parent, not separate selectable items. Their collection display
can be shared while their held shapes and room-drop IDs remain different.

## Shared conversion

The existing pipeline accepts `--representation handheld`:

```sh
python3 tools/v3_furniture_pipeline.py scan --representation handheld \
  --output build/held-scan/inventory.json
python3 tools/v3_furniture_pipeline.py convert --representation handheld \
  --assets-only --output build/held-assets
```

`--select` filters by donor inventory ID. Shared model roots are converted once;
each output records every selected parent/state that uses it. The supported
category is `static-held-model`. Unknown or unsupported selections reject before
creating output. `import` and conversion without `--assets-only` reject because
native player integration remains unfinished.

`prepare_models` and `compile_models` are shared with furniture conversion.
Both front ends use the same dependency tracing, complete texture/palette/vertex
conversion, material checks, triangle conversion, native graphics compiler,
alignment, and model-list assembly. Static held models introduce no simplified
mesh, replacement texture, dropped layer, or item-specific emitter. The prepared
objects use segment six; an eventual owner must explicitly establish and restore
the correct graphics bindings. No cartridge allocation or native profile is
implied by a prepared object's model-root description.

Nineteen held item/state records use fourteen static model roots: eight fans,
ordinary/golden shovels, and four axe appearances. Twenty records use animated
skeletons; forty umbrellas use a separate owner and no model root from this
table. Neither group is converted into a static substitute. Prepared output has
the distinct `AFV3-HANDHELD-PREPARED-ASSETS-1` format, which the furniture installer
rejects. Runtime and save-profile selection remain off.

## Shared skeleton and motion data

`tools/v3_keyframes.py` supplies reusable rotational-skeleton and keyframe
format handling. It follows complete header relocations, preserves every joint's
translation, child count, model root, and draw stream, and checks the complete
preorder hierarchy. Animation traversal accounts for root translation and every
joint rotation, consuming exactly the declared constant values, track counts,
and frame/value/velocity triples. Tracks must be ordered and within duration;
signed native index limits are enforced. Constant-only poses retain null key
and count pointers instead of inventing unused arrays.

The converter copies complete arrays without resampling or shortening motion.
It deduplicates source roots, aligns data, and rewrites only the four animation
pointers to segment-six addresses. Array/header receipts, all relocation targets,
and source bindings accompany the output. Its layout follows the native
`BaseAnimationR` and `JointElemR` formats; player-specific rig compatibility,
graphics matrices, action dispatch, and buffer ownership are separate work.

The shared handheld category prepares one complete dependency bundle:

```sh
python3 tools/v3_furniture_pipeline.py convert --representation handheld \
  --assets-only --category held-motion --output build/held-motion
```

This preparation category rejects `--select`; it packs the shared source
dependencies once, not a selected gameplay profile. Individual item selection
belongs to the eventual native/profile integration. The distinct
`AFV3-HELD-MOTION-PREPARED-1` format is not a furniture installation.

The checked equipment resource/type tables supply all sixteen equipment
animations and twenty skeleton descriptions. Every animated parent records its
real default animation and same-resource-type variants, with matching joint
counts. Complete player-animation pointer/default selectors supply seven
equipment holding animations. The complete fan setup function supplies its
actual swing index, checked against the same table. The combined twenty-four
animations retain 84 arrays in 7,760 bytes: sixteen equipment motions, six
constant player poses, fan idle, and fan swing. Fan idle has seventeen frames;
fan swing has nine. Neither timing is inferred from a catalogue model.

Skeleton descriptions preserve actual model dependencies but do not convert
those graphics or install draw callbacks. Net/rod joint-matrix commands and
balloon texture formats still require shared graphics support. Pinwheel model
preflight accepts its existing material commands, but complete rig/model
packing and native player ownership remain unfinished. No animated model is
flattened to pass the static converter.

## Native integration work

### Shared event stock

`tools/v3_event_acquisition.py` derives fireworks-stall stock from six complete
donor implementations, their relocation dependencies, and the three actual
stock/price/message tables. The records cover eight fans at 780 Bells, eight
pinwheels at 680 Bells, and eight balloons at 480 Bells. These are the vendor's
prices, not the ordinary item price table. The shared handheld scan attaches
these acquisition records to the existing 24 identities; it creates no new
identities or selectable imports. Official names remain bound to their existing
`itemName_tool` records and provenance.

The N64 vendor's stock differs from the donor's. Replacing its generator would
remove original merchandise. Its native event payload is 40 bytes; its stock
uses the first 20. The added stock occupies the second 20, retaining eight
`u16` slots, the count marker, and the donor category. No saved structure grows,
and no additional event slot is reserved. The native event allocator/lookup,
complete translated owner, relocation data, and allocation descriptor are
checked before installation. The existing initializer and original first 20
bytes remain intact. A direct-call scan of the original cartridge finds the
literal event-11 save getter and reservation calls only in this vendor; this is
not a claim to have proved every indirect event access.

The shared installer supports `--refresh-runtime --event-acquisition` with an
explicit base lock that includes seasonal ground integration. It appends one
shared 1,680-byte implementation and three eight-byte category records to the
equipment module, growing it from 44 to 48 KiB. The constructor's one local call
targets the resident wrapper, and its obsolete local relocation is removed.
The wrapper resolves the currently loaded vendor before calling its original
save initializer. It does not retain a relocated heap pointer.

Selected, implemented equipment alone enters added stock. Categories without
eligible variants are excluded before the donor-style random category choice;
selection within the surviving categories is uniform. Variant slots remain
stable with zero holes for disabled imports. No eligible category means no stock
write and no random-number consumption. The initialized count remains eight
after sales, preventing an empty stock list from being replenished on re-entry.
Unexpected existing data is rejected without clearing it.

The shared functions supply bounded stock counts, three-choice page indices,
item/price/message quotations, and checked consumption after a successful
transaction. They do not insert inventory items or debit Bells. The quotation
must still match before its slot can be consumed. Null arguments, invalid slots,
changed profile readiness, and malformed stock fail without writes.

The shared menu adapter below connects this stock to selection/payment/handover.
Donor category two is finite balloon stock, not the original unlimited-fruit
branch. Collection/catalogue, parent selection, ordinary conversations,
save/reload, and original-hardware appearance remain unfinished. Stock and menu
implementation alone do not permit enabling the parent choices. See the
[checkpoint](../docs/checkpoints/V3_FURNITURE_PIPELINE.md#shared-event-stock).

### Shared event menus

On a stock-enabled base, the same `--refresh-runtime --event-acquisition` adapter
installs one category-independent vendor menu. All original N64 callbacks,
merchandise, prices, and unlimited-fruit behaviour remain available through
`Original wares`. `Festival items` uses the separate selected stock, full English
parent names, source prices, and three-item pages. Empty selections bypass the
route chooser. Empty initialized imported stock stays sold out without closing
the original stall or replenishing purchased goods.

The shared runtime reuses native choice/order/message functions, pocket-space
and money checks, pocket insertion, payment, and item-handover requests. The
order flag is consumed once, so repeated updates do not repeat purchases.
Stock is consumed only after the item is inserted and payment completes.
Pocket insertion failure never charges money or consumes stock. There is no
yield between quotation, insertion, payment, and stock commitment. Three source
categories share this implementation; unimplemented pinwheels/balloons do not
become enabled because the menu can represent their stock.

The 2,385-byte module starts at `804AF000`; its linker limit is `804AFFF0`.
The complete equipment reservation becomes 52 KiB, ending at `804B0000` with
the usual sixteen-byte guard. All previous module bytes remain intact, and the
same startup checksum/cache transfer covers the full reservation. The vendor
allocation grows from `954` to `958` hexadecimal bytes to append a transient
route field. This field is not saved. Original actor fields stay at their
existing offsets, and native callbacks resolve through the loaded owner.

The installer changes the request callback and native action-setup entry,
removing exactly four obsolete HI/LO relocations. Original actions retain
their relocated callbacks; imported selection, purchase, and handover use the
resident implementation. The new route-choice action is six. No original action
table is indexed beyond its six entries, and invalid action requests end safely.

Original native introductions describe K.K. music at 980 Bells, gyroids at
1,000 Bells, and fruit at 1,280 Bells. The supplied GameCube and legacy English
messages instead describe fans, pinwheels, and balloons. Keep those official
messages for the matching imported stock. Messages `2EE7..2EE9` adapt only the
merchandise/price pages for the original route, retaining official greetings,
final questions, page boundaries, and unaffected control/timing commands.
Message `2EEA` reuses the donor's complete final menu question. These four
messages and the two assistant-written route labels have individual entries in
the single `translations/provenance.json` catalogue, including authored fragments
and source hashes. Human wording review remains explicit.

The text bank grows by 1,024 bytes and its directory by sixteen bytes. All
12,007 previous message entries and both choice resources remain unchanged.
The installer repacks only the four existing physical text files, preserving
their virtual identities and directory slots; no new DMA entry or duplicated
two-MiB text bank enters the import blob. It checks complete source/resource
hashes, virtual/physical overlaps, zero growth padding, message termination,
the 1,024-byte expanded-buffer bound, and both native message-count limits.

The proposed cartridge is experimental, not a playable handheld release.
Installed transaction code does not establish catalogue ownership, ordinary
vendor conversation or animation, saved-event persistence, or hardware support.
See the [menu checkpoint](../docs/checkpoints/V3_FURNITURE_PIPELINE.md#shared-event-menu-and-transactions)
for executed checks and the inherited seasonal-copy issue.

### Shared collection and catalogue identity

The [held-parent collection adapter](V3_COLLECTION.md#shared-held-parent-collection)
connects the actual native acquisition path and existing four-player save state.
Generated parent and rotated-display queries use the same selected canonical
bit without changing pocket IDs or ordinary room drops. No new saved format or
memory allocation is required; unimplemented parent choices remain disabled.

The donor's umbrella catalogue list contains 64 indices, including all eight
fans at positions 32–39, pinwheels, and balloons. Checking only its 601-row
furniture list misses these entries. The shared source receipt binds all nine
category lists and records each installed parent's actual category and position.
Its prepared furniture-style model is used for the umbrella-tab preview, not as
an ordinary room-drop replacement. Preview/list installation and optional
composition remain required before playable handheld selection.

### Shared resource loader

The existing importer accepts the complete checked static-held category:

```sh
python3 tools/v3_furniture_install.py --refresh-runtime \
  --equipment-art build/v3-handheld-static-prepared-02 --output build/held-runtime
```

`tools/v3_equipment_runtime.py` verifies the prepared graphics and derives all
equipment motions from the source selectors. Fourteen complete models and
sixteen independently packed animations occupy 31,584 bytes. Their indices are
`17 + source resource index`; native indices `0..16` keep their original
meanings. Fifty fixed source slots preserve holes for unsupported skeletons.
This installs no new inventory identity, equipment kind, action, or choice.
Player holding/swing animations use the additional shared adapter below.

Five native resource getters at `800B12C8`, `800B12F4`, `800B131C`, `800B1614`,
and `800B1650` delegate to shared readers. They supply model/animation pointers,
types, sizes, segment origins, and VROMs. Original lookup tables and the real
DMA/bias functions at `800B167C` and `800B16D0` remain unchanged. The same DMA
functions are used by `808B5A10` when changing equipment and by
`mSM_load_player_anime` after menus. A transfer probe does not establish ordinary
menu-close or take-out/put-away gameplay acceptance.

The shared equipment/action module occupies `804A3000..804A8FFF`, after the
accessory package and before the existing furniture model pool. Equipment
code is bounded below `804A3B00`; an `AFHR` version-one header and fifty
16-byte records start at `804A4000`.
Each record is `(vrom, bytes, segment-six pointer, type)`. Four `AF48C0DE` words
guard both the original 8-KiB region and the complete 24-KiB module. Empty slots, negative/out-of-range indices, unsupported
skeleton type one, malformed sizes/pointers, and out-of-storage transfers reject.
Individual transfers fit the existing 4,376-byte equipment-bank lower bound.
This does not approve arbitrary combined model-plus-animation sizes.

The importer appends payloads and the module before the checked terminal
catalogue/shop resources. Changed compressed owners receive uncompressed
storage without changing their logical DMA identity or size; the three unchanged
terminal owners move after that storage. Existing model VROMs, saved profiles,
and item selection remain unchanged. Startup loads/checks the entire module
against a compiled CRC before publishing its code. The equipment length is an
explicit compiled bound, not inferred from an unchecked RAM descriptor.
Shared transfer verification and one instruction-cache
flush covering the complete accessory package keep startup at 952 bytes inside
the unchanged 992-byte reservation. The linker still rejects overlaps; no guard,
configuration, or call-return scratch space is repurposed.

### Player motion and split-body masks

The existing importer extends an installed held-resource module with
`--refresh-runtime --player-motion`. Eight complete player animations occupy
2,256 additional ROM bytes: the equipment holding poses, pinwheel holding,
fan idle, and fan swing. They use stable indices `130 + source animation index`;
native indices `0..129` are unchanged. Sparse slots preserve the donor's complete
157-index namespace. Every object has 26 joints and fits the existing 3,848-byte
player-animation buffer; no actor size or permanent allocation grows.

`AFPM` version-one records live at module offset `1340`, using the same
16-byte resource format with `type` holding the source's default part-mask index.
The extra donor mask's 27 bytes live at offset `1FD0`. The source's complete
part-index function/table and mask-copy function are verified. All four native
masks equal their donor counterparts; native copying is retained through a
guarded prologue bridge at module offset `FE0`. Only mask index four uses the
new donor data. **The fan swing explicitly requests mask four in its action
initializer; its generic animation-to-part lookup returns three.** Preserve this
distinction when implementing the action, rather than changing the default table.

Core size/origin/VROM readers at `800B11B0`, `800B1264`, and `800B1D68` support
the sparse imported records. The existing animation DMA and segment-bias
functions stay intact. Mask copying at `800B1DE8` preserves the original path
for indices `0..3`; invalid indices remain no-ops. The player owner's pointer
getter `808B468C` and default-part getter `808B5B38` retain their native tables
and every HI/LO relocation. Their out-of-native-range paths delegate to the
shared module. No animation index limit is raised over an unchanged short table.

The combined module has 1,472 code bytes inside its existing reservation.
Original equipment hooks are rebound to the compiled symbols; existing models,
motions, and native table meanings stay intact. Footstep/event readers whose
native limit is 130 continue to reject imported animations; action-specific
sound needs its explicit donor timing, not an unrelated original sound table.
This installs resource readers and masks, not player actions or selectable fans.

### Kind-indexed readers

`--refresh-runtime --equipment-kinds` adds the six native kind-indexed consumers
through the same importer/module. `kind_bindings` verifies complete donor
functions, table spans, and relocations for holding pose, item main routine,
shape, equipment motion, tumble, and get-up. All 79 donor equipment kinds have
stable extended indices `36 + source kind`, remaining below signed-byte 128.
This namespace does not duplicate inventory items or offer existing tools as
new browser choices. The shared equipment selector below consults independent
profile bits; preparing a category does not enable those bits or add choices.

An `AFKD` version-one header and 79 twelve-byte records occupy module offsets
`B00..EC3`, before the unchanged `FE0` native part-copy bridge. The linker caps
code at `B00`. Six signed sixteen-bit fields retain animation indices above
255 and negative missing-resource values. Missing skeleton models stay `-1`;
separate umbrella ownership is not represented as an invented model. The
complete source binding remains in the build receipt. Dispatch values 21–23
describe pending balloon/pinwheel/fan routines; reader installation does not
install those routines or permit a new kind to reach ordinary gameplay.

Native getters at `808BD668`, `808BD690`, `808BD6B8`, `808BD6E0`, `808C2D4C`,
and `808C32CC` retain all 36 original table entries and both HI/LO relocations.
Only non-native kinds delegate to the shared reader. Negative/out-of-range
kinds retain each getter's original fallback; malformed headers reject too.
The last two functions select tumble/get-up motions, not take-out/put-away.
No table bound is raised over an unchanged native array.

The same source tables require four complete player animations, source indices
25–28. Their 5,744 bytes retain full 17-/32-frame timing and fit the original
3,848-byte animation buffers. They extend the existing sparse `AFPM` table;
the eight previously installed motions remain unchanged. Fans use the donor's
axe-style tumble/get-up pose, rather than the unequipped fallback. Actual fan
button/actions and ordinary take-out/put-away still need implementation.

Combined model/animation size is checked per source record. Nineteen static
item/state records have complete resource pairs, with a maximum of 4,032 bytes
inside the 4,376-byte bank bound. Uninstalled rigs are not approved by that
check; their geometry and joint-work arrays remain dependencies. There is no
resident-memory, actor, saved-format, or optional-profile growth. The current
[checkpoint](../docs/checkpoints/V3_FURNITURE_PIPELINE.md#shared-equipment-kind-readers)
records native relocation/readers and representative motion-transfer evidence.

### Extended action tables

`--refresh-runtime --player-actions` installs shared action-table capacity in the
existing importer. `tools/v3_player_actions.py` resolves all 22 byte metadata
tables and five callback tables through complete GAFE01-r0 consumers, source
symbols, and actual REL relocations. The common source reader indexes relocation
records by section; `.rodata` callback arrays are not mistaken for all-zero data.
Their zero placeholders acquire function pointers from relocation records.

The 105 native action indices and every original value/callback remain unchanged.
Indices `105..120` reserve the donor's own identities, including fan action 109.
Their permissions, priorities, movement, texture, weight, bee, menu, camera,
footstep, pitfall, and draw metadata come from the actual source tables. Fan
action 109 has its complete setup, movement, and net-reset callback group; its
submenu and settle callbacks remain null as in the donor. The other fifteen
extended actions remain null and reject at the native setup-table gate.
Action availability does not enable equipment selection or import choices.

The `AFPA` version-one header and complete 121-entry tables occupy 5,164 bytes
from `804A7000`. Shared dispatch code starts at `804A5000` and is bounded below
the tables. The equipment module grows by 16 KiB, retaining all original
equipment code, records, masks, and guards. One startup DMA/checksum/cache pass
covers the complete 24 KiB without growing the 952-byte startup routine or its
992-byte reservation. No actor, ordinary heap, animation bank, or saved field
grows. The new reservation ends before the furniture pool at `80500000`.

All 27 action bounds point into full-capacity tables. The importer redirects 28
native HI/LO table references and removes exactly their 56 obsolete relocations,
leaving other relocations and the original owner dimensions intact. It preserves
the reference at `808B99D0/808B99D8`: that address is the exclusive end of the
preceding eight-float spatial-search array, not an action lookup. Redirecting it
would make that unrelated loop overrun its stack buffer. Unknown interior or
shared references reject instead of being moved speculatively.

Expanded callback tables retain native linked addresses, not a pointer captured
from one heap allocation. The five native indirect calls use two shared register
variants which resolve those addresses against the currently loaded player's
constructor at `80143900`. Resident imported callbacks retain their fixed
addresses. Argument registers, stack arguments, and return addresses are retained.
Ordinary scene changes can therefore relocate the player owner without leaving
stale callback targets. These thunks do not implement any missing action.

Complete source callback dependencies remain in the receipt. The fan's net-angle
callback uses the equivalent native reset alongside its compiled setup and
movement callbacks. The outside-owner audit retains all three native bounds of
105: `80093954` limits a resource byte length, not an action; the equipment-change
callback used by `800B3398` only returns `-1, 7, 8, 9, 10`; event-position checking
at `800B5AF4` already returns the donor fan's zero value outside the native range.
Complete consumer/callback bodies, callback registration, and the source event
table are checked. No unrelated core table is extended for fan action 109.

### Player ownership and actions

The same `--refresh-runtime --player-actions` adapter extends an existing action
module with source-derived fan controls, requests, setup, per-frame movement,
sound, and end-of-swing transitions. `overlays/v3/player_actions.c` resolves each owner function against
the currently loaded constructor; no heap address is captured at build time.
The complete donor functions and every called native API are recorded and
checked. The installed dispatch entry addresses and all original actions stay
unchanged. The promoted action code occupies 1,944 bytes; the unpromoted selection
build occupies 2,504 bytes of the existing 8-KiB code reservation. In-place
code refresh preserves animation banks, actor size, and save profile. The sound
adapter appends a relocated complete sequence, retaining existing banks/samples.
It adds no selectable items.

Press and hold are distinct, including title-demo controller bytes `38` and
`39`. Fan kinds `107..114` use the normal scene/visibility-aware kind getter.
Walking/running/dashing reject fan input at native animation speed `>= 1.0`;
the original umbrella helper remains unchanged. The shared poll calls umbrella
then fan, matching the donor order. Four ordinary calls at `808C12EC`,
`808C1CE4`, `808C2194`, and `808C2A38` reach this helper, retaining priority four
and subsequent native input checks. Their four owner-local JAL relocations are
removed so relocation cannot corrupt the resident targets. The umbrella's own
repeat call at `808DCAA0` and its relocation remain unchanged.

The request stores action 109 and the start flag in the existing request union
at `D58`, only after the original priority/permission checks accept it. Setup
uses native `808B4A44`, the ten-argument standard initializer with separate
frames, speed, morph, mode, and mask. `808B4B6C` is the reverse initializer and
has a different signature. The upper layer uses imported animation 270, the
lower uses native WAIT1 zero, speed is `1.0`, repeat mode is one, and explicit
part mask is four. Initial waving starts both frames at one with morph `-5`;
repeat waving preserves the lower current frame and uses zero morph. The
donor's continue-animation optimization applies only to WAIT1 in the upper
layer, so it cannot change this fan initializer.

The retained WAIT1 animation has duration 33 in both games, but its donor
initializer uses speed `0.5` while native `808C1118` uses `1.0`. The adapter
preserves source keyframe coordinates and doubles the fan's playback speed and
input-speed threshold to match the native update interval. Source event frames
remain unchanged. Native morphing advances by one per update, versus the donor's
half-step; the common `-5` initial morph value needs no change. Movement uses
native common braking `808B3C74`, including its native `0.75` step, instead of
copying the donor's per-update `0.32625001` constant into native physics.

At frame `7.5`, the transition routine settles priority and sets the bee-attack
state. From frame eight, holding A can request another swing. Both events execute
in order when one native step crosses both coordinates. Otherwise movement can
request walking, and reaching `end - 0.5` settles priority and requests idle.
When repeat animation wraps before that last half-frame is observed, transition
checking uses the crossed end coordinate without changing the rendered frame
or advancing animation/morph twice. Release cannot disappear at the wrap.
Native idle request takes `(game, morph, flags, priority)`, unlike the donor's
five-argument form. The donor stores its extra delay-frame argument but its idle
setup does not consume it; flag two is also ignored by both idle initializers.
The adapter preserves the effective donor behaviour instead of passing a float
frame value into the native flags argument.

The complete per-frame callback preserves donor order: brake, forced-position
input, animation, frame-event sound, lean recovery, standing-object correction,
background collision, held-item update, and end-of-swing requests. Sound triggers
at frame `1.5` only when animation advances; a frozen frame cannot retrigger it.
These functions form the registered fan action. Parent inventory and
profile/acquisition integration remain required. The action tables still reject
every unfinished imported action.

The actual donor fan sound uses group-one program `0167`, at sequence offset
`0812..0831`. Its 32 complete bytes have SHA-256
`add4eb8fd717a5bede73d2b94c800c9ee448cefe5926db27622570bb0093d0b2`.
The complete donor bank-154 instrument 12 matches native bank-140 instrument
12: ranges, decay, envelope, tuning, sample, loop, and predictor. The sample has
3,726 bytes and SHA-256
`92b3c527d5e80475098149b98901f53f0e72ad639c4de1cfc149d8c7cd05a99c`.
Both priority-table entries for `0167` contain 60. The expanded native group has
106 slots; the shared converter registers the previously empty `0167` slot.
`tools/v3_sound_programs.py` accepts explicit-bank single-layer notes with custom
envelopes and optional special-mode pitch sweeps. It preserves all operands and
only rebinds the layer/envelope pointers and equivalent instrument index. Full
instrument, envelope, sample, loop, predictor, tuning, priority, interpreter,
and heap checks reject unsupported dependencies. It imports source IDs in a
batch, without per-item conversion code. No new sample or bank is needed here.
The sequence grows by 32 bytes to 20,208 bytes; complete permanent-resource
accounting leaves 224 bytes spare without enlarging the audio heap. Silent native
verification covers loading, triggering, sample transfers, and the live per-frame
callback. No listening, ordinary equipped-fan, or hardware result is claimed.

### Held-item callback tables

The same callback-table converter also handles the two held-item categories:
main/update and drawing. It resolves the complete 24-entry donor tables through
their real consumers and expands the native 21-entry tables without changing
any original callback. The 208-byte table block lives at `804A8430`, inside the
existing module, and does not enlarge any allocation. Four table-reference
relocations are removed; native callback addresses remain linked and use the
current-owner resolver. The main dispatcher needs a `v1` variant in addition to
the existing `v0`/`t9` variants; all existing entry addresses remain unchanged.

Index 23 provides fan main/draw. The source main returns zero; the checked native
zero-return callback provides exactly that operation. Static held drawing emits
one complete model display list using the selected equipment bank and shared
resource getter. The original outer drawer retains hand matrix, item scale,
opaque stream, and temporary segment-six setup/restoration. Invalid bank or
missing model emits nothing. The native rod-tip flag at `F44` is cleared; the
donor's separate balloon-start flag has no native storage and is not invented.
Balloon and pinwheel indices 21 and 22 remain null pending their actual rigs.

The donor fan net reset matches native `808BE140`: angles `(0, 182, -7281)`,
fraction `0.2`, and step arguments `2730` and `100`. The native callback is
registered in action 109. The shared selector retains scene permissions and
extends passive-equipment permissions. Full scene rendering, parent inventory,
acquisition, and persistence still need integration. Ordinary equipped-fan use
is not established by direct callbacks.

The refresh updates an already resident player relocation resource in place
inside the import blob. Its reported blob checksum includes that change; it
must not write the new relocation bytes only after computing the blob receipt.
No owner, table, or audio allocation moves for this update.

### Selected equipment and visibility

Selected equipment is installed in the current locked development cartridge.
Host/cartridge checks and the combined parent-reader native check establish
actual selection, independent profile bits, and passive/scene/visibility rules.
The checkpoint retains the exact tested builds and initial fixture failures.
Ordinary inventory gameplay is separate from these component checks.

The native player selector at `808BD3F8..808BD583` reads ordinary saved equipment
at player-private offset `3EC`, or title-demo equipment at controller offset
`3C`. The shared hook at `808BD430` preserves that choice and the complete native
36-entry switch for `2200..2223`. Its table at `808E0274` retains SHA-256
`b46dbe4b89cb5647022dddcf27baa8e2ca8ea5ffc73c02a249f32b3c695c6af1`.
Other item IDs use the selected-equipment reader, not a widened short switch.
The hook's native continuation resolves against the current owner constructor.

An `AFHS` version-one table occupies 752 bytes at module offset `5500`, RAM
`804A8500`. Its four-word header contains magic, version, 92 source slots, and
eight-byte stride. Slots use donor `2200 + index`; each record contains parent
item, signed extended kind, passive-visibility flag, profile-byte offset, mask,
and equipment-ready flag. Empty slots reject. Bounds, identity, header, ready
state, flag values, and exactly-one-bit masks are checked before profile reads.

`selection_records` combines the complete source item/kind selectors, shared
room aliases, implemented action/held categories, and installed resource-size
checks. It generates all eight fan records without an item list. Their inventory
IDs are `2254..225B`, extended kinds `107..114`, and canonical collection-display
IDs `314C..3168`. Each uses its display's existing furniture-profile bit, not a
second bit or a selection-order ID. Current profiles leave those bits clear;
these are prepared equipment records, not enabled inventory items or web choices.
The importer rejects collisions with an already selected profile identity.

The visibility hook at `808BD638` runs only on the native passive-item branch.
It retains the native umbrella rule and adds selected source-category records.
The earlier scene, hidden-item, force-visible, and all-items checks stay intact;
force-visible still cannot bypass a forbidden scene or the hidden-item flag.
All three complete native selector/scene/visibility bodies are bound before patching,
and the source visibility function is hash-checked. No table relocation is
removed by these two hooks. Rebuilding shared code rebinds existing fan callback,
draw, and poll pointers to their actual compiled symbols.

Connect parent inventory/readers, acquisition, context-correct catalogue and
collection, and optional composition before enabling profile bits. Check complete
take-out/put-away, drawing, and persistence through ordinary gameplay. Keep
unsupported equipment categories disabled; do not borrow unrelated tool actions.

The native player holds two model buffers at `DBC`, animation pointers at
`DC4`, segment bases at `DCC`/`DD4`, and shape/animation indices at `DDC`/`DE4`;
the active-bank index is at `DEC`. `808B5A10` places an animation immediately
after its model, so combined sizes need explicit bounds before enabling new
pairs. The native skeleton initializer at `808BD934` uses item skeleton state
at `A18`, joint work at `A88`, and morph work at `AB2`: seven vectors per array.
The donor uses eight. A seven-joint balloon needs eight vectors including root
translation; do not enable it with the current native buffers or paste the
GameCube player structure's offsets into the N64 owner.

For fans, the donor implementation is in `m_player_item_fan.c_inc` and
`m_player_main_swing_fan.c_inc`. Its draw entry is `.text:173A84`; setup and main
action entries are `.text:1962B0` and `.text:1965A4`; the controller check is
`.text:164628`. The full player wait/swing animation descriptors are
`.data:16A2A8` and `.data:16A49C`. Those animations, the split-body fan mask,
per-frame callback, drawing, and sound define the action's dependencies. The
callback, sound, and held drawing are installed as described above. The complete
wait/swing and tumble/get-up data is installed through the shared animation
readers; action 109 reaches its setup/main through native dispatch. This does
not make the complete handheld item selectable or playable.

## Shared parent names and prices

`parent_records` consumes the installed selected-equipment records, not a second
list of item IDs. It verifies the complete donor name, price, and item-category
tables, price/category consumers, pointer dependencies, and terminal price
sentinel. The parent's official `itemName_tool` name and `tool_price_table` price
are independent of the furniture catalogue model's metadata. Every installed
name is credited in `translations/provenance.json`; the ordinary shared importer
generates any missing entries using the descriptor's source symbol/index.

The `AFHI` table at `804A87F0` has four 32-bit header words: magic `41464849`,
version one, count 56, and stride 24. It covers IDs `2224..225B`; absent records
remain zero. Each record contains:

| Offset | Bytes | Value |
| --- | ---: | --- |
| `00` | 2 | Parent item ID |
| `02` | 2 | Donor price |
| `04` | 2 | Canonical collection display ID |
| `06` | 1 | Extended equipment kind |
| `07` | 1 | Donor inventory category, not a native category assignment |
| `08` | 16 | Complete official English name, space-padded |

The table occupies 1,360 bytes and ends at `804A8D40`, before the existing
module footer. Eight fan records are populated; no selection bit changes.
The runtime requires a valid header/identity and the same selected, ready kind
as the equipment selector. Missing or disabled items return no name/price.
Name writes require a non-null destination with at least sixteen bytes; wider
item-name arguments reject. Prices retain the native sixteen-bit argument rule.

Shared reader entry points are `804A6000` for names and `804A6100` for prices.
Their entries share the 1,284-byte parent/icon image in existing action-module
space. Player action code is bounded below `804A6000`; parent/icon code is bounded
below the icon data at `804A6800`. Existing action callbacks and player-owner
relocation do not move.
The 696-byte display wrapper delegates only the new parent range to these
entries, keeping native items and existing furniture/clothing paths intact.
No permanent allocation, model/animation resource, or saved field grows.

The donor gives fans item category 43. This is not the ID-derived menu category:
`mTG_select_tag_decide_item_normal` uses `(item >> 8) & 15`, so fans use tool
menu category two. Retain that source menu behaviour; do not install 43 as a
menu index. The native `mNT_get_itemTableNo` has a 36-entry equipment table and
still needs explicit support for extended IDs and its actual consumers. The
separate pocket-icon reader is connected below. Do not replace fan artwork with
umbrellas or furniture leaves. The inventory-screen player model
also has its own item selector, kind tables, and draw callback, connected by the
shared inventory-preview adapter below: source
`m_inventory_ovl.c` functions `mIV_Get_player_item_shape_index` and
`mIV_pl_shape_item_draw_fan`. The world-player action/draw adapter does not
automatically update that owner.

Inventory/ground categories and menus, ordinary inventory-screen appearance,
acquisition, context-correct catalogue/collection, optional selection, and
ordinary persistence remain required before enabling new handheld items.
Original tools must not be duplicated as imports. Preserve existing ROMs/saves
and both V2 patchers.

## Shared pocket icons

`pocket_icons` consumes the installed parent records and complete donor
`tool_tex_table$765`, including every palette/texture relocation and its
category-table binding. Full drawing consumers are source-bound. All eight fans
point to the same source icon: `inv_mwin_utiwa_pal` and `inv_mwin_utiwa_tex`.
The converter deduplicates by source address and resource kind, preserving all
1,024 CI4 indices and sixteen colours. GX tiles become linear N64 CI4 and RGB5A3
becomes RGBA5551 through the existing converters. Partial alpha and incomplete
resources reject; there is no resizing or placeholder artwork.

`AFIC` version one starts at `804A6800`: four header words contain magic
`41464943`, version, count 56, and stride eight. Descriptors cover `2224..225B`,
with zero records for absent parents. Each contains an absolute palette pointer
and texture pointer. Deduplicated resources follow on 32-byte boundaries; the
complete block occupies 1,024 bytes within the existing 2-KiB reservation.
The reader at `804A6200` requires the same selected/ready parent as names/prices,
valid header, eight-byte alignment, and complete resources within the reservation.

The native submenu hook replaces the two tool-table address instructions at
`8085C954..8085C958`. It removes only their HI/LO relocations, retaining the
560-byte relocation allocation and all other owner bytes. Native tools retain
their descriptors, and earlier umbrella, gift, fossil, and gyroid branches keep
priority. Selected imports return the source icon; missing/disabled parents
skip drawing instead of indexing past the short native table. Full-width GPRs,
HI/LO, floating-point state, and the existing drawing arguments are retained.
Continuation addresses resolve against the currently loaded submenu owner.

The shared parent/icon code occupies 1,284 bytes below `804A6800`; name and price
entry addresses stay fixed. The complete equipment module remains 24 KiB and
uses its existing startup checksum/DMA. No allocation, action table, model,
animation, saved format, or profile bit changes. No fan becomes selectable here.
See the [checkpoint](../docs/checkpoints/V3_FURNITURE_PIPELINE.md#shared-pocket-icons)
for component evidence and the remaining native control/guard/render checks.

## Shared inventory equipment previews

`tools/v3_inventory_equipment.py` extends the separate inventory owner through
the same `--refresh-runtime --player-actions` importer. Its records join the
installed parent identities, equipment kinds, complete models, and player
motions to the actual donor inventory-kind and drawing tables. Complete donor
consumers and all table relocations are checked; there is no per-item list.
Unsupported drawing categories reject instead of inheriting a fan callback.

Native preview kinds `0..4` retain their original tools; `5` remains the empty
sentinel. Supported donor kinds use `source preview kind + 1`, so the eight fans
occupy `26..33`. The `AFIV` selector at `804A9C00` contains magic `41464956`,
version one, count 56, and stride four, followed by fixed records for parent IDs
`2224..225B`: a 16-bit item identity, an 8-bit preview kind, and an 8-bit world
equipment kind. Empty slots stay zero. The runtime requires the same selected,
ready parent used by the world selector; disabled or invalid parents return the
unchanged empty sentinel.

Eight 41-entry word tables start at `804A9400`, occupying 1,312 bytes. They hold
player-animation indices/pointers, item-animation indices/pointers, shapes,
skeletons, split-body parts, and draw callbacks. Each retains its first five
native values. Fan records use installed shapes `59..66`, full holding pose
269, and part three. Their null skeleton means the native loader skips item
animation, matching the donor static-model route. The complete existing
15,584-byte item bank and player-animation banks remain unchanged.

The inventory owner is VROM `00785700`, linked at `8087D480`, with relocation
resource `007898C0`. Installation redirects all eight table references and
removes exactly sixteen corresponding HI/LO relocations. Section lengths
`15664/1008/160/1504` and the 672-byte relocation allocation remain unchanged.
The item-selector entry at `8087D51C` delegates to the resident selector;
the callback call at `8087E610` delegates to the shared dispatcher. All other
owner instructions and tables stay intact.

Original callbacks retain their linked addresses in the immutable table. The
dispatcher resolves them against the currently loaded inventory owner using
its BSS pointer at `submenu->overlay + 106DC`, minus the native BSS offset
`41C0`. It does not use a cached heap address or the world-player owner. Imported
static drawing uses the existing held-resource pointer reader and appends one
native display-list call. The surrounding inventory renderer retains matrix,
segment, timing, and graphics-arena ownership.

The 540-byte adapter starts at `804A9000`; code is bounded below `804A9400`.
The complete equipment reservation is 28 KiB, ending at `804AA000`, with its new
guard at `804A9FF0` and all preceding module bytes retained. Startup transfers
and checks the complete module; its code remains 952 bytes. The extra 4 KiB
fits below the existing furniture banks at `80500000`. No ordinary heap,
model/animation bank, saved field, profile bit, or logical choice grows.

The shared native probe exercises loaded-owner relocation, selected/disabled
kinds, complete model/pose transfers, and the native draw-table/dispatch window.
Its original axe/shovel cases verify callbacks resolve to the loaded inventory
owner. It does not run full inventory construction, outer matrix setup, GPU
rendering, ordinary equip/put-away, or a save/reload cycle. Those remain required
gameplay checks before claiming playable imports. See the
[checkpoint](../docs/checkpoints/V3_FURNITURE_PIPELINE.md#shared-inventory-equipment-previews).

## Ground and handover category integration

The item-type reader is native `mNT_get_itemTableNo` at `800A5630`.
The seasonal category adapter supplies selected imported types and delegates
other items directly to translated `af_v3_item_type` at `8046744C`, bypassing the
core entry to avoid recursion. The original equipment table retains 36 entries.
Do not simply return donor category 43: each native consumer owns smaller
draw-index tables, and the police renderer also indexes a local start array.

Current-cartridge aligned direct-call discovery identifies these consumers:

| Native owner | VROM | Call offsets within owner |
| --- | --- | --- |
| Lost-and-found | `007E4DF0` | `01C8` |
| Cherry-season ground | `007E5880` | `4900`, `4938` |
| Winter ground | `007F0350` | `4900`, `4938` |
| Christmas ground | `007FAEB0` | `4900`, `4938` |
| Ordinary ground | `00805E30` | `4900`, `4938` |
| Item handover | `00858A50` | `07B4` |

This identifies direct calls, not a proof that indirect references are absent.
The shared ground source `fg_no2fg_type` supplies the type index; the donor
police path subtracts one before indexing its draw-start array, while handover
uses the category directly in separate material/geometry tables. Retain native
gift/mail priority, table bounds, actual owner lifetimes, and original categories.
Extend these consumers together before enabling the extended category.

The donor fan ground/handover artwork is distinct from both pocket icons and
equipped models. Complete source lists `obj_item_utiwaT_mat_model` at
`.data+8902E0` (72 bytes) and `obj_item_utiwaT_gfx_model` at `.data+890328`
(24 bytes) reference one 32-byte palette, one 32×32 CI4 texture, and four
vertices. The split-list converter retains 608 resource bytes, a 184-byte
material list, and a 24-byte geometry list, without resizing or simplified
graphics. The police/handover adapter installs these assets; the seasonal adapter
below reuses them for ground rendering.

Discover the category dependencies through the complete source draw tables,
including all four ground variants and handover/police tables. Feed those
records into the existing converter and shared installer. Preserve material /
matrix / geometry order in handover and avoid creating another per-item list.

### Shared category preparation

`tools/v3_item_categories.py` discovers all extra handheld parents and states
from the actual equipment selector and item-type table, then groups them by
source category. It checks both complete handover/police material and geometry
tables and all four seasonal ground descriptor chains. Each supported ground
descriptor has exactly one ordinary list, no shadow dependency, and the real
source callback with material/geometry indices zero and one. Changed callback
code, additional shadows/lists, conflicting artwork, ambiguous dependencies,
and incomplete owners reject rather than being omitted.

```sh
python3 tools/v3_furniture_pipeline.py convert --representation handheld \
  --assets-only --category item-category-art --output build/item-category-art
```

The nine categories cover 43 parent/state records, not 43 newly selectable
items. Worn axes and catalogue representations do not become independent
imports. `--select` narrows the prepared categories by parent identity; each
shared resource retains every source parent using it. The prepared format is
`AFV3-ITEM-CATEGORY-PREPARED-ASSETS-1`; both furniture and held-equipment
installers reject it. A native category adapter must consume it explicitly.

`prepare_material_pair` uses the ordinary shared complete-model parser on the
ordered material/geometry pair. It then splits the validated command rows at
the actual source boundary, accounting for the paired Dolphin texture/tile
instruction. Material fragments cannot contain vertices, triangles, or nested
calls, and geometry fragments cannot change material state. There is no
fragment-parser mode that bypasses complete triangle/dependency checks.
The geometry emitter preserves inherited texture state, adding no texture-LUT
reset or preamble. Original full-model emission stays unchanged. Removing the
material list's return and concatenating the geometry list reproduces the
complete joined-model commands; the real renderer can insert its matrix
between the separate lists without moving the vertex load before that matrix.

Each category produces a complete 816-byte object. The nine-resource batch
contains 7,344 bytes, 9,216 CI4 texels, 144 palette entries, 36 vertices, and
18 triangles. Ground descriptors retain each source variant's real base:
the first three use 68, and the fourth uses 70. Do not impose one assumed
season-independent category offset. Preparation changes neither the cartridge
nor any saved/profile ID. The runtime adapter below supplies police/handover
tables and capacities; seasonal ground integration remains required.

### Shared police and handover runtime

`tools/v3_category_runtime.py` runs through the existing shared installer:

```sh
python3 tools/v3_furniture_install.py --refresh-runtime \
  --item-category-art build/v3-item-category-art-02 --output build/category-runtime
```

The category adapter checks the complete prepared source relationships,
resources, split lists, and generated commands. It installs all nine complete
objects in the equipment module. Only vertex, palette, and texture pointers
change: segment-six references become physical segment-zero addresses within
their permanent reservation. Resource contents and all other commands remain
unchanged. Callers do not need to replace their current segment-six binding.
Material and geometry remain separate so the native renderer inserts matrices
before vertex loading.

Native categories `0..26` retain their exact values and graphics. Added category
IDs use `27 + donor category`, independently of selected parents or conversion
order. Fan category 43 therefore uses native category 70. The current 71-entry
material and geometry tables share their original 27 values between both
owners; unused extended slots are zero. This is a transient drawing category,
not a saved item identity or an ID-derived action-menu index.

`AFCT` at `804AA200` has four header words: magic `41464354`, version one,
native capacity 71, and source-map width 53. Its 53 byte entries map supported
source categories; other entries are zero. The 344-byte reader at `804AA000`
requires valid installed parent metadata, a matching selected/ready equipment
kind, and a supported map entry. Unsupported or disabled extra parent IDs
return zero without reaching the original short equipment table. Other items
delegate to the existing translated item-type entry, preserving furniture and
original category decisions.

Material and geometry tables start at `804AA300` and `804AA41C`; each is
284 bytes. The nine objects occupy 7,344 bytes starting at `804AA600`.
The complete equipment reservation is 40 KiB, ending at `804AD000`, with guard
`804ACFF0`. The prior 28-KiB module prefix stays unchanged. Startup transfers,
checks, and flushes the complete module; its existing 952-byte code allocation
does not grow. All ordinary model/animation banks remain unchanged.

Police owner `007E4DF0`, linked at `808EB720`, receives matching capacity
changes: 70 start indices, a 184-byte setter stack frame, and an 18,060-byte
actor (88 bytes larger). The draw-position offset within the draw table becomes
`90`; all 257 68-byte matrix nodes remain. The following item-table offset within
the actor becomes `4648`. Allocation size, all matrix/item-table consumers,
clear/copy bounds, and drawing limit change together. Capacity remains three
modulo four to preserve the native two-plus-four-way unrolled copy. The output
helper uses an unsigned range check, rejecting negative and out-of-range indices
before any array access.

Handover owner `00858A50`, linked at `80963DC0`, retains its actor size,
animation, and drawing body. Both owners redirect their existing category call
and two complete table-reference pairs. Each drops exactly four obsolete HI/LO
relocations; all other owner code/data, relocation records, and resource sizes
remain unchanged. The changed compressed resources use the existing checked
uncompressed blob storage and preserve their logical DMA identities.

The seasonal adapter below connects the global item-type entry and all four
ground consumers. Neither adapter enables a parent/profile bit, creates a browser
choice, or changes a saved format. Do not enable handheld imports until the
remaining consumers, acquisition, collection/catalogue, and optional composition
are connected. Ordinary police/handover gameplay, GPU appearance, and persistence
are distinct from the focused native component checks recorded in the
[checkpoint](../docs/checkpoints/V3_FURNITURE_PIPELINE.md#shared-police-and-handover-runtime).

### Shared seasonal ground runtime

`tools/v3_ground_categories.py` uses the shared installer with
`--refresh-runtime --ground-categories`. It consumes the installed category map
and complete material/geometry resources, without repeated conversion or per-item
definitions. Each seasonal renderer has complete source hashes, relocation
inventories, and allocation contracts.

The 1,612-byte adapter starts at `804AD000`. Four 36-byte records at `804ADC00`
contain loaded-owner slots, native constructor offsets, original tables/counts,
expanded counts, new table/part offsets, callback offsets, and category bases.
The full module is 44 KiB, ends at `804AE000`, and has guard `804ADFF0`. Startup
remains 952 bytes and transfers/checks/flushes the entire module. Existing
artwork, player models, motions, sounds, and inventory tables remain unchanged.

Each overlay gains owner-local BSS, preserving every old BSS offset. Its
constructor wrapper copies the original relocated scenery rows and builds nine
category descriptors against that loaded owner. Four HI/LO pairs redirect table
consumers while retaining their native relocations. Only the actor profile's
constructor pointer loses its obsolete relocation; the replacement is resident.
The core allocation descriptor and relocation BSS size agree on the new bounds.

| Renderer | Categories | Category base | Overlay growth | Actor growth |
| --- | ---: | ---: | ---: | ---: |
| Cherry season | 108 | 37 | 1,376 bytes | 864 bytes |
| Winter | 107 | 36 | 1,360 bytes | 856 bytes |
| Christmas | 108 | 37 | 1,376 bytes | 864 bytes |
| Ordinary | 108 | 37 | 1,376 bytes | 864 bytes |

The original `NONE` value remains 64, or 63 in winter. It can receive a nonzero
start index during native classification. Because the expanded copy includes
that formerly excluded slot, every unassigned extended row points to a real
32-byte descriptor with zero ordinary/shadow drawing lists, not a null pointer.
Existing single-item `NONE` comparisons remain unchanged. Assigned categories
have one ordinary list, their actual native callback, complete material/geometry
pointers, and no shadow.

Four expanded index arrays are appended after each actor's original allocation.
Native constructor windows install their pointers/counts. The common state and
all 257 matrix nodes per block keep their offsets. Christmas's interleaved light
records retain their original `484` stride and matrix-node references; only the
independent index-array stride changes. Native setters use 264-byte frames,
expand every incoming argument offset, and retain each variant's two-byte index
format and four-way copy remainder.

All twelve ground furniture-type windows use the same selected-item query and
resolve continuations through their respective loaded-owner slots. Original
furniture, scenery, and equipment retain their values. Native category numbering
remains `27 + donor category`; saved identities never depend on season or order.

The adapter is implemented in a proposed build, not yet the promoted lock.
Focused host/cartridge and optional-composition checks pass; native validation
is incomplete at the setter-copy window. See the exact evidence and unresolved
check in the [checkpoint](../docs/checkpoints/V3_FURNITURE_PIPELINE.md#shared-seasonal-ground-runtime).
Full outdoor gameplay, acquisition, collection/catalogue, optional parent
selection, persistence, and original hardware remain required before completed
handheld imports can be claimed. Both V2 patchers stay unchanged.
