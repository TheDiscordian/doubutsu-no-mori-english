# Core runtime fixture follow-up

Eight test files select the verified `build/notice-seasonal-runtime` artifacts
used by the base rebuild recipe instead of the stale `build/runtime-module`
artifacts. Existing environment overrides, assertions, source guards, and
corruption checks remain intact. No runtime source, ROM, patch, or save changes.

The old module records 48 source files; the current module records all 60.
The missing files are `hboard_editor.c/.h` and the `notice/initial`, `notice/page`,
`notice/record`, `notice/seasonal`, and `notice/treasure` C/header pairs.
The two `mail/npc_loader` source hashes also differ. Rejecting that old fixture
is correct; production verification is not weakened to accept it.

The selected module is the unconfigured base fixture, not the final V1RC3
resident module. Its linked length is 24,576 bytes within a 32,768-byte
reservation. Verified SHA-256 values:

| Artifact | SHA-256 |
| --- | --- |
| `notice-seasonal-runtime/module.json` | `c5de2784fc1cbb12bd773c33713648e09f3716968ce3fbab1ddea34b48143f21` |
| `notice-seasonal-runtime/module.bin` | `493bc25a922bbd9d321759677134520bbb179413985f0e047df45e6e432664c6` |
| `notice-seasonal-runtime/bootstrap.bin` | `9c20b82708856897c19301bb23e35b84335482f9c10d4dd5ba5c3a3f7fb1d10f` |
| `design-items-resource/names.json` | `e13ea6b1f2b7bfbe2bf05bf367d4edb632e97cf0e475671fd05eaf5f58ae9828` |
| `design-items-resource/names.bin` | `ff138b625616f972118d66623804d509082d7f98d3e02704ccf8f99e1f283af3` |

Two composition tests also select the current 4,536-edit
`build/design-items-resource` used by the base recipe. The former `alias-items`
and alternate `mapped-items-final-resource` inputs fail the current item-name
provenance guard. The selected complete resource passes that unchanged guard.
Retained historical artifacts are not overwritten.

## Focused results

```sh
PYTHONPATH=tools:tests python3 -m unittest test_runtime_module test_catchphrases test_extended_items test_mail_catalog test_mail_view test_runtime_layout test_dialogue_dates test_birthday_fields -v
```

This run executes 69 checks in 23.112 seconds: 67 pass, and two composition
checks reject the old item resource. After the item-fixture correction, only
those two affected checks run again:

```sh
PYTHONPATH=tools:tests python3 -m unittest test_catchphrases.CatchphraseResourceTests.test_resource_configuration_and_mutation_guards test_mail_catalog.MailCatalogTests.test_installer_binds_registered_resource_and_all_configuration_words -v
```

Both pass in 3.361 seconds. Together these results provide passing evidence for
the 69 selected checks; the whole eight-file group is not claimed rerun after
the final two path corrections. Checks include portable C bounds, resource
configuration/corruption, bootstrap layout, letter snapshots, guarded instruction
replacement, and dialogue/birthday dates. No emulator or hardware execution is
claimed by this batch.

Five errors from the [historical full regression](V1RC1_REGRESSION.md) are closed:

- `ModuleRetailTests.test_module_artifacts_guards_and_insertion`.
- `CatchphraseResourceTests.test_native_scenario_uses_unsigned_o32_arguments_and_restores_checkpoint`.
- `CatchphraseResourceTests.test_resource_configuration_and_mutation_guards`.
- `ExtendedItemResourceTests.test_installation_requires_exact_resource_and_module`.
- `MailCatalogTests.test_installer_binds_registered_resource_and_all_configuration_words`.

The full suite is not rerun or declared passed. Other historical actor/capture,
generation, resource, and accounting failures retain their recorded unresolved
status. Counter maintenance remains deferred. V1RC3 is unchanged.
