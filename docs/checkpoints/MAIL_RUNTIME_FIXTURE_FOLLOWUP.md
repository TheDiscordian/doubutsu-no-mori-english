# Letter and shared-word fixture follow-up

Seven test files select current resources without changing production guards,
runtime source, translations, saved formats, or the playtest ROM. This closes
seven errors from the retained [full-suite result](V1RC1_REGRESSION.md), not the
entire suite. Percentage-tool expectations remain outside this batch.

## Resource selection and reproduction

Mail grading, complete NPC patching, resident words, capture validation, loader
installation, and shared words select `build/notice-seasonal-runtime`. The
resident-word environment override remains supported. The display-name
composition check selects `build/design-items-resource`, whose current item
provenance passes the unchanged guard. Module/item hashes are recorded in the
[core fixture checkpoint](RUNTIME_FIXTURE_FOLLOWUP.md).

The retained `build/npc-mail-capture` has a different module identity and stale
capture/linker/creator/catalogue/glyph/loader source hashes. Two fresh baseline
capture variants are compiled from current source in the existing pinned Docker
image. Neither replaces the historical directory or produces a ROM:

```sh
python3 tools/build_npc_mail_capture.py --module build/notice-seasonal-runtime/module.json --words build/npc-mail-words/words.bin --aliases build/npc-mail-names/aliases.bin --output build/npc-mail-capture-runtime-followup-01
python3 tools/build_npc_mail_capture.py --module build/notice-seasonal-runtime/module.json --words build/design-items-words/words.bin --aliases build/npc-mail-names/aliases.bin --output build/shared-npc-capture-runtime-followup-01
```

Use fresh output paths for later reproduction. Each image is 24,320 bytes with
a 240-byte relocation section. Both use module SHA-256
`493bc25a922bbd9d321759677134520bbb179413985f0e047df45e6e432664c6`,
alias SHA-256 `a79b6bc3c5b36c7ce2bcea55932ccdf4ce694608e5dcfb896226a24d368bf5d6`,
and relocation SHA-256 `6fbc0a803c7c5cf50b7dcbfc0a305007b2587dbc1ed2ba8c7e8db6f0df2f1a8e`.

| Fixture | Overlay SHA-256 | Manifest SHA-256 |
| --- | --- | --- |
| Baseline capture/loader | `5d8ab5a3a296f038be00fb112a15120069f06bfaa563a81731c8632df6476c1e` | `a7bce4080904b54b18497798d97d5b5db42a93083d1c1be749b998c507ea4ae8` |
| Current shared words | `a6a2be72455637870c66c17ee4feaf3fbb8d9880288798396e8b4c8218ab67db` | `9574c6a51bab4899efca1bf95f901bb04d71afd3ed3bca7f39db1dbc2c406ad0` |

The first variant uses donor-only word digest
`698e26d21c20eddcc25766317aa52024949f4eba51db99d73d58d46f6c5a12c1`.
The second uses current digest
`3e06014a398b03a9ccac58fa8c9ac57ba3c5a5312e39167b288c314cc6dee4f9`
and `AF_NPC_WORD_PROFILE=2`. Direct comparison finds exactly one changed record:
native `021A`, `brook trout` → `herabuna`. The corrected native species is already
installed in the translation; this is test alignment, not new translation work.

## Focused evidence

The first retained follow-up run passes 25 tests in 10.985 seconds:

```sh
PYTHONPATH=tools:tests python3 -m unittest test_mail_grading_patch test_mail_npc_patch test_resident_words -v
```

The affected display-name composition check separately passes in 2.112 seconds:

```sh
PYTHONPATH=tools:tests python3 -m unittest test_display_names.DisplayNameResourceTests.test_module_configuration_and_combined_item_resource -v
```

The initial capture/loader/shared run executes 23 tests in 8.978 seconds.
All six capture and six loader checks pass. Eight shared checks pass, but one
assertion and two installations fail: the test installs donor-only words while
current candidates require the corrected species profile. Its length expectation
also assumes 83 values over ten bytes; the actual corrected resource has 82.
Those are fixture/expectation mismatches, not evidence to accept mixed profiles.

After selecting the corrected fixture, all eleven shared tests and two existing
native-species source tests pass in 8.722 seconds:

```sh
PYTHONPATH=tools:tests python3 -m unittest test_shared_npc_words test_native_species.NativeSpeciesSourceTests -v
```

The shared source test checks all 352 values, exact resource identity, complete
donor agreement, and the single original-species exception with its native hash
and provenance. Every shared rejection case runs again with the now-valid
baseline, so a mismatched initial profile cannot mask later guard failures.
The source test independently rebuilds both word profiles from the three source
banks and confirms the one changed species, its dialogue, and current candidates.
Loader scenario generation reads the complete relocated bank; no emulator
execution is claimed by scenario generation.

Together these runs provide passing evidence for 51 distinct selected tests.
The seven historical errors closed are the display-name composition case,
grading class setup, NPC patch class setup, resident-word class setup, capture
artifact case, loader class setup, and shared-word class setup. The broader
suite is not rerun or declared passed. Other historical fixtures and unexecuted
gameplay/hardware acceptance remain separate work.

The unchanged V1RC4 SHA-256 is
`5930435f588947df35313ae9cc2ea301af9fc7e68d59a7d8e13a48741d4f3067`.
No saves, existing artifacts, or candidate ROMs are overwritten.
