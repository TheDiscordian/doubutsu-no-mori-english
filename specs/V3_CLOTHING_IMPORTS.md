# Complete clothing importing

## Source category

`v3_furniture_pipeline.py convert --representation clothing --assets-only`
prepares every distinct donor clothing appearance together. `--base-lock` binds
the retained resources to the current cartridge. `v3_clothing.py` supplies one
CI4/palette converter, without garment-specific names or texture hashes in code.
Full original-ROM, GAFE01-r0 archive, REL, and symbol hashes remain mandatory.

The converter compares all 1,024 decoded pixels of each of the 255 named donor
garments against all 256 native garment images. Palette-index differences do
not create false new items. Complete palettes, including unused entries, remain
in prepared resources. Partial alpha rejects. The result is 247 native artwork
matches, seven additive appearances, and one donor variant. The worksheet's
existing `24E3` correspondence identifies the changed puzzling shirt; its native
artwork stays available rather than being silently replaced.

`build/v3-clothing-category-work-01/prepared-02/` contains all eight distinct
appearances in 4,352 bytes. Resource SHA-256:
`89b3e8f1899446baf1a39f9420ab776fd6916d2d4201110eff6b207a696a7fb4`.
The three installed resources match the current ABI-306 cartridge. Prepared
content is not evidence of installed gameplay or selectable new content.

| Donor ID | Official name | State | Source stock |
| --- | --- | --- | --- |
| `241A` | red aloha shirt | Installed resource | Exclusive outfit |
| `241B` | blue aloha shirt | Installed resource | Exclusive outfit |
| `244B` | fish bone shirt | Runtime pending | C, all seasons |
| `2469` | fortune shirt | Runtime pending | B, all seasons |
| `24B6` | houndstooth tee | Runtime pending | B, all seasons |
| `24BF` | cherry shirt | Installed resource | A, all seasons |
| `24CB` | G logo shirt | Runtime pending | A, summer |
| `24E3` | puzzling shirt | Additive donor variant, runtime pending | A, all seasons |

Names, price words, complete stock lists, season partitions, and catalogue
positions come from the actual donor. Existing credits and five added name
credits use the single `translations/provenance.json` catalogue. No new English
wording is authored for these items.

Both complete room-conversion functions bind clothing `2400..24FE` to
mannequins `17AC..1BA7`, including four rotations and inverse pickup. A mannequin
inherits its carried garment's identity and name. For example, source `18D8`
is the fish bone shirt's display even though the external furniture worksheet
calls it a tomato shirt. The ordinary furniture scan classifies these forms as
`parent-representation` and directs them to the clothing path. Custom-design
mannequins starting at `1BA8` are not ordinary garments and remain separate
unfinished importing work.

## Connected runtime work

Keep this as one implementation batch for all five remaining appearances. Do
not add individual garment installers or new native scenarios for each shirt.

- Extend the fixed clothing/display registry without reassigning existing
  identities. Optional inclusion must not overwrite any native shirt.
- Replace the three-item dispatch in `clothing_roster.c` with checked category
  records. Its existing bridges preserve all live caller-saved registers;
  retain that contract for native DMA, player/NPC wearing, and default outfits.
  The old name/price readers already consume the returned metadata pointer.
- The prefix reservation `80462820..804628FF` fits only seven 32-byte records,
  not eight. Do not overwrite the melody table at `80462900`. The current
  1,076-byte roster begins at `80473A00`; town eligibility starts at `80473E40`.
  The linker's broader `80474000` limit is not free space. Allocate/rebind the
  complete table/helper once with the existing packet/reservation machinery.
- Install all five full texture/palette resources through the existing checked
  item-data allocation. The current build has 23,248 bytes of reusable padding;
  preserve the externally stored catalogue/shop owners and their DMA mappings.
- Reuse the complete native mannequin profile and callback. Add canonical
  sparse display profiles and parent metadata, then let the furniture loader
  identify clothing through its parent relationship instead of its three
  special profile addresses. The shared alias index has 11 of 58 rows occupied.
  Placement, pickup, names, pricing, and footprint readers already share it.
- Extend catalogue and source HRA/feng-shui rows in the same installation.
  Preserve all 245 original catalogue garments and the three installed additions.
  Reuse the shared scoring-category mapping and resource-tail writer.
- Extend the shared clothing stock reader for actual A/B/C source membership
  and season partitions. Preserve original rows, weights, selected-profile
  rejection, and the exclusive aloha outfits. The G logo shirt is summer-only.
- Extend browser/offline composition to use each reported metadata address,
  not `2820 + slot*32`, and include every garment/display pair together.
  Keep the translation-only output unchanged. Do not assume a current build
  installs every identity merely because the source registry reserves it.
- Reuse the existing 256-bit clothing and display-profile spaces. Inspect the
  actual current format-nine readers rather than introducing another save
  format merely for extra records. A larger selected profile still requires
  compatibility warnings and rejection by builds missing those resources.

## Evidence and limits

Five focused `tests.test_v3_clothing_batch` checks cover the complete category,
independent donor block addressing for all pixels, all palette entries,
preservation of the three current resources and metadata, stock seasons,
mannequin routing, and corrupted source/prepared-content rejection. These are
conversion and identity checks, not new emulator or hardware results.

The current cartridge remains ABI 306. No new garments are enabled yet, no save
format changes are made by preparation, and neither stable V2-14 patcher changes.
The creature constructor timeout and sound-scheduler disconnect remain
unclassified; their exhausted fixtures are not repeated by this work.
