# Completion queue

This is the durable queue for the complete translation project. A working
milestone does not complete the project. Continue through available work without
requiring the user to advance an automated procedure. Commit verified changes
and update the evidence links as each task progresses.

Status meanings: **active** = being implemented or audited; **pending** = required
work remains; **external validation** = cannot be claimed without the specified
hardware or independent permission/evidence. A task becomes complete only when
its acceptance checks pass, not when a candidate or specification exists.

## Main translation and runtime

| ID | Task | Status | Acceptance/evidence |
| --- | --- | --- | --- |
| R01 | English runtime substitutions, including town/date/time formats | active | Town, seven message date/time fields, and AM/PM pass; other UI callers remain |
| R02 | Choice strings beyond ten bytes | active | Sixteen-byte main path passes; fourteen choice translations, four-row/cancellation, and actor runtime tests remain |
| R03 | General strings and UI caller capacities | pending | Each imported string has a proven destination limit; no truncation |
| R04 | NPC and item names | pending | IDs matched from actor/item tables; full English names supported by every destination |
| R05 | Mail, headers, footers, and NPC mail components | pending | Safe expansion, editing, display, delivery, and save/reload |
| R06 | Remaining GameCube controls | active | AM/PM, capitalization, and protected pacing have targeted MIPS tests; choice-close, random-range, space, and wider flow coverage remain |
| R07 | Remaining message matching | pending | Every N64 ID classified, references established, N64-only content translated |
| R08 | Review all candidate dialogue | pending | Meaning, placeholders, branches, actor arguments, and delivery reviewed; candidates are not automatically approved |
| R09 | Embedded UI, calendar, credits, and other uncovered text | pending | Inventory extends beyond the current 29 banks and keyboard UI |
| R10 | Punctuation and layout polish | pending | Preserve GameCube line/page/timing intent; review necessary N64 departures individually |
| R11 | Reported font-atlas edge defect | pending, paused by user direction | Do not resume the discarded font comparison investigation without renewed direction |

## Stability and compatibility

| ID | Task | Status | Acceptance/evidence |
| --- | --- | --- | --- |
| V01 | Repeatable build and regression suite | active | Verified inputs, deterministic outputs, all tests passing, clean tracked worktree |
| V02 | New-town creation through normal gameplay | active | Name and town entry and arrival pass; house selection and introductory jobs remain |
| V03 | Save/reload and long names | pending | Isolated FlashRAM, RTC, no lost/truncated text, restart across sessions |
| V04 | Keyboard callers beyond player/town names | pending | Catchphrases, apology, song request, mail, and board |
| V05 | Dialogues and menus across progression | pending | All control families, four-choice menus, inventory, shops, item displays |
| V06 | Travel and Controller Pak | pending | Export/import, error paths, different towns, saved names |
| V07 | Dates, RTC, seasons, events, and credits | pending | Event coverage and boundary dates with controlled test saves |
| V08 | Legacy glitch/crash audit | pending | Reproduce reports where possible; distinguish damaged data from mere command differences |
| V09 | Four-MiB memory and resource budgets | active | Sixteen-KiB module reservation retains guards through town arrival; broader heap/graphics tests remain |
| V10 | Original hardware matrix | external validation | Real console/flash cartridge/Controller Pak evidence; emulator evidence is insufficient |

## Image and keyboard stretch goals

Work on these after the main porting effort, while inventory work may identify
the required resources earlier.

| ID | Task | Status | Acceptance/evidence |
| --- | --- | --- | --- |
| S01 | Identify every Japanese text-bearing image | pending | Asset IDs, dimensions, texture formats, palette use, and in-game location |
| S02 | Match English GameCube images, including title screen | pending | Extract from supplied disc; prove matching asset identity and intended use |
| S03 | Replace images with matching GameCube artwork | pending | Preserve identical artwork where formats allow; document any necessary conversion; check N64 memory/graphics budgets |
| S04 | GameCube-style English keyboard | pending, specified | Real 10×4 grid, case/symbol pages, N64 controller mapping, all editor callers and save limits tested |

## Release

| ID | Task | Status | Acceptance/evidence |
| --- | --- | --- | --- |
| P01 | Complete coverage report | pending | No unclassified or unreviewed required text/assets; intentional exceptions explicit |
| P02 | Provenance and redistribution review | pending | Nintendo inputs remain local; legacy permissions assessed; patch-only package |
| P03 | Reproducible release artifacts and instructions | pending | Source-hash rejection, verified patch application, checksums, install and compatibility notes |
| P04 | Final acceptance | pending | Main work, stretch goals, regression matrix, and required external validation complete |

Current observations and counts live in `PROGRESS.md`. Implementation contracts
live under `specs/`. Dated results and exact build hashes live in `WORK_LOG.md`.
Generated detailed inventories, captures, test saves, and binaries stay ignored
under `build/` and `local/`; original tools and documentation are versioned.
