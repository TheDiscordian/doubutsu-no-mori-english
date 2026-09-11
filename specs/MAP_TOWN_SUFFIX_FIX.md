# Map town-name suffix

The map has an independent 32 × 16 I4 bitmap reading `むら` at VROM
`00AAE1C8`, inside asset `00AAD000`. It is separate from the message-string
suffix and the inventory suffix. The native texture load at asset offset
`1178` points to segment `0C:0011C8` with the matching 32 × 16 tile size.
The existing material uses texture intensity for opacity.

The English GameCube `mMP_set_dl` draws the saved town name without a village
suffix. The correction makes this N64-only 256-byte bitmap transparent.
The complete current asset, original lettering, and texture reader are hash/
instruction guarded. All other pixels, display lists, vertices, native code,
map names, allocations, and saved formats remain unchanged.

`python3 tools/map_town_suffix_fix.py` applies the correction to current V2-06
and creates a fresh V2-07 ROM, original-input UPS, and build receipt. It retains
every other current DMA resource and checks patch reconstruction and the boot
checksum. This is a data-only follow-up; it does not rebuild the keyboard or
repeat old gameplay tests. The released trailer is left unchanged.
