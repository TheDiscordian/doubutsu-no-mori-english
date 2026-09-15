# Expanded catalogue storage and construction integration

## Installed scope

The capacity-expanded variant installs 446 furniture rows: all 436 native rows,
the barrel, drum, and speed bag, and seven construction furnishings. It retains
the complete independent 248-row clothing catalogue. Native stock lists also
contain all ten furniture imports in their verified donor A/B/C groups. The
room-scoring tables contain the seven new birth-category and colour records;
the construction theme has 28 members, within its 32-bit completion mask.

`tools/v3_construction_catalogue.py` builds this ABI 62 integration cartridge
from the pinned ABI 61 runtime. It preserves all original assets, fixed import
identities, resident code, audio, and saved profiles. The
[optional composer](V3_OPTIONAL_COMPOSITION.md) connects this larger installed set,
including selected catalogue rows/counts and package CRC handling.
Neither served patcher changes.

## Actual N64 state

The N64 constructor `808A96AC` uses zero-backed static state at `808AFA10`,
not the GameCube constructor's heap allocation. Native destruction clears the
owner pointer. Keep that ownership and the two 1,888-byte preview structures,
their external model/program buffers, and their original initialization.

Each category contains an eight-byte header, an item-ID array, and seven
ten-byte compatibility names. The complete sixteen-byte English names remain
in the existing 63-slot pointer-keyed cache; no new truncation or font change
is introduced.

| Field | Capacity-expanded layout |
| --- | --- |
| First category in state | `0EC8` |
| Per-category item capacity | 753 |
| Item array offset | 8 |
| Name-field offset | 1,514 |
| Category stride | 1,584 bytes |
| Nine-category array end / aligned frame | `4678` |
| Page-order array | `46C8` |
| Complete aligned state | 18,144 bytes |

This page size covers the donor's 742-entry maximum and aligns category starts
to sixteen-byte boundaries. Four native category-address calculations retain
seven instructions each. The replacement evaluates
`(((index * 3 * 16 + index) * 2 + index) * 16)`, or `index * 1584`.
No additional register, HI/LO clobber, new call, branch, or delay slot is used.
Interleaved loads remain untouched. Three initializer strides, three name-field
addresses, and seventeen frame/navigation-tail accesses change explicitly.
A scan of the complete native executable rejects unknown layout consumers.

## Cache, relocation, and allocation

Insert 5,568 zero bytes at the original BSS end, offset `CA30`. The state begins
at its original address. Its aligned frame/navigation tail moves by 5,560 bytes;
the different amount preserves the native frame alignment and final padding.
The complete name cache, translated Not for Sale adapter, and V3 suffix move
together. Rewrite relocation locations and internal targets, including matching
HI16/LO16 carry handling. External resident calls remain fixed. Unknown kinds,
unpaired lows, conflicting shared highs, duplicate locations, and out-of-image
targets are rejected. Check independent relocation at three actual RAM bases.

The complete catalogue is 62,224 bytes; its relocation resource is 720 bytes.
Both remain aligned, and the catalogue stays below its next VROM at `03980000`.
The source-checked parent descriptor receives the actual new endpoints.

The shared menu reservation grows by 6,144 bytes to 280,704 bytes. Its
conservative requirement is 279,872 bytes, leaving 832 bytes. Patch both native
allocator endpoint instructions: `80897620 + 1800 = 80898E20`, so the signed
low half requires `LUI 808A`, not `8089`. This is additional menu memory below
the unchanged native heap limit, not an increase beyond the existing Expansion
Pak requirement. Ordinary town-menu heap headroom still needs gameplay evidence.

## Stock, scoring, and persistence

Rebuild stock from the complete pinned native resource, inserting each item
before its verified A/B/C terminator. Preserve native order, special-event lists,
rarity distribution, random-selection routines, and the descriptor's alignment.
The actual native category/selection routines consume the updated descriptor.

Reconstruct both complete preceding scoring tables from verified donor sources
before updating them. Only the seven new records differ. Existing code,
relocations, all native rows, original imports, and the imported garment's
metadata remain intact. Retain native birth-field encoding and point weights.

Append revised resources to the existing physical blob allocation. Preserve all
previous object/audio addresses and compressed resources. The output remains
64 MiB, with eight MiB of RAM required. Recalculate startup/resource checksums,
N64 checksums, and the UPS, and verify reconstruction into the exact cartridge.

Saved format 2, IDs, and the selected profile are unchanged from ABI 61. Older
profiles still reject saves requiring the seven construction imports. Ordinary
cross-build reload is unverified; retain backups. Native pocket insertion is not
ordinary shop payment or a completed save/reload cycle.

The [checkpoint](../docs/checkpoints/V3_CONSTRUCTION_CATALOGUE.md) records the
passing native catalogue and stock checks, their artifacts, and remaining work.
