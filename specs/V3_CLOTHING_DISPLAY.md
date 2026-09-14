# V3 native clothing mannequins

## Installed scope

The clothing-enabled build gives cherry shirt a stable mannequin identity and
uses the original N64 clothing model, draw callback, and model-bank lifetime.
This supplies the renderer needed for house and catalogue display. The
[display readers](V3_DISPLAY_ITEM_READERS.md) connect metadata, canonical
collection, and expanded scoring tables; the [global conversions](V3_DISPLAY_CONVERSION.md)
connect normal placement/pickup callers. Ordinary inventory Drop and B pickup
pass inside the copied town's house. The [clothing catalogue](V3_CLOTHING_CATALOGUE.md)
adds the collected row and complete native preview with passing focused/native
checks. Remaining special readers, ordinary ordering/payment, rotation, and
placed-save persistence still need integration/verification.

Donor clothing `24BF` retains pocket item `34BF` and texture index `10BF`.
Its display dependency is item `3AFC`, runtime index 1,727, with rotations
`3AFC..3AFF`. The display registry fixes this assignment independently of
selection order. It is not a separately selectable item, and its ownership
belongs to the garment, not the decorative-furniture catalogue.

## Native model and callbacks

All 255 native clothing profiles at indices 491–745 point to the same 464-byte
program at VROM `0093BD70`, relocation `0093BF40`, original RAM `80A7BAD0`.
The builder verifies the complete program, relocation, room owner, and all 255
table bindings. The original resources remain untouched.

The program is relocated into owned resident memory at `80466000..804661CF`.
Its constructors, move/destructor callbacks, drawing instructions, profile,
and both native DMA calls remain native. Only the nine-word shirt-index window
changes: it calls the selected full-index reader, restores the bank argument,
then rejoins the original texture/palette and geometry transfers. The original
callback already reserves the stack slot used to preserve the bank.

The native geometry at VROM `013EB000` is 3,584 bytes. The bank contains the
512-byte shirt texture, 32-byte palette, and that geometry, totalling 4,128
bytes. This fits both the 5,120-byte room bank and the 9,216-byte catalogue
preview buffer. No heap, actor, model buffer, or DMA directory grows.

The draw callback writes its four original commands: segment 6 points at
`bank + 220`, segment 8 at the texture, segment 9 at `bank + 200`, and the
display-list command calls `06000390` in the native mannequin geometry.

## Resident layout and selection

| Address | Contents |
| --- | --- |
| `80465800..80465C9F` | Expanded furniture helpers, 1,184 bytes |
| `80466000..804661CF` | Relocated native mannequin program, 464 bytes |
| `80466200..8046626F` | Checked shirt-index helper, 112 bytes |
| `80466600..8046664F` | Display identity and native profile, 80 bytes |
| `8046A000..8046A08F` | Expanded-table initializer, 144 bytes |

These reservations use retired native table storage. Imported seed profiles
beginning at `804666CC`, all eight furniture public entries, and the field
bridge at `8046A200` remain intact. Expanded transient storage stays in the
[guarded table reservation](V3_FURNITURE_TABLES.md).

Startup installs the resolved profile pointer `80466608` at index 1,727.
Lookup requires the exact enabled row, resolved pointer, selected display bit,
and valid selected pocket garment. Missing or malformed dependencies reject
the imported profile. Native clothing indices retain their original calculation
and unknown-item fallback. The native room bank selector and reload/release
functions use the new profile through the stable furniture entry points.

## Save compatibility

Format 2, the 192-byte profile, the working-state layout, and the save codec
remain unchanged. Profile byte 119 gains bit `80` for display `3AFC`; clothing
byte 183 retains bit `80` for pocket item `34BF`. This dependency participates in
the existing saved-profile checks even before a player places the garment.

Older same-clothing profiles do not contain the new display bit. Their saves
are accepted by the expanded profile in the focused codec check, but saves
written with the new profile are rejected by those older builds. A profile
missing the dependency stops at the existing incompatibility guard; no migration
backwards is supplied. Back up existing saves. Fresh ordinary cross-build
reloads are not claimed. V2 and older format-1 V3 builds remain incompatible
with format-2 saves.

## Evidence and next integration

Three focused checks and the corrected 116-record native run pass. Native
execution covers the actual model-bank loader/reloader for all four rotations,
complete texture/palette/model contents and untouched padding, the original
draw commands, profile/bank cleanup, retained static and original furniture,
and memory guards. The draw check writes private CPU-side command buffers;
it is not an ordinary GPU-rendered house or catalogue scene.

The [checkpoint](../docs/checkpoints/V3_CLOTHING_DISPLAY.md) records exact
artifacts and the bounded test-setup correction. Both conversions at
`800BEFCC` and `800BF10C` are installed. Shared metadata/collection and the
2,051-row scoring tables and clothing catalogue preview pass native checks.
Complete remaining special readers, ordinary catalogue ordering/payment, and
placed-item persistence.
Neither served web patcher changes without user testing and explicit approval.
