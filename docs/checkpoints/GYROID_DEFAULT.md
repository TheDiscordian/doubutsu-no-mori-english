# Home-gyroid default integration checkpoint

The [default-message specification](../../specs/GYROID_DEFAULT.md) identifies
the four complete GameCube strings actually selected by both initialisation
paths: `076A..076D`, 92 bytes with their three separating newlines. The older
same-ID `055C` concatenation has different third-line wording and no manual
line separators, so it is not the correct full presentation source.

Native creation still loads `055C` into a 64-byte saved field, and the existing
resident formatter writes a 68-byte display field. The resident linked image
is exactly `6000` bytes; it has no remaining linked room. The native Haniwa
routine supplies its owner-message pointer at `sp+20` and selects `0928` for
other-owner messages. This provides an actor-owned selection point without
changing the resident allocation or saved structures.

`overlays/gyroid_default/default.c` recognises only an exact 64-byte original
default requested through `0928`. Every differing byte and every other request
is retained unchanged. Three host tests pass in 0.134 seconds, including all
16,320 single-byte customisations, unaligned inputs, and unchanged sources and
surrounding guards. The original comparison data is extracted from the supplied
cartridge into temporary test data, not committed as a game asset.

## Installed cartridge

`build/gyroid-default-pilot` contains the complete integrated ROM and UPS. The
206-byte `2AE7` variant substitutes only the introduction's one `40` insertion
with the 92-byte complete four-line default. Ordinary `0928`, every pause/page
boundary, owner field, and outgoing `0929` remain. Candidate and builder flags
require the complete pair; a typed exact-hash permission does not grant arbitrary
reserve or control changes. The reserve-label approval is reconciled only in
enabled builds; its source/reference approval file is unchanged.

The 6,976-byte actor adds only 176 bytes: 76 bytes of selector instructions,
36 bytes of adapter instructions, and 64 original comparison bytes. The adapter
retains its 24-byte frame; the selector has no frame. There is no new BSS or saved
storage. Only the native final call changes; its original table-load delay slot
remains. All 105 original relocations keep their order, with four added rows.
The 464-byte relocation file and actor retain their adjacent native DMA indices
at new VROM `03938000` and `03930000`. Main metadata `80100DD0` updates the
four DMA/allocation words while preserving profile and ownership fields.

Independent Docker builds in `build/gyroid-default-actor` and
`build/gyroid-default-actor-repro` agree on code, relocation, and reports. Exact
machine-word checks and relocation at three allocation bases pass. Eleven
focused host/source/actor/cartridge/accounting tests pass in 36.422 seconds;
seventeen sequence regressions pass in 28.612 seconds. Tests reject changed
payloads, permissions, source hashes, code, relocation, and actor-only installs.
They verify UPS reconstruction and complete prior-resource retention. The only
candidate change is `message:2AE7`; the candidate count remains 13,768.
Combined accounting credits original `string:055C` once through the verified
complete actor/text pair, without duplicate reserve weight or denominator change.

| Local artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| Complete ROM | 33,554,432 | `6501f5275dae76ab8f6cf00e3b7dfaae37f5bfdc0f352946ba1408f68424f8c7` |
| UPS | 4,502,119 | `f3d5fd94ab847397d97d01af5e120852cd49e96f88d4a05bf573918d99626508` |
| Actor | 6,976 | `42243f21e9ca3eea9af41ec6e0b993af2511eda844c9f40f7c43cbf5c10c9c3d` |
| Relocation | 464 | `734a1d3c2d8d32b30044a6ea311fbfa082b6856958fae5ccc8b0683e65931586` |
| Candidates | 11,723,945 | `eb2e0a256e0286541cfe51368c50a34c754e7ba583a83d80d71fef634d65b351` |

The pilot wrapper keeps all current item/creator/notice/letter dependencies:

