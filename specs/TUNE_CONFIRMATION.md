# Town-tune confirmation wording

## Scope and sources

The town-tune confirmation still draws Japanese `ホントに?`, `うん`, and
`やっぱやめる` in RC5. Its note images and separate OK artwork are already
English. Correct this remaining three-line reader without changing selection
indices, melody storage, pitch, sound, timing, window geometry, or allocations.

Baseline RC5 SHA-256:
`6ed7d636b953d24d4ad10ae8ea806deb133a752f4295ad79727c52336095dae4`.
Owner VROM `0079C020`, linked RAM `808988F0`, is the unchanged 6,288-byte native
image, SHA-256 `458215a2da1132b4cd30d24d4fdaacc656986f2d730c5825ddb41e13994e0459`.
Relocation `0079D8B0` has 416 bytes and sections `(5712,544,32,48,97)`, SHA-256
`2dd574142cde5d74fc66a80e4a4c2dd505b9808b76310e3e29dfbf94904c360f`.

Bind the supplied GC REL and complete symbols to `mMS_str_title` at
`.data:00080D98`, `mMS_str_ok` at `00080DA8`, and `mMS_str_cancel` at
`00080DAC`. The full counted strings are `Are you sure?` (13 bytes), `Yes`
(3), and `No` (2). These are the GC confirmation's actual three draw arguments,
not wording borrowed from an unrelated prompt.

## Existing storage and readers

The native strings and padding occupy the twenty-byte region `1844..1857`.
Repack it as title at `1844`, Yes at `1851`, No at `1854`, and two trailing
zero bytes. These are counted byte strings; they do not need word alignment
or null terminators. No copy to a shorter stack or saved buffer is introduced.
The following asset start/end table at `1858` must remain intact.

| Line | Native pointer / count | English pointer / count | Pointer low instruction | Count instruction | Font call |
| --- | --- | --- | --- | --- | --- |
| Title | `8089A134` / 5 | `8089A134` / 13 | `80899BE8` | `80899BF4` | `80899C0C` |
| Yes | `8089A13C` / 2 | `8089A141` / 3 | `80899C5C` | `80899C6C` | `80899C94` |
| No | `8089A140` / 6 | `8089A144` / 2 | `80899CDC` | `80899CFC` | `80899D08` |

Only two pointer low halves and three count immediates change. The corresponding
existing HI16/LO16 relocation pairs remain valid, including the byte-aligned Yes
address. Preserve every relocation record, high-half instruction, call, and
remaining owner byte. Confirm complete string selection after relocation at
several loaded addresses, including a low-half carry boundary.

## Presentation and safety

The installed width table is SHA-256
`74ecbd2d0f1ca55cd55fc57f977d3a957dc2659068e7ad99360f097ef9834fc1`;
the shared width branch at `80090294` is already disabled for proportional
Latin. Full widths are 78, 18, and 12 pixels. Do not change this shared font.

At full opening, native text X is 159 plus menu X, with Y 126, 142, and 158
minus menu Y. All three text scales follow the existing opening scale. The
native background centre is X 191 plus menu X, with half-width
`68 * 0.897059 = 61.000012` and half-height `64 * 0.708333`. Its four quads are in
the unchanged shared asset `00A6B000`, starting at `43F0`; the drawer at `4660`
binds them. The complete longest English line ends at X 237, inside the
native background. The text offsets and window extents both scale with the
same opening factor, so retaining these coordinates preserves containment
through the animation. Keep cursor/choice alignment and all vertical spacing.

The builder verifies source/ROM identities, full English donor strings, source
text, the actual three pointer/count/call sites, unchanged relocation structure,
font widths, background geometry, all unrelated resources, and UPS application.
Focused tests cover the repacked region, relocated readers, refusal of changed
inputs, and full cartridge retention. This does not claim ordinary screen,
save/restart, or original-hardware acceptance. No save migration is introduced.
