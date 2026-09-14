# V3 clothing ordinary-shop check

## Cartridge and fixture

The check uses ABI 39, `build/v3-clothing-shop-floor-01/animal-forest-v3-asset-loader.z64`,
SHA-256 `e112c96e3016d9fd4645565b2c3235d46ae6b123db10953b0c8a4a3cdd135059`.
No cartridge code changes in this batch.

`tools/v3_clothing_gameplay_fixture.py --shop-stock` creates an independently
packed format-2 copy of the preserved town. It replaces only shop goods index 2
(`2474` → `34BF`) and gives the disposable player 1,000 Bells. All pockets,
villagers, worn clothes, and other payload fields remain unchanged. Imported
ownership starts at zero. The fixture records every change to both banks and
checks the original source hash before and after staging. This is seeded stock,
not ordinary random stock generation or a seeded pocket acquisition.

The usable fixture is `build/v3-clothing-shop-fixture-02/test.flash`, SHA-256
`99d359406e64ea69acbcf85537d62329aa68c068ce3854bf49a618e8a728b636`.
Its separate emulator clock is 2026-09-10 at noon, matching the source's stock
day; the host clock is unchanged. The original town remains SHA-256
`d489736e39abc7eff1c5b5085bf52e679186f2882a0247339e11603799b80b60`.

## Results and limit

The focused fixture test passes. It independently checks both native payload
checksums and CRC binding, zero imported ownership, and the full retained
payload after restoring only the explicitly changed fields.

The initial arrival run fails a test assertion that read `C2E0..C35F` instead
of the clothing ownership range `C2D0..C34F`. The unexpected bytes are the intact
guard at `C350`, not game corruption. The source also proves to have zero Bells;
the corrected fixture explicitly provides purchase funds. The corrected
`build/v3-clothing-shop-arrival-02` run passes, reaches the town normally, and
retains the full `34BF` stock entry, 1,000-Bell wallet, original pockets, and zero
imported ownership. The town map and guards pass.

Frame-counted ordinary movement proceeds through the current-ROM checkpoints:
`v3-clothing-shop-route-01`, `v3-clothing-shop-approach-01`, and
`v3-clothing-shop-door-01`. The first door approach,
`v3-clothing-shop-enter-01`, and one corrected alignment attempt,
`v3-clothing-shop-aligned-entry-01`, both leave the player outside the shop.
The final position is approximately `(3508, 160, 1093)`, beside the building.
Private silent captures identify the navigation failure; the scenarios do not
assert successful entry. All observed guards, fault-pointer checks, and graceful
exits pass. No user save or physical audio output is involved.

**Ordinary purchase remains unverified.** There is no shop-construction,
payment, acquired-pocket, ownership-change, or sold-model gameplay claim from
these runs. The passing component sale/mannequin evidence remains recorded in
the [shop-floor checkpoint](V3_CLOTHING_SHOP_FLOOR.md); it is not relabelled as
an ordinary purchase. Stop navigation retries for this batch and continue
catalogue/home-display implementation. A later combined check can resume the
preserved current checkpoint, align south of the shop footprint before moving
east, and inspect the actual door position before approaching it.

Both patchers remain V2. V3 source stays on `v3/optional-imports`.
