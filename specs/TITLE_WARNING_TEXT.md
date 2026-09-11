# Native title warning text

## Scope and source

The installed English title retains a live native no-controller branch. Linked
`80AA1AF4..80AA1B10` reads controller-one presence at `80137950` and calls
`80AA08E4` when absent. The three direct font calls at `80AA096C`, `80AA09D8`,
and `80AA0A44` still select Japanese in RC6; the new logo adapters do not replace
this branch. Translate the warning without changing controller detection,
input, title transitions, or the instruction to power off before connecting.

The English GameCube title source has no equivalent three-line warning. Use
an original English translation of the native instruction:

```
Controller 1 is not
connected. Power off,
then connect it.
```

The native title-menu row at `80AA205E` also retains Japanese meaning
`Erase Save Data`. Translate its complete nineteen-byte padded label without
changing its selection, visibility, or action. Do not invoke any deletion
operation to validate wording, and do not infer ordinary access from storage.

## Storage and reader changes

The current title owner is VROM `03C00000`, linked RAM `80A9FC70`, 292,320 bytes,
SHA-256 `b2ee139e3b57411e3cb6bae925ad2e9303bc205f3e314b5c60b9a547ce2f6e36`.
Relocation `03C50000` is 720 bytes, SHA-256
`f8b4f4361dd9812f0bd7af8d744199f57a7e6fbfc0fb7507f7cfa983c7b042e9`.
Its flattened sections are `(292320, 0, 0, 0, 174)`.

Repack only the existing sixty-byte warning area `80AA2118..80AA2153`.
Complete line lengths are 19, 21, and 16 bytes; four unused bytes are zero.
The line pointers become `80AA2118`, `80AA212B`, and `80AA2140`. Retain the
original HI/LO relocation records; unaligned character pointers are permitted.
The erase label remains nineteen bytes in its original slot.

| Line | Pointer HI / LO | Count | X constant | Font call |
| --- | --- | --- | --- | --- |
| Controller state | `80AA0918` / `80AA094C` | `80AA0954` | `80AA0958` | `80AA096C` |
| Power instruction | `80AA0984` / `80AA09B8` | `80AA09C0` | `80AA09C4` | `80AA09D8` |
| Connection instruction | `80AA09F0` / `80AA0A24` | `80AA0A2C` | `80AA0A30` | `80AA0A44` |

The installed proportional widths are 108, 123, and 93 pixels. Centre each line
at X 160, producing origins 106, 98.5, and 113.5. Retain native Y positions
120/140/160, scale one, colour, opacity, background, and font flags. No new code,
allocation, stack space, saved bytes, glyph graphics, or relocation rows are
needed. The title's existing Expansion Pak reservation remains sufficient.

## Verification

`tools/title_warning_text.py` requires the exact RC6 cartridge and source title
identities, checks complete native strings and actual readers, and changes only
the two text spans and seven instruction words. It verifies relocated strings,
counts, and unrelated content at two lower addresses and the actual title
address `80400010`, with explicit eight-MiB bounds. Complete ROM reconstruction
retains every other DMA resource and checks standalone UPS application.

Focused tests cover complete wording, relocation, centring, unchanged controller
and save actions, retained title artwork, and refusal of altered inputs. These
are construction checks, not native rendering or hardware appearance acceptance.
Do not repeat completed title-animation or missing-Expansion-Pak tests for this
text-only correction. Save formats and readers/writers are unchanged; loading
and saving evidence must still be stated separately at handoff.
