# V3 imported clothing stock

## Scope

The clothing build adds selected cherry shirt `34BF` to the native A clothing
list, preserving original garments, B/C lists, seasonal eligibility, town
rarity, duplicate filtering, and one RNG draw per selection. This connects
stock generation and native acquisition; shop mannequins, catalogue display,
and ordinary payment remain separate implementation work. Neither patcher changes.

## Resource and selection

The complete source and donor hashes are recorded in [shops](V3_SHOPS.md).
The donor places its cherry shirt in the 32-item all-season prefix of A.
Native `24BF` is a different garment and remains present.

The resource at `011E5000` retains its original 560 bytes except pointer A at
`1F0`, then appends an expanded A list at `230`. Imported `34BF` occupies index
32, after the original all-season entries and before all original seasonal
entries. The original terminator is retained. Fourteen padding bytes bring the
resource to 720 bytes. Its SHA-256 is
`79ce16a16412af730b46d10e2946490a42fe7bfd2e1ac9c40d819b7d87e73e4a`.
The descriptor becomes `011E5000 011E52D0 060001F0` at `8010DAB8`.
No DMA row is added. The existing size-derived allocator, transfer, and free
paths handle the additional 160 temporary bytes; no resident buffer grows.

Native caller `800BFE4C` retains its output-pointer delay slot and instead calls
the eight-byte bridge at `80460F60`. The bridge passes the selected list from
`s1` to `af_v3_clothing_stock_index` at `80460DE4`, preserving the return address.
Only that call word and the descriptor end change in main code. Installation
validates complete selection, allocation, and original seasonal-helper hashes.

Unchanged B/C lists call the original seasonal helper. Expanded A requires both
the selected profile bit and validated garment resource. Selected A has 33
all-season entries, with unchanged native month/season mapping and seasonal
counts. Unselected or unavailable A calls the original helper and skips the
inserted slot when mapping its result. Each route consumes one native RNG draw;
the native caller retains list priority, special lists, and duplicate rejection.

## Memory, retention, and compatibility

ABI 37 identifies the build. The asset helper occupies 3,700 bytes at
`80460100..80460F73`, leaving 140 bytes before the object table. The new C
function uses a 40-byte frame. Existing public function addresses remain fixed.
Appending code moves the existing `V3 clothing` DMA diagnostic string from
`80460DE4` to `80460F68`; its sole address immediate changes at `80460B54`.
All other retained helper instructions and the complete string are unchanged.

The saved format remains 2, selected profile 192 bytes, working state 832 bytes,
and guarded runtime 864 bytes. ABI-36 saves with the same selection retain their
representation. Older format-1 V3 builds and V2 cannot load format-2 saves.
The ordinary wear/save/reload evidence remains attached to its unchanged code
and actual tested build, not described as a new stock-build playthrough.

See the [checkpoint](../docs/checkpoints/V3_CLOTHING_STOCK.md) for verification.
