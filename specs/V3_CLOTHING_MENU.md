# V3 clothing menu routing

## Selected clothing type

The shared full-register item query returns ordinary item type 2 for a selected
imported garment in classification mode. It validates the full item through
the shared category reader, including selected profile and actual resource.
All saved/held item IDs remain `34BF`; no native shirt replaces the artwork or
identity. Missing/unknown garments retain type 3. Native items and selected
furniture retain their existing results.

Furniture range mode and index mode are unchanged. Clothes do not pass the
furniture bounds check or receive an imported furniture index. Only consumers
asking for an item category receive the clothing classification. This connects
existing menu, icon, ground, and field classification detours, not every later
garment renderer or special item consumer.

## Additional tag checks

Three more pairs in the translated tag overlay need clothing classification:

| Address | Consumer |
| --- | --- |
| `808735CC` | Held-clothing animation selection |
| `8087477C` | Eligibility for clothing/other hand destinations |
| `80874CE4` | Cursor destination when carrying clothing |

Each detour preserves the original mask temporary, complete item ID, all other
full-width registers, HI/LO, and stack. It uses the existing register-preserving
query and constructor-relative continuation. The native branches, clothing
subcategory 4, action tables, present/quest handling, and owner sizes remain.

Other raw tag type checks only distinguish categories excluded from shirts:
`80870ADC` rejects fish/insects/other special items, `80872004` chooses the same
hand mode for a shirt on either branch, `80873B34` handles categories 3/13,
`808756F4` handles category-specific tool restrictions, and `80876284` through
`80876404` handle stacked turnips, money, and tools. Inventory `80880F38` also
handles a different category. Those checks remain unchanged; this review does
not declare every non-menu garment consumer finished.

## Memory and composition

ABI 35 uses 672 bytes at `80463C30..80463ECF` for the combined menu and
[player-wearing adapter](V3_CLOTHING_WEAR.md), after the house-gift code and
before villager readers. The first function replaces the shared value query
through an eight-byte entry jump at `80468000`. The existing full-register
wrapper stays at `804680B8`, and all its callers remain at their fixed addresses.
The C query uses a 40-byte frame. Its mode 3 converts valid clothing items to
full texture indices for player animation, with the original zero fallback.
No heap, DMA directory, save field, or
resource allocation grows.

The builder validates the complete current room code, empty destination space,
compiled dependencies, complete tag owner, and relocation file. New windows
must match their exact instructions, have no relocations, not start in a branch
delay slot, and have no incoming control flow into their interior.

Clothing edits apply after the villager-name reader pass to the same final tag
resource. Both families must survive final composition. The build test restores
only the three new instruction pairs and compares the complete resulting tag
with its parent. It similarly restores the shared entry, new code, and ABI to
compare the complete retained resident/ROM resource.

The [checkpoint](../docs/checkpoints/V3_CLOTHING_MENU.md) records native menu
execution and current output hashes. Ordinary wearing, drop/display, shops,
catalogue presentation, and save/restart remain combined gameplay work. Punchy's
defaults remain off, and neither web patcher offers V3.
