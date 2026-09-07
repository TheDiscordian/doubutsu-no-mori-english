# Full generated-letter reader

## Experimental scope

`--english-mail-snapshots` connects the immutable catalog decoder to the native
letter window. It requires `--english-mail-layout`, the resident module, and the
registered catalog. Native generation does not emit snapshots. The experimental
marker is exercised only with isolated test records; it is not a released save
format or a declaration of complete metadata-reader compatibility.

The reader recognizes `headerBackStart == 80` hexadecimal, outside the native
ten-byte and alternate twenty-byte header ranges. Ordinary font, stationery,
gift, recipient, sender, and mail-type fields retain their meanings. The marker
alone never establishes a valid snapshot: catalog identity, complete envelope,
checksum, fields, source rows, and formatting must all validate. Ordinary records
without this marker retain their original copy and editor path. All metadata
writers, other readers, excerpt consumers, normal delivery, and actual save/reload
still require integration before generation or release is enabled. The combined
grading build supplies [complete-record NPC sending](MAIL_NPC_SEND.md), including
distinct ordinary/quest grades and post-office failure retention.

## Initialization and ownership

The native board initializer calls `mMl_copy_mail` at linked `8088A47C`, before
its field scans, header-split clamp, and footer normalization. Its delay slot
saves the menu pointer at `5C(sp)`. A guarded call-site shim supplies that pointer
as the third argument to the resident copy wrapper.

The wrapper copies the complete 164-byte native record, resets its display
cache, and handles tagged records before returning to initialization. Decoding
uses a separate, aligned 3,552-byte workspace in resident RAM. Complete output,
header-name insertion, and the selected page also live in that cache. The
5,792-byte cache is bound to the current board address. Reopening a different
letter resets it. Reading never regenerates random words, queries current names,
changes capitalization state, or writes the source record.

For tagged records, only the board's temporary copy receives blank ordinary
text fields and a zero split, preventing opaque snapshot bytes from reaching
native length scans or drawing. The original metadata and source pointer remain.
The menu is forced into read mode, including when an edit-open path is requested.
This prevents lossy native editing; it is not the completed English editor.
Malformed or unavailable snapshots show an explicit English error message.
Neither a successful decode nor an error changes the original letter.

## Recipient display names

Read-mode headers resolve complete eight-byte English villager names from the
optional display-name resource. This applies to ordinary letters and decoded
snapshots, not to saved identity fields or the editor. The native name setter
at `8009C70C` stores recipient type one at mail offset `10`, the villager index
at `0C`, and the palette at `0D`. The reverse setter at `8009C780` reconstructs
the NPC ID as `E000 | index`. Offsets and addresses are hexadecimal.

Only type one and indices below 216 use this lookup. Player names, other types,
unsupported indices, and unavailable or invalid resources retain the saved
name. Indices 216 through 255 do not alias special-character rows. Header types
two, three, and five retain their native recipient-name suppression. Trailing
name padding is trimmed; header text, explicit spacing, and the insertion split
are unchanged. No recipient, sender, town, or saved text bytes are rewritten.

The snapshot header capacity is 1,032 bytes: 1,024 formatted bytes plus the full
eight-byte display name. Its two additional bytes occupy existing structure
padding, so the resident cache remains 5,792 bytes. The formatted-letter member
begins at offset 1,196; the decoder workspace remains at offset 2,236. Ordinary
headers use an eighteen-byte stack buffer for the native ten-byte header plus
the display name. Snapshot names load once on open; ordinary read-mode headers
resolve the name during drawing. Hardware timing remains unverified.

The original identity setter range `8009C70C..8009C780` has SHA-256
`e4eaf965033e414fe876b90d236a6ae9e79199171b8601270dc4798d7008d07d`;
the reverse range `8009C780..8009C80C` has SHA-256
`d6543275f47092b0c2de962c849e4ed26e5af909c402d21984e9b263866744bf`.
Window fixtures guard and execute the original setter to construct NPC names.

## Complete pages

