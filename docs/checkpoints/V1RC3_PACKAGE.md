# V1RC3 private playtest package

Local ROM: `build/v1rc3/Animal Forest English V1RC3.z64`.
SHA-256: `b8a4608b62c098b334dcbe5c87ad2483406c559ba3dbcd2ed26fd64ee27368f0`.

Patch archive: `build/v1rc3/V1RC3-patch.zip`.
SHA-256: `dd7c108a465d84abb16469b44738cb09e05549f7834b650b7fe8da82cd99fec3`.
UPS SHA-256: `27895f1412a60a5cb6ba2388b4db3a85fbd3c82c4167790f7ea0f6202a0f2796`.
Cartridge and packaging revision: `73a0d5f0e0fda629ad56b57a6d6380789f18229b`.

The complete `build/v1rc3-rebuild-01` two-stage replay passes from committed
sources, independently compiling the font extension and applying the transition
scale correction. Both intermediate/final ROMs match the tested candidates.
No retained compiled helper is an input. Receipt SHA-256:
`e8e1bea34a1ec2a7fb1f6d5eb0709310def955da8a644460bc24867e4b2925b4`.

Reproduction commands, using fresh output directories:

```sh
python3 tools/rebuild_v1rc3.py --output build/v1rc3-rebuild-new
python3 tools/package_v1rc3.py --build build/v1rc3-rebuild-new --output build/v1rc3-new
```

Preserved V1RC2 and verified retail N64 ROM are explicit inputs. The prior
base/artwork/RC1/RC2 recipes retain their recorded passing rebuild evidence;
unchanged earlier stages are not rerun for these corrections.

Seven focused implementation tests pass. Two package tests check patch-only
members, checksums, declared acceptance limits, and rejection of invalid
revisions, incomplete stages, or changed native evidence. The actual archived
standalone patcher executes against the original ROM and recreates the complete
32-MiB final image. No ROM, save, or loose game asset is included in the ZIP.

## Native evidence

The [font check](FONT_POLYGON_EDGES.md) uses the pre-transition cartridge;
the final image retains its exact tested font/module resources. The manifest
records this explicitly instead of claiming a same-ROM font run.
`build/font-edges-native-02/results.json` has SHA-256
`03902f0c5a34283d827fa0b35e9fbd4640a420e90c390f6c24f661a05a7e7d8e`.

The [transition checks](TRANSITION_EDGES.md) reproduce the old top strip and
verify all corrected closed shapes plus the centre open/midpoint states.
The corrected native check uses this exact final ROM. Receipts:

- Before: `build/transition-native-before-02/results.json`, SHA-256
  `57b158f1036c9ede0a96ec95ee0e3bb611cdd62a74a93f0fc4b4b08e180ba6d7`.
- After: `build/transition-native-after-02/results.json`, SHA-256
  `cff353ec4a71a413fa548f9ed1b31e8191d1fd2a99bd8026eec7d54a6d8c27ad`.

These complete silent checks retain guards/saved data and restore their isolated
checkpoints. Their initial setup failures/contaminated samples are separately
recorded, not relabelled as passing evidence.

Expansion Pak remains required. FlashRAM is 128 KiB with RTC; saved formats
and capacities are unchanged. RC1/RC2 hashes are rechecked and match their
preserved packages. No user save is accessed. The handoff links the named
V1RC3 ROM, not an intermediate preview.

Original-hardware appearance, ordinary save/restart, and broad playthrough
acceptance remain incomplete. The historical full regression retains recorded
fixture/accounting failures and is not claimed passed. The archive remains
private; public-release approval and completion of V1 are not asserted.
The N64-inspired V2 keyboard stays deferred.
