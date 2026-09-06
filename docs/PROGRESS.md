# Current progress

## Active work

Validate the halfwidth renderer in a silent emulator session, expand the text
replacement framework beyond original byte budgets, and audit the legacy script.

## Complete

- Private GitHub repository created and initial documentation pushed.
- Retail ROM SHA-256 verified; all 3,374 DMA entries extracted without errors.
- Legacy UPS applied with source, target, and patch CRC validation.
- Lossless text codec handles Japanese glyphs, Latin glyphs, and command tokens.
- All extracted text entries and bank tables pass unchanged round trips.
- Inventory covers 11,752 dialogue entries, 460 choices, 544 entries each in
  the main mail/header/footer banks, 1,562 strings, five 384-entry NPC mail
  component banks, and 220 original NPC names.
- Experimental halfwidth build changes 81 Latin glyphs to a 6-pixel advance.
  Japanese/symbol textures remain identical to the source.
- Generated UPS applies directly to the original 16 MiB ROM and reproduces the
  32 MiB experimental build. No manual ROM extension is needed.
- Twelve synthetic tests cover corrupt patches, bounds checks, byte order,
  malformed Yaz0 streams, character collisions, command boundaries, and tables.
- CIC 6102/7101 checksum independently matches `ipl3checksum` and retail header.

## Remaining

- Complete silent emulator verification; the first debugger session disconnects
  before returning a query response. Diagnose the harness before drawing game
  stability conclusions.
- Expand text banks and audit per-entry runtime buffer limits.
- Add fixed-width item names, embedded UI strings, graphics, and credits to inventory.
- Audit text coverage, crashes, menu constraints, and save compatibility.
- Extract English GameCube references if supplied and match them conservatively.
- Translate and review all remaining text and graphics.
- Complete silent emulator regressions and an original hardware test matrix.
- Prepare a patch-only public release after validation and provenance review.

## Release status

No release candidate exists. `build/halfwidth/animal-forest-halfwidth.z64` is an
experimental renderer build with Japanese text. Original hardware validation is
outstanding. Legacy ASCII-looking text is only a candidate, not reviewed English.
