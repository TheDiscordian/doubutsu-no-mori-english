# Automatic furniture pipeline checkpoint

## Parent-item and room-display discovery

Converter/installer revision 8 adds `tools/v3_room_aliases.py`, shared by the
full donor inventory, furniture pipeline, and browser review generator. Complete
donor placement, pickup, and both item/index functions are checked before their
actual range constants supply the records. No per-item identity list, converter,
installer, or scenario is added.

The six categories contain 48 room-display models: eight balloons, sixteen
diaries, eight fans, eight pinwheels, four golden tools, and four ordinary tools.
Four balloon models fall in `1xxx`; the other 44 entries occur in the `3xxx`
queue. Every record retains the official parent name/source hash, parent ID,
all four rotations, pickup ID, and the actual `no_convert_tools` condition.
Seven worn-axe inputs share the ordinary axe's model and return the ordinary
axe ID on pickup. That donor asymmetry is explicit, not seven new furnishings.

Aliases cannot install as standalone furniture, including through older asset
reports. Prepared artwork retains the parent relationship; unsupported graphics
keep a separate `conversion_reason`. The full 2,333-name donor inventory keeps
its original identities and links each parent/display pair; the worn states
also link to their canonical parent. Classification does not approve a native
identity, complete room conversion, or implement the parent's actual gameplay.
No new selectable option is claimed. Both served patchers remain V2.

Actual supplied-disc/N64 inventory generation succeeds at
`build/v3-room-alias-discovery-01/donor-catalogue.json`, SHA-256
`29b575ef4705816d90b70298628e47d05336e6edd3cc65fdfeda323142901363`.
The final current scan is `build/v3-room-alias-discovery-02/inventory.json`,
SHA-256 `771dd65a627aec167e3844ab64fd7ba9788cb2e1e40fae30c2a4cc1db2366f6b`.
It records 76 converter-supported and 166 review rows, with no supported new
uninstalled furniture. Those statuses describe converter eligibility, not the
larger installed set or completed gameplay. Of the 54 uninstalled entries in
the existing bulk-prepared batch, sixteen are diary aliases, thirteen retain
unknown acquisition, twelve require Tortimer gifts, six harvest acquisition,
five island acquisition, and two native identity review.

The focused run executes 44 tests: 41 pass, two optional prepared-asset tests
are skipped, and one assertion still expects the old diary acquisition reason.
Its correction verifies the actual parent-support rejection. The targeted run
passes seven tests, including the corrected assertion, the six alias tests,
and current revision-7 artwork acceptance through complete current validation.
Across both runs, 43 distinct checks pass and two are skipped. Coverage includes
all ranges/rotations, cross-range balloons, every parent name, worn-state
canonicalisation, changed complete code/helpers/relocations, full inventory
links and repeat annotation, shared scan/metadata rejection, rejection before
conversion creates files, installed-alias refusal, and generated browser review
data. Existing graphics/parser/material checks also pass. No emulator is replayed
for a discovery-only change.

The ABI-95 cartridge retains SHA-256
`01c7da7f945f02a4eebb1bafdc258b0485db5dd9240cf2254a51f3eefaccd68c`.
Its build lock, 104 installed choices, saved format, and runtime are unchanged.
The private browser interface export is not regenerated or served.
Next work is native parent identity/gameplay and shared placement/pickup support,
plus the still-missing graphics categories; these dependencies are not waived
by recognising the aliases.

## Constant model-sequence imports

Converter/installer revision 7 adds the shared `constant-model-sequence`
category. Complete compiled draw functions, actual model-pointer relocations,
and the one matrix-helper call establish fixed one-/three-model submission.
Null lifecycle slots are supported, but present lifecycle callbacks must be
complete no-ops. Extra code, calls, DMA callbacks, changed relocation pairs,
and effects are rejected. The same checked-code normaliser serves the existing
palette-fade category without changing its source receipts or runtime.

The converter links complete native lists in donor order with a generated
display list, recorded separately from the original model lists. The normal
opaque profile slot points to that sequence; generic rigs, animations, and the
callback pointer remain null. Lady Liberty retains all three material layers
on the opaque command stream, including their original internal material modes.
The tanabata palm retains its complete single list. Source scalars are unchanged.
No per-item integration script, runtime callback, scenario, or allocation is added.

The unrestricted category conversion at
`build/v3-furniture-static-sequence-assets-01/` discovers both eligible records:
Lady Liberty `3010` (6,736 bytes) and tanabata palm `3054` (4,416 bytes).
Together they retain 11,152 bytes, 248 vertices, and 179 triangles. Generated
links occupy 32 and 16 bytes respectively. The installer regenerates their
exact order, target addresses, bounds, hash, and normal profile binding.
Official names are credited in `translations/provenance.json`. Lady Liberty
uses the existing selected Gulliver reward category and remains non-orderable;
tanabata palm uses the donor event-stock list and actual catalogue policy.

The ABI-95 cartridge is
`build/v3-furniture-static-sequence-runtime-01/animal-forest-v3-asset-loader.z64`.
Automatic additions total 42. The offline composer contains 104 installed
choices: 81 furniture, three shirts, and twenty villagers. The model bank,
item-rendering code, saved format, and existing assets remain unchanged. Blob size
is 3,407,488 bytes, leaving 721,280 before English choices. The catalogue's
conservative memory requirement remains 280,384 of 280,704 bytes.

- ROM SHA-256: `01c7da7f945f02a4eebb1bafdc258b0485db5dd9240cf2254a51f3eefaccd68c`.
- UPS SHA-256: `2d893591aa7f6b49f5e27f1749cfc8a19ae51d8f998eb232143e4428aebdbaf3`.
- Build receipt SHA-256: `0f3991f6e27f59cd9698bbffe7dbe618b528e719773efd5906905b469bd75c9a`.
- Art receipt SHA-256: `aaf6e06e8d3cec9cc705d016dbf86e932703aa8e70a5fb066c12b1f3bb4006a8`.

The combined pipeline/composition suite runs 60 tests: 59 pass, and the
scoring-alias test is skipped because these two records need no alias. The
prepared palette batch is supplied to check that shared code normalisation
retains that category. Complete texels, vertices, triangles, material state,
ordered links, invalid source rejection, retained assets/code, names/credits,
stock/rewards, scoring, catalogue, profile subsets, and exact V2/no-import output
pass. The first silent current-build native run at
`build/v3-furniture-static-sequence-native-01/results.json` passes 124 records
and 85 assertions, SHA-256
`82491eb4dda46a75c9e32bfda38a32bef6d70a7d93b6e8add3d4753b014d31f9`.
It covers actual owner loading/relocation, both complete model transfers,
source framing, selected Gulliver rewards, event stock, acquisition/ownership,
restored state, and guards. Unchanged palette callback evidence is retained;
that scenario is not replayed. The emulator exits cleanly.

Ordinary appearance, interaction, complete catalogue construction, save/restart,
and hardware acceptance remain open. Saved format 2 is unchanged, but saves
containing these new identities must not load older builds or V2. Both served
patchers remain V2, and the private interface export is not regenerated.

The follow-up source review identifies the tools/fans/pinwheels/diaries as
room-display aliases of parent items, not independently acquirable furniture.
The donor forward function is `.text:0760E4`, 640 bytes, SHA-256
`5228a779089eca94c3f751a814e169f74ff085a57626673c86d7d789fadd6c66`;
the inverse is `.text:076364`, 664 bytes, SHA-256
`a948f3ad02dcf0d9f967363bb22203091447edbb416345498564bb18efda353e`.
Their source is `local/ac-decomp/src/game/m_room_type.c`. The native equivalents
in `upstream/af/src/code/m_room_type.c` lack those extra categories. Parent
identity classification and room-conversion implementation remain work; this
finding does not declare those aliases supported or discard their dependencies.

## Shared switchable-palette category

