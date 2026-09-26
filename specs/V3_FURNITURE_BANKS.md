# Dedicated Expansion Pak furniture banks

## Memory ownership

The import runtime reserves `80500000..8062C01F` exclusively for My_Room furniture models.
Do not use this range for diagnostic scratch, other assets, or heap growth.
The reservation contains 100 banks of `0x3000` bytes (12,288 decimal), with
16-byte guards before and after the data: 1,228,832 bytes total.

| Range | Owner |
| --- | --- |
| `80500000..8050000F` | Four `AF42C0DE` leading guard words |
| `80500010..8062C00F` | 100 consecutive model banks |
| `8062C010..8062C01F` | Four `AF42C0DE` trailing guard words |

Resident import/code reservations stay below `80500000`. Font memory remains
`80450000..80457FFF`; title resources end below it. The emergency fault
framebuffer starts at `807DA800`. Ordinary system/game heaps, framebuffer
allocations, and scene-object arenas remain below `80400000` and do not grow.
The native catalogue's separate preview allocations each hold `0x3000` bytes.
`tools/v3_furniture_capacity.py` binds the larger bank helper, room constructor
hook, preview allocation loop, and submenu reservation as one checked contract.
It reserves 307,200 additional Expansion Pak bytes and 6,144 additional submenu
bytes. The catalogue's two 8-KiB programme buffers remain unchanged. The native
allocation stride at `808A9784` changes to `addiu v1,v1,0x3000`; the complete
80-byte allocation loop is verified before patching. Main-code allocation at
`800C4B10` and subsequent catalogue rebuilds retain the same reservation chain.
No saved field or format changes.

The installer accepts larger complete models only after checking actual native
code, guards, strides, and reservation instructions. A receipt alone does not
raise the limit. Historical builds without this contract keep their checked
9,216-byte limit. Unknown dimensions, code, and allocation chains reject.

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

The shared DMA reader uses the same 12,288-byte capacity, accepts only aligned
banks within the reserved range, and requires equality with the active owner's
actual bank-table entry. Original furniture still uses its retained native
profile and DMA bodies; its buffers come from the same pool.

## Verification boundary

Focused checks cover complete source artwork, retained models, actual allocation
instructions, malformed-contract rejection, all 100 DMA-bank boundaries under
address/undefined-behaviour sanitizers, failed-DMA state, patch reconstruction,
and four browser/offline selections. Native execution establishes the full
100-pointer table, zero-demand reset, count0=100/count1=0, guards, complete model
DMA into first/last banks, untouched tails, and the exact two-preview allocation
loop. Its sparse owner fields do not establish full room/catalogue construction,
executed native teardown, GPU appearance, or original-hardware compatibility.
See the [capacity checkpoint](../docs/checkpoints/V3_FURNITURE_PIPELINE.md#complete-model-bank-capacity).
