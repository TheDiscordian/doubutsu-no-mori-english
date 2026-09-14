# V3 imported villager umbrellas

Cheri's installed draw record already contains umbrella 3, and Punchy's contains
13. Both match their actual GameCube defaults. No ROM correction is needed.

GameCube ordinary villagers take their umbrella from the saved animal's default
umbrella field; the donor draw-record byte at `+5D` is a special-character
fallback. The actual donor rows still contain the correct defaults for both
pilots, and the native draw converter already copies them. The comment about
that field's use is not evidence that its stored value is zero.

N64 ordinary villagers take the draw-record byte directly. Both constructors
copy `draw+5D` to `actor+85F`: `8097F588` loads `SP+B5`, and `8099F9CC` loads
`SP+AD`, with draw records at `SP+58` and `SP+50`. The eight native instruction
bytes at each consumer are verified in the current cartridge. Native umbrella
takeout reads `actor+85F` and passes that tool number to the existing service.
No executable, actor, or save field changes are needed.

## Asset correspondence

Tool numbers 3 and 13 map to `tol_umb_04` and `tol_umb_14` in both games.
The pinned verifier distinguishes the held assets from similarly named shop
assets. Each complete palette and 2,048 texture pixels match the native asset
after GX conversion. All 56 vertices, including positions, texture coordinates,
and colours, match after removing the GameCube matrix flag. Both canopy and
handle triangles match with material assignments and winding: 18 canopy
triangles and 15 handle triangles apiece.

Native assets `0110A000` and `01114000`, their renderer, and animations remain.
Native canopy batching differs from the GC lists but has identical mapped
geometry. No GameCube graphics commands are copied into the cartridge.

## Verification boundary

The current-cartridge review checks actual source/output hashes, both installed
defaults and full draw-record hashes, both constructor fields, and both complete
assets. Existing draw-loader/constructor-tail execution evidence remains
applicable to unchanged code. Ordinary rain/umbrella animation is checked with
ordinary imported-villager gameplay; it is not yet marked passed.

Move-ins remain disabled. Punchy's actual shirt and animated speed bag remain
unfinished dependencies. Both V2 patchers remain unchanged.
