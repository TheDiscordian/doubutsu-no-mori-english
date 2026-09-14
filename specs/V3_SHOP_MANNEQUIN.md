# V3 shop mannequins

## Scope and native owner

The clothing build recognises selected imported garments in the native shop's
mannequin count and tile search. The actor keeps its original model, collision,
texture/palette buffers, sold marker, animation, allocation, and cleanup.
This is the shop actor, not the furniture representation used for displaying
a garment at home or previewing it in the catalogue.

The complete 4,192-byte owner is VROM `0084E080`, linked at `809592B0`, with
SHA-256 `4381a0683e999c14da2a9c75898203710842ff2b35fee8b5ce5b02ceb6ba67b0`.
Its 160-byte relocation resource is VROM `0084F0E0`, SHA-256
`7041005848b758b0ef7e97ebfae4267697a2daa7b5108c403b16a8a95034fb68`.
Sections are 4,064 text, 64 data, 64 read-only data, and zero BSS bytes, with
32 relocations. Its native descriptor is at `801012D0`; loaded owner address
is at `801012E0`. None of these sizes or allocation fields changes.

## Checked decisions

Six sixteen-byte windows replace paired clothing bounds and their branch:
`80959320`, `80959348`, `80959370`, `80959398`, `809596C8`, and `8095972C`.
The first four are the unrolled count loop; the last two search even/odd tiles.
Original `24xx` uses the native fast path, including valid index-zero `2400`.
Higher IDs use mode 3 of the existing full-register query at `804680B8`.
Only a checked selected garment supplies a nonzero imported render index.
Unknown, missing, and unselected garments are excluded. Full IDs remain in
the native grid and mannequin slot; sold marker `1F35` retains its native path.

The adapter retains lower-bound delay effects and reproduces the count's
branch-likely increment only when taken. Search uses the original no-op delay.
Every continuation resolves through the actual loaded-owner pointer. Complete
source hashes, all six bounds, exact instruction words, displaced relocations,
incoming interior branches/pointers, and compiled dependencies are validated.

The native foreground and reload loops already subtract `2400` from the full
sixteen-bit item. Their calls at `80959B20` and `80959FE0` therefore pass imported
index `10BF` to the installed shared reader without further edits. Slot stride
stays `54` hexadecimal, item offset `14`, texture pointer `18`, palette pointer
`1C`. Texture/palette sizes stay 512/32. The naked mannequin still uses index FF.

## Memory and compatibility

ABI 38 uses 840 bytes at `80464C00..80464F47`, leaving 184 bytes before the
furniture helper at `80465000`. The preceding 238-entry selection shuffle
array ends at `80464BB8`; installation explicitly checks its declared capacity
against the new code start. The linker forbids growing past the furniture
helper. There is no additional resident allocation, actor growth, texture-bank
growth, or saved-format change.

The adapter reuses the existing register-preserving query frame: 32 bytes at
the call site plus the retained 256-byte wrapper and checked C query. Native
garments take the short branch without that query. Continuations use a separate
16-byte frame after the query returns. Both web patchers remain V2.

See the [checkpoint](../docs/checkpoints/V3_SHOP_MANNEQUIN.md) for the exact
current build and verification limits. Catalogue/home display, normal shop
purchase, and whole-scene rendering remain independent work.
