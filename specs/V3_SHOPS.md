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

The global category entry at `800C05E0` recognizes only enabled registered
`3xxx` furniture, returning category zero. Unknown or disabled imports return
minus one; all original types invoke the retained native implementation.
The original argument is preserved for that fallback.

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
