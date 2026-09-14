# V3 clothing stock checkpoint

## Build

`build/v3-clothing-stock-01/animal-forest-v3-asset-loader.z64`, ABI 37.

- ROM SHA-256: `04978d2f62d8ce70c2d5ce4c8e359a622501251669a59e0fb80ef692396cfa4f`.
- UPS SHA-256: `d665e9266f8c2be10780d4f8d476c036ea22abb646c48de943e3f768f6713d30`.
- Resident prefix SHA-256: `ebb99cc172d6a57a6959059e28aab43cedf5cef0557772ef3c61cd166f737dc5`.

The [stock adapter](../../specs/V3_CLOTHING_STOCK.md) installs actual donor-backed
cherry shirt in the native A all-season list without changing original garments,
B/C seasons, town priorities, or saved formats. Main-code changes are limited
to one selection call and the resource descriptor end. The resource needs
160 additional temporary bytes, released by the unchanged native free path.

## Verification

Two focused tests pass: sanitized seasonal logic and current cartridge
composition. The host check covers all twelve months, first/new/seasonal/last
eligible choices, disabled selection, missing resources, original lists, guarded
output, null output, and a single RNG draw. Cartridge checks compare the actual
donor conversion, complete original lists and counts, retained main/asset code,
all other resources, unchanged indices, configuration CRC, and UPS reconstruction.

The first cartridge comparison did not account for the changed DMA directory
when a resource grows. The second did not account for the moved existing
diagnostic string. Both were assertion assumptions, not ROM defects: the final
check validates each DMA index/size and the exact single relocated reference,
then compares all retained code and data. Logs are
`build/v3-clothing-stock-tests-01.log` and
`build/v3-clothing-stock-cartridge-tests-03.log`. The unchanged host test passed
before the build completed; the cartridge test ran against the completed ROM.

The initial silent native run `build/v3-clothing-stock-native-01` passes all
65 records and exits normally. It calls the complete native stock selector
seven times, including selected A in different seasons, seasonal A/B/C entries,
disabled A, and reversed town rarity. Every result is checked against the
installed resource and every RNG state confirms exactly one draw. Six native
availability calls retain A's current town rarity. Acquiring the actual last
selected stock item preserves full `34BF` in its pocket and sets only its
independent clothing ownership bit. No replacement RNG or item return is used.

The fixture uses current 192/832/864-byte profile/state/runtime dimensions,
copies and restores the private record and affected globals, validates stack/
allocation/save/translation guards and the zero fault pointer, frees its small
buffer, and restores the emulator checkpoint. No user save or cartridge is
modified. This is native stock/acquisition execution, not an ordinary shop visit,
payment, mannequin render, or save/restart test.

## Remaining work

Connect shop mannequin counting/search/loading and the displayed garment
representation, catalogue rows/previews, and complete ordinary buy/sell.
Retain the unresolved ground-pickup and queued NPC evidence from their existing
checkpoints; do not repeat those setup attempts as part of this stock batch.
Punchy's defaults and all imported move-ins remain disabled. Both patchers
remain V2 until user testing and explicit approval.
