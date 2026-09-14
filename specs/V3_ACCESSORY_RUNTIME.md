# V3 joint-attached villager accessories

## Implemented boundary

`tools/v3_accessory_runtime.py` installs all twenty imported native draw records
and attaches all sixteen required accessories through both NPC renderers. The
ordinary native characters and the existing Cheri/Punchy records are retained.
Remaining voices, text/defaults, houses, town behaviour, ordinary appearance,
and persistence still require integration. All twenty move-in flags remain off.
Neither served V2 patcher changes.

## Attachment and lifetime

The donor creates these tool actors in action 4, whose handler does nothing.
Their action tables have no independent animation or collision behaviour;
action 3 deletes the actor, and their destructor does nothing. The NPC supplies
the selected joint matrix and a one-use readiness flag. The N64 adaptation
therefore shares immutable accessory objects instead of allocating extra actors.

The wrapper forwards every original before/after callback argument, including
the original actor pointer, and preserves the callbacks' return values. After
the original after-joint callback, it captures joint 13 or 25 with the donor's
`1 / (actor.scale.x * 100)` correction. The CPU matrix stack is restored.
The captured matrix is local to that draw call: an absent joint cannot reuse
an earlier frame's transform, and actor deletion needs no separate cleanup.

The native body completes before the accessory commands are appended, avoiding
accessory palette/texture changes during later body joints. The accessory uses
the native NPC lighting/fog setup and opaque stream. Its fixed-point matrix
lives in the current frame's graphics allocation. Segment 6 is restored to the
native CPU segment-table value; the CPU table itself is never modified.
Ordinary NPC visibility controls accessory visibility.

The helper validates the installed identity, bank, joint, resource bounds,
alignment, and display-list offset. It skips attachment if fewer than 128 bytes
remain for seven commands and one 64-byte matrix. Original skeleton drawing
still runs. The compiled helper is 1,004 bytes, with a 136-byte main frame and
56-byte after-callback frame. No actor layout, saved field, or ordinary heap grows.

## Resident package

ABI 52 adds a separately checked 49,152-byte package at VROM `02270000`, loaded
at `80473000..8047EFFF`. This is additional resident memory; the original
`80460000..8046BFFF` startup prefix remains 49,152 bytes.

| Package offset | Contents |
| --- | --- |
| `0000..000F` | `AFA3` header, package ABI 1, size `C000`, row count 20 |
| `0100..04EB` | Accessory helper, entry `80473100` |
| `1000..113F` | Twenty 16-byte identity/attachment rows |
| `2000` onward | Sixteen complete objects, individually aligned to 32 bytes |
| `BFF0..BFFF` | Four `AFACC0DE` guard words |

Each row holds actor ID, bank ID, resident address, segmented display-list
pointer, joint, enabled byte, and object length. Pigleg, Dobie, Cheri, and
Punchy have empty accessory rows. The objects total 40,480 bytes before padding.

The descriptor at main-prefix offset `F0` contains VROM, size, CRC, and destination.
Startup validates those fields, the complete transfer, package header, and guard,
then performs cache maintenance before marking V3 ready. The 880-byte startup
fits before the existing configuration. Systems without eight MiB do not touch
the expansion reservation. The package follows the furniture reservation and
does not overlap the font, title, save code, diagnostic area, or emergency stack.

## Native hooks and cartridge

| NPC owner VROM | Original link base | Replaced skeleton call |
| --- | --- | --- |
| `008681F0` | `809735B0` | `80978654` |
| `008798C0` | `80995BF0` | `8099A2E0` |

Only each call's JAL target changes. The `sw t0,14(sp)` delay slot, native
renderer, callback relocations, and overlay sizes are preserved. The builder
pins both complete input owners and renderer functions and rejects a relocation
at either edited instruction.

The expanded blob is `7C000` bytes. Composition uses verified unused physical
padding, updates only that blob's DMA row, and patches the three existing
uncompressed owners in place. All other physical DMA locations, including audio,
remain intact. The cartridge stays 32 MiB; N64 CRC and UPS reconstruction pass.
Profile and saved formats remain unchanged from ABI 51, without asserting
ordinary cross-build save compatibility.

## Evidence and remaining checks

Seven focused host/cartridge tests pass. Partial native execution verifies actual
startup, both attachment joints, corrected transforms, emitted commands, native
fallback, and nearly full graphics-buffer handling. These use a synthetic rig
through the real skeleton engine, not ordinary NPC rendering or GPU acceptance.
The final guard tail remains unexecuted after the bounded fixture failures.
The [checkpoint](../docs/checkpoints/V3_ACCESSORY_RUNTIME.md) records exact
outputs and limits. Carry the corrected tail into the next combined native
test while continuing bulk voice/text/default/house integration.
