# Complete accented item names

## Exact source identities

The final eight wide-resource fields represent four names:

| Native records | Complete GC name | GC code | Native complete-pair encoding |
| --- | --- | --- | --- |
| `item_24:00A8`, `item_10:0A4C..0A4F` | café shirt | `7C` | `807C` |
| `item_25:0005` | Pokémon Pikachu | `7C` | `807C` |
| `item_2A:0031` | Café K.K. | `7C` | `807C` |
| `item_2A:0033` | Señor K.K. | `87` | `8087` |

Native clothing spelling is `あかチェッカーのふく`; all four placed rotations
must match that carried source. The remaining native names are `ポケピカ`,
`けけパリ`, and `セニョールけけ`. Preserve complete reference spelling and
accents; do not import the donor's alternate Unicode aliases as different glyphs.
The zero-filled furniture sentinel `item_10:0ECC` is not one of these fields.

## Separate font resource

The sixteen-cell profile retains the complete preceding fourteen glyph cells,
their codes, pixels, order, and advances. Slots fourteen/fifteen contain actual
GC `87`/`12` (ñ/Ñ), both six pixels wide. The guarded donor uppercase table maps
`87` to `12`, just as `7C` maps to `0A` (é/É). No native atlas, existing glyph,
line break, or timing value changes. The resource remains 1,600 bytes and uses
the two previously unused twelve-pixel cells in its existing row.

`tools/extended_glyphs.py --mail --accents` extracts this explicit profile from
the verified supplied disc. The original five/fourteen-cell profiles remain
unchanged; the old validators must not silently accept the new mapping.

## Installation boundaries

Resource extraction alone does not credit applied translations. Item approval
must bind exact native and full GC reference hashes, original placed/carried
conversion, both complete encodings, and sixteen-byte capacity. Ordinary short
bank imports must not gain extended-glyph permission from the wider resource.

All complete item readers must retain complete pairs and use the matching font.
The original generated-letter capture rejects `7F/80` literals, and catalogue-four
assembly deliberately retains that restriction. Adding accented item bytes to
the item resource without connecting capture/restoration would fail letter
creation. A new immutable assembly identity must support registered literal
pairs and accented capitalization while old catalogues retain their semantics.
The 122-byte snapshot envelope and sixteen-byte field capacity remain unchanged.
Unknown/truncated pairs, commands in literals, overflow, or a missing font reject.

The resident image has no linked headroom. Additional consumers must use a
checked owned extension or an explicitly revised memory layout; do not overwrite
test scratch or assume the user's Expansion Pak permission changes heap bounds.
Implement the font, item approvals, capture, reconstruction, and installed-route
verification before enabling the complete accented resource. Bounded native
checks cover the new consumers; unchanged broad mail cases reuse prior evidence.

## Immutable letter interpretation

Catalogue five uses assembly semantics three and retains every catalogue-four
template, part identity, payload checksum, and manual break. Only the catalogue
and semantics header words differ. Its 326,288-byte resource SHA-256 is
`26b2e95b10b8ae049853ecc6180e41c12b86efc677e39ee03f9742077e9005be`;
the installed VROM is `03100000`. Installation checks the actual DMA ranges.
Catalogues two through four remain unchanged and keep their literal restrictions.

The new capture accepts complete pairs only inside the four exact item names,
including their sixteen-byte space padding. The formatter recognizes the sixteen
registered pairs in catalogue five, preserves complete tokens, supports accented
initial capitals, and rejects malformed data or overflow before publication.
The byte-counting line reader uses exact pair advances and retains manual breaks.

Generation upgrades catalogue-four selection to five only when a selected field
contains a pair. Unused capture slots do not change the saved interpretation.
The native shop leaflets select catalogue two; only their sixteen classic sale
templates, IDs `0002..0011`, permit the same upgrade. All three parts of every
one of those templates must match catalogues four/five exactly. No other
catalogue-two or catalogue-three selection receives that permission.

Treasure notices retain the native 96-byte envelope. The new packer upgrades only
the exact item field and leaves the caller's record unchanged. The new validator
and decoder accept catalogue four with its original restrictions, or catalogue
five with an exact accented item in field two. Player/town/name fields do not
gain pair permission. The existing town-heading correction, native field masks,
source lengths/checksums, and formatting order remain intact.

The bound article resource changes five rows: the four carried names and the
placed-clothing group. Actual donor tables give `a` for café shirt and Pokémon
Pikachu, and no article for either K.K. song. Each row retains the full encoded
sixteen-byte name checksum, and every other row remains unchanged.

## Owned code and installation

`build/accent-mail-font` contains the complete font/world-label/mail core:
11,344 image bytes and 672 relocation bytes. The system allocation is 12,031
bytes, within the existing loader's image/relocation limits. Neither the linked
resident image nor the heap boundaries grow. Startup checks all four resident
mail entry pairs before installing the font/world hooks, then publishes the mail
hooks without a later fallible operation. The unchanged snapshot codec and CRC
functions remain exact resident imports. The production validator rejects
candidate-only reports and altered code, imports, sources, hook tables, or cells.

The common and sale-event creators use forty-byte tail bridges through the
existing owned font pointer at `80199F04`. The bridges preserve all argument
registers and stack arguments; an absent owner returns failure without writing.
Common-creator and board-reader treasure adapters append 2,256 code bytes and
retain every unrelated prefix byte and relocation. The common creator is 60,400
image bytes with 944 relocation bytes. The board reader is 26,560 image bytes
with 816 relocation bytes, within its existing 27,264-byte reservation. Its
native owner metadata uses the existing seasonal allocation. The sale actor
retains its 38,128-byte image size. Neither the shared submenu pool nor resident
image grows.

`tools/accent_mail_overlay_profile.py` binds each complete image, relocation,
metadata report, and reconstructed prior prefix. `tools/accent_items_install.py`
rebuilds from the exact original cartridge, retains original native DMA indices,
orders appended resources by VROM, and verifies all prior payloads except the
explicitly approved updates. It binds the exact full-name hash across existing
letter/shop consumers and verifies patch reconstruction. The combined counter
requires this complete installation before accepting the eight exact source-bound
accent fields; ordinary bank imports still reject extended pairs.
