# Dynamic-palette player/effect texture review

The four deferred prop/effect candidates have their native palette sources
resolved. Direct inspection finds no readable lettering in these selected
textures. Retain them; this is neither newly applied English nor a claim that
every dynamic material is reviewed. No ROM or runtime change is needed.

The native input is the verified original. The checked RC4 SHA-256 is
`5930435f588947df35313ae9cc2ea301af9fc7e68d59a7d8e13a48741d4f3067`.
The candidate inventory `build/artwork-matches-01.json` has SHA-256
`424fb279c90e7ac27a30ecbdf6c578b58cdfaeb3cd8549148a2d866816ad276f`.

## Player palette binding

Actor owner `007AC420` starts at linked RAM `808B2D50`. Segment-12 setup at
`808BFBE4..808BFC1B`, VROM `007B92B4`, emits `DB060030` and calls `800B1BB8`
for the palette pointer. This sequence hashes to
`b8e0d046e40bbf07711600b68a4630d3fec66c3f27868f536156a4ec7982ae53`.
Each selected material loads `FD100000 0C000000` before its local CI4 texture.

Accessor `800B1BB8..800B1BE7` returns the loaded face record plus `0E00`.
Loader `800B1A60..800B1A9F` requests `0E20` bytes from the address computed by
`800B16F8..800B1783` (constants hexadecimal):

```text
B8F000 + (face + gender*8 + altered_face*10)*E20 + alternate_bank*1C400
```

The two flag inputs are normalised to zero/one. The complete source owner is
`00B8F000..00BC77FF`, SHA-256
`6bd4934f252181c395fbf9c37636214d6c307fd95382bf2d11e27bdbf56cad54`.
Ordinary face-zero palettes are `00B8FE00` and `00B96F00` for the two native
gender values. The selector at `800B1D14..800B1D67` chooses the native
model/bank pair `06003538`/8 or `06003098`/51 (bank IDs decimal).

| Texture VROM | Dimensions | Inspection palette | Finding |
| --- | --- | --- | --- |
| `00D28180` | CI4 16×16 | `00B8FE00` | Curved colour/shadow boundary, no lettering |
| `00D28380` | CI4 32×8 | `00B8FE00` | Flat grey strip, no lettering |
| `00D2BEE0` | CI4 16×16 | `00B96F00` | Curved colour/shadow boundary, no lettering |

Palette selection, not a guess about which body part uses each tile, establishes
these views. Other face variants are not individually rendered or claimed tested.

## Effect palette binding

CI4 16×16 texture `01411760` loads at `014116F8`. The material references palette
RAM `80120F70`, a BSS address. Function `80086BD0..80086CA3` fills five palette
destinations using tables at `80106638` and `80106738`. Row two binds the
following values (constants hexadecimal):

```text
destination = 80120F70
bytes = 20
source = 0188E000 + 20 * palette_index
palette_index = table_8010674C[word_80136FB0]
```

The index table contains only indices 0 through 11. The complete source has
twelve 32-byte palettes at `0188E000..0188E17F`, SHA-256
`ceaf44d88c0ba641979895a11e74319223f192d79ed3e52fc3aa91d805fee1c3`.
The loader SHA-256 is
`cddd45770b9e283bfb8f355ec0d695b90b3a36c1acfa9d245bf5d29a4e22ea9a`;
tables `80106638..80106793` hash to
`f2962bf9681d85204e41d82feb56969da27441e321498410ba89b9f48c902bdc`.

The existing `build/rc4-town-stick-01/test.bs1` supplies an independent native
check without replaying gameplay: input 8 maps to palette 2, and RAM `80120F70`
exactly matches the 32 bytes at cartridge `0188E040`. This proves an actual loaded
palette, not ordinary visibility of the effect.

Directly decoded palette-0, -5, -9, and -11 views show a small irregular shaded
patch in green, brown, or pale colours, without readable wording. Other colour
variants are bound but not individually inspected.

## Retention and reproduction

All four complete textures, all eight recorded material sequences (48 bytes
before each load through 56 bytes after), both complete palette owners, the
segment-12 setup, and selected main-code loader/accessor/table ranges remain
native in RC4. Retained disassemblies are checked against the complete original
extracted code before their addresses are used.

Seven decoded PNGs remain local in `build/dynamic-prop-review-01/`. Existing
`tools/texture_preview.py` generates each from its listed texture, palette,
dimensions, CI4 format, and scale 8. Example with a fresh output:

```sh
python3 tools/texture_preview.py --address D28180 --palette B8FE00 --width 16 --height 16 --format ci4 --scale 8 --output build/dynamic-prop-review-new/D28180.png
```

No decoder, ROM, patch, save, or gameplay code is modified. This closes the
four deferred image candidates without repeating the 34 completed images or
claiming a new native test, whole-game artwork completion, or hardware acceptance.
