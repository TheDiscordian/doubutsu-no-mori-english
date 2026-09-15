# V3 camping furnishings

## Implemented boundary

The pinned GAFE01-r0 donor supplies seven complete static camping objects:
kayak, backpack, lantern, cooler, mountain bike, sleeping bag, and propane stove.
`tools/v3_furniture_art.py --batch camping` converts their complete models;
`tools/v3_camping_items.py` verifies identity and gameplay metadata;
`tools/v3_camping_runtime.py` installs their native profiles, English readers,
catalogue entries, scoring, and selected saved dependencies in ABI 68.

Summer-camper acquisition and ordinary placement/persistence are unfinished.
These are experimental offline selections, not completed playable imports.
Neither served patcher changes. V3 source may be pushed on its development
branch; changing a patcher requires the user's testing and explicit approval.

## Identity and complete assets

The actual decoded REL, symbol file, both furniture-quality tables, names,
profiles, relocation pointers, and identity worksheet are checked. The worksheet
has no native ID, name, model, or texture mapping for these seven identities.
The checks use the supplied disc and the pinned sources recorded in
[V3_OPTIONAL_IMPORTS.md](V3_OPTIONAL_IMPORTS.md); a matching label alone is
insufficient to establish an additive import.

| ID | English name | Runtime index | VROM slot | Object bytes | Footprint |
| --- | --- | --- | --- | ---: | --- |
| `3364` | kayak | 1241 | `02430000` | 3,248 | 1×2 |
| `3370` | backpack | 1244 | `02432000` | 4,384 | 1×1 |
| `339C` | lantern | 1255 | `02434000` | 2,064 | 1×1 |
| `33A4` | cooler | 1257 | `02436000` | 2,656 | 1×1 |
| `33A8` | mountain bike | 1258 | `02438000` | 5,632 | 1×2 |
| `33AC` | sleeping bag | 1259 | `0243A000` | 2,032 | 1×2 |
| `33B0` | propane stove | 1260 | `0243C000` | 4,208 | 1×1 |

Each fixed slot reserves `2000` bytes in the existing import resource. Its
profile DMA range covers only the actual complete object, not trailing padding.
The total 24,224 object bytes contain all 524 vertices, 362 triangles, 20,864 CI4
texels, and 112 converted RGBA16 palette entries. No geometry is simplified.

The kayak has two opaque profile slots. Its second model's `onT` spelling does
not make it translucent; the actual profile pointer owns that decision.
The lantern uses the source furniture profile's unlit/off model and palettes,
not the separate animated campground light. The sleeping bag has no sleep action
bit. All seven profiles have null animation, callback, contact, and interaction
pointers; preserve their actual shape, collision, scale, height, and flags.

Converter version 6 adds an explicit camping mode, mutually exclusive with
other special-family modes. It accepts only verified clamp/mirror combinations,
the backpack's explicit clamp reset and near-white tint, reviewed tile extents,
and the lantern's unlit geometry modes. GX texture wrapping is translated into
native tile fields. Unknown commands, colours, wraps, or pointers still fail.
Complete texels, palettes, vertices, triangles, loads, and material boundaries
are checked independently in the compiled native display lists.

## Acquisition and catalogue

All seven occur once in the actual donor `ftr_listTent`, and in no other furniture
acquisition list. The complete list also contains campfire `335C`, bonfire `3360`,
and tent `336C`; those three need separate behaviour conversion. Seven static
models are not the entire camping family.

In the pinned GC source, `aQMgr_order_decide_trade_common_item` in
`src/actor/ac_quest_talk_normal_init.c` chooses the Tent list for furniture rewards
in `SCENE_TENT` when the random value is at least 80. The native common quest
selector retains its exclusions. `src/game/m_shop.c` maps the Tent list type;
`src/actor/ac_event_manager.c` supplies the summer-camper NPC and tent placement.
Copying a stock list does not supply that scene, event, NPC, or conversation.
The N64 igloo system exists, but a summer-camper adapter is not installed.

