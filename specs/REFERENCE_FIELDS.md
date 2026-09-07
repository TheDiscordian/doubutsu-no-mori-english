# Reviewed current-player and current-town text fields

## Why an approval is needed

GameCube often addresses the player by name or names the current village where
the Japanese text says you or this village. This can add `1A` or `2F` to an
otherwise matching message. The default importer rejects any new field: most
insertions depend on temporary actor-prepared values and cannot be assumed valid.

The `available_fields` approval is limited to individually reviewed current-player
and current-town insertions. It is not a general allowance for text fields,
catchphrases, free strings, missing native messages, or GameCube-only features.

## Verified native sources

The original main code has SHA-256
`2639d08d6a3de000fa270ebd3837f86d546041cd4a00d40fbf817a63f7b13810`,
VROM `00675720`, and RAM base `80051A80`.

`1A` dispatches to `800A1078`. The handler calls `8009EBB0` to add the native
six-byte colour wrapper and `8009EC88` to insert the actual name. Both read
the current `PrivateInfo` pointer at `80136FD8`; the first six bytes are the
current player's name. Trailing spaces are trimmed. The colour helper advances
the text cursor six bytes before name insertion and includes any following
native prolonged-sound glyphs in its colour count. The source structure remains
unchanged. Player initialization assigns this pointer at `800B8E14`.

`2F` dispatches to `800A1774`, which calls `8009F428`. The town-name getter at
`800950D8` returns the fixed current-village name address `80129E00`. The
inserter trims its six-byte field and replaces the command. The existing English
runtime returns after copying the name, at `8009F4A4`, omitting the Japanese
village suffix. This approval introduces no new runtime patch.

Neither source is an actor-prepared free-string slot. The reviewed batch consists
of resident conversations in a loaded village with a current player, not startup,
name entry, a destination-town request, or an arbitrary menu context. Other-name
and destination-town fields retain their distinct original sources. The local
GameCube `m_msg_main.c_inc` names the corresponding current-player and land-name
consumers; actual N64 instructions establish the sources used here.

Catchphrase `1C` has a different contract: the main handler passes the actor at
message-window offset `20` into the installed catchphrase reader. New catchphrase
requests remain withheld pending caller-context review; this permission cannot
admit them.

## Approval and preservation contract

Each `available_fields` record in `translations/reference_matches.json` binds
the original source, complete GameCube reference, exact set of added commands,
and complete adapted candidate hash. Only `1A` and `2F` are allowed. The generator
verifies the unmodified reference hash, including any original article-suppression
prefix, then uses the existing `reference_layout` adapter. It preserves English
wording, manual lines/pages, pauses, and corresponding original N64 actor values.

The builder derives a typed permission from the repository approvals, independently
of translation-file metadata. Validation rechecks the complete source/output
hashes, main-message/runtime/layout scope, and exact added-field set. Existing
flow, actor-command, format-argument, unsupported-command, and expansion checks
still run. The permission does not transfer through native aliases or combine
with controller, menu, actor-request, or multi-message-sequence permissions.

Twenty-six records are approved: `01A3`, `020C`, `0215`, `02C5`, `03DC`, `04C6`,
`0845`, `0865`, `0879`, `0908`, `0C8A`, `0D4E`, `0E49`, `1145`, `1546`, `16A3`,
`1811`, `1816`, `182E`, `1B57`, `1B5C`, `1B8D`, `2496`, `271E`, `2BE4`, and
`2D4D`. Individual evidence records their meaning and distinguishes current-player
or current-town mentions from other supplied names. Final review and ordinary
gameplay remain required; candidates are not completed review records.

## Deliberately withheld references

Reference field availability does not establish semantic identity. `119C` and
`27C0` replace native carp-streamer content with Harvest Festival material;
`11AC` and `180B` replace native moon-viewing content with meteor showers.
`11F1` and `14FE` replace unrelated native advice with GameCube tailor features.
`0945`, `1BD3`, and `1BD4` have different travel/storage rules or actions.
Those five records and the post-wait conversations `147F/14CF` have
[original native-specific drafts](NATIVE_ADVICE_TRAVEL.md), not added-field
permissions. The festival references still need native-specific translation.
Blank native slots and messages with other changed controls remain withheld.

## Batched validation

Host tests cover exact permissions, all 26 local source/reference pairs, stale
evidence, reference article prefixes, altered output, invalid schemas, wrong
banks/policies/runtime, additional unapproved fields, flow changes, overflows,
and independent builder rejection. Ordinary unapproved field insertions still
fail.

The native batch loads each complete message from the cartridge and dispatches
every newly approved field in that message. The test temporarily supplies a
six-character current-player name and a space-padded five-character current-town
name through their actual native sources. Complete resulting messages, headers,
colour spans, cursor positions, source retention, and buffer/module guards are
checked. Verified consumer instructions and the English town-suffix patch are
checked before and during the run. The checkpoint restores the temporary inputs
before ordinary execution resumes. These isolated insertions do not establish
normal actor traversal, save/hardware acceptance, or final visual polish.
