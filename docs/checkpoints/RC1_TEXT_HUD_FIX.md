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

The existing full regression process remains active, advancing through the
alphabetical suite. Its log is `build/v1rc1-regression.log`; failures remain
unclassified beyond the previously verified stale fixtures. Do not restart
the entire suite or mark it passed. New follow-up tests are run separately;
the earlier process started before those tests existed.
