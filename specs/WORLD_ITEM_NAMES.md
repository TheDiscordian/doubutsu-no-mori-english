# Complete world item labels

## Storage and consumers

The original state at `801446A0` is forty bytes. Its ten-byte name at `+1D`
ends immediately before the live draw flag at `+27`. Do not widen this field.
The constructor at `800CBF90`, item loader at `800CC324`, width block at
`800CC32C..800CC344`, and font call at `800CC9A8` form one integration.

A variant of the existing startup-owned font image holds a separate sixteen-byte
name and its pixel width. Reset clears this state on every native constructor;
item changes retain the original ten-byte write and load the complete English
resource into the separate field. Failed loads show `Name unavailable`, never
stale or silently shortened names. Drawing and per-frame measurement do no DMA.

Replace the native character-count calculation with proportional pixel width,
trim only trailing storage padding, and keep the native mesh's scale formula
`max((pixels / 12 - 2) / 8, 0)`. Centre the complete line on the existing bubble.
The GameCube reference uses measured width and the same `0.875` text scale;
its different mesh coefficients are not transplanted into the N64 artwork.
Native vertical placement, animation phases, delays, fade, colours, field/item
conditions, and saved data stay unchanged. No text reflow or wording changes.

## Ownership and installation

The unchanged system-heap font loader owns code, pixels, and transient state
until reset, across scene teardown. The variant stays within its existing
`0x3000` image and `0x1000` relocation bounds. It does not consume the full
resident module or enlarge submenu allocations. Original font profiles remain
valid and retain their existing source identities and pixels.

Validate the original world update/draw region, every replacement instruction,
the complete item resource, and the exact resident full-name entry before
installation. At startup, check all world hooks before invoking the existing
guarded font installer. Install world hooks only after that succeeds, then
maintain both instruction and data caches. Configured startup failure keeps
the existing fail-closed loader behaviour.

## Bounded verification

Check host storage guards, reset/re-entry, full and short names, resource
failure/recovery, width and centring, preserved draw arguments, and installer
failure atomicity. Check compiled relocation and independent build agreement,
complete font/resource retention, full ROM/UPS reconstruction, and unchanged
translation accounting. Queue ordinary floating-label appearance and scene
transitions in the combined v0 smoke; do not create an exhaustive label harness.
