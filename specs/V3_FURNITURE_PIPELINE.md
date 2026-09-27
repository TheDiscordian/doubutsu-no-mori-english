# Automatic furniture import pipeline

## Workflow

Importing includes extraction, conversion, bulk asset/data installation, and
working item behaviours. Item-specific behaviours are not automatically deferred
until shared categories are finished. Conversion readiness is independent of how
players obtain the result. Prepare complete source resources even when rewards
or interactions remain unfinished, and retain explicit pending gameplay status.
Nook code-entry and gift systems are not prerequisites for completing a model,
material, or rig converter. Keep incomplete gameplay out of selectable imports.

### Automatic category dependencies

Furniture `import` plans implemented category dependencies from the selected
source records and checked current build. Clock, storage, hit-animation,
camera-facing scrolling, displacement-driven rolling rigs, and implemented
material lifecycles share this path. Missing rig/material resources, required audio, and complete behaviour
profiles are installed through the existing guarded runtime builder in that
order. Ordinary item installation follows a fresh eligibility check against the
resulting build. Missing acquisition remains explicit, not fabricated shop stock.

Rotated radio records also plan missing shared player-exercise stages: complete
motion resources, then native interaction. These stages run after room/music
profiles and also run when no graphics remain to convert. Installed stages are
skipped; a stage must publish its expected dependency before the plan advances.

`--category` selects a complete matching batch; `--select` limits identities.
Internal selected stages scan only those records. Prepared artwork is reused
across stages, and already installed dependencies are skipped. Every stage has
an immutable build lock; `pipeline.json` records the dependency plan, actual
steps, imports, pending reasons, and final lock. A dependency-only build does not
claim that pending items are available to players.

`v3_furniture_install.py --refresh-runtime --room-rigs-code` rebuilds only the
shared room code and its bound callback profiles from an explicit current build
lock. It preserves installed models, audio, selections, and saved fields. Use
this after changing shared code when no new resource category needs installation;
profile-only staging retains existing code unless it installs a newly implemented
material lifecycle; that stage rebuilds the shared packet and callback bindings.

### Built-in native profile staging

The same dependency planner stages complete native drawing/contact profiles,
constant model sequences, indexed static model/palette selections, and building
palette fades when their remaining metadata gate is acquisition. This stage
does not enable the selector or fabricate a reward. Identity correspondence,
source behaviour, placement layer, and action-sound checks precede eligibility.
Shared prepared-artwork validation retains every layer, scalar field, and palette.
The room runtime's `plain_rows` records these complete built-in paths; direct
models and flattened sequences use a zero vtable. Building fades reuse the
checked shared callback, complete resident packet, loader, and public entries.
Unchanged category code is not recompiled. Full canonical profiles, names, and
prices are installed inactive, with separate acquisition/catalogue/scoring flags.
Subsequent scans skip installed profiles. Later acquisition promotion verifies
and reuses the same complete model instead of appending another copy.

### Profile-owned creature resources

The shared profile reader accepts complete source-owned rotational rigs as well
as callback-owned rigs. `embedded-profile-keyframe-assets` preserves the profile's
direct display lists, every skeleton joint/model, all motion arrays, and the
12-byte skeleton/animation/speed descriptor. The converted descriptor uses
segment-six pointers and an aligned 16-byte allocation. Direct tank/cage lists
remain separate from the skeleton's model bindings. The static creature form
uses `static-creature-profile-assets` and retains all original layers.

The reader rejects unbound pointers, unsupported scalar/interaction fields,
partial resources, invalid speeds, and unknown callbacks. The complete shared
creature sound callback and its positioning helper are checked independently;
the descriptor retains the actual sound ID and excluded transition states.
Preparing this callback does not install its native audio or lifecycle.

Creature displays carry source-derived parent identities. Both complete donor
placement/pickup functions and the fish-index helper establish the carried ID,
inverse mapping, and official carried name. Display names remain distinct where
the donor uses a different spelling. These are representations of their parent
creatures, not independent furniture choices. Native identity correspondence,
room lifecycle/audio, inventory, catching/releasing, and collection readers must
be connected before eligibility. Metadata and native profile writing reject
these prepared-only categories until that integration is implemented. Preserve
the native herabuna when resolving the donor brook-trout slot.

### Composite models and dual-motion resources

`Source.model_graph` expands ordinary relocated display-list calls in execution
order. It retains every caller state command and every callee geometry/state
command, removing only calls and their matching returns. Full-symbol receipts
and flattened relocation positions accompany the result. Cycles, tail branches,
early returns, incomplete commands, depth beyond eight, and output above 64 KiB
reject. Direct models retain their established absolute-address convention.
The parser accepts a third explicitly bound scrolling display-list segment, 10;
this does not permit arbitrary unresolved calls.

`rotated-fixed-material-assets` identifies the complete radio lifecycle and
drawing functions. Both nested models, their shared vertices, both textures,
the fixed palette, and the -157.5-degree draw rotation remain. Room music
ownership, its constructor/destructor interactions, exclusive playback, and the
36-source-tick note emitter are installed integration dependencies. Mode 12 uses
the first/last words for the complete model and fixed palette, with zero skeleton,
animation, joint, and shown fields. Every pointer is aligned and bounded by the
complete object. The ordinary importer reuses the prepared object, reserves the
append-only legacy identity, and installs the inactive profile and official name.

`room_music.c` shares the original owner's 24-byte music state with native stereos.
The all-off mask includes both music bits (`4008`); general song reservation does
not call the native minidisk-item decoder. Checked loader entries replace music
application and common disk destruction, including the source aerobics exception
to positional playback. Rebuilds rebind the actual owner entries to the current
bootstrap. Carrying/colour checks restore only these verified hooks before checking
their original complete owner dependencies; arbitrary owner changes still reject.
The original actor stride, heaps, and saved fields do not change.

The complete source sequence/font/samples are compared with native audio. Only
initial volume/mute-scale operands may use the native mix; changed channel or note
data reject. The complete native effect 32 supplies all three note models and five
colours. Its native growth/debug scaling is retained as a documented platform
adaptation, not claimed to reproduce the donor particle trajectory exactly.

