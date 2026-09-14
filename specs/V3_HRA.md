# V3 furniture HRA evaluation

## Scope

The haz-mat barrel and oil drum participate in the native HRA evaluator with
their actual donor properties. Native scoring formulas, theme rewards,
wall/floor rules, mail selection, complete English score-letter creator, and
delivery-success handling remain intact. This is not a port of GameCube's
additional rooms or house-model rewards.

The [checkpoint](../docs/checkpoints/V3_HRA.md) owns executed evidence. Feng shui
uses a separate evaluator and remains the next integration step. No import is
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

The metadata is not directly interchangeable. Series/group occupy the high
six/ten bits in both games, followed by face and lucky flags at bits 15/14.
GC birth categories use six bits `[13:8]`, then surface `[7:6]`; N64 uses five
birth bits `[13:9]`, then surface `[8:7]`. The converter explicitly repacks
these fields and rejects categories without a reviewed native equivalent.
The pilots are construction-series furniture with no face, lucky, or surface
flag. Haz-mat barrel uses group-C acquisition category 2; oil drum uses group-A
category 0. Both use the native ordinary-acquisition point weight.

The expanded 1,267-row table preserves all 947 real native rows. Selected
imports occupy their stable room indices, not their larger catalogue bit
indices. Unselected gaps use inactive series 63 and are rejected by the selected
profile range helpers. The one-past-native marker `1ECC` is admitted by the
original upper bound, so row 947 is an inert OTHER/unobtainable record with
zero points. It cannot index series 63 into the 55-entry completion buffer and
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
by HRA letters already accepts these imported item IDs.

## Allocation and relocation

The on-demand pair moves to VROM `03F40000` / `03F48000` using the same DMA
indices. No additional DMA-directory slot is consumed. All original linked
text/data/BSS addresses remain unchanged; original BSS is included as zeroed
space before the appended code/table at `80929C30`.

The expanded image is 27,152 bytes, adding 10,176 bytes to its native 16,976-byte
resident size. The relocation resource is 1,184 bytes. The scheduler requests
the actual expanded image size and loads the moved pair. Its original allocator,
free helper, evaluated-points return, and mail-success handling remain unchanged.
The native overlay loader separately allocates/frees its relocation scratch.
The fixed resident V3 prefix remains 48 KiB; this component uses ABI 19 and adds
no permanent allocation or saved field.

The installer checks exact source identity, complete range/index inventories,
incoming branch targets, relocation ownership, collisions, table bounds, every
scheduler word, and full image reconstruction. Independent relocation at three
addresses verifies unchanged native code/data/BSS outside the declared patches.
The existing 64-MiB cartridge bound and exact import-free V2 output remain enforced.

Ordinary gameplay allocation, a whole-house evaluation with mail delivery,
placement/pickup, and original-hardware acceptance remain explicit limits.