Converter/installer revision 6 discovers eight complete building-model callback
sets without an item allowlist. Normalised complete PowerPC implementations,
exact local call targets, all relocation pairs, both endpoint palettes, and
actual draw order identify one reusable behaviour. All three layers remain on
the donor's opaque command stream, retaining each list's own material mode.
Constant transparent colours survive; changing colours require opaque endpoints.
Roof-colour selection and clocked station models are not silently flattened.

One category conversion produces all eight objects at
`build/v3-furniture-palette-fade-prepared-02/`: 29,664 bytes, 555 vertices, and
346 triangles. Each generated 32-byte header describes its complete size,
palettes, and ordered model pointers. Source callbacks and dependencies are
recorded in each descriptor. Post model requires `ftr_listPostoffice`; police,
museum, market, Katrina's tent, shop, and tailor models have no identified
acquisition list. Those seven remain prepared-only, not selectable gameplay.

The ordinary converter/installer discovers igloo model `31A4` and installs its
complete 2,944-byte object, official name, price, preview, scoring, canonical
profile, and winter-camping reward metadata. There is no dedicated item script,
browser entry, or native scenario. The installed name is credited in the single
provenance catalogue. Automatic additions total 40; the offline composer supplies
102 installed choices: 79 furniture, three shirts, and twenty villagers.

The shared callback compiles to 988 bytes, including reserved table/layout holes,
inside the existing 1,024-byte tent allocation. `80483700` retains the legacy
tent table; `80483720` is the generated-layout table. Creation, float-0.1 movement,
destruction, and drawing are shared; an immutable compatibility layout preserves
the installed tent object unchanged. The current item loader is 1,920 of 2,048
reserved bytes. It accepts the category by callback contract, not by a new item
ID case, and validates the complete loaded header before bank registration.
Startup already invalidates this complete code range; no new startup range,
heap, saved format, or permanent reservation is needed.

ABI 94 is pinned at
`build/v3-furniture-palette-fade-runtime-02/animal-forest-v3-asset-loader.z64`.
The `runtime-01` and `runtime-02` ROMs have the same SHA-256; the second receipt
also binds the legacy tent's current shared code/table correctly. No second
emulator replay is needed for that receipt-only correction.

- ROM SHA-256: `8dcb481ce08eb7bacbc4661cb06ec910bf3ec41d3eb6d3bb753ab0ebcfb6e358`.
- UPS SHA-256: `65d3bda763c7949146fb08d71a0dad11f6bdc73f8d6a51a2bd4c461d0cd5f972`.
- Build receipt SHA-256: `cfc62b59db3b27343a4bba5ce768cd878b6b0c7d09bb439c79176888b8a4ca0d`.
- Complete callback reservation SHA-256: `d9d7f05fe744e0e74ae712e1f53e09bd8372dc69af08001de9c9e40e2b189d5c`.

Blob size is 3,396,336 bytes, leaving 732,432 before English choices. Catalogue
memory is 280,384 of 280,704 reserved bytes. Every previously installed model
retains its VROM and data; only the declared helper/code tables change.

The combined focused suite executes 56 tests. Fifty-five pass; one old blanket
assertion incorrectly disallows the intentional furniture-loader change. Its
targeted correction verifies the exact declared helper/public jumps and proves
the rest of the resident prefix unchanged. That corrected test and a new complete
code/layout/vtable-binding test both pass: 57 distinct checks covered. Sanitizers
execute the shared C with all eight converted objects and the legacy tent,
covering independent instances, mid-fade reversals, submitted-frame lifetime,
all model commands, every palette colour, malformed headers, crowded graphics
arenas, and actor/arena guards. Complete texel/vertex/triangle/material checks,
source rejection, official credit, catalogue/scoring, optional subsets, full
profile, exact no-import V2 output, and saved-profile rules also pass.

The initial native invocation mistakenly omits the required Expansion Pak and
uses the short default timeout; the emulator disconnects before the startup
assertion. It supplies no gameplay result. The one corrected invocation uses
the explicit eight-MiB setting, 180-second bound, and existing Xvfb executable.
`build/v3-furniture-palette-fade-native-02/results.json` completes 190 records with
114 passing assertions, SHA-256
`5ed7848e5a353f5e0fff69f47d85106a8463c32eeb68d18192de1a87b8d474c8`.
The shared representative scenario verifies actual new/legacy model DMA,
all four callbacks, both draw layouts, full interpolated colours, surviving
submitted palettes, actor preservation, full seasonal trade preparation,
acquisition/ownership, restoration, and guards. The emulator exits cleanly.

Ordinary appearance, interaction, full catalogue construction, save/restart,
and original-hardware acceptance remain unverified. Saved format 2 is unchanged,
but saves using the new item must not load earlier builds or V2. Both served
patchers remain V2; the recorded private UI export stays at its earlier snapshot.
Continue remaining shared acquisition/callback categories, not per-item scripts.

## Shared seasonal reward records

Converter/installer revision 5 installs snowy tree model `31A8`, snow bunny
`31D4`, and sleigh `31E0` through the unrestricted automatic conversion and shared
installer. Their complete models contain 13,728 bytes, 322 vertices, and 275
triangles. No item-specific converter, integration script, or native scenario is
added. The three names use the official donor records in the single provenance
catalogue. Automatic additions total 39. The offline composer contains 101
installed development options: 78 furniture, three shirts, and twenty villagers.

The complete ABI-93 cartridge is
`build/v3-furniture-camping-runtime-01/animal-forest-v3-asset-loader.z64`, pinned
by `config/v3-import-build.json`. Artwork is in
`build/v3-furniture-camping-assets-01/`. The catalogue has 514 furniture and 248
clothing rows. Conservative menu memory remains 280,320 of 280,704 bytes. Blob
growth is exactly the 13,728 artwork bytes, to 3,393,376 bytes, leaving 735,392
bytes before English choices. Existing owner allocations and model VROMs remain.

Winter acquisition uses actual `ftr_listKamakura`, donor list type 19. The donor
normal-trade function at `.text:122B8C` rolls `random(100) >= 90` in scene 31;
the separate 10% house-gift roll follows it. The native body lacks this winter
special-list roll. The shared trade adapter enables it only when winter imports
are selected; otherwise the original native body runs without another RNG draw.
Summer scene 35 retains its `>= 80` roll and list type 23. Carpet/wall donor
descriptors have neither special-list pointer and retain physical-A fallback.

Both seasons and Gulliver share the same source-derived item metadata. The ten
summer items no longer live in a hand-maintained runtime array. All seventeen
installed reward records carry their actual category in byte 27. The 948-byte
resident reader preserves rare/existing-item exclusions, the donor's small-list
duplicate allowance, and exhausted-profile fallback. It exports a checked count
entry at `80474EFC`, used without randomness to select winter's original-body
fallback. Code and guards fit the same `80474BB0..80474FEF` reservation.

The dependent camper suffix compiles to 1,152 bytes, down from 1,344, with 192
zero padding bytes. Its complete normal owner remains 20,736 bytes and its
relocation file remains 2,272 bytes, with 558 entries. The original prefix outside
the two entry hooks, native state, quest descriptors, callbacks, and shared
conversation allocation remain unchanged. Both relocated bases are checked.
Future automatic batches rebuild the suffix against the actual resident count
entry rather than assuming a stale compiled address.

HRA donor category 33 maps to native scoring category 3, using the same verified
412-point equivalence as summer category 37. The actual donor point table,
installed native weights, expanded evaluator patches, and all three native
five-bit consumers are checked. This changes scoring metadata only, not the
reward route. Native counters, point weights, and stack allocation stay intact.

- ROM SHA-256: `fe9b175801c5b1d7eb00b7ddf23d01d4fd164643cd01d9f2f6270d7e89f8598e`.
- UPS SHA-256: `e80813e4d538cfe5d117afbc07e6d2ca90d3dc1bd01704a092aa3e4c881669ad`.
- Build receipt SHA-256: `4973f7d2705be2c280c321d29b7c51daddfa2e708b949db5c6cfd6153a5ec1c3`.
- Art receipt SHA-256: `463e19c092235b63f907b12a8493e799e6d2561268c2b4c16a404f6a8ebb26cf`.
- Blob SHA-256: `f4301306b6245a24b59d62225f34ded2d44545b615699f1224eaf2ad43d2e91c`.
- Shared reward code SHA-256: `193943c60d253c8eacc76250d2960a902ff8e79d648efa10587a61b36fd430b1`.
- Trade owner SHA-256: `1a6571128da3e3c8171a347af5a829eb8acaf3246362c0fcb5b7a5074056037e`.
- Trade relocation SHA-256: `f4a0fffe3564208ccd2ec1e95d65c8703a7f5efc54c62bbfbccad237bb5246bd`.

