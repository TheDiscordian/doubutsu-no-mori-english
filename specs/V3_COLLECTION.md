# V3 native item collection

## Implemented scope

`--collection` connects native item collection and live-player clearing to the
four imported-furniture catalogues in [V3 save state](V3_FLASH_RUNTIME.md).
The clothing variant also connects selected garments to their independent
per-player ownership in [format 2](V3_CLOTHING_SAVE.md).
It includes the existing FlashRAM runtime. The additional
[catalogue adapter](V3_CATALOGUE.md) connects the screen's list, previews,
completion, and prices. Ordinary ordering/delivery remain work; neither switch
claims a complete playable item or exposes web selections.

Both web patchers remain V2. Non-clothing builds retain the FlashRAM runtime's
format and profile. Clothing uses format 2 and requires its selected garment
and display dependencies. Its current display-reader integration retains the
complete ABI-41 save runtime and profile. V3 saves must not be loaded in V2 or
earlier incompatible experimental formats.

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
With clothing enabled, the checked shared item-category reader validates the
selected full garment ID and artwork. `34BF` records clothing bit `BF` in that
player's separate 32-byte catalogue, never the furniture rotation group.
The [display readers](V3_DISPLAY_ITEM_READERS.md) canonicalize selected
`3AFC..3AFF` to `34BF` before recording or querying ownership. All rotations
share that same clothing bit; a mannequin is not a separate collectible.

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
outside the supported range. The catalogue adapter calls this internal API for
extended rows while retaining the original bit reader for native entries.

## Memory and guarded installation

The non-clothing collection helper occupies `804699C0..80469BB7` (504 bytes).
The clothing variant occupies `804699C0..80469BDF` (544 bytes), within the
existing loaded 48-KiB prefix. ABI 33 connects clothing without further
allocation or save-format changes beyond the existing format-2 variant.
Its entries are record at `804699C0`, query at `80469AD4`, and private clear at
`80469B50`. Two original-function bridges occupy `8046BA80..8046BA9F`, after
the FlashRAM bridges and before the existing end guard.

The current clothing display variant redirects only the record/query prologues
to `80466D94`/`80466DD4`. Two additional sixteen-byte bridges at `80466F00` and
`80466F10` retain the displaced instructions and rejoin those original bodies.
The installer verifies the full 544-byte dependency before editing; the clear
entry, remaining collection code, and FlashRAM bridges are unchanged.

The linker pins the public query address and keeps the selected-item check
shared, preserving all three public entry addresses. It rejects overlap with
shop code at `80469C00`. The installer validates complete native collection/clear function hashes and
the unchanged acquisition pair. It binds the actual compiled save guard,
warning, codec collection, and furniture-selection symbols. The save guard is
the existing `require_state` function at `804692F4`; the linker alias is accepted
only with that exact compiled symbol. The FlashRAM runtime code remains
unchanged. Unknown function bodies, moved dependency entries, or overlapping
resident bytes stop construction.
The clothing variant additionally verifies the shared item-category entry at
`8046744C`, whose installed jump reaches the selected garment implementation.

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

## Catalogue integration contract

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

The catalogue adapter implements this contract with separate catalogue-local
index encoding, static resident profiles, retained native DMA, and a relocated
ordering table. Its specification records the actual hooks and pool bound.

Focused collection verification is recorded in
[the collection checkpoint](../docs/checkpoints/V3_COLLECTION.md). Acquisition
function fixtures do not establish an ordinary shop/reward route or hardware
acceptance. Ordinary catalogue ordering/delivery, item scoring, acquisition and
placement, houses/move-in, and Controller Pak support remain required.

## Shared held-parent collection

`--refresh-runtime --held-collection` on the shared installer connects installed
equipment-parent records to the existing collection entry and owned-item query.
It requires the event-equipped proposal and adds no per-item installer or item
list. `v3_held_collection.source_records` verifies the actual donor conversion
contexts, installed parent/selection records, and all nine catalogue lists with
their pointer/count bindings. Fans occupy umbrella-list positions 32–39; their
absence from `mCL_furniture_list` does not justify removing catalogue support.
The same generated records retain category/position for preview integration.

The selected parent reader exposes `af_v3_held_item_collection` at `804A6600`.
It validates the same metadata, readiness, and selected-profile bit as names,
prices, and icons. Parent IDs and all four display rotations resolve to one
collection identity. Unknown or disabled parents do not enter native tool
tables. Original IDs and clothing keep their existing collection implementation.
This function changes no room-placement conversion or saved pocket identity.

The 488-byte record/query adapter starts at `804AFA00`, with the query fixed
at `804AFB00`. Both fit before the existing equipment guard at `804AFFF0`.
The parent reader occupies 1,716 bytes at `804A6000`; its original 1,284 bytes
and public name/price/icon/assembly entries remain unchanged. The display
wrapper retains its 696-byte reservation and redirects only its collection
calls. Existing prior-collection bridges remain at `80466F00`/`80466F10`.
No allocation grows, and startup checksums cover the complete changed module.

Ownership uses the actual canonical display's existing profile bit and the
correct resident's 128-byte collection. The original native pocket setters
still determine whether the acquired condition records ownership. Queries are
read-only, all rotations share one bit, repeated acquisition is idempotent,
and the existing resident-clear hook clears these bits too. Selected imports
acquired by a visiting private record retain the existing safety warning;
Controller Pak transport is not implemented by this adapter. Save format 2,
the current selection profile, and all codec entry addresses are unchanged.

No parent choice is enabled by collection installation. The umbrella category's
list, actual display models, canonical name/price readers, and selected preview
construction still need installation before optional selection and ordinary
gameplay/persistence checks. Both served patchers stay V2. See the
[checkpoint](../docs/checkpoints/V3_FURNITURE_PIPELINE.md#shared-held-parent-collection)
for exact tests and the inherited seasonal-copy restriction.
