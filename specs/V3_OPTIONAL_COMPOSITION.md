# Local optional import composition

## Scope

Compose experimental selections from the pinned ABI-83 integration cartridge
with the [official localized credits title](../docs/checkpoints/OFFICIAL_CREDITS_TITLE.md),
including the complete tent model, both fires, their checked DMA/callback
loaders, four-cell item readers, complete sound resources, and the additive
campsite scene/exterior runtime, native calendar, independent camper, and native
tent placement/removal adapter, English event-manager extension, and saved-camper
move-in exclusion, both camper NPC-profile routes, first/repeat quest state, and
all 253 summer messages and 49 choices, summer greeting selection, and transient
last-gift tracking, full-ID trade picking, selected summer rewards, and the
tent's native floor sound, donor point-light parameters, and complete timed
lamp lifecycle. Native creation, fade, drawing commands, environment updates,
and cleanup pass; ordinary scene appearance remains unverified. The
complete greeting initializer/return passes in the current native trade check;
the earlier intermediate breakpoint remains unexplained. Both manager
activation and tent setup require actual selected camping-item rows. Camper
conversations and acquisition remain unfinished.
Shared audio changes
remain in every nonempty profile; the empty profile still returns exact V2.
The pinned source includes [expanded import storage](V3_IMPORT_STORAGE.md),
the [full-sized Western runtime](V3_WESTERN_LARGE_ITEMS.md), dedicated
model banks, garden imports, expanded reward counters, and corrected aloha scoring.
This is an offline development step, not a served web option or a declaration
that all imported gameplay is complete. Neither V2 patcher changes.

The selectable development catalogue contains twenty villagers and thirty-nine
installed logical items: thirty-six furniture items and three shirts. A shirt's
mannequin is a required representation, not another selectable item. Unconverted
donor items are rejected. Select-all means these installed development entries,
not every item on the donor disc.

An empty selection returns the exact pinned V2-11 cartridge. A nonempty selection
retains the shared ABI-83 engine and all compiled resources, but enables only the
chosen identities and their declared dependencies. IDs, object slots, house
layers, and allocations never depend on order or subset. Resource compaction is
not part of this step.

## Dependency resolution

Use fixed source identities from `v3_registry.py`. Derive required shirts from
the installed villager metadata and required furnishings from the actual two
installed house layers. Normalize furniture rotations to their canonical item.
Reject unknown imported house furnishings or missing defaults. Selecting Punchy
therefore requires the cherry shirt and speed bag; selecting Cheri requires
both barrels. Islanders require their actual red or blue aloha shirt. Each shirt
requires its fixed mannequin in the save profile and native item records.

Canonicalize duplicate/order-varied selections into sorted sets. Record explicit
selections, automatically required identities, dependency reasons, destinations,
and the complete 192-byte save profile. A cancelled selection must be resolved
again from the original selection, not by editing an earlier dependency result.

## Checked cartridge writes

Pin both the complete ABI-83 cartridge and its source report. Validate each
installed registry binding before generating writes. Resident changes cover the profile
at blob offset `20`, twenty eligibility bytes at `1E60`, selected villager
metadata's `present` bytes, and the installed furniture/clothing/mannequin
`enabled` fields. Furniture's existing selector reads the `enabled` field;
changing the save profile alone would not disable ordinary furniture stock.

Thirty-five furniture rows occupy fixed canonical slots in the expanded
accessory/audio package at RAM `80484000`, backed by blob offset `211000`.
The slot is `(item - 3000) / 4`; absent slots stay zero. Validate the package descriptor
and CRC before resolving that mapping; subtracting the main prefix RAM base
would target the wrong resource. Only the thirty-five reviewed four-byte enable words
are writable in that package. The animated speed bag retains its prefix row.
The shared item metadata is at `80498000`; composed reports retain the correct
address and logical row count for each installed batch. The dedicated model pool
is shared runtime capacity, not another selectable item or a profile-dependent
allocation.

The package is 196,608 bytes at VROM `02400000`, loaded at RAM `80473000`.
English choices reside at `025F0000`; composition never changes their contents.
Its item-code extension and the fixed save-resource forwarding entries remain
unchanged across profiles. Watering trough, covered wagon, and storefront retain
size 1/two-cell metadata. The selected profile gates their compiled catalogue
framing; raw GameCube preview-mode numbers are never written into native rows.
The bonfire retains size 2/four-cell metadata and its complete fire callbacks;
both fires keep their native loop programs, samples, and per-actor sound IDs.

Pack selected appended catalogue rows after all unchanged native rows, preserving
donor order and every item ID. Clear unused appended table slots in their existing
storage. Update the furniture search/initialization/completion counts together,
and the clothing shared iteration/completion count. Reducing the latter without
packing selected rows would lose a chosen later shirt. The actual allocated
753-slot page capacity, native category order, pointers, and image size stay.

Exclude unselected furniture and mannequin records from the HRA metadata table,
using its existing inert `FC000000` entry. Native grouping scans this whole table
independently of the placed-item selector: leaving disabled records would require
unavailable furniture for theme completion and missing-item recommendations.
Retain all original records, all selected properties, series definitions, names,
code, and relocation. Empty series have zero members after native initialization.

Every write includes its expected input and rejects overlap, unknown bytes, or
out-of-range destinations. Recompute the package CRC first, then the prefix CRC
which covers that descriptor, and the N64 header checksum. Apart from the two
bounded furniture-count immediates, executable instructions remain unchanged.
Source artwork, physical and virtual file ranges, house contents, and save-codec
code remain unchanged.
All-selected composition must reproduce the pinned full integration ROM.

The offline CLI writes a new ROM, UPS patch, selection receipt, and matching
build report only under ignored `build/`. Verify the original ROM and reconstruct
the full result through the UPS patch before writing output. Never overwrite
an existing output directory. Do not modify a source cartridge, save, web
recipe, or running service.

## Saves and verification

Selected imports are saved dependencies even if not yet acquired. The existing
format-2 codec accepts a saved profile in an equal or larger selection and
rejects a missing dependency before modifying output state. A smaller selection
is not a save migration. Never load imported saves in V2 or imply that stable
field sizes establish gameplay compatibility.

Focused checks cover dependency closure, selection-order independence, every
changed enable field, collision rejection, preserved code/resources, exact
all/empty outputs, and actual codec subset/superset handling. One combined
native check verifies selected versus excluded runtime entries and a non-prefix
shirt/furniture subset's real catalogue selection and completion. Ordinary
cross-profile save/reload and player acceptance remain separate evidence.

Browser composition and input conversion remain later work. GitHub development
source is allowed; both web patchers remain on V2 until testing and explicit
approval from the user.
