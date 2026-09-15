# V3 camping actors

## Scope and current boundary

Convert and port the complete GAFE01-r0 campfire, bonfire, and tent model.
These complete the assets for the ten-entry `ftr_listTent` family alongside
the seven static objects in [Camping items](V3_CAMPING_ITEMS.md).
They are additive imports, not substitutions for native furniture.

ABI 70 installs all three complete actors: the tent model with its light
callbacks, and both fires with full rigs, billboard flames, two-tile scrolling,
and actual positional sound refresh. English metadata, catalogue/scoring,
selected dependencies, complete-object DMA, and the bonfire's four-cell readers
are installed. Individual selections are available in the offline composer.
Summer-camper acquisition and ordinary gameplay/persistence remain required.
Source on the V3 development branch is permitted; neither served web patcher
changes before user testing and explicit approval.

## Identities and complete assets

| Item | English name | Fixed index | Price | Footprint | Native bytes |
| --- | --- | ---: | ---: | --- | ---: |
| `335C` | campfire | 1239 | 1,360 | 1×1 | 8,000 |
| `3360` | bonfire | 1240 | 2,240 | 2×2 | 6,032 |
| `336C` | tent model | 1243 | 2,550 | 1×1 | 4,288 |

The tent model is decorative furniture with a switchable light, not an enterable
campground tent. The bonfire has shape **5 and collision type 5**; the item size
query returns **2**. These numbers serve different purposes.

`tools/v3_camping_actor_art.py` verifies the supplied decoded REL and symbols,
actual profile and vtable relocations, both furniture-quality tables, all
23 acquisition lists, names, prices, catalogue framing, HRA/feng metadata, and
the pinned identity worksheet. Each item appears once, only in `ftr_listTent`.
The worksheet has no native ID, English/native name match, model, or texture
counterpart for these identities. No dummy furniture or ordinary-stock route
is used to stand in for the missing actors.

The objects retain all 376 source vertices, 203 triangles, 12,032 texture texels,
and 112 palette entries. Source position, UV, and vertex colour/normal bytes
stay intact; GX-only vertex flags are normalised. All 18,320 converted bytes fit
the existing 9,216-byte per-object bank without reducing meshes or textures.

Campfire includes the actual fish artwork and all three palettes. Several local
donor symbol names also occur in unrelated objects, so those resources require
their exact section addresses rather than the first matching name.

## Display-list conversion

Shared converter version 7 adds explicit, mutually exclusive tent, fire-body,
and small/large flame modes. Unknown states, pointers, wrap modes, or dynamic
dependencies fail conversion. Existing static families retain their defaults.

The tent keeps all four model parts in donor order: green, body, detail, light.
All four use the opaque head, regardless of the `T` in some source symbol names.
Its window-light material loads a palette through `08000000`, which is an
intentional runtime segment, not an absent REL relocation. Other palette and
texture addresses are rewritten into segment 6 as usual. The native converter
retains the exact wrapped and mirrored/clamped materials.

Both flame lists retain two independent I4 textures. Native multi-block loads
reserve TMEM word 0 for tile 0 and word 128 for tile 1. Neither list needs a TLUT.
The complete donor combiner, primitive/environment colours, render mode, and
unlit, unculled geometry remain. A checked call to `09000000` follows both
texture loads; the runtime must bind the scroll display list before rendering.

| Actor | Tile 0 dimensions / shifts | Tile 1 dimensions / shifts | Scroll velocity |
| --- | --- | --- | --- |
| campfire | 32×64 / `(0,0)` | 32×32 / `(0,0)` | `(0,−6)` and `(0,0)` |
| bonfire | 32×64 / `(1,1)` | 64×32 / `(2,0)` | `(0,−3)` and `(−2,0)` |

Velocities are the donor callback arguments per frame. Their native texture
coordinate representation must be checked when connecting the scroll helper.
The bonfire body also retains the explicit extended tile extent of its 16×16
clamped-S/wrapped-T material. It is not an enlarged or cropped source image.

## Fire callback contract

