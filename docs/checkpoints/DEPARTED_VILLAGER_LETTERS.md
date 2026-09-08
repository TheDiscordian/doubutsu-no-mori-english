# Departed-villager integration work record

All eighteen classic letters `00FC..010D` have complete English creation and
native queued receipt. Full villager names, player/town fields, donor newlines,
spacing, and capitalization commands are retained. The
[specification](../../specs/DEPARTED_VILLAGER_LETTERS.md) defines the input
descriptor, native patch boundaries, and retry limitations.

## Built artifacts

- Integrated ROM: `build/departed-letters-pilot/animal-forest-halfwidth.z64`,
  SHA-256 `b4135c8447cc6a55cbef5bea154518e26fd1f310aa1162547fd8d51908a7a414`.
- Original-ROM UPS SHA-256:
  `94a56338fae24aec2005923eadb4486880a9ab64ed26d46111127a92a9bd7ecc`.
- Creator image: 26,656 bytes, SHA-256
  `7b8eea11ce95501d3c22a0073f86633b2ab44e72d2a893a3184ab387255b3de6`.
- Relocation section: 320 bytes, SHA-256
  `1449a6ed42f350f872abc5ff368bb076e76325caaeb4303bab5e2ce748f089cb`.
- Scenario: `build/departed-letter-scenario.json`, SHA-256
  `6c0a4459de996205c5bfee71155873abd3eccea98a5cb52caa1827093b9f30ea`.
- Native results: `build/smoke-departed-letters-01/results.json`, SHA-256
  `2610ccd1e4c08858cce1f16a38d33e4012c10002fa97e2235adb30a78c6ba602`.
- Native helper SHA-256:
  `fc7c9e021e90560b4961605d106de006a0103badd3bfd2b59b8fc699e98df805`.
- Silent runner SHA-256:
  `63853e83cd91a7587628793f2dff7e44f71c544958dedd32174667c4faddf58a`.

Independent `build/departed-mail-creator` and `build/departed-mail-creator-repro`
images, relocations, and manifests agree. The complete blob is 26,976 bytes;
with unchanged workspace and alignment, a call requests 32,335 temporary bytes.
The departed dispatcher frame is 152 bytes; its native wrapper frame is 48 bytes.
The resident module remains 24,288 linked bytes with source-module SHA-256
`2399b8cad820cf83f8d1d9c36c58633703facba4f12b3835a2637e43487faef6`.
No saved structure grows. All 13,383 ordinary translation edits remain installed.

## Executed checks

Thirteen host creator tests pass in 7.273 seconds. These include all eighteen
templates in both capitalization states and full English names for all 216
villagers: 252 departed-letter cases. They compare all 164 metadata/snapshot
bytes, complete reconstruction, capitalization, field order, and retained inputs.
Inherited Mom and ordinary NPC creator tests run through the extended dispatcher.
Invalid descriptor/IDs/source resources, all catalogue DMA failures, disabled
catalogue, invalid personality/paper/floating values including NaN, and aliases
are covered. The same thirteen tests pass with AddressSanitizer and
UndefinedBehaviorSanitizer in 11.074 seconds, recorded in
`build/departed-letters-sanitizers.log`.

Six creator-relocation tests pass in 0.104 seconds, including the narrowly
validated aligned read-only `LWC1` constant references. Six installer tests pass
in 2.642 seconds. They bind all 54 complete parts, verify allowed changes and
both failure destinations, preserve legacy variants, reject dependency/guard
faults atomically, and verify the actual integrated ROM. Independent assembly
matches all 376 creator bytes and 52 publication-gate bytes. Its patch SHA-256 is
`6dbd3ed4cc5e3e3471f82b588b25182b9cf31e6a2a6e0af4951e6806ef676b43`.

The silent native batch compares all eighteen selections in both capitalization
states with the original creator. Native metadata, all temporary fields, final
RNG words, source private data, and unrelated save memory agree. All eighteen
templates enter the native queue and reconstruct through the installed resident
reader; successful delivery clears only the remembered-villager record and the
native staging record. Duplicate delivery is rejected after that clear.

Six rejection cases cover disabled catalogue, mismatched owner, full home, full
queue, visitor, and invalid villager ID. The disabled-catalogue retry succeeds
without resetting the RNG and clears the remembered villager only after receipt.
The test verifies the retry's complete letter within the same personality group;
it does not claim an identical selected template or paper across failed attempts.

The batch records 177 calls, 473 helper memory assertions, and one resumed-state
assertion: 474 total, with no failed assertion. Allocation accounting, code and
stack guards, live-save restoration, global restoration, checkpoint resume, and
graceful shutdown pass. The creator and resources load from the cartridge; only
the original 376-byte comparison function is uploaded into owned test memory.
The 131,072-byte FlashRAM remains all `FF`; the Pak retains its blank-fixture hash
`ab2a6e04fd3ceb36594f1216c888a1b8bd0a3ba0a94f715a7c7601e98c49ec51`.

The full regression batch passes all 965 tests in 474.374 seconds, recorded in
`build/tests-departed-letters-regression.log`, with a successful process exit.
Its log SHA-256 is
`0aa190136eaa0fc2f6de925e42ec7d1be0d8eab2e895424a053682c220c8bfd3`.
Independent comparison of all 3,382 DMA files with the Mom pilot finds changes
only in native code, resident configuration, the optional creator, and the DMA
table itself. The table-containing file changes only inside the DMA table range.
Every other resource, including all ordinary text banks, remains unchanged.

The next villager-event source check verifies 165 parts across 55 templates:
54 complete reference letters and one birthday body requiring the semicolon.
This check does not install the next route or add applied-translation credit.
The [next-batch specification](../../specs/VILLAGER_EVENT_LETTERS.md) records the
shared creator, selected gift/name sources, native caller boundaries, and
Christmas gift difference.

## Reproduction

Build the creator with `tools/build_npc_mail_capture.py --mother-letters
--departed-letters --output build/departed-mail-creator`. Run
`tools/check_departed_assembly.py` for the independent native patch comparison.
Use the full [Mom pilot recipe](MOTHER_LETTERS.md), changing its creator directory
to `build/departed-mail-creator`, adding `--english-departed-letters`, and setting
the output to `build/departed-letters-pilot`.

Generate `build/departed-letter-scenario.json` with
`tools/departed_letter_scenario.py --output build/departed-letter-scenario.json`.
Execute it with `tools/emulator_smoke.py`, that pilot ROM, a new isolated output
directory, the configured Xvfb binary, and `--seconds 400`. The emulator is silent
with 4 MiB RAM and no Expansion Pak. All generated assets, ROMs, patches, and test
results remain ignored. No user save or physical hardware is used.

## Remaining work

- Normal departed-villager scheduling, queued-mail draining, real save/reload,
  old-save acceptance, and original hardware remain unverified.
- Retained remembered-villager identity does not preserve exact template/paper
  selection across attempts; failure does not roll back native random draws.
- Continue birthday/Christmas and other letter creators, complete remaining
  general/item text, and supply missing mail glyphs without shortening wording.
- Full review, batch gameplay/save validation, human playthrough, patch-only
  release preparation, title-first artwork, and GC-style keyboard remain in scope.
