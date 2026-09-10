# V1RC2 private playtest package

Local ROM: `build/v1rc2/Animal Forest English V1RC2.z64`.
SHA-256: `7a265fca118e522591085d0f7ce3a926b46d78a86c67e6f07443c64befe005bb`.

Patch archive: `build/v1rc2/V1RC2-patch.zip`.
SHA-256: `1746ceace5a539e1d7b015b6e32adf0f75008497a32a0d7c40cfcf28473ea987`.
UPS SHA-256: `6c334b39eeb92801196e3b7712e2ccf8663daa1d14bb92f8aed5ee7bdd393e43`.
Cartridge and packaging revision: `f81ee0833d8ff5b65938a91c8886d233dba9cff2`.

The complete `build/v1rc2-rebuild-01` replay passes from committed sources with
no working-source changes. Its three stages compile the hiring-notice no-op,
text/HUD clamping, and corrected keyboard helper from source; no retained
compiled helper is an input. The final ROM/UPS match the independently tested
keyboard candidate. Stage times are 7.227, 7.061, and 13.348 seconds.
Receipt SHA-256: `d475d0f0e2cdfebb13db770b222ae1c207582b7fda94ab43b960d2d6065d7b70`.

Reproduction commands, using fresh output directories:

```sh
python3 tools/rebuild_v1rc2.py --output build/v1rc2-rebuild-new
python3 tools/package_v1rc2.py --build build/v1rc2-rebuild-new --output build/v1rc2-new
```

The preserved V1RC1 ROM and supplied original games are explicit inputs.
Earlier 61-stage base, 28-stage artwork, and seven-stage RC1 recipes retain
their recorded passing rebuild evidence; they are not rerun for unchanged code.

Two package checks pass in 1.657 seconds. They verify exact patch-only members,
checksums, acceptance flags, and rejection of missing stages, invalid revisions,
mismatched native-test ROMs, and absent checkpoint restoration. The actual
archived standalone patcher also executes successfully against the supplied
original and reproduces the complete final ROM. No ROM, save, or loose game
asset is included in the ZIP.

The package binds the complete controlled keyboard native result:
`build/v1rc1-keyboard-native-02/results.json`, SHA-256
`2fc1f192cfc8a94f138e0c1c7faca1dce28476290804e439b0733c78e91b141f`.
Five calls/thirty assertions pass with unchanged save data, intact guards,
released fixture, restored checkpoint, and graceful shutdown. The
[keyboard checkpoint](KEYBOARD_RC1_FIX.md) records geometry and setup limits.

The ROM is 32 MiB and requires an Expansion Pak. FlashRAM remains 128 KiB with
RTC; saved formats and capacities are unchanged. V1RC1's ROM hash is rechecked
and remains `63794bd31fe5c7c9ae786b15a41d6a80c2390c890b2edd963ace9a9e5edb8d37`.
No user save is accessed. The user-facing handoff links the named V1RC2 ROM,
not an intermediate preview.

Original-hardware appearance, ordinary save/restart, the broad playthrough,
and embedded-warning drawing are not marked passed. The full historical
regression still has recorded unresolved fixture/accounting failures; its
title metadata failure has a passing focused correction. The archive states
these limits and remains private, without public-release approval or a claim
that V1 is complete. The N64-inspired V2 keyboard stays deferred.
