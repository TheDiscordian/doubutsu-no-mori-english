# V3 imported furniture in native shops

## Scope

`--shops` includes catalogue, collection, and FlashRAM integration, then adds
the two selected static furniture pilots to native ordinary goods lists and
the global shop-category reader. It retains native list priority, town rarity,
random selection, duplicate filtering, and daily stock-generation code.
Imports remain development-only; neither web patcher changes from V2.

The save format and required profile are unchanged. V3 imported saves require
V3; do not load them in V2. Ordinary shop confirmation/payment, floor displays,
placement, scoring, and player lifecycle
still need work before an import is enabled for playtesting.

## Verified goods lists

The complete native furniture goods resource is VROM `011E6000`, 960 bytes,
SHA-256 `ec1b8d3ed3ae8228ba9a16a5851f804659e53148517186aa5416a82de5b4d6a2`.
The main-code descriptor at `8010DAA0` contains its start, end, and segmented
pointer-table address `0600038C`. The twelve-word table includes all ordinary,
event, and special lists; it is not a three-list-only resource.

Actual verified GAFE01-r0 REL data places oil drum (`32B8`) in `ftr_listA` and
haz-mat barrel (`3224`) in `ftr_listC`. The converter appends each selected ID
before the corresponding native terminator. All original entries, ordering,
terminators, and other lists remain intact. It adjusts every segmented list
pointer and the main descriptor. A single import needs separate two-byte
padding before the pointer table; the table stays word-aligned and the complete
resource stays sixteen-byte-aligned.

Both selected imports produce 976 bytes, table offset `390`, and descriptor
`011E6000 011E63D0 06000390`. Ordinary list lengths are A: 102, B: 101, C: 102.
Empty selection returns the complete original resource exactly.

Town priorities remain authoritative. An import's donor list is an A/B/C group,
not a fixed common/uncommon/rare assignment. Native `800C0490` membership and
`800BFCF0` random selection use the town's existing group-to-rarity mapping.

## Category helper and installation

The global category entry at `800C05E0` recognises enabled registered
`3xxx` furniture, returning category zero. Unknown or disabled imports return
minus one; all original types invoke the retained native implementation.
The original argument is preserved for that fallback.

The clothing variant also recognises selected `34BF` as shop category 2. It
calls the checked shared item-category entry at `8046744C` and requires clothing
category 12; unselected/unknown `34xx` is rejected. Native sixteen-bit argument
conversion remains intact. ABI 36 identifies this variant, whose 116-byte
helper and 24-byte frame fit before the room identity adapter at `80469D00`.
Both linker and installer enforce that boundary. This category query does not
add stock, catalogue rows, or mannequin rendering. The
[clothing checkpoint](../docs/checkpoints/V3_CLOTHING_SHOPS.md) records current
host/cartridge and native execution evidence.

The 68-byte helper starts at `80469C00` inside the existing 48-KiB resident
prefix. An original-function bridge occupies `8046BAA0..8046BAAF`. ABI 16 adds
no allocation or saved bytes. The builder validates the complete original
function, dependency symbols, free destinations, exact resource descriptor,
source hashes, pointer bounds, and explicit resource-resize permission.
Complete native list-selection, random-choice, daily-generation, and town
priority functions must remain identical to the pinned V2 baseline.

## Catalogue delivery integration

Native pending orders contain real sixteen-bit item IDs. The unchanged
post-office creator calls the shared `af_load_item_name` reader at `801969C8`,
which already supports the imported complete English names. No second postal
name patch is needed. The native pending-order loop at `800B6C88` retains its
mailbox receipt gate and packed translated-letter creation.

The combined [shop interaction check](V3_SHOP_INTERACTIONS.md) executes that loop
with two imported pending orders and confirms both complete 164-byte delivered
letters, full captured names, correct attachments, pending-order clearing, and
complete restored English text. Ordinary confirmation/payment remains untested.

The accent-aware reader is installed at startup from the persistent font image.
Its owner is `80450010`, not ordinary heap storage; the exact V2 font/creator
resources remain unchanged. Verification binds that actual owner and reuses
the already verified stock prefix without replaying it.

See the [checkpoint](../docs/checkpoints/V3_SHOPS.md) for exact results and limits.

## Clothing stock integration

The actual donor puts cherry shirt (`24BF`) at position 27 in `cloth_listA`,
inside its 32-item all-season prefix. The complete 144-byte donor list has
SHA-256 `7851eefd2ebb8eeb4ae6b1361a76f0bdf813718b1d68178afa8f48b54c9c51c6`.
It occurs in neither B nor C. The donor seasonal counts are `32,10,11,9,9`.

Native clothing stock is the separate 560-byte resource at VROM `011E5000`,
SHA-256 `7a939815d2f483dec67ea98d01f9d711ef7143ed9e63cf948478b0702f3f3d85`.
Its descriptor starts at `8010DAB8`: `011E5000 011E5230 060001F0`.
A/B/C lists start at offsets `000`, `090`, and `120`; the eleven-word pointer
table starts at `1F0`, and the same five seasonal counts start at `21C`.
Do not overwrite native `24BF`: it is a different garment despite the shared
donor item number.

The native seasonal random-index helper at `800BFAA8..800BFBFF` takes only an
output-index pointer, not the selected list. Its caller at `800BFE4C` retains
the actual list pointer in `s1`. Appending an all-season item only to A needs a
list-aware index adapter; globally raising 32 to 33 would select the wrong
seasonal entries in unchanged B/C lists. Preserve the native season mapping,
single RNG draw, group-to-rarity mapping, special lists, and duplicate filtering.
The [clothing stock adapter](V3_CLOTHING_STOCK.md) appends the expanded A list
and updates only pointer A, retaining the original lists and counts at `21C`.
The resource grows to 720 bytes through the unchanged size-derived allocation
and free paths. Focused seasonal/composition tests and the native stock,
town-rarity, and acquisition check pass. Shop mannequin rendering, catalogue
presentation, and ordinary payment remain work.