The combined suite runs 52 tests: 51 pass and the optional prepared-only artifact
check is skipped. Sanitizers execute the actual shared selector and camper C,
including all ten summer identities, sparse profiles, both seasonal thresholds,
house override/empty-house fallthrough, duplicate/exclusion rules, and unchanged
ordinary trades. Complete source texels/vertices/triangles, material commands,
owner-prefix retention, fixed allocations, scoring equivalence/rejection,
catalogue, source credits, profile composition, and exact V2/no-import output pass.

The first silent native run completes all 162 records with 118 passing assertions
at `build/v3-furniture-camping-native-01/results.json`, SHA-256
`c2cff0b14ccb4f61b7b2e95c37715fbe4ac3cf52fee77a80c06c6c90c1cfc92d`.
It covers actual current owner loading/relocation, complete model DMA, readers,
preview, ownership, all three selected reward categories, sparse first/last
choices, no-selection native stock fallback, and complete seasonal trade calls.
Real RNG seed 7 produces the selected winter reward; disabling winter imports
executes the original native trade body. Seed 6 checks the unchanged summer
threshold through the shared reader. Input identity/slot, carpet/wall candidates,
pitfall mode, state restoration, guards, and clean shutdown pass. No native retry
is needed, and no old build is rerun.

These results do not establish ordinary camper conversations, handover animation,
GPU appearance, full catalogue construction, save/restart, or original-hardware
playtesting. Saved format 2 and permanent allocations remain unchanged, but saves
using the three new IDs must not load older builds or V2. Both served patchers
remain V2 pending the user's testing and explicit approval.

The post-scan at `build/v3-furniture-camping-post-scan-01/inventory.json` identifies
73 supported entries, all installed, and 169 review entries. This includes seven
already-installed summer models now recognised by the shared metadata path.
Fifty-four additional real models pass artwork preparation but retain their
actual requirements: 29 unidentified acquisition routes, twelve Tortimer gifts,
six harvest, five island, and two identity reviews. Sixteen diary models also
need diary gameplay. Continue shared acquisition/callback categories and the
remaining V3 gameplay/browser integration; prepared assets are not playable imports.

## Shared acquisition categories

Converter/installer revision 4 discovers, converts, and installs five further
objects without an item list: Arc De Triomphe `3014`, mermaid statue `301C`,
plate armor `3034`, Chinese lion `3050`, and festive flag `327C`. Complete artwork
totals 20,128 bytes, 487 vertices, and 401 triangles. The four souvenirs use the
actual `ftr_listJonason`; the flag uses `ftr_listTrain`. Every name has official
source attribution in `translations/provenance.json`. Automatic additions total
36, with 98 installed offline development options: 75 furniture, three shirts,
and twenty villagers.

The complete ABI-92 cartridge is
`build/v3-furniture-acquisition-runtime-01/animal-forest-v3-asset-loader.z64`, pinned
by `config/v3-import-build.json`. The artwork is in
`build/v3-furniture-acquisition-assets-01/`. The shared catalogue has 511 furniture
and 248 clothing rows, using a conservative 280,320 of 280,704 menu-pool bytes.
The blob is 3,379,648 bytes, leaving 749,120 bytes before English choices.

The train gift uses native list 4 and its catalogue-orderability mask. Gulliver
already exists in the N64 game: actor `A8`, owner `00958220`, RAM `80A97FB0`.
The original gift function at `80A983B4` selects native rare furniture; the donor
selects souvenir list type 12. Only its list argument at `80A983BC` and selection
call at `80A983D8` change. Native conversations, inventory checks, demo requests,
pocket insertion, and event completion remain. The complete owner and unchanged
304-byte relocation resource are checked. The 3,712-byte compressed owner moves
once to uncompressed blob storage before the three regenerable terminal owners;
future batches can update it in place without accumulating copies.

One shared 700-byte reader at `80474BC0` uses canonical item metadata byte 27 and
enabled profiles, not per-item switches. Encoded route `0C02` supplies donor
category 12 with native fallback 2. Selected souvenirs retain the donor's random
rare-item rejection; empty/all-excluded selections use the original native route.
Souvenirs stay non-orderable and absent from ordinary shop lists. The code and
guards fit the checked gap between preview data and accessory artwork. Startup
is 924 bytes and explicitly invalidates the helper's code range. No permanent
RAM reservation, item-record width, saved format, or original identity changes.
Saved format 2 remains; saves containing these new IDs must not load older builds
or V2. Ordinary cross-version save/restart compatibility is not newly claimed.

- ROM SHA-256: `ffe996df066c4bfb85f8a438ffef852691e1e2ea4a58bda81d3816c2f3b92252`.
- UPS SHA-256: `4bf6a6e7d039dc431f7e81b21198ad4f75cce98edf7c67f5e8ba0da7c797bb5d`.
- Build receipt SHA-256: `5c99e5d37918f14f0af315eeaf77e6899300acf1acd922e9de2b0a023521db3d`.
- Art receipt SHA-256: `d02e0c22a1badb5dd11afc4a76ad7613add19004499c4d713099a9b5557c6a77`.
- Blob SHA-256: `066fefd4aba0bf5026b1866fb70b6c2a1dfab18d5954b7feb19b562513042679`.

The combined focused suite runs 49 tests: 48 pass and the optional prepared-only
artifact test is skipped. Complete conversion/material checks cover the new
installed batch. Host sanitizers cover multiple reward categories, sparse and
disabled records, canonical identity validation, random endpoints/rejection,
rare-only fallback, and all seven native arguments. Cartridge checks verify the
complete owner with exactly two instruction changes, retained relocations,
non-orderability, repeated helper installation, safe terminal reuse, source text
credits, scoring, subsets, select-all, and exact import-free V2 composition.

The first native run passes 87 assertions in 104 records, then the harness rejects
a direct upper-memory helper call before executing it. This is the debugger's
explicit below-4-MiB proof restriction, not an observed game failure. Its evidence
is retained at `build/v3-furniture-acquisition-native-01/results.json`, SHA-256
`08637abdc036b6dc2ac34dd0f56be9bf40edd445c564232635eb4cec67c582d4`.
The test reuses its existing checked low-memory jump bridge; no cartridge change
or debugger-permission expansion is needed. The one corrected retry passes all
131 records with 104 assertions at
`build/v3-furniture-acquisition-native-02/results.json`, SHA-256
`81bd7f935c9c901e334b3b54ac5cb5b85727df1d7dcc611566f63e6065838dc8`.
Representatives are selected by category (`3034`, `301C`, `327C`), not separate
scenarios. Actual owner loading/relocation, installed call instructions, complete
model DMA, native readers/footprints, preview, stock/catalogue rules, acquisition,
ownership, two isolated sparse souvenir selections, empty-selection native reward
fallback, restored state, and all final guards pass.

These checks do not establish ordinary NPC conversations/gift animation, train
gift delivery, GPU appearance, full catalogue construction, save/restart, or
hardware playtesting. Both served patchers remain V2. Source may be pushed;
switching either patcher still requires the user's testing and explicit approval.

The post-scan at `build/v3-furniture-acquisition-post-scan-01/inventory.json`
contains 63 supported entries, all installed, and 179 review entries. Fifty-seven
uninstalled real models pass artwork preparation: 29 unidentified acquisition
routes, 12 Tortimer gifts, six harvest, five island, three winter-camper, and two
identity reviews. Diary gameplay remains an additional dependency for sixteen.
Continue shared acquisition and animated callback categories; do not restart
per-item conversion, installers, or tests. Prepared assets remain distinct from
completed playable imports.

