# RC4 catalogue and repayment labels

## Scope

Correct reported findings V1-21 through V1-23 on the exact RC4 cartridge,
SHA-256 `5930435f588947df35313ae9cc2ea301af9fc7e68d59a7d8e13a48741d4f3067`.
Use complete wording and source pixels from the supplied English GC release.
Preserve existing translations, controller navigation, prices, orderability,
repayment arithmetic, saved formats, and the separate bordered-font reservation.

## Catalogue currency image

The existing asset is VROM `00B2A000`, 47,408 bytes, SHA-256
`86ceb1eee7f2fd023e8cbe1a0987483733ce1add3429cacdd77ac145045ecba0`.
Its 32×16 I4 currency image at offset `4888` still contains Japanese.
The sole texture load at `37E0` and native quad at `2ED0` already use complete
32×16 coordinates. Replace only its 256 texel bytes with GC `.data:003E88A0`,
bound by `clg_win_beruT_model` at `003EF490` and texture command `003EF4A8`.
Do not import GC display lists or change native price/control geometry.

## Catalogue Not for Sale

The catalogue is already relocated to `03970000`, with relocation resource
`03980000`, linked RAM `808A6100`, and 53,584 loaded bytes. Its price presenter
at `808A8218..808A835B` still copies five Japanese bytes from `808AF964` into
the eight-byte stack region at `sp+50`. Increasing the copy length would damage
the caller's stack. Preserve this bounded native copy and all price formatting.

Redirect only its final font call at `808A8344` through an appended assembly
adapter. The native price value is saved at `sp+40` before the branch. For a
nonzero price, tail-call the original font routine without changing any drawing
argument. For zero, point directly to the complete twelve-byte GC `Not for Sale`
text and use length twelve, without copying it into the native stack buffer.
The GC source is `.data:0007E158`; bind the exact symbol and complete wording.

Use the GC non-sale text origin `(48 + menu_x, 167 - menu_y)` and 0.875 scale:
the native non-sale origin is `(57 + menu_x, 168 - menu_y)` at 0.75 scale.
The adapter subtracts nine from X and one from Y and sets both scales only for
the non-sale branch. Installed English width is 70 pixels before scaling,
61.25 afterwards, within the existing price area. Paid-item values retain all
original coordinates, scale, formatting, and the native five-byte draw length.

Append adapter code and text after the complete current name cache. Preserve
all original relocation entries and add only the font-call relocation plus
the adapter's internal text pointer pair. The external font target stays fixed
at `80090E98`. Increase the single flattened text-section size and the catalogue
parent row's VROM/RAM ends, without changing starts or callbacks. Verify rounded
overlay and relocation growth against the existing shared-menu reservation;
do not infer memory safety from cartridge space. Native BSS and complete-name
cache addresses remain unchanged.

The current shared-pool immediate is `25CE7620`, not the older embedded-warning
stage's `25CE3220`. Bound the full RC4 source and retain this current reservation.
For a conservative bound, charge the entire later `4400`-byte reservation as
used in addition to the earlier 253,696-byte requirement. The adapter adds 64
rounded bytes; relocation storage remains in its existing 640-byte rounded
allocation. Required capacity is at most 271,168 of 274,560 bytes.

## Repayment heading and confirmation

Owner `0079B120`, RAM `808979C0`, is still the native 3,568-byte image,
SHA-256 `c399ed1dd7f5c8f3552993294f234b2190889448f5ceb76dc3861f8694e28d63`.
Its 272-byte relocation is `0079BF10`, SHA-256
`b0c5b4c56ce2844910a0d9a75428ce35912b00233fae22bd23144d04cb62d1ba`.
Sections are `(3440, 112, 16, 48, 59)`.

Replace the nine-byte heading at `0DB4` with complete GC `Your Loan` from
`.data:00081028`. Replace the three-byte button slot at `0DC0` with `OK` from
`.data:00081034` and one zero padding byte, changing the actual draw length at
`80898384` from three to two. Retain heading length nine and both native string
pointers. These are drawn text, not the previously translated asset labels.

Centre both shorter English labels on the original native text centres using
the installed width table and 0.9375 scale. `Your Loan` is 54 pixels unscaled:
heading origin 133 becomes 158 (ideal 158.3125). `OK` is twelve pixels: origin
213 becomes 224 (ideal 224.25). Change only the corresponding immediate float
constants; keep Y, colour, selected-state logic, font scale, and all transaction
code. Preserve the whole asset `00ACC000`, including existing English imagery.

## Bounded verification

Bind exact source/candidate hashes, GC strings/symbols/actual texture relocation,
all changed native words, complete relocation headers/entries, parent metadata,
the existing font metrics, and assembled adapter code. Check relocation at
several valid loaded addresses and preserve the original fixed main-code call.
Check both adapter branches against the native calling contract, including
the unexpanded five-byte stack copy and complete English pointer/length.
Verify all unrelated resources, every earlier fix, and complete UPS application.
One focused drawing check may cover both menus when setup is available; ordinary
hardware appearance remains a playtest check, not inferred from these guards.
No save migration is required by this presentation-only correction; new-build
loading and save/restart evidence must still be distinguished from that fact.
