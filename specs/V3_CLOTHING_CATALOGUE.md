# V3 clothing catalogue

## Identity and ownership

The clothing page preserves all 245 original entries, their ordering, and their
native ownership. It appends the imported cherry shirt as entry 246. The actual
donor catalogue contains mannequin index 682 once, at position 183; its complete
494-byte table, pinned REL, and source symbols are verified before conversion.

The catalogue uses its existing `(item - 1000) / 4` encoding. Display `3AFC`
becomes catalogue index 2,751 (`ABF`), distinct from room index 1,727 (`6BF`).
Its ownership call uses the existing canonical clothing query, so all display
orientations share pocket `34BF`'s clothing bit `BF`. Missing or uncollected
imports remain absent. The 444-item category limit and nine-page name cache
remain unchanged; a new clothing row is not a decorative-furniture row.

The original descriptor at `808AF7BC` points to the appended 492-byte list;
its count at `808AF7C0` is 246. The category-loop call at `808A952C` uses the
checked imported ownership reader, retaining the original bit function for
native clothing, wallpaper, flooring, stationery, music, and other categories.
Native `1000 + index * 4` returns the complete display ID without another hook.

## Preview and ordering

The existing expanded profile reader loads the real native mannequin under
the stable display profile. Its geometry, shirt texture/palette, constructor,
lighting, and animation initialization use the native preview path and buffers.
A wrapper around `808A627C` calls the complete native initializer first, then
applies its clothing presentation to the selected display: scale 1.0, viewing
height 38, and model Y -4. Native previews return unchanged.

The wrapper's bridge retains the original stack prologue and rejoins at
`808A6284`. The complete original function is checked before editing, and its
internal branches remain untouched. The catalogue's ordinary-stock query maps
the selected display to pocket `34BF`, clothing category 2, and the original
common/uncommon/rare query. Price comes from the installed 380-Bell reader.
Ordering uses the shared inverse conversion to retain pocket `34BF`, not a
mannequin identity in an order or delivered letter.

## Bounds and verification

ABI 44 identifies the clothing catalogue integration. Its catalogue image is
56,560 bytes, including the 2,880-byte suffix; relocation occupies 720 bytes.
The rounded shared-menu requirement is 274,176 of the existing 274,560-byte
reservation, leaving 384 bytes. No pool, saved format, profile, or resident
allocation grows. The clothing initializer and availability helper each use
a 32-byte stack frame. The appended garment list is at `808B3BF8`, the wrapper
at `808B3304`, and its original-function bridge at `808B34D4`.
Complete source checks, relocations, descriptor updates, and composition remain
mandatory. Two focused tests and the initial 71-step native check pass, covering
all 246 rows, full names, selection, price, presentation, complete 4,128-byte
garment/model loading, disabled dependencies, original retention, restored state,
and guards. No GPU appearance, ordinary payment/delivery, hardware compatibility,
or complete playable villager claim follows. The
[checkpoint](../docs/checkpoints/V3_CLOTHING_CATALOGUE.md) records exact evidence.

Save/profile compatibility with ABI 43 is expected in both directions, but no
new ordinary cross-build reload is implied. Older profiles without the display
dependency reject new saves. Both web patchers stay V2 until user testing and
explicit approval.
