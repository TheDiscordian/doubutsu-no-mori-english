# Native designs and consistent species names

## Required native identity

Twenty-one source-bound original approvals in
`translations/n64-design-item-names.json` retain the native assembly podium,
fretwork table, four paintings, vending/washing fixtures, coin basin, three
garments, herabuna fish, danger paper, two floors, and two walls. Each approval
retains the exact source name/hash and pinned comparison-sheet row. The English
words are project-authored, not attributed to replaced GameCube objects.

The [JAANUS architectural glossary](https://www.aisf.or.jp/~jaanus/deta/f/fusen.htm)
supports the coin-form meaning of the native basin name. The native painting
adjectives are translated without swapping artwork or colliding with the
separately installed `fine painting` name. The original dress, tuxedo, sweater,
paper pattern, bathing-area designs, wood floor, and earthen wall remain.

Four source-bound GameCube matches in `translations/item_design_matches.json`
resolve the gym clothing. The native placed colour labels are reversed relative
to the carried labels. Actual conversion maps `17FC` to red `2414`, and `1800`
to blue `2415`; the exact catalogue model/texture references agree for each pair.
Preserve the distinct complete supplied `sweats`/`sweatsuit` wording in the
placed/carried fields. No global unequal-source alias exception is introduced.

## Herabuna correction across consumers

The native placed `1C2C` (`ヘラ`) converts to carried fish `2301` (`ヘラブナ`).
The [species reference](https://nookipedia.com/wiki/Herabuna) confirms that
GameCube Animal Crossing replaces this fish with brook trout. The source-bound
original name is `herabuna`, retaining the native species and the full romanised
name. Both unequal Japanese fields have independent original approvals.

This corrects an inherited complete-but-wrong English carried name. Coverage
does not increase for correcting a field already counted as English. The native
catch message and tournament response also require original translations:
`translations/n64-herabuna-dialogue.json` retains every native command, argument,
page boundary, and continuation target. The flat-shape joke, bass-only tournament
rule, and native cooking aside stay; the trout pun and replacement-species recipe
do not apply to this fish.

`tools/native_species.py` binds general string `021A` to its exact Japanese hash,
the exact replaced donor wording, and the original English correction. The
complete 352-word dialogue/NPC-letter resource changes only that one word and
its declared length/digests. Its IDs, family, slot, article, row width, allocation,
and the other 351 values remain unchanged. Provenance identifies original wording
while retaining the source alignment IDs and donor hashes as evidence.

The NPC creator selects one of two immutable word profiles at compilation.
The default retains the original digest; `AF_NPC_WORD_PROFILE=2` selects the
corrected herabuna digest. Each compiled initializer accepts only its selected
complete resource. The builder selects the flag from the verified resource hash.
The artifact validator resolves the digest argument actually passed by the MIPS
initializer and checks it against the embedded words, in addition to checking
the manifest. Shared-word bank installation requires the same
word profile in the verified installed creator; independently valid but mixed
profiles are rejected before bank publication. The new item/article profile also
requires the corrected herabuna word profile. Names, ordinary conversations,
dynamic letters, and catch/tournament dialogue must agree in the complete ROM.

## Names, grammar, and acceptance

The batch adds 74 formerly Japanese wider fields and corrects one previously
English field. All 18 newly fitting short fields enter native storage. The wider
resource contains 4,536 translated fields; eight accented name fields remain.
No other existing English name changes. Explicit articles accompany every
original name, and the rebuilt immutable article profile binds all names.

Only text/name data, creator word/article data and selected integrity digest,
and its resident CRC configuration
may change. Machine code, symbol offsets, relocations, reader, font, saved layout,
workspace, and memory bounds stay unchanged. Earlier immutable profiles may
retain their exact recorded generator and original-article approval hashes;
arbitrary source changes remain forbidden. Earlier name-resource reconstruction
must not be called correct when it contains the superseded brook-trout identity.
Only the exact conditional-digest C source change permits its pinned predecessor
for the original word profile; default recompilation must reproduce the original
machine code and complete image. The corrected profile requires current source.

Check every source, rotation/alias, complete name and capacity, intentional earlier
name correction, remaining accented fields, both builder rejections, exact word
resource reconstruction, shared-bank/creator coupling, unchanged code, full ROM/
UPS reconstruction, and combined text credit. Batch only new native loaders and
the corrected word/message paths; do not replay completed dialogue/letter tests.
Normal display, contextual review, save/travel/gameplay, release preparation,
title/keyboard work, and hardware evidence remain required.
