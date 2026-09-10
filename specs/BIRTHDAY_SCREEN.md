# English birthday window

Replace only the native birthday drawing function with a source-compiled,
read-only renderer. Keep the existing background, animation, selection handlers,
valid-date checks, birthday initialization, and saved month/day fields. Match
the GC presentation with the complete "When's your birthday?" prompt, full
English month name, numeric day, and OK. Draw the words through the installed
English font, rather than importing a second font or altering saved date values.

## Ownership and bounds

The native owner is `0079DA50`, RAM `8089A350`, 2,336 bytes, SHA-256
`96c2b38dff3968ed6c138cfe83b5daceb8ff11b116a543ee6ac96f3ab58f10e8`.
Its drawing function occupies `8089A684..8089AA8F` (1,036 bytes).
The compiled replacement is 800 bytes with a 136-byte stack frame, compared
with the original 232-byte frame. Clear only its unused function tail. Other
owner code/data and its sixteen-byte BSS remain unchanged.

Relocation file `0079E370` is 192 bytes, SHA-256
`976c3542d4cddf142d26c2b36562f50f5532c8ff92e8701e4720367f8ba0c736`;
native section sizes are `(2272, 64, 0, 16)`. Remove the six relocations belonging
to the old drawing function, retaining the other 35 in their original order.
The new function imports only five absolute native calls; immediate floating-
point constants avoid additional local pointers. Retain the complete original
relocation-file size and trailing size word, with zero-filled unused entries.

The 22,208-byte asset `00ADD000` has original SHA-256
`e0f0c6847214f1c116448e2172c02639d379795f3e14531cbdb5094ad7a9c0a6`.
Reuse the two obsolete Japanese suffix images' combined 512-byte area
`2DB8..2FB7` for read-only English strings: prompt at `2DB8`, twelve ten-byte
month slots at `2DD0`, a bounded invalid-month marker at `2E48`, and OK at
`2E52`. Replace the two 72-byte suffix load/quad/draw blocks at `0AB8` and
`0B08` with native no-ops. No remaining display-list command reads those strings
as texture data. All other asset bytes remain unchanged.

## Native contracts

The original entry arguments are submenu, menu-info, and game pointers. Read
submenu overlay at +`2C`, birthday state at overlay +`10710`, asset pointer at
menu +`28`, menu X/Y at +`18`/+`1C`, and graph at game +`0`.
The state contains month/day unsigned halfwords at +0/+2 and selection index
at +4. Read only; no state is written. Out-of-range months display `?` without
reading outside the fixed string table.

Retain native scale (16,16,1), translation (X,Y,140), graph front/back ownership,
segment C, model-view matrix, background mode/model at `0C000740`/`0C0012C8`,
and the original scrolling tile-size calculation with a factor of two and
seven-bit mask. Use the original submenu font-matrix callback at +`106B4`.
Imports are matrix scale `800E041C`, translate `800E0314`, graph matrix allocation
`800E13C4`, the existing two-digit formatter `8009264C`, and font `80090E98`.

The full GC prompt is bound at `.data:0007A6FC` in the supplied REL. Prompt,
day, and OK positions follow the GC layout: (119,88), (171,124), and (198,124),
offset by the native moving window. Month text begins at (97,124), with enough
room for September before the day. Prompt scale is 0.875; the three fields use
1.0. Native selected/unselected colours remain (195,0,0)/(70,145,225).
Month/day/OK retain selection indices 0/1/2. Native font flags and numeric
formatter arguments remain unchanged.

Bind the compiled sources, five external call sites, complete old sources,
original reader blocks, and all preserved resources. Verify relocation at
multiple ordinary-heap addresses, drawing output, text lengths, read-only state,
and allocation/stack guards. Add the two discovered embedded strings to the
common text inventory, with installed-renderer verification before credit.
Measurement reads the 800-byte renderer from the cartridge, requires its exact
approved hash, and verifies the complete reconstructed owner, relocation, assets,
and source-bound report. It must not require a retained development compilation
folder. Compilation itself still checks its ELF call inventory and metadata.
Native screen execution and ordinary hardware/date entry remain separate
acceptance; neither compilation nor a host drawing check implies those passed.