Both fire rigs have three joints and two displayed models, a three-byte zero
flag array, 12 constant components, no keyframe tracks, and a 101-frame header.
Null track-count/key pointers remain null. Five real pointers connect the native
flags, constants, body/flame lists, joints, and skeleton. The middle joint is
800 units above the campfire root or 2,700 above the bonfire root. The bonfire's
last-joint draw flag remains 1; the campfire's remains 0.

The constructor uses the repeat initializer and speed 0.5. The move callback
evaluates the rig and retains that speed. The before-draw callback suppresses
the ordinary joint-2 shape draw. The after-draw callback obtains that joint's
position, applies the current camera billboard matrix, rotates 90 degrees about
Y, applies the actor's scale times 0.01, and draws the flame on the translucent
head. A static flame or ordinary non-billboard joint is not equivalent.

The donor selects the gameplay frame counter or generic game counter using
`ctr_type`. Both opaque and translucent heads receive the current base matrix;
the translucent head receives segment 9. A failed scroll-list allocation must
not lead to a draw with an unbound segment.

The donor loop-sound numbers are `005D` (campfire) and `005C` (bonfire). The
installed audio adapter explicitly supplies those two native IDs with their
complete mapped resources; numerical equality alone is not the mapping. Furniture
transition-state exclusions use different native and donor enum values.

### Native implementation bindings

Native actor scale is at `714/718/71C`, the rig at `134`, joints/morph at
`1A4/1DA`, and the two ten-matrix banks at `210`. Native gameplay frame and
billboard matrix are at `1EA0` and `1E5C`; generic frame is at `A0`.
The GC `ctr_type` at offset 2 is not a native field and is never read. The checked
catalogue wrapper at `808A7814` passes a null room argument; the native room
wrapper at `80946F40` passes the room owner. The callbacks use that distinction
to select the appropriate frame counter without borrowing uninitialised padding.

The native repeat initializer is `80052408`, full rig draw `800530D8`, and
positional level-sound entry `800D1D08`. The complete rig draw emits segment D
on both heads, transforms the suppressed flame joint, and calls the after-draw
callback with that transformed matrix. Preserve that path rather than replacing
the full actor with a static flame. Reserve/check both command heads and all
frame-owned matrices/scroll data before any draw writes.

Donor `two_tex_scroll_dolphin` doubles its input coordinates. The donor's
standard N64 SetTileSize decoder multiplies those coordinates by four to reach
the same representation. Thus the donor callback velocities correspond to
half those values in native quarter-texel coordinates, not an unchanged copy.
The callbacks mask the doubled donor coordinates to 14 bits, then shift to the
native quarter-texel representation. Bonfire's odd frames use explicit floor:
the maximum instantaneous difference is 1/8 texel, with no accumulated drift.
Even frames, campfire scrolling, and bonfire's horizontal scrolling are exact
at the native tile-origin precision. Textures and vertex UVs are unchanged.
The source bindings are `src/game/m_rcp.c`, `include/libforest/gbi_extensions.h`,
and `src/static/libforest/emu64/emu64.c` in the pinned GC checkout.

### Actual loop-sound dependencies

Main SFX sequences are donor 242 and native 199. Their channels 8–13 start at
`164`; C2 selects the level table at donor `2E02` or native `265C`. The donor
table has 96 entries; native has 68. IDs `5C/5D` cannot index the native table.
The six triggered-sound tables at `188` are not the looping-sound dispatch.

Donor `5C` targets `2F08` and `5D` targets `2F5A`. Both programs contain two
layers using instruments 12 and 14 from donor font 153, the default selector.
Its native counterpart is font 139, but those instrument numbers refer to
different waves/tuning. Import the actual programs and dependencies, not matching
numeric IDs. The donor samples contain 18,514 and 2,826 ADPCM bytes in wave 5 at
`23820` and `284D0`, with their complete loops, books, and envelope data.

The [complete audio converter](../docs/checkpoints/V3_FIRE_AUDIO.md) uses the two
spare native font-140 table words for instruments 72/73, without shifting original
resources. Font 139 already has 126; appending there would reach reserved values.
Each new program explicitly selects font selector 1 and large-note mode. All five
program pointers relocate, both layer instruments map, and every other source
byte remains, including the aligned envelope and original padding. The C2 table
operand at sequence offset `179` points to 128 checked level entries: original
IDs retain their targets, `5C/5D` select the imports, and unassigned IDs stop.

