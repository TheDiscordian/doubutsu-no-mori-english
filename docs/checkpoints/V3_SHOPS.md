# V3 native shop-stock checkpoint

The [shop adapter](../../specs/V3_SHOPS.md) connects both selected static furniture
pilots to native ordinary-stock lists and the global category reader.
Cartridge: `build/v3-shops-01/animal-forest-v3-asset-loader.z64`.

- ROM SHA-256: `025da46e786105754a571953051b3e80a59059fb29fb5beeeb4de3b61a9d0765`.
- UPS SHA-256: `d24e0f0a24995004c5f2605f3c95677f641a9c83d9c6669a961bb28e953cbb5d`.
- Goods: 976 bytes, SHA-256 `7d3f0022ec538b40f4c3535d7cbec1350b91ddb566129b01942e0d9be18d09a0`.
- Helper: 68 bytes, SHA-256 `c9fab38393600408a866f825bc297bce3ea9ff0a71fd8a3ba641d99b588fc61d`.
- ABI 16; unchanged 48-KiB loaded prefix and save/profile format.

```sh
python3 tools/v3_asset_loader.py --shops --output build/v3-shops-01
python3 -m unittest discover -s tests -p test_v3_shops.py -v
```

Construction and all four focused tests pass. ASan/UBSan checks selected and
disabled categories, rotations, and original argument-preserving fallbacks.
Cartridge checks verify complete native goods-list preservation, each selected
subset's concrete pointer-alignment risk, complete retained stock functions,
helper/bridge/descriptors, composition, UPS reconstruction, and exact import-free
V2. Single-import tests concern two-byte list insertion, not exhaustive gameplay.

## Bounded native results

The initial combined attempt is `build/v3-shops-native-01`, using
`tests/scenarios/v3_shops.json`, silent private Xvfb, an Expansion Pak, a
disposable cartridge save, and a 180-second limit. It records 58 steps, 30 native
calls, and 23 passing assertions before one fixture comparison fails.

Completed prefix:

- Complete current resident code, installed category, goods descriptor, retained
  stock owners, and retained postal creator/pending loop match the cartridge.
- Twelve native membership calls cover both imports, all three rarity values,
  and two different town priority permutations.
- Four complete native stock-selector calls choose the added rows. Actual
  native RNG advances once each; an analytically chosen seed selects the last
  row without replacing the RNG or selector implementation.
- Global category checks cover both imports, rotations, unknown/disabled IDs,
  and five original categories.
- Actual native free-pocket acquisition retains both item IDs and records the
  correct imported ownership bits.
- The actual pending-order loop returns normally for two queued imports. The
  complete first delivered oil-drum letter matches its independent 164-byte
  reference, including captured name and attached item ID.

The first failure compares reader entry `80196C28` to pre-startup ROM words.
V2 startup intentionally replaces those words with its accent-aware reader.
The retry corrects that ownership model and runs only delivery, preserving the
stock-prefix evidence rather than replaying it.

`build/v3-shop-delivery-native-01`, using `tests/scenarios/v3_shop_delivery.json`,
records 20 steps, three native calls, and thirteen passing assertions. It again
confirms the first complete delivered letter, then stops before calling its
reader: the fixture still expects ordinary heap ownership. Static review of
`overlays/font_memory/loader.c` identifies the actual owner, `80450010`. The
current font configuration confirms a `6C60`-byte image and the hook row targets
linked `80C013C4`. The fixture now checks the fixed Expansion Pak owner and
records the relevant values, but is not rerun in this batch.

These are setup failures before reader execution, not established game crashes.
The incomplete check is not passed: the second letter, final pending-order and
whole-save comparison, reader output, final guards, and graceful-checkpoint
completion remain unverified. Cleanup restores the fixture's saved live state.
No FlashRAM write or ordinary shop confirmation/payment is tested. Neither
attempt establishes a full player lifecycle or original-hardware acceptance.
The initial attempt and one justified retry exhaust this batch's setup allowance;
unrelated implementation continues. Reuse unchanged collection/FlashRAM and
catalogue evidence rather than replaying those checks.

## Remaining work

Connect/review actual shop confirmation/payment and floor handling, then finish
scoring, ordinary placement/pickup/persistence, houses/move-in, selection, and
Controller Pak profile transport. Resume only the unresolved delivery tail in
a later relevant combined check. Neither furniture nor villager pilots are
complete, and the broader English-donor import goal remains active.

Development source is pushed only to `v3/optional-imports`. Both web patchers,
the stable V2 cartridge, user saves, and released trailer remain unchanged.
