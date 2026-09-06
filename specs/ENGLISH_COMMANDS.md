# English message command extension

## Dispatch contract

The module hooks the native code-size function at `8009034C`, code-attribute
function at `800903CC`, and message cursor dispatcher at `800A21C0`. Every native
opcode `00..60` retains its original size, attributes, and handler pointer. The
original tables at `80106BF4` and `80107CB8` remain intact and are read directly.
Invalid attributes return zero instead of reading beyond the native table.

The dispatcher verifies the current index and message length before examining
the opcode. A native handler receives the same window and index pointer. The
native result value zero means continue processing at the current text index.
Module entry jumps preserve the o32 calling convention and are source-guarded.

## English extensions

`7F75` sets one-shot capitalization. Player, NPC, catchphrase, free-string,
town-name, item-string, and mail insertion consume the flag and uppercase the
inserted first Latin character. Dates and selected-answer insertion do not
consume it, matching GameCube. Native colour wrappers may move the text index;
capitalization uses that updated index. The source or saved string is not changed.

`7F76` inserts `AM` or `PM`. Both the command and its result occupy two bytes, so
the buffer length and following text do not move. Attribute two identifies the
operation as a dynamic string, matching the native date fields.

Like the English GameCube implementation, the hour-field handler latches AM/PM
from the RTC hour into bit 17 of the window's status flags. The later AM/PM
command uses that stored value, even if the clock changes between the two
insertions. The builder requires a preceding hour field in the same message.
Window data is at offset `0C`, status flags at `28C`, and the data structure's
length and text are at offsets `08` and `10`; compile-time layout checks enforce
these offsets.

Unsupported extension codes remain invalid translation tokens. The codec uses
zero-size sentinel rows for gaps and rejects them rather than looping or treating
their arguments as characters. Runtime size lookup retains the native unknown
command size of two, but an unimplemented command cannot enter a built edit.

## Verified capabilities and reference import

The builder requires all resident entry hooks, date patches, bootstrap changes,
and the exact added DMA file before enabling extended tokens. A command-line
flag alone cannot relax the validator. Existing sixteen-byte choices retain
their separate complete-patch verification.

Under the explicit resident-module reference policy, a source message already
using an RTC field may import the other seven RTC components. All use the same
verified clock object and bounded formatters; this permits GameCube's weekday
and reordered calendar presentation without guessing actor-provided fields.
Other names, items, free strings, branches, and actor arguments retain their
existing matching requirements. Manual line/page breaks and timing are preserved.

## Cursor pacing contract

GameCube `7F72` and `7F73` set and clear status bit 14. These commands prevent
fast-forward/cancellation during their span; they do not change line geometry.
Implementing only their flag writes would not preserve GameCube timing.

The complete N64 port gates cancel-order detection and the initial B-button
fast-forward trigger, makes the cursor timer ignore fast/cancel flags while bit
14 is set, and retains explicit pause speed. The existing per-character and page
behaviour remains native. The message initialiser clears bit 14, and opcode 73
restores normal fast-forward behaviour. Native input flags remain available for
other game systems; no global controller input is discarded.

The timer block at `800A22A4..800A231B` can call a bounded module helper while
retaining the original continuation at `800A231C`. The caller's timer pointer,
choice-delay constant, and result constant must be restored before continuing.
The explicit-pause fast-path comparison at `800A0730..34` must test fast mode
without the pacing lock. All source instructions and helper addresses are
verified before building. Targeted timer/input/pause tests and a complete
dialogue regression are required before accepting pacing-dependent imports.

Article semantics beyond the existing narrow adapter and other GameCube flow
commands remain separate work until their complete semantics and tests exist.

## Choice cancellation

`7F62` enables B-to-last-option selection with the GameCube closing-sound policy.
The module ports the choice flags, closing-sound decision, duplicate message-sound
suppression, and both flag-reset paths. Native animation geometry remains intact.
See [choice cancellation](CHOICE_CANCELLATION.md) for the layouts, hooks, import
restrictions, and silent native regression. A changed GameCube menu is not made
compatible merely by supporting this opcode.

## Reference page delivery

The dialogue-only `reference_delivery` policy permits the confirmed English
reference to use different page-clear (`02`) and wait-for-button (`04`) placement
from the Japanese source. These are native display/input operations, not new
runtime opcodes. The imported English text retains its exact reference newlines,
pages, waits, and pauses; the tool does not reflow or remove them to fit a bubble.

Other controls still compare in order: end/continue markers, choices, branch
targets, actor requests, sound/BGM, and embedded operations are not discarded.
The existing read-only-field rules and conservative 1,024-byte expansion budget
still apply. Native actor arguments may be restored only when the complete
non-presentation opcode sequence agrees. Explicit font geometry and colour-span
commands remain separately gated. Generated manifests record the page/wait counts
and keep these imports labelled as candidates awaiting gameplay/layout review.

The separate `reference_layout` policy also retains the native formatting
commands after verification of the actual font consumers and parameter limits.
See [reference formatting](REFERENCE_LAYOUT.md). Sound code `51` remains strict.
