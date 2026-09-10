# Nook 'n' Go hiring-notice correction

The artwork review found the native Japanese hiring notice still visible in
V1RC1. The English GC version omits that notice, retaining the same background
wall. The [source contract](../../specs/SHOP_HIRING_NOTICE.md) binds the actual
models, texture readers, palettes, vertices, and the covered wall area.

The correction replaces only the notice's two-triangle command with one
independently compiled SDK no-op. No CPU code, save field, allocation, wall
surface, shop rule, other triangle, texture, palette, or vertex is modified.
The unused original notice texture remains in local cartridge storage; it no
longer draws. The supplied English room has no corresponding English placard
to import.

## Artifacts

- Follow-up ROM: `build/v1-shop-notice-fix-03/animal-forest-title-preview.z64`.
- ROM SHA-256: `5ccd35ba077e3abf1d1ab90d919c095343ff404884b504ca14ea709a04ec1dfc`.
- UPS SHA-256: `bd69d7d44260f4c4a0f8ce2f458775600dda93714059b5eca804c8d0ceb6d55a`.
- Changed room SHA-256: `c3b0093356c0a67b0a5dd75e00bba95e079bfa37a4a04fc81b626bbfeaa0e955`.
- Original V1RC1 remains `build/v1rc1/Animal Forest English V1RC1.z64`, SHA-256
  `63794bd31fe5c7c9ae786b15a41d6a80c2390c890b2edd963ace9a9e5edb8d37`.

This is a separately tracked post-V1RC1 correction, not a replacement or renamed
V1RC1. Both cartridges are 32 MiB and require an Expansion Pak. Existing user
saves and earlier artifacts remain unchanged. The same correction output is
reproduced in `v1-shop-notice-fix-02`; `03` also records source/compiler identity.

## Verification

Four focused tests pass in 9.530 seconds, including fresh native SDK command
compilation in a temporary build directory. They verify native/GC model identity,
actual donor pointers, matching wall pixels/palette/UVs/lighting, coverage of all
four notice corners by the donor wall, exactly two omitted triangles, and one
eight-byte command change. Full reconstruction preserves every unrelated DMA
resource and native identity/size, and UPS application reproduces the exact
follow-up ROM. The command is compiled from the existing fishing artwork's
`gsSPNoOp()` section using the pinned public MIPS image.

The first build guard incorrectly rejected other English-room trim at the same
Z depth but well to the left of the notice. Inspection placed all that trim
at X 1280..3840, outside the notice's scaled X 4728..5512. The corrected guard
checks the actual placement instead of forbidding that depth across the entire
room. That rejected build produced no cartridge. This was an implementation
guard correction, not a game crash or a native test retry.

Ordinary room appearance remains hardware/playtest acceptance work. No new
emulator scenario, audio playback, percentage-tool work, or public publication
is performed for this eight-byte graphics correction.
