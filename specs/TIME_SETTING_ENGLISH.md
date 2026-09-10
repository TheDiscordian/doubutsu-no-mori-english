# English native time-setting screen

## Scope

Translate the four embedded native clock-screen records and align their editable
values for the installed halfwidth font. Keep the original year/month/day/hour/
minute selection order, value limits, time arithmetic, RTC writes, animation,
and save interaction. The GameCube's separate month-name/weekday-art redesign
is not needed to make the native picker English and is not represented as
installed by this adapter.

Use the exact supplied GameCube `Adjust the clock.` and `OK` strings at
`.data:00083EA4` (17 bytes) and `.data:00083EB8` (two bytes). The Japanese
year/month/day suffixes become an unambiguous `20YY-MM-DD` display, preserving
the native year-first control order. The hour/minute suffixes become `HH:MM`.
These are explicit native-layout adaptations, not copied GameCube date layout.

## Native boundaries

Owner VROM `0078AE30`, linked RAM `808831A0`, 4,272 bytes; relocation VROM
`0078BEE0`, 208 bytes. The [screen checkpoint](../docs/checkpoints/SCREEN_ARTWORK.md)
records complete native hashes. Sections `(4128, 144, 0, 32, 46)` remain unchanged.
The four source records are at `808841E0`, `808841EC`, `808841FC`, and
`80884204`, with lengths 9, 14, 5, and 3.

Repack only their existing 40-byte data span into four aligned fields:

| Address | Capacity | Read length | English |
| --- | --- | --- | --- |
| `808841E0` | 20 | 17 | `Adjust the clock.` |
| `808841F4` | 12 | 10 | `20  -  -  ` |
| `80884200` | 4 | 1 | `:` |
| `80884204` | 4 | 2 | `OK` |

The date's blank pairs are occupied by the existing editable two-digit values;
the fixed `20` prefix remains native. Require digit, space, and hyphen advances
of six pixels and a colon advance of three pixels in the installed font. The
native text scale remains 0.875. Date text begins at `(122,115)`, year digits
at `(132.5,115)`, month at `(148.25,115)`, and day at `(164,115)`. Time digits
use `(102,137)` and `(115.125,137)`, with the colon at `(112.5,137)`.
The title uses the GameCube `(131,82)` position; the shorter native OK label
starts at X 190 inside the existing confirmation area.

Only eleven existing instruction immediates change: title/date/colon/OK
coordinates, string lengths, and the two moved string addresses. Retain all
font-call targets, numeric formatter, selection-dependent colours, native
return/stack handling, and the complete relocation file. Verify the modified
owner at two heap placements, including the new low-address fixups. No new
resident code, buffer, allocation, asset, branch, or saved field is introduced.

## Accounting and checks

Add all four Japanese source records to the combined ledger for every measured
build. Credit them only when the complete installed owner, relocation, widths,
positions, and reader instructions match the checked English profile. An older
build gets the same newly discovered source denominator without credit.
Numeric separators replace the Japanese unit semantics through the verified
complete date/time composition, not a guessed English resource elsewhere.

Focused checks cover exact donor wording, full glyph representability, bounded
reads, numerical alignment for all supported two-digit values, retained owner
state/code, independent instruction assembly, two-base relocation, all previous
cartridge resources, and UPS reconstruction. Ordinary clock adjustment and
hardware display remain gameplay checks; font-call/patch verification does not
claim an RTC write or saved-town round trip.
