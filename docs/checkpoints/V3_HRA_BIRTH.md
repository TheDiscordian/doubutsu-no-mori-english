# Native reward-category scoring prerequisite

## Completed implementation

The real native HRA evaluator supports 23 acquisition categories with complete
expanded stack counters/products. All nineteen original point weights remain;
the four appended values come from the actual donor. This prevents category 19
from overwriting the evaluator's output pointer. No new furniture is enabled.
See the [specification](../../specs/V3_HRA_BIRTH.md).

Artifact: `build/v3-hra-birth-01/animal-forest-v3-asset-loader.z64`.

- ROM SHA-256: `ad8c7be6e3ec0918b0bcbc3df5028dbccbca4c2d29370f6ef9d726f3d41eedef`.
- UPS SHA-256: `546ea13ae2c43ec54a463643d4b29820fad77f6ba709bd117c4a185a161e734f`.
- Report SHA-256: `f365e023c7cf2b94ef0dccc5cd61c982a34fb07128d872c3c2172995856c197c`.
- Blob SHA-256: `e0c9e531db3354d67b8572d318d39d0ec032776e2da9c32f87beaa3ce0326125`.

Runtime ABI 63; 64-MiB cartridge, Expansion Pak required. Blob storage is
1,425,776 bytes. HRA uses 31,392 on-demand bytes, a 96-byte increase; permanent
RAM stays unchanged. The evaluator's temporary stack grows by 32 bytes.
Saved format and selected profile are unchanged from the ABI-62 source. Ordinary
cross-build reload is unverified; keep backups. This is not a complete handoff.

## Executed checks

Three focused checks pass in 0.294 seconds. They verify complete stack layout,
all array endpoints, original/new point values, exactly 23 changed instruction
words, unchanged relocation records and unrelated data, relocation at three
destinations, all actual scheduler operands, CRCs, file bounds, and saved profile.

The initial `build/v3-hra-birth-native-01/` run passes **82 records**, including
60 explicit memory assertions and 14 native calls. Result SHA-256:
`7ecc654f02cb065b258a3c74118dae677d11cbb835c960233e11b78cd69166f1`.

Actual overlay loading/relocation and eleven complete evaluations pass:
empty baseline; individual categories 7, 8, 18, 19, 20, 21, and 22; a mixed
two-layer room with the last category in the far corner; null first layer; and
both layers absent. Every evaluation checks all 23 occurrence counters and all
23 weighted products. Totals retain the caller's accumulator and native wall/
floor baseline. Stack restoration, boundary guards, unchanged executable code,
complete saved import state, checkpoint restoration, and graceful shutdown pass.
No retry is needed. Audio is disabled, and no game save is written.

The fixture temporarily assigns categories to native test furniture records;
no actual reward item is awarded. Native scheduler sizing has focused cartridge
verification, while this run calls the native loader directly with the new
resource size. Ordinary scheduled HRA mail delivery, reward acquisition,
garden runtime/catalogue/composition, and hardware gameplay remain separate work.
The offline composer remains pinned to ABI 62 until the combined item update.
Both web patchers stay V2 pending user testing and explicit approval.