```sh
python3 tools/build_gyroid_default_actor.py
python3 tools/reference_candidates.py \
  --rom 'local/rom/Doubutsu no Mori (Japan).z64' \
  --output build/gyroid-default-candidates --english-runtime \
  --runtime-module build/notice-seasonal-runtime \
  --extended-font build/mail-font-cartridge --english-dialogue-dates \
  --english-fortunes --english-resetti-replies --english-shop-units \
  --english-resident-words --english-shared-npc-words --english-credits \
  --english-gyroid-default
bash tools/build_gyroid_default_pilot.sh
```

## Native acceptance and next work

The source-bound native plan is `build/gyroid-default-scenario.json`, generated
by `tools/gyroid_default_scenario.py`. Its executor loads the actual cartridge
actor/relocations through `800262D0`; it does not upload production instructions.
It exercises selector/adapter requests, custom-byte changes, native demo
eligibility, the complete original other-owner path for all four homes, both
message loads, and the original continuation. Guards, live actor ownership,
saved RAM, heap, globals, and checkpoint restoration are required.

The first isolated attempt, `build/smoke-gyroid-default-01`, stops at a fixture
expectation for custom text after passing the native selector cases and the
first real default/custom owner pair. The test expected trailing padding spaces
to stay unwrapped. The established formatter correctly inserts a newline when
their measured width passes its boundary; the observed hash equals the existing
host formatter's result. No production code changes are needed for that result.
The corrected `build/smoke-gyroid-default-02` batch completes successfully:
112 calls and 133 assertions across 261 result records. It passes all 64 native
one-byte customisation cases, eight selector/adapter request IDs, null selector
input, all four demo-eligibility states, eight actual default/custom routes
across four homes, and complete `0928`, `2AE7`, and `0929` cartridge loads.
The real native owner decision and table-load delay slot execute unchanged.
All saved bytes remain intact through each owner call; fixture saves/globals,
heap usage, live ownership, stack/buffer guards, and the checkpoint are restored.
The run shuts down gracefully with blank FlashRAM and Controller Pak. This is
controlled native execution, not normal interaction, saved persistence, or hardware.
Earlier completed native batches are not replayed.

| Native evidence | SHA-256 |
| --- | --- |
| Plan | `de92345355006f5673fd692acb0faa7f7c61ff84331e2154984f6a111b72015f` |
| Results | `0f024263da89bf716dd1d96eb9a52b5ece519ab9408299a95ec5d79039719def` |
| Checkpoint | `979e2a91b0e2085a234079aab8b6d51b56423db70451363fb2a5d1f3424879aa` |

`tests/test_gyroid_default_results.py` checks the frozen evidence and regenerated
source-bound plan without replay. The final combined gyroid test run passes all
twelve tests in 35.615 seconds. Eighteen formatter/placeholder regressions
pass in 33.926 seconds. Their stale fixture references now select the current
resident module and include the already-installed diagnostic's `2AEB` reserve
and 72 sequence parts; no production behaviour changes for those corrections.
Logs are `build/gyroid-default-{actor-build,actor-repro,candidates,pilot-build,
integration-tests,sequence-regressions,retained-regressions,native-complete}.log`.
The final test logs are `build/gyroid-default-final-tests.log` and
`build/gyroid-default-evidence-tests.log`.

The owner-message editor remains the next implementation task. The original
Japanese default stays in saved storage and must not appear as the finished
English default in that editor. Preserve explicit input limits, custom text,
cancel/confirm semantics, and existing saves; do not truncate the 92-byte default
or silently shorten edited text. The supplied GameCube actor's
`aHNW_talk_with_master2` selects `mSM_OVL_HBOARD` for this editor, and
`aHNW_menu_open_wait` opens it with the house index as its second argument.
Reference sources are `local/ac-decomp/src/game/m_hboard_ovl.c` and its header;
these are leads for binding the native editor, not proof that its layout matches.
Do not mistake the generic name-entry overlay for the owner-message editor.
Normal gyroid interaction and actual save/reload
are still required. The broad goal remains active: other general/letter text,
accented names, full-name callers, review, gameplay/save validation, patch-only
release, and title/keyboard work continue. No hardware validation is claimed.
