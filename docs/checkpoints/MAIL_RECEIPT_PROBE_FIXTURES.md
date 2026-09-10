# Receipt, generation, shared-word, and date fixture follow-up

Eighteen focused checks pass. This closes four errors and two assertion failures
from the retained [full regression](V1RC1_REGRESSION.md), without changing
production validators, game code, translations, ROMs, or saved data.

## Corrections

`test_pelly_receipt` selects verified `build/notice-seasonal-runtime`, replacing
its obsolete resident fixture. The unchanged grading resource remains
`build/mail-grading`. Seven checks pass: pocket restoration prerequisites,
both reason-indexed lookups, relocation retention, allowed instruction ranges,
complete appended English errors, and atomic rejection of damaged dependencies.
This closes the historical class setup error.

The mismatched shared-word-profile case moves from historical-cartridge
`NativeSpeciesInstallationTests` to the existing source-built `SharedWordTests`
fixture. The historical fixture's obsolete source inventory caused rejection
before the intended profile check. The test now first proves the complete
matching composition passes `verify_consumers`, then verifies the other valid
word profile fails for the intended reason. Both calls must leave replacements,
additions, and module metadata unchanged. The corrected herabuna profile and
all source guards remain. This closes the historical assertion failure, not
the separate native-species accounting case.

`test_mail_generate_probe` selects a freshly compiled generation-only program
bound to the current module. Six checks retain source/import validation, entry
bounds, synthetic jump relocation, unknown-target rejection, alignment, and
memory limits. This closes its historical actual-artifact error. No production
generation hook or enabled game feature changes.

The date-inventory tests construct their two scoped cartridges in memory with
`add_runtime_module`, `dialogue_dates.install`, and `leaflet_dates.install`.
This replaces obsolete recovery/leaflet pilot fixtures whose unrelated mail
creators fail current source guards. All four date tests pass, closing two
historical errors and the masked unknown-target assertion failure. The original
expected caller identities/counts and all rejection assertions remain intact.
No production audit or installation guard changes.

The base test composition intentionally has ten resident date calls and thirteen
native calls. The leaflet composition has seventeen resident calls, two verified
English hour-body calls, and four native calls. These are partial test-fixture
expectations, not remaining-Japanese counts for RC4. The malformed month call
must fail for its unexpected day-formatter target, and a changed hour body must
fail despite retaining its original address. Both unmodified compositions pass.

## Build and test evidence

Module digest:
`493bc25a922bbd9d321759677134520bbb179413985f0e047df45e6e432664c6`.
Shared creator: `build/shared-npc-capture-runtime-followup-01`, retaining the
[preceding checkpoint's identities](MAIL_RUNTIME_FIXTURE_FOLLOWUP.md).
Grading image/manifest digests:
`ad74645e6ea19f864e697db220e614194eb01e52ceacdc90e3cce77722f80513`
and `09ac2eebccc3e57a54273f11db67f21aa04c5907566918d6228bb1c433c7d935`.

```sh
python3 tools/build_mail_generation.py --module build/notice-seasonal-runtime/module.json --output build/mail-generation-runtime-followup-01
```

The new 1,420-byte program has SHA-256
`5a87bb5f30aaee9ee32a56a088398673853587bbde616d43b261abd396aaf205`;
its `generate.json` has SHA-256
`cd6e7064a9845f981c9aeca5e97907b5dacd69d279a4474bb5078b32c9ae3590`.
Compiler: GCC 14.2.0, existing public image
`ghcr.io/dragonminded/libdragon@sha256:b68e8dfd393f76ba69c1ba62da6b42dcda8b5b52eaa8fb96adc5aab7865a2d40`.
The original fixture is preserved; reproduction uses a fresh output directory.

The unchanged `build/leaflet-dates/hour.bin` has SHA-256
`eeb382edeeda4fb8ab3f7c070118a40ae224ee647b5a36b17294c924bec3bfaf`;
its manifest has SHA-256
`d85b051dc59b58350f75c294cb8c438151e69cebdd0eccc02a16d5887e3bae23`.
The full hour code/source checks pass during fixture construction. Older pilot
ROMs remain preserved; these generated in-memory fixtures are not new playable
RCs or replacements for ordinary date/calendar acceptance.

```sh
PYTHONPATH=tools:tests python3 -m unittest test_shared_npc_words.SharedWordTests.test_shared_bank_rejects_mismatched_valid_creator_word_profile test_pelly_receipt -v
PYTHONPATH=tools:tests python3 -m unittest test_mail_generate_probe -v
PYTHONPATH=tools:tests python3 -m unittest test_date_caller_audit -v
```

The first command passes eight checks in 9.388 seconds; the second passes six
in 0.006 seconds; the third passes four in 15.225 seconds. These are host/build
checks, not fresh native receipt/delivery/date execution or hardware validation.
Other generation variants, postal/museum/
actor fixtures, and counter-only failures remain separate work. The complete
historical suite is neither rerun nor declared passed.
