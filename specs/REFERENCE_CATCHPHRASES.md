# Reviewed resident-speaker catchphrase insertions

## Scope

Twenty-seven English resident conversations add a catchphrase where the native
wording has none: `036A`, `039A`, `03BB`, `03BF`, `0428`, `042D`, `0439`,
`0524`, `084A`, `0AE2`, `0F30`, `129D`, `16CA`, `1AEC`, `1E24`, `1F6F`,
`202D`, `2227`, `258B`, `25B9`, `25BA`, `25BC`, `2610`, `2703`, `271F`,
`282B`, and `2840`. Each complete native/reference pair has an individual meaning
record in `translations/reference_matches.json`; the legacy independently confirms
the reference wording. These are resident errands, greetings, questions, and
seasonal conversations, not actorless system prompts. Their ordinary traversal
and final wording/layout review remain gameplay and human-playthrough work.

## Native speaker chain

The original main CODE SHA-256 is
`2639d08d6a3de000fa270ebd3837f86d546041cd4a00d40fbf817a63f7b13810`,
VROM `00675720`, RAM base `80051A80`.

The local N64 decompilation `m_demo.c` retains the actor supplied to
`mDemo_Request`, copies the selected request to `demo->current`, and passes that
actor to its callback. Ordinary `wait_talk_start` passes `demo->current.actor`
to the message appearance request. Native `8007BF54` loads the actor from
`demo+E0`; `8007BF64` calls `8009D3E4`, with message ID supplied from `demo+300`.
An actorless event-message caller also exists at `8007C5BC`: not every message
has a villager speaker.

`8009D3E4` requests appearance with the supplied priority. On success it stores
actor, message ID, display-name flag, and colour at window offsets `2E0`, `2E4`,
`2E8`, and `2EC`. Initializer `8009FFB0` loads the complete requested cartridge
message through `8009E558`, then passes the stored actor and name flag to client
setter `8009D308` at `8009FFE8`.

The setter stores actor and flag at window `20` and `24`. Installed display-name
changes affect its getter and eight-byte width argument, not these stores. Null
input clears both fields. Handler `800A1124` reads precisely window `20` and calls
installed `af_copy_catchphrase` at `800A114C`. It does not use the player, quest
target, another named villager in the sentence, or a previous global speaker.

The existing [catchphrase resource](CATCHPHRASES.md) resolves that actor's native
animal identity and four saved phrase bytes into a complete English default.
Custom phrases retain their bytes; null actors produce empty insertions. No
saved structure, actor API, runtime instruction, or font metric changes here.
Corresponding local GameCube `m_msg_ctrl`, `m_msg_appear`, and `m_msg_cursol`
sources corroborate the roles; actual native instructions establish N64 offsets.

## Approval and preservation contract

`speaker_catchphrase` contains exactly `context: native_resident_talk` and the
complete `adapted_sha256`. Its containing record binds source, reference ID,
complete reference hash, and meaning evidence. Raw reference hashing includes
article-suppression prefixes; only the normal adapter removes supported prefixes.

The builder independently constructs a `SpeakerCatchphrasePermit` from repository
approvals, never translation-file metadata. Validation requires exact source/output
hashes, main dialogue, resident runtime, reference layout, and added-field set
`{1C}`. Other or redundant fields, new flow commands, oversized messages, and
different contexts fail. Current-player/town, controller, menu, actor-request, and
sequence permissions cannot combine with this approval. Aliases cannot inherit it.

English wording, manual lines/pages, emphasis, pauses, and corresponding native
actor values remain. There is no generic `1C` allowance or automatic reflow.
The other thirteen catchphrase-only rejections remain withheld for changed
choices/actor commands, blank native records, or different conversation topics.

## Batched validation

Eight host tests cover all 27 retail pairs, complete evidence, article prefixes,
schema/type/context/policy/runtime scope, exact added fields, flow/capacity checks,
and independent builder rejection. The full suite runs once for this validator
change.

`tools/reference_catchphrases_test_scenario.py` verifies original code and installed
consumers, then calls the real appearance request and complete initializer for
every candidate. It never writes requested/current actor fields directly. The
initializer performs cartridge DMA and client binding. Added catchphrases pass
through the actual dispatcher. Complete resulting messages/headers, cursor values,
and both complete actor/animal sources are compared.

Two different ten-character defaults exercise separate actors. The first complete
message additionally tests the other actor, custom `Yup!`, and a null request
clearing a previously assigned client. Fixtures leave over two KiB below the
native test stack for nested DMA calls. Message/window, fixture/stack, and module
guards are checked. A checkpoint restores all inputs before execution resumes.
The runner disables audio and uses isolated blank saves. These isolated calls do
not establish normal NPC navigation, page rendering, travel/save compatibility,
or original-hardware acceptance.
