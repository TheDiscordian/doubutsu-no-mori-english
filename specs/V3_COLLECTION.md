# V3 native item collection

## Implemented scope

`--collection` connects native item collection and live-player clearing to the
four imported-furniture catalogues in [V3 save state](V3_FLASH_RUNTIME.md).
It includes the existing FlashRAM runtime. The catalogue screen's list,
preview, completion, and ordering paths remain separate implementation work;
this switch does not claim a complete playable item or expose web selections.

Both web patchers remain V2. The saved format, required imports, memory bounds,
and compatibility warning are unchanged from the FlashRAM runtime. V3 saves
must not be loaded in V2 or earlier experimental formats.

## Native contract

`mPr_SetItemCollectBit` at `800B88EC` records the current player's ownership.
The active private-data pointer is at `80136FD8`. The four native saved player
records begin at `80126EC0`, with stride `BD0`. Determine the slot by exact
pointer equality with those four record starts, not a guessed player number,
range-only check, or catalogue offset. A visiting player can use separate
`g_foreigner_private` storage at `801439A0`.

Original furniture collection uses thirty words at private offset `AF0`.
Those 960 native bits do not hold extended furniture indices. Original paper,
wall, floor, music, clothing conversion, and excluded gift-category rules retain
the native implementation. Imported `3xxx` IDs instead use their selected
registry group, `(item & FFF) >> 2`, in the correct player's 128-byte V3 catalogue.
All four rotations share a bit. Unknown or disabled imports are not credited.

`mPr_SetPossessionItem` at `800B8B08` updates pockets/conditions and invokes
collection only for condition zero. `mPr_SetFreePossessionItem` at `800B8B8C`
finds a free slot and calls that setter. Both full native functions remain
unchanged, including wrapped-present and quest-item behaviour. The collection
hook also covers other direct callers of `mPr_SetItemCollectBit`.

`mPr_ClearPrivateInfo` at `800B7ADC` clears one complete native private record.
The V3 wrapper clears the matching imported catalogue when that record is one
of the four resident slots, then invokes the original implementation. Clearing
a temporary/passport record does not clear any resident's imported collection.
The save-state guard is checked before clearing a resident's data.

`af_v3_catalogue_owned(private, item)` queries imported ownership without writes.
It returns zero for unknown/disabled IDs, an invalid private pointer, or an item
outside the supported range. It is an internal API for the upcoming menu work;
the current catalogue screen does not call it yet.

## Memory and guarded installation

The collection helper occupies `804699C0..80469BB7` (504 bytes), within the
existing loaded 48-KiB prefix. ABI 15 adds no resident allocation or saved bytes.
Its entries are record at `804699C0`, query at `80469AD4`, and private clear at
`80469B50`. Two original-function bridges occupy `8046BA80..8046BA9F`, after
the FlashRAM bridges and before the existing end guard.

The installer validates complete native collection/clear function hashes and
the unchanged acquisition pair. It binds the actual compiled save guard,
warning, codec collection, and furniture-selection symbols. The save guard is
the existing `require_state` function at `804692F4`; the linker alias is accepted
only with that exact compiled symbol. The FlashRAM runtime code remains
unchanged. Unknown function bodies, moved dependency entries, or overlapping
resident bytes stop construction.

## Remaining player-lifecycle work

Controller Pak transfer requires its own imported profile/catalogue transport.
Acquiring a selected imported item while the active record is not a resident
slot stops with the existing V3 safety warning instead of crediting another
player or silently discarding ownership. This is a development limitation,
not completed visiting-player support.

`mPr_CopyPrivateInfo` at `800B7F48` is the native `BD0`-byte copy used by
Controller Pak return paths. It does not yet transport V3 ownership; copying a
passport record must be handled together with the complete Pak format and
profile policy, not by copying a resident's unrelated catalogue. Broader player
transfer/deletion paths remain subject to that implementation review.

## Next catalogue integration

The current translated catalogue is VROM `03970000`, relocation `03980000`,
linked at `808A6100`; the complete-name adapter and its 63 cached names stay
intact. Each category currently has 444 item slots and a 966-byte stride.
The furniture ordering table at native `808AEB84` contains 436 four-byte rows.
Both preview lookup (`808A6600`) and list construction (`808A9460`) use that
count. The two pilots fit the current list capacity; a larger imported set
requires reviewed expansion, not merely raising the loop bound.

List construction at `808A9470` calls the native catalogue-bit reader
`808A931C`, which indexes original ownership. Its return-to-item arithmetic at
`808A9488..808A9490` assumes `1000 + index * 4`. Preview initialization at
`808A629C..808A62A4` independently assumes `(item - 1000) >> 2`, and its program/
profile loading uses catalogue-local tables at `808A9888`/`808AD3B8`. Connecting
the room renderer alone does not connect this second preview loader. Preserve
model allocation, scale, lighting, order eligibility, and the complete-name
adapter when adding the imported paths.

Focused verification is recorded in
[the collection checkpoint](../docs/checkpoints/V3_COLLECTION.md). Acquisition
function fixtures do not establish an ordinary shop/reward route or hardware
acceptance. Complete catalogue menus, item scoring, ordinary acquisition and
placement, houses/move-in, and Controller Pak support remain required.
