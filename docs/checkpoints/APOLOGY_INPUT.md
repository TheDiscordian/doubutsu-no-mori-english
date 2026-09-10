# Complete sun/skull apology input

## Implemented

- Exact GC targets `U R my ☀!` and `Reset = 💀`, ten native bytes each, in the
  relocated general bank. Source and reference hashes bind both complete values.
- Apology-only sun, skull, and equals keys, complete-token insertion/deletion,
  byte-boundary navigation, protected case exchange, native confirmation, and
  cleanup. Other editor modes retain their existing handlers and saved formats.
- Complete previous owner and letter editors, with the same DMA ownership and
  a 256-byte shared-pool increase. The actual build retains four-MiB memory bounds.
- Actual-installed input/font/matcher verification in combined translation
  accounting. These twenty Japanese source characters receive credit once.

Build recipe: `bash tools/build_apology_input_pilot.sh`.
ROM/UPS: `build/apology-input-pilot/animal-forest-halfwidth.{z64,ups}`.
The 32-MiB ROM SHA-256 is
`be3636e5a32b7bf628dd7ad9ed492b577b5c55f4d89c14a89dde24f48c074282`;
the UPS SHA-256 is
`e3ac9ca063c6ae23a6cbb6b3bb2871e32bdbe2f569cb33a6699547644f114815`.
The patch reconstructs the complete ROM from the verified original input.

## Verification

All five focused tests pass: sanitizer checks of the editing core and scoped
adapter, exact reference/permission/allocation checks, independently reproduced
MIPS image and relocation validation, and complete cartridge/UPS/counter checks.
All twelve counter regressions and eight prior owner-editor regressions pass.
All unrelated resources match `build/reserve-strings-pilot`; main code changes
only the pool word, and owner metadata changes only the editor row. General-bank
changes are limited to the two exact targets. Original font pixels are unchanged.

The first silent native fixture completes both exact entries, atomic edits,
Done callbacks, case-sensitive acceptance/rejection, and all three correct key
texture draws. Its final guard check detects an incorrectly placed fixture
guard in the native loader's relocation staging area. The fixture also needs
separate space for the submenu owner's complete 67,376-byte BSS. The corrected
layout reserves disjoint image/BSS/relocation ranges before the editing context;
production code is unchanged. The single corrected retry cannot allocate its
separate 196,608-byte fixture (`8009BFC0` returns zero). The fixture rejects that
result before loading images or making further writes. This is a test allocation
failure, not an observed game crash or production-editor overflow. Both attempts
remain incomplete; neither establishes restored-checkpoint or complete guard
success. No further standalone retry is made under the v0 testing limits.

Evidence is retained in `build/apology-input-native-01` and
`build/apology-input-native-02`. The first attempt records fifty native calls,
including both ten-byte entries, accepted/incorrect matcher results, three actual
key draws, and unchanged complete live-save data. Its thirty-three passing
assertions do not waive the later guard failure. The next useful check is ordinary
keyboard entry through the existing submenu allocation during the combined v0
smoke, without allocating a second complete submenu owner alongside a synthetic
copy. The corrected fixture's required image/BSS/staging ranges are explicit and
checked for overlap.

Ordinary controller navigation, whole keyboard/window interaction, and save/restart
remain in the bounded combined v0 smoke. Human playthrough and original hardware
follow the handoff. Remaining main work includes accented item names and residual
general/letter text; the GameCube-style keyboard and title artwork remain v1.
