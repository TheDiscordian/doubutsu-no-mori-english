# V3 clothing display metadata and ownership

## Installed behaviour

Selected mannequin IDs `3AFC..3AFF` share pocket garment `34BF`'s complete
English name, 380-Bell price, and per-player clothing ownership bit `BF`.
They are placed-furniture category 10, not pocket-clothing category 12.
All four rotations use the native mannequin footprint reader with equivalent
item `17AC | rotation`, preserving all four twelve-byte cells and coordinates.
Pocket `34BF` retains its native non-furniture footprint rejection.

Canonicalization requires the complete selected display profile at runtime
index 1,727, including its resolved pointer and selected garment/artwork.
Missing dependencies retain the previous readers' rejection behaviour.
Name/query inputs keep their full-width validation; native readers that accept
a sixteen-bit item keep that convention. No new decorative-furniture ownership
bit is recorded. All original items and the two static imports remain intact.

## Memory and entry points

The 516-byte helper occupies `80466C00..80466E03`. Its reservation reclaims
`80466C00..80466F1F` from the retired bank-index seed. The installer verifies
the complete 1,267-byte `FF` seed before touching it; the tail beginning at
`80466F20` remains `FF`. Live bank indices use the separate expanded tables.

| Existing entry | Installed target | Previous implementation |
| --- | --- | --- |
| Name `80467300` | `80466C50` | `8046D8DC` |
| Category `8046744C` | `80466C90` | `8046D9E8` |
| Footprint `804674B4` | `80466CE0` | `8046DA6C` |
| Price `80467574` | `80466D54` | `8046DB2C` |
| Collection record `804699C0` | `80466D94` | Bridge `80466F00` |
| Ownership query `80469AD4` | `80466DD4` | Bridge `80466F10` |

The canonical item helper begins at `80466C00`. Each collection bridge retains
the two displaced prologue instructions and rejoins the unchanged body.
Private clearing and the complete secondary item/save implementation remain
intact. The largest new stack frame is 40 bytes. The build report records these
final redirects under `clothing.display.readers`; the earlier item-reader report
describes the underlying installation, not the final entry jumps.

## HRA and feng shui metadata

The clothing variant has 2,051 rows in both on-demand scoring tables. Its full
1,267-row previous prefix stays intact. Native rows, inert markers, and the
two decorative imports retain their values; index 1,727 receives the garment's
verified donor properties. Non-clothing builds retain 1,267 rows.

The actual donor conversion function maps `24BF` to mannequin index 682.
Its complete function hash and conversion instruction are checked before using
that row. HRA donor `D4050800` converts to native `D4051000`: series 53, group 5,
birth category 8, and no surface flag. Construction still has 21 groups.
Feng shui donor `0000` supplies no colour bonus or facing penalty. The original
255 native garment rows remain `0001`; they are not rewritten to donor values.

HRA occupies 30,288 image bytes plus 1,184 relocation bytes; feng shui occupies
7,968 plus 80. Both fit their existing 32-KiB/8-KiB image reservations. Existing
DMA indices and on-demand allocation paths remain. Only recorded scheduler
size operands change; the resident prefix stays 48 KiB. HRA's missing-item
search uses the expanded count and rejects padding indices 2,048 and above.

## Verification and compatibility

Two focused host/cartridge checks pass. Complete native item-reader and
collection exercises pass, covering four rotations and canonical ownership.
Native loading/relocation of the expanded HRA owner passes. Its group/points
assertions and feng shui execution remain pending after bounded test-driver
corrections, as recorded in the [checkpoint](../docs/checkpoints/V3_DISPLAY_ITEM_READERS.md).

ABI 42 retains ABI 41's complete save runtime, codec, selected profile, and
working-state layout. Same-profile compatibility is expected in both directions,
but no new ordinary save/reload cycle is claimed. Older profiles without the
display dependency still reject new saves; keep backups.

Global pocket/display conversion, remaining special readers, actual catalogue
rows, ordinary placement, and placed-item persistence remain work. Native
component checks do not establish those gameplay routes. Both web patchers
stay V2 until user testing and explicit approval.
