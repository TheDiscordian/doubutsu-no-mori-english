# Complete catalogue-order and raffle-ticket letters

## Content and native identities

Templates `0049..004C` are the four shop-level catalogue-order letters; `0057`
delivers raffle tickets. All fifteen header/body/footer parts match the supplied
English GameCube banks through verified transcoding. Complete wording, manual
breaks, article commands, punctuation, and the donor's website footer remain.
Both registered creator catalogues support these parts. No GameCube-only IDs
or unused catalogue entries receive translation credit.

Order bodies require full sixteen-byte item names in field zero. Ticket body
`0057` requires only the nine-byte English month in field four. Although the
GameCube preparation function also supplies a last-day field, the actual donor
body never uses it. The selected ticket gift encodes the original expiry month;
no new RTC read, year, day, or date calculation is needed.

`tools/post_office_letters.py` pins seven complete original N64 functions and
seven supplied GameCube functions. The supplied executable and three banks have
whole-file hash checks. Native and English field sets must agree for every part.

| Native range | Role |
| --- | --- |
| `800B6AC8..800B6B94` | Free mailbox slot and complete receipt |
| `800B6B94..800B6C14` | Common template/gift/recipient creation |
| `800B6C14..800B6C88` | One catalogue order |
| `800B6C88..800B6D40` | Five pending-order slots |
| `800B6D40..800B6D80` | Original numeric month preparation |
| `800B6D80..800B6DCC` | One ticket delivery |
| `800B6DCC..800B6EBC` | Pending-ticket batching and receipt |

## Creator and ownership

The optional `--post-office` creator includes the complete earlier creator
chain and uses the unchanged resident loader ABI. `af_post_office_mail_create`
dispatches the new twelve-byte animal argument descriptor:

| Offset | Bytes | Value |
| --- | ---: | --- |
| `00` | 4 | ASCII `AFPO` |
| `04` | 2 | Original selected template, big-endian |
| `06` | 2 | Original gift, big-endian |
| `08` | 1 | Original paper 55 |
| `09` | 2 | Zero reserved |
| `0B` | 1 | Marker `F9`, outside native personality values |

The player is the original sixteen-byte identity; remail is null, condition and
foreign are zero. Remail requests delegate before reading the animal argument;
misaligned animal inputs reject before dereference. Unknown valid personality
markers retain the ordinary NPC chain. Bad postal magic, reserved fields,
paper, templates, zero order gifts, and invalid ticket month/count reject.
Valid gifts are `2C00 + (month-1)*8 + count-1`, month 1–12, count 1–5.

The shared read-only creator guard checks small control objects and all output
intersections before reading session fields. It checks work, destination,
capitalization, active session, input ranges, and immutable word/alias resources.
Earlier dispatchers also pass their extra immutable inputs to the common guard.
Workspace size remains 5,344 bytes. The compiled postal image is 31,504 bytes
with 448 relocation bytes; its temporary allocation is 37,311 bytes, including
workspace and alignment. Resident code and the saved 164-byte record do not grow.

Order names come from the full item resource, never widened native ten-byte
locals. Invalid required text or unavailable resources reject without publishing
the destination or capitalization. English fields, complete record packing, and
full reader reconstruction must all succeed before copying the final letter.
Recipient, empty sender, original gift, font zero, type seven, and paper 55
retain native meanings. The packed record marks its own complete-reader format.

## Delivery and retention

`--english-post-office-letters` installs the common 128-byte creator wrapper and
two 28-byte receipt gates. The wrapper uses a 48-byte frame and returns boolean
creation success. Each gate skips mailbox copying on failure; on success the
unchanged native copy function returns whether a free mailbox slot received it.
The original order/ticket loops already retain pending contents on zero, so
neither loop changes. A full mailbox retains the gift/count even if local letter
creation succeeded. Transient capitalization may change after successful local
creation followed by a full-mailbox rejection; saved mail does not.

Order item and shop-level remain in the original four-byte pending row, five
rows per player. Ticket expiry month and pending count remain at offsets `32`
and `33` hexadecimal from the player's private identity. The loop delivers at
most five tickets per letter and subtracts only after successful receipt.
The original preparatory native item/month fields remain unchanged in size;
their temporary writes are not the complete English capture.

No home selection, shop choice, receipt policy, queue, saved layout, date, or
RNG policy is redesigned. Runtime failures retain pending gifts for a later
attempt. Source approvals, compiled creator configuration, exact catalogue/font,
item resource, native creation, both receipt gates, and unchanged native loops
are checked before the combined counter credits the five templates.

## Acceptance

Host contracts cover every shop and capital state, complete sixteen-byte names,
all twelve months and five counts, every catalogue-read failure, resource retry,
invalid descriptors, overlap rejection, and all previous creator contracts.
Independent MIPS assembly checks wrapper and gates. Actual-ROM checks cover
owned code ranges, retained resources/text, UPS reconstruction, and translation
accounting. Native acceptance must additionally cover complete readbacks,
original metadata, ordinary pending-loop success/failure, full-mailbox retention,
retry, heap/guard integrity, and restored isolated state. Normal gameplay,
saving/reloading, review, and original hardware remain broader requirements.

Executed evidence and remaining work live in the
[post-office checkpoint](../docs/checkpoints/POST_OFFICE_LETTERS.md).