## Direct-colour category and bulk prepared assets

Converter/installer revision 3 adds shared RGBA16 materials and prepares every
eligible uninstalled static model in one command:

```sh
python3 tools/v3_furniture_pipeline.py convert --assets-only \
  --output build/v3-furniture-all-static-prepared-02
```

The resulting 62 non-placeholder objects contain 211,136 bytes, 5,065 vertices,
and 3,720 triangles. The art receipt SHA-256 is
`0cf956288f7c323d5d0571fd9b8426fd93105a070d4bcb205a3fb1b06d2dffad`.
No individual item list or specialised graphics description is used. The shared
RGBA16 category includes Diver Dan `31D0`, retaining all 5,120 bytes, 107 vertices,
102 triangles, CI4 body materials, direct-colour helmet, and I4 reflection layer.
Its actual island acquisition remains required.

The supplied executable SHA-256 is
`e3166b15b810ff20397784fc83b2eb053db5d0c2a9e22ac2ead63a645881d150`.
Its complete 64-byte `fmtxtbl__5emu64` at `800AAFC0` has SHA-256
`7ae4019ff69d72ee09dd42b8b1c5a4c7a3a236d07aa238e2acdb93c97302fe30`.
The actual RGBA/16 entry is GX format 5, RGB5A3, not RGB565. The matching source
is `src/static/libforest/emu64/emu64.c` in the pinned donor checkout. Conversion
untile uses complete four-by-four blocks and native RGBA5551. Opaque and fully
transparent alpha are retained exactly; partial alpha fails instead of being
thresholded. Textures remain bounded to 2,048 bytes so switching back to CI4
cannot lose palettes in upper TMEM. Native 16-bit loads retain source scales,
wrapping, and shifts. No texture is resized or dropped.

Bulk discovery identifies sixteen entries using the same `iam_dummy` profile at
donor `.data:00092D6C`; fifteen have plausible item names. Both actual profile
tables select that placeholder. The converter now excludes this category by
its source pointer, not a maintained item-name/ID list. These entries retain
`asset_ready: false` and an explicit missing-artwork reason. An initial prepared
collection at `build/v3-furniture-all-static-prepared-01/` exposed the placeholders;
it is retained but not the current prepared collection. Unknown/dummy names also
remain excluded. A missing model in this English donor is not proof that the
item is unused in other editions.

The final collection retains actual missing dependencies:

| Dependency | Prepared objects |
| --- | ---: |
| No identified acquisition list | 29 |
| Tortimer holiday gifts | 12 |
| Harvest rewards | 6 |
| Island rewards | 5 |
| Gulliver rewards | 4 |
| Winter-camper rewards | 3 |
| Native identity/artwork correspondence | 2 |
| Train reward route | 1 |

Acquisition is not the only possible requirement: the sixteen diary display
models also need their actual diary gameplay. Prepared output is a separate
format and cannot pass installation. No prepared object is added to the offline
selection catalogue or counted as a completed playable import.

Forty-six focused pipeline/composition checks pass with the new direct-colour
artifact; the additional actual-executable format-table check and updated shared
placeholder-discovery check also pass. The shared complete-artwork and compiled-
material checks pass again against all 62 final prepared objects. Thus forty-seven
distinct focused checks pass across this batch. Independent comparisons cover
every source sample, vertex, triangle, model layer, material state, native load
format, palette mode, stride, texture scale, wrap, and shift. Partial-alpha and
incomplete-block rejection are covered without a new native scenario.

The current cartridge, build pin, 93 installed development options, saves, and
both served patchers remain unchanged. ABI-91 native results below are retained;
no old cartridge or unchanged emulator path is rerun. The newer converter source
does not relabel the ABI-91 build receipt as produced by revision 3. The scan still
has 58 supported and 184 review records; placeholder classification improves the
reason rather than hiding those records. Continue shared acquisition and animated
callback implementation using these prepared assets.

## Current shared intensity materials and resource reuse

The complete development cartridge is ABI 91:
`build/v3-furniture-intensity-runtime-01/animal-forest-v3-asset-loader.z64`.
The shared `intensity-materials` category discovers G logo `31E8` and bird bath
`3240`, retaining complete CI4/I4 textures, all opaque/translucent model layers,
reflection/water material state, and actual stock A acquisition. Their 6,880 bytes
contain all 202 vertices and 126 triangles. No item-specific model definition,
installer, runtime code, or native scenario is added. Automatic additions total
thirty-one; the offline composer contains 93 installed development options:
70 furniture, three shirts, and twenty villagers.

Converter revision 2 supports complete four-bit CI and intensity textures without
resizing. Pure I4 objects do not require a palette. Mixed lists select native
TLUT state at every actual format transition. Independent positive S/T scales,
four-bit shifts, wrapping, primitive/environment colours, and reviewed generated
reflection coordinates retain their source values. Unknown formats/state still
fail. The earlier CI4-only category remains available; `static-4bit` covers both.
The same category prepares miniature car `3094`: 7,104 bytes, 170 vertices,
and 98 triangles. Its acquisition is unresolved, so this prepared-only artifact
cannot be installed. Harvest mirror passes graphics discovery but still needs
the harvest acquisition adapter. No unsupported callback or acquisition is waived.

The installer reuses exactly the preceding automatic batch's terminal catalogue,
relocation, and shop resources. Complete hashes, DMA mappings, aligned contiguous
extents, zero padding, terminal boundary, resident boundary, every other DMA
resource, and all canonical profile extents are checked before reuse. Changed
receipts or live overlaps fail. The 64,496-byte prior tail starts at blob offset
3,284,400. Its retained prefix SHA-256 is
`0bb5766df6d034e6fca7acbed4efe8b7213db38808110f5ccac0df1663d429ac`.
New art precedes the regenerated owners; their fixed VROM identities and all
previous model VROMs remain unchanged. Reuse affects only the fresh output, not
input ROMs, previous builds, or saves. It prevents new redundant copies; it does
not compact older superseded data elsewhere in the retained prefix.

The catalogue has 506 furniture and 248 clothing rows. Conservative menu memory
remains 280,320 of 280,704 bytes. The import blob is 3,355,776 bytes, leaving
772,992 bytes before English choices. Growth is exactly the new 6,880 artwork
bytes, rather than another catalogue/shop copy. No runtime code or permanent
allocation grows. Saved format 2 remains; saves containing either new item must
not be loaded by older builds or V2. Forward ordinary cross-version reload is
not newly claimed. Both served patchers remain V2.

- ROM SHA-256: `ad194977b9083764c0efe8636614ba45d69b9370d6322514e2fd0b24aff2c1e3`.
- UPS SHA-256: `419588ce3dbf295f27ce96c8647f9042ed7111645fb84560f1d19f1aed89a2cd`.
- Build receipt SHA-256: `cbd63fe09ae8661bf4f9490e7f9ab3adcfb1e014c5d7932408322fce4203809b`.
- Art receipt SHA-256: `53659935e7ba271730ff1cb7b5cc5fe89ed290c9d40a3ab5af7975fa97c5e035`.
- Import blob SHA-256: `1c125a28cb24537db05e4f81e5703050d910a4542291586e5acbb71d1959383d`.
- Prepared car receipt SHA-256: `d9235377ce673ab0119b5cb025e5df3abc68d4f6cd06889b56b9ed3698966077`.

All forty-four focused pipeline/composition checks pass, with no skips. Material
tests independently decode compiled format, palette mode, stride, S/T scale,
wrapping, and shifts against source commands. Complete sample/vertex/triangle
checks also cover the prepared car. Palette-free I4, CI4 palette rejection,
mixed LUT transitions, changed tail data/receipts, and retained-profile overlap
are covered. Every previous complete model stays unchanged; tail reuse is
verified again from the new receipt. Existing sanitizer, stock/scoring,
official-text attribution, original-code, optional-subset, full, and exact V2
composition checks pass. All twenty current build-source hashes match the receipt.

