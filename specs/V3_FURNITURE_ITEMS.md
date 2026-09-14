# V3 shared furniture item readers

## Implemented boundary

`tools/v3_furniture_items.py` installs full English names, native furniture-leaf
classification, donor price values, size queries, and placement-footprint data
for the two reviewed static pilots. The readers require the selected furniture
profile; unused `3xxx` IDs are not automatically accepted.

This is shared-reader integration, not ordinary inventory or placement support.
The [room adapter](V3_FURNITURE_ROOM.md) connects its checked native-range and
inline index sites. Other item consumers still need integration. Acquisition,
catalogue/scoring flags, pickup,
rendered placement/collision, and saved-item/profile handling remain required.
The [checkpoint](../docs/checkpoints/V3_FURNITURE_ITEMS.md) owns test evidence.
Both public and local patchers stay V2.

## Source-bound metadata

The actual GAFE01 revision 0 REL and symbol hashes are verified through the
existing furniture source checks. The sixteen-byte name records are copied from
`ftrName2_table` only after exact comparison with each reviewed identity. These
two records already use supported Latin bytes and complete space padding.
The donor's 1,267-entry price table includes its terminating entry; it is not
an extra import. The installer checks the actual profile's shape and the complete
single-unit placement data in both games.

| Destination item/rotations | Runtime index | Complete name | Donor price value | Footprint |
| --- | --- | --- | --- | --- |
| `3224`–`3227` | 1,161 | haz-mat barrel | 830 | 1×1 |
| `32B8`–`32BB` | 1,198 | oil drum | 840 | 1×1 |

Prices are values returned by the shared native item-price function. The
surrounding purchase/sale calculations retain their existing interpretation;
the adapter does not invent a new markup or sale multiplier.

Each 32-byte metadata row contains a 16-bit runtime index, item, and price;
one-byte footprint/enabled fields; sixteen name bytes; and eight reserved zero
bytes. Two rows occupy `804672A0`–`804672DF`. Selection also checks the installed
resident furniture profile, so metadata alone cannot enable an absent model.
Only the reviewed 1×1 shape is supported by this adapter. Other shapes require
their complete footprint implementation, not a silent 1×1 fallback.

## Runtime paths

V3 ABI 6 retains the same 32-KiB resident allocation and ROM-only model tail.
The 700-byte item helper starts at `80467300`; the guard at `80467FF0` is unchanged.
Five sixteen-byte return bridges occupy `80464600`–`8046464F`, immediately after
the current villager helper. The builder rejects code/bridge/table overlap.

| Entry | Imported behaviour | Original behaviour |
| --- | --- | --- |
| `801969C8`, full item name | Copy exactly sixteen complete bytes | Retained V2 capacity/alias conversion and real name DMA |
| `800A5630`, item category | Furniture-leaf category 10 | Retained native category/special-item logic |
| `800BE69C`, size query | Verified 1×1 size | Retained native size table and fallback |
| `800BE72C`, placement cells | All four native cells; first occupied | Retained native initialization, rotation, and footprint tables |
| `800C0194`, item price | Actual donor value | Retained native conversions, prices, and transient resource allocation |

Each full original function is hash-bound. Its first two stack/prologue
instructions move to a return bridge followed by a jump to the original third
instruction. There are no displaced PC-relative instructions. Non-`3xxx` items
tail-call those original bodies. The fixed-width name API continues to reject
IDs above `FFFF`, short capacities, null destinations, and unavailable imports
without writing. Unaligned name destinations are supported.

Native footprint output consists of four twelve-byte records containing
`exists`, `x`, and `z`. The selected 1×1 profile occupies the first record;
all four coordinate pairs match the native unit-offset rules. A missing import
clears the records and returns the native invalid-size value 3. This does not
bypass upstream checks that still prevent an imported item from being placed.

## Verification and remaining callers

Focused host checks use address/undefined-behaviour sanitizers for all rotations,
unaligned names, capacities, disabled selections, original fallback dispatch,
complete footprint writes, and adjacent guards. Current-cartridge checks compare
actual donor metadata, unchanged original function bodies, exact installed
bridges, RAM bounds, CRC/configuration, UPS reconstruction, deterministic
composition, and import-free V2 retention.

Native checks call the actual installed five entries for both pilots, rejected
inputs, and an original furniture item. They do not insert objects into a town,
write a save, or establish ordinary menu/rendering behaviour.

The room adapter covers the `My_Room` constructor range at `80938A34`, its index
conversion at `80938AA0`, and the actual constructor's index reader at `809386B0`,
along with the other reviewed room range/type sites. The shared placement
functions also have callers outside that owner that reject extended IDs before
reaching them. Inventory dispatch, field lists,
catalogue/scoring, mail articles/attachments, and saved dependencies still need
their complete selected-item paths.
