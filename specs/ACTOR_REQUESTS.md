# Retaining native actor requests in English dialogue

## Native semantics

Message controls `09` and `0C` address different parts of the actor-order table.
They are not interchangeable emotion commands. The five-byte encoding is
`7F opcode index value_hi value_lo`.

The original main code has SHA-256
`2639d08d6a3de000fa270ebd3837f86d546041cd4a00d40fbf817a63f7b13810`,
VROM `00675720`, and RAM base `80051A80`. Its table at `80107CB8` selects
`800A0984` for `09` and `800A09E4` for `0C`. Those wrappers pass row four and
row nine respectively to the shared helper at `800A08F8`. The row arguments
are explicit instructions at `800A0990` (`24060004`) and `800A09F0`
(`24060009`).

The helper calls the parser at `8009DF90`, whose inner routine `8009DF1C`
extracts the one-byte index and big-endian sixteen-bit value. The setter at
`8007B44C` bounds row and index to `0..9`, reads the table-object pointer from
`80104A70`, and writes a halfword at `object + 0x10 + 20*row + 2*index`.
The helper advances the message cursor by the native command size.

The local GameCube decompilation provides corresponding names in
`m_msg_cursol.c_inc`, `m_msg_main.c_inc`, `m_demo.c`, and `m_demo.h`:
`mMsg_Main_Cursol_SetDemoOrderNpc0_ControlCursol` selects `mDemo_ORDER_NPC0`
(four), and the quest wrapper selects `mDemo_ORDER_QUEST` (nine).
`mDemo_Set_OrderValue` stores a sixteen-bit value in the selected row/index.
Native machine instructions, not these names alone, establish the N64 writes.

## Individually approved adaptations

Twenty-five favour/task-response messages have confirmed complete English
references but use native `09` requests where GameCube uses `0C`. Each approval
preserves the original N64 request and value; it does not translate a GameCube
request number by a shared lookup. For example, the reference value `0068`
corresponds to different original native values in different records.

The reviewed IDs are `02B8`, `02B9`, `02BA`, `02BC`, `02BE`, `02BF`, `02C0`,
`02CA`, `02CB`, `02CD..02D2`, `0452..045A`, and `11D1`. They cover disappointment
after a failed favour, accepting an apology, reassurance after a difficult task,
and anger after rejected advice. The English wording is independently confirmed
by the supplied legacy reference; the approval evidence describes the native
and English meaning individually. This is not blanket approval for all quests.

`native_actor_request` in `translations/reference_matches.json` binds the
complete native source, reference ID/hash, unique five-byte reference request
at an exact offset, exact original native request, and complete final candidate
hash. Only `0C` to `09`, index five, is admitted by this schema. After that
replacement, the complete actor-command sequence (`08..0C`) must equal the
native sequence. Missing, additional, reordered, or altered other requests fail.
Controller and choice adaptations cannot share this permission.

Normal flow, field, command, and capacity checks still run. Complete GameCube
wording, lines, pages, pauses, and other presentation commands remain subject
to the existing reference-layout policy. The builder independently checks the
final payload hash, regardless of translation-file metadata. All outputs remain
candidates requiring final review, not automatically completed translations.

## Batched verification

Host tests cover exact replacement, changed source/reference content, wrong
offsets/values/opcodes/slots, duplicated requests, other actor-command changes,
invalid approval schemas, all 25 retail inputs, and the independent build guard.

`tools/actor_request_test_scenario.py` loads each complete approved message from
the built cartridge, dispatches its actual native request through `800A21C0`,
and checks the full order table and adjacent guards. A temporary scratch table
receives the native row-four/index-five value; the separate quest row remains
unchanged. The native handlers, parser, setter, and dispatch entries are checked
against the verified original code before and during execution. The whole
machine checkpoint is restored before ordinary execution resumes.

These isolated calls test actual dispatch and request storage, not subsequent
NPC action selection, friendship changes, animation, or normal quest traversal.
Those checks belong to the combined gameplay and final human-playthrough pass.
There is no production runtime, saved-layout, font, or reflow change in this batch.
