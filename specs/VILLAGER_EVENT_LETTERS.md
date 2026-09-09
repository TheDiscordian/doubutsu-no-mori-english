# Complete villager-event letters

## Installed scope and verified content

The optional integration groups native friendship gifts, birthday cards, moving-away
goodbyes, and the Christmas card. `tools/villager_event_letters.py` verifies all
165 selected parts against the original ROM, selected immutable catalogue two or four, and the
supplied English executable and text-bank hashes. `--english-villager-event-letters`
installs complete supported creation and guarded publication. It requires the
creator built with `--mother-letters --departed-letters --villager-events`,
the previous system-letter integrations, and full installed item names.

| Group | Classic templates | Complete references | Required fields |
| --- | --- | --- | --- |
| Friendship gifts | `0060..0071` | 18 | Player 0, full villager name 6 |
| Birthday cards | `00EA..00FB` | 18 with catalogue four; 17 with two | Player 0, full villager name 1, selected gift name 2 |
| Moving-away goodbyes | `020E..021F` | 18 | Player 0, full villager name 1, current town 3 |
| Christmas | `00D7` | 1 | None |

Body `00F6` retains its exact semicolon through the creator's `--mail-glyphs`
variant and catalogue four. The default catalogue-two creator still rejects that
body. Do not substitute punctuation or change immutable catalogue two.
Source/English field sets deliberately differ
in several bodies. The verifier records those exact sets; prune unused captured
values without inserting arguments omitted by the supplied English wording.

## Shared native creation boundary

`mNpc_LoadMailDataCommon2` occupies `800A93AC..800A9468` (188 bytes), SHA-256
`c032ea2500931cc53d4fc3b0abb2b210b825b3775189e9d675109d18fceb48e8`.
The friendship-gift, birthday, and goodbye creators all call it after preparing
their selected template, gift, paper, and temporary fields. The shared routine
installs complete text for all three groups while retaining their original
choice and gift operations. Native callers use the
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

## Synchronous descriptor

The optional extension of the on-demand system creator leaves the resident
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
The optional dispatcher checks all output/input/control/resource overlaps
before inspecting it, including smaller output objects before session reads.
The descriptor contains copied data, no embedded pointers.
The existing player input remains the sixteen-byte native recipient identity.
The independently assembled common wrapper has a 48-byte frame, copies the
twelve-byte identity through halfword accesses, and rejects null/odd identities
or oversized template/gift/paper arguments before narrowing. It occupies the
original 188-byte range without adding resident code.

Creation stages complete metadata and a complete English snapshot privately,
then publishes all 164 bytes and capitalization only on success. Sender,
recipient, gift, paper, and native type are retained. Ordinary replies, Mom, and
departed letters continue through their existing dispatcher paths. The
`af_load_item_name` import is optional for this creator variant; legacy catalogue
selection remains available through a current rebuild. Only birthday bodies `00EF/00F1/00F4/00FB`
require a complete gift-name load. Bodies which omit that field do not depend on
the unused lookup. Article state remains zero, matching the donor's plain setter.
Goodbye field three captures the actual saved town at `80129E00`.

## Caller gates and Christmas metadata

Friendship and birthday mailbox copies and queue submissions test the returned
complete destination pointer before publication. Their existing creator
epilogues retain that return register. Mailbox gates occupy 48 bytes each at
`800A961C` and `800A9B3C`; eight-byte queue gates occupy `800A9688` and `800A9B9C`.
Goodbye creation uses `sltu v1,zero,v0` at `800AC340` to propagate real success
into its unchanged publication/pending-bit callers. Notification eligibility
does not preserve exact template/gift/paper selections across attempts. No RNG
draw is rolled back, and no new durable selection state is added.

Christmas uses a separate 148-byte entry with a 64-byte frame.
Its N64 implementation randomly selects a gift from category zero, priority
three, whereas the supplied GameCube implementation sets a fixed NES item. Keep
the N64 gift operation; the supplied English body describes a present without
identifying the item and remains applicable. Preserve native type one and paper
22. It clears the temporary gift output before the original selection call and
then supplies a descriptor with twelve zero identity bytes, template `00D7`,
the selected gift, marker `FC`, and paper 22. The mailbox copy has a 48-byte
failure gate at `800A9E08`.

The original N64 Christmas creator does not clear its shared staging letter;
the supplied English caller explicitly does. Complete creation uses freshly
cleared private staging and an empty invalid sender instead of carrying a
previous villager's identity into a system letter. Native metadata comparisons
use a freshly cleared original baseline. This is an intentional initialization
correction, not a claim that arbitrary stale native sender bytes are preserved.

## Acceptance still required

The creator, guards, full selected item lookup, and caller success propagation
are installed. Seventeen host creator tests and the sanitizer run pass, covering
all complete templates in both capitalization states, full-name combinations
for all 216 villagers, and the inherited ordinary/Mom/departed contracts. Five
installer tests and independent builds/entry assembly pass, along with all 987
regression tests. All 54 templates pass native selection comparisons and complete
delivered readbacks in both capitalization states; eighteen rejection cases and
four resource-recovery retries pass.

The native batch checks all complete templates, native selection/gift/metadata
comparisons, unavailable text, resource failures, mailbox destinations, queue refusal,
and complete reader reconstruction. Its results belong in the
[integration checkpoint](../docs/checkpoints/VILLAGER_EVENT_LETTERS.md).
The top-level goodbye pending-bit scheduler, normal scheduling,
queue draining, real save/reload, human playthrough, and original hardware remain
outside direct-call proof. The complete catalogue-four creator and its acceptance
are tracked in the [creator checkpoint](../docs/checkpoints/MAIL_GLYPH_CREATORS.md).