The page builder measures the approved font's actual advances against a
192-pixel width. It never trims spaces, removes blank lines, or reflows words.
An overflowing glyph remains for the next line. Every source section is retained;
no footer or body is shortened to fit the native saved-field capacities.

Positions are relative to the native header origin. The header begins at zero;
six body rows begin at 28, then advance sixteen pixels; the signature ends at
136. A one-line header repeats on continuation pages. A longer header continues
through available rows before body text begins. Signatures wrap by measured
width and align each line's right edge to the paper edge. Additional signature
lines reserve room above the final baseline. A signature moves to its own page
when it cannot fit with the final body rows; signatures longer than seven rows
continue on additional pages. Explicit blank rows still occupy their space.

D-pad Left/Right changes pages, with bounds at both ends. A, B, and START retain
the native close behaviour and take priority over simultaneous page input.
Paging applies only to the active cached board in read mode. The footer-adjacent
`Left/Right: current/total` hint appears only for multiple pages. Paging uses the
already decoded text and does not read the cartridge again.

These additional pages preserve complete reference wording that cannot fit in
the native paper window. They do not claim that GameCube mail has the same
pagination UI. The ordinary one-page layout and explicit reference line breaks
remain the presentation target.

## Installed calls and relocation

The two body/footer hooks from `MAIL_VIEW.md` remain. Three additional calls are
guarded and replaced:

| Linked call | Original target | Resident target |
| --- | --- | --- |
| `8088A034` | `80889CD8` header | `af_mail_header_hook` |
| `8088A47C` | `8009C67C` copy | `af_mail_copy_hook` |
| `8088914C` | `80078DF4` trigger | `af_mail_reader_trigger` |

The header shim forwards non-read modes to the original header renderer using
the guarded return-address difference `0364`. The trigger call retains its
submenu/menu arguments; its preceding two stores are checked explicitly.
Only the header call has an additional overlay relocation to remove:
`440011A4`. Forty-nine other relocation entries, every delay slot, resource
length, and the original functions remain unchanged. The copy and trigger
targets are native resident functions and have no overlay-call relocations.

## Verification and remaining work

Host tests cover full reconstruction, measured page spans, extreme section
lengths, ordinary-record fallback, corrupt snapshots, disabled resources,
unchanged input and adjacent bytes, special header types, page bounds, native
close-button priority, and stale/inactive cache input. N64 compilation checks
the exact display-cache BSS size and rejects other mutable globals in the
codec/formatter/catalog/page/reader objects or undefined symbols. The separate
NPC send adapter owns one four-byte scoped-context pointer.

`mail_reader_test_scenario.py` selects long classic and composite reference
witnesses from the installed cartridge catalog. The silent real-window test
opens each snapshot through the native submenu loader, checks full cached
content, and observes the header hook's actual entry and return. It verifies
graphics allocation sizes and every glyph quad on every page, traverses pages
in both directions, and checks unchanged source letters and saved preferences.
The complete emulator checkpoint must be restored afterwards. Test records and
reference wording stay in ignored output directories.

The full native run passes six long reference letters and two rejected
snapshots across fourteen pages, 1,705 glyphs, and 6,820 vertex positions. All eight
source/preference checks pass. Two reference probes use the native NPC identity
setter and complete eight-byte English recipient names. The fourth reference letter requests edit-open
mode two and reaches read-only mode one without rewriting its source. A corrupt
checksum and an unknown catalog each display the error message through the real
font renderer. A separate ordinary-header/body/footer regression passes ten
header cases, full glyph positions, memory guards, and non-read-mode forwarding:
36 calls and 842 assertions across 1,010 steps. Complete machine checkpoint
restoration and blank FlashRAM status are
retained in local evidence; this remains distinct from actual game saving.

Ordinary generation, semantic template matches, missing glyph support, complete
metadata/excerpt/other-reader handling, lossless editing, normal delivery, persistence,
and original-hardware validation remain required. No public release or save
compatibility claim follows from isolated snapshot-window tests.
