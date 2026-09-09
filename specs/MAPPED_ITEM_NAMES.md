# Reviewed item names across shifted reference tables

## Scope

308 explicit furniture-name approvals cover native groups outside the first
300: 138 at individually reviewed shared indices and 170 at different English
indices. The native Japanese name, complete source hash, all four rotations,
full supplied English name/hash, and exact reference ID remain the authority.
No index-shifting heuristic is added to generation or installation.

The selected cross-index groups have these relationships. Group numbers here
are decimal; committed IDs and reference IDs use hexadecimal.

| Native groups | Selected approvals | English index difference | Content |
| --- | ---: | ---: | --- |
| 746–777 | 31 | +8 | Insects; 751 remains unapproved |
| 778–809 | 31 | +16 | Fish; 779 remains unapproved |
| 810–841 | 16 | +24 | Individually matched umbrella designs |
| 850–946 | 92 | +44 | Furniture, chess pieces, fossils, and seasonal series |

The supplied English table inserts mannequins and additional creatures,
umbrellas, and games. Equal numeric IDs therefore stop describing the same
objects. For example, native common butterfly maps to English `02F2`, not the
mannequin at the native group number. The fossil and seasonal matches reach
English rows beyond the native group's count, within the same extracted
1,024-row English furniture table.

## Name and part fidelity

Japanese queen/king and tail/torso words select the exact English part where
the legacy gloss swaps those names. White/black pieces and right/left wings
remain distinct. No neighbouring row is accepted merely because its name is
similar. Tests explicitly check the shifted creatures, umbrella, phonograph,
kiddie couch, chess pieces, fossil parts, and Snowman spelling/case.

Shared-index approvals cover identifiable furniture, bath objects, plants,
clothing motifs, numbered pool-ball shirts, and established series names.
Retain supplied spelling/case, including the full `racoon obje` reference;
its unusual spelling belongs in final wording review, not silent correction.

The gyroid families have [separate complete approvals](GYROID_ITEM_NAMES.md).
The priest-cicada comparison, the native hera versus
English brook-trout comparison, swapped red/blue gym clothes, changed party/
tuxedo and console-logo designs, blank numbered-shirt references, native game
slots, figurines, and ambiguous clock/umbrella designs stay unapproved. Those
names need specific semantic or asset evidence. Name approval does not establish
matching artwork, unchanged object design, reachability, or full gameplay.

## Capacities and native aliases

All 308 complete names fit sixteen bytes, adding 1,232 furniture rotation slots.
Eighty-one names fit the unchanged ten-byte bank, adding 324 rotation slots.
The other 227 are never shortened for unexpanded callers.

The existing native placed-item conversion and identical Japanese source fields
also admit 114 additional wider ordinary aliases: 98 clothing, ten umbrella,
five insect, and one fish slots. Eleven additional aliases fit ten bytes: nine
clothing, one umbrella, and one insect. Existing ordinary candidates take
precedence only when their complete English spelling already agrees; conflicting
names fail. This adds 1,346 wide slots and 335 ordinary edits in total without
changing any earlier candidate.

Two separate ordinary approvals cover `item_24:006D/0078`: the winter sweater
adds a Japanese linking particle in its carried name, and bear shirt uses
katakana instead of hiragana. Exact-source alias matching correctly rejects
both variants. Their actual ordinary source names and English references are
independently bound instead; no general spelling normalisation is introduced.
Both names fit sixteen bytes; only bear shirt fits ten. These direct approvals
bring the batch to 1,348 added wide slots and 336 ordinary edits.

Including the [flooring/wallpaper approvals](FLOOR_WALL_NAMES.md), the full wide
resource has 2,783 candidate slots from 841 reference IDs; ordinary ten-byte
storage has 789 candidate slots from 252 references. These are
separate storage counts, not distinct translated sentences. Four rotations and
their converted ordinary alias must not be counted as five new name identities.
Resource size, headers, DMA entries, native IDs, saved structures, code, font
metrics, and caller capacities remain unchanged.

## Acceptance

All 559 registry entries (487 furniture, two clothing, and seventy floor/wall)
are independently checked against native/reference hashes and exact name bytes.
Tests cover complete output at both capacities,
cross-index identities, withheld mismatches, exact placed conversion, metadata
removal, and rejection of shortened/relabelled names. Artifact checks compare
every installed ordinary edit and every converted wide-name result with the
complete selected reference, reconstruct the resource, and apply the UPS to the
original ROM. Only the native item-name file and existing wider-name resource
may change for this batch.

Native execution checks all wider reference representatives, boundaries,
unaligned destinations, rejected capacities/headers, and every new original-width
item slot, with guards and restored checkpoints. Normal item display and each
remaining wider caller still need integration and gameplay validation. Exact
run results and hashes belong in the work log.