The complete sustained layer uses a 32,000-tick continuous note; each crackling
layer has ten notes, a one-time 100-tick rest, and a repeated 300-tick rest.
Bonfire retains its five-semitone layer transposition. Its melody, timing,
velocities, decay, loop state, predictors, and sample tuning are not approximated.
The font grows by 352 bytes, the sequence by 432, and streamed wave data by
21,360 including alignment. Conservative permanent usage grows by 800 to 109,312,
requiring more than the native 108,544-byte pool. The
[sound runtime](../docs/checkpoints/V3_FIRE_SOUND_RUNTIME.md) increases total,
fixed, and permanent allocation by 1 KiB, preserving session/cache capacity.
Actual native allocation, complete font/header relocation, both sample transfers,
and start/stop pass. The installed pool has 256 conservative bytes spare.
The full wave file moves to physical `03800000`, retaining external wave 2's
physical location through the checked native unsigned header-base addition.
Fire move callbacks refresh their actual IDs through `sAdo_OngenPos`, using the
actor address as the source identity and the actual actor position. Native
transition states 5, 6, 13, and 15 suppress refresh; the positional manager owns
expiry. No repeated one-shot substitute is used.

### Installed native callbacks

`overlays/v3/fire.c` occupies 1,240 bytes at `80483800`. Its two callback tables
are at `80483FC0` and `80483FD8`; both retain null destroy/DMA entries. The guard
at `80483FF0` remains intact. Full objects occupy VROM `02468000` and `0246A000`.
The checked complete-object DMA gate accepts only each exact index/item/vtable
combination. Neither fire can borrow the other fire's callback permission.

Every draw checks both display heads before writing. It reserves 176 bytes plus
at most 15 alignment bytes from the opaque arena, with five commands per head.
The identical opaque/translucent base transform shares one immutable matrix;
a second frame-owned matrix contains the billboard transform. Five immutable
scroll commands follow. Arbitrarily aligned allocation tails are accepted when
the aligned resources and command heads fit; insufficient capacity changes
nothing. Native cache writeback covers both frame resources and the two used
actor matrices. No new normal heap, resident package, or model-bank allocation
is required. Full native rig traversal retains all three joint transforms.

The bonfire catalogue uses native mode 0 with its verified `0.86/−3` final
framing, not GC mode 19 as a native index. Both fires remain non-orderable, and
ordinary shop lists stay unchanged. HRA uses the same safe camping weight
mapping as the other rewards, while feng shui preserves the zero-colour data.

## Tent light contract

The donor constructor allocates a private 32-byte, 32-byte-aligned palette,
initialises the fade from `switch_bit == 1`, and builds the palette. Move steps
toward the selected endpoint by float 0.1, clamps at 0 or 1, and updates all
16 entries. Destructor releases the private storage if present. Drawing binds
segment 8 and emits all four complete opaque parts.

Both full palette endpoints are converted. Only entry 7 changes: native off
`0001`, on `FFE5`. Its five-bit RGB components must interpolate with truncation,
retaining the off alpha bit. Unchanged entries, including transparent colours,
must stay unchanged. Do not apply the donor RGB5A3 packing directly to RGBA16.

The N64 actor stride is `740`, with switch state at `12C`, not the GC actor
layout. GC `dynamic_work_f`/`pal_p` offsets cannot be copied into the N64 actor.
The native adapter stores the four-byte fade in unused joint storage at `1A4`.
The tent's native profile has no generic rig or texture animation. Checked
constructor, update, and draw branches in both the original and current ROMs
skip the generic animation consumers when those profile pointers are null.
No other item uses this tent-specific interpretation of joint storage.

`overlays/v3/tent_model.c` supplies create, move, draw, and destroy callbacks.
Create/move preserve the donor's boolean switch interpretation, float step,
clamping, and interpolation. Draw creates an immutable palette for that submitted
graphics frame. The existing opaque arena supplies a 32-byte-aligned 64-byte
matrix followed by the complete 32-byte palette; both receive a native cache
writeback. Six commands load the matrix, bind segment 8, and draw all four parts.
Both arena ends are checked before writing. Insufficient space leaves the arena
and commands unchanged rather than submitting an invalid pointer.

