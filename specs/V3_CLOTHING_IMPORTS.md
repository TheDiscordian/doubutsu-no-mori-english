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
The prepared resources are installed in the current ABI-307 cartridge. Preparation
and installation remain separate operations; actual evidence is recorded below.

| Donor ID | Official name | State | Source stock |
| --- | --- | --- | --- |
| `241A` | red aloha shirt | Installed | Exclusive outfit |
| `241B` | blue aloha shirt | Installed | Exclusive outfit |
| `244B` | fish bone shirt | Installed | C, all seasons |
| `2469` | fortune shirt | Installed | B, all seasons |
| `24B6` | houndstooth tee | Installed | B, all seasons |
| `24BF` | cherry shirt | Installed | A, all seasons |
| `24CB` | G logo shirt | Installed | A, summer |
| `24E3` | puzzling shirt | Installed additive donor variant | A, all seasons |

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

## Connected runtime

Install the complete prepared category through the shared pipeline:

```sh
python3 tools/v3_furniture_pipeline.py import --representation clothing \
  --base-lock build/v3-creature-insects-work-01/connected-04/build-lock.json \
  --reuse-assets build/v3-clothing-category-work-01/prepared-02 \
  --output build/v3-clothing-category-work-01/connected-09
```

The output directory must be fresh. The current built proposal is that
`connected-09/build-lock.json`; it does not change the main lock or deployments.

- Append-only registry identities retain the original three garments and add the
  other five without replacing native shirts. Resource addresses come from the
  checked common allocator, not checkbox order.
- One 4-KiB packet at `8066E000..8066EFFF` holds the complete eight-record reader,
  metadata, independent identity tuples, and A/B/C stock descriptors. A final
  16-byte guard follows the code/data. Existing register-preserving bridges
  redirect to it. Names/prices, native texture/palette DMA, player/NPC wearing,
  and default outfits consume the same returned records.
- The prefix `80462820..804628FF` and old roster `80473A00..80473E33` are not
  enlarged into neighbouring melody or town-eligibility data. The eight records
  live at `8066E800..8066E8FF`.
- Complete textures/palettes use the existing import-data allocation. The shared
  planner preserves external catalogue/shop owners and physical-only resources,
  including zero-filled bytes inside their reservations. Remaining reusable
  item-data padding is 16,432 bytes.
- Canonical sparse mannequin profiles reuse the complete native profile and
  callback. The loader follows the parent relationship, and recompilation rebinds
  both public reader entries and the actual room bank-constructor call.
  Shared forward/inverse aliases handle placement, pickup, names, prices, and
  footprints. The complete index has 16 of 58 rows occupied.
- All 245 original catalogue garments and three existing additions are retained;
  five appended entries bring the clothing catalogue to 253 rows. Official
  HRA/feng-shui metadata uses the shared category mapping. The actual menu pool
  grows by 128 bytes, with complete-image/relocation bounds checked.
- Original A/B/C stock and season groups remain intact. Added records use their
  actual donor list and season; disabled profiles do not enter the draw.
  The G logo shirt is summer-only. Exclusive aloha outfits are not inserted into
  ordinary shop lists. Every selection uses one native random draw.
- Browser/offline composers use reported metadata/profile addresses and enable
  garment/mannequin pairs together. The clothing packet checksum is updated
  before the containing equipment checksum. Empty/default composition produces
  the unchanged V2-14 translation-only build.
- Twelve startup descriptors share one transfer/checksum/cache loop in the
  existing 688-byte reservation; code and descriptors occupy 504 bytes.
  Physical-ROM insect transfers and native-DMA packets retain their complete
  ranges and ordering. Initialization does not run after a failed packet.
- Existing 256-bit clothing/display profiles and format-nine saves remain.
  Added garments require their matching selected resources. Builds or profiles
  missing those bits reject the save; forward loading with the required imports
  is supported by the retained codec. Preserve backups. Native save/reload of
  this clothing batch is not claimed.

## Evidence and limits

Current build: ABI 307, ROM SHA-256
`76381bfe94508f6c521c5fff56246943f45914ba6d06a03438a19b84acb6643a`.
UPS SHA-256:
`b08c39f462b1e812bcc030bda14ad428302ef20272558276ff7af4f40f2e3327`.

Three `tests.test_v3_clothing_install` checks pass on this cartridge:

- Complete resources, stock seasons, canonical profiles, hooks, saved-layout
  preservation, actual startup descriptors/checksums, menu bounds, and UPS
  reconstruction.
- Sanitized actual C readers for all eight garments, wearing/fallbacks, mannequin
  DMA in every rotation, all three stock groups and twelve months under empty,
  individual, and complete selections; twelve-packet startup and all failed
  transfer/checksum positions.
- Five browser/offline profiles agree: empty, select all, all clothing, summer
  shirt alone, and donor puzzling-shirt variant alone. An actual offline output
  at `build/v3-clothing-category-work-01/selected-summer-01/` also succeeds.

The existing `v3_clothing_resources.json` scenario uses the generalized shared
probe, not a new per-garment scenario. One silent current-ROM run at
`build/v3-clothing-category-work-01/native-01/` passes 80 records and 50
assertions: complete startup packet, actual native DMA of all eight imported
textures/palettes plus an original garment, disabled-import no-write behaviour,
unchanged saved state, guard preservation, checkpoint restoration, and no fault.
No existing save is used or modified. This is reader/startup execution, not a
claim of ordinary shop purchases, worn GPU appearance, room interaction,
save/reload, or original-hardware acceptance.

The five complete source-conversion checks remain retained evidence, not a new
historical-build replay. The creature constructor timeout and sound-scheduler
disconnect remain unresolved; their exhausted fixtures are not repeated.
Neither stable V2-14 deployment changes.