The source indoor player-aerobics interaction is installed through the shared
player-action refresh. Its complete twelve-motion category includes the 161-frame
motion and enlarged native animation banks. The registered gesture/chaining/tempo
core uses native controls, wait/action dispatch, eligibility, both camera readers,
and actual audio-clock/tempo fields. Checked startup and constructor reset own
its immutable code and transient state. The shared profile reader verifies these
bindings before recording `indoor_aerobics_installed`. See
[exercise motions](V3_HANDHELD_ITEMS.md#shared-exercise-motions-and-player-controls).
Room music alone cannot make this item eligible for selection. Original
acquisition remains a separate requirement. See the
[radio checkpoint](../docs/checkpoints/V3_FURNITURE_PIPELINE.md#installed-radio-room-music-lifecycle).

`dual-motion-scroll-rig-assets` retains both complete animation headers and all
motion arrays, in addition to every skeleton joint and model. `motion_offsets`
uses semantic opening/closing order independently of physical header sorting.
The chest supplies six joints, five displayed models, and two 51-frame motions.
Its three independent 32-by-8 scrolling layers retain source phases 0, 5, and
15. Preparation never enables the ordinary import or native profile.

`room_dual_motion.c/.h` converts the complete source-order constructor, movement,
destructor, and draw behaviour. The caller resolves closed/open animation
pointers, durations, mapped clicks, full positioned-loop ID, actual front contact,
and context predicates. NPC contexts force closed; other contexts use saved
switch equal to one. A nonzero press toggles only at the front while idle;
the newly selected motion starts at frame one and speed 0.5. Sound threshold
tests precede animation evaluation, matching GAFE01 revision 0, not the later
Australian callback. Two source steps are required per native room update, with
the press delivered only on the first. Accepted state must be mirrored before
native save capture, and the actual destruction callback must remain connected.

The core uses the existing larger joint workspace without changing actor size
or saved fields. Drawing reserves an aligned parent matrix, all three tile lists,
and the complete opaque/translucent command requirements before mutating arenas.
Room and preview counters both convert to the source rate with unsigned wrap.
The installed mode-11 dispatcher binds front contact through the actual room clip
at `80136F2C`, its owner, and direction at owner offset `1A0`. Scene selection uses
the native saved scene at `80126EB4`; NPC house 6 forces closed. The complete
35-scene table and added campsite selector are hash-checked. Neither provides a
GameCube basement or cottage, so the source basement-only scroll pause cannot
occur in the supported native scenes. New scene support must revisit this binding.

The 24-byte rig record retains the full opening pointer in `animation`, the full
closing pointer in `first`, both mapped trigger words in `last` (opening high,
closing low), and the complete source loop ID in the previously reserved byte.
This byte remains zero for every other mode. Both motion headers must be distinct,
aligned, within the object, and retain their complete valid frame counts. A
resource-only record has zero trigger words and cannot dispatch. Profile staging
binds and checks both complete programmes, full instruments, native scene/contact
readers, start-disabled placement, destruction, and save-state mirroring before
republishing the shared packet. The ordinary importer handles resources, triggers,
loop audio, and profiles in dependency order; unfinished acquisition stays separate.

### Multi-instrument trigger programmes

The sound converter retains layer-level instrument commands (`C6`), including
switches back to an earlier instrument. Every referenced complete instrument,
envelope, sample, loop, predictor, and tuning record goes through the shared font
importer. Binding requires an explicit mapping for every layer instrument;
missing or out-of-range mappings reject. Notes, rests, pitch sweeps, and timing
stay intact. Re-registering a bound fragment preserves its native instrument
selectors and source receipts.

All six source dispatch tables contribute programme boundaries even though only
the supported groups are imported. This prevents a sound's extent from absorbing
unrelated following programmes reached through another table. No unaccounted
tail is silently removed. Furniture behaviours can request additional trigger
words together; one shared font expansion handles the whole batch and records
every mapped word. The chest needs distinct opening and closing triggers plus
its separate continuous level sound. Preparing these resources does not install
its gameplay profile or establish audio synthesis.

### Reversible motion and larger skeleton work

`reversible-keyframe-rig-assets` recognises the complete stopped/reversible
constructor, move, draw, and destruction callbacks. It retains every skeleton
node and motion channel, including hidden joints. Prepared artwork alone does
not enable ordinary imports. The ordinary category importer
installs its complete dispatch, audio, identity, and persistence bindings before
allowing selection. Mode 9 stores the animation duration as a float in the first
word and requires a zero last word. It uses the shared trigger-sound table.

The matryoshka has eleven joints and five displayed models. The native fixed
vectors hold eight joints plus root, so using those vectors directly is unsafe.
`room_reversible.c/.h` instead reserves two seventeen-vector arrays and a switch
state in unused slots six through nine of matrix buffer zero, at actor offsets
`390..45F`. This 208-byte work fits the existing allocation without changing the
`740` actor stride or saved fields. The adapter must bind the complete native
drawer and enforce at most six displayed matrices and sixteen joints. Both
matrix-buffer parities keep that region untouched. Other rig categories retain
their own layouts; this is not simultaneous needle/motion work on one actor.

The converted source step accepts any nonzero press only while idle, reverses
start/end frames at speed `0.5`, plays the complete source sound, and stops when
the keyframe evaluator returns one. Initialization derives state from saved
switch equal to one; destruction writes the internal state back to the native
switch. The room adapter performs two source steps per 30-Hz update, delivering
the press on the first step. N64 captures switch flags before destroying actors,
so the adapter mirrors the accepted internal state after construction and each
update, including rejected presses while moving. The actual destruction callback
also remains connected. This preserves the switch that the donor destructor
would save without changing the N64 owner's save order or other furniture.
The complete native evaluator/drawer, switch capture, input toggle, and three
removal paths are checked before installing this layout.

The bootstrap shares checked two- and four-argument dispatch helpers across
ordinary, material, and scrolling callbacks. Destruction has its own checked
entry, and every entry still loads and verifies its packet before calling it.
Cache publication follows data writeback and instruction invalidation; failed
DMA or checksum verification cannot dispatch. The sound converter accepts a
complete one-step envelope followed by its terminator, retaining all timed notes
and rests. Empty or malformed envelopes remain rejected.

### Reversible material and particle rigs

`reversible-material-effect-rig` recognises a complete stopped/reversible rig
with delayed material selection and a particle emitter. Full callback instruction
shapes, relocations, constants, source helpers, joint callbacks, motion channels,
and dynamic texture tables establish the category. Every source model remains,
including the joint hidden from opaque drawing and explicitly redrawn translucent.
The generic graphics converter retains the complete texture/primitive/environment
colour interpolation and alpha formula. No item-ID switch chooses these conversions.

Mode 10's first word points to a 32-byte immutable block; its last word is zero.
The block stores big-endian duration float and fire-model pointer, segment/frame
count/sound/joint bytes, delay and frame-size halfwords, five frame-offset halfwords,
and six zero padding bytes. Parameters, model pointer, complete frames, and memory
bounds are checked before dispatch. Profile binding requires installed complete
loop/click audio, the complete steam engine and source, extended joint work, and
destruction. Missing particle dependencies install before rig code is published.

The category reuses the larger reversible workspace and adds delayed state,
steam countdown, and switch-delay halfwords in the same unused matrix slots.
Actor size, heaps, and saved fields do not change. Its source constructor uses
`saved switch != 1`, distinct from the plain reversible category. Any nonzero
press is accepted only when both animation speed and delay are zero. Each native
update performs two source steps, with the press delivered on the first. The
19-tick delay, .5 motion speed, exact loop/trigger order, and randomized steam
countdown are preserved. Loop and steam pause during the mapped transition
states; click acceptance does not. Steam appears 18 units above the actor with
spread six and a new `int(10 + random * 20)` interval. The complete native float
random routine is bound at `8002C9AC`. Accepted state is mirrored before native
save capture, and the source destructor remains connected.

Drawing uses delayed state in gameplay and the source end-frame test in previews.
It selects from all four on-table entries or the separate off image, using twice
the native room/graphics frame. It reserves command space in both streams and
two aligned matrices before changing the arenas. The hidden joint is redrawn
with its original fire model and current joint matrix; both matrices and the
skeleton's submitted matrices are written back. Crowded arenas leave drawing
unchanged. Ordinary GPU appearance and hardware behaviour require playtesting.

### Combined skeleton and timed materials

`material-keyframe-rig` combines the complete skeleton/motion converter with the
typed dynamic-texture converter. Callback instruction shapes, relocations,
repeat initializer, sound helper, and full resource tables identify the category;
item IDs do not select the conversion. The ordinary category importer installs
graphics, complete loop audio, and profiles before checking actual acquisition.
The hamster cage supplies seven joints, five models, two complete texture frames,
and a positioned loop. Nothing is replaced with an inert display model.

Rig mode 8 points its first word at a 32-byte immutable parameter block; its last
word is zero. The block contains segment/frame-count/sound/reserved bytes,
big-endian divisor and frame-size halfwords, eight frame-offset halfwords, and
eight zero padding bytes. Every used frame is aligned and wholly in the object;
unused offsets and padding must be zero. Installed bindings verify the complete
block, graphics, sound resources, and compiled dispatch feature.

Construction evaluates the repeating motion once at speed `0.5`. Each native
30-Hz update runs two source evaluations at speed `1.0`, then refreshes the
positioned sound, including transition states as in the donor. Drawing selects
`((graphics_frame * 2u) / 5u) % 2u`, with unsigned wrapping, independent of room
play-frame or on/off state. Segment 8 precedes the complete skeleton draw. The
actual actor remains the draw callback argument, and the graphics-frame parity
selects the existing matrix buffer. Bounds reserve the extra segment command;
no actor, saved field, or heap allocation grows.

### Switched joint motion and translucent redraws

`joint-callback-rig-assets` retains its reusable complete artwork descriptor.
A separate checked lifecycle binds source create/move/draw code, helper code,
relocations, constants, and audio. The ordinary `import` command installs all
complete lifecycles in the selected category together, reusing prepared objects.
The implemented motion kinds cover lighthouse easing, moon clock/rotation, and
snowcone easing/scrolling/sound, and parent-sensitive compass motion. Parent-sensitive
motion requires the installed carrying adapter and its actual parent readers.

The parent-sensitive needle conversion is in `room_needle.c/.h`, with complete
donor bindings in `v3_furniture_needle.py`. It preserves the eighth-source-tick
rotation kick, signed phase wrapping, damping, ordered self/parent contributions,
and world-angle correction. One source step is explicit; the room adapter must
execute two steps per native update. Constructor evaluation uses speed `0.5`
before stopping the keyframe. The source debug phase/decay inputs are explicit.
Transient work needs sixteen bytes and no saved fields.

Recognition checks complete callbacks, helpers, constants, and the relocated
status jump table. Native rotation states 3/4 correspond to donor left/right;
wait states 8/7 precede them. The ordinary lifecycle planner validates this
contract and rejects installation without complete installed parent support.
Prepared artwork remains reusable without descriptor changes.

The native room move/draw loops use the installed shared adapter for the donor's
moving-parent registration and carried-child transform, including foreground
removal/restoration and final child positions/angles. The joint dispatcher binds
the actual parent and angle-delta exports from that verified packet. A permanent null parent, a fixed
needle, or merely lifting the native movement restriction is not an implementation.
The donor routines live in `ac_my_room_move.c_inc`, `ac_my_room_draw.c_inc`, and
`ac_my_room_action.c_inc`, alongside the parent readers in `ac_my_room.c`.

`room_carry.c/.h` provides the converted carrying core. Its 152-byte transient
state contains a parent ID/captured angle and four 36-byte slots. Each slot
retains relative/world positions, a child actor ID or loose-item identity, and
the captured loose-item angle. The six footprint shapes use a 16×16 grid of
40-unit cells. Actor layout assertions preserve the native `740` stride.

The owner supplies actual foreground, actor/used arrays, lookup, placement,
tabletop height, angle, and drawing operations. Missing operations reject
registration; they are not no-op fallbacks. All children validate before any
foreground mutation. Duplicate actor references use one slot and clear each
occupied source cell. Negative/out-of-grid footprints reject. World transforms
follow `T(parent) R(angle delta) T(parent base) T(relative)`. Furniture drawing
uses the carried world position and its own angle plus the parent delta; the
needle still receives its own angle and the separate parent delta.

The movement hook must update carrying after the parent's final position/angle
snap, then release. Release validates all destination cells before restoring
foreground and placement, snaps child furniture to cell centres, and updates
its short/float/target angles. A failed restoration retains active carrying
state; the adapter must handle failure without losing the detached items.
Native `kept_item` at `73A` is storage/music content, not a tabletop child, and
its movement restriction stays intact.

The N64 `Shop_Goods` clip is eight bytes with only single-draw and drop callbacks.
Its single and ordinary drawing paths lack the donor's loose-item Y rotation.
`room_goods.c/.h` supplies a transient 512-byte angle grid, clear-on-successful-
drop behaviour, both drawing paths, and the actual donor per-category rotation
flags. It scopes carried-object angles around the complete native single draw,
preserving nesting and unrelated dropped-item drawing. The grid clears when the
owner is constructed and becomes unavailable during destruction, including when
there is no allocated clip. The original category count, dropped-object cleanup,
clip allocation/free, model table, and call delay instructions are retained.

`v3_room_goods.py` checks six complete donor functions and relocations, the full
90-row donor drawing table, and the complete native owner. Native category flags
come from matching category ranges; conflicting flags reject. The three native
categories absent from the generic donor table retain native orientation.
Five call replacements remove only the two affected overlay relocations.

The resident code has a 4-KiB reservation at `804D9000`; transient state reserves
1 KiB at `804DC000`, using 524 bytes. The checked surface startup loads the
independent code packet before the native actor chain, without growing the main
startup or existing room bootstrap. Every shared runtime refresh retains this
preload and the editable surface checksum field. The donor angle grid is
transient, not a new save-format requirement.
The carrying adapter is installed through twelve checked owner call/count
replacements, preserving native destination permission and stored-item checks.
It occupies `804DA000..804DBFFF` plus transient state at
`804DC400..804DC7FF`. The shared startup loads and verifies its independent
packet after loose-item code. Final position/angle snaps precede restoration;
failed ordinary restoration retains the carrying state for a later retry.
Teardown completes an accepted in-flight movement before native persistence.
Installed-resource and host checks do not
establish ordinary native drawing or original-hardware behaviour.

Rig mode 6 uses first-word low byte 1/2/3/4 for these source motion kinds. Kind 3
also stores complete level sound `51` in the next byte and clicks `0016/0017`
in the last word. Kind 4 has no sound and a zero last word. It uses the native
stopped initializer, evaluates once at speed `0.5`, then stops. Each update runs
two source steps with the actual carried parent's state; joint three subtracts
own angle, parent delta, and damped needle offset. Its sixteen-byte work occupies
`450..45F` inside unused matrix slot nine. Native debug registers CRV 80/81 retain
source phase/decay adjustments without allocating a new debug owner.

The complete carrying packet, goods dependency, all twelve installed owner
hooks, relocations, and exported reader bounds are checked before enabling this
lifecycle. The original complete movement/draw dependency hashes are compared
after verifying and reversing only those known hook windows. Artwork alone or
an `installed` flag alone does not satisfy the dependency. Unknown parameter
combinations reject. The source's initial
evaluation runs at half speed; movement performs two source steps per N64 update.
Moon rotation starts from actual RTC minutes/seconds and retains source wrapping.
Snowcone starts disabled through the native placement adapter, retains both
clicks and its complete loop programme, and maps source transition exclusions
to native states 5/6/13/15.

Actor stride remains `740`. Motion floats use `450..457`, inside unused matrix
slot nine of buffer zero, outside all nine root/joint and morph vectors. The
complete native evaluator, drawer, and owner are bound: at most eight displayed
joints consume one matrix each. Custom-owner drawing does not overwrite this
work area. Both matrix-buffer parities retain independent actor state.

Before/after callbacks preserve all models. Lighthouse joints 3/7 and snowcone
joints 3/4 move to the translucent stream using the original shape pointer and
joint transform. Lighthouse retains beam colour/LOD; snowcone retains alpha and
both scroll tiles over its full source image. Moon retains its joint-one Z
rotation. Each draw checks both graphics arenas and reserves 240 aligned bytes
for parent/joint matrices and tile commands; all used matrices are flushed.

The complete shared room packet has a 36-KiB layout at `804D0000..804D8FFF`,
with a 32-KiB code reservation and the existing 4-KiB record table at `804D8000`.
The reaction state at `804CD000..804CD3FF`, colour state at
`804CD400..804CD4FF`, and model pool starting at `80500000` remain separate.
Effect callbacks and controller/player bridges are rebound to the moved code.
Older 8-/20-KiB layouts remain valid inputs; extension never shrinks a wide packet.
No saved field or actor allocation grows. Acquisition remains a separate pending
requirement for these three objects, so the installed profiles stay inactive.

### Direct-model interactions and town-tune instruments

`static-interaction` recognises complete move callbacks while retaining every
direct profile model. Recognition uses checked instruction shapes, relocations,
helper implementations, and source parameters, not item IDs. The ordinary
`import` command installs trigger or town-melody audio before staging complete
profiles. Prepared models are reused without recompilation. Unknown callbacks
remain preparable artwork, not implicitly inert furniture.

The shared immutable table lives in the room packet's code/constant reservation.
Its header is magic `41464931`, count, eight-byte stride, and zero reserved word.
Each record contains a native index, mode byte, parameter byte, native sound
halfword, and zero reserved halfword. Mode 1 takes one Bell from the current
player's nonempty wallet and plays its complete source sound. Mode 2 forwards the
source instrument parameter through the native room clip's melody callback.
Both preserve any-nonzero interaction pulses and the absence of transition-state
exclusions. Melody position updates continue without a new press. The shared
dispatcher handles these records before the stricter ordinary-trigger gate.

Native wallet offset `38` is bound to the current private pointer at `80136FD8`;
the donor's `8C` offset is never copied. The melody callback is clip offset `64`
at pointer `80136F2C`. Complete native registration, dispatch, data getter, and
two-track instrument functions are checked. No actor or saved allocation grows.
Room and catalogue index forms resolve the same complete model/behaviour.

The musical adapter extends the three complete instrument tables in native
sequence 203 from fifteen to sixteen entries. It preserves every original
program and changes only four verified table references. The complete donor
sequence 246 supplies the new header, flags, nineteen notes, channel commands,
pitch, duration, and velocity. Bank 0 grows from 71 to 72 complete instruments,
including the source sample, loop, predictor, tuning, and envelope. The shared
font converter explicitly permits valid one-step envelopes for this bank;
existing consumers retain their stricter default. All original instruments are
compared before and after relocation.

Modes 3 and 4 implement periodic and directional effects through the same
immutable records. Mode 3 refreshes complete source level sound `55` and emits
steam every eight native play frames, thirty units above the furniture with
spread nine. Mode 4 accepts exactly pulse one, reads the native contact owner,
and fires forward/backward according to the source's two accepted directions.
Both translate the source transition exclusions into native states 5/6/13/15.
The angle is the checked halfword at actor offset `124`; play-frame offset
`1EA0` is distinct from the graphics frame counter. No actor fields grow.

The ordinary planner installs full trigger/level sound resources, complete
steam/projectile effects, then the furniture profiles. Effect sound dependencies
are explicit even when no furniture in the selected batch directly owns that
sound; installing the shared projectile programme never enables an unselected
cannon. Installed dependencies are skipped, and complete artwork is reused.
The shared [effect specification](V3_ROOM_EFFECTS.md) defines bank relocation,
native profiles, and particle lifetimes. Unresolved preparation sound `FFFF`
cannot enter an installed callback.

The complete 239,920-byte wave-0 resource is stored externally in the import
reservation. Its signed-relative header preserves native streaming; the shared
wave archive and its other resources remain intact. Later archive relocation
rebinds this external header while checking the same physical sample resource.
Permanent audio capacity is checked against all current resources and expanded
only in the existing bounded allocation scheme.

Registry entry `1FAC` uses additive destination `3C40`, index 1808. The pinned
identity worksheet identifies no N64 counterpart; existing IDs do not change.
Post-office and island acquisition remain actual source requirements, not shop
substitutions. Complete callback/audio installation alone does not enable them.

### Displacement-driven rolling rigs

`contact-rolling-keyframe-rig` recognises the complete source lifecycle,
including its repeat initializer, movement helper, contact reader, constants,
resource relocations, skeleton, motion, and every joint model. It uses no item-ID
switch. Existing converted artwork and movement-sound bindings are reused.
The ordinary importer installs the missing rig and profile stages, then enables
eligible records through their actual acquisition and catalogue metadata.

Mode 5 stores the animation duration as its first floating-point parameter and
zero as its second parameter. Construction evaluates the source's initial frame
at speed 0.5 and then stops. Movement retains forward/reverse rolling, stationary
contact motion, and stopped behaviour for other directions or absent contact.
Two half-displacement evaluations per N64 update preserve source timing.

Native furniture states differ from the donor's enum. Checked dispatch and
transition code map push states to 9/11/14/1, pull states to 10/12/2, and
birth/bye/death/birth-wait exclusions to 5/6/13/15. These mappings also govern
the shared mower contact/fade, movement sounds, looping sounds, and trigger
sounds; a donor state number is never used directly as a native condition.

The native owner overwrites `last_position` before the item callback; the donor
does so afterward. Mode 5 therefore retains previous X/Z in its own unused
instance floats at `0204` and `0208`. Those fields are outside its joint/morph
vectors and are not saved. A straightforward read of native `last_position`
would incorrectly suppress all displacement-dependent rolling.

The shared room packet supports a checked 20-KiB layout at
`804C8000..804CCFFF`: 16 KiB of code followed by the unchanged 4-KiB table format
at `804CC000`. Sound/material tables move with that table; stable callback
vtables and the CRC-checked loader remain in the equipment module. The password
packet ends at this reservation's start, and the model pool starts at `80500000`.
The old rig, scrolling, and surface reservations remain untouched. Existing
8-KiB packets remain valid inputs; extension migrates complete records and
checks both cartridge capacity and neighbouring RAM reservations. No saved
layout or scene-actor allocation grows.

### Camera-facing scrolling rigs

`billboard-scroll-keyframe-rig` derives complete skeletons, motions, all joint
models, two-tile scroll parameters, and positional sound from checked source
callbacks. The category covers tiki torch, campfire, and bonfire without an
item-ID switch. Existing specialised camping imports retain their resources and
profiles; ordinary installation skips them instead of installing duplicate items.

The shared rig record uses mode 4. Its first parameter points to a 16-byte
immutable object suffix: flame model pointer, four dimension bytes, four signed
scroll-rate bytes, sound ID, state-suppression flag, joint index, and reserved byte.
The builder requires the complete source loop programme before enabling a profile.
Tiki torch retains unconditional sound refresh; the camping fires retain their
source transition-state exclusions mapped to native states 5/6/13/15.

Construction evaluates the repeat animation at speed 0.5; movement evaluates it
once before restoring that speed. Drawing retains every joint, including the
torch's extra opaque core. Checked existing camera-facing helpers replace only
joint 2's shape, preserving its transform, camera matrix, rotation, and scale.
Both graphics streams are bounded. Each draw owns two matrices and five scroll
commands in a 176-byte, 16-byte-aligned frame allocation, and flushes every used
joint matrix. Native drawing emits the hidden joint's matrix on the opaque stream.
Room and catalogue frames retain the donor's wrapped and quantised scroll rates.

### Complete hit-animation rigs

`switch-hit-keyframe-rig` checks complete donor create/move/draw implementations,
paired resource relocations, animation constants, and every sound operand.
Skeletons, all joint models, motions, textures, and the sound programme come from
those bindings. Item identities and model names do not select the adapter.

The shared 24-byte rig record uses mode 3. The retriggerable policy has zero
extra parameters; the idle-only policy has first word 1 and second word the
source speed 0.25 as a float. The endpoint-only policy has first word 2 and
source speed 0.5. Unknown combinations reject. Hit rigs support eight joints
plus root; only switch/rolling behaviours that reuse morph vectors for private
work retain a six-joint limit. Callbacks retain instance-local work vectors,
frame-parity matrices, bounded complete model DMA, and room/catalogue index
normalisation. Complete sound dependencies must be installed before a profile
can become usable.

For retriggerable and idle-only policies, construction retains the donor's stop
initializer and initial evaluation at speed 0.5, then stops the motion. The
retriggerable policy clears the hit pulse;
the idle-only policy preserves it, matching their complete source constructors.
The native initializer uses speed 1, so the callback explicitly supplies 0.5
before evaluating. Discovery
checks the donor initializer's full code, relocations, and constants.

Retriggerable movement preserves the donor's evaluation order, including its
second step while moving, restart on any nonzero hit pulse, and positioned sound. Donor excluded
states 13/14/15/12 map to native states 5/6/13/15; the room owner retains ownership
of clearing the pulse. Drawing uses the complete shared native rig drawer.
Sound and rig rows may share an identity: profile binding must retain the model
record while independently validating the complete audio record.

The idle-only variant accepts a press only at zero speed. Its first evaluation
occurs before assigning speed 0.25. While moving, it ignores further presses,
evaluates twice unless the first evaluation reports completion, and explicitly
sets speed to zero at that endpoint. Its complete callback shape, constants,
initializer, and source trigger are checked independently of item identity.
This preserves tiger bobblehead's full behaviour with its already converted
two-joint model; it is not treated as a retriggerable mask.

The endpoint-only variant starts moving at half speed and accepts presses only
when the native evaluator reports the endpoint. It retains the source's first
evaluation, second evaluation while moving, and restart at frame one. The bell
uses all seven joints and four model lists; no joint is removed to fit a smaller
runtime. The source constructor does not clear the interaction pulse.

Its complete conditional dependency uses [the shared room effects](V3_ROOM_EFFECTS.md):
positional sound `0174`, singleton system sound `817E`, and the camera-flash
controller when the actual wall is ringside seating. Both complete programs
and all instrument/sample dependencies enter the same audio batch. Wall 65 in
the donor maps to full native index 76, not native wall 65. The system sound
retains singleton suppression while effect requests still occur independently.
The optional wall is not forced into every bell selection.

Eight-byte sound rows retain their existing index and primary sound fields.
The final word is either zero or the checked wall byte, effect byte, and full
system-sound halfword. Unknown conditions and incomplete installed effect/audio
bindings reject before enabling the profile. Native actor allocation, matrix
storage, and saved formats do not grow.

The shared sound records admit checked groups 0, 1, and 4. The audio importer
retains complete source programmes, instruments, samples, and trigger priorities,
using separate vacant slots in each group's table. It validates the actual room
packet layout before updating sound records, including the extended code layout.
Source `1FC4` has no native correspondence in the pinned worksheet or approved
translation mappings. Its append-only destination is `3C3C`, runtime index 1807;
the original furniture, display aliases, and existing imports keep their IDs.

### Shared password acquisition

`convert --assets-only --representation rewards --category password` prepares
the complete donor code tables and freestanding MIPS codec in one batch. There
are no per-item decoder definitions or rewritten shop-stock categories. All six
code types use the same 28-character transform. Source eligibility, identity,
selected destination resolution, keyboard/dialogue, and actual delivery remain
separate required integration steps, described in [V3 passwords](V3_PASSWORDS.md).
Prepared codec success does not activate any import or update a deployment.

`--category password-policy` uses the same rewards representation and explicit
current build lock. It prepares complete donor eligibility, Nook result rules,
and current import destinations with their live selection-field bindings. The
source's HomePage furniture is Famicom-only; Mario furniture instead uses birth
category 34 without ordinary stock membership. An empty `ftr_listMario` must
not cause this source category to be lost. The runtime refresh's
`--password-runtime <prepared-policy-dir>` links these packets and callbacks,
including native RNG and live selection access, in a checked lazy-loaded module.
Original-item correspondence, display aliases, frontend, and actual
handover remain required. An unavailable destination never becomes a substitute
item or bypasses the active profile.

### Complete donor scoring themes

`--refresh-runtime --furniture-scoring` extends the current checked HRA owner
through the shared installer. All 60 donor series fit 63 allocated rows: the
three inert padding entries preserve the native three-plus-four and one-plus-two
unrolled loops. Sentinel 63 stays excluded. Every counted loop, original table
reference, and the imported missing-item helper receives the matching bound.
The metadata end pointer can equal the old series-table start; reference identity,
not address alone, determines which pointer moves.

Original 55 definitions and all existing furniture metadata remain intact.
The five additional definitions retain complete source types, official names,
and stable paired surface mappings. Harvest is a base series, not a theme;
Mario is a theme. The native scheduler and complete overlay relocation receive
the increased image size, bounded by 32 KiB plus the existing relocation limit.
The separate English score-letter creator appends missing source names while
preserving every previous lookup key and template selector. The single text
provenance catalogue records the exact donor name fields.

This category changes no saved fields, selection bits, or active imports.
Acquisition and base-point support remain independent eligibility requirements.
The ordinary installer checks a row's series against installed
storage before accessing it. Neither web-patcher deployment is updated.

### Complete donor base-point categories

The same `--furniture-scoring` refresh installs shared base-point support after
the theme storage. `donor_categories` derives stable scoring buckets from the
complete checked 38-entry donor table. Existing native categories 0–22 retain
their identities and points, including native lottery 2,951 rather than donor
1,029. Donor categories 23–37 reuse an equal native point value or append one
missing value in source order. Four new buckets contain 1,983, 1,300, 1,177, and
1,400. This mapping changes scoring metadata only, never the acquisition list.

Twenty-seven counters fit the native five-bit birth field and three-plus-four
unrolled loops. Both complete counter/product arrays grow four words, moving the
count array `AC -> BC` and frame end `108 -> 128`. The complete native stack and
point-reference inventories are checked, including the surface-scoring tail's
caller arguments. Stack use grows 32 bytes to 296. The complete point table
adds 112 aligned owner bytes, and both relocation and scheduler sizes follow it.
Original metadata, themes, letter names, and all full-index surface values remain.

The ordinary metadata generator uses the shared source map. The installer checks
the full current owner, complete weight table, installed frame and instructions,
all three birth-field readers, selected bucket, and complete converted metadata.
A prepared row cannot supply a missing counter, arbitrary point substitute, or
unavailable theme. Shared surface-table rebuilding reads the complete active
counter layout while retaining all original values. No item is enabled merely
because its score can be represented.

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

The registry reserves reviewed ordinary legacy identities in `3C10..3C94`,
after the balloon displays at `3C00..3C0C`. Existing native IDs, the entire
garment display range, and every previous import reservation remain intact.
Reservations are literal and append-only, not assigned by selection order.
The mappings identify reviewed additive furniture; acquisition,
graphics, and behaviour still come from source records, not that registry.
Other legacy entries remain in review until identity and representation are
established. Unresolved worksheet cells alone do not justify a new identity.
Registry version eleven includes four paintings and three gifts. The checked
worksheet has no N64 ID/name/model/texture correspondence for these seven, and
the original-ROM/donor dependency check finds no approved native translation or
shared-identity evidence. Their append-only destinations do not change any
previous mapping. The four paintings retain their actual event/ordinary stock;
the gifts have complete inactive profiles while acquisition remains pending.

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

Fixed and indexed constant-material sequences specialise checked source draw
callbacks into complete model lists. Both texture and palette segment bindings
resolve to verified full resources; generated native commands use the object's
own addresses, not unresolved donor segments. Indexed forms retain their full
selector tables, range, fallback, and selected row. Whole-function checks and
paired relocations identify the category without item-ID or name switches.

The `constant-material-model-sequence` preparation category includes the console
models. Their three full lists and ordinary linked draw sequence share one
converter. A nonempty lifecycle produces
`constant-model-sequence-pending-lifecycle`: artwork can be prepared in bulk, but
metadata and native profile writing both reject it until gameplay is implemented.
An explicit DMA callback is accepted only when its entire source is the empty
return instruction; real DMA behaviour remains unsupported, never discarded.
The drawing-only Super Tortimer model follows its actual source semantics.
Names and unused-game status alone do not select its behaviour.

The [console-game converter](V3_CONSOLE_GAMES.md) retains complete game payloads,
ordered save operations, source tags, and checked fixed/indexed launch arguments
as one dependency batch. Prepared console artwork includes those launch receipts;
missing native gameplay still prevents installation. The absent game-twenty
payload is distinct from the twelve supplied additions. Existing native mapper
callbacks do not by themselves establish complete launch or persistence support.
Checked native iNES/QD loading/storage permits ordinary category staging of
all twelve supplied additional console profiles. The shared room dispatcher uses actual source
game mappings and the native interaction clip; constant draw lists remain the
same prepared resources. All acquisition gates still apply. The repeat planner
skips installed profiles rather than repeatedly rebuilding those records.
Planning verifies the complete installed disk packet, both BIOS copies, boot
data, common save-call bindings, and native owner/relocation hashes. Profile
staging publishes the QD readiness bit through the existing room table and
rebuilds the startup checksum, without recompiling callback, engine, or art.
An installed engine is distinct from an installed room binding; both are
required before profile activation. Missing donor payloads remain explicitly
unavailable, not pending emulator implementation. The checked arena allocator
is installed; native title execution, rendering, Reset retention, and cleanup
pass for the disk game and a cartridge game. Ordinary room entry/world return,
user-controlled gameplay, and hardware remain unverified. See the
[room checkpoint](../docs/checkpoints/V3_CONSOLE_ROOM.md).
Console conversion also prepares the common bounded save executor. It preserves
all four players' separate progress and the complete score/reset/battery/disk
semantics. Preparation and donor comparisons do not enable games or install
FlashRAM storage; readiness still requires native integration. The same command
prepares the [bounded compressed bank envelope](V3_CONSOLE_STORAGE.md), retaining
all four records and both town-save banks with explicit capacity rejection.

The ordinary `import` dependency planner includes scrolling resources, complete
positioned-loop/switch-fade audio, and draw-only or audio-backed profiles. Audio
is installed before the scrolling lifecycle table; profiles follow full resource
and lifecycle verification. Already installed dependencies are skipped and all
stages reuse prepared artwork. A completed inactive profile with an unfinished
acquisition route does not schedule another conversion.

The parameterised three-model scrolling shape preserves opaque body, translucent
glass, and translucent bubbles in source order. Its generator emits both tile
origins even though the bubble model samples just the first tile. Descriptors
keep the two complete generator records and separately declare the sampled tile
count; model parsing verifies every actual texture load and dynamic call. The
glass's additive environment alpha and the bubbles' primitive alpha are preserved
as complete single-texture combiner expressions. The existing generic scroll
renderer handles this shape without extra native code or allocation.

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
The mower's contact/floor-driven alpha state and separate room-owner movement
sounds are installed; ordinary profile/acquisition selection uses both bindings.

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
The shared scrolling installer binds this category for all matching source
records, including newly added drawing records in the same batch. It installs
the contact code and records within the existing reservation. Ordinary profile
binding requires the independently verified room-owner movement sounds.

Floor binding compares every decoded pixel of the complete converted donor
surface against the native room-floor bank. Zero matches require an additive
surface import; multiple matches require identity resolution. An equal numeric
index is not evidence. GameCube backyard lawn at 26 has no native artwork match:
native 26 is old plank floor, independently recorded in the translation catalogue.
Daisy meadow at 48 matches all 16,384 pixels. Backyard lawn binds to registered
additive identity 74 after the surface item/artwork/house/catalogue/save/audio/
stock and optional-selection stages are present. The binding rechecks the full
converted texture, source record, destination registry, and actual enabled item
metadata. These are alternative floor predicates, not mandatory checkbox
dependencies: a mower on native meadow does not require selecting backyard lawn.
No existing native floor is replaced. Preparation accepts the checked build
report so its dependency result reflects installed additive floors.

The complete alpha callback remains independent from room movement sounds.
Installed alpha callbacks do not by themselves enable a parent profile or web option.
Future batches rebind source functions and complete installed floor resources;
a readiness flag or matching numeric index cannot stand in for those checks.

Furniture switch-click validation follows the installed group-zero movement
table. A surface-audio expansion preserves all original 80 entries while adding
new sounds; the verifier checks the complete original entries and each click's
program, instruments, and priority instead of assuming the table remains at its
original address.

#### Shared room movement sounds

`convert --assets-only --representation audio --category room-movement`
prepares the complete source room-owner category, using the current explicit
build lock. Both dispatch cases, source states/directions, complete helper
functions, floor identities, and sound words come from `aMR_SetMoveSE`.
The regular `--furniture-audio-art` installer installs the prepared category;
ordinary profile and bulk-import steps remain responsible for activating items.

The native complete movement function at `8093EA60..8093EACF` keeps its room
predicate and floor calculation. Its one call at `8093EAB8` targets a fixed
bridge at `804B1E50`, preserving the native position argument and fallback floor.
The bridge follows the current lazy-loader function when later shared batches
rebuild the bootstrap. No native overlay relocation changes. Added code and
records fit the existing room reservations: 3,984/4,096 code bytes and a
1,510/1,536-byte bootstrap. The movement table at `804BBF20` has a 16-byte
magic/count/stride/reserved header and up to eight 12-byte records containing
native index, mode, two sounds, and two floors. Records are immutable and do not
change actor or saved state.

Mode one preserves seven push/pull states and chooses rolling for left/right
contact, dragging otherwise; absent contact is silent. Mode two preserves four
push states and back contact on either bound grass floor, remaining silent for
other contact/state combinations on grass. Other floors retain the ordinary
native floor sound. Original furniture always retains that native fallback.

Complete trigger programs preserve transposition, continuous-note mode, and
all timed pitch sweeps. The shared registrar can add a dispatch group while
preserving previous groups and every old slot/priority. Group zero retains all
81 existing movement entries and grows to 128 slots. Sound mapping is source
`007D/007E/0177` to native `0069/006A/016F`; these are generated mappings, not
item-specific code constants. Two real instruments and their samples are added,
growing the font by 288 bytes and sequence by 320 bytes. Existing audio capacity
is sufficient, with 288 conservative bytes spare; no heap increase is needed.

The mower uses ordinary event-item stock and catalogue reordering. Its optional
selection does not require backyard lawn: native meadow also satisfies the
source condition. Save format 4 is unchanged; selected imports still require
their profile bits in future builds. Stone-coin movement audio does not waive
that item's separate unfinished model/material behaviour.

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
candle, Mouth of Truth, and chowder together. Descriptors distinguish room/preview
counters, division/modulo timing, switch-dependent stopping, and an actor-state
selector. Source lifecycle receipts remain attached. The artwork alone
does not implement sounds, surprise/rumble, player colour changes, or switch
coordination. Ordinary metadata and the native profile writer require a complete
checked lifecycle, not a forged runtime annotation.
Use `convert --assets-only --category material-frame-assets` with the
current explicit build lock; reuse the resulting complete objects through
`--refresh-runtime --material-frames-art <prepared-directory>`.

The shared native material renderer uses a checked 40-byte record containing
stable destination index, complete object size, selector mode, segment, counts,
division, complete frame size, four model offsets, eight frame offsets, native
private-state offset, material kind, and lifecycle selector. All unused fields
are zero. Eleven records fit at table offset `E20`: `804B9E20` in the original
8-KiB packet, or `804CCE20` in the extended 20-KiB packet. Its header is `AFM1`,
count, stride, and zero. Code uses the packet's existing code reservation;
no new allocation or object header is needed. The stable vtable
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
Material objects with complete installed switch-trigger moves or the checked
invalid-index initializer use the shared profile staging path. Acquisition stays
independent. Mouth of Truth's reviewed legacy source `1FD8` has the append-only
destination `3C30`, runtime index 1804; the native worksheet correspondence and
approved translation map contain no existing native identity for that source.

The invalid-index initializer recognises complete source create/move/destroy
callbacks: signed halfword `-1` at donor `82A`, followed by inert updates and
destruction. Relocations, lengths, digests, and actual donor instructions must
all match. Lifecycle byte 1 maps that work field to private native `1A4`; the
renderer remains timed mode 0. It does not claim a general linear correspondence
between donor and native actor offsets. Lifecycle 0 retains its previous no-op
construction. Unknown lifecycle/mode/work combinations reject.

Lifecycle 4 supplies periodic steam with complete level sound, timed texture
frames, and inert source construction/destruction. Its source callback,
relocations, height constant, and selector are checked together. The two textures
alternate every six donor frames; all three models remain in source submission
order, including alpha-bearing lists submitted in the source's opaque arena.
Native movement emits steam every four play frames at height 15 and spread 10,
while refreshing the full source level sound `54`. Transition exclusions match
the native state map. The shared parameterised steam emitter also serves direct
models, without adding private actor fields or a separate particle pool.
The record's state halfword binds the sound ID for this lifecycle, not an actor
offset. The ordinary importer requires complete material, sound, and particle
dependencies before installing its profile and actual winter-camper acquisition.

The existing room constructor dispatches non-rig records to the material
constructor. The material vtable reuses the existing CRC-checked constructor
bootstrap; no extra bootstrap entry, allocation, or saved field is added.
Construction changes only the mapped halfword, including catalogue aliases,
while all model/frame resources remain immutable. Source frame timing and light
scalar remain intact. `import --category material-frame-assets` discovers missing
renderer, sound, and complete profile stages automatically, skips installed
dependencies, and then uses ordinary eligibility. This enables festive candle
through its donor train/Christmas stock and catalogue route, while missing
Mario acquisition and the other material behaviours remain explicit.

Completed profiles and ordinary imports are removed from deferred-resource
reports. An old pending receipt cannot override a verified installed lifecycle.

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
single-layer note sequences, including repeated notes, short/wide timed rests,
and optional custom envelopes set before or between timed events. Durations,
velocities, pitches, tuning, and envelope data remain exact;
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
reward. Selected roof colours use the shared lifecycle described below;
additional effects require their complete adapters, not static substitutions.
Clocked rigs have complete installed assets
and a shared native lifecycle; ordinary profiles/acquisition remain separate
requirements.

Other dynamic texture/palette pointers, animation rigs, custom callbacks, unsupported
contact/interaction flags, other action sounds or acquisition routes, oversized
or different-format artwork, and framing outside the checked source table remain explicit review
categories. Unsupported does not mean unused or unimportant. A successfully
converted object is not automatically evidence of complete gameplay.

### Selected roof palettes

`selected-palette-fade-assets` extends the existing palette-fade converter for
indexed endpoint tables. Category recognition binds complete create/move/draw/
destroy functions, paired table/model references, calls, and full selector/morph
helpers. Both house models share the same lifecycle and twelve-entry endpoint
tables; their complete three-list drawing order comes from their actual callbacks.
No item ID or model-name suffix selects the implementation.

The converter retains both complete 384-byte tables as twenty-four aligned
sixteen-colour native palettes per object. Every roof colour and transparency
entry survives; changed on/off entries must both be opaque. Both complete models
use the existing geometry/texture/material emitter and one bulk compiler run.

The prepared object has a 32-byte `AFP2` header: magic, 16-bit full object length,
16-bit model count, two 32-bit offsets for the on/off palette tables, three
segmented model pointers in source drawing order, and the 32-bit palette count.
This is distinct from `AFP1`; existing fixed-endpoint runtime code must not accept
it as an ordinary pair. The metadata and profile builders reject it until the
native roof selection and full lifecycle are bound.

The donor selector uses the current room's home roof colour during gameplay,
the current player's assigned home in previews, and colour zero where neither
applies. Native field IDs, player/house arrangement, stored roof indices, and
their correspondence to the twelve donor palettes are bound by
`tools/v3_furniture_roofs.py`. Complete compiled native field, arrangement,
home-initialization/upgrade/current-player, and exterior constructor blocks are
checked before installation. Common data is at `80126EA0`, player number at
offset `10003`, homes at `3588` with stride `B48`, and current roof colour at home
offset `24`. Gameplay control type is one; other control types use the preview
player's arranged home. Invalid colour or player values safely select zero.
There is no GameCube island cottage among the native N64 scene identities.

The native exterior pointer tables start at offsets `8` and `174` in resource
`D5D000`; player-home palettes start at index 25. Every summer and winter
palette agrees with the official donor apart from the transparent first entry.
Summer roof shades 10..12 match model shades 11..13; winter snow covers the first
two but retains the third. This verifies all twelve numerical identities,
including the differently ordered C/D resource symbols.

The ordinary importer installs these as shared room mode seven with no skeleton
or animation pointers. `room_palettes.c` reuses `tent_model.c` under a separate
selected-palette build define inside the checked room packet, leaving fixed
palette code and its reservation unchanged. The actor's unused non-rig work
holds the fade at `1A4` and selected roof at `1A8`. Construction initializes both;
movement re-reads the current home colour and approaches the switch by the
source float `0.1`. Drawing checks the full `AFP2` header/table/model bounds and
submits all three lists in source order with a frame-owned palette. Both native
eight-byte tail alignments are accepted; the allocation itself is aligned to 32.
No heap or
saved allocation is added, so teardown has nothing to free.

The runtime catalogue binds complete resources, source helpers, native selectors,
callbacks, profiles, names, and optional-record guards. Actual HRA reward
delivery remains a separate acquisition requirement; installed profiles stay
inactive until that route exists. Resource preparation alone still rejects at
the metadata/profile boundary without the verified installed lifecycle.

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
Donor HRA birth categories use the shared checked point-equivalence map above;
categories 33 and 37 retain their existing 412-point mapping to category 3.
This is scoring metadata only: winter/summer acquisition remains independent
in byte 27. Original weights remain unchanged; complete counter/stack expansion
is an explicit shared runtime dependency, never a per-item adjustment.

Canonical furniture identity version 2 is independent of conversion order,
checkbox selection, and resource placement:

```text
saved item ID = canonical donor 3xxx ID
runtime index = 1024 + (saved item ID - 0x3000) / 4
```

Existing native items, old explicit reservations, and display aliases remain.
The checked build manifest records each new object's VROM; it is not a saved
identity. Object storage is appended at 16-byte alignment with complete physical
and virtual overlap checks, the installed model-bank limit, ROM boundary checks,
CRC updates, and full patch reconstruction. No new DMA-directory entry is needed.
The checked [capacity extension](V3_FURNITURE_BANKS.md) provides 12,288-byte room
and catalogue model buffers. Without its verified native installation, the
pipeline retains the 9,216-byte limit; it never drops geometry to make an object fit.

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

The runtime accepts the legacy `804B8000..804B9FFF` packet and the extended
`804C8000..804CCFFF` packet described above. Both have a 4-KiB table with a header,
up to 128 twenty-four-byte descriptors, sound/material records, and padding.
The larger code reservation preserves the gold-tree, scrolling, surface, and
password owners, without growing scene actors or model banks.

Each descriptor contains the canonical index, complete object length, skeleton
and animation pointers, joint/visible counts, category, zero reserved byte, and
two category parameters. Switch rigs require zero parameters. Clocks supply
distinct hour/minute joint indices; storage supplies finite start/end frames
within the complete source motion. Native work supports eight joints plus root;
switch and rolling callbacks reserve the final two morph vectors as private work
and therefore support at most six joints. Complete-object and pointer bounds
remain mandatory. Reusing an identical prepared asset from a different cache
does not change its source identity: only the cache-location receipt is excluded
from profile equality, while all model bytes, hashes, and source bindings remain checked.

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

## Shared room-effect dependencies

The [room-effect adapter](V3_ROOM_EFFECTS.md) prepares complete camera flashes
through the native effect controller, including both lifecycles, donor drawing
commands, lighting, and additive effect identities. The controller extension
retains the current campsite-lamp hooks and every original effect. Endpoint-hit
profiles require the installed controller, complete sprite, both sounds, and
actual full-index wall condition. Prepared resources alone cannot enable an item.

## Switched texture frames and positioned sound

The complete switched-screen draw form extends `material-frame-assets`; there
is no item-specific converter or installer. It preserves both opaque models in
source order, every on-frame table entry (including duplicates), and the separate
off image. Material mode 3 uses five frame offsets: four timed on frames followed
by the off frame. The full source draw function, pointer relocations, frame
resources, matrix helper, and selector are checked before conversion.

The source control type chooses the gameplay or preview counter. Native counters
advance at half the donor rate, so the renderer doubles the selected counter,
performs signed division by six, and selects the low two quotient bits. Counter
wrapping retains the source result without signed C overflow. The off image is
selected in both rooms and previews; it is not a frozen on-frame. Native actor
control type at offset two supplies the selector, independently of a room pointer.

Lifecycle 5 stores the complete bound level-sound identity in `state_offset`.
It refreshes the positioned loop while switched on, excluding native transition
states 5/6/13/15. Both source switch clicks remain: any nonzero change pulse plays
the appropriate click, including during those transition states. No private actor
work, allocation, or new saved fields are required. The checked native placement
adapter honours the donor's start-disabled flag without changing reload state.
The ordinary importer plans complete artwork, loop/click dependencies, and the
shared profile together. Actual missing reward acquisition remains explicit.

The sound converter accepts timed lead-in rests before a layer's instrument.
The initial rests, note timing, envelope, loop target, and full sample are retained.
Channel/layer/envelope/restart pointers and instrument bindings alone relocate.
Channels with internal envelopes preserve source address parity so their absolute
envelope addresses remain halfword aligned; channels without internal envelopes
retain the established even-address layout. Unknown commands, zero-time lead-ins,
escaping pointers, partial envelopes, and unexplained trailing data reject.

## Timed material reactions and N64 vibration

`convert --assets-only --representation lifecycle --category timed-surprise-material`
prepares complete reaction dependencies through the existing pipeline. Discovery
checks the complete source callbacks, relocations, player helpers, surprise
consumer, duration constant, and material selector, without an item-ID switch.
Ordinary material import plans the implemented lifecycle automatically. It reuses
complete prepared artwork, publishes the shared reaction code and wave bank,
installs the controller hook, and enables eligible source acquisition records.
Lifecycle 2 requires material mode 2 and private face offset `1A4`; incomplete
source functions or engine bindings reject before profile installation.
The existing material constructor and movement bootstrap dispatch this lifecycle,
including when no sound rows are installed. No per-item installer is used.

The two source signed work fields are distinct: countdown at `82A` maps to
native `1A6`, while face at `82C` maps to native `1A4`. Construction clears both.
Two ordered source steps per native update preserve the 50-frame countdown,
vibration at 20, and reset below zero. Only the first step consumes the native
interaction pulse. Catalogue previews do not request player reactions. The
source room request keeps retrying until the player reaches shock; native
priority 14 remains authoritative. The source's 20 update-duration units become
10 native units at 30 Hz. The native room's smaller allocation never receives
the donor's out-of-bounds room work offsets.

The shared vibration bank retains all sixteen source waveforms and their exact
lengths. Its 272-byte representation uses relative offsets and no donor pointers.
The complete source engine and relocation map are pinned. Four concurrent
requests retain attack/sustain/release phases, floating-point accumulation,
distance attenuation, removal-before-selection, and first-wins priority ties.
The request's `100` operand means intensity percentage, not 100 frames.
Controller retraces evaluate the envelopes at 60 Hz, independently of room
updates. Both donor stop commands map to motor off: the N64 Rumble Pak has no
separate active brake.

The transport calls native `osMotorInit` at `80031574` and `__osMotorAccess` at
`80031300`, using a private 104-byte `OSPfs`. It never shares a Controller Pak
save-system instance. Only a positively recognised Rumble Pak receives motor
commands. Disconnect/replacement invalidates the device; transient failed stops
remain pending and retry. A positively identified other accessory does not keep
receiving idle probes. The item still reacts without a Rumble Pak attached.

The safe controller call site is `800D7150`: input and status reads are complete,
and padmgr owns its serial queue. The earlier rumble callback runs during an
outstanding SI read and must not perform motor transfers. Short interrupt-masked
sections protect shared envelope updates; no interrupt mask is held while SI
transfers block. A six-retrace heartbeat stops suspended/abandoned requests, and
the existing pre-NMI flag stops remaining vibration. These are platform safety
adaptations, not a new saved GameCube vibration-setting field.

The mutable reservation is `804CD000..804CD3FF`, immediately after the
immutable shared packet and below the model pool. Packet publication records
and checks that reservation against other reported owners. Its magic is cleared
before publishing the ready word. The main-RAM bridge retains the original Pak connection check,
then tests successful V3 startup and the exact room-packet CRC before calling
Expansion Pak code. It occupies only checked tails of the fully replaced size
readers at `800B11B8..800B11F7` and `800B1324..800B1363`; their original entries
remain. The native part-copy tail at `800B1DF0` is still active and is not spare.
Every shared-packet refresh receives the current main-code owner and recompiles
the bridge against the actual packet CRC and linked retrace address. Validation
restores only its two checked windows and four-byte call in a temporary copy,
then checks the complete original native functions and reservation ownership.
Intervening live code and the replaced readers' entry jumps stay untouched.

Focused checks compare the evaluator against the donor C functions using the
actual disc's wave data. They cover all sixteen waves, omitted phases,
overlapping requests, malformed input, the full timed reaction, delayed shock
acceptance, and mocked detection/start/stop/failure/disconnection. The shared
native batch probe checks installed hooks, cold-load guards, constructors,
complete model DMA, native shock-call arguments, countdown and envelope timing,
saved-state preservation, and bounds. Its disconnected accessory and captured
player callback do not establish actual SI motor transfers, ordinary player
animation, or hardware rumble.

## Exclusive player-colour material loops

`convert --assets-only --representation audio --category exclusive-player-colour-loop`
uses the existing shared sound importer. Discovery checks complete create/move
callbacks, the switched four-palette selector, positioned sound, player-colour
request/update/draw consumers, same-furniture switch traversal, fog helper,
and read-only timing/colour constants. No item-ID installer is added. Selected
audio preparation scans only requested source records.

The complete source lifecycle starts switched off. Non-transition updates
refresh the positioned loop and request player colour while switched on. An
on-transition switches every used instance of the source identity off, then
restores the initiating instance to on. Lifecycle 3 uses the native transition
mapping and the room owner's actual used-instance work, resolved through its
loaded overlay base. The checked count is at most 48 with a `740`-byte stride.
The shared frame table stores the immutable level-sound ID in `state_offset`
for this lifecycle; it is not an actor work offset. Complete audio and source
consumer bindings are required before profile installation.

The donor player effect consumes its request every update. Continuous requests
advance a float timer by one donor tick, wrapping at the exact binary 79.68
constant; activation starts at zero. Drawing divides by the binary 9.96
constant, alternates disabled fog with colour phases, and restores ordinary
scene fog immediately after the player skeleton, before drawing held items.
The donor binary indexes three rows at stride three including column three.
Its actual four RGB results are `(255,100,255)`, `(255,255,255)`, `(100,100,100)`,
and `(100,255,255)`. Preserve those accesses through bounded flat indexing;
the decompiler's `[4][3]` expression would otherwise invoke undefined behaviour.

Sustained single-layer loops support an optional custom-envelope command.
Without that command, the complete instrument's own envelope and decay remain
authoritative. Mode, note, duration, velocity, and restart target are retained;
channel/layer pointers and instrument selectors alone relocate. Unknown commands,
zero-duration events, escaping pointers, and unaccounted tails reject.
Both envelope forms use the same source/native instrument and sample comparison.

Timed retrigger loops additionally preserve multiple note/rest events and
envelope changes without forcing sustained-note mode. Every channel/layer,
envelope, and restart pointer relocates; notes, durations, velocities, decay,
envelope data, and padding remain unchanged. Restart targets must be command
boundaries with at least one timed event in the repeating section. An
envelope-only zero-time cycle rejects. Distinct envelopes are checked in full,
including their alignment and complete tail coverage. Source level `54` uses
five timed notes and two envelopes; its full instrument and sample pass through
the same font/archive importer as sustained loops.

Native player-colour and exclusive-switch callbacks are installed. The player
owner changes exactly two calls: the complete original pre-action update is
preserved, and the six-argument skeleton call is wrapped. The update wrapper
resolves the actual relocated player through `Player_actor_move_func` at
`80143908`; actor field `164` is a resident trampoline, not that relocated entry.
The initializer, trampoline, original update/draw bodies, room list/count table,
and native fog functions have complete checked source-image bindings. The
replaced owner-local update call loses its one `R_MIPS_26` relocation; the new
fixed bridge calls are not owner-relocated.

The immutable guarded bridges occupy `804B1E60..804B1F3F`; packet publication
rebinds their CRC and update/draw targets. Cold bridges call the native routines
without touching unloaded room code or transient state. Colour state owns
`804CD400..804CD4FF`, outside the immutable packet and independent vibration
state. Bootstrap clears its magic before publishing the packet. Actor sizes,
heap allocation, saved fields, and save format 4 do not change.

Two source update ticks run per native frame. Drawing inserts source fog before
the skeleton and restores scene fog afterward, retaining all six arguments and
graphics-tail allocations. If callbacks consume the remaining restoration
space, the initial tint commands are replaced with ordinary scene fog instead;
no out-of-bounds commands or persistent tint are emitted. Sound and animation
resources are unchanged. This material remains unavailable until its actual
Mario reward route is installed.

## Fixed rigs with joint callbacks

The `joint-callback-rig-assets` category discovers complete fixed rotational
rigs from the verified constructor and shared skeleton-draw shape. Paired
skeleton/animation references, initializer calls, constants, complete motion
arrays, every joint model, and both joint callbacks are retained. Constructor
and draw shapes, rather than item identities, select the converter. The category
prepares resources only; metadata and native profile writers reject it until
its complete gameplay implementation exists.

The callback records distinguish parent-relative needle rotation, accumulated
joint rotation, translucent redraws with primitive LOD scaling, and translucent
redraws with primitive alpha and scrolling. Hidden joints still retain their
entire original model; explicit redraw references must match the corresponding
skeleton joint. Complete create/move/draw receipts remain pending, including
switch behaviour, parent transforms, sound, and clock-derived state. No callback
is replaced with a static model or silently discarded.

The shared material converter supports GX I8 as complete eight-by-four tiles,
reordered into native linear I8 without changing sample values or allocation.
The donor executable's actual format table verifies I/8 maps to GX I8. Native
commands use an 8-bit intensity tile, the correct row stride, and no palette.
Complete primitive-alpha and primitive-LOD combiner expressions remain intact.

Texture memory layout and a callback's scrolling window are separate. One
reviewed callback samples a full 16×32 I4 image through an 8×32 scrolling window,
while producing two scroll-tile records. The complete image and its 16-pixel
source pitch remain; the runtime dependency retains both 8-pixel window records,
rates, and the exact generator. Conversion does not resize the texture or
replace the donor's window with its image width.

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
