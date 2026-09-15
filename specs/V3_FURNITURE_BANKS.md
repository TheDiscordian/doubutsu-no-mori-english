# Dedicated Expansion Pak furniture banks

## Memory ownership

The import runtime reserves `80500000..805E101F` exclusively for My_Room furniture models.
Do not use this range for diagnostic scratch, other assets, or heap growth.
The reservation contains 100 banks of `0x2400` bytes (9,216 decimal), with
16-byte guards before and after the data: 921,632 bytes total.

| Range | Owner |
| --- | --- |
| `80500000..8050000F` | Four `AF42C0DE` leading guard words |
| `80500010..805E100F` | 100 consecutive model banks |
| `805E1010..805E101F` | Four `AF42C0DE` trailing guard words |

The current resident import package ends at `80484000`. Font memory remains
`80450000..80457FFF`; title resources end below it. The emergency fault
framebuffer starts at `807DA800`. Ordinary system/game heaps, framebuffer
allocations, and scene-object arenas remain below `80400000` and do not grow.
The native catalogue's separate preview allocations already each hold
`0x2400` bytes. Neither those buffers nor the menu-pool reservation increases.

## Actual native constructor and teardown

`tools/v3_furniture_banks.py` pins the complete My_Room owner at VROM `0082D7F0`,
link RAM `80936710`, image size `16C10`, resident size `18F00`, and its relocation
file at `00844400`. The single loaded owner's descriptor is at `80100DF0`,
with its live pointer at `80100E00`. Its 100-pointer bank table is at live+`18D68`.

The original allocator entry `80938D44` still calls its native count helper,
which caps demand at 100 and divides it into at most 35 contiguous banks and
65 separately allocated banks. The retained prefix reserves the dummy keyframe
in the existing scene-object arena and DMAs `013AB000..013AB57F`. Decode its
signed `addiu B000` correctly: `lui 013B` does not make this `013BB000`.

Only the 20-byte window `80938E14..80938E27` changes. It passes the saved room
pointer to the resident pool adapter, then branches to the original epilogue
at `80938ED8`. This bypasses both old allocation loops and their 5,120-byte
strides. The four high/low relocations in that window are removed; the other
1,397 entries and the relocation-file size are retained. Three independent
relocated-address comparisons verify that nothing else changes.

The adapter checks actual 8-MiB RAM, the owner descriptor, live owner bounds,
room-pointer bounds/alignment, and both counts. It sets count0 to their sum,
sets count1 to zero, fills exactly the requested bank pointers, zeros unused
pointers, and initializes both guards. The bank lifetime is that of the single
My_Room owner; no imported item owns or frees the reserved pool independently.

Native teardown `8093B6F4` frees only count1 heap banks. Keeping count1 zero
ensures no fixed upper-RAM address reaches `zelda_free`. Profile allocations,
actor state, and dummy scene-object cleanup remain native. Unsupported memory
or owner/count contracts stop through the existing fatal runtime path.

The shared DMA reader uses the same 9,216-byte capacity, accepts only aligned
banks within the reserved range, and requires equality with the active owner's
actual bank-table entry. Original furniture still uses its retained native
profile and DMA bodies; its buffers come from the same pool.

## Verification boundary

Focused installed-ROM checks pass for exact model/profile contents, full bank
capacity, relocation removal, retained cleanup instructions, unchanged unrelated
ROM regions, and CRCs. Native execution establishes the full 100-pointer table,
count0=100/count1=0, and exactly one retained dummy scene-object allocation.
The observed dummy DMA hash matches the actual `013AB000` source.

The two permitted native setup attempts stop at fixture expectation mistakes;
the [checkpoint](../docs/checkpoints/V3_WESTERN_RUNTIME.md) preserves both failed
records and their exact causes. The corrected fixture is unexecuted. Paired
upper-RAM model DMA, the two-bank reinitialization, and executed native teardown
remain unverified. Do not call this a complete native bank-lifetime pass or
an original-hardware result.
