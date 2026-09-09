# Complete HRA score letters

## Source-bound scope

The original N64 scoring overlay selects twenty-one templates `0034..0048`.
All sixty-three Japanese/English parts have verified identities and field sets.
Twenty complete letters are installed through the optional score creator and
native scheduler gates; body `003D` needs the semicolon path. Reference extraction
alone does not credit text. The translation counter verifies the actual installed
creator, scoring overlay, relocation resource, and scheduler before crediting
the twenty complete templates.

The scoring overlay is VROM `0081D9D0`, 15,728 bytes, SHA-256
`9e42076944c8684c0220f442cb03c60d4ae485c15658a7fa761091f34fcb196b`.
Its adjacent relocation resource `00821740` is 1,024 bytes, SHA-256
`1696efd5639209dc45a2531679a04422aeb44c839644613c97c8397d15a6dc7b`.
Sections are 10,704 text bytes, 5,024 data bytes, no read-only section, and
1,248 BSS bytes, with 248 relocation entries. Linked memory spans
`809259E0..80929C30` (16,976 bytes). Signed low address halves are significant:
the entry is `809281B8`, not `809381B8`.

| Native function/data | Address | Verified role |
| --- | --- | --- |
| Series-name copy | `809259E0..80925A5C` | Copies ten bytes from one of 55 series rows |
| Letter choice | `80925BB8..80925D1C` | Original three-way draw, score/room/bit selection |
| Item choice | `80925D1C..80925D54` | Prefer nonzero base item, otherwise theme item |
| Name length | `80925D54..80925E48` | Native forward/reverse length operations |
| Score letter | `80925E48..809260A4` | Six field preparations and mailbox/queue receipt |
| Scoring entry | `809281B8..809283B0` | Evaluates the room, then invokes the letter creator |
| Series names | `80928458`, 550 bytes | 55 fixed ten-byte Japanese names |
| Letter bits | `80929628`, eight bytes | Current evaluation selection bits |
| Letter table | `80929630`, 256 bytes | 64 signed template values |
| Selected series scratch | `80929740` | Original static ten-byte series destination |

The first three table rows choose `0034..0041`; fallback chooses `0042..0048`
by points and room size. Small/medium/large rooms select `0043/0044/0045` below
20,000 points; the default also selects `0045`. Remaining thresholds are
70,000 and 100,000. The GameCube table adds cottage `0220`; its selector also
adds house-model rewards `0221/0222`. None belongs in native N64 selection.
The N64 creator clears the gift and does not award either GameCube house model.

## Complete English field capture

| Field | Meaning | Required English width |
| --- | --- | ---: |
| 0 | Comma-separated points, leading-space aligned | 10–13 |
| 1 | Selected base/theme item | 16 |
| 2 | Selected furniture-series name | 16 |
| 3 | Evaluation year | 4 |
| 4 | Evaluation month | 9 |
| 5 | Evaluation ordinal day | 4 |

All bodies use points and year/month/day. Only `0037` uses item field one;
only `003A/003B` use series field two. No header/footer uses free fields.
Full supplied wording and manual line placement remain unchanged. English
fields must come from full resources, not widened writes into ten/two-byte
native locals. Prune fields omitted by the chosen complete body.

The 55 N64 series rows map in order to the first 55 supplied English rows.
This is verified against the native copy/table and supplied executable table,
with explicit series identities reviewed. Donor spelling remains unchanged,
including its shortened category names. The last five GameCube series are not
imported as N64 IDs. Keep generated Japanese/English table bytes ignored.

The supplied `mFont_UnintToString` routine inserts comma separators. Its 428
bytes have SHA-256 `b1daafc049aa5cbe1a25c47f9aef50a4a43e0e077acbf003e16f68f86d0cf484`.
The English score caller requests ten characters with leading spaces. Values
that require more than ten characters after comma insertion expand to thirteen
instead of losing leading digits. This deliberately corrects the donor's fixed
ten-character overflow, while retaining ordinary score alignment. Signed-negative
points reject. Valid dates cover 1901–2099, with Gregorian leap/month bounds;
invalid dates reject rather than clamp. All manual template line breaks remain.

## Optional creator and descriptor

`--academy-scores` requires the complete advice/event/departed/Mom chain and
exports `af_academy_score_mail_create`. The existing resident loader ABI and
configuration layout remain unchanged. A new call uses the eighteen-byte remail
argument as the following big-endian descriptor:

| Offset | Bytes | Value |
| --- | ---: | --- |
| `00` | 4 | Nonnegative native score |
| `04` | 2 | Selected base item, otherwise theme item |
| `06` | 2 | Zero reserved |
| `08` | 2 | Evaluation year |
| `0A` | 1 | Month |
| `0B` | 1 | Day |
| `0C` | 2 | Original selected template |
| `0E` | 2 | Zero gift |
| `10` | 1 | Marker `FA` |
| `11` | 1 | Original paper 51 |

