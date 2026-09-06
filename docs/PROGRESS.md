# Current progress

## Active work

Expand the text replacement framework, audit runtime buffer limits, match the
extracted GameCube English script, and identify remaining translation work.
Line wrapping and paragraph balance are a later polish pass, after text and
command handling are settled. Preserve explicit page/branch commands during
reflow; use the proportional glyph metrics for line widths.

## Complete

- Private GitHub repository created and initial documentation pushed.
- Retail ROM SHA-256 verified; all 3,374 DMA entries extracted without errors.
- Legacy UPS applied with source, target, and patch CRC validation.
- Lossless text codec handles Japanese glyphs, Latin glyphs, and command tokens.
- All extracted text entries and bank tables pass unchanged round trips.
- Inventory covers 11,752 dialogue entries, 460 choices, 544 entries each in
  the main mail/header/footer banks, 1,562 strings, five 384-entry NPC mail
  component banks, and 220 original NPC names.
- Experimental halfwidth build changes 81 Latin glyphs to at most a 6-pixel advance.
  Japanese/symbol textures remain identical to the source.
- Narrow glyphs use ink width plus one spacing pixel: `i`, `I`, `l`, and the
  apostrophe advance four pixels. Shared drawing/measurement tables agree.
- Silent isolated ares tests boot the ROM, accept controller input, and render
  original English K.K. introduction drafts. Message-bank relocation is confirmed
  by reading the active loader instructions in emulator memory.
- English GameCube CISO, FST, RARC, and Yaz0 extraction succeeds without expanding
  the sparse disc. All 16,273 dialogue entries decode without command errors.
- Exact visible-text matching through the legacy script identifies 9,440 unique
  GameCube references for N64 dialogue. These remain unapproved candidates.
- Generated UPS applies directly to the original 16 MiB ROM and reproduces the
  32 MiB experimental build. No manual ROM extension is needed.
- Twelve synthetic tests cover corrupt patches, bounds checks, byte order,
  malformed Yaz0 streams, character collisions, command boundaries, and tables.
- CIC 6102/7101 checksum independently matches `ipl3checksum` and retail header.

## Remaining

- Expand text banks and audit per-entry runtime buffer limits.
- Add fixed-width item names, embedded UI strings, graphics, and credits to inventory.
- Audit text coverage, crashes, menu constraints, and save compatibility.
- Improve GameCube matching and audit every reused entry against N64 semantics.
- Translate and review all remaining text and graphics.
- Polish line wrapping, page balance, punctuation, and text alignment using the
  final glyph widths; do not conflate this with translation completeness.
- Complete silent emulator regressions and an original hardware test matrix.
- Prepare a patch-only public release after validation and provenance review.

## Release status

No release candidate exists. `build/halfwidth/animal-forest-halfwidth.z64` is an
experimental renderer build with Japanese text. Original hardware validation is
outstanding. Legacy ASCII-looking text is only a candidate, not reviewed English.
