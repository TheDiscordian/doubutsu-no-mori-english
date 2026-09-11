# Validation requirements

## V0 versus full acceptance

The [v0 delivery plan](V0_PLAN.md) defines the bounded pre-handoff checks and
retry limits. Build safeguards stay mandatory. The matrix below records wider
acceptance work; it is not an all-pass prerequisite for the v0 build.
Human playthrough and original-hardware testing require the delivered build and
cannot block its creation. Untested areas remain labelled, not claimed passed.

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
- Run affected checks once per meaningful content/runtime batch; reuse passing
  native evidence for unchanged dependencies. Follow the v0 limit of one initial
  scenario attempt, one concretely justified retry, and at most 30 minutes of
  new harness construction/debugging per batch. Record difficult cases for the
  combined bug pass and continue unrelated implementation. Do not weaken guards
  or conceal credible crash/save/memory risks to meet that limit.

The user plans a human playthrough after the main translation work, reporting
bugs for the final fix and polish pass. Prepare a broadly complete playable build
with known issues and untested areas listed. Automated checks focus on crashes,
save corruption, broken text, and obvious regressions. Neither planned manual
testing nor passing narrow fixtures proves full gameplay or hardware acceptance.
The [human playthrough guide](PLAYTESTING.md) defines the final test handoff and
the information needed to turn observations into reproducible bug reports.

## Emulator matrix

Use isolated saves and disabled audio. Record the exact ROM SHA-256 and emulator
version and the actual RAM requirement. Test the supported configuration;
four-MiB compatibility is not a prerequisite for an Expansion Pak build.

| Area | Required evidence | Current status |
| --- | --- | --- |
| Boot and intro | Rendered dialogue, advancing messages, active loader instructions | Tested in ares 148 |
| Four-MiB memory | `osMemSize` at `0x80000318` equals `0x00400000` | Tested |
| Resident module | Startup identity, reduced heap bounds, guards through gameplay | Tested through town arrival; wider allocation and hardware coverage outstanding |
| English date fields | Month/weekday expansion, ordinal day, twelve-hour time, padded minutes/seconds | Seven native insertion calls and exhaustive portable format tests pass; other UI outstanding |
| Prepared resident dates | Real overlay loading, ten-byte fields, native lunar conversion, leap month, and source retention | 53 preparations, thirteen conversions across six years and a leap month, six festival-message loads, and eight insertions pass; 102 native calls and 184 assertions; normal seasonal gameplay, birthday item fields, other actors, and years outside the native table remain |
| Native seasonal dialogue | Complete native commands, shrine/moon/insect topics, inviter identity, spring choices/branches, and full text loading | 21 original drafts pass source/command/layout checks and all native cartridge loads, with 65 assertions and intact guards; final wording/layout and ordinary seasonal gameplay remain |
| English command extensions | Latched AM/PM, one-shot capitals, protected pacing | Targeted MIPS tests pass; full actor/control coverage outstanding |
| Name-entry opening | Fresh-town intro reaches the native editor | Tested |
| English keyboard | Default ABC, case, delete, cursor, confirmation, all modes | Tested with memory assertions in ares 148 |
| Name cursor geometry | Rendered prefix width, mixed-width letters, correct selection position | Basic entry visually checked; mixed-width runtime cases outstanding |
| Name limits | Six-character player/town, four-character catchphrase, ten-character request | Player and town limits runtime-tested; others have static invariants |
| Saved text | Enter names/mail/board text, save, restart, recover correctly | Native FlashRAM round trip passes 192 synthetic stored-letter slots in both banks and full English reconstruction in a fresh process; ordinary save/restart/reload and reported editor fixes are separately human-accepted; exhaustive stored-text cases are not claimed |
| Choice menus | All lengths, four entries, cancellation, branch outcome | Twenty-byte capacity, thirteen long reference loads, four rows, selected text, and cancellation pass isolated native tests; corrected shop labels and messages pass cartridge loads; ordinary actor-specific selection remains outstanding |
| Town arrival | Train dialogue completes and arrival message runs | Tested in ares 148 |
| Dialogue controls | Page/wait, animation, sound, fields, selection, RNG, branches | Partial intro coverage; 25 approved task-response messages pass complete cartridge loads and actual native actor-request dispatch with exact values/destinations; subsequent ordinary actor progression remains |
| Added current-player/town names | Correct source identity, complete insertion, colours, cursor, and memory bounds | 26 individually approved messages and all 27 added field occurrences pass native loads/dispatch; no generic free-string/catchphrase permission; ordinary traversal remains |
| Added resident catchphrases | Native appearance actor binding, complete insertion, defaults/custom/null behaviour, source retention | 27 approved messages pass real requests and initializer/DMA loads; 30 insertions, 91 calls, and 432 assertions pass, including clearing an old client; no generic catchphrase permission or ordinary traversal claim |
| Native text formatting | Colour spans, offsets, anchors, character/line scales | Actual renderer dispatch, restoration, argument extremes, and guards tested; individual layouts need review |
| Separate English glyphs | Startup ownership, actual native drawing/reveal, complete source-bound imports | 26 draws, eight cursor cases, six complete message loads, and 324 assertions pass with no font-code upload; native atlas/widths/saves retained; ordinary glyph-bearing conversations, mail/editor consumers, and hardware remain |
| Travel and persistence | FlashRAM, Controller Pak, RTC and calendar | Isolated native FlashRAM and both Controller Pak letter-file persistence tests pass fresh-process reads; ordinary saving is separately human-accepted; untested travel/storage UI, RTC, and calendar cases remain |
| Long-play content | Shops, items, mail, board, credits, seasons and events | Outstanding |

