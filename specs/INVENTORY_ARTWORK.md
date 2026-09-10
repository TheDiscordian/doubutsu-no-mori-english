# Inventory heading artwork

## Resources and layout

The inventory asset file is VROM `00A30000`, 64,544 bytes, SHA-256
`d39cedf24822c4b3ad6b28944eda1dc7a90c478a1bf18529b2f70fb4cc1b73ed`.
The native renderer uses segment twelve. CPU inventory/tag owners, item names,
selection, and saved pockets are separate and remain unchanged.

The supplied GameCube labels are I4, 64 by 16: Items at `.data:0043B960`,
Letters at `.data:0043BB60`, and Bells at `.data:0043BD60`. Their actual REL
model texture pointers are at models `.data:0043E398`, `.data:0043E3C8`, and
`.data:0043E3F8`; each model is 48 bytes. The source identity and pointer checks
are the same as the other supplied GameCube artwork batches.

| Label | Native texture VROM | Native vertex VROM | Donor vertex index |
| --- | --- | --- | --- |
| Items | `00A3AD00` | `00A360B0` | 56 |
| Letters | `00A3AF00` | `00A36170` | 60 |
| Bells | `00A3B100` | `00A361B0` | 64 |

Donor vertices start at `.data:0043CFE0`. Both native inventory and GameCube
vertices use screen units directly; do not apply the map asset's tenfold scale.
Port the three source quad positions and texture coordinates, matching corners
while retaining native winding, vertex flags, and colours. Items moves from a
vertical Japanese heading to the source horizontal heading above the pockets.

The native Items texture is 16 by 64 rather than 64 by 16, with the same
512-byte storage. Compile its replacement load into the existing 56-byte
command range at `00A371A8`, using `overlays/inventory/artwork.c`. The other
two label loads keep their complete native command sequences. Use the source
Items primitive colour `(120, 120, 225, 255)` at native `00A371A0`; the other
two heading colours already match. Preserve all source texture intensities.

The native separate `ベル` unit at `00A3AA00` becomes a transparent 256-byte
texture: the GameCube inventory uses one Bells heading, without this duplicate
Japanese unit. The amount's runtime drawing and position do not change.

## Boundaries and checks

Install over the English map/shop candidate with both first-job fixes retained.
Keep resource sizes, palettes, allocation, every other DMA resource, and save
layouts. Verify exact English pixels, donor pointers, geometry, compiled native
load, full cartridge/UPS reconstruction, and negative source/layout cases.
Ordinary appearance/navigation and hardware are not established by these host
checks. No new exhaustive menu harness is required for unchanged CPU owners.

The separate `むら` town suffix at `00A300B8` also becomes transparent. The native
normal-frame function at `8087FA80` measures the saved town name, positions the
suffix, and emits its `0C000040` model call at `8087FCD0..8087FCDC`. The supplied
English `mIV_set_normal_frame_dl` omits that suffix, and `mIV_set_normal_dl`
draws the actual land/player names independently. Keep the native CPU code and
live name rendering; only remove the redundant Japanese suffix art.

The unchanged item artwork includes separate bags/signs, and collection pages
have their own headings. These remain in the broader image inventory; the
ordinary pocket-screen heading batch is not a claim that every inventory tab
and item picture is fully English.