The player argument is the original sixteen-byte identity, condition is zero,
and foreign is one. The animal argument borrows the native ten-byte selected
series. Its existing twelve-byte overlap checks remain conservative; only ten
bytes are read. It is required only for `003A/003B`. Marker `FA` cannot name a
valid native personality. Other markers delegate to the earlier creator chain.

The 55 native/English series pairs occupy 1,430 bytes plus ten zero alignment
bytes in the on-demand creator. The full 1,440-byte resource has SHA-256
`be1258e1806e2a5e38a64cad52863c632d45b4610685ec9590dd264bb1569a38`.
The installed image and its manifest bind this table. The creator rejects missing,
unknown, or ambiguous required series names. Only `0037` requests the full item
resource; unusable item data does not reject unrelated templates.

Output/work/control/resource overlap checks run before writes. The private
5,344-byte workspace is cleared after preserving its input session. Full field
capture and complete snapshot/reader validation precede publication of all 164
letter bytes and the final capitalization value. Sender fields, recipient,
zero gift, font zero, type six, and paper 51 retain native meanings. The original
200-byte handbill temporary strings stay untouched: this complete owned capture
replaces their six old preparations, rather than widening those native fields.

The linked creator has 32,512 image bytes and 560 relocation bytes. Each call
requests 38,431 bytes including workspace and alignment. The score dispatcher
frame is 144 bytes. Only 256 image bytes remain below its 32 KiB image limit;
the complete blob is allowed to include a separately bounded relocation table.
The resident module stays at 24,288 linked bytes. No saved structure grows.

## Native publication and failure propagation

The score wrapper replaces only `80925E48..809260A4`, using a 256-byte frame
instead of the original 272. Arguments retain home arrangement index, points,
room size, the native series pointer, and the two item IDs. The original
`mMkRm_DecideLetterNo` performs the choice and RNG draw. Current date and private
player come from `80136FBC` and `80136FD8`.

Complete creation precedes the original mailbox copy or queue submission.
The wrapper returns delivery success in both `v0` and `v1`. The surrounding
scoring entry retains the original evaluated points in `v0` and propagates
delivery in `v1`. Its twelve-byte invalid-player guard rejects both negative and
out-of-range players and returns zero points/success without evaluating a room.
Every scoring instruction outside that guard and the letter wrapper is retained.

The resident scheduler changes only `8009CF28..8009CF6C` in addition to the
required welcome/advice installation. It calls the allocated scoring entry,
saves `v1` in unused original stack space, always invokes the original overlay
free helper, and calls the existing conditional mark-end helper with delivery
success. Failed creation/receipt therefore retains house-update eligibility and
the previous evaluation date. Successful delivery uses the original mark-end
routine. The original scoring allocation, cartridge load, home selection, queue
policy, and reward behaviour remain.

Only four obsolete internal-call relocations are removed (`440004C8`,
`44000524`, `44000540`, `44000560`); the original selection call moves to
`440004B8`. The resulting 245 entries occupy the unchanged 1,024-byte adjacent
resource. All section sizes, VROM identities, BSS, and actor ownership remain.
Independent relocation models check three four-MiB addresses, including signed
low-half transitions. Independent assembly checks the 604-byte wrapper,
twelve-byte invalid-player guard, and 68-byte scheduler patch.

Failure does not retain the exact chosen RNG draw. A later attempt reevaluates
and selects using the original logic. This is eligibility retention, not durable
selected-template recovery. Queue rejection can follow successful local creation;
in that case the complete creator's transient capitalization result remains,
but no mail or evaluation date is published.

## Validation and remaining work

The 25 host creator tests include all earlier dispatch contracts, every supported
score template, both capital states, all 55 series, all 366 days of a leap year,
numeric/date bounds, missing resources, retries, and overlapping inputs. The
same tests pass under AddressSanitizer/UndefinedBehaviorSanitizer. Five installer
tests check exact owned changes, immutable scoring data, relocation differences,
atomic rejection, CLI dependencies, and both HRA verifiers against the real ROM.
Independent creator builds and independent native-patch assembly agree.

`tools/academy_score_scenario.py` and `tools/academy_score_smoke.py` exercise
native cartridge loading, original selections/metadata/RNG, complete English
readbacks, actual scoring returns, and scheduler cleanup/retry. The
[checkpoint](../docs/checkpoints/ACADEMY_SCORE_LETTERS.md) records executed
results and current artifacts. The complete batch passes forty comparisons,
forty-four readbacks, thirteen rejections, two retries, and original evaluation
returns. The scheduler's NULL-game allocation path passes delivery and cleanup;
game-owned system allocation fails in the checkpoint and retains eligibility.
Successful game-owned allocation is not covered by this batch. Normal gameplay,
save/reload, semicolon support,
editorial/presentation review, and original hardware remain acceptance work.