The first silent native run passes 88 records with 68 assertions:
`build/v3-furniture-intensity-native-01/results.json`, SHA-256
`0153c9a523feb3316d5ce3d809f06e195e08c43a2149d0e0b4c7ad4dd51118cb`.
Both items represent distinct model-layer configurations. Complete native owner
loading/relocation, model DMA and bank tails, names/prices, footprint, catalogue
framing/fallbacks, relocated owners, stock, acquisition, ownership, restoration,
guards, and clean exit pass. No retry is needed. This is not GPU appearance,
full catalogue construction, ordinary gameplay, save/restart, or hardware proof.
No old cartridge is rerun.

The post-scan at `build/v3-furniture-intensity-post-scan-01/inventory.json` has
58 supported entries, all installed, and 184 review entries. These include
aliases and special imports, not a completion percentage. Continue shared
callback/acquisition categories and verified RGBA16 conversion; miniature car,
holiday gifts, island items, harvest items, and diaries retain their actual
unresolved dependencies.

## Square-furniture and double-bed batch

The complete development cartridge is ABI 90:
`build/v3-furniture-square-runtime-01/animal-forest-v3-asset-loader.z64`.
One `convert --category 2x2` batch discovers picnic table `32DC`, neutral corner
`333C`, red corner `3340`, and blue corner `3344`. The shared installer supplies
their complete models, profiles, names/prices, catalogue/scoring records, and
stock C/A/event/lottery routes respectively. No item-specific converter,
installer, gameplay code, or native scenario is added. The 15,568 bytes of
new artwork retain all 330 vertices and 182 triangles. Automatic additions
total twenty-nine; the offline composer has 91 installed development options:
68 furniture, three shirts, and twenty villagers.

Square collision category `5` and shape `5` remain distinct profile fields.
The existing four-cell reader supplies the same clockwise, upper-left-anchored
footprint in every rotation. The build rechecks the actual original/donor
footprint tables and the complete installed 1,020-byte reader at `80483000`,
SHA-256 `baf6957601fea4fc0829382bbc21604ade478479e9f0f6375c6e4d49e2f0317d`.
The three ring corners keep contact action `0x10` and the existing native
double-bed routines; they are not flattened into decorative furniture or
single beds. The complete checked room engine and expanded profile bindings
remain unchanged. No permanent allocation, saved structure, or native code
reservation grows.

The catalogue contains 504 furniture rows and retains 248 clothing rows.
Conservative menu memory is 280,320 of 280,704 bytes. The import blob is
3,348,896 bytes, leaving 779,872 bytes before English choices. Saved format 2
remains, but saves containing the new four items require this build or a
compatible profile superset; older builds and V2 must not load those saves.
Ordinary cross-version save/reload is not newly claimed. Neither served patcher
changes.

- ROM SHA-256: `91be4e2ccd1fc9bb3be77f16c11eff74a7b387582475deed575d3a316ea02277`.
- UPS SHA-256: `935651090a5a5b62ac99ddb37a9871951b8b3eaa9813bca90e3bfb06603bc0cd`.
- Build receipt SHA-256: `bdbeb14058d69b704de14865b5b2bb47048636345d34eccb76887265fcbffdfe`.
- Art receipt SHA-256: `bec4490afaca0b848c3d8fb4b4d5bd5e5a22a3773e1befb034ba2847f4291d74`.
- Import blob SHA-256: `02b36fbc1e93a002ca5c3f9db66f46c260aae3853b24d8a7eb9b291562b0eaa5`.

Thirty-eight focused pipeline/composition checks pass; one optional prepared-
assets check is not requested. New checks cover shared square/double-bed
discovery, intact donor scalars, unknown collision rejection, changed native
reader rejection, and the existing four-cell host fixture under address and
undefined-behaviour sanitizers. Complete texture/vertex/material conversion,
installed records, official text credits, retained native code, stock/scoring,
and optional-profile composition also pass.

The first silent native run passes 180 records with 158 assertions:
`build/v3-furniture-square-native-01/results.json`, SHA-256
`208149336a2def36a3647f23eb8aa1bc3450527ef25c89e93824c020c297ba9e`.
All four items are representatives because their stock categories differ.
Their complete model DMA, names/prices, four-cell footprints in all rotations,
catalogue framing/eligibility, stock, acquisition, ownership, restoration,
and guards pass. One double-bed representative exercises the actual native
head-direction and both side-position functions in every rotation, retaining
the wider side span and half-cell pillow offset. Inactive-bed rejection and
complete temporary-actor preservation also pass. No retry is needed.

The shared probe checks bed geometry once per changed contact category and
tests imported chair sounds for the new batch rather than every previous
chair. Full source audio/code checks remain in the build contract; earlier
passing native evidence remains recorded. No old candidate is rerun.
These checks do not establish ordinary bed entry/rolling/exit, complete room
appearance, catalogue construction, save/restart, or original-hardware play.

The post-scan has 55 supported entries, all installed, and 187 review entries.
It includes aliases and special imports and is not a completion percentage.
The next shared storage improvement is safe reuse of the regenerated
catalogue/relocation/shop tail (64,496 bytes in this build), preserving every
retained resource and previous output. Shared mixed CI4/I4 material handling
also remains: miniature car, G logo, and bird bath have I4 layers, while Diver
Dan additionally has RGBA16. Keep acquisition/callback dependencies explicit.

## Single-bed batch

The complete development cartridge is ABI 89:
`build/v3-furniture-bed-runtime-02/animal-forest-v3-asset-loader.z64`.
The shared `single-bed` category discovers and installs hammock `329C` and
weight bench `3358` without per-item model definitions, installers, gameplay
code, or native scenarios. Both retain stock C, their complete two-layer
models, two-cell footprints, donor profile scalars, official names, prices,
scoring, and preview framing. Total new art is 8,416 bytes, 196 vertices, and
108 triangles. The automatic pipeline has installed twenty-five additions;
the offline composer contains 87 development options: 64 furniture, three
shirts, and twenty villagers.

The category uses native contact action `08`, not a decorative approximation.
The checked native room engine already handles bed positioning, contact, entry,
and exit through the expanded profile table. The build verifies the complete
owner SHA-256 `ca540a6f48fa15fb8bfad4d36abf77bb3d318799732d965f278063207f64b74a`
and the four reviewed profile bindings at `809404D0/809404DC`,
`809407BC/809407C8`, `80940FA8/80940FB8`, and `809419D0/809419E0`, all addressing
`80470010`. No gameplay code or permanent memory is added. Native timing and
player animations remain unchanged.

Beach chair and harvest bed pass this category's model/dependency discovery
but are not installed. Their actual `ftr_listIsland` and `ftr_listHarvest`
acquisition routes still need shared adapters. Their presence in a supported
bed category does not waive those requirements or replace them with shop stock.

The catalogue contains 500 furniture rows and retains all 248 clothing rows.
Conservative menu memory is 280,320 of 280,704 reserved bytes. The import blob
is 3,268,832 bytes, leaving 859,936 bytes before English choices. Model-bank
allocations and saved format 2 are unchanged. Saves containing the new items
must not load in older cartridges or V2. Ordinary cross-version reload is not
newly claimed; both served patchers remain V2.

- ROM SHA-256: `e460ec11ba2eb2abebcc7aa15c8060728a5c986ddfb0c3f67078689c1a0d9dff`.
- UPS SHA-256: `7020d093e96bb510a36e46383bb715d7a8b4e5757f4eda476bfc65636a478232`.
- Build receipt SHA-256: `ad8cc4af55fae0da16115b5d251ff6a07372b84abcbb70bdf734278b3d2ffb16`.
- Art receipt SHA-256: `56d48e0b812717e4368abb986813d89223920e896ac9b4152fc96d52a8b9205a`.
- Import blob SHA-256: `0dbf4c68f6f5bc46c105887be5d268816cbcff90ecc26c1b5d3af832cc5d489b`.

