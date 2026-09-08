# Complete special-actor conversations

## Full English content

Eleven reviewed conversations use the existing all-or-nothing reference sequence
framework. Eight remain complete single records; three split only at an existing
English wait/newline/page-clear span. No English word, manual line, emphasis,
pause, or other page boundary is removed or reflowed. All expression tuples
occur in each root's own native source; no standing-resident or additional-actor
permission is used.

| Native root and continuation | Complete conversation | Expanded bounds |
| --- | --- | --- |
| `0723 → 072A` | Gracie's introduction, physique praise, clothing criticism, and fashion advice. | 490 |
| `0789` | Redd welcomes a returning customer and advertises rare stock, including the complete English truck aside. | 684 |
| `078D → 2B02` | Redd's dresser complaint, denial of coercion, buyer-blaming, flattery, and sales pitch. | 546 / 539 |
| `07AA` | Jingle's snowy holiday, delivering gifts/dreams, and farewell to finish tonight's work. | 844 |
| `09C8 → 09CA` | Sound choices, selected-setting acknowledgement, and the native next message. | 177 |
| `2401 → 2B03` | Gulliver's giant-squid story, disbelief, napping/jellyfish explanation, and gift. | 658 / 600 |
| `2402 → 2B07` | Gulliver's slippery deck, rescue, overseas joke, age-related interruption, and gift. | 691 / 375 |
| `2403` | Gulliver's sailor identity, uniform/fashion tradition, apology, and thanks. | 942 |
| `240B` | Gulliver's life at sea and repeated appearances on the beach. | 264 |
| `2ACF` | Rover offers to call the shopkeeper for the first resident without a home. | 472 |
| `2ADD` | Rover recalls the earlier resident and offers the same help to the next one. | 517 |

`072A/09CA` are original external destinations, not newly allocated records.
The three internal continuations use generic native reserve slots. Their full
unsplit English bounds are 1,067, 1,240, and 1,048 bytes respectively; adding
page clears inside one record would not reduce those storage/expansion bounds.

Redd splits at encoded span `[523,528)`, after the denial of forcing a purchase.
The squid story splits at `[635,640)`, after asking whether the story was invented.
The joke splits at `[668,673)`, after the duck begins speaking, before the
age-related interruption. Each gap is exactly `04`, newline, `02`. The first
part replaces that span with one native continuation boundary; the last retains
the original ending. Full source/reference/part hashes and complete ordered
coverage are mandatory. No source reference text is committed.

## Actor and ending boundaries

The supplied English localisations remain complete, including Gulliver's
Crusty Barnacle/jellyfish and unfinished duck/husky/cougar jokes, the uniform's
seafaring/fashion tradition, and Jingle's holiday wording. Native game actions,
event scheduling, gifts, player identity, and saved data are not changed to
match another platform. These are reviewed conversation identities, not a
blanket permission for different native dates, questions, or gameplay topics.

Only speaker-zero `09` expression tuples already in the exact native root can
be repeated, omitted, or repositioned to follow the English presentation.
Every other `08..0C` actor request retains exact native order and multiplicity.
This stronger independent guard also accepts every earlier approved sequence
without changing its payload. Native mood/duration, quest, handoff, and slot-nine
requests cannot be duplicated or dropped merely because the tuple is known.

The sound question retains `0074/0075/0076`, its wait and selection commands,
slot-nine `0001`, selected field `2E`, special expression `FD`, and `09CA`.
No sound setting is exercised or host audio played by the text test.
Rover retains the complete native town field and existing `FE` commands.
Gulliver's three gift-ending stories retain `01`, not an ordinary `00` ending.
The sequence test explicitly recognises these approved final endings.

## Continuation-slot evidence

`2B02/2B03/2B07` each contain the complete generic reserve label with normal
`00` ending and source hash
`b2c0b6f9facf02630f093fd1b6a5a6e47d722ecadd50e6c82fae305db4821e2c`.
They have no incoming native message-script target, matching arithmetic/
comparison/logical executable immediate, or aligned non-executable halfword in
the pinned executable-section inventory. Each approval binds its own exact slot.
This is not exhaustive proof against every indirect computation of a message ID;
normal actor progression remains required. Nearby `2B08`, which has data matches,
is not allocated, and actual save-menu messages beginning at `2B09` are untouched.

## Verification boundary

Five focused tests pass complete reference reconstruction, exact cuts and endings,
all part bounds, all-or-nothing installation, changed-payload rejection,
unchanged non-expression requests, and repeated slot-reference checks. The 110
reference tests and nine long-advice regressions also pass, including stale-source
rejection. All 12,569 installed payloads and the complete UPS reconstruction pass;
only the eleven roots and three designated reserve replacements differ from the
earlier candidate sets. Full/basic parts are identical.

`build/smoke-special-actors-01/` passes 278 recorded steps: 59 native calls,
51 expected returns, eighteen complete cartridge message loads, eight choice
labels, and 109 memory assertions. The independently regenerated scenario checks
every call/argument/return, full read, restored stack, internal/external
continuation, both ending phases, and one restored checkpoint. The complete
plus-glyph tip also loads successfully. Four-MiB configuration, silent graceful
shutdown, no seeded saves, disabled save-write flags, and blank FlashRAM/Pak pass.

No production runtime, font, native actor allocation, or saved format changes.
Normal special-actor traversal, expressions, gift/service outcomes, sound-setting
UI, final presentation, save/reload, and original hardware remain separate checks.
