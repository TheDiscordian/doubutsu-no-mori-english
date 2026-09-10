# Regional donor and native artwork review

## Island-cottage panel

The GC source `obj_s_house_i_3_us_tex_txt` at `.data:52BFC0` is not a native
player-house sign. The pinned `src/actor/ac_cottage.c` binds its skeleton and
window model in `Cottage_data` to `aSTR_TYPE_COTTAGE_NPC`, `aSTR_PAL_HOUSE_I`,
and the island villager's cottage. The native structure enum ends at `2E`, and
its actor table has no cottage profile; it has the five ordinary resident-house
types and three player-house types instead. No cottage model is added to N64.

The decoded 32×64 CI4 GC panel contains a circular log-like ornament, wood, and
blank plaques, with no readable wording. Its neighbouring complete textures
and this image do not match the original N64 image storage in the bounded
exact-source search. Absence of a match alone is not the feature proof; the
actual cottage binding establishes why this donor is outside the native game.
This closes the regional donor lead without changing native houses or claiming
that every native house image is reviewed.

## Native gloom reaction

The N64 effect controller's 20-byte overlay-table entry `0B`, at RAM `80A19C6C`,
binds VROM `008F56A0..008F5A20`, RAM `80A2DC00..80A2DF80`, with profile
`80A2DF30`. The init routine at `80A2DD08` passes effect ID `0B`. Profile draw
pointer `80A2DF3C` selects `80A2DDC0`; its final draw emits display list
`0600CF88`. The controller's model-table row at `80A1A494` is
`0600CF40..0600D820`. Its loader at `80A19170` skips the eight-byte section header
and adds VROM base `01410000`; the draw controller binds the matching segment 6.

The complete loaded model/texture section is `0141CF48..0141D820`, 2264 bytes,
SHA-256 `a11904af05e721a8571ff3f9946687b87d124140d7b9154136a30c786fea4b95`.
At `0141CFC0`, the actual material loads texture `0141D020`; its render-tile
command specifies IA8 and its tile-size command specifies 64×32. The four
vertices are at `0141CF48`. The complete 2048-byte texture SHA-256 is
`5406e6422aab88f4a2f0d987f932b0f83501ba8e76f4efaa2b812c4cf810c4df`.
Direct decoding shows staggered vertical lines, not Japanese lettering.

The GC replacement uses two scrolling intensity textures and different effect
code. Importing it would change a language-neutral reaction, not translate a
Japanese label. Retain the native effect, timing, allocation, and sound code.
No emulator or audio playback is used for this inspection.

These complete owners remain unchanged in playtest 05:

| VROM | Bytes | SHA-256 |
| --- | --- | --- |
| `008E0A30` | 14144 | `01a72c566b8198e20ec5d2659ab3d58e7fb26e2bff460a33952ee1ff0945ac75` |
| `008E4170` | 1328 | `79c3813b5cbf68b2c3ab3825bfa4d4cbef4e3cc546afdcee369a79bea6961b1e` |
| `008F56A0` | 896 | `4ffb2a77125479fd19d010c58b842d337d6012848093e352b64b766739b86f41` |
| `008F5A20` | 96 | `74b3650daacffb031f17ff4a3eca1fc4366b4a9be736d71a8e32d73439c766d9` |
| `01410000` | 93328 | `daba24d2339b983ce39646017cf9685174ae5e074d5ad0599e6fe962fbfef952` |

Local disassemblies are `build/disassembly/regional-effect-review/code.asm` and
`build/disassembly/gloom-review/code.asm`. They use the verified original ROM
and pinned public compiler image. The decoded image is
`build/artwork-inspection/native-gloom.png`.

## Three shop drapes

The source-matching inventory identifies three unmatched CI4 64×64 images in
shop rooms. Direct inspection shows the same red-and-white ceremonial drapes
and rosettes, without readable Japanese wording:

| Image VROM | Palette VROM | Texture-load command |
| --- | --- | --- |
| `013B4B88` | `013B0968` | `013B0168` |
| `013CA410` | `013CA130` | `013C9098`, `013C9178` |
| `013DAB30` | `013D6710` | `013D59B0` |

The current candidate retains these three complete textures and palettes.
Their common texture SHA-256 is
`993fc15ee4c3e4101b309de80fef14755c269f9015ad79be6410ad2aaf98388d`;
their common palette SHA-256 is
`b0af81084ba9c7531bdaf673f17491c003dc83a0bcb27bb608407e2f97db10fb`.
Retain them; an unmatched donor search is not a reason to replace neutral art.
Their local views are `shop1-unmatched.png`, `shop3-unmatched.png`, and
`raffle-unmatched.png` under `build/artwork-inspection/`.

## Inventory evidence and limits

`tools/artwork_matches.py` produces `build/artwork-matches-01.json`, SHA-256
`424fb279c90e7ac27a30ecbdf6c578b58cdfaeb3cd8549148a2d866816ad276f`.
It binds 6642 named GC texture sources and finds 1170 native material candidates:
942 exact format/dimension/texel matches and 228 unmatched candidates. Six
focused tests pass in 0.064 seconds. The known Japanese police poster is
unmatched, while its already installed English replacement matches the correct
GC source, as does the installed English WELCOME sign; a native house-window
image matches its named donors. Repeated
material commands retain one image identity.

This is a review aid, not complete artwork coverage, visible palette matching,
active display-list reachability, or a translation percentage. Dynamic and
cross-segment readers and unsupported formats remain explicit exclusions. The
report preserves their counts; it does not count them as translated. No cartridge,
patch, save, shared text credit, or existing report is changed by the inventory.
Use unmatched images and neighbouring named matches to select the next bounded
review. Do not rerun the regional or shop-drape inspection unchanged.
