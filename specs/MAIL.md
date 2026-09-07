# Complete English mail

## Required result

Preserve complete English GameCube letter wording and intentional line breaks,
with correct recipients, senders, substitutions, gifts, delivery, storage,
editing, and save/reload. Shortening letters or truncating expanded text is not
the storage solution. Default letters, assembled villager replies, player-written
letters, NPC saved letter bodies, post-office storage, and message-dialogue
excerpts all require coverage.

## Verified native record

`Mail_c` occupies `A4` hexadecimal bytes, confirmed independently by the clear
and copy routines at `8009C384` and `8009C67C`. The content metadata starts at
`26`; the three text fields are contiguous:

| Field | Record offset, hexadecimal | Native bytes | English GameCube capacity |
| --- | --- | --- | --- |
| Header | `2A` | 10 | 24 |
| Body | `34` | 96 | 192 |
| Footer | `94` | 16 | 32 |

The N64 clear routine fills 122 bytes starting at `2A`. The classic handbill
wrapper supplies header length ten and footer length sixteen; the body loader
copies/pads at most 96 bytes. These instructions have exact mutation-tested
guards in `tools/audit_mail.py`. Some comments in the N64 header retain larger
field offsets; do not use those comments as native layout evidence.

The English GameCube capacities are defined by the pinned `m_mail.h` and used
through `mHandbill_Load_HandbillFromRom`. They do not imply that the N64 record
can accept larger text. The native `mMsg_Set_mail_str` has a separate 68-byte
message excerpt, while NPC-owned saved letters also copy 96-byte bodies.

## Native reference inventory

The executable/literal audit covers all pinned text segments and every DMA file.
It records full source hashes, call addresses, and surrounding instructions:

| Routine | Address | Direct calls |
| --- | --- | --- |
| Classic letter assembly | `80093F04` | 17 |
| Letter assembly with explicit header/footer sizes | `80093F54` | 3 |
| Header loader | `80093B28` | 2 |
| Footer loader | `80093C98` | 2 |
| Body loader | `80093DA8` | 2 |
| Composite NPC letter assembly | `800944B8` | 1 |
| Handbill free-string setter | `80092D10` | 54 |
| Message mail excerpt setter | `8009DA94` | 2 |
| Mail clear | `8009C384` | 39 |
| Mail copy | `8009C67C` | 30 |

No aligned literal pointers to these ten routines are found. This is not an
inventory of every inline field access or structure copy. Calls to the shared
memory routines, stack/static/persistent allocations, rendering, and editor
destinations still need their own proofs before changing the representation.

## Text-bank evidence

Native `super`, `mail`, and `ps` each contain 544 records, while the English
reference has 982. Among the 544 shared numeric IDs, raw encoded English text
exceeds the native field size for 170 headers, 490 bodies, and 251 footers.
Shared numeric IDs are not automatically approved semantic matches, and raw
encoded size is not final expansion size. The audit keeps GameCube-only records
and native-ID records distinct.

The five NPC composite banks each contain 384 records in both games. Their
parts are assembled before insertion; they are not independent 96-byte body
destinations. Candidate import cannot infer capacity from a part's ROM length.

## Storage and implementation work

### Independent control parser

Mail does not use the main-dialogue command dispatcher. Its 97-entry table at
`80107020` has only twenty non-null handlers: `24` through `2D`, and `36` through
`3F`, selecting the twenty handbill free-string slots. The table SHA-256 is
`5d956ef287b35240a4f6e09028618e43fe701b87ed8386b0b7f45cd35ba5700c`.
The audit checks the actual table, not a capability inferred from message code.

The dispatcher at `8009341C` leaves an unsupported command unchanged. The
conversion loops at `80093478` and `80093520` advance the cursor only for ordinary
text, so an unsupported command can stall conversion. This verified mechanism
does not establish the cause of any reported legacy crash. English reference
mail uses additional commands, including capitalization, which require their
own mail implementation even when main dialogue already supports them.

The build validator rejects unsupported commands in all eight mail banks.
Tests cover every opcode through `7A` for every bank, with main-dialogue runtime
features enabled, and compare all twenty handlers against the original ROM.
Wider imports and additional controls remain disabled until mail consumers
and persistence support them.

### Lossless representation

The representation is not chosen yet. Either a complete, lossless compact
representation or a fully migrated record/save layout must preserve all required
text. A display cache alone cannot preserve edited or delivered letters across
saving, moving, and restarting. Template references require saved snapshots of
all variable substitutions and coverage of every reader; they cannot silently
regenerate different random words or current names when an old letter is read.

Before enabling wider imports:

1. Inventory every saved, temporary, and copied mail destination, including NPC
   letters, mailbox/post-office storage, and travel data.
2. Trace actual assembly commands, random-word substitutions, header-name split,
   line fillers, and control-byte handling in both engines.
3. Prove the chosen representation preserves full English output and custom
   editor contents, with explicit versioning and unsupported-input rejection.
4. Implement and test native assembly, all display/editor consumers, gift and
   delivery operations, copying, old-save policy, and save/reload.
5. Exercise ordinary gameplay and the complete original-hardware matrix.

Until these checks pass, the audit does not authorize wider mail imports or
mark mail translation complete. Generated reports stay local at
`build/audits/mail.json`.
