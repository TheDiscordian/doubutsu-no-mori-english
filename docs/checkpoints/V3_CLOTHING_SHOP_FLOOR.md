# V3 clothing shop-floor checkpoint

## Build

`build/v3-clothing-shop-floor-01/animal-forest-v3-asset-loader.z64`, ABI 39.

- ROM SHA-256: `e112c96e3016d9fd4645565b2c3235d46ae6b123db10953b0c8a4a3cdd135059`.
- UPS SHA-256: `b88ff8007e4cf9c25410cf207d573fa5be71fc07fbe370ceea9d5e8fa1b5a182`.
- Resident prefix SHA-256: `9eed05834d608c5d84664294a8831a91fd611cd7171d230640140ef57a62ed5f`.
- Shop-floor helper SHA-256: `7b9057c14d7ce270de786aa3ff177a22823161a09bcede4ff41901055ffcad81`.
- Complete shop-floor owner SHA-256: `57a0ed582d39c0eb0d4d453bff3a63fdf09de1f694dabbd3c484ea2715015bcb`.

The [adapter](../../specs/V3_CLOTHING_SHOP_FLOOR.md) adds three clothing branches
to the existing furniture floor integration. Its 388 additional bytes fit
inside the original reservation; existing public entries and the original
340-byte helper remain identical. There is no allocation or saved-format change.
Same-profile ABI-38 saves retain their representation. Format-2 saves require
a compatible clothing-enabled V3 build, not older format-1 V3 or V2.

## Verification

The first build completes successfully. The focused cartridge test passes in
`build/v3-clothing-shop-floor-tests-01.log`: all three single-word hooks and
retained delay instructions, complete existing furniture helper retention,
full owner comparison after restoring the three branches, complete helper
installation, all other resource identities/sizes/contents, unchanged clothing
profile/artwork/readers, startup CRC, and UPS reconstruction.

The initial silent native run `build/v3-clothing-shop-floor-native-01` passes
all 61 records, restores its checkpoint, and exits normally. It executes actual
relocation of both the shop-floor and mannequin owners. Twelve complete reserve
and selection calls cover selected clothing, index-zero original clothing,
sold marker, unknown clothing, retained imported furniture, and disabled clothing.
A real one-block field supplies native bounds/index/grid access.

The complete native sale function runs for `34BF`, with its real 380-Bell price.
The native goods update changes `34BF,24BF` to `1F35,24BF`. The actual mannequin
callback changes only the matching slot's naked flag, retaining its full item
identity. The native foreground setter clears the purchased tile to `FFFF`.
Comparing the complete saved payload confirms that only the fixture's shop sales
total changes, from 100 to 480. This is shop revenue, not a claim that a player's
wallet was debited or that ordinary confirmation was tested.

The test explicitly models post-constructor shop/mannequin actors. Native
construction, graphics submission, ordinary controls/payment, and save/restart
are not executed here. The loaded owners, complete resident prefix, allocation/
stack/save/translation guards, and zero fault pointer pass. Saved payload and
all affected globals are restored; the fixture allocation is freed. No physical
audio or user-save modification occurs.

## Next work

The [bounded ordinary-shop check](V3_CLOTHING_SHOP_GAMEPLAY.md) preserves imported
stock through cold boot, with unchanged pockets and zero imported ownership.
Purchase remains unverified after two door approaches leave the player outside;
all observed guards and fault checks pass. Retain those checkpoints and stop
navigation retries for this batch. Continue the remaining clothing catalogue/
home-display representation and mail/gift consumers.

Punchy's defaults and imported move-ins stay disabled. Full clothing display,
villager lifecycle, remaining imports, browser selections, and profile transport
remain on the V3 queue. Both patchers stay V2 until user testing and approval.
