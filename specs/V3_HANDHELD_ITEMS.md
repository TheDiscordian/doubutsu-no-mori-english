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

The 8-KiB resident module occupies `804A3000..804A4FFF`, after the accessory
package and before the existing furniture model pool. Code is bounded below
`804A4000`; an `AFHR` version-one header and fifty 16-byte records follow.
Each record is `(vrom, bytes, segment-six pointer, type)`. Four `AF48C0DE` footer
words guard its end. Empty slots, negative/out-of-range indices, unsupported
skeleton type one, malformed sizes/pointers, and out-of-storage transfers reject.
Individual transfers fit the existing 4,376-byte equipment-bank lower bound.
This does not approve arbitrary combined model-plus-animation sizes.

The importer appends payloads and the module before the checked terminal
catalogue/shop resources, moving only those three unchanged DMA owners.
Existing model VROMs, saved profiles, original player owner, and item actions
remain unchanged. Startup loads/checks the entire module against a compiled CRC
before publishing its code. Shared transfer verification and one instruction-cache
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
new browser choices. The actual equipment selector remains unchanged until
category actions, permissions, acquisition, and selected profiles are ready.

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

### Player ownership and actions

The current native player equipment selector is `808BD3F8..808BD583` in owner
VROM `007AC420`, linked at `808B2D50`. Its 396 bytes have SHA-256
`3e1e9584685cef3dcb81e6fe99ef412ddc49fd4a8df74901f55b1742f234258b` in both the
original and current ABI-99 cartridge. It reads ordinary saved equipment at
player-private offset `3EC`, or title-demo equipment at controller offset `3C`.
It accepts only `2200..2223`, using a 36-entry jump table at `808E0274` with
SHA-256 `b46dbe4b89cb5647022dddcf27baa8e2ca8ea5ffc73c02a249f32b3c695c6af1`.
The extra donor handheld IDs are therefore not existing native player support.

The next implementation must extend equipment selection and category permissions
using the shared kind readers without changing original kind meanings or
overstepping signed-byte bounds. Connect selected models to the shared loader, safe cleanup and
graphics bindings, take-out/put-away, and actual per-category actions. Do not
route a fan through an unrelated umbrella or ordinary tool action.

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
button/timing behaviour, and sound still need native integration. The complete
wait/swing and tumble/get-up data is installed through the shared animation readers; it is not
connected to native player actions yet. Held graphics and motion data do not
implement the controller/request/action flow on their own.

Inventory/ground readers, official names and prices, acquisition, context-correct
catalogue/collection integration, optional selection, and save/profile handling
remain required before enabling new handheld items. Original tools must not be
duplicated as new imports. Preserve existing ROMs/saves and both V2 patchers.
