# V3 clothing resource checkpoint

## Current scope

The [clothing specification](../../specs/V3_CLOTHING.md) describes the additive
cherry-shirt resource and shared reader. The new item reservation is `34BF`,
render index `10BF`, VROM `03F0F000`. NPC clothing streaming, wearing/items,
acquisition, mannequins, and a reviewed clothing save registry remain work.
Punchy's defaults and import eligibility remain disabled.

## Artifacts

`build/v3-clothing-resources-01/animal-forest-v3-asset-loader.z64` uses ABI 28.

- ROM SHA-256: `48140ace682f65c7bc9961dc0cf786075222e021e4d8cbba67af24170a4bce3b`.
- UPS SHA-256: `011661f01fcbb2bbed05d655f8f9d843986ebe666626c9c9ecb4da36bece119f`.
- Resident prefix SHA-256: `3db454a21b4c4ff963ac679a27439e9eb89a2a9ba9face0ea88ee1fa4d8a2385`.
- Complete 544-byte garment SHA-256: `4144452f514d67a012abc5c81209099ef36b246b021028b5ea5b3f65eac37bce`.

The existing V3 DMA file grows to `F220` bytes; only its first `C000` bytes
are resident. The garment occupies a checked ROM-only tail after both furniture
models. The DMA row count and ordinary heap sizes remain unchanged.
Combined asset code is 2,380 bytes. Source lookup is at `804608F0`; shared
loader is at `80460994`, with a 32-byte frame, matching the native reader's
frame size. No original garment is modified.

## Verification

Four focused tests pass in 1.137 seconds. They cover all 256 native source
pairs, distinct imported source/index, malformed/disabled metadata, complete
bounded transfers, null/unknown arguments, DMA failure, source/table/configuration
checks, unchanged existing resources/profile, UPS reconstruction, and the
unchanged import-free V2 composition.

The initial native run `build/v3-clothing-native-01` completes all thirty-four
recorded steps and exits normally. It calls the actual patched `800B1EDC` entry,
first for native `BF`, then imported `10BF`; complete 512/32-byte outputs match
their respective cartridge resources. The two garments remain distinct.
Null, unknown, and disabled requests leave the outputs intact. Heap/stack/output
guards pass, metadata is restored, the complete resident prefix matches, and
the fault pointer remains zero. The native allocation is freed and the original
emulator checkpoint restored. No game-save writes or ordinary clothing/item
gameplay are claimed.

The previous Cheri gameplay evidence remains retained for unchanged NPC
construction/drawing/conversation paths. The completed follow-on chat is
recorded in [the Cheri checkpoint](V3_CHERI_GAMEPLAY.md); no replay is queued.
V3 development is stored on GitHub, while both web patchers remain V2.
