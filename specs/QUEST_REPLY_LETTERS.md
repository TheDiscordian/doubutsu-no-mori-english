# Letter-quest replies

## Complete text and native meaning

`0075..00BC` are the 72 replies to the villager letter-writing quest, not the
ordinary background reply generator. The original selection is
`0075 + rank * 6 + personality`, with twelve ranks and six personalities.
`tools/audit_quest_reply_letters.py` binds five native functions and their
supplied English executable counterparts, the conversation result branch,
and all 216 complete header/body/footer parts. English wording, explicit
spaces, manual breaks, commands, and capitalization remain intact.

Every signature uses free field six for the sender's name. Six English bodies
use item field zero: `008D/008E/0092/0094/00B3/00B6`. Native `0098/00B8` also
name their gifts, while the supplied English wording does not insert the item
name; that exact source difference is retained. No GameCube-only selection is
added. Names capture the complete eight-byte approved villager identity, and
required item fields capture all sixteen bytes of the selected item name.
The original saved identities and gift IDs remain unchanged.

## Native ownership

The main-code creator `800BB86C..800BB990` clears a 164-byte letter, prepares
native name field six (six bytes) and optional item field zero (ten bytes),
formats the selected parts, copies the recipient, sets the NPC sender,
and sets received font zero, mail type zero, paper 22, and the selected gift.
Its original `FromRom2` call is at `800BB91C`; later ten/sixteen-byte copies
would overwrite a snapshot placed only at that lower-level call.

The delivery owner `800BB990..800BBAB0` resolves the recipient in the quest's
player identity at offset `0E`, maps the player's home, checks its owner, and
finds an empty slot among ten letters. Rank and gift come from quest offsets
`20/22`. Its 240-byte stack frame holds the complete letter at `sp+4C`.
The original creator call at `800BBA5C` ignores creation failure and copies
the result into the mailbox. The replacement checks success before that copy.
Eligibility, home mapping, slot selection, and the result return remain native.

The conversation overlay at VROM `008108C0`, linked `80918450`, calls the
delivery owner at `8091A9DC`. The verified result branch sets talk step `1C`
only for success, otherwise `1B` and message category `02A6`. This unchanged
branch must remain; isolated delivery tests do not establish complete quest
progression, cleanup, or retry through normal conversation.

Reward selection `800BB740..800BB86C`, grading `800BBAB0..800BBB30`, and receive
handling `800BBB30..800BBBEC` remain unchanged. The native grade retains length
boundaries 17/49, the score bonus of three, and the attached-item bonus of six.
The existing complete-body English grading integration remains at its shared
consumer. Reply creation never rolls a new gift or changes quest grading.

## Creator and wrapper

The optional `--quest-replies` creator extends the existing shop-notice
dispatcher. Its private eighteen-byte request uses the loader's existing
visitor input, with original player/animal identities supplied independently:
`AFQR`, rank byte, zero byte, gift BE16, eight zero bytes, marker 246, zero byte.
The loader's condition/origin arguments are zero/one. Ordinary visitor records
have personality `0..5` at the marker offset and retain their existing route.
No resident ABI, linked size, RAM reservation, or saved structure changes.

The shared guard rejects intersecting input/output/work/control objects before
descriptor reads. The creator checks reserved bytes, rank, identity, personality,
required gift, and all source resources. It captures complete English fields
before native short-field preparation, stages the original metadata, and
publishes only after the complete formatter and reader accept the snapshot.
Failure preserves the full destination and shared capitalization; disposable
workspace and native temporary fields are not saved retry state.

The replacement native wrapper uses 104 instruction bytes within the original
292-byte creator slot and a 64-byte stack frame. It validates the full incoming
rank before reducing it to a descriptor byte. The 52-byte copy gate replaces
`800BBA64..800BBA98`; a zero creator result reaches the original zero-result
return without copying. Both sections have an independent exact-word model,
checked against the Docker-assembled binary. All intervening owner code and
the remaining native grading/reward/conversation instructions stay unchanged.

## Integration and acceptance

`--english-quest-replies build/quest-reply-owners` requires the complete creator,
full item resource, and existing snapshot reader/catalogue dependencies. The
combined counter credits the 216 parts only after installed creator, owner,
catalogue/font, item-resource, and native-retention checks pass. Catalogue
presence alone gives no new credit.

Host tests cover all templates and capitalization states, complete item values,
every villager's name, all catalogue read failures, corrupted name resources,
rejected descriptors, aliases, retained output, and earlier creator routes.
Native acceptance must cover original metadata/temporary-field comparisons,
complete mailbox deliveries/readbacks, home/slot ownership, rejected resource
preparation, and unchanged quest/reward data. Normal conversation, saving,
presentation review, and original hardware remain broader acceptance work.
