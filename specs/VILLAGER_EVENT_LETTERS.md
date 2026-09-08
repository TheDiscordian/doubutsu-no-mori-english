# Complete villager-event letters

## Verified content and next implementation

The next batch groups native friendship gifts, birthday cards, moving-away
goodbyes, and the Christmas card. `tools/villager_event_letters.py` verifies all
165 selected parts against the original ROM, immutable catalogue two, and the
supplied English executable and text-bank hashes. This is content/caller evidence,
not an installed translation route.

| Group | Classic templates | Complete references | Required fields |
| --- | --- | --- | --- |
| Friendship gifts | `0060..0071` | 18 | Player 0, full villager name 6 |
| Birthday cards | `00EA..00FB` | 17 of 18 | Player 0, full villager name 1, selected gift name 2 |
| Moving-away goodbyes | `020E..021F` | 18 | Player 0, full villager name 1, current town 3 |
| Christmas | `00D7` | 1 | None |

Body `00F6` requires the missing semicolon glyph. Preserve the complete wording;
do not substitute punctuation, change immutable catalogue two, or count the
unavailable letter as complete. Source/English field sets deliberately differ
in several bodies. The verifier records those exact sets; prune unused captured
values without inserting arguments omitted by the supplied English wording.

## Shared native creation boundary

`mNpc_LoadMailDataCommon2` occupies `800A93AC..800A9468` (188 bytes), SHA-256
`c032ea2500931cc53d4fc3b0abb2b210b825b3775189e9d675109d18fceb48e8`.
The friendship-gift, birthday, and goodbye creators all call it after preparing
their selected template, gift, paper, and temporary fields. Replacing this
shared narrowing routine can install complete text for all three groups while
retaining their original choice and gift operations. Native callers use the
staging letter at `80142F80`, distinct from Mom/departed staging at `80144570`.

| Creator | Creator range | Publication caller |
| --- | --- | --- |
| Friendship gift | `800A94C8..800A956C` | `800A956C..800A96B0` |
| Birthday | `800A99B8..800A9A98` | `800A9A98..800A9BC4` |
| Goodbye | `800AC284..800AC358` | `800AC358..800AC488` |
| Christmas | `800A9CD4..800A9D68` | `800A9D68..800A9E54` |

Birthday selection is `00EA + personality*3 + RANDOM(3)`. Its native gift
selection precedes ten-byte item-name preparation and the paper draw. Capture
the complete sixteen-byte English item name from the selected item ID through
the installed item resource; do not widen the original ten-byte local buffer.
Friendship gifts use `0060 + personality*3 + friendship-type`. Goodbyes use
`020E + personality*3 + mQst_GetRandom(3)` and capture the current saved town,
not an assumed town derived from the recipient identity.

## Proposed synchronous descriptor

Use an optional extension of the on-demand system creator, leaving the resident
loader and saved layout unchanged. The ordinary loader permits a null animal
argument when an eighteen-byte reply-origin record is present, with condition
zero and the foreign flag one. That same bounded input slot can carry this
temporary descriptor:

| Offset | Value |
| --- | --- |
| 0..11 | Complete native twelve-byte villager identity |
| 12..13 | Selected classic template, big-endian |
| 14..15 | Selected gift, big-endian |
| 16 | `FC` marker |
| 17 | Selected paper, 0..63 |

Offset sixteen holds native reply flags whose lower seven bits encode personality
0..5; `FC` instead encodes 124 and cannot represent a valid ordinary reply.
The optional dispatcher must check all output/input/control/resource overlaps
before inspecting it. The descriptor contains copied data, no embedded pointers.
The existing player input remains the sixteen-byte native recipient identity.
Freeze and independently assemble the final wrapper before installation; this
descriptor is a design, not an installed ABI claim.

Creation must stage complete metadata and a complete English snapshot privately,
then publish all 164 bytes and capitalization only on success. Preserve sender,
recipient, gift, paper, and native type. Ordinary replies, Mom, and departed
letters must continue through their existing dispatcher paths. The item-name
import is optional for this creator variant; do not invalidate older artifacts.

## Caller and Christmas requirements

Friendship and birthday mailbox copies and queue submissions need failure gates.
Their existing creator epilogues retain the called routine's return register,
but this must be checked against actual installed instructions. Goodbye creation
currently sets success unconditionally after the shared creator; propagate real
success there so the existing per-player pending bits are cleared only after
successful delivery. Do not claim exact selection retries across attempts merely
because notification state remains eligible.

Christmas has a separate creator and requires a distinct entry adaptation.
Its N64 implementation randomly selects a gift from category zero, priority
three, whereas the supplied GameCube implementation sets a fixed NES item. Keep
the N64 gift operation; the supplied English body describes a present without
identifying the item and remains applicable. Preserve native type one and paper
22, and guard the mailbox copy. The original sender/staging initialization needs
an explicit metadata check before choosing how to replace creation.

## Acceptance still required

Implement the creator, guards, full selected item lookup, and caller success
propagation. Batch all complete templates, native selection/gift/metadata
comparisons, unavailable text, resource failures, all mailbox/queue destinations,
retained pending bits, and complete reader reconstruction. Normal scheduling,
queue draining, real save/reload, human playthrough, and original hardware remain
outside direct-call proof. Complete the semicolon mail path as part of the full
translation rather than silently excluding that letter.
