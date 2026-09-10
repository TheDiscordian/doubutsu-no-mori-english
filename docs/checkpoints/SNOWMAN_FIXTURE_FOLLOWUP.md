# Snowman fixture follow-up

## Result

Eleven selected installer, scenario, and historical-evidence checks pass.
This closes five errors in `build/v1rc1-regression.log`: two installer errors,
two result-audit errors, and one scenario setup error. The Snowman counter-only
error remains deferred; the full suite is not rerun or declared passed.

The complete corrected base passes installed actor, immutable letter snapshots,
full-name resource, catalogue, font, reader, ownership, and relocation checks.
All twelve gifts, 36 English header/body/footer parts, both capitalization
states, and full sixteen-byte item fields retain their existing validation.
This is fixture and evidence maintenance, not newly translated text.
No production code, ROM, saved data, source approval, or release package changes.
No compiler or emulator is launched for this batch.

## Current fixture

The tests use `build/v0-hardware-fixes-02` and the existing compiled actor at
`build/shop-notice-snowman`. The actor image and relocation match the installed
files; its whole manifest matches the combined report and passes current source
validation. Compared with the original Snowman actor manifest, only the resident
module digest differs. The linked capitalization address, image, and relocation
remain identical. The approved artifact is reused without editing its manifest.

Installer setup verifies the original ROM and the combined ROM/report hash,
extracts the actual current replacements, additions, and VROM mappings, and
checks the installed actor against the source-built fixture. In memory only,
it restores the original 32-byte ownership metadata and removes the Snowman
replacement/relocation entries. Production installation must reproduce the
entire corrected base ROM, not just the actor. Other current text, resources,
readers, and relocation mappings remain present.

Existing negative checks retain changed text/code/source/snapshot rejection,
missing or damaged relocation rejection, duplicate relocation rejection,
dependency checks, and rejection before caller-owned maps change. A positive
complete installation check prevents these tests from passing merely because
their starting fixture is already invalid.

Historical artifact checks remain separate. They retain original-ROM UPS
reconstruction, every preceding file, exact ownership-only code changes,
original adjacent DMA-row ownership, and agreement of the two original actor
builds. The historical counter test keeps its original inputs and expectations
and is not selected for this batch.

## Historical native evidence

The result tests pin the exact archived scenarios and executed ROM to hashes
already recorded in the [original checkpoint](SNOWMAN_LETTERS.md). They bind
each scenario to its run report, actor and relocation, original comparison actor,
loader, native helper bytes, metadata, and module/actor reports. All 24 complete
expected letter records are reconstructed from the archived cartridge's real
catalogue and item resources, with each seed checked against the original RNG
calculation. The existing result, stack, guard, save-file, and cleanup assertions
remain unchanged.

`smoke-snowman-02` still has one failed foreign-player fixture assertion and
does not reach final cleanup. It is not labelled a successful run. Its completed
24 gift/capital comparisons and 48 readbacks remain documented separately.
`smoke-snowman-03` retains only its corrected edge-group evidence, matching-ROM
checkpoint relationship, state restoration, and graceful shutdown. Neither
audit is a new execution of the corrected base or RC4.

The native Snowman owner has no durable pending reward for allocation or
full-mailbox failure. This batch preserves that policy; it does not claim a
new retry guarantee, change saved bits, or infer normal scheduling/save tests
from injected calls or emulator checkpoints.

## Executed checks

```sh
PYTHONPATH=tools:tests python3 -m unittest \
  test_snowman_install.SnowmanInstallTests \
  test_snowman_install.SnowmanHistoricalArtifactTests.test_patch_retains_every_previous_file_and_changes_only_actor_metadata \
  test_snowman_install.SnowmanHistoricalArtifactTests.test_cli_rejects_missing_dependencies_before_reading_rom \
  test_snowman_scenario -v
PYTHONPATH=tools:tests python3 -m unittest test_snowman_results -v
```

The first command passes nine tests in 31.996 seconds. The second passes two
in 2.829 seconds. No selected tests fail or skip. Do not repeat this completed
group for unchanged code or resources.

| Artifact | SHA-256 |
| --- | --- |
| Current fixture ROM | `b93a54b8804f262e1c05e7dabcd6aac4f5b47d637c69d94264f058c12dbdbd35` |
| Current resident module | `493bc25a922bbd9d321759677134520bbb179413985f0e047df45e6e432664c6` |
| Snowman image, 18,384 bytes | `bdf537175e7b2b82ef20f82b3b5ece33c5020907d6f103668101ac41c717d084` |
| Snowman relocation, 1,104 bytes | `115c1fb48957d81471b428d7a2e943ee404ae91d5d04211bbe8a9752a4107097` |
| Current actor manifest | `a8d997b72c0c5f18404c58935ca874ec14b0526232fc9055254c5ebc558c13b6` |

## Next actor fixtures

A read-only follow-up verifies the installed renovation actor with
`renewal_actor.verify_installation` on the same complete corrected base, using
`build/shop-notice-renewal`. Its image is 7,488 bytes, with 44 relocation entries.
The manifest matches the installed report. The old test fixture still uses
outdated generation-probe/module approvals and needs a current composition.

The event actor also passes `event_actor.verify_installation` with the actual
combined overlay report and `build/shop-notice-event/creator-original.bin`.
It has 38,128 image bytes and 433 relocation entries. Passing the earlier
unextended `shop-notice-event/overlay.json` against the final actor correctly
rejects: the final actor includes the already-installed accented-mail adapter.
The actual report validates that adapter and its retained preceding actor.
This is a fixture/report selection issue, not a newly identified game defect.

Both early installers require the original snapshot-reader pair, whereas the
complete corrected base contains later letter-reader changes at `007908A0`
and `00792610`. The current resident image matches its raw module digest after
the documented configuration words are cleared in memory. Do not weaken the
installers' reader checks or substitute the earlier event report for the final
accented actor. Construct an explicitly pre-later-reader fixture through the
existing guarded reader/date installers, preserve separate full-current-actor
verification, and retain exact ROM reconstruction and atomic rejection tests.
These remaining actor tests are not repaired or counted as passed here.

The [current queue](../WORK_QUEUE.md) retains remaining fixtures, artwork review,
ordinary save/restart and gameplay checks, hardware acceptance, and patch-only
public-release requirements. Counter maintenance stays deferred.