The smoke runner's XTest mappings are A=`a`, B=`b`, Start=`Return`, Z=`z`,
L=`q`, R=`r`, C-Up=`u`, C-Down=`j`, C-Left=`h`, C-Right=`k`, D-pad=arrow keys,
and analogue stick up/down/left/right=`w`/`s`/`f`/`g`. An action's `key` may be
a list for simultaneous presses. These are isolated test mappings, not changes
to the user's emulator configuration.

`advance_to_choice` advances dialogue within an explicit press/time limit and
stops before confirming an active choice. It checks native choice state 2,
not stale row contents left by a closed menu. Every message/choice snapshot is
recorded as the action runs, and failure to reach a menu fails the scenario.

F5 saves an emulator checkpoint, F6 loads it, and F12 closes the isolated
emulator normally. Test output records flushed FlashRAM, RTC, and Controller Pak
file hashes. A blank FlashRAM file or an emulator checkpoint does not establish
that the game itself has saved and reloaded a town.

The installed debugger's scalar register packets interpret indices differently
from the current source. `p25` is retained only as a raw observation and is not
labelled a PC. The bulk `g` response follows the N64 core's 71-register ordering;
the checkpoint probe records both forms for comparison.

## Original hardware and release

The [human acceptance record](checkpoints/V1_HUMAN_ACCEPTANCE.md) confirms
ordinary save/restart/reload across repeated real-game sessions and every
user-reported defect (V1-01 through V1-23). Those hardware checks are complete;
the emulator matrix's narrower historical results do not reopen them. The
confirmation is not a claim that every candidate pair or seasonal/Pak case is
tested, nor fresh execution of a candidate the user has not received.

These are broader acceptance/public-release requirements, not prerequisites for
the private v0 playtest handoff. Hardware results follow access to that build.

Record console region, flash cartridge/firmware, RAM configuration, Controller
Pak, RTC behaviour, patch and source hashes, and saved-game migration results.
Run the same menu, name, save, travel, and long-dialogue cases on hardware.
An emulator boot cannot establish original-hardware stability.

No public release until remaining translations and graphics are reviewed, known
crashes are reproduced or disproved with evidence, save compatibility is tested,
and provenance review permits the proposed patch distribution.
