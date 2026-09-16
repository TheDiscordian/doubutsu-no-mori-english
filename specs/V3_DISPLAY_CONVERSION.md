# V3 pocket and mannequin conversion

## Installed contract

Selected imported garments convert between pocket and room representations
through generated [shared alias records](V3_FURNITURE_PIPELINE.md#native-alias-records).
The installed pairs are `341A ↔ 3868`, `341B ↔ 386C`, and `34BF ↔ 3AFC`.
All four room orientations return the same parent garment. Both paths require
the complete display-profile and clothing selection checks. Original clothes,
fish, insects, umbrellas, furniture, invalid items, and missing imports use the
original native functions. Prepared tool/fan/pinwheel models are not yet enabled.

Native forward conversion is `800BEFCC..800BF10B`; inverse conversion is
`800BF10C..800BF22F`. Both complete bodies and their exact prologues are checked
before installation. Each entry redirects through a new resident wrapper and
a sixteen-byte bridge that executes the displaced instructions before rejoining
the original body. Existing callers retain their argument/return conventions,
including sixteen-bit item truncation and native caller stack slots.

The 260-byte conversion code occupies `80466270..80466373`, within reservation
`80466270..8046637F`, before the roster helper. Bridges occupy
`804665E0..804665FF`. The alias/metadata helper at `80466C00` supplies
canonicalization; the immutable forward index is at `804A0010`. The build verifies
complete prior code, hooks, unused tails, and metadata before replacement.
No heap, saved field, selected-profile bit, or DMA slot grows. ABI 96 retains
ABI 95's complete saved format/profile; same-profile compatibility is expected
in both directions, without claiming a new ordinary reload.

## Verification boundary

Global conversion is installed for normal callers and the
[clothing catalogue](V3_CLOTHING_CATALOGUE.md). Remaining special readers and
ordinary ordering/payment still need integration/verification. Focused host and current
native shared-reader checks pass: twenty focused host/cartridge/composition
checks and the corrected 187-record native run with 177 assertions. The
[pipeline checkpoint](../docs/checkpoints/V3_FURNITURE_PIPELINE.md) records the
test-entry correction and complete passing evidence. Unchanged HRA grouping,
recommendations, base-point evaluations, and feng-shui checks retain their
recorded evidence instead of being replayed for an alias-only change.
The initial ordinary 22-record copied-town run also passes inventory Drop and
B pickup inside the house, with the complete imported identity retained,
display bank allocated/released, other items unchanged, and guards intact.
The garment is fixture-seeded, not purchased. Rotation, appearance inspection,
and placed-item save/reload remain unverified. See the
[checkpoint](../docs/checkpoints/V3_DISPLAY_CONVERSION.md).

Both web patchers remain V2 pending user testing and explicit approval.
