# Complete message-system diagnostic

The last inventoried Japanese dialogue-bank record, `0004`, has its complete
English translation installed through `0004 → 2AEB`. All 62 native commands,
manual line/page boundaries, repeated samples, and diagnostic instructions remain.
The [specification](../../specs/MESSAGE_DIAGNOSTIC_SEQUENCE.md) binds the complete
961-byte original translation and replaces only its existing `[416,421)` page
separator. The two expansion bounds, 713/886, fit the unchanged 1,024-byte buffer;
single-record installation still correctly fails at 1,581 expanded bytes.

`2AEB` has no native script, relevant code-immediate, or aligned data reference
in the pinned scan, and no conflicting explicit identity approval or sequence.
The complete candidate set contains 13,768 records. Reusing the reserve also
makes the English alias for `0487..0489` unambiguous: these three reserve labels
now read "Extra Space" from complete GameCube `0485`, instead of "Extra Area".
Their commands and accounting credit stay unchanged. Every other prior edit is
retained. No font, code, item/name/mail resource, saved structure, or memory bound
changes. Only message data, message offsets, and the DMA table differ from the
preceding rendering-diagnostic ROM. Original-ROM UPS reconstruction passes.

Six source/capacity/slot/ROM/accounting checks pass in 23.533 seconds. Combined
accounting adds only the complete `0004` root; all prior credit remains, the
source denominator stays 751,002, and no inventoried Japanese message-bank
record remains. This does not claim that other text banks or all game text are
finished. All seventeen sequence regressions pass in 29.051 seconds, fourteen
source/native-sequence/train-state regressions pass in 2.135 seconds, and the
frozen native-evidence check passes in 0.238 seconds without replay.

## Completed silent native batch

`build/smoke-message-diagnostic-01` completes 105 actions and 106 result records:
seventeen native calls and 51 memory assertions. Complete cartridge loads,
continuation target, both phases of continuing/final termination, actual loaded
message changes, and ordinary page setup pass. Both active-cancellation states
retain cancellation-enabled state. All twenty complete free fields, five native
item mirrors, and the mail field remain unchanged through both transitions.
Cursor/timer resets, neighbouring guards, stack/checkpoint restoration, blank
isolated FlashRAM/Pak, and graceful shutdown pass. No audio or screenshot is
produced. Frozen evidence verifies the source-bound plan without replay.

The private-window fixture does not execute the diagnostic's player assignments,
RNG, mail display, or sounds. It does not claim normal actor traversal, rendered
field expansion, save/reload, human review, or hardware acceptance.

## Reproduction and artifacts

Generate `build/message-diagnostic-candidates` with the complete seasonal runtime,
extended font, and all English string options used by the rendering-diagnostic
checkpoint. `bash tools/build_message_diagnostic_pilot.sh` builds the complete
cartridge. The scenario generator accepts the final `build.json` through
`--module`, so it verifies the installed runtime's final creator configuration
instead of an earlier unconfigured module manifest.

| Artifact | SHA-256 |
| --- | --- |
| Complete ROM, 33,554,432 bytes | `424eaf9ef301fe84cf0f7863b259c74a5c35054b115a0faef9e2da9096248cbe` |
| UPS, 4,493,696 bytes | `ff2cbe6480dd153ffd2abc9ac2635e6d6e5f43dadd2def082981b4eee08554d7` |
| Candidates | `8605f9db9757f7c876fefacd936a5be9154baafd26bb75446fb46b5524b128dc` |
| Native scenario | `d6c069d399a3451d7f816d908ea7f7ded629f538c9af205de4182138b4a84f42` |
| Native results | `9b58e38eecc179a2bbae599736cf10c5eb3c3f0944910379d4dfaf6700c0d01e` |
| Restored checkpoint | `59a6a62c560aadf476d5a68165a9112bf8162c37aad3da81ec9d9976103af3b4` |

Logs use the `build/message-diagnostic-` prefix: `candidates.log`, `build.log`,
`final-tests.log`, `sequence-regressions.log`, `native.log`, and `evidence-tests.log`.

## Continuing work

General strings, letter templates and their delivery paths, accented names,
complete-name callers, contextual review, save/gameplay acceptance, patch-only
release preparation, title-image replacement, and the GameCube-style keyboard
remain. Expansion Pak use is permitted; the actual build remains four MiB.
Do not replay this completed diagnostic batch while implementing those families.