The donor catalogue's orderability query checks ordinary, train, event, lottery,
and orderable-present lists, not Tent rewards. Keep all seven not for sale even
though their item metadata contains nonzero prices. Do not insert them into
ordinary shop or generic event stock as a substitute for camping acquisition.

The full experimental furniture catalogue has 469 entries and retains all 248
clothing entries. Donor order is preserved for appended items. The mountain bike
uses donor preview mode 24 (`0.85`, `-3.0`), which is not a native mode number.
Build it through native mode zero, then apply the two final framing fields only
for its selected canonical identity. Retain other preview fields and the actual
native initializer. Four rotations, neighbouring IDs, disabled records, and
the existing clothing/Western rules are checked with sanitized C tests.

The complete catalogue code/data suffix is 3,408 bytes within its 3,664-byte
limit. The existing menu reserves 280,704 bytes; the conservative requirement
is 280,256, leaving 448 bytes. Do not extend subsequent batches without checking
both the suffix and actual menu allocation.

## HRA and feng shui

The donor uses six acquisition-category bits; category 37 means camping, with a
412-point base weight. Native metadata has five bits, and the installed evaluator
has 23 counters. Copying raw category 37 is unsafe and incorrect.

Only for HRA base-point metadata, map category 37 to native scoring category 3,
whose verified weight is also 412. Acquisition remains `ftr_listTent`. This is
not a change to the donor reward category or permission to use event stock.
`score_mapping()` checks the complete pinned current cartridge, HRA owner,
23-counter extension, weight table, and all three actual native bitfield-reader
pairs in `EvaluateBasePoint`: `809275E0/E4`, `8092763C/40`, and `80927680/84`.
The donor field is likewise consumed in its base-point evaluator. No other
native category consumer is assumed to tolerate this mapping.

Preserve the upper series/group/face/lucky fields and repack the donor surface
bits into their native positions. All seven remain series 53, whose native and
donor definition is `0000FF`; no new completion theme or letter is invented.
Native HRA words are `D4050600`, except lantern surface 2 uses `D4050700`.
Feng-shui words are copied only after verifying their complete source table:
kayak `0100`, lantern `0200`, sleeping bag `0400`, and zero for the other four.

Only those seven rows change in each scoring owner. All counters, weights,
instructions, relocations, series definitions, and English letters remain.
The mapping adds no stack, heap, or resident memory.

## Storage, selection, and saves

Use [the fixed sparse tables](V3_IMPORT_STORAGE.md) at `80484000` and `80498000`.
All old rows and runtime readers remain unchanged. There are 32 installed static
profiles and 33 furniture item records, including the separate animated speed
bag. Absent slots remain zero. Startup derives pointers from enabled rows.

The import resource has 2,414,528 bytes and 1,714,240 bytes of remaining virtual
reservation. The full DMA directory retains 3,389 entries and its sole terminator.
Catalogue and relocation data use a new tail range; scoring owners retain their
physical allocations. The checked resident package, model banks, and normal
heaps do not grow.

The offline composer has 56 experimental options: 20 villagers, 33 furniture
items, and three shirts. Canonical IDs never depend on checkbox order. An empty
selection reproduces V2, and selecting all reproduces the pinned full cartridge.
Disabled camping entries leave the catalogue and HRA grouping data; retained
asset storage is not permission to use an unselected item.

Saved format 2 and its code remain unchanged, but the full build enables seven
additional profile bits. The actual codec accepts equal/larger profiles and
rejects missing dependencies without writes. This is not proof of ordinary
cross-build loading. Preserve saves; do not load imported saves in V2.

The [checkpoint](../docs/checkpoints/V3_CAMPING_ITEMS.md) records actual build
hashes and executed verification separately from unfinished acquisition,
rendering, interactions, and persistence.