Each draw uses 144 bytes plus at most 16 bytes of alignment padding. Fade updates
remain per actor even when not drawn, and successive draws cannot mutate a
previous frame's palette. Destruction resets only the private fade: there is no
heap palette to release and no dangling palette reference when an actor is reused.
The lifetime differs from the GC allocation strategy while retaining its visible
fade and avoiding cross-frame mutation on N64.

The callbacks occupy 580 installed bytes at `80483400`, with their vtable at
`80483700`. The full 68-byte profile retains height 15.7, scale 0.01, shape 4,
collision 0, and interaction `8000`, with no generic model/rig/texture pointers.
The model occupies VROM `0244E000..0244F0BF`. Canonical sparse slots contain
the complete callback-owned profile and English item record. The checked
startup loads and invalidates the existing item-code reservation, including
these callbacks; no separate loader or larger resident package is required.
The catalogue retains native mode 0 and explicitly disallows ordering in all
four orientations. Native HRA uses `D4050600` (412 points, scoring category 3);
feng shui uses `0100`. Neither mapping changes the summer-camper reward route.

The [runtime checkpoint](../docs/checkpoints/V3_TENT_MODEL_RUNTIME.md) records
installed native callback/reader execution and deterministic offline selection.
The [loader repair](../docs/checkpoints/V3_TENT_MODEL_LOADER.md) also verifies
actual complete-object DMA and rotated bank reuse. The DMA gate accepts exactly
tent index 1243, canonical item `336C`, and vtable `80483700`; its fifth DMA entry
is zero. Other callback-owned objects need their own reviewed permission.
GPU appearance, ordinary light interaction, acquisition, and persistence are
not established by the callback probe. The
[callback checkpoint](../docs/checkpoints/V3_TENT_MODEL_CALLBACKS.md) retains
the component's source/host evidence.

## Four-cell item readers

`AF_V3_FOUR_CELL_ITEMS` extends the existing multi-cell reader with size 2.
Without the new flag, prior one/two-cell builds retain their original rejection
of size 2. The new flag requires `AF_V3_MULTI_CELL_ITEMS`.

Both original ROM and donor tables contain the same clockwise cell records:
`(1,0,0)`, `(1,1,0)`, `(1,1,1)`, `(1,0,1)`, expressed as exists/X/Z.
All four are occupied and are relative to the upper-left anchor for every
rotation. The square footprint does not rotate around the anchor like a 1×2
item. Inactive one/two-cell records still retain the anchor coordinates.
Coordinates use unsigned addition to retain native signed-boundary wrapping.

`tools/v3_four_cell_items.py` verifies the actual original selector at
`800BE6D8` and table at `8010D2FC`, then compiles the shared readers against
the sparse selected-profile table and all three clothing records. Disabled,
missing, misidentified, or unsupported records reject placement with result 3
and four zeroed records. Native-item fallbacks remain unchanged.

The compiled extension occupies 1,020 bytes at `80483000`, inside the existing
4 KiB resident item-code reservation. ABI 70 replaces the checked reader code,
rebinds all five public bridges, and refreshes the saved-resource, package, and
prefix checksums. The code ends before the tent callbacks at `80483400`.
Save structures do not change; selected dependencies include enabled fires.

## Remaining integration

1. Connect the actual summer-camper reward route for all ten items. Do not
   substitute ordinary shop stock or an unrelated generic gift source.
   [Complete campsite scenery and the scene/event bindings](V3_CAMPSITE.md)
   supply the assets and define the remaining runtime adapter.
2. Preserve the seven static furniture profiles as supplied. In particular,
   the collectible lantern has no light callback and the sleeping bag has no
   sleep/contact action bit. `ef_tent_lamp` is a separate campsite scene effect,
   not an unimplemented collectible interaction.
3. Verify ordinary appearance, interaction, and persistence in a bounded gameplay
   batch. Original-hardware acceptance and the remaining donor content stay open.

Executed checks and artifact hashes live in the
[camping actor checkpoint](../docs/checkpoints/V3_CAMPING_ACTORS.md) and the
[complete fire runtime checkpoint](../docs/checkpoints/V3_FIRE_RUNTIME.md).
