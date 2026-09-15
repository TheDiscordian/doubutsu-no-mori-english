# Local optional import composition

## Scope

Compose experimental selections from the pinned ABI-60 integration cartridge.
This is an offline development step, not a served web option or a declaration
that all imported gameplay is complete. Neither V2 patcher changes.

The selectable development catalogue contains twenty villagers and the six
installed logical items: three furniture items and three shirts. A shirt's
mannequin is a required representation, not another selectable item. Unconverted
donor items are rejected. Select-all means these installed development entries,
not every item on the donor disc.

An empty selection returns the exact pinned V2-11 cartridge. A nonempty selection
retains the shared ABI-60 engine and all compiled resources, but enables only the
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

Pin both the complete ABI-60 cartridge and its source report. Validate each
installed registry binding before generating writes. Change only the profile
at blob offset `20`, twenty eligibility bytes at `1E60`, selected villager
metadata's `present` bytes, and the installed furniture/clothing/mannequin
`enabled` fields. Furniture's existing selector reads the `enabled` field;
changing the save profile alone would not disable ordinary furniture stock.

Every write includes its expected input and rejects overlap, unknown bytes, or
out-of-range destinations. Recompute the existing prefix CRC in the translation
module and the N64 header checksum. Instructions, source assets, physical and
virtual file ranges, house contents, and save-codec code remain unchanged.
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
native check can verify selected versus excluded runtime entries. Ordinary
cross-profile save/reload and player acceptance remain separate evidence.

Browser composition and input conversion remain later work. GitHub development
source is allowed; both web patchers remain on V2 until testing and explicit
approval from the user.
