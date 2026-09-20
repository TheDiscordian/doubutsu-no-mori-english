# V3 import storage and fixed metadata slots

## Implementation boundary

Expand the existing import resource without consuming another DMA-directory
entry. The directory contains 3,389 entries and its sole remaining terminator;
appending a new file would overrun the original boot allocation.

The current import reservation is `02200000..027FFFFF` (6 MiB). The legacy
reservation ends at `025F0000`; a larger bound requires the verified capacity
receipt, not a changed constant. Physical free space is checked independently.

`tools/v3_resource_capacity.py` relocates the complete shared English resources
without changing their directory indices, physical starts, offset tables, text,
buffers, or saved identities:

| Resource | Current VROM | Offset table | Native base-load pair |
| --- | --- | --- | --- |
| English choices (511 entries) | `029E0000` | `00D06000` | `80065614` |
| General strings (1,562 entries) | `029F0000` | `00D18000` | `800C3F1C` |

Both complete 320-byte native address functions must match the checked source.
The core must contain exactly one load of each previous base's upper half,
including all register forms. Only the two verified base pairs change. The
existing module at `02800000` and all other resource identities remain intact.

The native text loaders round transfers up to eight bytes. Resource extents are
padded to sixteen bytes after checking that the existing physical padding is
zero, inside the ROM, and outside every other live resource. General strings need
three padding bytes; their final five-byte entry requires an eight-byte transfer.
No text or offset is changed. Enlarging the declared resource end prevents the
native DMA bounds assertion for that final entry.

The shared installer validates the expanded receipt against the actual complete
resources, tables, readers, and logical overlaps before using its bound. It also
checks every final physical/logical extent, directory terminator, retained owner,
CRC, and complete patch reconstruction. The room-category installer appends
complete batches when verified retired storage is insufficient; it does not
allocate a separate resource per item. This capacity expansion adds 2,162,688
bytes of cartridge reservation and no resident RAM.

## Resident package

The package begins at VROM `02400000`, loads at `80473000`, and occupies
`2D010` bytes, including its final guard. Existing accessory, roster, melody,
display, and shared-item code addresses remain fixed. The two new tables are
indexed by `(item - 3000) / 4`, with 1,024 slots each:

| RAM | Contents |
| --- | --- |
| `80484000..80497FFF` | 1,024 static-profile rows, 80 bytes each |
| `80498000..8049FFFF` | 1,024 item-metadata rows, 32 bytes each |
| `804A0000..804A000F` | Complete-package guard |

The increase is 114,704 resident bytes. The ordinary heaps, menu allocation,
and dedicated model banks at `80500000` do not grow. Uninstalled rows are zero.
The slot capacity is not a claim that 1,024 items are implemented. Existing
animated furniture and clothing-display profiles keep their separate callbacks.

Shared readers validate canonical identity, enable state, and the actual active
profile pointer. Startup derives transient profile pointers from validated rows,
not from the limited old seed table. Original native entries start empty; the
three final padding entries remain empty, and all bank indices start at `FF`.

## Verification and publication

The builder binds the exact previous cartridge and report, checks every moved
record and code entry, retains complete save-code bodies, rejects virtual or
physical overlaps, and reconstructs its UPS output. Verification targets changed
startup, sparse lookups and boundaries, choice relocation, and an offline subset.
Unchanged model-rendering and acquisition evidence is not replayed.

The current capacity/clock batch changes neither saved format 3 nor selected
identity bits. Ordinary cross-build reload is unverified. It is not a complete-import handoff. Both
served web patchers stay on V2 pending user testing and explicit approval.

Four current host/cartridge checks pass, including complete resource retention,
consumer/overlap rejection, all fifteen installed clocks, and exact full/empty
optional composition. The focused native run passes 153 assertions covering the
final-string boundary, three complete clock representatives, live hand angles,
memory guards, restoration, and clean exit. Other relocated-text checks retain
their passing evidence from the preceding partial run; they are not replayed.
The [current checkpoint](../docs/checkpoints/V3_FURNITURE_PIPELINE.md#bulk-storage-and-complete-clock-installation)
records exact artifacts and limits. The
[initial storage checkpoint](../docs/checkpoints/V3_IMPORT_STORAGE.md) preserves
earlier sparse-table and choice-reader evidence without retesting that build.

## Camping content

The actual English donor identifies seven static camping models: kayak `3364`,
backpack `3370`, lantern `339C`, cooler `33A4`, mountain bike `33A8`, sleeping bag
`33AC`, and propane stove `33B0`. They occur in `ftr_listTent`, not ordinary
shop stock. The source profiles have no animation/callback pointers; kayak,
mountain bike, and sleeping bag use the two-cell shape. Their
[complete conversion and runtime](V3_CAMPING_ITEMS.md) use fixed sparse slots
without further resident growth. Summer-camper acquisition remains work.

Their donor HRA birth category is 37, beyond the current native 23-counter
adapter. The scoring-only mapping uses the verified equivalent 412-point native
weight while preserving the real camping acquisition route. Do not copy the
six-bit donor category into the native five-bit field or give these items
ordinary shop stock. The other Tent entries require separate behaviour
review; the seven static profiles do not define the entire family.
