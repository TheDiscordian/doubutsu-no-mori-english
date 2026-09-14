# V3 additive clothing

## Resource foundation

`--clothing` includes the current villager/furniture foundation and installs
Punchy's actual GameCube cherry-shirt artwork, name/price metadata, and the
shared indexed texture/palette reader. It does not enable the garment as an
inventory item or enable Punchy's initial outfit. NPC-specific streaming,
wearing, menus, acquisition, mannequins, and profile/persistence integration
remain required before the garment is selectable.

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

The two clothing helpers are linked after the existing asset/draw/audio code,
inside `80460100..80460FFF`; the linker forbids overlap with the object table.
The loaded prefix remains 48 KiB. Configuration ABI 28 identifies this variant.
The native ordinary arenas, actors, and saved clothing field sizes do not grow.

## Shared indexed reader

The complete native reader at `800B1EDC..800B1F73` is source-hash checked, then
its entry jumps to `af_v3_load_clothing`. Native indices 0–255 keep their
original texture and palette VROM addresses. Index `10BF` requires the exact
installed cherry-shirt metadata. Missing, disabled, malformed, negative, or
otherwise unknown imported indices return no resource and do not write buffers.
Both destination pointers must be present. Transfers remain synchronous through
the native DMA manager, using the original 512/32-byte sizes.

NPCs have additional asynchronous and foreground clothing paths in both NPC
overlays. Their category checks currently accept only `24xx`, and they calculate
their own source addresses. Player startup/change-clothes paths also calculate
addresses directly. Patching the shared indexed reader alone does not connect
those paths; do not enable the imported default on that evidence.

## Remaining item and save integration

Connect full clothing identities to the NPC category checks and their texture/
palette sources, player startup/change-clothes, full names, item classification,
menus/icons, normal acquisition, price/buy/sell paths, display mannequins,
mail/gifts, and ordinary saving/loading. Keep original garments and behaviour.

The existing [V3 save registry](V3_SAVE_PROFILE.md) allocates its item bits to
furniture rotation groups. Do not reuse a furniture bit for this clothing ID:
the clothing class needs a reviewed registry/format extension before player use.
This resource-only build leaves the profile unchanged and does not claim
imported-clothing persistence. V3 saves still must not be loaded in V2.
Public and local patchers remain V2 pending user testing and explicit approval.
