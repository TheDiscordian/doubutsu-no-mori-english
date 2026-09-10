# English shop artwork checkpoint

## Installed candidate

`build/shop-artwork-02/animal-forest-halfwidth.z64` contains twelve imported
GameCube textures for Nook's Cranny, Nook 'n' Go, and Nookway, including both
summer and winter. It retains both first-job conversation fixes, the Shrine
correction, and every preceding English resource. The separate title preview
is not included. ROM SHA-256:
`507ddfe5ed585bcd6e20fbab44f7247315339a9c90b66dacec03b1e6b22fbc3a`.
UPS SHA-256:
`bd2ff87dd8b178ba200bc51a35bf75c6bca2828eff3d8c7053f698efe237d9b3`.
The cartridge remains 32 MiB with four-MiB RAM use and unchanged save formats.

The batch changes 3,154 texture pixels. Native models, palettes, animation,
allocation, and executable instructions remain unchanged. All 328 vertex uses
associated with the twelve imported atlases match GameCube positions and
texture coordinates; all twelve actual donor REL texture pointers are checked.
Every visible palette entry used by the replacements matches the donor. Hidden
RGB and unused palette entries remain native. [The specification](../../specs/BUILDING_ARTWORK.md)
records the source, format, bindings, and boundaries.

## Verification and limits

All five focused tests pass in 7.595 seconds. They cover exact texture indices,
all model bindings, rejected source/shape/pointer/coordinate mismatches, visible
palette equivalence, preview decoding/PNG checks, complete cartridge/resource
retention, both existing conversation fixes, and complete UPS reconstruction.
The scripts compile and the source diff passes whitespace checks. The preview
PNG files decode the installed native CI4 bytes; they are not in-game renders.
No new gameplay harness or user-save operation is performed for unchanged
asset loaders. Ordinary appearance, all live lighting states, and original-
hardware acceptance remain pending.

The corrected v0 handoff stays at `build/v0-hardware-fixes-02`, with its private
patch package. The artwork candidate remains separate while the screen/artwork
batch continues; it is not the independently tested title build.

## Next implementation

The map's baked `ごあんない` header is at VROM `00AB4B60`, inside asset file
`00AAD000`, and has the same 64-by-16 I4 dimensions as the GameCube `TOWN MAP`
header at `.data:004B45C0`. Its native display-list load is at `00AB4368`.
Native `ばんち` and `ちょうめ` textures are at `00AB8460` and `00AB8260`;
their replacement must respect the live coordinate labels, not duplicate an
English word over both. Trace the screen layout before completing that part.
The previously corrected Shrine label is runtime text and remains separate
from these textures.

Continue map, inventory, and time-setting screen artwork. Nookington's needs
an explicit model/palette adaptation, and the post office's GameCube mailbox
changes are not a text-only atlas replacement. Japanese decorative lettering
can remain even in a GameCube donor; no whole-building completeness claim is
made from these twelve installed textures alone. Other signs/bags, the English
title integration, and the GameCube-style keyboard remain in the queue.
