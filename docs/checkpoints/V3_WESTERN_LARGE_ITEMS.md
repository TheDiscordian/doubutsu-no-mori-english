# Full-sized Western imports and expanded resident package

## Completed batch

Watering trough, covered wagon, and storefront have complete native models,
English names/prices, two-cell placement, catalogue framing, real stock routes,
scoring, and selected dependencies. This completes installation of all ten
Western theme furnishings. It does not complete ordinary gameplay validation
or the broader donor-import goal. Both served web patchers remain on V2.

The [specification](../../specs/V3_WESTERN_LARGE_ITEMS.md) records source identity,
translucent water, narrow-texture DMA, four rotations, catalogue-mode mapping,
and exact memory ownership. The first integration build succeeds with every
source, allocation, relocation, checksum, and patch-reconstruction check enabled.

The expanded checked package adds 8 KiB in unused Expansion Pak RAM. Its new
988-byte item reader code retains old public entry addresses through five
forwarders; save-code instructions remain intact. The actual three-shirt
roster supplies names/prices, without the old single-shirt compiler assumption.
Catalogue memory remains within the existing reservation, with 576 bytes spare.
Only 47,888 bytes remain in the current VROM import file; future storage expansion
must preserve the separate resource at `02400000`.

## Artifacts

Full integration: `build/v3-western-large-runtime-01/animal-forest-v3-asset-loader.z64`.

- ABI: 66; ROM remains 64 MiB, with Expansion Pak, RTC, and 128-KiB FlashRAM.
- ROM SHA-256: `5c51f80525a253e889a38b4ed4730df7e21b9a5e63a80917f0406b512faaebfe`.
- UPS SHA-256: `83bba82b8c267e66f488fcd0da69554b781b4a6decbd25ac7ec4386591ed8fb3`.
- Build report SHA-256: `ce78cdb3f8fe717679fd8b74bf92cadb11cec19fc0f6abbe8b6b26284946547e`.
- Art report: `build/v3-western-large-art-01/art.json`, SHA-256
  `aa29967549c87df4fa1d0a81536ac08ef0e1e78870db661e592dc3e68f50c3d1`.
- Item records: `build/v3-western-large-items-01/items.bin`, 96 bytes, SHA-256
  `2ded48047745baf16753611617f29ff552b38fc61fc97fde69640494cf6b442f`.
- Resident package: 69,632 bytes, SHA-256
  `9e6af018a618a4462d9f8363781182911b18eb08d93a4d65bc09e615c6aeda6f`.

The offline composer has 49 experimental entries: twenty villagers, twenty-six
furniture items, and three shirts. The generated subset selects watering trough,
covered wagon, and red aloha shirt with no unrelated dependencies:
`build/v3-optional-western-large-01/animal-forest-v3-asset-loader.z64`.

- Subset ROM SHA-256: `877c108f39c7014beb3661144549ea7ec56b59ef47bd2c4cba8a85c8b51dc20d`.
- UPS SHA-256: `9ad41d3d33e8f06520d047ceaf684462413a6e70055416331118e1e06510f824`.
- Build report SHA-256: `bb35309451aa40461ab80edc54b065dae92844833cce6ae0e0b6b4a4a3b87d50`.
- Profile SHA-256: `33eeba6a12e672a250ecda2d07c197db069d2eb72927c7f208b5f5253c74ec67`.

These are ignored local development artifacts, not release packages. No ROM,
patch, extracted image, disc resource, save, or emulator checkpoint is committed.

## Executed verification

Twenty-eight focused current-source/integration checks pass:

- Eleven complete new art/metadata checks plus one retained clothing-catalogue
  host check: 12.917 seconds. Complete texels, palettes, vertices, triangles,
  compiled material/load commands, distinct pitches, water state, source/native
  footprint tables, identity/stock/preview data, and actual C readers are checked.
- Five cartridge/startup checks: 0.502 seconds. Complete relocated metadata,
  retained resident assets, old entry dispatch, saved-code preservation, package
  CRC/header/cache ranges, scoring, menu bounds, and exact ROM changes pass.
- Eleven current-composer checks: 6.560 seconds. Individual selections, real
  dependencies, fixed IDs, all/empty equality, selected-only catalogue/HRA data,
  new two-cell records, and actual codec equal/superset/rejection paths pass.

ASan/UBSan cover changed C placement/name/price readers, all three roster
records, selected/disabled catalogue overrides, and expanded-package startup.
The generated full and subset cartridges both reconstruct through their UPS.

The initial silent native run is `build/v3-western-large-native-01/`:

- 88 records, 45 checked native calls, 32 passed memory assertions, no failed
  assertions, restored emulator checkpoint, and graceful shutdown.
- Cold boot confirms installed ABI 66 and the new package header.
- All three native names, classifications, and prices pass through existing
  callers into the relocated item code.
- All four rotations of every new item return the two-cell size and all four
  complete placement records, including inactive-cell coordinates.
- Cherry shirt and both aloha shirts retain their actual full names, prices,
  clothing classification, and cleared non-furniture placement result.
- Scratch guards, the expanded package guard, the translation guard, and the
  no-CPU-fault checks pass, including after checkpoint restoration.

Native results SHA-256:
`8b2c9261c2eab4456188f09a4c296bbca41e7123500a341b3d8a081b1d2b9214`.
No retry is needed. Audio output is disabled. No town save, inventory insertion,
Pak operation, or old build is tested. The earlier bank fixture is not repeated.
This run does not execute the new catalogue initializer or render the models.

## Compatibility and remaining work

Save format 2 and codec instructions are unchanged, but the three added profile
bits are new mandatory dependencies. The codec accepts equal/larger selections
and rejects missing dependencies without writes. Older/smaller builds reject
these profiles; imported saves must not be loaded in V2. Ordinary cross-profile
save/restart/reload is not established by these tests. Existing saves and builds
remain untouched.

Continue further donor families and their actual behaviours, reviewed import
storage expansion, mailbox banking/reward delivery, villager move-in/persistence,
and eventual offline browser composition. Keep ordinary acquisition/placement,
catalogue appearance, translucent-water rendering, and persistence pending.
Retain incomplete bank-DMA/teardown evidence for a later relevant combined
integration check rather than replaying its exhausted setup batch. V3 source
may be pushed on its branch; neither web patcher switches without user testing
and subsequent explicit approval.
