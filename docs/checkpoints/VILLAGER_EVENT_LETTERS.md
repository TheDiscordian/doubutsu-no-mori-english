# Villager-event letter integration work record

The optional integration installs 54 complete supported letters: eighteen
friendship gifts, seventeen birthday cards, eighteen moving-away goodbyes, and
the Christmas card. Birthday body `00F6` still requires a semicolon. The
[specification](../../specs/VILLAGER_EVENT_LETTERS.md) defines the descriptor,
full selected names, native gates, and intentional Christmas initialization fix.

## Current artifacts

- Integrated ROM: `build/villager-event-letters-pilot/animal-forest-halfwidth.z64`,
  SHA-256 `e7b1fbae527e6ba033535388225eb97663cc72120715ba185f10c5670f4dc316`.
- Original-ROM UPS SHA-256:
  `0f80405d995ceea11fe4507c1cd8717b64ac9b774f75fe22c43d8dc385dfc286`.
- Creator: 28,256 bytes, SHA-256
  `032c3d455bd08c31d38e4ea6bcada3111bcd740e7a33a9d9566e0ffd51c85c02`.
- Relocations: 416 bytes, SHA-256
  `c6aa0b6113afefa289e962764734e5434db7c5fdededaf34bac7dd71f24af7c4`.
- Native scenario: `build/villager-event-scenario.json`.
- Native results: `build/smoke-villager-event-01/results.json`, SHA-256
  `5ef7ca4ac26c17162da1985ac89b75a4130b0ddba032b491c434971dd930f248`.
- Full regression: `build/tests-villager-event-regression.log`, SHA-256
  `e323de7c75e579e4544c2d115dd5e80548160a0d006996165fe816df7cafacda`.

Independent `build/villager-event-mail-creator` and
`build/villager-event-mail-creator-repro` images, relocations, and manifests agree.
The complete creator blob is 28,672 bytes; a call requests 34,031 temporary bytes
including unchanged workspace and alignment. The new dispatcher frame is 160
bytes. The common wrapper uses 48 bytes and Christmas uses 64 bytes. The resident
module remains unchanged at 24,288 linked bytes; no saved structure grows.
All 13,383 ordinary translation edits remain in the integrated ROM.
Independent comparison of all 3,382 DMA resources against the departed pilot
finds changes only in code, resident configuration, creator, and DMA metadata.
The metadata-containing resource changes only within its DMA table.

## Executed checks

Seventeen host creator tests pass in 16.342 seconds. They cover all 54 supported
templates in both capitalization states, plus all 216 full villager names in
each of three field arrangements. Complete metadata, snapshots, reconstructed
text, capitalization, source retention, and guards are compared. The inherited
ordinary NPC, Mom, and departed contracts run through the new dispatcher.
Unused gift-name lookups do not block bodies which omit that field. Invalid
descriptors, unavailable semicolon text, each catalogue-read failure, disabled
resources, and input/control aliases retain the promised output.

The same seventeen tests pass under AddressSanitizer and UndefinedBehaviorSanitizer
in 24.095 seconds (`build/villager-event-creator-sanitizers.log`). Five installer
tests pass in 4.843 seconds, covering complete source parts, all eight allowed
instruction ranges, publication failure destinations, goodbye success propagation,
atomic dependency/guard rejection, optional item imports, all earlier creator
variants, and the actual completed ROM. Independent assembly agrees across
188 common-entry bytes, 148 Christmas-entry bytes, three 48-byte mailbox gates,
two eight-byte queue gates, and the four-byte goodbye result instruction.
The assembly source SHA-256 is
`22e167e63de872fbab5a69382ab4747ad2c7de3ad856deed3dbc842fd4a31965`.

All 987 regression tests pass in 504.165 seconds.

The completed native batch compares complete native selection, gift,
paper, sender, recipient, temporary fields, and RNG with owned original function
copies, then checks actual publication and complete resident-reader output.
Original comparison copies retain native helpers; their three shared-creator
calls point to the owned original common function. No new creator code is
uploaded. The 4 MiB emulator is silent, uses fresh isolated saves, and has a
600-second bound. All 54 templates pass in both capitalization states: 108 native
comparisons and 108 complete delivered readbacks. Eighteen rejection cases cover
disabled resources, invalid ownership, full mailbox/queue, unavailable semicolon,
and missing required item names. Four resource-recovery retries reconstruct
completely. The batch executes 573 native calls and 1,955 internal memory
assertions, plus the resumed-checkpoint assertion (1,956 total). Live save memory,
globals, and heap accounting are restored. Shutdown is graceful; isolated Flash
and Controller Pak files retain their blank hashes. Direct calls do not establish
ordinary scheduling or original-hardware compatibility.

## Reproduction

```sh
python3 tools/build_npc_mail_capture.py --mother-letters --departed-letters \
  --villager-events --output build/villager-event-mail-creator
python3 tools/check_villager_event_assembly.py
```

Use the full [departed pilot recipe](DEPARTED_VILLAGER_LETTERS.md), change its
creator to `build/villager-event-mail-creator`, add
`--english-villager-event-letters`, and set output to
`build/villager-event-letters-pilot`. Generate the scenario with
`tools/villager_event_scenario.py --output build/villager-event-scenario.json`
and execute it through the silent smoke runner with a fresh output directory.
Generated donor text, ROMs, patches, resources, and results remain ignored.

## Remaining acceptance

The top-level goodbye pending-bit scheduler, ordinary event scheduling, queue
draining, real save/reload, old-save policy, and original hardware remain
unverified. Retained eligibility does not preserve exact template/gift/paper
draws across failed attempts. Complete the missing mail glyph path, other letter
creators, remaining general/item text, full review, patch-only release preparation,
title-first artwork, and GameCube-style keyboard within the full project scope.
