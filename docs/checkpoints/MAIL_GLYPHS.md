# Complete mail-glyph framework checkpoint

## Implemented

- Source-verified fourteen-cell font: original five cells plus seven missing
  mail glyphs and the two accented uppercase forms used by the donor formatter.
  The original atlas and existing cell advances remain unchanged.
- All 4,866 supplied reference parts transcode. All 100 previously unsupported
  occurrences across 59 parts retain exact donor code identities. Every
  previously available catalogue-two part remains equal to its frozen content.
- Frozen catalogue four at VROM `030A0000`, format one, semantics two. Old
  catalogues two and three remain separate and unchanged.
- C/Python formatting retains complete pairs and accented capitalization after
  empty fields. Saved literal fields keep their single-byte restriction.
- C catalogue scanning, pagination, and footer alignment consume each pair once
  while preserving drawing byte offsets, explicit lines, and page/footer rules.
- Catalogue installation requires the matching complete font and resident code;
  final ROM publication requires the exact installed font and snapshot reader.
- Shared CRC32 and drawing routines keep the resident image within its original
  limit. No saved structure or RAM reservation grows.

## Verified evidence

`build/mail-glyph-content-tests.log` passes six tests, including all complete
6,514 reference assembly cases, independent in-place semantics, exact source tokens,
all pair identities, atomic output bounds, and rejected split pairs.

`build/mail-glyph-reader-tests-final.log` passes all 54 focused tests in 8.774
seconds. It covers old and new full reconstruction, glyph-bearing pages and
footer drawing, font pixels/binding/relocation, loader failures, and sanitizer
checks for the font primitives and startup owner. It is not a full-project
regression or a sanitizer claim for every mail consumer.

The final combined focused batch passes all 80 tests in 23.996 seconds:
`build/mail-glyph-final-regressions.log`. It includes three catalogue/font
installation tests, all source/capability checks, the complete reader tests,
current artifact/relocation tests, and runtime layout checks. Independent font
images/relocations/manifests and resident images/bootstrap/manifests agree.

The broader 60-test creator batch passes 55 checks and identifies four stale
compiled artifacts plus an unknown-catalogue fixture that still selects ID four.
The resident and fortune/leaflet/event probes are rebuilt. The event probe test
uses the current module rather than a historical renewal pilot; unknown-ID
preflight testing uses unassigned ID five. All corrected checks pass in the
final 80-test batch. Other old module-bound actors/creators still require rebuilding
for the complete translation ROM. A full-project regression is not claimed.

The first focused batch exposes a stale fixture assumption: catalogue four is
treated as unknown after a preceding test loads it. The corrected fixture clears
the complete simulated cartridge between tests and uses unassigned ID five for
unknown-identity rejection. Production code is unchanged for that correction.

The complete silent four-MiB native batch passes as `build/smoke-mail-glyph-01`:
114 glyph-bearing reference reconstructions, eight old-catalogue reconstructions,
28 direct line scans, 44 actual native draws, and seventeen actual cursor cases.
All 346 native calls and 1,224 assertions pass, including restored checkpoint
memory and resumed execution. The font/code/pixels come from normal startup,
not debugger uploads. Allocation release, font/native-width retention, guards,
and graceful shutdown pass. FlashRAM remains entirely erased. Controller Pak
contents equal the preceding blank isolated HRA score fixture. These tests do
not create or deliver letters through native gameplay routes and do not perform
a real letter save/reload.

Evidence SHA-256 values:

- Final 80-test batch: `92ea9d1339217c067c462915d511ff2e36b54757169e3c65c70552ec9db18980`.
- Initial corrected 54-test batch: `5f8375183ce44d464b7622e6902011c8622b71281c42a38b7a17e3750b920ed5`.
- Three installer tests: `66d48efba5cf291e40c479ab2a861aa0bed23ebf7097f95e0bea32a7c3344a7a`.
- Native results: `0537b24e1a707420d401deb60be16206fe563fadcb8425b976eb65a01d5bacfa`.
- Native scenario: `b8ce574a9a8bda1f7101b54333a22be048fdf7ac96d484991d14f9db3e79db82`.

## Artifacts

- Catalogue four: 326,288 bytes,
  `76aa61189ccc1043ee4d91f3fd7a2d351b0914b4a932515b47b5bcbe426323bb`.
- Fourteen-glyph resource: 1,600 bytes,
  `12a90673f21a6c0bfa3fc05039279b1efc65d96319460ae36993eafa0822c105`.
- Persistent font image: 3,680 bytes,
  `2e23b50fe14fb3ce02d7f881e6b0f39656f9cb8858d987216ed39a65669de833`.
- Font relocation: 304 bytes,
  `cd13bb76254ddf9d4af391c523a6b83e7332c09f8cb057c2436bbceaf3ee9b84`.
  Complete persistent allocation including alignment is 3,999 bytes.
- Resident: exactly 24,576 linked bytes in the unchanged 32,768-byte reservation,
  padded image SHA-256
  `70e63aa11f2b2d4bdf1907a46d8463254cbbc7dff36929ca0328b50ceb5836ea`.
- Isolated cartridge fixture:
  `build/mail-glyph-native-fixture/mail-glyph-test.z64`, SHA-256
  `323411eeef0999daf67e5f97a81e1da59fd670213fda6a03256bebe29e2c47bc`.

The fixture is not a complete translation build and is deliberately excluded
from automatic translation-progress selection. It contains synthetic read tests,
not native delivery integration. All generated assets/ROMs/results remain ignored.

## Reproduction

```sh
python3 tools/extended_glyphs.py --mail --output build/mail-glyphs
python3 tools/build_extended_font_cartridge.py \
  --resource build/mail-glyphs/glyphs.bin --output build/mail-font-cartridge
python3 tools/mail_catalog.py --rom 'local/rom/Doubutsu no Mori (Japan).z64' \
  --catalog 4 --output build/mail-glyph-catalog
python3 tools/build_mail_glyph_catalog.py --output build/mail-glyph-resources
python3 tools/build_runtime_module.py --rom 'local/rom/Doubutsu no Mori (Japan).z64' \
  --output build/mail-glyph-runtime
python3 tools/mail_glyph_scenario.py --output build/mail-glyph-native-fixture
```

Run `tools/emulator_smoke.py` against that fixture ROM/scenario with disabled
audio, a fresh isolated output directory, `--no-initial-screenshot`, the existing
headless Xvfb path, and the declared 600-second bound. The combined batch restores
one checkpoint after all glyph and old-catalogue checks.

## Required continuation

1. Connect catalogue four to the affected native creator routes, beginning with
   all supported Mom, birthday, HRA score, and composite replies together. Preserve
   source identity approval and original metadata/selection/reward behaviour.
2. Rebuild all module-bound creator/probe/actor dependencies and the complete
   translation ROM. The resident has no linked headroom. Do not expand into test
   scratch or raise creator bounds without actual allocation evidence.
3. Validate complete delivered letters, old saved catalogue reconstruction, and
   isolated save round trips. Only installed, verified routes receive translation
   credit. Wider source identity review, ordinary gameplay, editorial polish,
   hardware, patch-only release preparation, and both stretch goals remain.

The paused atlas-edge task remains paused. Title artwork remains the first
image-replacement task after the main text port.
