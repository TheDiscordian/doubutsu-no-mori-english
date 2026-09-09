# Complete words shared by resident dialogue and NPC replies

## Source and identity

The shared import contains all 352 complete English values from the eleven
native thirty-two-entry reply families. The complete canonical resource digest
is `698e26d21c20eddcc25766317aa52024949f4eba51db99d73d58d46f6c5a12c1`.
Every value agrees with both the supplied English source and the complete
legacy value. Commands, empty values, changed order or identity, changed source
hashes, shortened values, and values exceeding sixteen bytes are rejected.
Generated reference text remains in ignored local build directories.

Five families also feed ordinary resident dialogue: `01E5`, `0219`, `02F4`,
`0314`, and `0334`, each with thirty-two entries. Fish map from native `0219`
to English `06A1`; insects map from `01E5` to `0679`. The other nine mail
families retain their verified identities. The additional eight GameCube fish
and insects are not imported into the random pools, and no draw is repeated.
See the complete [reply-word resource](NPC_MAIL_WORDS.md).

## Consumer requirements

Ordinary dialogue requires the complete [resident-word patch](RESIDENT_WORDS.md).
Its sixteen-byte temporary and item fields retain each full value; the three
outer preparers keep the native tables, field slots, and random draw counts.
All 136 separately scoped resident values must also be installed. No additional
resident code, stack, BSS, saved layout, or persistent allocation is introduced.

The mail preparer keeps its original ten-byte temporary and compatibility
fields. Eighty-three shared values exceed that capacity. The complete creator
captures each original selected ID, resolves its full sixteen-byte word from
the verified resource, and publishes a complete English snapshot letter. The
temporary prefix is never treated as the complete letter field. The catalog,
snapshot reader, all eight capture calls, complete creator blob/configuration,
and exact submission failure gate are mandatory together.

The source audit binds seven original mail functions and six dispatch/selection
tables. An aligned-literal scan across the original DMA files and a direct-jump
scan across pinned executable sections find only these creator entry references:

| Target | Native entry references |
| --- | --- |
| Composite wrapper `800A8B84` | Good-reply call `800A8F0C` |
| Field preparation `800A8C48` | Good/bad calls `800A8E48`, `800A8F6C` |
| Good reply `800A8DB4` | Metadata dispatch pointer `8010B894` |
| Bad reply `800A8F30` | Metadata dispatch pointer `8010B890` |
| Metadata creator `800A9028` | Submission call `800A915C` |

The submission call is redirected to the complete cartridge creator. The
verified saved-catchphrase and special-name tables do not select any shared
word ID. These scans establish the listed references in the verified revision;
they are not a general proof excluding arbitrarily computed function pointers.

## Two-phase installation

`--english-shared-npc-words` requires `--english-resident-words` and
`--runtime-module` in both candidate generation and ROM construction. The ROM
builder additionally requires `--npc-mail-generation` and that option's complete
runtime, reader, catalog, and grading dependencies. Generation remains opt-in.

1. Validate the complete source-bound group, then defer all 352 ordinary-bank
   replacements. Apply the other translations and consumer patches normally.
   The intermediate bank retains the original shared words, and the intermediate
   applied count excludes the deferred group.
2. Install and verify the complete cartridge creator and all its dependencies.
3. Independently check the installed module, reader, catalog, creator, eight
   capture sites, failure gate, and ordinary actor. Reversing only the approved
   mail patches must recover all seven original functions and six tables.
4. Require every deferred entry still to equal its original source. Rebuild the
   existing relocated bank and offsets with all 352 complete values; retain
   every other entry and every native ID. Publish both files only after every
   check succeeds, then add 352 to the applied count.

There is no generic capacity exception in the text validator. Without the flag,
normal generation retains its earlier results; the complete group cannot be
applied through the ordinary short-entry validation path. Unknown actor patches,
missing or changed resources, duplicate installation, a partially replaced
intermediate group, or changed module code must fail without publication.

## Validation scope

Host checks cover complete source agreement, explicit fish/insect mapping,
group corruption, CLI dependencies, deferred publication, unchanged unrelated
entries, and failure of each required installed consumer. Cartridge scenario
generation reads the actual relocated general-string data without clipping it
to the Japanese bank's original size.

The combined native batch covers all 288 ordinary random words: the earlier
128 plus the 160 shared words. It also covers all three real outer preparers,
four shop levels, complete message insertion, native RNG, actor/stack/heap
guards, and save retention. A separate checkpoint in the same batch exercises
48 original NPC metadata comparisons, eight successive complete letters, and
eight rejected creator calls using cartridge-loaded code and resources.

The shared-word host suite passes all 851 tests. The dialogue portion passes all 288 random
words, six outer preparations, 118 complete message loads, 447 insertions, and
1,896 helper assertions across 926 calls. Its checkpoint restores. The current
glyph-capable creator separately passes all 48 original comparisons, eight
successive complete replies, and eight rejections in its matching-town fixture.
All 245 calls and 539 assertions pass, with live save/heap/global retention,
checkpoint restoration, blank cartridge/Pak saves, and graceful shutdown. The
earlier fixture's capture rejection is not reproduced; its cause remains
unproven. The [current checkpoint](../docs/checkpoints/MAIL_GLYPH_CREATORS.md)
binds these results to the actual ROM. Direct creation is not ordinary delivery.

Normal
villager interactions, creator-to-receipt and pending-loop integration, semantic
review, ordinary saving/travel, presentation, and original hardware remain
separate acceptance work. The title artwork stays the first image task after
the main port; the approved font metrics and paused atlas investigation stay
unchanged.
