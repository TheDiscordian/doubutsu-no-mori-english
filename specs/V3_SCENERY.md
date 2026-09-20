# V3 shared seasonal scenery

## Scope and workflow

Scenery is an engine dependency, not another item checkbox. The golden shovel
requires the donor's actual gold-tree planting, growth, and shake/drop route.
Prepared artwork does not enable that route or its item choice.

`tools/v3_scenery.py` follows source foreground tables into complete drawing
descriptors, body lists, and shadow dependencies. It feeds the shared model
converter and compiler; there are no per-season converters or item installers.
The initial `gold-tree` category discovers descriptors by source family and
obtains foreground IDs from the complete type tables.

```sh
python3 tools/v3_furniture_pipeline.py scan --representation scenery \
  --output build/scenery-inventory.json
python3 tools/v3_furniture_pipeline.py convert --representation scenery \
  --category gold-tree --assets-only --output build/scenery-assets
```

Use fresh ignored paths. `import`, conversion without `--assets-only`, individual
item selection, and unknown categories reject. Neither this adapter nor its
output edits a cartridge, save, build lock, or served patcher. Furniture and
equipment installers reject the distinct scenery bundle format.

## Complete source graph

The pinned GAFE01-r0 REL and symbols remain mandatory. Source owner order is
cherry, ordinary, winter, Xmas; native order differs and must be matched by
identity during installation. Twelve-byte foreground rows supply the drawing
index and both position arrays. Thirty-two-byte descriptors supply complete
display-list tables, ordered body lists, and optional shadow vertices,
adjustment flags, lengths, and draw lists. Body/shadow callbacks must match the
checked complete consumers. Missing or unused dependencies, unexpected fields,
and unsupported callbacks reject.

The gold-tree category contains fourteen foreground identities per season:
`007B..0081` and `0863..0869`. Ten descriptors per owner represent five growth
sizes, a dead sapling, and four stump sizes. The mature model is shared by its
reward/spent and hidden-content states. The adapter retains all 52 body-list
uses and 24 shadow-list uses, deduplicated to 37 complete material/geometry
pairs. Xmas shares winter graphics. Source positions, shadow adjustments,
callback bindings, and source/output hashes remain in the generated reports.

## Caller-supplied graphics state

The shared converter accepts explicit `render_context` contracts:

- `palette_slot`: the caller loads this palette. CI4 materials must select
  exactly that slot. Missing, overwritten, conflicting, and unused contracts
  reject. Ordinary models retain local palette loading and slot fifteen.
- `external_vertices`: one complete source array, up to 32 vertices, loaded
  by the caller before geometry. Its full contents are converted and preserved;
  every triangle is checked against its bounds. Embedded replacement vertex
  loads reject. Shadow geometry does not load static vertices over the caller's
  adjusted vertices.

Material and geometry validate together, then compile into independent lists.
Body ordering remains material → instance matrix → geometry. Shadow ordering
remains material → shadow colour → instance matrix → adjusted vertices →
geometry. Caller-owned colour, matrices, and adjustments are not guessed.

Gold body materials use palette slot eight. The field palette initializer uses
the original eighteen-term selector and all fourteen sixteen-colour palettes.
All 448 bytes convert from RGB5A3 to RGBA5551; partial alpha rejects instead of
being discarded. Six shadow pairs retain complete four-vertex source arrays,
I4 textures, and wrapping.

## Runtime installation and ownership

`tools/v3_scenery_runtime.py` installs the prepared category through the shared
runtime refresh. It validates the complete source graph and prepared resources;
it does not reconvert the models or add individual-item definitions.

```sh
python3 tools/v3_furniture_install.py --refresh-runtime \
  --scenery-art build/v3-scenery-gold-tree-01 \
  --base-lock build/v3-shared-balloon-menu-04/build-lock.json \
  --output build/scenery-runtime
```

Each seasonal owner owns one 32,864-byte bank appended to its BSS. The nineteen
objects retain complete vertices, textures, material/geometry lists, descriptors,
position arrays, and adjusted-shadow dependencies. Three cartridge banks cover
the four owners; Xmas shares winter. Verified retired module copies supply
cartridge storage, with explicit live reservations preventing subsequent reuse.
The import blob and its DMA identity do not grow or overlap English choices.

The equipment module retains its size and guards. Its unused
`804ADC90..804ADFEF` range contains a 267-byte bootstrap, bounded before the
retained guard at `804ADFF0`. Constructors transfer and verify a 2,892-byte code
packet into the reserved `804B5000..804B5FFF` range, flush the instruction cache,
then prepare the native/held table and load the active scenery bank. A missing
or corrupt resource enters the existing fault reporter instead of constructing
an actor with invalid pointers. The five added diagnostic strings are credited
to the assistant in the single text catalogue.

The bank's 128-byte header records separate CPU, graphics, and callback fixups;
all pointers are offsets before loading. CPU pointers acquire the owner's
address; graphics pointers become physical segment-zero addresses. Callback
roles bind to the loaded owner's original shadow loop and the shared body
wrapper. No heap address persists between scene loads. Complete fixup bounds
are checked before relocation. Graphics retain source order and slot-eight
palette selection. The body wrapper follows the native eighteen-term calendar,
refreshing the active 32-byte palette when needed before calling the original
body loop. Caller-adjusted shadow vertices are not replaced by static vertices.

Ten previously unused descriptor slots hold the category: `65..74` for cherry,
ordinary, and Xmas, and `64..73` for winter. Original rows, the NONE sentinel,
all installed held-item rows, actor sizes, stack frames, and existing copy
capacities remain intact. Further category expansion must respect the scenery
owner records' reserved slots; zero category-map entries are not blanket proof
that those drawing indices remain free. Native foreground tables contain 112
low and 84 environmental rows. All fourteen imported IDs lie outside those
existing ranges; no original scenery identity is replaced.

The owner-local classification entry preserves the native routine through a
cache-flushed trampoline. Selected golden-shovel profiles resolve the complete
new type/position records. Original items call the native routine, retaining the
held-category hooks. Disabled imported foreground IDs resolve the native empty
row rather than indexing beyond a native table. Save/profile restrictions still
apply; this fallback does not authorise removing imports from a saved world.

The explicit ABI-149 proposal is `build/v3-shared-scenery-04/build-lock.json`.
It adds a 4,096-byte fixed reservation and 32,864 bytes per loaded seasonal owner.
All existing 128 experimental choices and format-3 saves remain unchanged.
The main ABI-109 lock and both served V2 patchers stay unchanged. Component tests
cover native loading, all seasonal type bindings, actual body-list generation,
guards, and restoration; rendered appearance and ordinary gameplay are not
claimed.

## Remaining gameplay integration

Reuse the installed renderer and prepared resources. World collision,
planting, growth/death, cutting, shaking, and selected-only acquisition remain
required. The source plants an ordinary shovel in a shining hole; do not
substitute shop stock, arbitrary letters, recoloured ordinary trees, or seeded
pockets for this route. Existing celebration and collection consumers remain
installed, but all four golden choices stay disabled until their routes work.

The [checkpoint](../docs/checkpoints/V3_FURNITURE_PIPELINE.md#shared-seasonal-scenery-preparation)
records resources and focused checks. Component checks do not establish
gameplay, rendered appearance, persistence, or original-hardware verification.
