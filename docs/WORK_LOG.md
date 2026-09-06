# Work record

## 2026-09-06: reference framework and English-first keyboard

- Extended reference import across eleven message/string/mail-component banks.
  The generated pilot contains 8,902 edits: 8,301 dialogue reference candidates,
  221 choice candidates, 376 other candidates, and four original drafts.
- Added auditable GameCube article-suppression and N64 actor-demo adaptations.
  Added the dialogue-only existing-text-field policy. Branches, waits, RNG, and
  embedded-mail operations remain strict. No automatic reflow was introduced.
- Added fixed-width GameCube name extraction using pinned REL symbols. Withheld
  legacy item candidates whose offset notes do not match the supplied image.
- Added input preparation, reference-pin checks, archive safety tests, original
  bank integration tests, and rejection of an empty first cumulative-table entry.
- Paused the font-atlas investigation following the user's explicit instruction.
  The diagnostic probe is retained as work history, is not a build dependency,
  and does not establish a fix. Default renderer output retains zero left padding.
- Mapped the N64 keyboard and name-entry overlays. Patched English mode as the
  default, translated five prompts and the destination suffix, and generated ten
  English texture labels from unscaled local retail glyphs. Preserved overlay
  sizes, pointer relocation files, callbacks, and 6/6/4/10/10 field limits.
- Added simultaneous controller inputs, analogue-stick bindings, and keyboard
  memory snapshots to the isolated silent test runner. A first English-keyboard
  run ended externally with exit 143 before reaching the editor; this is not a
  passing test or evidence of a game crash. A bounded transient user service is
  used for the rerun so the test is independent of the invoking shell lifetime.
- `make pilot` passes 31 tests and regenerates the candidate build. ROM SHA-256:
  `c851db851fc4426353d3cad2ea68c122d0ea71b6d40c0c09523d92c9ccf1330e`.
  UPS SHA-256:
  `407f7772c434203994d4fbb1cdcbf23393c4130662a42b1eb4bcee00823e5db1`.
- Documented the GameCube 10×4 keyboard reference and the separate grid port.
  The grid is not implemented, and original hardware remains untested.

### Keyboard input and cursor validation

- `build/smoke-english-keyboard-03` passed 62 recorded steps in silent ares 148
  with four-MiB RAM. Memory assertions verified mode 3 on opening, `CCC` entry,
  `CCc` case conversion, one-character deletion to `CC`, left/right cursor
  movement, six-character enforcement after excess insertion attempts, and mode
  transitions 3→4→0→1→2→3. Name confirmation returned to Rover messages
  `2ACA` and `2AD6`.
- Replaced the name cursor's fixed-cell position calculation with the existing
  proportional prefix-width routine. Assembled and independently checked the
  96-byte MIPS patch; removed only its two obsolete constant relocations.
  `build/smoke-keyboard-cursor-01` passed the same 62-step regression, and entry
  captures confirmed the caret follows the text. No font textures changed.
- Added verification of all ten RDP texture descriptors and strict rejection of
  unsupported label characters. Added an inventory of sixteen embedded/graphical
  keyboard UI entries. The test suite passes 33 checks, including four optional
  retail-input integration checks.
- Rebuilt pilot ROM SHA-256:
  `344d4290c7877f446f01175d9cffb90fcead5bb064f7cde148c8c18c5b9f701a`.
  UPS SHA-256:
  `32a3c109dae53858a0ecf7d4bf5f0d5c85ac8f7cbc0cdaea7f6653cd33baed6c`.
- `build/smoke-keyboard-town-01` passed the extended 93-step regression in
  5 minutes 14 seconds. Destination naming opened in English mode, rejected
  excess letters beyond `AAAAAA`, and returned to Rover dialogue after
  confirmation. The destination prompt and translated “town” label were
  visually checked. Four-MiB RAM remained confirmed at test completion.
- The post-destination dialogue exposed a separate untranslated path: `7F2F`
  appends the Japanese town suffix inside messages such as `2ACE`. This is
  recorded for the main translation work; the keyboard patch does not alter that
  insertion routine. Save/reload and hardware testing remain outstanding.
- Repeated the complete `make pilot` pipeline with 33 passing tests and the same
  output hashes. Confirmed the GitHub repository remains private.

Generated assets, logs, screenshots, ROMs, patches, and reference text remain
local under ignored `build/` and `local/` paths. Current status belongs in
`PROGRESS.md`; this file records completed work and test observations.
