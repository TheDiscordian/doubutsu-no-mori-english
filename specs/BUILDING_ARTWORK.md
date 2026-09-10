# English building artwork

## Source and scope

Use the supplied English GameCube REL and its pinned symbol map, with the exact
source identities defined in `tools/title_assets.py`. Convert GX C4 tiled storage
to native row-major CI4; retain every palette index. Never copy Dolphin display
lists into the N64 executable. Source and converted art remain local and ignored.

The first batch replaces twelve textures: front, roof/sign, and side for both
Nook's Cranny seasons; door and main sign for both Nook 'n' Go seasons; and the
main sign/door atlas for both Nookway seasons. Each texture occupies 2,048 bytes.
The N64 destination is the existing object file at VROM `00D5E000`, 611,456 bytes,
SHA-256 `8b0736724abe607a4939686db0d714874d6702072c155f731050049c5795cca2`.
The unchanged palette file is VROM `00D5B000`, 5,104 bytes, SHA-256
`374551b2ecdfb841eb3269e1ac2b6abdd92abf5033d67684b751393cb050bd6c`.

## Bindings and retention

`tools/building_artwork.py` records native texture addresses, scoped GameCube
symbols, palettes, model commands, and vertex arrays. Compare the supplied
model's actual texture command with the declared dimensions. Native display-list
references must load the expected size, format, and row stride; every vertex
position/texture-coordinate pair used by these references must exist in the
matching GameCube model's vertex array. Vertex flags and lighting normals are
not ported. Models, animation, doors, light control, collision, and actor code
stay native.

All used palette indices have the same visible colours in both formats. RGB
under fully transparent entries can differ and remains native. The summer
Cranny palette also differs at two indices unused by all three replacement
textures; those entries remain unchanged. Never replace the shared palette to
make unused colours match. Require exact opaque colours and alpha for every
index that is used.

Install over the corrected `build/v0-hardware-fixes-02` image, not the original
v0 or the independent title preview. Rebuild from the original cartridge with
all prior resource replacements, additions, and virtual moves retained. Check
the complete DMA inventory, unchanged file sizes, every unrelated resource, the
ROM checksum, and reconstruction from the original cartridge plus UPS.

## Remaining work and verification

Nookington's differs substantially in textures, palette, and model layout and
is not a direct atlas swap. Its [main-sign adaptation](NOOKINGTON_SIGN.md) uses
separate source-sized lettering within the native per-building slots, while
retaining all other seasonal building streams. The post office already contains English lettering;
GameCube changes also alter the mailbox/sign design, so keep that work separate
from the shop texture batch. Other signs, bags, buildings, and the remaining
map/inventory/time-setting screen lettering require their own bindings. A
GameCube donor can retain Japanese decorative lettering; importing a donor
does not establish that the entire building has no Japanese text remaining.

Focused host checks cover conversion edges, palette equivalence, actual model
bindings, rejected incorrect inputs, unchanged code/geometry/palettes, retained
translation and conversation fixes, and UPS reconstruction. Unchanged native
asset loaders do not require a new all-seasons gameplay harness. Ordinary visual
inspection and original-hardware acceptance remain separate checks; do not
report extraction or installation alone as completed gameplay verification.
