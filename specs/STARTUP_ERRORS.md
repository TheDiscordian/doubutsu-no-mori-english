# Native cartridge-clock and town-data errors

`translations/n64-startup-errors.json` supplies complete original English drafts
for startup errors `09CC` and `09D1`. The supplied GameCube equivalents change
hardware or actions, so they are not imported as complete native equivalents.
These edits do not change executable code, save data, clock handling, or recovery.

`09CC` describes the clock inside the cartridge appearing to have stopped,
refers to the instruction booklet, explains that playing without the clock is
possible, and offers starting immediately or waiting before another attempt.
Native choice IDs `00E7/00E8` and branches `09CD/09CF` remain unchanged. The
existing English successors retain the date-entry and return-to-title paths.
Every native command, argument, pause, page, and terminator remains exact except
the highlighted `Instruction Booklet` length: `50:E11ED7:0C` becomes `13`.
No GameCube console-clock location or replacement choice `01DD` is introduced.

`09D1` apologises for the interruption, reports corrupted town data, asks the
player to start again from the beginning, and apologises once more. It retains
all original pauses/pages, the existing `09:09:0001` request, and final `00`.
It does not claim automatic erasure, ask to reinsert a Memory Card, add a field
or choice, or follow the legacy's different `09D7` continuation. Translation
does not establish that recovery succeeds or authorise a storage operation.

Focused tests compare every complete source hash and command sequence, enforce
the sole colour-length change, check both native choice/branch IDs and the
distinct error meanings, and retain the existing expansion/layout limits.
Normal startup error selection, date entry, clock recovery, saving, wording
review, and original hardware remain acceptance requirements. Exact build and
test results belong in `docs/WORK_LOG.md`.
