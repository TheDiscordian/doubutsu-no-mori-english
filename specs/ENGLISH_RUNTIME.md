# English runtime substitutions and choices

## Scope

The opt-in English runtime removes the Japanese village suffix from the town
field and expands plain choice text to sixteen bytes without the resident module,
or twenty bytes with its verified storage. The supplied English disc contains
thirteen matched choices of seventeen to nineteen bytes despite the sixteen-byte
constant in the pinned GameCube source. The resident variant imports these in full.
The save format, message-window structure, overlay sizes, and main-code load
size remain unchanged. This is a runtime change, not just a ROM-bank expansion.

The supplied English disc has an empty general string `01E4`. The corresponding
N64 string contains `むら`; `mMsg_CopyCountryName` appends it after a six-byte town
name. The English runtime returns after copying the town name. It does not add
an English suffix: the surrounding English message supplies its own wording.

## Storage

| RAM region | Purpose |
| --- | --- |
| `8009F4A4..8009F4B7` | Early return from `mMsg_CopyCountryName` |
| `8009F4B8..8009F4F7` | Four sixteen-byte choice rows |
| `8009F4F8..8009F507` | Sixteen-byte selected-answer buffer |
| `8009F508..8009F50B` | Unused padding before the next function |

The storage replaces the now-unreachable village-suffix code. It is ordinary
writable RDRAM inside the permanently loaded code file, not extra heap or
Expansion Pak memory. The only game choice window is obtained through
`mChoice_Get_base_window_p`, which returns the message window's embedded choice
structure. Its old inline text arrays are no longer used; lengths, selection,
colours, positions, and all following fields keep their original offsets.

No instruction cache operation is required: the replacement is in the ROM
file before boot, and runtime writes touch only unreachable data addresses.
No executable instructions may refer or branch into the reclaimed data.

## Required patch coverage

- `800651A4`: adding a choice, length validation, and sixteen-byte row indexing.
- `80065278`: all four setter argument bounds.
- `80065348`: width calculation using the relocated rows and original lengths.
- `80065604`: ROM entry limit; the existing relocated bank address is preserved.
- `80065D90`: zero-size clearing, copied length, padding, and substitution bound.
- `80066130`: copy sixteen selected bytes; preserve length and selected ID.
- `80066BB0`: draw each relocated row with its original length and colour.
- `8009F3A8`: insert the relocated selected-answer text into messages.
- `800A0DF4`: all main-message choice staging pointers, strides, and lengths.

The loader's source declares a 29-byte aligned-DMA staging array. Its physical
stack slot is `sp+48..67`, thirty-two bytes, with the live length temporary at
`sp+68`. Sixteen-byte entries require at most `align8(7 + 16) = 24` bytes; twenty-byte
entries require at most `align8(7 + 20) = 32`. Both fit the existing allocation.
The guarded instruction checks retain its frame, DMA pointer, and length slot.

All four hundred and sixty original choice entries are command-free. Expanded
choice imports must remain plain text: command-bearing or two-byte-tag choices
are rejected until their separate substitution paths are proved safe.

## Actor callers

A scan of every aligned word in every decoded DMA file finds additional loader
calls in two overlays. They must be patched with the main loader.

| Overlay VROM | Linked RAM | Required adjustment |
| --- | --- | --- |
| `849B50` Quest Manager | `80954D80` | Four-row staging array grows from forty to sixty-four stack bytes; both row calculations and all setter lengths change |
| `8A1F10` Player Select 2 | `809BE720` | Two staging stack frames grow by twenty-four bytes; saved values and incoming argument offsets above the arrays move; name-row helpers and extra menu rows use sixteen-byte strides |
| `932B60` Festival Stall | `80A728C0` | No ROM choice loader; existing ten-byte item/embedded-label arguments remain valid and are copied into the larger rows |

Actor instruction offsets and relocation records remain in place. Stack and
stride changes do not alter overlay pointers or relocation requirements.

## Resident twenty-byte variant

The module owns a 32-byte-aligned structure containing four 32-byte rows and one
32-byte selected-answer row. The text capacity is twenty; the larger row stride
allows the existing instruction slots to use a single shift. The module header
at offsets `28..37` hexadecimal records capacity, stride, row pointer, and selected
pointer. These must agree with the linked storage symbol and module bounds.
Startup fills the entire structure with spaces before the game uses it.

Main-message loading and drawing advance by thirty-two bytes. Length limits,
copying, padding, and selected-answer insertion use twenty. Actor staging uses
tightly packed twenty-byte rows: the Quest Manager frame grows from 176 to 216
bytes; Player Select frames grow from 136 to 176 and from 128 to 168 bytes.
All saved temporaries and incoming arguments above the arrays move by forty.
The existing multiply-by-ten row calculations become multiply-by-twenty.

Builders verify the complete module and English runtime together before allowing
twenty-byte text. Selecting an increased text limit alone cannot enable imports.
The baseline sixteen-byte implementation and its assembled width code stay
unchanged. The test runner reads the module header and checks the active row
pointer instructions before interpreting the larger choice storage.

`tools/choice_test_scenario.py` creates ignored test data from a built ROM. Native
MIPS tests load all thirteen long entries through real cartridge DMA, check
destination guards and padding, exercise all four rows and their width, reject
a fifth row and excess length, select every row, and insert the selected text
into a message. Complete emulator checkpoints restore the machine after these
test-only calls. Normal gameplay and actor-specific paths require separate runs.

## Acceptance

Every source file hash and every changed instruction are guarded. Builds report
the changes, capacities, and RAM allocation. Tests must reject partially applied
patches, mismatched source files, unsupported capacity requests, and overflowing
or command-bearing choice edits. MIPS assembly is independently checked with
the pinned Docker toolchain.

Runtime acceptance includes long choices, all four rows, selection and colour,
selected-answer insertion, both actor-specific callers, unchanged town names,
and four-MiB memory. Emulator assertions are not original-hardware certification.
