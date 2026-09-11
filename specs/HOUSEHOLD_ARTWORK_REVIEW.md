# Household and igloo-detail artwork review

Resolve a fixed set of 28 unreviewed household images and the unresolved igloo
detail `0138DA28`. This is source/current-asset inspection, not a gameplay test
or old-build replay. Keep cartridges, patches, game inputs, and saves unchanged.

`tools/review_household_artwork.py` uses the verified original N64 ROM, exact
current RC8, supplied decoded GC REL, pinned symbol map, and existing artwork
inventory. Bind every selected native texture's complete dimensions and bytes
to its load/tile commands. Read the actual preceding palette load and TLUT
count: sixteen entries for CI4 or 256 for CI8. Require each selected complete
owner to remain native in RC8 before inspecting it.

For household images, bind the named GC texture and its palette through actual
same-module data relocations within the named model. Require the correct palette
load count and no intervening call/return. Compare complete decoded RGBA values,
ignoring RGB only when both pixels are fully transparent. Record mismatches and
emit a separate donor view rather than silently calling CI-index matches colour
matches. Visual classification remains an explicit inspection step.

The inspection decoder supports CI8 with a complete 512-byte palette and one
unsigned index per texel. GC CI8 storage uses 8×4 tiles and RGB5A3 palettes;
native palettes use RGBA5551. Preserve CI4, intensity, and alpha semantics.
Use small synthetic tests for the new format, not old-build test scenarios.

The igloo detail uses native CI4 16×16 and twenty vertices loaded at `0138BAC8`.
Record those vertices and the twelve following triangles so the material's role
is not guessed from a tiny texture alone. A same-sized GC storage allocation
does not establish a donor: `rom_kamakura_nabe1` is actually CI4 8×32 on different
geometry. Do not substitute that pot surface or claim the igloo layout is an
exact English-GC import.

Write PNGs and the decoding/source receipt only to a fresh ignored directory.
Commit the inspection script, decoder change, tests, and findings. No English
application credit, new candidate, or runtime/hardware evidence follows merely
from a completed neutral-image review.
