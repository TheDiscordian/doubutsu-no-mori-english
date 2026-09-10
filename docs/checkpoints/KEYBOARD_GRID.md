# Shared English keyboard grid

## Implemented

The standalone grid controller and six mapped GameCube key tables are complete.
The grid uses the supplied 10-by-four QWERTY/alphabetical arrangements, with
case/page switching, clamped movement, and native-rate repeat timing. Unsupported
characters are disabled explicitly. Sun/Skull tokens remain apology-only; single-
line editors cannot insert a newline. The controller emits existing editing
commands and never writes a saved or draft input buffer.

Three focused tests pass: source-bound layout conversion, host address/undefined-
behaviour sanitizers for controls and boundary cases, and independent MIPS
compilation without external runtime dependencies. The generated 480-byte layout
has SHA-256 `de0934289f9ee4f86cdadd87df63fe2eba0ab0b7d5cdb76949bd98ab7c54c0a7`.

The 23 inventoried clock characters also update the common source denominator
in 21 existing test modules. Those edits change only denominator expectations;
the expensive historical integration fixtures are not rerun for this mechanical
change. The focused clock and combined-counter checks already verify this shared
inventory. Older fixtures with other historical denominators remain separate
regression maintenance, not newly passing tests.

## Current implementation

Append the native bridge, renderer, and private state after the exact complete
apology/owner editor. The four verified hook sites and retained native editor
contract are in [the specification](../../specs/KEYBOARD_GRID.md). Regenerate
relocations and owner bounds, reserve the actual extra shared-menu memory, and
verify complete preceding-resource retention before building a keyboard ROM.

The grid is not installed in a ROM yet. The combined English-title handoff
continues to use the English-first radial keyboard. After integration, perform
one bounded combined native editor check; ordinary navigation, save/restart,
and original-hardware interaction remain human playtest work.
