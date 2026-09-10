# System-letter and glyph fixture follow-up

All 33 selected tests pass after six test files select current source-built
resources. This closes twelve errors from the retained
[full regression](V1RC1_REGRESSION.md): five system-letter class setup errors
and seven glyph-installation errors. Production validation, runtime code,
translations, cartridge builds, saved data, and earlier artifacts are unchanged.

## Cause and scope

The old system-letter creators target obsolete resident-module identities and
capture/creator/linker source inventories. The five class setups select
`build/runtime-module`; the glyph installer selects `build/mail-glyph-runtime`.
Neither is the current complete module. Several compositions also select the
superseded `mapped-items-final-resource`, which correctly fails the current
item-name provenance check. The remedy is current test resources, not relaxed
source, variant, font, catalogue, or item guards.

All six tests use `build/notice-seasonal-runtime`; item-dependent cases use
`build/design-items-resource`. Their hashes are in the
[core fixture checkpoint](RUNTIME_FIXTURE_FOLLOWUP.md). Current source is compiled
into six new subdirectories of `build/letter-runtime-fixtures-01`. The preceding
`build/shared-npc-capture-runtime-followup-01` supplies the already verified
base dispatcher where the optional-variant tests require it.

The first five variants deliberately select immutable catalogue two to test
its supported and rejected bodies. The sixth selects catalogue four and tests
complete glyph-bearing English. A catalogue-two rejection is not reported as
missing text in the current playable cartridge, which uses the complete path.

## Reproduction and identities

Every variant uses the existing `tools/build_npc_mail_capture.py`, pinned public
Docker compiler, module `build/notice-seasonal-runtime/module.json`, words
`build/design-items-words/words.bin`, and aliases
`build/npc-mail-names/aliases.bin`. No earlier directory is overwritten.

| Output suffix | Required flags |
| --- | --- |
| `mother` | `--mother-letters` |
| `departed` | `--mother-letters --departed-letters` |
| `villager-event` | `--mother-letters --departed-letters --villager-events` |
| `academy` | `--mother-letters --departed-letters --villager-events --academy-letters` |
| `academy-score` | `--mother-letters --departed-letters --villager-events --academy-letters --academy-scores` |
| `glyph` | `--mother-letters --departed-letters --villager-events --academy-letters --academy-scores --mail-glyphs` |

For example, reproduce the complete glyph variant into a fresh directory:

```sh
python3 tools/build_npc_mail_capture.py --module build/notice-seasonal-runtime/module.json --words build/design-items-words/words.bin --aliases build/npc-mail-names/aliases.bin --output build/letter-runtime-fixtures-new/glyph --mother-letters --departed-letters --villager-events --academy-letters --academy-scores --mail-glyphs
```

All variants retain word digest
`3e06014a398b03a9ccac58fa8c9ac57ba3c5a5312e39167b288c314cc6dee4f9`
and alias digest
`a79b6bc3c5b36c7ce2bcea55932ccdf4ce694608e5dcfb896226a24d368bf5d6`.
The score variants include the verified 55-series resource. Full source,
compiler, import, symbol, relocation, and resource inventories remain in each
local `overlay.json`.

| Variant | Image/relocation bytes | Image SHA-256 | Manifest SHA-256 |
| --- | --- | --- | --- |
| `mother` | 24928 / 240 | `a7920abf0ab15d34cfacc65a87b54d608df1a86c6fe03dba38e0549ac40da0ce` | `935af3c8c850c699759a4c86788e6a4fe34789c66a226a0bc6cef9d471e74b61` |
| `departed` | 26064 / 320 | `9f72babff2cd043548d86a2491a99295043ababe1087ec3d2315902661ab6ad6` | `770f10d3a84659d6ecea086c3b3714c5e237d1c88b3bca4b80eb2223af153c1c` |
| `villager-event` | 27248 / 368 | `bd97ae561333d486855e3355ccef6a1e67f32857d758fb9832a318394f252aa6` | `4961b19678975920d2e92f4a25f31b2a14fd2ea9f02258ec6e3b85cbb5141e0e` |
| `academy` | 27840 / 368 | `4ab5c598f4ffc3d776d216d6ee5c4b2da3d7f82bfa6bb8b5547c4e716df7b3a5` | `9d1f2ed765d0605cb01b3acf354c861a2f9a8fa40511888e21b6e192e6bb1861` |
| `academy-score` | 30720 / 432 | `1380aa24ce08006f638e332d96675424f90647ae27e7e10d834ffa773265df30` | `e3f7e67ecc2a8912d2099e43caa1341918bd523bcd9615b8739d4c9ec81b056c` |
| `glyph` | 30720 / 432 | `6fa0d45920812c2f3265c81c2548dbf7c91e6b57b182916a4de1fc155b1a1833` | `b5e9f70db88e57065b984b681237d9b8e2cd9be7c615bd2f031c6e0ebc8bb996` |

## Executed checks

The five system-letter suites pass all 26 checks in 20.755 seconds:

```sh
PYTHONPATH=tools:tests python3 -m unittest test_mother_install test_departed_install test_villager_event_install test_academy_install test_academy_score_install -v
```

The glyph suite passes all seven checks in 7.185 seconds:

```sh
PYTHONPATH=tools:tests python3 -m unittest test_mail_glyph_install -v
```

Checks cover complete source-bound parts, exact permitted instruction ranges,
publication failure branches, unchanged scoring data/relocation layout, optional
dispatcher exports, dependency/variant corruption, atomic rejection, catalogue
reproduction, actual font installation, full glyph-catalogue routes, and
rejection of missing or altered font/catalogue resources.

The system suites' existing cartridge checks select the complete combined
`build/v0-hardware-fixes-02` rather than obsolete intermediate pilots. Its ROM
SHA-256 is `b93a54b8804f262e1c05e7dabcd6aac4f5b47d637c69d94264f058c12dbdbd35`;
the report SHA-256 is
`c84926794a2bfa0854bccbe64e6ee437b8df96a3601a577e51377288f833bbc3`.
All five actual installation verifiers and resident-module verification pass.
The HRA malformed-report case removes one complete template; the former fixture's
full-template list is now correct for catalogue four and is not malformed data.
No correctness check is replaced by accepting an early unrelated rejection.

These are host/source/cartridge-structure checks, not fresh emulator execution,
ordinary delivery, save/restart, or hardware acceptance. They do not relabel the
selected v0 fixture as a new RC4 execution. RC4 and the supplied saves remain
unchanged. The entire historical suite is not rerun or declared passed.

Other obsolete probe, actor, and later letter fixtures remain separate work.
The native-species mismatch test still uses `design-items-pilot`'s older runtime
inventory, so its expected word-profile rejection is masked by the earlier
current-source guard. Preserve that failure until its specific test uses a
verified current composition; do not loosen the guard or change counter totals.
