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
Both saved capitalization states produce the complete fixed wording. The source
audit is independent of installation; `tools/notice_overlay.py` installs creation
and display hooks together and verifies the actual cartridge resources.

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
The initial-post route is installed. Seasonal and treasure identity/field review
remain part of the complete board requirement.

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
drawer retains sixteen-byte rows for editing. The full reader intercepts its
page-draw caller without replacing the retained function. Its complete
`8089542C..8089562C` hash is
`6541da6eea1c047aeb02a666ba10fe7148897459df37f66ccb5b4ad792f8517c`.

The family-prefix test deliberately recognises unsupported versions so a future
reader can display an error instead of treating encoded data as ordinary text.
The editor/tag-discrimination audit verifies that all five original keyboard
palettes exclude `7F` and `80`; the actual selector at
`80885140..808851D8` reads the pointer/count tables at `808885C8/808885DC`.
The five counts are 50/30/50/30/10. The native case/ornament converter at
`80886168..808861E0` reads the 256-byte map at `80888710`; that map has SHA-256
`b362d398e9b519b0e336eb53a2490a5af1ca78ddd426de3c3034153a38bf1e5e`.
The transitive set of palette/space/newline bytes and repeated conversions has
253 values, excluding both reserved prefixes. Insertion copies the selected
byte, deletion shifts it, and down-at-end adds `CD`. This covers native manual
input; arbitrary third-party saved edits and old Japanese automatic-post
translation still require separate compatibility handling.

## Installed native ownership and remaining acceptance

`overlays/notice/initial.s` replaces `800A5BC4..800A5CB0` with 188 instruction
bytes and zero padding. It clears each 96-byte message, installs its canonical
sixteen-byte compact prefix, and copies the original eight-byte timestamp. The
four table words at `8010B4A0` become fixed template/checksum words. The native
clear routine handles the eleven remaining slots. No new initial-creation
allocation or cartridge read is needed.

The full reader is appended after the original file and 128 zero-backed BSS
bytes. Its 13,840-byte file resides at VROM `03920000`, with the 560-byte adjacent
relocation file at `03928000`. The original DMA row indices remain. Original
section-relative relocations are flattened without reordering, and appended ELF
relocations include only targets inside the overlay; fixed verified resident
imports are not moved. Code, initialization, relocations, and exported offsets
have independent compiled identities. Three relocation bases retain all
untouched original code/data/BSS.

The submenu owner at VROM `007749C0` has program-six metadata at offset `2AD0`.
It declares the complete new file/RAM range and constructor while retaining
native destructor/set-procedure offsets. It has no cross-overlay metadata
relocation rows. The native `linkedAllocEnd` loader advances by the aligned
declared size; source is `upstream/af/src/overlays/submenu/submenu_ovl/`.
The pool calculation's instruction at `800C4B10` adds 16,384 bytes to its editor
term, which is part of the dominant submenu sum. The actual arithmetic yields
214,400 native bytes and 230,784 expanded bytes, above the unchanged alternative
199,488 and player 186,240 terms. The added reader's aligned growth is 7,104
bytes. This reserves space without changing any other program's declared image.
The actual native program loader and constructor pass in an isolated owned
submenu fixture, including complete image/asset DMA, aligned allocation advance,
relocated callbacks, single-owner reopening, and temporary relocation cleanup.
The top-level submenu pool allocator and normal menu initialization are not
executed by that fixture and still need validation.

The constructor wrapper clears two 1,216-byte caches and invokes the retained
constructor. The read dispatch at `80895BC0` wraps the retained controls, and
calls at `80895750/80895768/808957C0` draw English entry/date/body text. Original
read/edit functions are not overwritten by wrappers that would recurse into
themselves. Full RTC dates use day byte three, month byte five, and BE16 year
at byte six. Complete English month names are right-aligned in the header.
L/R select additional six-line pages; existing post/navigation/edit controls
take precedence. Native L/R limits and complete hint/entry/month glyph positions
pass at the settled coordinates. Ordinary C-button/edit navigation and human
review of the complete window still need validation.

The reader's aligned decoder workspace is temporary heap storage; only its full
decoded body stays in a cache. Comparing all 96 input bytes invalidates changed
slots. Both sides of a post transition can remain cached. Failed restoration
displays a bounded error without modifying the saved record; reopening retries.
Editor mode invokes the retained native body/cursor implementation, and a draft
confirmation never interprets its bytes as a persistent snapshot.

The resident module retains its exact binary, symbols, reservation, and heap
bounds. The resident compiler excludes the explicit on-demand notice C units while
keeping every nested runtime source/header in its source inventory.
The full build requires a freshly generated manifest, the English keyboard,
complete glyph resources, and snapshot reader. An Expansion Pak is permitted,
but the implemented memory configuration remains four MiB.

