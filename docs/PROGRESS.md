# Current progress

## Active work

English-first keyboard input, English keyboard graphics and prompts, repeatable
input tests, and a GameCube-style keyboard design. The wider translation work
continues with buffer audits, reference matching, and missing-text coverage.

GameCube line breaks, page breaks, emphasis, and pause timing are the presentation
reference. Do not automatically reflow text to fill a bubble. Deliberate layout
polish follows translation and command handling. The reported atlas-edge defect
in `font-halfwidth.png` remains unresolved; font investigation is paused at the
user's direction. The production build retains the approved spacing metrics.

## Implemented

- Private GitHub repository, pinned reference sources, and local-only inputs.
- Verified extraction of all 3,374 retail DMA entries; checksummed UPS generation
  and application directly to the original 16 MiB ROM.
- Lossless text codec and unchanged round trips for 29 banks, including dialogue,
  choices, strings, mail components, NPC names, and fixed-width item-name groups.
- Proportional Latin rendering for 81 glyphs, at most six pixels advance. Narrow
  `i`, `I`, `l`, and apostrophe advance four pixels. Japanese glyphs are preserved.
- Relocatable dialogue and choice banks, guarded loader patches, command checks,
  source hashes, and conservative runtime expansion bounds.
- GameCube CISO/FST/RARC/Yaz0 extraction and decoding of all 16,273 main messages.
  Fixed-width GameCube item and NPC names are also extracted as local references.
- Reference import retains GameCube presentation commands and restores matching
  N64 actor-demo arguments. Read-only text insertions may differ only when the
  N64 message already supplies the requested fields. Flow commands stay ordered.
- English-first native keyboard, translated name-entry prompts and ten texture
  labels, with the original 6/6/4/10/10 input limits and unchanged overlay sizes.
- Silent isolated ares test runner, debugger memory assertions, controller input,
  repeated scenarios, and incremental message-state recording.
- 33 passing synthetic and retail-input tests. Retail tests require the local ROM.
- Keyboard UI inventory identifies six embedded text entries and ten graphical
  labels, with per-entry source hashes and verified texture formats/dimensions.

## Current reference candidates

The generated pilot contains 8,902 edits. These are candidates, not a claim of
reviewed translation coverage. Accepted reference imports comprise 8,301 dialogue
entries, 221 choices, and 376 string/mail-component entries, plus four original
introductory drafts. Three draft IDs override reference selection.

Main dialogue still has 3,448 rejected entries. Principal reasons are unconfirmed
same-ID matching (1,854), flow/control mismatches (1,251), new text fields (143),
unsupported GameCube commands, and two expansion-bound failures. Another 996
accepted dialogue candidates have conservative layout warnings. Entry-level
rejection and adaptation reports are generated in `build/candidates/`.

238 choices exceed the unchanged ten-byte runtime buffer. Extending ROM storage
does not fix that buffer. General strings, mail, saved names, dates, and item
names have separate restrictions. Unsafe legacy item-name mappings are withheld.

## Validation and release status

Silent emulator runs confirm a four-MiB configuration, active relocated text
loaders, intro dialogue, English-first input, case conversion, single-character
deletion, cursor movement, six-character enforcement, all five mode transitions,
and successful name confirmation. The proportional name-cursor correction passes
the same regression and has been visually checked during entry. Destination-name
entry, its six-character limit, and confirmation also pass. No hardware-certified build or
release candidate exists. Save/reload, travel, mail, board, RTC, calendar, credits,
seasonal events, and original hardware tests remain outstanding.

An observed remaining translation issue is the Japanese town suffix appended by
dialogue insertion command `7F2F`. The keyboard's destination label is English,
but the separate dialogue insertion path still needs translation. Catchphrase,
song, mail, and board editor callers also need their own runtime regressions.

The GameCube-style grid is a separate implementation task; the current keyboard
still uses the N64 radial layout. See [keyboard design](../specs/KEYBOARD.md),
[validation](VALIDATION.md), and [build instructions](BUILDING.md).

Public release requires completed translation review, stability testing,
original-hardware results, and third-party provenance review. Only patches and
original tooling may be published; ROMs and extracted assets stay local.