Thirty-five focused pipeline/composition checks pass; the optional prepared-
assets check is not requested in this batch. They include complete conversion,
source credits, shared category discovery with acquisition rejection, changed
native-engine/table-binding rejection, complete installation, retained native
code, stock, scoring, and selected-profile composition.

The first silent native run passes 112 records with 93 assertions:
`build/v3-furniture-bed-native-01/results.json`, SHA-256
`6fc9749bd4f071050ee9f506c3347f13c88c7a4ead97f6c7dce110f00804fe9f`.
The shared selector chooses the larger weight-bench model to represent the
same stock, footprint, material layers, preview, sound, and bed category.
Actual head-direction (`80940304`), foot-side (`80940498`), and pillow-side
(`80940784`) functions pass all four rotations through the installed imported
profile. Inactive beds return no positions; the complete temporary actor stays
unchanged. Complete owner loading, model DMA, shared item/catalogue/stock
readers, acquisition, ownership, restoration, and guards also pass. No retry
is needed. The final recipe receipt refreshes a source comment and reproduces
the exact native-tested cartridge; no emulator rerun follows that comment edit.

These checks do not establish ordinary climbing onto/leaving a bed, full
catalogue construction, GPU appearance, save/restart, or original-hardware
behaviour. Continue shared callback, graphics, and acquisition categories;
use the same representative batch scenario rather than adding an item scenario.
The post-scan at `build/v3-furniture-bed-post-scan-01/inventory.json` has 51
supported entries, all installed, and 191 review entries. Those entries include
aliases and special imports; these counts are not a completion percentage.

## Material and catalogue-framing batch

The complete development cartridge is ABI 88:
`build/v3-furniture-material-preview-runtime-02/animal-forest-v3-asset-loader.z64`.
Shared discovery installs bug zapper `3234`, coffee machine `323C`, candy machine
`3254`, and steam roller `328C`, with 15,104 complete object bytes, 258 vertices,
and 153 triangles. The first two retain stock A, candy machine retains stock C,
and steam roller retains event acquisition and its two-cell footprint. All names
have official-source credits in the single provenance catalogue. Automatic
additions total twenty-three; the offline composer contains 85 installed
development options: 62 furniture, three shirts, and twenty villagers.

All four use the same unlit texture/primitive material command. Its two cycles
pass texture RGBA through, then multiply RGB by primitive colour while retaining
alpha. The symbolic native `gsDPSetCombineLERP` compiles to donor words
`FCFFFE60 FFFCF3F8`; complete compiled material/geometry checks pass. The coffee
machine's environment-lighting flag is also retained. There is no item-specific
graphics description or installer.

Catalogue framing is now source-indexed for all 62 installed furnishings. Byte
26 of the existing 32-byte item record stores the donor framing index plus one.
The complete 328-byte/41-entry table and its guards occupy
`80474A30..80474B9F`, with table data at `80474A40`. It fits after the placement
table and before accessory artwork, without increasing any permanent allocation.
The general native helper changes only model Y and scale after native
construction; clothing aliases keep their existing presentation. It replaces
the installed per-item Western, bike, and campfire overrides. The steam roller
and campfire both obtain the donor's mode 19 (`0.86`, `-3.0`) through records.
Disabled, absent, invalid-selector, and original-native cases retain their input.

The complete catalogue suffix is 3,408 bytes, and its 498 furniture rows retain
all 248 clothing rows. Conservative menu memory is 280,256 of 280,704 reserved
bytes. The import blob is 3,195,952 bytes, with 932,816 bytes before English
choices. Model-bank allocation and saved format 2 are unchanged. The required
saved profile is a superset of ABI 87. Saves using the four new items must not
be loaded in older builds or V2; ordinary cross-version reload is not newly
claimed. Both served patchers remain V2.

- ROM SHA-256: `5644a08760b63a396747adf2d5926340255667309152c7d9d0e4290263945319`.
- UPS SHA-256: `ed9c1c5b54e57d7414cc6b1f2b4dca39e9b5e284925222b999f54249e809c74e`.
- Build receipt SHA-256: `c8181c0ccb92625fb8d031317f8b83df5be29d9a09a5e5bddff64340105f5cfe`.
- Art receipt SHA-256: `e0e93177e8b011b6f73d571ce6e805317f4d13797adf03eefd2ee70ba4598a57`.
- Import blob SHA-256: `76032e58970f9e296b3d8054b09220662ef571a20339b345034ca9e8a172521a`.
- Preview table SHA-256: `fa6592f8af1ebb2ddb984e59b39649c36afeb85bdd4f9127dbcae26ba62a2a98`.
- Preview reservation SHA-256: `44d06f4df2fca8da04bb6c6a4ee48f131d9a2e1d22dce012027f077cb32b71bb`.

Thirty-four focused pipeline/composition checks pass against this candidate
before promoting its lock. They include the shared native combiner expression,
complete resource/geometry comparisons, all source-derived framing selectors,
guarded repeat-batch reuse, source credits, installed metadata, and selected/save
profile composition. The catalogue's host address/undefined-behaviour checks
cover the complete framing-table range and invalid boundaries. The fixture
preserves the distinct clothing-display stock route when enabling the full
catalogue wrapper. An initial build catches the old seating helper's reserved-
byte check; the corrected check recognises byte 26 as framing metadata while
retaining zero checks on bytes 27–31. That partial build has no promoted ROM.

The first silent native run passes 146 records with 124 assertions:
`build/v3-furniture-material-preview-native-01/results.json`, SHA-256
`3ae031b8643fbcd3a029b4387e2a7e5fde499f4b1157e4d687878e159a20b777`.
The shared representative selector covers all four new records because their
stock, footprint, preview, and lighting categories differ. Actual owner loads,
complete model DMA, source framing with every other preview field unchanged,
disabled/invalid/native framing fallbacks, names, prices, rotations, stock,
acquisition, ownership, restoration, and guards pass. The emulator exits cleanly;
no native retry is needed. This is not proof of full catalogue initialization,
GPU appearance, ordinary gameplay/save-restart, or original-hardware execution.

The post-scan in `build/v3-furniture-material-preview-post-scan-01/inventory.json`
has 49 supported entries, all installed, and 193 entries needing review. That
inventory includes aliases and unused records and is not a remaining-content
percentage. Continue shared behaviour/format/acquisition categories.

## Shared identity-indexed model and palette conversion

The converter handles the complete nine-entry flower selector through one
`indexed-static-model-palette` rule. No item list, separate graphics converter,
installer, runtime helper, or native test scenario is added. The source's fixed
actor identity selects two opaque models and a palette. Both models retain
their full material/geometry commands, and their segment-eight palette loads
become direct loads of the selected native palette.

The checked donor has `fNFL_dw` at `.text:2D0768`, 192 bytes, SHA-256
`612998bdab7cb941114e08d66db7100ded74894f8c1ccfdbdffe4bb9fbb44917`.
Its four code relocations bind the save/restore helpers and the complete
`fNFL_model_data` table at `.data:092BE0`, 108 bytes. The actual instructions
subtract runtime index 1246 and multiply by a twelve-byte row stride. All three
lifecycle callbacks are four-byte returns; the DMA slot is null. The verifier
checks those facts and dependencies, not merely function names. The donor room
renderer's `aMR_DrawRegistModel` uses the same current matrix and opaque0/opaque1
order; the special callback adds only the constant palette selection. Catalogue
rendering also retains that model order. Native execution of these new assets
is not yet claimed.

One command prepares all nine variants:

```sh
python3 tools/v3_furniture_pipeline.py convert --assets-only \
  --category indexed-static-model-palette \
  --output build/v3-furniture-indexed-palette-art-01
```

The output contains 19,152 object bytes, 555 vertices, and 288 triangles across
all three pansies, three cosmos, and three tulips (`3378..3398`). Each object has
its actual official donor name/source index and its selected palette. The
complete prepared receipt SHA-256 is
`6e173ac1c9c1889389779d93b63fd7ac6589d5644bd6d0afa9387dfe72711e83`;
the inventory SHA-256 is
`20df1500755bc29f67ffcb923f84a34244430e79a758bc718eb6e89b4e61f522`.
Individual object/resource hashes are in that receipt.

