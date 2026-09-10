# V1RC1 text/HUD follow-up

The user reports V1-13 through V1-16 on the actual V1RC1 cartridge. The keyboard
sounds are accepted; panel appearance is not. The new text/HUD batch implements
the three non-keyboard findings without replacing the user's V1RC1 artifact.

`build/v1rc1-text-hud-fix-01/animal-forest-title-preview.z64`:

- SHA-256: `40d2478cdea8cbb808ae1d1dd7e65184bb9efe11215524a6411efff3efc15378`.
- UPS: `7b4504d0d41cca444d015eaed1040a4b24772adeffb7972826abbe90e853c3b5`.
- 32 MiB; Expansion Pak required; save format unchanged.
- Predecessor: hiring-notice correction `5ccd35ba077e3abf1d1ab90d919c095343ff404884b504ca14ea709a04ec1dfc`.

The first-time-player choice now copies the complete GC `I'm new` into its
existing expanded row. The actor gains sixteen aligned bytes; its two changed
instructions and retained 188 relocations pass checks at two load addresses.
The shop unit receives exact GC `Bells` pixels without moving its amount or
heading. PM edge wrapping is corrected by independently compiled clamp flags;
the raw PM bitmap proves how the first-column descender can repeat after `m`.
The [specification](../../specs/RC1_TEXT_HUD_FIX.md) records exact bindings.

Four focused tests pass in 10.418 seconds. They compile the graphics command
from current source, compare complete visible donor pixels, verify the reported
edge condition and corrected tile flags, check actor bounds/relocations, and
verify the complete patch and preservation of unrelated resources. The build
also passes independently. No audio is played or user-facing render opened.
This is not ordinary gameplay or original-hardware revalidation.

Keyboard V1-14 remains pending. Direct GC model inspection identifies the
bottom-right panel as vertically reversed in the current renderer. The native
quad approximation also discards the donor's one-pixel corner offsets, and
the oversized key panel is being used behind control hints that belong outside
the original GC key area. Correct the actual panel/UV layout, contain control
hints, and consolidate supported symbol pages. Preserve the accepted sounds
and existing proportional text editor. Do not package this partial batch as
the completed combined follow-up.

The user's clarification identifies the top-right segment as too low and the
bottom-right as upside-down, accepts the GC origin of the design, and adds
poor placement of `_`, `1`, and `0` inside keycaps. Fix the shared key-label
positioning rather than only those examples. The current atlas inspection
finds both digits have bounds X=0..4/Y=2..13 and advance six, but their ink
distribution differs: `1` is strongly right-heavy. Underscore occupies X=0..4,
Y=14..15; the current key renderer's Y+1 origin puts its last row outside a
sixteen-pixel key. Review actual ink placement and typographic baseline without
changing the global font or reviving the deferred atlas-edge investigation.

Useful verified keyboard source details:

- GC panel quads at `.data:0041FFF0`: lower-left uses texture B with
  S=0..2048/T=0..1024; upper-right uses B with S=2048..0/T=1024..0;
  lower-right uses A with S=2048..0/T=1024..0 (the installed code wrongly
  uses T=0..1024); upper-left uses A with S=0..2048/T=0..1024.
- The donor's upper-right/lower-right sit one pixel above the left pair.
  The installed equal-half rectangles omit that offset. Donor key-panel bounds
  are X=55..235/Y=129..202; native keys already use its exact forty placements.
- Native hints are at Y=202/215 below the key rows. Their bounds must be checked
  against the visible background, not just the 236×114 rectangular allocation.
- Source `overlays/keyboard_grid/core.c` uses `page<3` and modulo three;
  tables four/five are symbols/marks. Consolidate supported entries without
  losing newline/space or the two apology-only extended glyphs. Preserve the
  accepted input/page sounds and native saved capacities.
- Background compilation already owns an appended suffix. Prefer replacing
  that owned suffix to retaining dead old artwork and consuming another full
  allocation. The existing pool immediate is `7620`, close to its signed bound.
  Any replacement must preserve earlier pixel-editor hooks and relocations.

The prior 30,272-byte editor prefix is recoverable from the current ROM alone:
restore the draw call `808882D8` from `RAM+30600` to `RAM+25748`, then retain
the 542 flattened relocations below offset 30,272 and rebuild the relocation
header/footer. This is executed read-only and reproduces the complete prior
owner hash `231fc18359e3ae7c0031aa4571a436f7cdb18c0898a5adfbbbeac94c5149df9d`
and relocation hash `db23c6b194a7beef0221ab3c235b99fe14740311fa120ad9df6a35f471fe570a`.
No historical compiled directory is needed to recover that prefix. The two
existing page-count instructions are verified as `8088AC0C:2C630003` (validity)
and `8088B074:24030003` (modulo divisor); changing each final immediate to two
preserves all function locations. These changes are not yet installed.

The original two symbol tables contain 24 distinct supported key codes after
deduplication, including newline/space and the apology-only sun/skull. One
forty-key page has sufficient capacity without removing any supported symbol.

Raw GC controller-background images `gc-keyboard-control-{a,b,c,d}.png` and
`gc-keyboard-bottom.png` are decoded in `build/artwork-inspection/`. They are
background silhouettes, not translated button labels. The user clarification
does not require a new GameCube-controller redesign; prioritise the identified
corner/label defects and preserve the established N64 controls.

The existing full regression process remains active, advancing through the
alphabetical suite. Its log is `build/v1rc1-regression.log`; failures remain
unclassified beyond the previously verified stale fixtures. Do not restart
the entire suite or mark it passed. New follow-up tests are run separately;
the earlier process started before those tests existed.
