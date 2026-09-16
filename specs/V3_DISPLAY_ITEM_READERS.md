# V3 clothing display metadata and ownership

## Installed behaviour

Selected mannequin IDs share their parent garment's complete English name,
price, and per-player clothing ownership bit. The installed pairs are
`341A ↔ 3868`, `341B ↔ 386C`, and `34BF ↔ 3AFC`, including all four rotations.
The same generated [alias records](V3_FURNITURE_PIPELINE.md#native-alias-records)
serve every reader; no new per-item switch or duplicate text source is needed.
They are placed-furniture category 10, not pocket-clothing category 12.
All four rotations use the native mannequin footprint reader with equivalent
item `17AC | rotation`, preserving all four twelve-byte cells and coordinates.
Pocket garments retain their native non-furniture footprint rejection.

Canonicalization requires the complete selected display profile at its actual
runtime index, including its resolved pointer and selected garment/artwork.
Missing dependencies retain the previous readers' rejection behaviour.
Name/query inputs keep their full-width validation; native readers that accept
a sixteen-bit item keep that convention. No new decorative-furniture ownership
bit is recorded. All original items and existing furniture imports remain intact.

## Memory and entry points

The 640-byte helper occupies `80466C00..80466E7F`, within the existing
`80466C00..80466EFF` reservation. The installer verifies the previous complete
helper and zero tail before replacement. Collection bridges occupy
`80466F00..80466F1F`; speed-bag code beginning at `80466F20` is live and must not
be overwritten. Live bank indices use their separate expanded tables.

Stable public entries are name `80467300`, category `8046744C`, footprint
`804674B4`, price `80467574`, collection record `804699C0`, and ownership query
`80469AD4`. The shared installer binds each entry to its actual compiled symbol
and records the exact old/new hook bytes. It does not assume fixed internal
function offsets across compilations.

The canonical item helper begins at `80466C00`. Each collection bridge retains
the two displaced prologue instructions and rejoins the unchanged body.
Private clearing and the complete secondary item/save implementation remain
intact. The build report records these
final redirects under `clothing.display.readers`; the earlier item-reader report
describes the underlying installation, not the final entry jumps.

## HRA and feng shui metadata

The clothing variant has 2,051 rows in both on-demand scoring tables. Native
rows, inert markers, and installed furniture retain their values. Each selected
garment display has verified donor properties at its actual runtime index.
Shared alias-reader updates leave both scoring resources completely unchanged.

The actual donor conversion function maps `24BF` to mannequin index 682.
Its complete function hash and conversion instruction are checked before using
that row. HRA donor `D4050800` converts to native `D4051000`: series 53, group 5,
birth category 8, and no surface flag. Construction still has 21 groups.
Feng shui donor `0000` supplies no colour bonus or facing penalty. The original
255 native garment rows remain `0001`; they are not rewritten to donor values.

The checked build receipt records complete scoring image/relocation sizes and
hashes. Existing DMA identities and on-demand allocation paths remain; the
resident prefix stays 48 KiB. HRA's missing-item search uses the expanded count
and rejects padding indices 2,048 and above.

## Verification and compatibility

Twenty focused host/cartridge/composition checks pass for the shared adapter.
The current native run passes 187 records with 177 assertions, including all
three pairs, four rotations, complete English names, prices, native footprint
cells, selection rejection, original fallbacks, restored profile, and guards.
Host sanitizer checks cover canonical ownership and generated-footprint routing.
Unchanged native collection/scoring checks retain their evidence from the
[conversion batch](../docs/checkpoints/V3_DISPLAY_CONVERSION.md).
The [reader checkpoint](../docs/checkpoints/V3_DISPLAY_ITEM_READERS.md) preserves
the initial bounded test-driver failures without relabelling them passed.

ABI 96 retains ABI 95's complete save runtime, codec, selected profile, and
working-state layout. Same-profile compatibility is expected in both directions,
but no new ordinary save/reload cycle is claimed. Older profiles without the
display dependency still reject new saves; keep backups.

The [global conversion](V3_DISPLAY_CONVERSION.md) connects normal pocket and
display callers. Ordinary house placement and pickup pass on the copied town.
The [clothing catalogue](V3_CLOTHING_CATALOGUE.md) installs the collected row
and complete preview. Remaining special readers, ordinary payment/delivery,
rotation, and placed-item persistence remain work. Both web patchers
stay V2 until user testing and explicit approval.
