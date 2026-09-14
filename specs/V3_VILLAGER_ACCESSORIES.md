# V3 islander accessory conversion

## Scope

`tools/v3_accessory_art.py` converts all sixteen separate accessories used by
the supplied GAFE01-r0 islanders. Every output includes its actual model,
palette, and textures in native N64 format. The separate
[runtime adapter](V3_ACCESSORY_RUNTIME.md) attaches these components; conversion
alone does not supply playable villagers or browser selections.

Do not remove an accessory to make a villager pass the body converter.
Accessory-bearing rows require the verified compiled dependency, which is
included in the resulting body bundle with its actual attachment joint.
`load_objects` pins the complete verified manifest and validates every object's
size and SHA-256; an edited receipt, missing object, or corrupted object fails.
This dependency binding does not implement runtime attachment.
Preserve the original N64 villagers, their
model banks, the translation-only path, and both stable V2 patchers.

## Verified bindings

The complete REL and symbol hashes are the existing import-source pins.
The actual 68-entry tool/profile table is `.data:00042034`, 136 bytes,
SHA-256 `0a54d36b4eda12e5c0c22c2ede016dbcc082060c63e6a0d96c0a9e31f23e9c98`.
Its final sixteen entries select the accessory actor profiles. The actual
villager draw rows identify these consumers and zero-based attachment joints:

| Tool index | Model family | Villager | Joint |
| --- | --- | --- | --- |
| 52 | anrium1 | Plucky | 25 |
| 53 | bag1 | Yodel | 13 |
| 54 | bag2 | Boomer | 13 |
| 55 | biscus1 | June | 25 |
| 56 | biscus2 | Maelle | 25 |
| 57 | biscus3 | Faith | 25 |
| 58 | biscus4 | Bliss | 25 |
| 59 | hasu1 | Elina | 25 |
| 60 | hat1 | Rowan | 25 |
| 61 | hat2 | O'Hare | 25 |
| 62 | hat3 | Flash | 25 |
| 63 | rei1 | Drift | 13 |
| 64 | rei2 | Bud | 13 |
| 65 | zinnia1 | Annalise | 25 |
| 66 | zinnia2 | Flossie | 25 |
| 67 | cobra1 | Ankha | 25 |

Tool indices are donor identities, not assigned N64 actor or object-bank IDs.
Dobie, Pigleg, Cheri, and Punchy have `-1/-1` accessory fields. The converter
requires all sixteen distinct consumer bindings and rejects unknown joints.

Each actual actor profile is 36 bytes, with actor size `01D4`, tool object bank
16, part 5, and flags `30`. REL pointers bind its constructor, no-op destructor,
move callback, and draw callback. The destructor is the verified eight-byte
`none_proc1` at `.text:0004B38C`, which returns zero. Each actual draw function
has one PPC high-adjusted/low-half model-address pair; both relocations must
target the exact selected model. Filenames alone are not identity evidence.

All model palette, texture, and vertex pointers bind unique complete resource
spans. Raw resources must contain no relocations. Missing, duplicate, external,
or unaccounted model pointers fail conversion. Palette alpha remains restricted
to binary native alpha; no partial-alpha colour is silently flattened.

## Native graphics

Each self-contained object uses segment 6. Resource starts align to 32 bytes,
display lists to eight, and complete objects to sixteen. The sixteen objects
total 40,480 bytes; individual sizes range from 1,584 to 5,024 bytes. This is
asset storage, not a claim that runtime RAM has been allocated.

Convert every GX CI4 texture into row-major native texels, every RGB5A3 palette
into RGBA16, and only the recognised vertex matrix flags into native zero flags.
Positions, UVs, normals/colours, alpha, all 1,156 vertices, and all 820 ordered
triangles are retained. Native graphics macros compile with the existing pinned
Docker MIPS toolchain; no GameCube graphics command is executed on the N64.

The existing strict furniture parser has an explicit accessory mode. It accepts
only the observed clamp/clamp, mirror/clamp, and mirror/repeat tile pairs,
their zero shifts, opaque/texture-edge render modes, and white or `B2B2B2FF`
primitive colour. It retains the two explicit native tile extents, 32×32 and
64×32, used with mirrored textures. Native mask widths use actual texture
dimensions, not the mirrored display extent. Ordinary static and speed-bag
parsing stay separate and keep their original accepted settings.

## Runtime attachment

In the donor, NPC construction creates a separate tool actor using the declared
type. The NPC joint callback copies the selected joint matrix after applying
`1 / (actor.scale.x * 100)` and sets the accessory's matrix-ready flag. The
accessory draws only when that flag is set, consumes it, and uses the ordinary
NPC lighting/fog setup and opaque display stream. Preserve this relationship
when adapting attachment; a texture alone does not supply the accessory.

The [runtime adapter](V3_ACCESSORY_RUNTIME.md) implements shared immutable
storage, frame-local joint transforms, donor scale correction, and renderer-state
preservation. It needs no persistent extra actor or deletion cleanup and leaves
the native reserved NPC model buffer unchanged.
All twenty villager body conversions are available, including Yodel's separate
complete gorilla model. Verify ordinary animation and appearance after connecting
the complete body and accessory. Town schedules, dialogue, houses, moves, and saved identity are
separate remaining islander work. Neither web patcher changes before user
testing and explicit approval.

The [accessory checkpoint](../docs/checkpoints/V3_ACCESSORY_ART.md) records
actual construction, complete asset checks, and current limits.
