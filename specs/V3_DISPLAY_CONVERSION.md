# V3 pocket and mannequin conversion

## Installed contract

The selected imported garment converts from pocket `34BF` to room display
`3AFC`. All four display orientations `3AFC..3AFF` convert back to `34BF`.
Both paths require the existing complete display-profile selection check.
No other item identity changes. Original clothes, fish, insects, umbrellas,
furniture, invalid items, and missing imports use the original native functions.

Native forward conversion is `800BEFCC..800BF10B`; inverse conversion is
`800BF10C..800BF22F`. Both complete bodies and their exact prologues are checked
before installation. Each entry redirects through a new resident wrapper and
a sixteen-byte bridge that executes the displaced instructions before rejoining
the original body. Existing callers retain their argument/return conventions,
including sixteen-bit item truncation and native caller stack slots.

The 160-byte code occupies `80466270..8046630F`, after the existing mannequin
index helper, within reservation `80466270..804665DF`. Its two stack frames
are 24 and 32 bytes. Bridges occupy `804665E0..804665FF`, before its profile row.
The current alias/metadata helper at `80466C00` supplies canonicalization.
No heap, saved field, selected-profile bit, or ROM DMA slot grows. ABI 43
identifies this integration. Save/profile compatibility with ABI 42 is expected
in both directions, but unchanged formats do not prove an ordinary reload.

## Verification boundary

Global conversion is installed for normal callers; catalogue clothing rows and
remaining special readers still need integration. Focused host and current
native conversion/scoring checks pass: two focused tests and the initial
157-step native run. Full HRA grouping, recommendations, seven base-point
evaluations, nine feng shui item evaluations, and three room evaluations pass.
The initial ordinary 22-record copied-town run also passes inventory Drop and
B pickup inside the house, with the complete imported identity retained,
display bank allocated/released, other items unchanged, and guards intact.
The garment is fixture-seeded, not purchased. Rotation, appearance inspection,
and placed-item save/reload remain unverified. See the
[checkpoint](../docs/checkpoints/V3_DISPLAY_CONVERSION.md).

Both web patchers remain V2 pending user testing and explicit approval.
