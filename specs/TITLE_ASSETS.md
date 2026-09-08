# English title asset route

## Priority and scope

The title screen is the user's first image-replacement priority after the main
port. Use the supplied English GameCube artwork and preserve its intended
appearance; do not redraw it from memory. Other Japanese text-bearing images
remain in the image inventory. The main logo is an animated collection of
textured letter pieces, not one flat title bitmap.

This document records source discovery, not an installed replacement or verified
native drawing patch. No title asset, actor, font metric, or transition changes.

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
