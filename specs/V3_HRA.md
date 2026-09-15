# V3 furniture HRA evaluation

## Scope

The reviewed construction furniture, three clothing displays, and speed bag
participate in the native HRA evaluator with their actual donor properties.
The speed-bag variant includes expanded boxing-theme storage. Native scoring formulas, theme rewards,
wall/floor rules, mail selection, complete English score-letter creator, and
delivery-success handling remain intact. This is not a port of GameCube's
additional rooms or house-model rewards.

The [checkpoint](../docs/checkpoints/V3_HRA.md) owns executed evidence. The
[feng shui adapter](V3_FENG_SHUI.md) connects its separate native evaluator. No import is
enabled in either web patcher; V3 testing and explicit user approval are required.

## Sources and metadata conversion

The exact translated owner is VROM `0081D9D0`, 15,728 bytes, SHA-256
`bb2d983ca0751681838d02dd96d5e7fdf63402d2acdc8410cfd3c0f1d89712a1`.
Its 1,024-byte relocation resource is SHA-256
`a53d04cb5992a96bff77aa8cb9f022aff02764821f659c5578763b61fc6e39a5`,
with sections `(10704, 5024, 0, 1248, 245)`. Existing English mail changes are
part of the required source, not overwritten with the original Japanese owner.

The donor REL and symbol inventory are pinned by the furniture converter.
Two local symbols share the name `mMkRm_ftr_info`. The HRA definition is section
five offset `4FAFC`, 5,064 bytes, SHA-256
`231d23625c126b048d95be99f397e2f05f564af23423c1f911d706acaec37f0e`.
Name-only lookup would select the earlier, unrelated feng shui definition.

| Item | Runtime index | Donor HRA row | Native HRA row |
| --- | ---: | --- | --- |
| haz-mat barrel `3224` | 1161 | `40050200` | `40050400` |
| oil drum `32B8` | 1198 | `40050000` | `40050000` |
| cherry shirt display `3AFC` (clothing variant) | 1727 | `D4050800` | `D4051000` |
| red aloha display `3868` | 1562 | `D4050800` | `D4051000` |
| blue aloha display `386C` | 1563 | `D4050800` | `D4051000` |
| speed bag `3350` (animated variant) | 1236 | `E8050000` | `E8050000` |

The [aloha correction](V3_ALOHA_SCORING.md) binds donor mannequin rows 517/518
and supplies both installed displays' real clothing properties. Enabled records
must never use the inactive series-63 placeholder. Their full native grouping,
point evaluation, disabled exclusion, and completion-array bounds are checked.

The metadata is not directly interchangeable. Series/group occupy the high
six/ten bits in both games, followed by face and lucky flags at bits 15/14.
GC birth categories use six bits `[13:8]`, then surface `[7:6]`; N64 uses five
birth bits `[13:9]`, then surface `[8:7]`. The converter explicitly repacks
these fields and rejects categories without a reviewed native equivalent.
The static pilots are construction-series furniture with no face, lucky, or surface
flag. Haz-mat barrel uses group-C acquisition category 2; oil drum uses group-A
category 0. Both use the native ordinary-acquisition point weight.

The expanded table has 1,267 rows without clothing and 2,051 with clothing;
both preserve all 947 real native rows. The clothing display uses series 53,
group 5, and birth category 8, from verified donor mannequin index 682.
Its [reader specification](V3_DISPLAY_ITEM_READERS.md) records conversion and
passing current native scoring evidence. Selected
imports occupy their stable room indices, not their larger catalogue bit
indices. Unselected gaps use inactive series 63 and are rejected by the selected
profile range helpers. The one-past-native marker `1ECC` is admitted by the
original upper bound, so row 947 is an inert OTHER/unobtainable record with
zero points. It cannot index series 63 into the completion buffer and
is not a new collectible item.

## Native readers and bookkeeping

Forty checked detours cover twenty furniture range decisions and twenty index
conversions. Lower/upper register aliases, branch-likely annulment, original
branch-delay entry points, full-width integer registers, HI/LO, and floating
registers are preserved. Range detours use the existing selected-profile query;
index detours preserve rotation while producing the actual room index. Dynamic
returns use the real loaded HRA pointer at `80107B50`.

Forty-eight relocated table/end references target the appended metadata.
The adjacent native wall/floor category table is not an expanded-table endpoint
and remains untouched. All four native group-assignment functions keep their
original loops and rules; the expanded count preserves the unrolled loop shape.
Construction has nineteen native records plus the two selected imports, giving
21 distinct groups within its original 32-bit completion mask. Disabled subsets
exclude their metadata before grouping, not just their names.

