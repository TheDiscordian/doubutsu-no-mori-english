# Validation requirements

## Automated checks

- Verify source identity and all DMA bounds before patching.
- Preserve unchanged text-bank round trips, IDs, and overlay allocations.
- Reject stale patch guards, unsafe controls, and entry/bank overflows.
- Re-extract every replacement and verify the generated UPS round trip and CIC
  checksum. Preserve the source ROM region except checksum and DMA metadata.
- Keep keyboard input limits, state size, and callbacks intact. Preserve each
  relocation not deliberately replaced by an audited code patch.
- Keep graphics edits inside declared texture spans; never resize neighbours.
- Record candidate provenance, command adaptations, rejection reasons, and layout
  warnings independently of translation approval.

## Emulator matrix

Use isolated saves and disabled audio. Record the exact ROM SHA-256 and emulator
version. Four-MiB RAM tests precede Expansion Pak tests.

| Area | Required evidence | Current status |
| --- | --- | --- |
| Boot and intro | Rendered dialogue, advancing messages, active loader instructions | Tested in ares 148 |
| Four-MiB memory | `osMemSize` at `0x80000318` equals `0x00400000` | Tested |
| Name-entry opening | Fresh-town intro reaches the native editor | Tested |
| English keyboard | Default ABC, case, delete, cursor, confirmation, all modes | Tested with memory assertions in ares 148 |
| Name cursor geometry | Rendered prefix width, mixed-width letters, correct selection position | Basic entry visually checked; mixed-width runtime cases outstanding |
| Name limits | Six-character player/town, four-character catchphrase, ten-character request | Player and town limits runtime-tested; others have static invariants |
| Saved text | Enter names/mail/board text, save, restart, recover correctly | Outstanding |
| Choice menus | All lengths, four entries, cancellation, branch outcome | Outstanding |
| Dialogue controls | Page/wait, animation, sound, fields, selection, RNG, branches | Partial intro coverage |
| Travel and persistence | FlashRAM, Controller Pak, RTC and calendar | Outstanding |
| Long-play content | Shops, items, mail, board, credits, seasons and events | Outstanding |

The smoke runner's XTest mappings are A=`a`, B=`b`, Start=`Return`, Z=`z`,
L=`q`, R=`r`, C-Up=`u`, C-Down=`j`, C-Left=`h`, C-Right=`k`, D-pad=arrow keys,
and analogue stick up/down/left/right=`w`/`s`/`f`/`g`. An action's `key` may be
a list for simultaneous presses. These are isolated test mappings, not changes
to the user's emulator configuration.

## Original hardware and release

Record console region, flash cartridge/firmware, RAM configuration, Controller
Pak, RTC behaviour, patch and source hashes, and saved-game migration results.
Run the same menu, name, save, travel, and long-dialogue cases on hardware.
An emulator boot cannot establish original-hardware stability.

No public release until remaining translations and graphics are reviewed, known
crashes are reproduced or disproved with evidence, save compatibility is tested,
and provenance review permits the proposed patch distribution.
