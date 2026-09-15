# V3 import storage and fixed metadata slots

## Implementation boundary

Expand the existing import resource without consuming another DMA-directory
entry. The directory contains 3,389 entries and its sole remaining terminator;
appending a new file would overrun the original boot allocation.

The English choice data moves from VROM `02400000` to `025F0000`. Its complete
contents, cumulative offset table, DMA identity/physical location, text buffers,
and saved IDs remain unchanged. Retarget the shared address calculation at
`80065614` and verify actual choice-address lookup and DMA. No other consumer
is permitted to keep the old address. This frees the import resource's contiguous
reservation `02200000..025EFFFF`, before the relocated choices and existing
general strings at `02600000`. Physical free space is checked independently.

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

This layout changes neither format 2 nor selected identity bits. Ordinary
cross-build reload is unverified. It is not a complete-import handoff. Both
served web patchers stay on V2 pending user testing and explicit approval.

Seventeen focused checks and the first actual native run pass. The native run
has 23 calls and 48 memory assertions, including all installed static pointers,
boundary rejection, one/two-cell and callback-item readers, a retained shirt,
both extended English choice IDs, long odd/even choices, and final guards.
The [checkpoint](../docs/checkpoints/V3_IMPORT_STORAGE.md) records exact artifacts,
the corrected preflight, source report, and ordinary-gameplay limits.

## Next content batch

The actual English donor identifies seven static camping models: kayak `3364`,
backpack `3370`, lantern `339C`, cooler `33A4`, mountain bike `33A8`, sleeping bag
`33AC`, and propane stove `33B0`. They occur in `ftr_listTent`, not ordinary
shop stock. The source profiles have no animation/callback pointers; kayak,
mountain bike, and sleeping bag use the two-cell shape. Model conversion and
runtime installation remain work.

Their donor HRA birth category is 37, beyond the current native 23-counter
adapter. Preserve the real camping acquisition route and implement a safe
category mapping/counter adaptation before enabling these imports. Do not copy
the six-bit donor category into the native five-bit field or silently give the
items ordinary shop stock. The other Tent entries require separate behaviour
review; the seven static profiles do not define the entire family.
