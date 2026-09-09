# Complete treasure reader and installation

The treasure profile installs the native transaction owner and complete reader
together. It retains the four initial announcements, original reader/editor
functions, two active-post caches, 96-byte saved messages, and eight-byte RTCs.
The full English body is temporary read-mode state, not a larger saved post.

## Reader profile

`overlays/notice/reader_treasure.c` wraps the retained reader source. Its complete
restore function tries the source-bound initial decoder, then the treasure
decoder using the same aligned workspace. An unsupported initial identity fails
before catalogue reads. Both decoders publish only complete output and leave it
unchanged on failure. Unsupported or damaged envelopes retain the bounded error
and close/reopen retry behaviour; they never enter the manual-text path.

`tools/build_notice_overlay.py --treasure` adds the treasure C unit and one fixed
resident import, `af_mail_format = 80197654`. The existing initial-only artifact
profile remains independently verifiable. Source inventories, exact exports,
compiled suffixes, relocation inventories, and both source audits distinguish
the two profiles; a self-checksum alone cannot approve a changed binary.

| Property | Initial profile | Treasure profile |
| --- | ---: | ---: |
| Complete reader file | 13,840 | 15,984 |
| Relocation file | 560 | 640 |
| Appended code end offset | 11,232 | 13,168 |
| Appended BSS/cache offset | 11,392 | 13,536 |
| Extra submenu reservation | 16,384 | 16,384 |
| Initial native creator | 236 | 236 |

Both files retain the original 6,656 bytes and 128 zero-backed BSS bytes before
appended code. Three relocated bases preserve all untouched native code/data/BSS.
The treasure reader uses 9,216 aligned growth bytes, inside the 16,384-byte
reservation. The resident module/bootstrap and implemented four-MiB bounds stay
unchanged; Expansion Pak permission does not imply an eight-MiB build.

Every complete body retains the supplied manual whitespace. Full names can make
a source line exceed the existing 192-pixel width; the page planner retains every
character on continuation rows/pages. L/R page controls do not replace native
post selection or editing. The native-specific `01F4` heading keeps the town/row
clue, blank third line, and sender decoration without exposing the buried item.

## Coupled installation and verification

`tools/build.py --english-notice-treasure <owners>` requires
`--english-noticeboard <treasure-reader>` and `--npc-mail-generation <owner-creator>`.
The notice installer rejects an initial-only reader with treasure bridges, a
treasure reader without bridges, or a configured creator lacking `notice_owner`.
It verifies the real resident configuration, exact complete creator and article
data, matching full-name resource, reader image/relocations, and source-bound
native bridge instructions before publishing replacement maps.

The verifier checks every scheduler, placement, deposit, pitfall-helper, and town-
helper interval against the original code plus the precise intended edits. It
also retains the original saved-post count, clear, append/shift, and allocation
instructions. Only the initial pool patch remains in the allocator. The generated
ROM is checked by extraction, checksum, and UPS reconstruction.

The combined counter calls this actual-installation verifier before crediting
`mail:01F0..0201`. It counts each Japanese source once. Names remain in the same
whole-game inventory and do not gain duplicate credit from sample field expansion.
The installed route contains twenty-two complete board bodies; the forty-one
seasonal bodies are not credited by this route.

## Evidence and remaining execution

The [treasure checkpoint](../docs/checkpoints/NOTICEBOARD_TREASURE.md) records exact
artifacts and logs. Ten combined-reader tests pass normally and with address/
undefined-behaviour sanitizers. They cover all eighteen bodies, both capitals,
five article modes, complete pages, unchanged saved posts, mixed initial/treasure
caches, unsupported fields/IDs, failed reads, and reopen recovery. Eight artifact/
installation/accounting tests pass, including partial-install rejection and actual
native-hook removal. Existing initial artifact/native evidence remains verifiable.

The completed native owner batch exercises all 72 records, original burial,
both cartridge-loaded transaction phases, all 25 pitfall shapes, and eleven
failure/eligibility cases. Null allocation returns in both phases and exact
rollback are observed. The separate native reader batch loads the larger reader
from the same ROM and draws the same 72 records completely: 9,148 glyphs and
36,592 vertex positions. These particular full-name records fit single pages;
multi-page treasure control paths have host, not additional native, evidence.
Both batches restore checkpoint/save/heap/input state, retain blank isolated
saves, and shut down gracefully. Completed initial-post cases are not replayed.
The checkpoint binds the complete logs and records the limited fixtures: ordinary
items are selected by substitution at placement, and normal scheduling, normal
submenu entry, save/reload, gameplay review, and hardware remain unverified.

The initial reader fixture places graphics state at auxiliary offset `3800`;
that is too early for the larger treasure reader. The treasure fixture uses
auxiliary offset `4000` and a `D000`-byte allocation, with checked non-overlapping
ranges and independently modelled soft wrapping. Its layout model also passes
host comparisons against the actual page planner for explicit whitespace, glyph
pairs, full-width boundaries, and random complete text. Native owner tests remain
distinct from source-only direct decoder calls, which cannot prove rollback.
