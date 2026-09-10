# Renovation, event, and fortune actor fixture follow-up

## Result

All sixteen selected actor-installation tests pass. This closes six errors in
`build/v1rc1-regression.log`: the installation/reconstruction and installed-actor
errors in each of the renovation, event, and fortune test classes. No full-suite
pass is claimed, and counter-only expectations remain deferred.

The tests now use current source-built dependencies and explicitly distinguish
an early installation stage from the complete corrected base. Production
installers, reader checks, source approvals, relocation checks, allocation
limits, and payment/receipt safeguards remain unchanged. No gameplay code,
translation, ROM, saved data, or release package changes. No compiler or emulator
is launched in this batch.

## Why the old fixtures failed

The old renovation/event pilot reports point to generation probes built against
earlier source/module approvals. Their installers correctly reject those inputs.
The old fortune fixture likewise fails current resident-module checks. These
are not failures of the actual installed actors: all three complete actors
verify on `build/v0-hardware-fixes-02` with their corresponding current reports.

Simply pointing the early installer tests at the final cartridge is not enough.
The early installers require the exact original snapshot-reader pair. Later
letter-reader changes replace that pair in the final cartridge. The event actor
also includes an accented-mail adapter absent from its earlier source-built
predecessor. Neither change may be discarded from the actual playable build or
accepted by weakening an installer's required inputs.

## Test composition

`tests/current_letter_actor_fixture.py` constructs only in-memory test stages:

1. Verify the original ROM, the combined ROM/report digest, the current resident
   module, the actual installed actor, and its source-built dependency.
2. For the event actor, validate the complete accent adapter and recover its
   verified predecessor. Require that predecessor's code, relocation, and report
   to match `build/shop-notice-event`, including the explicit creator offset.
   The other two source-built actors must match their installed files/reports.
3. Construct the early snapshot reader through the production guarded reader
   installer. Independently verify the actual current reader variants through
   `verify_reader_files` before composing the earlier test stage.
4. Assemble an expected installed-stage ROM independently of the actor installer.
   Compared with the real corrected base, only reader files `007908A0` and
   `00792610` may differ; the event fixture also uses its pre-accent actor and
   relocation. All other current replacement/addition maps remain intact.
5. Restore only the selected actor's original ownership metadata and DMA
   mapping. Renovation/event receive their required source-checked date patches;
   fortune restores the native unmodified actor by removing its replacements.
6. Run the real installer. Its output must reconstruct the entire expected
   in-memory ROM, preserve additions, and change only owned code/actor/relocation
   entries. Invalid inputs must leave all caller-owned maps unchanged.

The temporary test-stage ROMs and adjusted installation expectations are not
playable candidates or full-build reports for publication. They are never saved
to disk. Separate tests verify each actual final actor on the unmodified
corrected base; the final event test explicitly retains the accent adapter.

## Retained coverage

The renovation tests retain complete native relocation/profile checks, all
fixed-data imports, the failure gate's correct return-address target, original
ownership/mail helper guards, and exact date-patch composition. Missing
catalogue/reader/date inputs, occupied addresses, changed metadata/helpers,
stale modules, and damaged relocations reject atomically.

The event tests retain native calls/profile pointers, zero-initialized owned
work and pending storage, internal jump relocation, original gate targets,
source/import/entry/bounds checks, and the same atomic dependency rejection.
The current saved pending-flag semantics and their documented compatibility
limits are unchanged; host installation checks are not a new pending-save test.

The fortune tests retain the 8,192-byte native overlay limit, separate relocation
scratch bound, 2,400-byte actor-instance limit, complete phrase data, callback and
charge-call relocation, and native payment/lifecycle helper guards. Damaged
source, ownership, phrase, profile, import, and relocation data reject. The
installation test also checks complete ROM reconstruction, in addition to its
existing replacement-map checks. This does not establish a new ordinary paid
reading or interrupted-payment gameplay result.

## Executed checks

```sh
PYTHONPATH=tools:tests python3 -m unittest \
  test_renewal_actor_install test_event_actor_install \
  test_fortune_actor_install -v
```

Sixteen tests pass in 43.139 seconds, with no failures or skips. An earlier
ten-test renovation/event pass completes in 20.602 seconds before adding the
fortune branch and final-reader verification. Those ten are included in the
final sixteen, not counted again. Do not repeat this completed batch for
unchanged code or resources.

## Artifact bindings

The fixture cartridge SHA-256 is
`b93a54b8804f262e1c05e7dabcd6aac4f5b47d637c69d94264f058c12dbdbd35`.
The current resident-module digest is
`493bc25a922bbd9d321759677134520bbb179413985f0e047df45e6e432664c6`.
Existing source-built directories are `build/shop-notice-renewal`,
`build/shop-notice-event`, and `build/shop-notice-fortune`; no reports are edited
to make an old binary appear freshly compiled.

| Artifact | SHA-256 |
| --- | --- |
| Renovation image, 7,488 bytes | `505ccc28bec929eed6753fe57f303ad7d6d43e4dd68d4261e34a2c1d546e6e70` |
| Renovation relocation, 208 bytes | `65aa1240de288c60bd4ad1c664ca0380ea289240f3a8ddd205d728c89cc6efb5` |
| Renovation manifest | `d112c9ec65cf43ba472d28a90448f365aa6c8ec6a8c445cf5fc6f0f9861f0e42` |
| Renovation creator, 3,116 bytes | `377a0d30fe5b132cc9dcb653dbed9a94352b5e50fec537e33226e28283ab10d0` |
| Pre-accent event image, 38,128 bytes | `13c5977cc07b8ee08bd2d0c4ac9bfd5b6a975854e9dbb0982124ef2a3950dca2` |
| Pre-accent event relocation, 1,760 bytes | `3bc6ec21a36ff20aac4b52634e271d8b59181fee9e466415abfb6e385a51d9f7` |
| Pre-accent event manifest | `2c0e3ad89fbc5295632480c738e5d8dadaaea8bbc6ed28fe0daaac81da81eccc` |
| Event creator, 3,732 bytes | `f17016964a2d3c5b9a819a287a2dcc8b5ce4374e6cb9f8e8fcf95e7b6d1f6b0c` |
| Installed accented event image | `8fcde6e3c4b2fb84c956e92043637091209c901f8d493c1cea5484aebe842e2b` |
| Installed accented event relocation | `5e87254084e743ef9dbc0d4b4d7bc9faede2a8f2b7623ade973f210033a9011c` |
| Fortune image, 8,048 bytes | `296988c24fa2ec610e93dcd0c941add0e968c386b2184853da230076ef9fc338` |
| Fortune relocation, 336 bytes | `a17f3346fb9e6f43af816a0fd96415785922a44f05e243579be63ff6872f7ff6` |
| Fortune manifest | `91f68aa3c1a1121152d826ec83e14945ff185606600c545bc68ad12bbd2028fa` |

## Remaining work

Continue the relevant remaining source/resource fixture errors, including the
leaflet-date installer and fortune resource/string tests. Preserve this completed
actor group and its shared test composition. Percentage-tool work remains
deferred. Ordinary mail scheduling, payment/refund interactions, save/restart,
hardware acceptance, further artwork review, and public-release requirements
remain in the [current queue](../WORK_QUEUE.md). No historical injected-call
evidence is relabelled as a new execution of the corrected base or RC4.
