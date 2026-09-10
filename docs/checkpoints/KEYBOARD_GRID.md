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

## Installed candidate

`build/keyboard-grid-01/animal-forest-halfwidth.z64` installs the complete shared
grid on the collection/artwork/conversation-fix baseline. ROM SHA-256 is
`e5f2a22f50f89fdf7e0e9743368abf9a2f4d261e303dc0339f5cbbc4a0ad48f7`;
UPS SHA-256 is `c8fe9ddeccada6537a7eee637bc02ba008ff0ec5ebe506c54ab878118050d849`.
The cartridge remains 32 MiB, with unchanged saved fields and resident module.
This separate candidate does not include the title; the English-title handoff
continues to use the radial keyboard until the combined candidate is rebuilt.

The overlay is 28,656 bytes, including the retained 23,168-byte apology editor,
with a 2,096-byte relocation resource. Four existing relocated calls select the
new input/drawing bridges. Owner metadata uses the complete image bounds and
the clearing destructor. The shared menu pool increases by 5,632 bytes to
253,056 bytes, exceeding the 252,736-byte conservative requirement. The original
editor state, name/letter/message handlers, input capacities, native case/
ornament exchange, and caller-window drawing remain. No writes enlarge a save.

The native renderer uses all forty donor key positions and the losslessly
untiled 128-byte I4 keycap, with its original mirrored UV span. Key glyphs use
the installed proportional font; no font pixels are changed. English labels
describe N64 controls. Drawing checks opaque-buffer capacity and each glyph
call's allowance. Source-bound Sun/Skull keys use only the apology adapter.

Five control/resource/bridge checks and three compiled/integration checks pass.
The latter rebuild the overlay independently, compare all retained resources,
verify relocation at three heap addresses, reconstruct the complete cartridge
from its patch, and exercise the strict shared apology/letter/inventory
verifiers. A keycap fixture initially compared a list to bytes; the corrected
type-normalised comparison passes without changing the texture or ROM.

The bounded silent ordinary-name scenario at `tests/keyboard-grid-scenario.json`
is running against this candidate. It checks fresh native loading/drawing,
case/deletion/cursor controls, capacity, Done, and resident guards. Actual
display/input acceptance is not yet claimed. Letter/message native checks,
normal save/restart, and original-hardware acceptance remain pending. Continue
those bounded checks, fix actual defects, and then combine the title and grid.
