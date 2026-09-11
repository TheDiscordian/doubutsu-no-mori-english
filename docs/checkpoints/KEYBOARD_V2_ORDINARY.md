# V2 ordinary name-entry work record

## Result

The ordinary name editor is reached using normal controller input on V2,
without injecting a drawing function or changing game RAM. The first run
completes character entry, space insertion, caret movement,
deletion, and Start confirmation back to Rover's dialogue. Actual isolated
display captures are inspected for the released controls and held L, Z, A, R,
B, C-left, and C-right. No new input failure, crash, or resident-guard failure
is observed.

The screenshot review identifies one V2 presentation adjustment: the stick's
`Move` hint is not readable at its original left-side position. Moving the hint
from `(29,178)` to `(44,177)` still crowds the curved panel edge. The final
adjustment removes that redundant left-side label; the stick graphic and bottom
movement hint remain. No font pixels, key positions, native artwork, controls,
sounds, editor capacity, or saved formats change. The screenshot skill informs
this adjustment through isolated emulator captures, without viewing the user's
desktop or opening repeated status renders.

## Current artifacts

- ROM: `build/v2-keyboard-05/Animal Forest English V2 Development.z64`.
- ROM SHA-256: `085e3dfc10cc03e591ce4197d7f3841c45e3fba3b51344d1be58c87cda2fe9d9`.
- UPS SHA-256: `cbcee703fcf3f3957a112449a11e0718ac1a134fb440d2afddcfc6705228c888`.
- Editor SHA-256: `d40983449e1d0cb5cbdd5a44e6640ed00db06c636ed2e3e8e826b5d333ad4942`.
- Relocation SHA-256: `b1a4f83459d71ff7b76bbb237fb0bb034487406518e0ae27c078ab8e81826808`.
- Build receipt: `build/v2-keyboard-05/build.json`.

The editor is 37,984 bytes, using 7,744 of the existing 8,192 suffix bytes.
V1 Final remains unchanged. All artifacts stay local and ignored; the source
repository is confirmed private. No public release or new RC is created.

## Ordinary interaction evidence

`build/v2-keyboard-name-entry-01/results.json` records 47 result entries and
graceful shutdown. Its SHA-256 is
`774d3a1c74d75aa4e0eeb30a39608d7c1f2558d4c74efc731814e088072d18f5`.
This run executes the then-current `v2-keyboard-03` ROM, SHA-256
`df903c293c98c9c8f942c95c47f7a8b1fbd8298ce86aa78d82eae2a4644fcd90`.
It is not relabelled as execution of the subsequent label-position change.

- The ordinary six-character, one-row name editor loads at `803AA050`.
- Normal L and Z presses display lowercase and the consolidated symbol page.
- A inserts `!`; R adds a real blank, with recorded length changing from one
  to two and the caret advancing. C-left and C-right move the visible caret.
- B clears the field. A letter is selected and entered as `Q`.
- Start closes the keyboard; message `2ACA` and the inspected final screenshot
  show Rover responding to the entered name.
- The eight-MiB setting and resident guard assertions pass.

The screenshots reviewed are `name-empty.png`, `name-l-held.png`,
`name-z-held-symbols.png`, `name-a-held.png`, `name-r-held.png`,
`name-b-held.png`, `name-c-left-held.png`, `name-c-right-held.png`, and
`name-confirmed.png`, all under the result directory. Representative hashes:

- `name-empty.png`: `6089e9d2ef0daf332514610cd0e3ce4df9f01deac44b030a576bbc0cd4ea02c1`.
- `name-confirmed.png`: `7a4a43b810b0a2fe5cb6a8adc5ed29f1b74d8518fa5e7791709080bc01715e36`.

The existing runner gains a bounded held-key capture option. It uses ordinary
host key events, lets the display update, and releases every held key in a
`finally` block even if capture fails. Four focused helper checks pass. It
does not write controller state or call test-only game functions. An isolated
emulator checkpoint is saved for recovery but no checkpoint load is needed;
this is not a game-save persistence test.

## Label correction verification

Four artifact checks pass in 2.608 seconds against the intermediate
`v2-keyboard-04`, SHA-256
`7cf3006e83beb9aae76c51f322fd7f5a967d4f8227d5336aa0d24e5cfa36cb0e`.
The focused ordinary-menu run at `build/v2-keyboard-stick-label-01` completes
31 result entries with intact resident guards and graceful shutdown. Its
inspected screenshot exposes the remaining label crowding; successful program
execution is not incorrectly reported as successful placement.

- Results SHA-256: `041621aae05c5a7fcc96f6a3b09d6ca43649ff86dcfe985e95e94aea22fc01e1`.
- `name-stick-label.png` SHA-256: `31016a472fda6db34e8461c26f4391e51e1930a1736c638188e5a245ed56225f`.

Removing the redundant label produces `v2-keyboard-05`. Its four focused
artifact checks pass in 2.601 seconds: complete patch reconstruction, all
unrelated resource retention, the complete editor prefix under relocation,
native artwork/font/key metrics, and allocation limits. An assertion ensures
the unwanted left-side label call is absent. Removing that font call reduces
graphics work and rounded suffix size by 64 bytes; no new geometry or input
path is introduced. No further native replay is run for the removal, and no
claim is made that the intermediate crowded placement is accepted.

## Limits and handoff

The earlier controlled native 155-draw check remains evidence for the retained
graphics geometry/materials and bounded allocations. It is not repeated or
presented as fresh execution of the final one-label removal.
Ordinary name-entry evidence does not certify every keyboard caller, every
button combination, or original hardware. Start's completion behaviour is
executed; its short-lived pressed artwork and C-up/C-down pressed appearance
are not separately reviewed. These are playtest limits, not new automated
test queues.

Expansion Pak, 128-KiB FlashRAM, and RTC remain required. V1 Final → V2 and
V2 → V1 Final save compatibility are expected without migration because the
saved formats and editor prefix are preserved; those particular loading
directions are not executed here. The user's saves remain untouched. V1's
human-accepted ordinary save/restart/reload checks remain closed.

Continue with concrete V2 playtest findings. Do not replay old builds, broaden
the artwork scope, construct an exhaustive keyboard matrix, or publish without
the user's direction.
