# English title asset route

## Priority and scope

The title screen is the user's first image-replacement priority after the main
port. Use the supplied English GameCube artwork and preserve its intended
appearance; do not redraw it from memory. Other Japanese text-bearing images
remain in the image inventory. The main logo is an animated collection of
textured letter pieces, not one flat title bitmap.

The source extractor and lossless texture conversion are implemented; native
drawing/animation integration is pending. No title replacement is installed,
and no actor, font metric, or transition changes.

## Supplied English source

The local `GAFE01` decompilation binds the logo in `ac_animal_logo.c` to three
animated skeletons: `logo_us_animal`, `logo_us_cros`, and `logo_us_sing`.
Their model sources describe CI4 letter textures, separate sixteen-entry
palettes, vertices, and keyframe data. Repeated local palette/letter symbol
names occur at different `.data` offsets; extraction must use their scoped
offsets, not the first matching symbol name.

Four I4 background pieces are each 64 by 128 pixels. The trademark texture is
I4, 32 by 32. Separate `log_win_logo3_tex` and `log_win_logo4_tex` supply two
64-by-16 IA8 Press Start tiles. The supplied actor source draws those tiles at
X 96 and 160, Y 159, with its existing opacity and colour choices. Nintendo
notice textures are separate again. Do not mistake Press Start for the main
logo or combine notices into the letter animation.

The extracted `foresta.rel.szs.decoded` is 15,640,056 bytes, SHA-256
`29306a927eee861b073c571408393f99cb384048684eee4bff3d219725429837`.
Its file-backed `.data` begins at file offset `002DD340`, length `00ADF4F8`.
The model/split inventory places title-related data, including the notices,
at `.data:005E5020..005F3CD8` (exclusive end), 60,600 bytes, SHA-256
`7c6ad2869ec1e3760b134c8fcc073518590beeeb2204dddf3e3232ea3d26303c`.
These bounds and hashes are checked against the supplied extraction. Decompilation
bindings identify intended asset roles; a native installation needs its own
machine-code and display-list checks.

## Native destination

The verified Japanese cartridge's `ovl_Animal_Logo` uses VROM `0095FEC0`,
RAM `80A9FC70`, and 9,952 file bytes, SHA-256
`2c91de2e6987199c74b092698a3e656bc023ad0fd924b32e4a7aeb4ffc177a01`.
Its 608-byte relocation file is VROM `009625A0`, SHA-256
`5642d27903df612f39d052b66682acaf2d4a634d878fcd8da05246fa50d1e29b`.
The pinned native split describes no BSS. Original function bodies still need
the dedicated drawing/asset-pointer audit; GameCube addresses and Dolphin
display-list extensions cannot be copied into the N64 executable.

## Extracted assets and texture conversion

`python3 tools/title_assets.py` writes 80 independently scoped source assets and
28 converted textures under ignored `build/title-english-assets/`. The manifest
binds the full supplied REL, the symbol map, the complete title region, every
raw asset, and every output. Repeated local names use their section offsets in
filenames. Geometry, keyframes, display lists, and unrelocated pointer fields are
retained as source data, not presented as ready-to-execute N64 commands.

The eighteen letter textures expand their scoped RGB5A3 palettes to row-major
RGBA32 without colour or alpha quantization. The five intensity-only textures
become row-major I4. Five eight-bit intensity/alpha tiles, including the two
Press Start tiles and three separately retained notices, become N64 IA8.
GX four-bit textures use 8-by-8 blocks; GX IA4 uses 8-by-4 blocks and stores
alpha above intensity, requiring a nibble exchange for N64 IA8.
The format interpretation is checked against the
[Dolphin texture decoder](https://github.com/dolphin-emu/dolphin/blob/master/Source/Core/VideoCommon/TextureDecoder_Generic.cpp)
and the pinned GameCube texture commands; no Dolphin implementation is copied.

The converted texture payload is 263,680 bytes. This is stored asset size, not
a demonstrated runtime allocation or TMEM budget. The renderer still needs
bounded texture strips/tiles, source geometry, and animation integration.
The exporter checks the 23 model-texture dimensions against the actual supplied
display-list commands. Equal byte counts cannot distinguish a 48-by-64 letter
from 32-by-96 or a 64-by-32 piece from 32-by-64. Five focused tests pass, including
wrong-shape rejection, repeated-symbol scoping, all tile edges, exact palette
expansion, and complete real-source extraction. No image or ROM is published.

## Native drawing and allocation observations

The constructor at `80AA1C5C` loads the original title asset range
`01336000..0134BCD0` into separately allocated memory and stores its pointer at
actor offset `02FC`. The draw body at `80AA19CC` installs that pointer as segment
six and draws six Japanese logo pieces through `80AA0C98`. The actor size is
`0328`; its state, transitions, and allocation ownership must remain explicit.

The Press Start body at `80AA1458` draws three native IA8 64-by-16 tiles from
segment offsets `1110`, `1510`, and `1910`. Its X positions are 74, 138, and 202;
all three Y positions are 154. The English reference uses two tiles at X 96/160,
Y 159. The native renderer's third tile must be deliberately removed or made
transparent; replacing two textures alone leaves Japanese pixels behind.
These observations are from the source-hash-bound native disassembly at
`build/title-native-disassembly/code.asm`, not an installed patch.

## Implementation and acceptance still required

- Resolve native title textures, palettes, geometry, animation, and lifetimes
  from the actual actor and assets. Separate drawing from start/menu, clock,
  save-data, and selected-player transitions.
- Extract complete scoped English assets with hashes. Verify texture packing
  and palette formats, and convert only representation where the N64 requires it.
  Retain source dimensions, transparent edges, colours, letter placement, and
  animation intent; keep extracted/repacked assets local.
- Choose a guarded cartridge asset/drawing integration that fits four MiB and
  preserves native actor allocation and transition behaviour. Verify texture
  memory, display-list bounds, relocations, and complete frame guards.
- Test initial appearance, animation, Press Start, input, menu transitions,
  return-to-title, and existing-save handling silently, then on original hardware.
  Release only the patch and original tooling after provenance review.
