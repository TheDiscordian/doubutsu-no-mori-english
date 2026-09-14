# V3 shared clothing item readers

The clothing variant's shared item readers recognise selected item `34BF` as
`cherry shirt`, native clothing category 12, with the verified donor price of
380 Bells. The complete sixteen-byte name is copied only with sufficient
capacity and a valid destination. Full-width invalid name IDs are rejected.
Selection bit `BF` in the clothing profile and the complete checked resource
record are both required. Adjacent IDs do not alias furniture rotations or the
shirt. All original item paths and both furniture imports remain active.

The shared size function retains the native fallback zero. The footprint
function is specifically `mRmTp_GetFurnitureData`, not a general one-tile item
query. Clothes retain its native non-furniture result: return 3 and clear all
four twelve-byte cells. The separate [display readers](V3_DISPLAY_ITEM_READERS.md)
support placed alias metadata, category, footprint, and canonical ownership.
Global pocket/display conversion and ordinary mannequin placement remain work.

## Installation and memory

ABI 32 redirects the five existing public item helper entries through guarded
eight-byte jumps to implementations appended to the separate clothing codec.
The complete original helper and fixed clothing-resource dependency are checked
before editing. Existing native entry hooks and original-function bridges stay
unchanged. Save-code instructions, selected profile, runtime state, and artwork
are retained. The resource remains within VROM `03F0F400..03F0FFFF`, loaded to
`8046D000` by the checked startup descriptor, without another DMA directory row.

The build compares the complete retained prefix after restoring only the five
entry jumps, ABI, and descriptor; it also compares retained save instructions,
resources, profile, and patch reconstruction. Host tests use sanitizers, actual
clothing selection/resource checks, native fallbacks, and guarded buffers.
Native evidence and exact output hashes are recorded in the
[checkpoint](../docs/checkpoints/V3_CLOTHING_ITEMS.md).

Normal [collection](V3_COLLECTION.md) records separate saved clothing ownership.
Menus/icons, wearing actions, ordinary acquisition/buy/sell,
mannequins, and ordinary gameplay/save integration remain required. Punchy's
defaults and move-in eligibility stay disabled. Both patchers remain V2.
