# V1RC7 private playtest package

Local ROM: `build/v1rc7/Animal Forest English V1RC7.z64`.
SHA-256: `3a2e8b4241837daa7cea094deb2f2d229b2fa34755cf9103e493e27b1cf3fd8a`.

Patch archive: `build/v1rc7/V1RC7-patch.zip`.
SHA-256: `7ac2c682a00c6e83aa81e99a167f82c9ac8ed26d79909b7879aaececc95a0980`.
UPS SHA-256: `c477bd1e5fdeb7e36621bd7c594d23b369e9d97216eb2df68473c31a8a796427`.
Packaging revision: `157efbb92a601a05ea5d8c523cf6c396e8bbc04d`.
Packager SHA-256: `e77fb073b178a1f37b18196e7fddf1c42f8c381d59c56106485a791bec73cd60`.
Local manifest SHA-256: `3aeb2105d7bf99bbd947bfb5397f599e861bfdc494ff4ab99038b07cc178ac63`.
Verification SHA-256: `de260d16515fd6fdf245ee60a28f2aa2b0b4d00bb1c4cea5e333330a52f65220`.
README SHA-256: `9f9e0e6336d438b8fb68b2a06ed539463de93e99223ef175da5e0237c4e3c1cb`.

## Included work

The cartridge matches the complete committed [gamestate build](GAMESTATE_MENU_TEXT.md).
It contains all RC6 corrections, the native controller warning/erase label
(V1-26), and nine separate player/save-gamestate labels (V1-27). Both correction
receipts, their source revisions, builder hashes, exact ROM/UPS identities,
stage ordering, and unchanged save/allocation/relocation/menu-action contracts
are verified. Each recorded builder is read from its actual Git commit and
checked against the recorded and current source hashes. A later clean replay
may alter receipt metadata only while retaining those exact code/output checks.

## Verification

Three `test_package_v1rc7.py` checks pass in 1.684 seconds. They verify:

- Exactly eight ZIP members and seven payload checksums, complete cartridge
  reconstruction, source-guide link, and both committed correction stages.
- Explicit RC6 compatibility expectations and separation of accepted prior
  hardware playtests from unexecuted RC7 changes.
- Rejection of missing/reversed/dirty/disconnected receipts, altered source or
  revision, and changed memory/save/menu-action contracts.
- Acceptance of committed replay metadata only with the same bound sources.

The committed packager executes the archived standalone patcher in an isolated
temporary directory against the verified original Japanese ROM. The patcher
recreates the exact checked 32-MiB candidate. Only after that check passes does
the packager write the named local ROM, ZIP, manifest, verification, and README
to a fresh output directory. No older candidate, save, or SD-card file changes.

The ZIP contains the UPS, manifest, README, source notes, tooling licence, two
Python files, and checksums. It contains no ROM, save, emulator state, or loose
game asset. The earlier ten passing correction checks and clean source builds
are retained, not rerun. No unchanged native scenarios or full suite are rerun.

To reproduce from the retained committed stages into fresh output:

```sh
python3 tools/package_v1rc7.py --output build/v1rc7-new
```

## Compatibility and human acceptance

RC6-to-RC7 and RC7-to-RC6 save compatibility are expected, with no migration:
saved formats and readers/writers are unchanged. These particular loading
directions are not independently executed. Keep backups and test copies; do
not use the known-broken RC3 cartridge as a fallback. Expansion Pak, 128-KiB
FlashRAM, and RTC remain required.

The user explicitly confirms ordinary save/restart/reload and all reported
fixes V1-01 through V1-23. [The human record](V1_HUMAN_ACCEPTANCE.md) closes
those checks; the new manifest retains that evidence separately. RC7's new
labels are not part of those earlier sessions. Its candidate-specific false
execution flags do not reopen accepted unchanged fixes or the general save
workflow. Source-identified menu appearance, development-menu access, and other
genuinely untested cases keep their own limits.

## Next work

Review the separate `ovl_select` development scene-name table using its actual
graphics-print encoding and current installed resource. Do not enable debug
menus or invoke destructive operations. Preserve completed direct-font scans,
reserved-name padding classifications, accepted fixes, and all current builds.
Finish remaining content/release preparation with concrete bugs taking priority.
Public distribution requires approval and redistribution review; V2 is deferred.