All nine remain **prepared, not installed**. The donor's
`ftr_listEventPresentChumon` contains these nine flowers, two tree models, and
weed model. `mCL_furniture_init` and `mMpswd_check_present_user` treat this category as
orderable/password-eligible, but that does not establish a working native initial
acquisition route. The N64 has no matching stock-list slot. Do not put the objects
in ordinary shop stock or claim acquisition is complete. Shared acquisition and
catalogue handling must cover the twelve source records together.

The actual initial acquisition comes from `mSC_trophy_item`, not a random shop
list. Its 244-byte donor function at `.text:07C31C` has SHA-256
`48321dd6e22de9f11751b89f9557c5be837f142f70b36bbe5cbd8ff933ea8234`.
The 56-byte `soncho_item_table$582` at `.data:010714` has SHA-256
`2bf4a655de09672b8c202cad690e6595cae1859656b5f379e9b9347822ea2fd9`.

| Donor event | Source reward rule |
| --- | --- |
| Founder's Day, index 1 | Weed model `3080` |
| Cherry Blossom Festival, index 7 | Pink tree model `307C` |
| Nature Day, index 9 | Tree model `3078` |
| Groundhog Day, index 13 | Uniform random runtime index `1246 + RANDOM(9)` |

The gift list at `.data:698630` is 26 bytes including its terminator, SHA-256
`07391eb07d67a5f92dfcd3300ac0586bc3908bb470e8ff2257cd7e39e1a8040f`.
`aES2_talk_before_give` checks pocket space; `aES2_talk_give` performs the normal
handover, inserts the actual item, and records the event trophy. Their complete
function hashes are respectively
`a3129746c1e60b877ecd74ae82f6861db8ef00509f0f15bfebe097324683bacc`
and `adb99cc52df75acb980d5f865c3c20f9778e223011b86d6f0b00d59aeec0d699`.
This requires the donor Tortimer event actor, English conversations, calendar
integration, selected-reward eligibility, and reviewed per-player trophy/calendar
persistence; the N64 actor/profile inventory has no corresponding Tortimer
implementation. Donor private-data offsets are not native saved fields. Implement
the shared event route without turning these rewards into ordinary stock, and
continue unrelated conversion categories while that larger dependency is open.

Thirty-two focused pipeline/composition checks pass with
`V3_FURNITURE_PREPARED_ART=build/v3-furniture-indexed-palette-art-01`. The reused
asset checks compare complete texels, vertices, triangles, materials, and palette
load targets. New checks cover every actual selector row, independent relocation
resolution, unknown/changed callback rejection, extra DMA effects, bad indices,
ambiguous palette bindings, and refusal to install prepared-only output. No
native emulator run is repeated: ABI 87, the ROM, import lock, saves, and both
served V2 patchers are unchanged. The 81 installed options do not include these
nine prepared objects.

Callback inspection also identifies useful next shared categories: fifteen
station models with one animated clock/skeleton implementation; eight building
models using palette-fade callbacks; tool, fan, and pinwheel display selectors;
and move-only sound callbacks. These are category candidates, not approved static
substitutions. In particular, station clock hands and animated parts must remain.

## Collision and placement categories

The collision/placement cartridge is ABI 87:
`build/v3-furniture-placement-runtime-01/animal-forest-v3-asset-loader.z64`.
The same importer installs grass model `30E8`, dirt model `30F0`, and boxing
mat `3348`, retaining all 2,768 object bytes, 44 vertices, 24 triangles, textures,
and the donor's `0010` no-collision flag. Official name credits are in the single
provenance catalogue. Automatic additions total nineteen; the offline composer
contains 81 installed options: 58 furniture, three shirts, and twenty villagers.

Inspection identifies five native readers still indexing the original 947-entry
placement-layer table with imported indices. This can read unrelated data and
lose surface behaviour. The shared fix preserves the original prefix and adds
source-derived rows for every installed furnishing and all three clothing display
aliases. Four imported surfaces (teacher's desk, orange box, chess table, and
ringside table) and five surface-placeable objects (garden gnome, cow skull,
lantern, Luigi trophy, and Mario trophy) now have explicit correct categories.
Other imported furniture has category zero. No item-specific runtime branch is
added. The complete native collision-registration routine is unchanged except
for its corrected table address, preserving its ordinary-room/shop distinction.

The 2,051-entry table and guards occupy `804741F0..80474A1F` in the unused
registry-to-artwork gap. The five actual HI/LO pairs are at
`8093825C/80938268`, `80943878/8094387C`, `80943978/8094397C`,
`80943A34/80943A40`, and `809462C8/809462D4`. Ten obsolete relocations are
removed. All other native owner bytes and accessory records/artwork remain.
There is no added executable code, resident allocation, or saved-format growth.

- ROM SHA-256: `004a1173c51cdea009c3a5e291067469675d40809002bf8fd41d99f28f671c1d`.
- UPS SHA-256: `df73ad1e2f7c8f010bd6016356a2d03b333d4295de4bb8d04c44cc286906c999`.
- Receipt SHA-256: `64805f9215d264303347fc40842f5fa6b15d2c549453f3e6c5b7ac654b1e85ec`.
- Import-resource SHA-256: `c328b130c6bb338de7582f24ceb6f3b741769427477e5c237a7a9b5c53665a58`.
- Placement-table SHA-256: `9f6d51793f058d2b8ebe8952a4369fd4a7b5d48eb19c9998333b885aac89ef01`.
- Native owner SHA-256: `ca540a6f48fa15fb8bfad4d36abf77bb3d318799732d965f278063207f64b74a`.
- Relocation SHA-256: `c97bc9e48c97a6830145218f5fcdcaa664a7611167b2f013bc93d75f4e493bc5`.

The blob contains 3,116,400 bytes, with 1,012,368 bytes remaining before English
choices. The catalogue has 494 furniture rows and 248 clothing rows; conservative
menu memory remains 280,384 of 280,704 reserved bytes. All 28 focused pipeline/
composition tests pass. They include every converted texel/vertex/triangle,
unknown interaction/placement rejection, source-derived table entries, all five
retargeted references, complete relocation comparisons at two load addresses,
unrelated-owner retention, repeat-batch reuse, and save-profile composition.
The first silent native run passes 125 records and 107 assertions, including
the complete placement table/guards, native owner loading/relocation, actual
no-collision registration for all three new objects, complete model DMA,
one-/two-cell rotated footprints, names, prices, stock, catalogue eligibility,
acquisition, ownership, restored state, and guards. The existing four sound
routes also pass. The emulator exits cleanly; no native setup retry is needed.
Results are in `build/v3-furniture-placement-native-01/results.json`, SHA-256
`5757a4b7580348303195455ae9c1b5b17e425a3bafa18cfc19c549673a7e733a`.

Ordinary room appearance, table use, walking across the collision-less objects,
and save/restart remain unverified. Saved format 2 is unchanged and the profile
extends ABI 86; no ordinary cross-version reload is newly claimed. Saves using
the three new objects must not be loaded in older builds or V2. Neither served
patcher changes.

## Shared seating category

The seating-category cartridge is ABI 86:
`build/v3-furniture-seats-runtime-02/animal-forest-v3-asset-loader.z64`.
The automatic pipeline adds lawn chair `324C` and teacher's chair `3288`
without an item definition, dedicated installer, or separate native scenario.
Their 7,872 bytes retain all 163 vertices and 81 triangles. This brings the
automatic additions to sixteen and the offline composer to 78 installed options
(55 furniture, three shirts, and twenty villagers).

The category extension also supplies the donor's correct soft-chair sounds for
lawn chair and hard-chair sounds for teacher's chair, lefty desk, and righty desk.
Byte 25 of each existing item record stores its source-derived category. All
installed furniture is populated from the actual donor table, including entries
with no action sound. No per-item runtime branch or separate audio import is
needed. Full sound programs, timing, complete instruments, envelopes, samples,
loops, and predictors match native audio; matching sound numbers alone are not
the verification. Original native items retain their original reader body.

