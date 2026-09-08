# Complete references with original random responses

## Contract

Four complete English references differ only in the random branch's number of
entries after normal presentation adaptation. `263E/2646/2650` repeat their
positive response in the GameCube three-entry command; `26C5` repeats its
second response. The N64 scripts use their original two-entry `13` commands.
Keep those complete native commands, including destination order and repeats,
without importing GameCube response weighting or changing the runtime.

An explicit `complete_reference.native_random` approval binds the complete
native source, supplied English reference, and final output hashes. It requires
exact native/reference command offsets and one complete `13` or `14` command
in each record. Both must have the same destination set, and the commands must
differ. Replace only that reference command with the actual native command.
Every English character, newline, page, wait, emphasis, and pause remains.

All other gameplay commands `08..19` must already match the original exactly
after replacement, before the ordinary adapter. No new actor request, menu,
conditional branch, missing destination, or changed terminator is permitted.
No other content adaptation or approval permission combines with this rule.
Normal text-field, command, buffer, and source checks remain. The builder
independently requires the complete approved output regardless of edit metadata.

The rule does not identify topics automatically. Every approval requires review
of the question and connected responses. Native `2769`, whose third destination
differs from GameCube, is deliberately outside this contract. Unknown flow
controls and command-only reachability review remain separate work.

## Reviewed conversations

| Question | Original responses | Retained meaning |
| --- | --- | --- |
| `263E` | `263F/2640` | Greeting praise, or speak louder with a retry. |
| `2646` | `2647/2648` | Old-fashioned greeting praise, or speak louder with a retry. |
| `2650` | `2651/2652` | Sleepy bedtime acceptance, or a more heartfelt greeting and retry. |
| `26C5` | `26C6/26C7` | Denying responsibility for rain, or training to become the sunshine boy. |

The four conservative expanded bounds are 58, 58, 59, and 127 bytes.
Each connected response already has an English candidate. Native friendship,
mood, retry, selection weights, and branch destinations remain unchanged.

## Verification boundary

Require schema/offset/length/destination rejection tests, unique token-aligned
spans, complete reference retention, unchanged gameplay commands, both source
and output hash guards, ordinary candidate validation, and cartridge loading.
Production runtime, font, resource formats, and saves are unchanged. Ordinary
conversation selection, mood progression, rendered presentation, and hardware
are separate gameplay/playthrough checks.

Eight focused random-reference tests pass within the 104-test reference group.
The native content batch loads all four complete questions and all eight
connected replies from the cartridge, alongside fifteen native-specific drafts
and their other replies/labels. The combined 57-call/137-assertion batch passes
with complete text, guards, one restored checkpoint, silent shutdown, and blank
isolated saves. It loads the original branch commands without executing the
random selection routine; native selection behaviour is retained by leaving
both its source commands and runtime implementation unchanged.
