# V3 imported furniture catalogue

## Implemented scope

`--catalogue` includes native collection and FlashRAM support, then connects
the two selected static furniture pilots to the catalogue's ownership filter,
ordering table, full names, completion indicator, preview loading, selection,
and price display. It preserves all 436 native furniture rows in their original
order and appends haz-mat barrel and oil drum in donor order: 438 rows total.
The existing 444-slot category limit is enforced. Additional imports require
reviewed capacity expansion; increasing a loop count alone is not sufficient.
The clothing variant also appends cherry shirt to the separate clothing page,
preserving all 245 native garment entries. Its [clothing adapter](V3_CLOTHING_CATALOGUE.md)
connects canonical ownership, full names, the native mannequin preview, clothing
presentation, and order identity. It does not add a third furniture-page row.

This is development source, not an enabled browser option. Ordinary ordering,
delivery, acquisition, scoring, placement, and complete player lifecycle still
need integration/verification. Both web patchers remain V2 pending the user's
V3 testing and explicit approval. The save format and required profile are
unchanged from the collection build; V3 saves still require V3.

## Identity and native readers

The catalogue retains its original `(item - 1000) >> 2` index encoding and
inverse `1000 + index * 4`, rather than adopting room-runtime indices.

| Item | Item ID | Catalogue index | Room index |
| --- | --- | --- | --- |
| haz-mat barrel | `3224` | 2185 | 1161 |
| oil drum | `32B8` | 2222 | 1198 |

At `808A9470`, the extended ownership reader queries the active resident's saved
imported catalogue. Native entries retain the original bit reader at `808A931C`;
uncollected, disabled, and unknown imports do not appear. The original category
construction and nine-page, 63-slot complete-name cache remain intact.

The catalogue's independent program loader at `808A6148` selects a resident
static profile for enabled imports and retains its complete original fallback
for native furniture. Imported catalogue indices map to room indices by
subtracting 1024. Native model DMA at `808A61C8` loads the complete converted
object into each original `2400`-hexadecimal-byte preview buffer. No room actor,
copied program, or extra resident model allocation is required for these static
profiles. Native preview initialization at `808A627C` retains geometry setup,
lighting/render paths, scale, vertical position, viewing height, and price.

Selection has a separate type check at `808A6B14`. Its detour calls the existing
full-register-preserving room query with mode two, mapping only selected imports
to furniture type one. This preserves actual item IDs and enables the original
selection routine to initialize the second preview normally.

Both imports use donor preview mode zero, verified against the actual supplied
REL: scale `0.9`, vertical position `-3`. The native viewing height is `42`.
The donor's ordinary goods tables contain the barrel in list C and oil drum in
list A. Six catalogue-local availability calls use this verified eligibility to
show the existing imported prices, 830 and 840 Bells. This does not add the
items to the native shop's random stock or override town rarity distribution.

## Ownership, relocation, and memory

The complete V2 catalogue is 53,680 bytes at VROM `03970000`, relocation
`03980000`, linked RAM `808A6100`. Its translated names and Not for Sale adapter
are retained. The code/table suffix starts at `808B32B0`: 2,144 bytes without
clothing and 2,880 with clothing. The complete images are 55,824 and 56,560
bytes, with 688- and 720-byte relocation resources respectively.
Both resources retain 16-byte alignment. The parent descriptor at VROM `7749C0`,
offset `2C90`, receives only the new end addresses after preserving the installed
V3 icon edits.

The conservative shared-menu requirement is 273,408 bytes without clothing
and 274,176 with clothing, within the existing 274,560-byte reservation.
The installer binds the actual reservation
instructions and refuses overflow. It does not reuse the smaller historical
name-only allocation calculation. No additional pool or resident memory is
allocated; the resident prefix remains 48 KiB. The clothing variant uses ABI 44.

Whole-source hashes, donor resources, compiled dependencies, expected native
instructions, ELF relocations, duplicate targets, virtual-ROM overlaps, and
composition are checked. Independent relocation at three destinations rejects
any unrelated prefix change. Suffix-local jumps are relocated; calls into the
fixed resident helper remain fixed. ROM construction allows resizing only these
two explicitly named resources. Empty composition still returns exact V2.

## Verification and remaining work

Four focused tests cover sanitized helper contracts, native-table preservation,
limits/alignment, current cartridge composition, UPS reconstruction, and exact
import-free V2. A 70-step native check runs actual overlay relocation, list and
name initialization, both full model DMAs, imported selection, all-438-entry
completion, and original preview fallback. Guards, restored state, and graceful
shutdown pass. It does not submit graphics to the GPU, use ordinary shop
controls, deliver an order, or write a save. See the
[checkpoint](../docs/checkpoints/V3_CATALOGUE.md) for exact artifacts and failures.
The current clothing variant's two focused checks and initial 71-step native
run also pass, including all 246 garment rows and their complete preview path.
Its [checkpoint](../docs/checkpoints/V3_CLOTHING_CATALOGUE.md) separates that
component evidence from unverified ordinary payment/delivery and GPU appearance.

The catalogue ordering handoff retains original ID conversion at `800BF10C`;
the native conversion returns these `3xxx` values unchanged. Review the actual
shop confirmation/payment and saved pending-order paths before claiming orders.
The translated post-office creator calls the shared imported-name reader; no
separate postal name patch is needed. The [shop adapter](V3_SHOPS.md) connects
native ordinary stock. The [interaction adapter](V3_SHOP_INTERACTIONS.md) records
complete native pending-order delivery/readback for both imports.
Confirmation/payment, independent shop-floor handling, scoring, and complete
gameplay remain work.
