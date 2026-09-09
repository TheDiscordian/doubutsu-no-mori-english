# Noticeboard text and lossless storage

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

## Initial source binding and controller adaptation

The four initial reference bodies have stored lengths 141, 166, 137, and 154
bytes respectively. Their headers contain only a newline, and their footers
are empty. The HRA guide retains the native 10,000/20,000/70,000 thresholds.
The final instruction body says "C Stick", whereas the native text names the
C buttons. The source-bound profile changes the seven bytes at body offset 81
to the nine bytes `C Buttons`. Every other byte and manual break remains. The
complete output lengths are 141, 166, 137, and 156 bytes. Catalogue four stays
immutable; the adaptation belongs to the notice decoder, not the mail catalogue.

`tools/audit_noticeboard.py` binds the four Japanese body hashes, all twelve
native/reference parts, the complete supplied English banks and decoder,
catalogue-four identity, original initializer/table, and actual native controls.
`runtime/notice/initial.c` checks the selected fixed identity, empty field mask,
complete decoded body length/checksum, and exact controller span before output.
Both saved capitalization states produce the complete fixed wording. This
source binding does not install creation or display hooks.

The actual reader is submenu program six, overlay VROM `00797A50`, linked at
`80894250`, with 6,656 file bytes and 128 BSS bytes. Complete file SHA-256 is
`b7f501e8efe2761f0f0e6fd4c18bd648ceae48658cbfe0f350d8a8386a8f7cb7`.
Read controls `80894560..80894814` have SHA-256
`bda6eb0b4479eb456d61b1f88ae3d7acbde5b756cc98a47fd5e02d13ebd6b559`.
The native trigger masks are C-left/right `0002/0001`, C-down/up `0004/0008`,
A `8000`, B `4000`, and START `1000`. C-left/right select adjacent posts;
C-down/up jump to oldest/newest. The analogue-stick directions also select
posts. Preserve these actions and the native transition animation.

A starts a fresh blank 96-byte draft at notice-state offset eight, copies its
timestamp to offset `68`, and passes that draft to editor type two. It does not
copy the selected saved post into the editor. This branch has no visitor check.
The confirmation path calls the original writer at `80894DA0`, with the same
draft address in its delay slot, and then performs the first-job completion
check. Creation, navigation, and editor-publication hooks must retain these
boundaries. Read-mode state remains separate from editable draft text.

Across the 63 scoped bodies, the longest stored reference is 170 bytes before
field expansion. Fifty-seven have six explicit visible lines, four have five,
one has four, and `01AE` has seven. These are source-layout observations, not
pixel-fit or native-draw proof. Preserve manual breaks and check the seventh
line, full dynamic names/dates, and existing post-navigation/edit controls.
The initial-post route is the next installation group; seasonal and treasure
identity/field review remain part of the complete board requirement.

## Implemented compact envelope and full-body page planner

`runtime/notice/record.[ch]` and `tools/notice_record.py` implement profile one:

| Message bytes | Meaning |
| --- | --- |
| `0..2` | Reserved notice-family prefix `7F 42 4E` |
| `3` | Profile version one |
| `4..95` | First 92 bytes of a canonical classic mail snapshot |

The embedded snapshot retains its own version, used length, immutable catalogue
identity, template ID, capitalization, field mask, exact literal field bytes,
article choices, and CRC16. Its used length must not exceed 92; remaining bytes
must be zero. Decoding restores the omitted thirty zero bytes in separate
122-byte scratch storage before invoking the existing strict mail codec.
Composite records, incorrect sizes/catalogues, reserved bits, malformed fields,
checksums, unsupported profiles, and noncanonical padding fail without output.
Overlapping input/output is supported through staging. Neither codec operation
writes a timestamp or enlarges a native post.

All 63 scoped templates fit with every used field at sixteen bytes and every
article retained: the maximum complete stored prefix/payload is 84 bytes.
Initial records use sixteen bytes, padded to 96. This is capacity evidence, not
approval of the seasonal/treasure wording or the native field preparers.

`af_notice_initial_restore` uses a disposable aligned workspace and publishes
only a complete body. It rejects workspace/input/output overlap and leaves
output unchanged after failed cartridge reads, invalid sources, or unsupported
identities. The output may overlap its original compact input after decoding.
The native integration must allocate this workspace off a small nested stack
and retain a full decoded body only for the active reader's lifetime.

`runtime/notice/page.[ch]` plans complete six-line, 192-pixel pages with the
existing proportional line scanner. It preserves explicit blank lines, leading
and trailing spaces, and complete registered glyph pairs. The whole body is
validated before publishing even page zero. A seventh line continues on another
page; a final newline does not invent an extra empty page. All four initial
bodies fit one page under the approved metrics. The native `8089542C` body
drawer still uses sixteen-byte rows and is not yet replaced. Its complete
`8089542C..8089562C` hash is
`6541da6eea1c047aeb02a666ba10fe7148897459df37f66ccb5b4ad792f8517c`.

The family-prefix test deliberately recognises unsupported versions so a future
reader can display an error instead of treating encoded data as ordinary text.
Native integration must first finish the editor/tag-discrimination audit. All
five original keyboard palettes exclude `7F` and `80`; the actual selector at
`80885140..808851D8` reads the pointer/count tables at `808885C8/808885DC`.
The five counts are 50/30/50/30/10. Case/ornament conversion and existing saved
manual posts still require explicit compatibility checks. Palette exclusion
alone is not a complete proof for every editor output or old save.

## Native installation and acceptance still required

Complete generated bodies need a lossless representation within the existing
96-byte saved message and a compatible full-body reader. The current mail
envelope occupies 122 bytes and is identified through a mail-only split marker;
neither assumption can be applied directly to a noticeboard record. A compact
representation may reuse the existing bounded payload if its actual used bytes
fit, but detection, malformed-record handling, full decoding, page drawing,
custom-post editing, and old-save compatibility need explicit implementation.
Profile one is implemented as bounded helpers, but no noticeboard format or
reader hook is installed in the complete translation ROM.

Continue by connecting the creator and reader together, with guarded native
overlay allocation/relocation and lifetime. The submenu loader uses
`linkedAllocEnd`, loads the declared program range, and advances by the aligned
declared RAM size; source is `upstream/af/src/overlays/submenu/submenu_ovl/`.
Any appended code or state must update and verify that owner and its total pool,
not merely the overlay relocation record. The resident module has no linked
headroom. An Expansion Pak remains permissible, but these helper objects do not
change the actual memory requirement or any heap bound.

Preserve original timestamps, insertion order, full-board shifting, manual
posts, treasure/reward selection, and scheduling. Complete creation must precede
publication. Native tests must cover full content, retention on failure, all
saved positions, the real reader/editor boundaries, and save/reload. Normal
seasonal gameplay and original hardware remain separate acceptance requirements.
