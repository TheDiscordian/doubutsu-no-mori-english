# Postal and museum fixture follow-up

## Result and scope

Twenty selected checks pass across the postal and museum installer, scenario,
and historical-result tests. This closes ten errors in the retained
`build/v1rc1-regression.log`: three installer errors, one scenario setup error,
and one historical-result error for each family. Both counter-only failures
remain deferred. The full suite is not rerun or declared passed.

The errors came from applying current compiled-source checks to old pilot
creators. Production source, resource, and patch guards remain unchanged.
This batch changes test fixtures and evidence binding, not game code, English
content, saved formats, the playable cartridge, or the release package.

The current installation checks use the complete corrected base at
`build/v0-hardware-fixes-02`. They are not new RC4 native execution. Ordinary
mail scheduling, save/restart, and original-hardware acceptance retain their
existing unverified status.

## Fixture construction and retained assertions

Each installer test verifies the original ROM and binds the combined cartridge
to its build report. It checks all three already-installed patch ranges before
restoring just those ranges from the original code in an in-memory copy.
Reinstalling through the production installer must reproduce the complete
combined code exactly, retain every other resource, and match the build report.
No stored ROM is edited or reconstructed for this fixture setup.

Postal checks retain all fifteen supplied English header/body/footer parts,
full item names, used month fields, the common creator wrapper, both receipt
gates, seven original function guards, and atomic rejection of missing or
damaged dependencies. Museum checks retain all 81 parts, 27 templates, the
original fossil mapping and canonical sender identity, both publication gates,
the queue argument contract, and atomic rejection. Positive complete-cartridge
verification precedes malformed-report rejection in each family.

Fresh source-built postal and museum creator variants replace the obsolete
configuration fixtures. The existing current glyph/HRA-score creator provides
the preceding postal variant. Source inventories, exact configuration, entry
selection, and invalid option types remain checked. Old creator binaries and
reports are preserved; none receive replacement source hashes.

Separate historical-artifact test classes retain original-ROM UPS
reconstruction, all-resource comparisons, the exact two DMA-table changes, and
the 800-byte postal/736-byte museum growth expectations. Counter tests remain
in these historical classes without changed expectations and are not selected
for this batch.

Scenario-generation tests use the complete corrected base, preserving all
68 postal cases and 54 museum cases, full expected fields/text, original cache
helpers, changed-ROM rejection, and one restored checkpoint per scenario.
These tests construct cases; they do not execute the game.

Historical-result tests read the actual archived scenarios, pinned to the
previously recorded scenario and ROM digests. They bind the requested module,
catalogue, items where used, native comparison code, and guarded code ranges to
those exact cartridges, then independently reconstruct every expected case.
All existing result, call, stack, receipt, pending-loop, heap, state, save-file,
and shutdown assertions remain. Postal evidence retains 364 calls and 615
assertions; museum evidence retains 313 calls and 666 assertions. These are
audits of the preserved executions, not repeated emulator runs or evidence
that a different cartridge executed those cases.

## Reproduction

Build the fresh variants with the existing pinned public Docker toolchain:

```sh
python3 tools/build_npc_mail_capture.py \
  --module build/notice-seasonal-runtime/module.json \
  --words build/design-items-words/words.bin \
  --aliases build/npc-mail-names/aliases.bin \
  --output build/letter-runtime-fixtures-02/post-office \
  --mother-letters --departed-letters --villager-events \
  --academy-letters --academy-scores --post-office --mail-glyphs
python3 tools/build_npc_mail_capture.py \
  --module build/notice-seasonal-runtime/module.json \
  --words build/design-items-words/words.bin \
  --aliases build/npc-mail-names/aliases.bin \
  --output build/letter-runtime-fixtures-02/museum \
  --mother-letters --departed-letters --villager-events \
  --academy-letters --academy-scores --post-office --mail-glyphs --museum
```

Both builds complete with GCC 14.2.0 and
`ghcr.io/dragonminded/libdragon@sha256:b68e8dfd393f76ba69c1ba62da6b42dcda8b5b52eaa8fb96adc5aab7865a2d40`.
The earlier glyph fixture is documented in the
[system-letter checkpoint](SYSTEM_LETTER_FIXTURE_FOLLOWUP.md).
Select a fresh output directory when rebuilding; preserve these artifacts.

Executed focused commands:

```sh
PYTHONPATH=tools:tests python3 -m unittest \
  test_post_office_install.PostOfficeInstallTests \
  test_post_office_install.PostOfficeHistoricalArtifactTests.test_complete_rom_existing_resources_and_original_rom_patch \
  test_post_office_install.PostOfficeHistoricalArtifactTests.test_clis_reject_missing_dependencies_before_inputs -v
PYTHONPATH=tools:tests python3 -m unittest \
  test_post_office_scenario test_post_office_results -v
PYTHONPATH=tools:tests python3 -m unittest \
  test_museum_install.MuseumInstallTests \
  test_museum_install.MuseumHistoricalArtifactTests.test_complete_rom_prior_text_resources_and_original_rom_patch \
  test_museum_install.MuseumHistoricalArtifactTests.test_clis_reject_missing_dependencies_before_inputs \
  test_museum_scenario test_museum_results -v
```

Results: six passes in 8.776 seconds, four in 7.425 seconds, and ten in
22.235 seconds. No selected tests fail or skip. These timings exclude the
compiler builds. Do not repeat the unchanged completed checks.

## Artifact bindings

| Artifact | SHA-256 |
| --- | --- |
| Postal image, 31,504 bytes | `6487b8136390472e6429993fdcb051899258e9b376a86f25c695e7371a8f2996` |
| Postal relocation, 448 bytes | `019ea87f345781a9817c2f5854d7db6e90f2e05913d7a36aa280efd96fa1ace3` |
| Postal `overlay.json` | `2720e65545cfbe1f860a5a731e42519370d49a9e613f4315cd80dcc2b1da6780` |
| Museum image, 32,224 bytes | `7a26272c62434565bea8fb66c5b08baf2c25f26e836cb5213843acc4412c8f74` |
| Museum relocation, 464 bytes | `3ced3f5917255bfb19a4b12f9781d55b3b735c2b3394cdcd6e21d596be558d9d` |
| Museum `overlay.json` | `64c7c7372d16d340da0fea94176c19e9a87360a3ea3de3d004f3238069e20c02` |
| Resident module | `493bc25a922bbd9d321759677134520bbb179413985f0e047df45e6e432664c6` |
| Complete corrected base ROM | `b93a54b8804f262e1c05e7dabcd6aac4f5b47d637c69d94264f058c12dbdbd35` |
| Unchanged RC4 ROM | `5930435f588947df35313ae9cc2ea301af9fc7e68d59a7d8e13a48741d4f3067` |
| Preserved supplied RC2 save | `d489736e39abc7eff1c5b5085bf52e679186f2882a0247339e11603799b80b60` |

The original [postal](POST_OFFICE_LETTERS.md) and
[museum](MUSEUM_LETTERS.md) checkpoints retain historical cartridge, scenario,
and result hashes. Their broad continuation instructions are historical;
the current [queue](../WORK_QUEUE.md) governs remaining work.

## Next work

Continue relevant remaining letter/actor fixture failures, including snowman,
renewal/event, and Miko checks, without rerunning this completed group or the
entire suite. Keep percentage-tool expectations deferred. Prioritise any new
concrete playtest defect, remaining Japanese artwork, and the documented
ordinary gameplay/hardware acceptance work.
