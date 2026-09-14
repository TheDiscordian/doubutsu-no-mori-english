# V3 display item-reader checkpoint

## Artifact

`build/v3-display-readers-02/animal-forest-v3-asset-loader.z64`, ABI 42.

- ROM SHA-256: `d8caeb04d9a2c8cfcac605e45cf9826cd82fb33b8014c0d9f4efcd4706fae09c`.
- UPS SHA-256: `54bfb1f66a6f9e97d8cc2df4cd22c10521ce4a9abf26e2880b8a42b06c08615b`.
- Resident prefix SHA-256: `7d6d5d37db238fa79a7dede138a254dc6a5299d4ed51013da8ce4f1e269f5f45`.
- Display readers, 516 bytes: `d1925e47e2f98f22021aee0513bdcb7c728cf76dbb84eacd9e4ed37de36428d2`.
- HRA image, 30,288 bytes: `d91dfd3bf92f5f549877a4c18622649f16c2439e787a497b990bb855d2b91716`.
- HRA relocation, 1,184 bytes: `c727a505f8fe0de1cefa6c26ae45aad151126f8e873d5d128766cf159d25f439`.
- Feng shui image, 7,968 bytes: `549fb3640dc54c055d3b916d63a5c8ae661bd0765e8cd75636fa820857d00493`.
- Feng shui relocation, 80 bytes: `3e26a63e04f84c423742c7313b74109cb153e60548cda15f0586db78ba244ff7`.

The [specification](../../specs/V3_DISPLAY_ITEM_READERS.md) records canonical
garment metadata/ownership, source-verified donor scoring rows, and memory
bounds. The first build stopped before producing a ROM because the installer
expected zero in retired bank-index storage. That seed actually contains `FF`.
The corrected build verifies the entire seed, reclaims only its owned block,
and succeeds with the pinned Docker compiler. The complete V3 DMA file remains
65,440 bytes with 96 bytes of existing ROM-tail space.

## Focused checks

`build/v3-display-readers-tests-02.log` records two passing tests in 2.685 seconds:

- Sanitized C wrapper checks cover all rotations, names, categories, prices,
  native footprint delegation, canonical collection/query routing, full-width
  input handling, and unchanged disabled/native arguments.
- Cartridge checks cover all six final redirects and both prologue bridges,
  complete helper code and padding, retained resident/secondary/save code,
  unchanged selected profile and runtime layout, actual startup CRC/ABI,
  complete scoring tables and donor row 682, original overlay reconstruction,
  allocation/relocation limits, all other resources, and UPS reconstruction.

The first host attempt missed the expected main-code scheduler edits in its
unchanged-resource comparison. The corrected test restores only each recorded
HRA/feng shui scheduler operand before comparing the entire main resource with
ABI 41. Exactly twelve main-code bytes differ, all explained by the new sizes.
No previous ROM is replayed. Construction-source hashes match the build report.

## Native execution: complete components and unresolved tail

The silent `build/v3-display-readers-native-01` run records 148 steps and is
**incomplete**, not passed. Its entire item-reader exercise passes, including
four real native mannequin footprints, all 48 bytes per footprint, full names,
prices, categories, missing-profile rejection, code retention, and guards.

The following collection exercise confirms four-player acquisition rules,
all rotated display aliases sharing clothing bit `BF`, and missing-display
rejection. Its artificial missing-profile case then queries valid pocket item
`34BF` before restoring the current profile. The real `require_state` guard
compares current and working profiles and correctly stops on that mismatch.
The callback trace identifies that exact non-returning call. The test is fixed
to restore the profile before querying the valid garment; the game guard is
not weakened. Scoring and the final checkpoint restore are not reached.

The one corrected retry, `build/v3-display-readers-native-02`, skips the
completed item-reader exercise and records 89 steps. The entire collection
exercise passes, including all four residents, present/quest timing, canonical
ownership, disabled aliases, original/static retention, selective clearing,
full record/runtime restoration, complete code checks, and guards.

HRA then loads its actual expanded image and relocation through the native
loader into a sufficiently large private fixture. The complete independently
relocated owner/BSS comparison passes, and the native group initializer returns.
The subsequent expected-table assertion fails because the Python predictor
overwrites its table-capacity variable with a per-series count, predicting
`all 0 assigned native/imported metadata rows`. The outer variable is corrected
to `capacity`, and syntax checks pass. That correction is **not re-executed**.
HRA group/points assertions, feng shui execution, and the run's final checkpoint
restore remain unverified. Neither overall native run is labelled passed.

The batch's initial setup attempt and single justified retry are exhausted.
Do not start another native retry of this unchanged build. Carry the corrected
scoring tail into the next meaningful game-code integration. These test-driver
failures do not establish scoring correctness, and do not justify disabling
memory/profile checks. No physical audio or original user save is touched.

## Next work and compatibility

Connect global pocket/display conversions and remaining special readers, then
catalogue presentation, ordinary placement, and persistence. Keep the corrected
HRA/feng shui tail pending for that integration. The wider villager/item,
acquisition, Controller Pak, and browser-selection goal stays open.

The complete save runtime, secondary codec/item code, selected profile, and
working state are unchanged from ABI 41. Same-profile compatibility is expected
in both directions; this is not a new ordinary reload result. Older profiles
without the display bit still reject new saves. Preserve save backups.
GitHub development is allowed; neither web patcher changes without user testing
and explicit approval.
