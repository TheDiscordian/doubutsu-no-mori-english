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

The strict noticeboard verifier also passes a focused check after its obsolete
editor-only signed-half bound is restricted to editor-only builds. Complete
letter/grid builds use their already-verified exact pool instruction and
high-half guard. The whole combined text counter succeeds on the grid candidate;
the new keyboard does not remove preceding translated text or application credit.

## Native scenario limit

`keyboard-grid-native-01` and its one corrected setup retry,
`keyboard-grid-native-02`, both reach the normally loaded grid, pass the hook,
ownership, nonzero-draw, and zero-error checks, but stop at the initial empty-name
assertion: the observed lengths are four and one, respectively. The old fixed-
count opening script presses A after entry opens, which selects an actual key
on this grid instead of doing nothing at the old radial neutral position.
Reducing the opening count from 27 to 23 does not produce a reliable empty
starting field. The retained message trace also differs in opening variants.
Neither run proves the subsequent case/deletion/cursor/capacity/Done sequence.

The snapshot writer now publishes keyboard observations before evaluating their
assertions, so future failures retain the complete state. These two earlier
logs retain their message prefix and terminal assertion, not the unpublished
keyboard row. No screenshot or checkpoint is reached; no visual approval,
normal shutdown, or completed input sequence is claimed. The candidate remains
experimental, and the handed-off title build is unchanged.

Stop retrying this opening setup during this batch. Continue remaining artwork.
The next useful combined screen/editor check must use a state-based keyboard
arrival or a deliberate clear-field setup, not another guessed A-press count.
Letter/message native checks, normal save/restart, and original-hardware
acceptance remain pending. Actual game defects remain mandatory fixes.

## Title combination

`build/title-grid-combined-01/animal-forest-title-preview.z64` combines this
grid with the unchanged English title and Expansion Pak instruction screen.
ROM SHA-256 is
`f2c46b98e4d5748d39bcd17ce697f50c4f6dbeae6b560e2ba4851ad43b46ec8d`;
UPS SHA-256 is
`e9672ca364a27ab4a970570bd9d0b2ecb78119c47007cca2835c6f3692db4d62`.
One focused combination check passes: full rebuild/patch reconstruction,
complete retained grid/artwork/text resources, strict current grid ownership,
and identical title/asset/boot/warning resources compared with the tested title
candidate. The unchanged title component reuses its recorded native evidence;
the grid's incomplete native acceptance is not promoted by combining the ROMs.
This candidate requires an Expansion Pak and is not a new recommended handoff.

## Combined screen check

The Nookington/title batch's `combined-grid-native-01` reaches the English
opening message but the runner's 70-second process deadline stops it before
keyboard entry. The one retry, `combined-grid-native-02`, has a 310-second
deadline and deliberately clears the field using B before assertions.

The retry verifies normal grid ownership and zero draw errors, deletion of the
opening's accidental `1`, an empty six-character name, selection of Q, insertion
of Q, case switching, and insertion of q. The retained image shows the complete
grid and caller's name window. A checkpoint is retained for this exact ROM at
`build/combined-grid-native-02/test.bs1`, SHA-256
`7416357e9a824f38b418c79eae54afde84167b9ebf0715ca38eb5cf892c55a02`.
The 0.08-second B step deletes both characters instead of one. The capture
reports approximately 210 FPS, so that hold can exceed the native eight-frame
repeat delay. The result is consistent with unthrottled test timing; it does not
verify single-frame deletion or the later capacity/cursor/Done assertions.

Both attempts are complete; do not repeat this setup batch. Future input checks
must control emulated frame duration and resume a matching checkpoint when safe.
No completed normal save or original-hardware acceptance is claimed.

The image also reveals an actual control-label encoding defect: raw ASCII plus
and slash bytes select native heart/music glyphs. The bounded label adapter
encodes plus as native `5C` and uses a space between the movement devices. It
changes exactly three resource bytes, with unchanged code, relocation, layout,
and capacities. The [label adapter](../../tools/keyboard_grid_labels.py) binds
the exact compiled and corrected images; broader grid verification restores
only those reviewed bytes before checking the compiled profile.
