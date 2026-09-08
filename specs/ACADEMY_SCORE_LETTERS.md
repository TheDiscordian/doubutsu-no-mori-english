# Complete HRA score letters

## Source-bound scope

The original N64 scoring overlay selects twenty-one templates `0034..0048`.
All sixty-three Japanese/English parts have verified identities and field sets.
Twenty complete references fit the current mail encoding; body `003D` needs the
semicolon path. The source verifier does not install or credit these letters.

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
| 0 | Points | 10 |
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

## Remaining integration

`tools/academy_score_letters.py` writes the ignored source/English pairing and
part hashes to `build/academy-score-references/references.json`. Four focused
tests pass, including 2,200 complete snapshot/format combinations across the
twenty currently encodable templates, both capitalization states, and all 55
full series names. Ten-digit points, sixteen-byte item names, full months, and
ordinal days fit without truncation. This is reference/capacity evidence, not
native creation or publication. The test log is
`build/academy-score-references-tests.log`, SHA-256
`1e575733611bf74a0d3179196cc6faab134f627ca0ef9545a39646977242c763`.

The native creator takes home arrangement index, points, room size, a pointer
to the native series name, and base/theme item IDs. It obtains current date
from `80136FBC` and current private player from `80136FD8`. The caller passes the
selected static series buffer and original item IDs at `80928388`.

Preserve the original score calculation, choice draw, metadata, and mailbox/queue
policy. Replace complete creation at its owner boundary, capture full English
fields, and test success before publication. Propagate failure through the
scoring entry and the resident scheduler's mark-date call, without losing the
existing returned points value or skipping overlay cleanup. No new saved-layout
or reward flags are needed. Synchronous retry eligibility must survive failure;
whether exact selected choices need retained storage remains an explicit design
decision. Compare original selections and all complete text in one native batch,
then include real save/reload and normal gameplay in later acceptance.
