# V1RC4 private playtest package

Local ROM: `build/v1rc4/Animal Forest English V1RC4.z64`.
SHA-256: `5930435f588947df35313ae9cc2ea301af9fc7e68d59a7d8e13a48741d4f3067`.

Patch archive: `build/v1rc4/V1RC4-patch.zip`.
SHA-256: `b12db3634936ceeef06bcd2047d5771c4b420146de1c9c9a07e820ef59998119`.
UPS SHA-256: `f0e7d50f644135ea99cecb11b84056151b07f28500a9b36d2fe07dc1244f16a1`.
Cartridge/packaging revision: `b772f334db544227736d92827f0ed7347f0cce43`.
Manifest SHA-256: `df31fbb45ef13167b2754b19cd53d581bc5660a2f1bbae55b6fbef3f763f22eb`.

The complete `build/v1rc4-rebuild-01` replay compiles the replacement font
initializer from committed sources and applies both guarded corrections to
the exact preserved RC3 cartridge. Output matches the natively tested candidate.
Receipt SHA-256: `f2625d4cee5dd0983e821b7e9c240835b96a938b90f1159150f27fa2326176a0`.
No compiled helper is reused. Earlier unchanged rebuild stages retain their
own evidence; they are not rerun or mislabelled as fresh executions.

Three `test_v1rc4_package.py` checks pass in 3.546 seconds: patch-only archive
reconstruction and scoped compatibility metadata, rejection of changed parents
or cartridges, and refusal to package without the native loading evidence.
The actual archived standalone patcher executes against the verified original
Japanese ROM and recreates the complete 32-MiB candidate. No ROM, save, emulator
state, or loose game asset is included in the ZIP.

Reproduction with fresh output directories:

```sh
python3 tools/rebuild_v1rc4.py --output build/v1rc4-rebuild-new
python3 tools/package_v1rc4.py --build build/v1rc4-rebuild-new --output build/v1rc4-new
```

The packager requires retained local native evidence as well as the source ROM,
RC3, and its bound manifest. It independently checks the complete relocated
font, guarded owners, faulted-thread state, heap links, controller movement,
supplied save identity, and clean unsupported-memory stop before creating the
archive. [The implementation checkpoint](RC4_MEMORY_AND_SPACES.md) records
the reproduced failure, eight passing implementation checks, and exact native
state hashes. The original copied save remains unchanged and is not distributed.

## Save compatibility and limits

The supplied RC2 cartridge save loads on this exact ROM, and the loaded player
responds to the controller. Saved formats and readers/writers remain unchanged;
no migration is introduced. Loading RC3-created saves in RC4, loading RC4-written
saves in older RCs, and a manual save/quit/restart cycle remain unverified.
Keep original backups and separate test copies. RC3's existing-town memory crash
remains present in RC3 itself; do not recommend returning to RC3 for testing.
Cross-version compatibility is preferred, not mandatory, with explicit warnings
required for necessary incompatibilities.

Expansion Pak, 128-KiB FlashRAM, and RTC remain required. Font pixels, glyph
borders, speech spacing, and the transition correction remain intact. The font
has a new verified allocation address; older controlled drawing evidence is
identified as older evidence, not a fresh RC4 raster test. Native space-marker
drawing and original-hardware acceptance remain unverified.

This is a private playtest, not complete V1 or a public release. Broad gameplay,
remaining artwork/provenance review, and hardware acceptance remain. The
historical full regression is not claimed passed. The N64-inspired V2 keyboard
remains deferred until V1 completion.
