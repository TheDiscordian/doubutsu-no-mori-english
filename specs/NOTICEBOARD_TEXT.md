# Noticeboard text: native boundary inventory

## Verified native storage and owners

The board has fifteen 104-byte saved records starting at `80129E0A`, or
`Save+2F6A`. Each record starts with a 96-byte message, followed by its eight-byte
RTC timestamp at offset `60` hexadecimal. The supplied GameCube C structure
uses the same field order, but its message is 192 bytes and its timestamp starts
at `C0` hexadecimal, making each record 200 bytes. Preserve the N64 layout and
neighbouring land/home records; do not copy the larger donor structure into
native storage. The donor definition is `local/ac-decomp/include/m_notice.h`,
SHA-256 `ef58288e87dcd544b50d22b5c6e8fc6d80c6d30f683ee414825fa8520f19d5a1`.

The original main-code functions are:

| Native range | Verified operation | SHA-256 |
| --- | --- | --- |
| `800A5B50..800A5BC4` | Clear messages and timestamps, stride 104 | `c996ac78a71b6fc789810c9531865c390a5c5d503e0fa606776b307a772996fd` |
| `800A5BC4..800A5CB0` | Install four initial posts, then clear eleven slots | `1fa0a689e509bf025a7eac40d9d4a1e73a8681523fea021593559b54384cf599` |
| `800A5CB0..800A5D30` | Count up to fifteen posts by timestamp | `5e021786deb17a1126a12e984906552025601e2a3db24bcdb83fa90422e6655e` |
| `800A5D30..800A5DF4` | Append a post, shifting fourteen older records when full | `1f42a947e45c6ee77c8b245aff761cdd65720c8313959bc28fb540fd8b5798c3` |
| `800A6384..800A63F8` | Concatenate native month/day text | `9482556995c89177e926528712e92986898a0d1084728724bbcf58e86dca89b7` |

The initial table at `8010B4A0` has four BE32 IDs `001E/001F/0020/0021`.
The initializer calls the classic formatter at `800A5C68`, with header/footer
scratch separate from the message pointer; only the body belongs to the post.
Its frame is 136 bytes. Full snapshots cannot simply overwrite those separate
header/footer destinations and be assumed to reach saved noticeboard storage.

The automatic-post path calls the formatter at `800A6778`, adding `01A4` to
the selected native index. It then calls the actual writer at `800A6780`.
Date preparation still needs complete combined English month/day fields; see
[date caller evidence](LEAFLET_DATES.md). The reader's shared length call at
`8089571C` scans the selected 96-byte message; it is not a stored-mail reader.
See [storage evidence](MAIL_STORAGE.md) for the separate interface contexts.

## Supplied references and remaining matching

The supplied `local/ac-decomp/src/game/m_notice.c` confirms the initial-post,
automatic-post, and treasure-post semantic groups. The complete glyph catalogue
contains all four initial bodies, 41 bodies at `01A4..01CC`, and eighteen bodies
at `01F0..0201`. Their headers are nonempty and have no free fields; all their
footers are empty. The initial bodies have no free fields. Seasonal bodies
use none or one of fields `0/1/2/4`. Treasure bodies use two to four of fields
`1/2/3/4/5`. These field inventories are reference facts, not installed support.

The donor's seasonal schedule includes different events and two daylight-saving
posts. Its treasure code also has version-dependent variants. Do not approve all
same-number bodies without checking original Japanese meaning, native selection,
field sources, event dates, and venues. Preserve the N64 events where the donor
describes a different holiday. Bind approved complete text to both source
identities; draft native-specific English for actual differences.

The native treasure preparer `800A5E58..800A5F08` sets sender field one to six
bytes and item field two to ten bytes, without the donor's item-article setter.
Its acre fields three/four are decimal digit characters (`block_z/block_x + 30`
hexadecimal), unlike the donor's lettered vertical-acre lookup. Preserve the
native map-coordinate meaning. Its town helper `800A5DF4..800A5E58` copies six
saved name bytes, finds the non-space length, appends two bytes from `8010B500`,
and returns that length plus two. The English counterpart returns only the
town-name length. Complete English capture must not inherit the native suffix
or assume the donor's coordinate/article preparations already exist.

## Implementation and acceptance still required

The four initial reference bodies have stored lengths 141, 166, 137, and 154
bytes respectively. Their headers contain only a newline, and their footers
are empty. The HRA guide retains the native 10,000/20,000/70,000 thresholds.
The final instruction body says "C Stick", whereas the native text names the
C buttons. Preserve the whole reference and its manual breaks, but adapt that
controller instruction after verifying the native board-navigation input.
The current immutable mail catalogue does not perform that controller change;
do not install the unadapted body or mutate an existing saved-mail catalogue.

Across the 63 scoped bodies, the longest stored reference is 170 bytes before
field expansion. Fifty-seven have six explicit visible lines, four have five,
one has four, and `01AE` has seven. These are source-layout observations, not
pixel-fit or native-draw proof. Preserve manual breaks and check the seventh
line, full dynamic names/dates, and existing post-navigation/edit controls.
The initial-post route is the next bounded implementation group; seasonal and
treasure identity/field review remain part of the complete board requirement.

Complete generated bodies need a lossless representation within the existing
96-byte saved message and a compatible full-body reader. The current mail
envelope occupies 122 bytes and is identified through a mail-only split marker;
neither assumption can be applied directly to a noticeboard record. A compact
representation may reuse the existing bounded payload if its actual used bytes
fit, but detection, malformed-record handling, full decoding, page drawing,
custom-post editing, and old-save compatibility need explicit implementation.
No noticeboard snapshot format is installed or approved by this inventory.

Preserve original timestamps, insertion order, full-board shifting, manual
posts, treasure/reward selection, and scheduling. Complete creation must precede
publication. Native tests must cover full content, retention on failure, all
saved positions, the real reader/editor boundaries, and save/reload. Normal
seasonal gameplay and original hardware remain separate acceptance requirements.
