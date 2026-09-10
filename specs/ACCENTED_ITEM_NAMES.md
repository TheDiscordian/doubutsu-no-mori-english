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
Generated-letter capture currently rejects `7F/80` literals, and catalogue-four
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
