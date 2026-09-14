# V3 additive clothing

## Resource foundation

`--clothing` includes the current villager/furniture foundation and installs
Punchy's actual GameCube cherry-shirt artwork, name/price metadata, and the
shared indexed texture/palette reader, both NPC clothing paths, and player
startup/change-clothes readers, selected shared item metadata, and native shop
stock. Inventory wearing and ordinary save/reload work on the copied test town.
It does not enable Punchy's initial outfit. Remaining clothing actions,
ordinary acquisition, mannequins, and display persistence remain required before
the garment is selectable in the patcher.

All 256 original native clothing textures and palettes remain intact. Donor
`24BF` is not native `24BF`: all 1,024 converted colour pixels are compared
against every native garment, and none matches. The source archive, REL,
symbol table, full converted texture/palette hashes, name, and dimensions are
checked before installation.

## Identity and resource ownership

The clothing registry reserves donor `GAFE01-r0/item/24BF` as item `34BF`,
independently of selection order. Its render index is `10BF`, retaining the
native `item - 2400` relationship without changing existing cloth fields.
The native game has no type-3 items; the current furniture pilots and the
verified English donor's 242 second-bank furniture groups all lie below `3400`.
The reservation is not permission to pass the garment to furniture readers.
Its name is `cherry shirt`, and its donor base price is 380 Bells.

The 512-byte CI4 texture and 32-byte RGBA16 palette are stored consecutively at
VROM `03F0F000..03F0F21F`, in the ROM-only tail of the existing V3 DMA file.
This retains the DMA directory size and remains below the reserved villager
texture range at `03F10000`. No complete ROM or extracted asset is committed.

One 32-byte resource record occupies `80462820..8046283F`, immediately after
the twenty 104-byte NPC draw slots and before the audio index data at `80462900`.
It contains item/index, resource VROM, base price, resource-enabled flag,
sixteen-byte name, and checked zero padding. Resource availability is distinct
from completed item support and move-in eligibility.

The clothing helpers are linked after the existing asset/draw/audio code,
inside `80460100..80460FFF`; the linker forbids overlap with the object table.
The loaded prefix remains 48 KiB. Configuration ABI 41 identifies this variant;
its separate [format-2 save codec](V3_CLOTHING_SAVE.md) is loaded independently.
The native ordinary arenas, actors, and saved clothing field sizes do not grow.

## Shared indexed reader

The complete native reader at `800B1EDC..800B1F73` is source-hash checked, then
its entry jumps to `af_v3_load_clothing`. Native indices 0–255 keep their
original texture and palette VROM addresses. Index `10BF` requires the exact
installed cherry-shirt metadata. Missing, disabled, malformed, negative, or
otherwise unknown imported indices return no resource and do not write buffers.
Both destination pointers must be present. Transfers remain synchronous through
the native DMA manager, using the original 512/32-byte sizes.

## NPC-specific loaders

Both NPC owners retain ten `B0`-byte clothing slots at controller offset `174`.
The four resource entries per owner jump to resident helpers. Two 32-byte
category-decision windows per owner call a checked index reader: native `24xx`
keeps its index, installed `34BF` gives `10BF`, and invalid clothing retains the
native `2400` fallback. Full item IDs and the other slot flags remain intact.
The remaining controller loops, reset/reuse logic, and native relocation tables
are unchanged. Complete source-function hashes, incoming control-flow checks,
and relocation exclusions guard every edit.

Texture/palette banks stay at slot offsets `8`/`5C`, destination pointers at
bank offset `4`, requests at `14`, queues at `34`, and message storage at `4C`.
Foreground reads use native synchronous DMA. Queued reads preserve the native
single-submission marker, one-message queues, and nonblocking completion poll.
Transfers remain 512/32 bytes; no extra live slots or garment buffers are added.
The shared transfer helper uses a 72-byte frame, matching the original queued
reader and adding 40 bytes to foreground calls. The checked index uses 24 bytes.

Focused checks pass. Native evidence confirms the first owner's complete
foreground loop with original, imported, and invalid clothing. Queued completion
and the second owner's execution remain unverified; the bounded test checkpoint
records the allocation/timing setup limits.

## Player startup and clothing changes

The complete native functions at `800B1960..800B19C3`,
`800B19C4..800B1A27`, and `800B1BE8..800B1C83` are hash-checked and redirected
at their entries. Startup registers the same texture/palette banks 14/15 through
native `800B1838`, retaining both buffer indices, their native offset convention,
and 512/32-byte sizes. It reads the existing private clothing index at `A76`.
Missing artwork uses native index zero without modifying the saved clothing;
profile compatibility remains the save guard's responsibility.

Clothes changes retain native buffer toggling and texture lookup. An unknown
resource returns without toggling or writing. An unavailable inactive bank
restores the preceding active index. Valid changes load the texture and adjacent
palette through the installed shared reader. No bank, buffer, or saved field
grows. Startup/change helpers use 40-byte frames.

Three focused tests and the initial 47-step native run pass. Native evidence
includes complete original/imported startup artwork, all four registered bank
records, both buffer changes, unchanged inactive contents, unknown/missing
handling, private-field retention, restored globals, and guards. This is resource
integration, not an ordinary inventory-driven clothing change or save/reload.

## Remaining item and save integration

The [shared item readers](V3_CLOTHING_ITEMS.md) connect the complete English
name, clothing category, and donor price, while preserving the native
non-furniture footprint result. The [menu routing](V3_CLOTHING_MENU.md) connects
selected clothing classification and additional hand/cursor decisions without
changing item identities. The [player animation adapter](V3_CLOTHING_WEAR.md)
preserves the full imported texture index at the actual change-clothes frame.
Ordinary inventory-driven wearing, outdoor rendering, gyroid Save & Quit, and
fresh-process reloading pass on a copied town. Both saved clothing fields,
all expected pockets, ownership, and complete active artwork survive the cycle.
The [shop category reader](V3_SHOPS.md) recognises selected imports as clothing
without changing native categories or item IDs. The
[stock adapter](V3_CLOTHING_STOCK.md) includes selected cherry shirt in A's
all-season stock, retaining native seasons, rarity, and single-draw RNG.
Focused and native stock/acquisition checks pass. The
[shop mannequin adapter](V3_SHOP_MANNEQUIN.md) connects native counting/search
while retaining both full texture-loading loops; focused cartridge and native
checks pass. The [clothing shop-floor adapter](V3_CLOTHING_SHOP_FLOOR.md)
connects reserve, selection, and native sale processing, including actual
sold-stock updates, the bare-mannequin callback, and foreground clearing.
Cartridge and native checks pass. Connect remaining clothing actions
and ordinary acquisition/buy/sell, home/catalogue display, mail/gifts, and
persistence for those representations. The
[display adapter](V3_CLOTHING_DISPLAY.md) installs the actual native mannequin
under stable identity `3AFC`, with checked complete native loading and drawing
commands. Global placement and remaining alias readers are not yet installed.
Keep original garments and behaviour.

The [format-2 save extension](V3_CLOTHING_SAVE.md) installs independent clothing
profile/ownership bits while retaining the earlier furniture records. Native
encoding/decoding and migration checks pass. The normal collection adapter
records per-player clothing ownership; catalogue presentation remains work.
Format-2 saves must not be
loaded in older format-1 V3 builds or V2. Keep existing saves backed up.
Public and local patchers remain V2 pending user testing and explicit approval.
