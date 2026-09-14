# V3 town-selection checkpoint

The [selection specification](../../specs/V3_VILLAGER_SELECTION.md) records the
four complete native procedures, independent transient arrays, preserved saved
history, and fixed-ID subset mapping. Native default initialization and six
personality rules are retained. Import-eligibility flags stay off while the
remaining ordinary-gameplay integration is unfinished.

Current development cartridge:
`build/v3-villager-selection-01/animal-forest-v3-asset-loader.z64`.

- ROM SHA-256: `ef6b82232e0d8a134e46f04cd176ec8fc47d25c407ee442776b975f1a5e33f32`.
- UPS SHA-256: `8e9d97c6bf4e4fb3c1b81c5f70208711cccf31a2d634fc2a98c03405719fac36`.
- Resident prefix SHA-256: `c00a486956e75ea2d3a05806169194dacaf9a11e6eca64da0f0d1361a36d1561`.
- Selection code SHA-256: `4b7205dcfb2aac9354d26d2768ec18fb541a18127ea6f7805e41868920400104`.

The code is 1,476 bytes, within `80463400..80463FFF`. Its largest individual
compiled stack frame is 64 bytes. Candidate and shuffle state occupy explicit
unused resident ranges; ordinary heap and saved layouts do not grow.

## Focused checks

All six host/cartridge tests pass in 1.230 seconds. They cover native/imported
unseen counts, missing outfit/metadata/role rejection, already-resident and seen
exclusion, saved-history reset, invalid randomness, exact native shuffle sizes,
fixed imported identity mapping, unique starter personalities, unused population
slots, source-function guards, unchanged surrounding resources, startup CRC/ABI,
patch reconstruction, and exact import-free V2 output.

The first native check, `build/v3-villager-selection-native-01`, passes all four
selection entries. Actual native random permutations agree with an independent
model of the pinned `fqrand` implementation. Complete six-villager populations
match expected IDs with imports disabled and with Cheri's temporary test flag
enabled. The latter population includes `E0EA`, not a compacted shuffle index.
Each population contains all six personalities. Unseen/disabled/resident
exclusion, appearance-history reset, unused slots, memory guards, prefix
restoration, and fixture cleanup pass. Temporary live records, history, RNG,
eligibility, and transient arrays are restored; no game save is written.

## Combined house check

The same current-cartridge run then executes the prepared house fixture. The
complete appended foreground DMA and all 498 sparse pointer slots pass. Native
house-table initialization returns, but its expected position check fails:
the fixture expects tile centres, while the verified native
`mFI_UtNum2PosXZInBk` returns tile origins. The expected coordinates are corrected
from `(2140, 0, 2820)` to `(2120, 0, 2800)`; no cartridge code changes.

The single corrected retry, `build/v3-villager-selection-house-tail-01`, runs
only the house portion on this cartridge. The passing selection prefix is not
replayed. All 42 recorded steps pass: complete native house initialization,
foreground DMA and pointer sorting, imported main/secondary layer selection and
transfer, restored globals, guards, checkpoint restoration, and clean shutdown.
An ordinary house visit and complete scene-foreground allocation remain distinct
from these focused calls.

## Remaining implementation

Finish the remaining native ID/data-driven readers, actual house visits and
conversations, imported villager/profile persistence, and Controller Pak
transport before enabling ordinary imported move-ins. Cheri's complete default
and house dependencies are installed; Punchy's actual shirt and animated speed
bag remain work. Complete the furniture acquisition/rotation/persistence route,
broader donor content, optional browser composition, and eventual hardware
playtest handoff. GitHub development continues; both V2 patchers stay unchanged.
