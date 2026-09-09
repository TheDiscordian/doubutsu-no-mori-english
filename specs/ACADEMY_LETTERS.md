# Happy Room Academy letters

## Complete welcome and advice integration

The optional `--english-academy-letters` route installs all twenty welcome/advice
templates `01DC..01EF`, with sixty complete English parts. Their original and
GameCube field sets are empty. Complete supplied wording, manual lines, punctuation,
and header/footer positioning stay intact. The eleven series tips map to the
same N64 furniture series (exotic, lovely, classic, ranch, cabana, regal, blue,
modern, green, cabin, and kiddie); the other tips concern matching sets, rare
event/raffle furniture, useful placement, creativity, and neighbour trading.
No GameCube-only house feature is introduced by these letters.

`tools/academy_letters.py` binds the original creator/scheduler, supplied English
executable functions, selected immutable catalogue two or four, decoder, and all sixty source parts.
Catalogue presence alone does not count as installation. The creator is built
with `--mother-letters --departed-letters --villager-events --academy-letters`.
The existing resident loader and saved record layout remain unchanged.

## Creation and publication

The eighteen-byte synchronous descriptor has twelve zero bytes, template BE16,
zero gift BE16, marker `FB`, and paper 51. It uses the original sixteen-byte player
identity, null animal, condition zero, and foreign one. Native reply flags cannot
encode the marker as a valid personality. The dispatcher checks aliases before
session reads, validates the whole descriptor, builds privately, and copies all
164 bytes only after complete text and snapshot reconstruction succeeds. Metadata
retains the cleared sender, recipient, type six, and wing paper. The optional
score dispatcher handles score templates through its separate complete field path.

The 276-byte native `8009CC94..8009CDA8` entry becomes a bounded wrapper. Its
240-byte frame owns the temporary descriptor and whole letter, adding 24 stack
bytes over the original. Home index and full template arguments are checked
before narrowing. The original free-mailbox lookup runs before allocation or
creation; full homes return failure without publication. A successful complete
letter goes to the original selected mailbox slot. No queue policy is added.

The welcome continuation `8009CE2C..8009CE7C` tests success before setting the
membership bit and calling the native mark-date helper. Unused continuation
space holds a six-word conditional tail call at `8009CE64`. The hint completion
call at `8009CF94` uses that helper, so failed generation/full homes do not mark
the hint delivered. The original nineteen-way RNG and original eligibility/date
checks stay intact. A failed hint does not durably retain its random selection.

The GameCube hint rotation tracks previously sent advice and uses different
scheduling. Do not import its saved bitfield or probability into the N64 game.
The native N64 creator returns no success status and unconditionally advances
membership/date after attempted delivery; the new gates intentionally correct
that failure behaviour, following the supplied English welcome caller's intent.

## Score-letter continuation

The N64 score overlay is VROM `0081D9D0..00821740`, linked RAM
`809259E0..80929C30`, with entry `809281B8` and owner `80107B50`. Its caller
allocates, loads, invokes, frees, and marks the date. Complete score letters need
verified points, full item/series names, dates, and selected templates. Native
selection covers `0034..0048`; catalogue four retains the semicolon in `003D`. The N64 selector
has no GameCube house-model reward checks or gifts. Do not introduce GameCube-only
cottage `0220` or reward `0221/0222` templates. Preserve N64 scoring/selection and
propagate publication failure before clearing evaluation eligibility. The
[score-letter specification](ACADEMY_SCORE_LETTERS.md) records the installed path and acceptance limits.

## Verification and remaining work

All 21 host creator tests, sanitizers, five installer tests, and independent
assembly/build checks pass, along with all 1,013 regression tests. The silent native batch passes all twenty complete
letters in both capitalization states, all forty home/slot combinations, and
actual scheduler membership/date gates, resource failure/retry, full home,
duplicate prevention, input bounds, guards, heap accounting, and checkpoint
restoration. The [checkpoint](../docs/checkpoints/ACADEMY_LETTERS.md) pins results.
Normal gameplay, real save/reload, original hardware, and the
wider project remain incomplete.