The helper is 208 bytes at `80483D00`, before the fire vtables at `80483FC0`.
The installer verifies the existing fire code and empty intervening bytes;
linker limits also prevent shared item/tent/fire/behaviour overlap. The helper
uses a bounded 32-byte stack frame and no new permanent RAM or audio resources.
The catalogue contains 491 furniture rows and 248 clothing rows. The resource is
3,049,104 bytes, with 1,079,664 bytes remaining before the English-choice region.

- ROM SHA-256: `e6f334027c352039fededafe8672d7ff480b5234bad914646b4beeffad00d1ab`.
- UPS SHA-256: `b20ac5cf1f0bc6452a3ec38b76d15ab76d5e215e9112fd81d0c912af42ce6d40`.
- Receipt SHA-256: `b3f9a540d3426a87dad66cc7eec0732fef38283b72de4fc312b87fd75eee4b54`.
- Import-resource SHA-256: `2963fa39c0886ac784b3b6ed842e8dc6a8c88cef65c7b4909868a7debbeefff5`.
- Native result: `build/v3-furniture-seats-native-01/results.json`, SHA-256
  `33895a6070a9e352a7fc663f22c4fc5b1e45d84eaed84919005199c897733f4c`.

All 26 focused pipeline/composition checks pass. The shared sound implementation
passes address/undefined-behaviour sanitizers for original delegation, complete
import index bounds, modes, categories, metadata identity, and disabled records.
The first silent native run passes 88 records and 73 assertions: complete helper
loading, original fallbacks, both modes for all four imported sound routes,
disabled-profile rejection, invalid indices/modes, complete chair model DMA,
names, prices, stock, catalogue eligibility, acquisition, ownership, restoration,
and guards. No audio is played through the user's speakers/headphones.

The initial installer attempt stops at a missing shared compiler-entry mapping;
the mapping is added and the completed build passes. There is no native setup
retry. Ordinary sitting, audible playback, GPU appearance, transactions, and
save/restart are not established by these component checks. Saved format 2 is
unchanged; the new profile is a superset of ABI 85, but ordinary cross-version
reload is not newly tested. Saves containing the new chairs must not be loaded
in an older cartridge or V2. Neither served patcher changes.

## Initial automatic batch

Source revision `7149f9c` discovers and installs fourteen new items in one
batch, without an item-specific converter definition, stock/catalogue switch,
installer, or test scenario. The complete command is:

```sh
python3 tools/v3_furniture_pipeline.py import \
  --base-lock tests/fixtures/v3-furniture-pipeline-base.json \
  --output build/furniture-reproduction
```

The recorded run used the same pinned input through the current-build lock
before that lock was promoted. The final output is
`build/v3-auto-furniture-final-01/animal-forest-v3-asset-loader.z64`, ABI 85.
The one-command output in `build/v3-auto-furniture-02/cartridge/` has the same
complete ROM and patch hashes. The final rebuild adds reusable predecessor/art
locations to the receipt; it does not change any cartridge bytes or require
another native run. The folder name identifies this implementation batch,
not a finished V3 release.

- ROM SHA-256: `571e849108cf36983c7129a38d08bfc3b47dd71db5c4347cfe16b7425b1ed35c`.
- UPS SHA-256: `d9283d2908b779694ee584889d5f1559523159bbc3f8ae4512d368bf11d664f5`.
- Final build receipt SHA-256: `9f1df24e3e98f4972afc7c38720f91947afe6417082a79d13bdeee3959b80166`.
- Appended import resource: 2,976,720 bytes, ending at VROM `024D6BD0`,
  leaving 1,152,048 bytes before the reserved English-choice resource.
- Models: 50,064 bytes, 1,038 vertices, and 570 triangles, with complete textures
  and palettes. No donor artwork is truncated or replaced with a placeholder.
- Catalogue: 489 furniture rows and 248 clothing rows. The compiled suffix is
  3,424 bytes; conservative menu memory is 280,384 of 280,704 reserved bytes.
- No additional permanent RAM, model-bank allocation, or saved-format growth.

Imported records: track model `30EC`, train car model `30F4`, orange box `30F8`,
merge sign `31EC`, radiator `3248`, chess table `3250`, cement mixer `325C`,
jackhammer `3260`, potbelly stove `326C`, flip-top desk `3278`, Luigi trophy
`32C8`, Mario trophy `32CC`, boxing barricade `3338`, and ringside table `334C`.
Names have generated official-source entries in `translations/provenance.json`.

The offline composer resolves 76 installed development options. The concrete
subset `build/v3-optional-auto-furniture-01/` selects radiator, Mario trophy,
and ringside table without other new furniture, ROM SHA-256
`a973cee3a9e2f24adca32dd95e766c6a94e5d965da52805a8562aff558ab6453`.
Empty selection reproduces V2; all selection reproduces the complete cartridge.
Neither served patcher changes, and this is not a public-release handoff.

### Initial batch verification

Seven shared format/donor tests, five current-cartridge tests, and twelve
composition tests pass: **24 focused tests**. Checks cover every new texel,
vertex, and triangle, actual source relocations, retained material commands,
complete installed assets/profiles, official names, stock membership, scoring,
catalogue order, ROM checksums, full/empty/subset selection, and saved-profile
requirements. The shared catalogue reader passes address/undefined-behaviour
sanitizers across its bounded index/list/category/rotation cases.

The initial native attempt stops before emulation because `Xvfb` is not on PATH.
The one corrected retry explicitly uses the existing executable:

```sh
python3 tools/emulator_smoke.py \
  --rom build/v3-auto-furniture-final-01/animal-forest-v3-asset-loader.z64 \
  --output build/furniture-native-reproduction \
  --scenario tests/scenarios/v3_furniture_batch.json \
  --xvfb /home/discordian/Games/OpenRSC/headless/vendor/usr/bin/Xvfb \
  --seconds 180 --expansion-pak --no-initial-screenshot
```

`build/v3-auto-furniture-native-02/results.json` passes **148 records and 133
assertions**, SHA-256
`d97bcd43bf3a6665c0e63f1d87a3e9cb99b7500d5c394acb6887e40f286e44f7`.
The manifest chooses train car model, Luigi trophy, Mario trophy, flip-top desk,
jackhammer, and ringside table to cover A/B/C, event, lottery, one-/two-cell,
and model-layer categories. Actual owner loading/relocation, names, prices,
rotated footprints, complete upper-memory model DMA and untouched tails, bank
assignment, stock membership, catalogue eligibility/rejection, acquisition,
saved ownership, restored state, and guards pass. The emulator exits cleanly.
No existing save is used and no test FlashRAM write is requested.

Ordinary room appearance, GPU rendering of these new models, transactions,
interactions, and save/restart remain unverified. The preceding full profile is
a subset of this profile; the codec accepts equal/superset requirements, but
ordinary cross-version reload is not newly tested. Do not load saves using the
new items in an older build or V2.

## Category queue

The donor worksheet contains 242 canonical 3xxx entries. This converter supports
43 under its present complete category rules, all installed. The post-install
scan identifies no remaining supported,
uninstalled entries. This is **not** a whole-project completeness percentage.
The other 199 entries include already-installed special adapters and explicit
identity/unused cases as well as genuinely missing imports.

Continue through shared feature categories, not individual item queues:

1. Shared callback families: 102 uninstalled entries stop on custom callback
   tables. Classify the actual callback/dependency patterns and implement shared
   behaviour adapters; never discard callbacks to fit the static category.
2. The supported `0010` flag exposes further dependencies: sixteen diary display
   models need diary identity/gameplay/acquisition; weed model needs the shared
   `ftr_listEventPresentChumon` reward route. Neither is a completed static import.
3. Acquisition categories, special preview framing, and graphics variants:
   extend reusable adapters for the inventory's explicit reasons. Some items
   need combined features; clearing one reason need not make the item complete.

No more bespoke furniture installers or item-by-item metadata definitions are
the default development path. The legacy scripts remain as reproducibility
records; new supported items flow through the shared pipeline.
