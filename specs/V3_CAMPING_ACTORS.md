# V3 camping actors

## Scope and current boundary

Convert and port the complete GAFE01-r0 campfire, bonfire, and tent model.
These complete the assets for the ten-entry `ftr_listTent` family alongside
the seven static objects in [Camping items](V3_CAMPING_ITEMS.md).
They are additive imports, not substitutions for native furniture.

Complete converted objects and the native four-cell item-reader extension are
available. Tent model is installed in ABI 69 with its light callbacks, English
metadata, catalogue/scoring, and optional saved dependency. The two fires are
**not installed or selectable**. Fire animation/sound callbacks and integration,
summer-camper acquisition, and ordinary gameplay/persistence remain required.
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

The donor loop-sound numbers are `005D` (campfire) and `005C` (bonfire). They are
source identities, **not verified native sound IDs**. The runtime must map the
actual sound resource and keep position/lifetime behaviour. Existing furniture
transition-state exclusions use different native and donor enum values.

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
4 KiB resident item-code reservation. Integration must replace the checked code,
rebind all five public bridges to their compiled entry points, and refresh the
resident package and prefix checksums. Compiling it alone does not modify ABI 69
or create a new playable bonfire. Save structures do not change.

## Remaining integration

1. Port the fires' complete rig,
   billboard, dual-tile scrolling, and mapped loop sounds to native callbacks.
2. Install complete profiles and item rows, four-cell readers, true catalogue
   framing (`0.86/−3` for bonfire), non-orderability, HRA/feng data, and selected
   dependencies. Use the current ABI 69 source, not an older cartridge chain.
3. Add individual and combined offline options only when their dependencies are
   actually installed; retain exact V2 composition for an empty selection.
4. Connect the actual summer-camper reward route for all ten items. Do not
   substitute ordinary shop stock or an unrelated generic gift source.
5. Verify affected native calls and ordinary interaction/persistence in a bounded
   batch. Original-hardware acceptance and the remaining donor content stay open.

Executed checks and artifact hashes live in the
[camping actor checkpoint](../docs/checkpoints/V3_CAMPING_ACTORS.md).