Native storage execution passes initial creation, count/clear, all fifteen
positions, full-board shifting, manual/encoded record retention, timestamps,
guards, and checkpoint restoration. Actual expanded-owner loading, all initial
body decoding/drawing, two-post caches, corrupt-record recovery, L/R paging,
entry labels, and all full months have native evidence. Normal draft publication,
C-button/edit navigation, old automatic-post display, save/reload, seasonal/
treasure creation and full fields, ordinary gameplay, and original hardware remain.
See the [integration checkpoint](../docs/checkpoints/NOTICEBOARD_READER.md).

## Treasure source review and next integration

`tools/audit_notice_treasure.py` binds all 54 native/reference parts and both
executables' field/selection helpers. The native treasure scheduler is
`800A5F08..800A62EC`, SHA-256
`e548281b85424af417431715461bd63d5806f4e15151fb90c0b263039917e53f`.
The instruction sequence selects `01F0 + personality*3 + random(3)`, calls the
formatter at `800A62A0`, publishes the 104-byte post at `800A62A8`, then updates
the buried timestamp. Complete English creation must succeed before publication;
failure after burying the object also requires an explicit recovery policy.

Seventeen supplied English bodies preserve their corresponding native clue
scope. Their 34 complete-field examples fit compact storage with full sixteen-byte
villager/item names, decimal acre coordinates, and the six-byte town identity.
The donor's `01FE` omits the author signature; its complete English wording is
retained. Manual breaks and article commands remain part of the reference.

`01F4` is not approved unchanged: Japanese fields `1/3/5` name the sender, row,
and town, while the donor's `1/2/3` reveal the buried item. Adapt the town's
treasure-hunt heading without disclosing that item. This is a real clue difference,
not a reason to drop the entry or pass an empty item name to the donor formatter.
All eighteen need native owner/reader installation, publication handling, and
persistence integration; the source audit grants no installed-translation credit.

## Complete treasure helpers and integration contract

`runtime/notice/treasure.[ch]` accepts only the eighteen source-bound identities
and each complete selected field mask. Fields one/two retain complete sender/item
text up to sixteen bytes. Row three is a single native digit `1..6`; column four
is `1..5`. Town five retains up to six original identity bytes without a Japanese
suffix. Only the item field may carry an article. Empty names, embedded commands,
newlines, extra fields, wrong catalogues, malformed envelopes, and changed complete
source lengths/checksums are rejected before body publication.

Seventeen bodies retain their complete supplied wording and manual whitespace.
For `01F4`, the two-line heading is `{town}'s Treasure Hunt!` followed by
`Come and join the fun! Woo!`. The blank third line and remaining donor lines,
including the row clue and sender decoration, remain intact. The decoder loads
and verifies the immutable donor body in scratch, substitutes the heading there,
and formats again with native fields `1/3/5`. It never stores, displays, or reveals
an item for that clue. The catalogue itself does not change. Both capitalization
states and all source manual line boundaries are retained.

`af_notice_treasure_restore` publishes a complete body with a cleared unused tail;
failure leaves output unchanged. Input/output overlap is supported after decoding.
The existing aligned notice workspace remains sufficient. The split-scratch API
lets the mail creator use its existing catalogue/text/wire members without a second
allocation or incompatible-structure casts.

The optional `af_notice_treasure_create` dispatcher preserves the complete earlier
creator chain. Its twelve-byte request is `AFNT`, BE16 template, BE16 item, row,
column, item article, and marker `245`. The existing loader's player argument
points to the selected native animal identity with sixteen readable bytes; animal
points to the request. Remail, condition, and foreign are zero. The template must
match the original animal personality group; the creator does not choose new RNG,
items, or coordinates. Town bytes come from the source-verified `80129E00` identity.

The dispatcher captures complete immutable villager names and sixteen-byte item
names, packs the compact record, and validates its whole decoded body before
publishing exactly 96 message bytes plus 68 zero staging bytes. Its 164-byte output
is only the existing loader's scratch interface, not a native notice record.
The owner must copy **only 96 bytes** into the original 104-byte post and retain
its original timestamp. No saved post, buried object, timestamp, or eligibility
state is modified by these helpers. Article is currently a validated caller input;
the GameCube article-table lookup still needs native item-identity binding.

The complete creator image is 37,792 bytes with 656 relocation bytes, no mutable
global state, and the unchanged 5,344-byte caller workspace. Independent builds,
49 host/sanitizer checks, and artifact/retention checks pass. The creator remains
inside the existing 65,536-byte image limit, and the freshly inventoried resident
module and bootstrap are unchanged. Native hooks, reader routing, article capture,
post-burial failure recovery, actual execution, and persistence remain uninstalled
or unverified. See the [treasure checkpoint](../docs/checkpoints/NOTICEBOARD_TREASURE.md).