The small missing-item search retains native series/group matching but converts
an imported runtime index back into its real `3xxx` item ID. It checks the actual
enabled import profile using a runtime index. Unselected, unassigned, and invalid
matches do not return a substitute item. The complete English name reader used
by HRA letters accepts these imported item IDs. The independent
score-letter series-name translator includes the new boxing name.

## Boxing-theme storage

`tools/v3_hra_series.py` expands the animated variant to **59 series**. It
preserves the native 55 definitions and ten-byte name keys, reserves 55–57
with disabled type `FF`, and installs boxing at its actual donor series 58,
type 2. The complete donor descriptor/name tables are hash-checked. The
original 55-entry search storage remains untouched; a new 59-word array holds
completion masks. All 27 native references to these three resources and all
seven series bounds are checked and retargeted.

The count is deliberately not the donor's 60. Native necessity scoring handles
three initial rows and then four per iteration; theme wall/floor matching
handles one initial row and then two per iteration. Both use equality at the
end. A 59-entry table preserves both termination rules without rewriting
scoring code. The initializer clears all 59 masks; group assignment retains
the actual native rules. The installed speed bag receives group zero within
its own one-item selected boxing group, not the construction or OTHER group.

Boxing's donor wall/floor index 65 has no installed mapping in this profile.
Its native descriptor explicitly uses `FF` for no matching surface, so an
unrelated native wall/floor cannot award completion or produce a bogus item
recommendation. Matching donor surfaces can be added by their own import
adapter; they are not mandatory dependencies for selecting a standalone item.
The ten-byte boxing key contains its complete English name. The
[score-letter extension](#english-boxing-score-letters) recognises it alongside
all original name keys.

The model row is enabled in the private gameplay build and included in its
selected save profile. Missing-item recommendations still reject it when the
profile's runtime row is disabled.
The [boxing checkpoint](../docs/checkpoints/V3_SPEED_BAG_HRA.md) owns the current
native scoring evidence and remaining integration limits.

## English boxing score letters

`tools/v3_hra_mail.py` preserves the complete V3 generated-letter creator at
VROM `03200000`, including its full-name readers, dispatcher, and every
original template. It appends a 1,456-byte table containing all 55 original
ten-byte keys and sixteen-byte English names, followed by boxing. Lookup row
55 is independent of the game's series index 58. Both name references and
four loop/sentinel bounds are patched, together with the guarded resource
length. The nearby literal 55 for template `37` remains unchanged.

The image grows from 61,200 to 62,656 bytes, within the native loader's
65,536-byte image limit. Its 960-byte relocation table retains every record;
the complete blob is 63,616 bytes. The module-approved lengths and CRC are
updated. Independent relocation at three addresses verifies unrelated code
and data. No saved record format or original English wording changes.

The [gameplay-connections checkpoint](../docs/checkpoints/V3_SPEED_BAG_GAMEPLAY.md)
records passing native creation and complete text restoration for both boxing
templates, an original exotic-series letter, and a speed-bag item recommendation.
Unknown name keys leave the output untouched.

## Allocation and relocation

The on-demand pair moves to VROM `03F40000` / `03F48000` using the same DMA
indices. No additional DMA-directory slot is consumed. All original linked
text/data/BSS addresses remain unchanged; original BSS is included as zeroed
space before the appended code/table at `80929C30`.

The expanded image is 27,152 bytes without clothing, 30,288 with clothing,
and 31,296 with boxing storage. Growth above the native 16,976-byte resident
size is respectively 10,176, 13,312, and 14,320 bytes. All fit the 32-KiB image
limit. Boxing adds 1,003 resource bytes plus five alignment bytes without
additional executable text. The relocation resource is 1,184 bytes. The scheduler requests
the actual expanded image size and loads the moved pair. Its original allocator,
free helper, evaluated-points return, and mail-success handling remain unchanged.
The native overlay loader separately allocates/frees its relocation scratch.
The fixed resident V3 prefix remains 48 KiB, without additional permanent
allocation or saved fields for scoring.

The installer checks exact source identity, complete range/index inventories,
incoming branch targets, relocation ownership, collisions, table bounds, every
scheduler word, and full image reconstruction. Independent relocation at three
addresses verifies unchanged native code/data/BSS outside the declared patches.
The existing 64-MiB cartridge bound and exact import-free V2 output remain enforced.

Ordinary gameplay allocation, a whole-house evaluation with mail delivery,
placement/pickup, and original-hardware acceptance remain explicit limits.
