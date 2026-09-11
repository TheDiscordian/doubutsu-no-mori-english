# V1RC5 private playtest package

Local ROM: `build/v1rc5/Animal Forest English V1RC5.z64`.
SHA-256: `6ed7d636b953d24d4ad10ae8ea806deb133a752f4295ad79727c52336095dae4`.

Patch archive: `build/v1rc5/V1RC5-patch.zip`.
SHA-256: `f8608541b4ffc04907c1a1d0fff6a5eb5a0a2a9055c3ca1b219d178ca720443d`.
UPS SHA-256: `aaa8c3c35f6ea187f375906af789823235a06599cdc6ce50af4049727f037ec8`.
Cartridge/packaging revision: `aa4248789b6d3954a5ff339c7fddfcf3ff844751`.
Local manifest SHA-256: `5da58d20793aedb7b8cce93d9df8f1fcdf443eb72a824aa2cbfd828dd465657c`.
Verification SHA-256: `f26369cd0444accefaa4d95096d651ef80c575e9317c255beb68da4ff057f6f7`.

The committed `build/rc4-menu-labels-03` replay compiles the catalogue adapter
and reconstructs all three guarded menu corrections from the retained RC4
cartridge. Its ROM and UPS match the focused/native-tested development build.
Receipt SHA-256: `50b499b8cf95ecd49336637cc6a5ee9e164e1dd1810eeb1b56c5b7aed251ea2b`.
The receipt records a clean production worktree and the exact toolchain/source
hashes. Earlier unchanged stages retain their separate evidence; they are not
rerun or represented as fresh executions.

Two `test_package_v1rc5.py` checks pass in 1.537 seconds. They verify the exact
eight-member patch-only archive, every member checksum, complete reconstruction,
source-guide link, scoped native evidence, compatibility metadata, and rejection
of an uncommitted cartridge receipt or invalid source revision. Packaging also
executes the archived standalone patcher in an isolated temporary directory
against the verified original Japanese ROM, producing the complete checked
32-MiB candidate. No ROM, save, emulator state, or loose asset is in the ZIP.

The [implementation checkpoint](RC4_MENU_LABEL_FIXES.md) records the five
passing focused checks and the successful two-branch native adapter execution.
Its captured font arguments establish complete English text selection and
buffer retention, not screen pixels or original-hardware appearance.

Reproduction uses fresh output directories:

```sh
python3 tools/rc4_menu_labels.py --output build/rc4-menu-labels-new
python3 tools/package_v1rc5.py --build build/rc4-menu-labels-new --output build/v1rc5-new
```

The packager requires the bound local native evidence and committed production
sources. A documentation-only packaging revision changes archive metadata, not
the checked cartridge. Preserve the original handoff and earlier candidates.

## Save compatibility and limits

RC4-to-RC5 and RC5-to-RC4 compatibility are expected because saved formats,
readers/writers, names, and transaction code are unchanged. No migration is
required. Neither direction nor a manual RC5 save/restart cycle is independently
verified. Keep original backups and test copies; do not use RC3 as a fallback
because its known town-loading memory defect remains in RC3 itself.

Expansion Pak, 128-KiB FlashRAM, and RTC remain required. The three catalogue/
repayment findings are implemented; their ordinary hardware appearance remains
pending. Broader V1 acceptance, artwork/provenance review, and the human
playthrough remain unfinished. The historical full suite is not claimed passed.
This is a private playtest, not a completed public release. V2 remains deferred.
