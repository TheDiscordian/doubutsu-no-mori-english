# V1RC6 private playtest package

Local ROM: `build/v1rc6/Animal Forest English V1RC6.z64`.
SHA-256: `800c7e9d4e6a4b81db05d0a8258d151417d02c9edc47806cf3429e3d144fab09`.

Patch archive: `build/v1rc6/V1RC6-patch.zip`.
SHA-256: `4a35f3a91b9e6772cb0f8c602c28c45b38ba87a3283fd803fc61593c4ea41bcd`.
UPS SHA-256: `51702b426b92097686087fc1bf239fe1ed4e4eb7c91a9bacdbbfb288de33e0bb`.
Packaging revision: `5c945c033601aa45dc00899c9283c1e6a98019e9`.
Local manifest SHA-256: `2e6e7a3d6c721a84813629de9400027cbdf2afe29868c5c79a83eabf9c91ad64`.
Verification SHA-256: `79558f71400f65b82bf60ac2035b1b459f9dc058adcf1cebcd61f924cd43e5b8`.

The cartridge and UPS match the committed combined
[menu-text follow-up](MENU_TEXT_FOLLOWUP.md). Both construction receipts, their
source revisions and builder hashes, exact ROM/patch identities, stage ordering,
and unchanged saved/allocation/relocation contracts are checked before packaging.
The packager reads the builder at each recorded Git revision and compares its
hash with both the receipt and the checked current source. A later clean replay
using those unchanged builders may have different receipt metadata; it remains
acceptable only with the same checked source and complete output identities.

Three `test_package_v1rc6.py` checks pass in 1.476 seconds. They verify exact
eight-member ZIP contents, all seven payload checksums, complete reconstruction,
the source-guide link, both source stages, explicit compatibility/acceptance
limits, rejection of incomplete/dirty/disconnected/unbound receipts, and valid
committed-replay metadata handling. These are new package checks; the earlier
eight passing implementation checks and committed builds are retained, not rerun.

The archived standalone patcher executes in an isolated temporary directory
against the verified original Japanese ROM and recreates the complete checked
32-MiB cartridge. The ZIP contains only the UPS, manifest, README, source notes,
tooling licence, two Python files, and checksums. No ROM, save, emulator state,
or loose game asset is included. All earlier candidates remain untouched.

To reproduce the package with retained correction builds and fresh output:

```sh
python3 tools/package_v1rc6.py --output build/v1rc6-new
```

## Compatibility and acceptance

RC5-to-RC6 and RC6-to-RC5 save compatibility are expected, not independently
load/save-cycle verified. These changes alter only counted menu strings,
pointer/count instructions, and the Pak heading's X origin. No format or saved
reader/writer changes and no migration are introduced. Keep original backups
and test copies. RC3 remains an unsuitable fallback because its known existing-
town memory failure is still present in RC3 itself.

Expansion Pak, 128-KiB FlashRAM, and RTC remain required. Ordinary menu appearance,
broader V1 acceptance, and public-release review remain unfinished. No fresh
native execution, hardware certification, full-suite success, or human
playthrough completion is claimed. The Pak instruction can be viewed without
deleting notes; no destructive operation is requested to test a label.

The follow-on read-only menu scan finds retained source Japanese in moved
address, gyroid, warning, and other owners alongside non-text binary runs.
Those bytes alone are not missing English: their installed reader must be
checked before treating retained old storage as an active untranslated route.
Direct inspection of this RC6 confirms the address prompt calls its appended
helper at `8088CCA0`, all twelve gyroid response entries select appended English,
and the first inventory/Pak warning records select `You can't hold any more
letters!` and `Reading data from`. These are source/reader checks, not fresh
native execution; preserve these classified hits instead of rescanning them.
This scan is not a full-game text audit or additional translation credit.
V2 keyboard work remains deferred until V1 completion.
