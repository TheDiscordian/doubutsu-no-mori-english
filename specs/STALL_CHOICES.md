# Complete festival-stall choices

The fireworks stall builds four choices from eight saved goods. Native
`80A72DB8..80A72FA4` uses a forty-byte stack array for ten-byte names and two
embedded Japanese cancellation labels. The supplied GameCube counterpart
`aEYMS_set_choise_data` uses the same item scan, first-empty-row cancellation,
and returned next-item index, with complete English labels.

## Storage and instructions

The native actor is VROM `00932B60`, linked at `80A728C0`, with its adjacent
relocation at `00933DB0`. Its 4,688-byte file has 4,528 bytes of code, 160 of
data, and no BSS. Append two sixteen-byte English labels to data, preserving
every original label and unrelated data address. New actor/relocation VROMs
are `03990000` and `03998000`. The main actor table row at `80101BB0` receives
the complete new file extent and linked allocation end. Allocation grows by
32 bytes; relocation operations and actor entry points remain unchanged.

The stack frame grows from 168 to 192 bytes. The four-row array stays at
`sp+78` and grows from forty to sixty-four bytes. Its sixteen-byte pointer array
at `sp+68` and all saved registers below it stay in place. The live choice
pointer moves from `sp+A0` to `sp+B8`. All offsets in this paragraph are hex.
Array initialisation, both row strides, four setter lengths, and frame restoration
must change together. Choice indices, returned next-item index, and messages stay.

The name loop replaces multiply-by-ten with shift-by-four, making room for the
capacity-aware resident call without moving any branch or relocation site. It
stores the row pointer, loads the original unsigned goods ID into `a2`, and calls
`af_load_item_name` with destination in `a0` and capacity sixteen in `a1`.
The existing resource and loader are required. A failed load leaves the already
space-filled row unchanged; normal native goods IDs select their complete names.

Both cancellation-copy lengths become sixteen and their existing relocated
HI/LO pointer pairs address the appended labels. The exact supplied English is
`I'm not buying! ` for the end of the goods list and `I don't want it!` otherwise.
The first label's trailing space is retained. All other strings, prices,
item-transfer behaviour, line/page boundaries, and timing stay unchanged.

## Verification

Require complete native actor/relocation identities, the exact actor-table row,
the supplied English REL and label/function hashes, and the installed resident
item resource and twenty-byte choice runtime. Reject conflicting actor/table
edits and occupied replacement DMA ranges. Preserve the original relocation
rows and change only their data-section size. Verify both relocated label pointers
and the new external name-loader call at representative legal load bases.

Focused checks cover stack ranges and saved-pointer movement, all patched
instructions, full labels, the four-row setter contract, source/dependency guards,
unchanged unrelated payloads, allocation metadata, and complete UPS reconstruction.
Count the two original Japanese labels once, with the same denominator in builds
without this feature; credit requires the installed caller, labels, and dependencies.
Item names still share their original IDs with other consumers.

Ordinary stall browsing, purchase/cancel, and save/restart join the combined v0
smoke. Static, assembly, and artifact checks are not native gameplay or
original-hardware certification. Shared dynamic-choice substitutions and other
item-name readers remain separate unfinished application work.
