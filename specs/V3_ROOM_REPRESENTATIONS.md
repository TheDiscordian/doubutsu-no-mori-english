# Room representations and native artwork variants

## Saved designs

`tools/v3_room_representations.py` derives all eight custom mannequins and eight
custom umbrellas from both donor profile tables and their complete DMA/draw
callbacks. The mannequin range is `1BA8..1BC4`; umbrellas use `1D88..1DA4`, with
four rotations per slot. These are player-saved patterns, not sixteen fixed
appearances supplied by the disc. Their source names remain source names, not
proof of the rendered design or a correspondence with the same numerical N64 ID.

Each slot reads a 544-byte saved record containing a 512-byte, 32×32 CI4 texture,
a palette index, and a name. Drawing copies the texture and a 32-byte palette
from the player who owns the house. Mannequins use segments eight/nine for
texture/palette; umbrellas reverse those segments. The original create, move,
and destroy callbacks are empty; the DMA callback is not.

Full support requires saved designs, editing and naming, ownership resolution,
pattern rendering, wearing/umbrella interactions, and the related wall/floor
representations. The N64 game does not supply the donor design system. Custom
designs and Able Sisters belong to V4, including dependent sign boards and these
saved-pattern forms. No empty patterns or frozen substitutes are presented as
implemented imports. Other V3 item/villager importing work continues.

## Museum scenery

The Museum building is V4 work. Ordinary collectible fossil, fish, and insect
imports remain V3 work and do not require constructing that building.

The complete `mMmd_museum_fossil_data` table and
`mMmd_MuseumFossilProcess_MakeFgData` function distinguish 25 donated specimens
from nine placeholder models used before donation. The entry named `fossil`,
`1F9C`, supplies the empty display for amber, dinosaur track, ammonite, dinosaur
egg, and trilobite. It is not an additional collectible or an unidentified
fossil that needs a new identification route.

All nine placeholder identities remain in the donor inventory, with their actual
museum positions, rotations, associated specimen IDs, and profile evidence.
Neither scenery classification nor a fixed name authorises a furniture import.
Unexpected consumer code, relocations, table data, or profile relationships reject.

## Shared consumers

The donor inventory, furniture scan, and experimental browser review use the
same representation records. Saved designs remain explicitly unsupported;
museum placeholders are identified as scenery. They are not selectable, and
ordinary import/conversion requests for those records reject. Existing selectable
garments, creatures, and equipment own their display representations; the browser
does not repeat those forms as unrelated missing furniture.

`scan --select` limits the scan itself, not merely its printed results. A focused
identity check must not rescan unrelated conversion categories.

## Fixed artwork variants

The shared furniture pipeline resolves worksheet-native counterparts through the
original, hash-verified N64 room profile and model resources. Automatic variant
approval is limited to static source/native profiles without interactive callbacks
and to demonstrably different geometry. It follows native model/material calls,
checks bounds, rejects transformed/unresolved geometry, and records the complete
profile/model hashes and coordinate comparison. Matching coordinates or an
unreviewed behaviour do not automatically approve a duplicate. Changed names or
binary layout alone are not artwork evidence.

Both current records use the ordinary importer together:

| Donor appearance | Donor ID | Preserved N64 ID | Source stock |
| --- | --- | --- | --- |
| school desk | `3208` | `1200` | C |
| bus stop | `3270` | `10A0` | B |

Their full converted objects occupy 4,144 and 3,696 bytes. Each uses its real donor
name, price, footprint, placement, catalogue/orderability, scoring, and save-profile
identity. Selection is independent of the original N64 item and of the other
variant. Browser details identify the GameCube appearance and retained N64
version; in-game names retain official wording. Both names have official source
credits in `translations/provenance.json`.

No per-item installer, behaviour switch, or native scenario is introduced.
The installed palette runtime and furniture loader are reused unchanged.
The palette contract recognises the checked creature dispatch before comparison;
the catalogue capacity check retains and validates its separate 128-byte clothing
allowance through subsequent imports. Neither change bypasses a memory guard.

## Verification and remaining work

`tests/test_v3_room_representations.py` covers the complete 16/9 categories,
25 specimen associations, changed-source rejection, shared inventory/browser
classification, parent-display suppression, and unsupported conversion rejection.
`tests/test_v3_native_variants.py` covers complete source-derived conversion,
preserved native/imported resources, real stock and metadata, allocation guards,
unchanged save codec and resident loaders, patch reconstruction, and five matching
browser/offline profiles: neither variant, each variant, both, and all imports.

These are source/build/composition checks, not ordinary native gameplay or
original-hardware results. Existing passing checks for unchanged runtime code
remain retained. The format-nine save codec is unchanged, but saves using these
variants require a profile that includes them. Preserve backups; older builds
or profiles without the variants cannot load those saved items safely.

Sixteen ordinary diary styles are a separate unfinished carried-item category.
Their catalogue models are not substitutes for working diary reading, writing,
inventory use, and persistence. Complete that shared import path before moving
to acquisition systems and the remaining gold-tree work.
