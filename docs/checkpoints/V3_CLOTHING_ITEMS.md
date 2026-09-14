# V3 clothing item checkpoint

## Completed component

The selected cherry shirt has its complete English name, category 12, and
380-Bell donor price through the actual shared native entries. Invalid or
unselected shirts do not acquire another item's identity. The furniture-only
footprint query retains native garment rejection and clears all four cells.
Original clothes and both imported furniture pilots remain intact.

Build: `build/v3-clothing-items-03/animal-forest-v3-asset-loader.z64`, ABI 32.

- ROM SHA-256: `54e4a88d853f25c073e3d0c4f13aa86c970b8bb90ad39865da248935450041a4`.
- UPS SHA-256: `baa41ac5ed0def3d0ab99fe6ed221f56934b427da933f75674aea5c2b09a709f`.
- Resident prefix SHA-256: `515896b7defdc3dd7fdf5bbb71c49984dadcac9ce20f23ef60e0840792d5a968`.

The combined save/item code is 2,972 bytes, padded to 2,976, at `8046D000`.
Its ROM resource ends at `03F0FFA0`, below villager textures. The existing
2,008 save-code bytes remain identical. Five old item entries dispatch through
checked jumps; the rest of the loaded prefix, artwork, and save state remains
unchanged apart from ABI and the separate-code descriptor. No heap, saved field,
or DMA directory grows. Saves still use clothing format 2, incompatible with
older format-1 V3 builds and V2.

## Verification

The current sanitized host test and complete cartridge/reconstruction test pass.
The unflagged furniture-source host check also passes; no old cartridge is run.
The initial native attempt passes name/category/price/size, then reveals an
incorrect fixture assumption: `mRmTp_GetFurnitureData` returns 3 for clothes,
not a one-tile furniture footprint. Source inspection confirms that behaviour.
The unnecessary native-garment special call is removed, and host/native
expectations now preserve the actual non-furniture contract.

The corrected current native run, `build/v3-clothing-items-native-02`, passes
all 60 records and exits normally. It covers the installed shared entries,
complete unaligned English names, category/price/size, cleared non-furniture
footprints, short/oversized/adjacent-ID rejection, profile removal, both rotated
furniture names/categories/prices, and the original `24BF` garment's different
full name. Profile bytes are restored; complete prefix and separately loaded
code, scratch/stack guards, translation guard, and zero fault pointer pass.
The checkpoint is restored. No acquisition or device writes occur.

## Remaining work

Connect normal acquisition/ownership, menus/icons, clothing actions, buy/sell,
mannequins, and ordinary gameplay/persistence. The unresolved NPC queued/second-
owner evidence remains in its checkpoint. Punchy's outfit/move-in defaults are
disabled, and V3 is not enabled on either web patcher.
