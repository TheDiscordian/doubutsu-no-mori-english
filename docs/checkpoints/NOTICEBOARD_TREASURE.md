# Complete treasure text, item articles, and native integration work

## Implemented

The complete installed build is `build/notice-treasure-pilot`. It contains the
transaction creator, native treasure bridges, and full-body reader together;
all eighteen treasure bodies receive verified application credit. Native creation
and full reading pass the bounded batches below. The complete translation project remains
active, including seasonal/general text, names, review, persistence, hardware,
patch-only release preparation, title artwork, and keyboard stretch work.

All eighteen treasure notices have complete C/Python decoding models, including
the native-specific `01F4` town/row clue. Seventeen use the supplied GameCube bodies
unchanged. The adapted two-line heading keeps the six-line structure, blank third
line, remaining wording, and sender decoration without disclosing the item.
Source lengths/CRC32 values and exact native field masks guard every body.

The optional text-only creator captures full names, numeric N64 coordinates, and
the original town identity, then verifies complete decoding before publishing its
compact output. It uses the existing 164-byte loader destination only as scratch:
the first 96 bytes are the notice, and the final 68 are zero. Native saved records
remain 104 bytes with their RTC field at offset 96. Creator workspace stays 5,344
bytes; no native save or buried-object state is touched by the creator.

## Transactional native owner

The [transaction owner](../../specs/NOTICEBOARD_TREASURE_OWNER.md) adds original
burial, a sixteen-byte stack-only undo record, complete text creation, and native
publication. The fixed bridge can undo a failed second loader allocation without
loading any code again. Ordinary items and all 25 native pitfall shapes are
handled; no-change or unexpected deposits restore the selected acre immediately.
No saved record or resident allocation grows.

Use `--notice-owner` in addition to the complete treasure/article creator flags.
Current images are `build/noticeboard-treasure/owner-creator` and
`owner-creator-repeat`; native bridges are `owners` and `owners-repeat`.
Independent binaries, relocations, and manifests agree.

| Artifact | Size | SHA-256 |
| --- | ---: | --- |
| Transaction creator | 48,752 | `d68503a283a0186402c70a4f1c6969702fb76a3b6ee9da01f82f6ff25cebd9a8` |
| Transaction relocations | 752 | `434c01f2c661f8b6376485bbe50bb1ee54cb51e2d6fb95f51a5dd011e872df86` |
| Transaction manifest | 16,450 | `bf50fdf98a57591055dca453d4bb30f5d3bbfd3d96898aab60cfd04a4bc7f682` |
| Native bridges | 176 | `c9d5f554774e693859c185a28789458201c29edb6a7218dac1c17b0d653c5596` |
| Native bridge manifest | 689 | `039852bf32486ceab386fe42803e650b7532b12c4c79d1e4df1cf3084c76c334` |

Fifty owner/creator tests have passing host and sanitizer results. They retain
every earlier dispatcher and cover thirty acres, all 256 unit positions, every
pitfall shape, existing flag bits, failed/malformed deposits, exact undo, source
failures, and complete publication. The expanded publication case separately
checks all eighteen bodies in both capitals with ordinary items and pitfalls:
72 complete source-model, saved-message, and RTC comparisons. That case passes
normally and with sanitizers. Five artifact tests bind all bridge words, guard
every changed native interval, verify independent builds, and retain both the
text-only treasure and quest-reply creator manifests. Four retained initial-reader
evidence tests pass without native replay.

Logs are `owner-tests.log`, `owner-focused-tests.log`, `owner-sanitizer-tests.log`,
`owner-publication-tests.log`, `owner-publication-sanitizer-tests.log`,
`owner-artifact-tests.log`, `owner-initial-reader-retention-tests.log`, and both
owner/creator build logs under `build/noticeboard-treasure/`. The current playable
ROM's main code accepts guarded patch construction: resulting code length 826,800,
SHA-256 `99f690b9a4bc523c87ab13206985b60c3b90df298e22d54ec786b80e6423bbe6`.
The complete installed ROM has that same main-code digest. The host rollback
helper models the bridge's stores only; the native batch below separately
executes actual placement, loading, undo, and publication from this ROM.

## Installed complete reader and ROM

The [treasure reader profile](../../specs/NOTICEBOARD_TREASURE_READER.md) adds all
eighteen decoder routes while retaining the initial reader source and its frozen
native evidence. Independent `reader` and `reader-repeat` builds agree. It grows
the reader by 2,144 bytes inside the existing submenu reservation; no saved or
resident structure grows. The complete ROM changes only main code, reader and its
relocations, submenu metadata, the creator and its resident configuration, and
the physical DMA table. Every other translation resource is unchanged.

| Artifact | Size | SHA-256 |
| --- | ---: | --- |
| Complete reader | 15,984 | `61180ff0e7dc2b99518bb8c3678b7a09a4c0461005744d0d43d8d51ae58a7a7e` |
| Reader relocations | 640 | `5eac036261e2bda36c9bf5545d800d12bc2621438958eea06def3e98bab1b837` |
| Appended suffix | 9,200 | `8b4dbfefe26ff39b938cefa28d1323b5983794a24231f505ec84b71e831934ff` |
| Complete ROM | 33,554,432 | `df1ef97f9376e4cb0f0cdfc7e8845de837f61a1d9427334333b69a8f3c5f035d` |
| UPS patch | 4,474,425 | `e97ead04029a9202fb9a77fc77d19ec01e2565ade4e658b8ab287e54364f0ed3` |

Ten combined-reader tests and the same sanitizer tests pass. The complete-body
case checks all eighteen templates, both capitals, and all five articles, with
all characters reachable through pages and no saved-message edits. Other cases
cover mixed initial/treasure caches, malformed fields, every read failure for the
adapted template, retry, unchanged native-control precedence, and retained dates.
Eight new artifact/installation/accounting tests pass. Ten initial installer tests,
five owner artifact checks, and four retained native-reader evidence checks pass.
No completed native initial batch is replayed.

Logs under `build/noticeboard-treasure/` are `reader-build.log`,
`reader-repeat-build.log`, `full-build.log`, `reader-tests.log`,
`reader-sanitizer-tests.log`, `reader-install-tests.log`,
`initial-install-retention-tests.log`, `reader-owner-retention-tests.log`, and
`reader-native-retention-tests.log`. The combined counter verifies the current
ROM's complete owner/reader installation before adding precisely the eighteen
source bodies; the source inventory and denominator remain unchanged.

Rebuild the reader with `python3 tools/build_notice_overlay.py --treasure
--module build/notice-treasure-runtime/module.json --output
build/noticeboard-treasure/reader`. The complete ROM uses the existing full-build
options, with `--npc-mail-generation build/noticeboard-treasure/owner-creator`,
`--english-noticeboard build/noticeboard-treasure/reader`,
`--english-notice-treasure build/noticeboard-treasure/owners`, and
`--output build/notice-treasure-pilot`. The builder rejects partial installation.

## Text-only creator profile

`build/noticeboard-treasure/article-creator` and `article-creator-repeat` contain
identical images, relocations, and manifests. The builder requires
`--notice-treasure --item-articles build/noticeboard-treasure/articles/articles.bin`,
the complete quest-reply chain, and `--mail-glyphs`. Fado object ordering follows
the linker's text order; the linked ELF independently agrees with the relocation
inventory.

| Artifact | Size | SHA-256 |
| --- | ---: | --- |
| Creator image | 46,592 | `eda487cce42ace3d63bbbc1709377bc7a51471f0232d11c1add8c80b059be980` |
| Relocations | 672 | `2f7a3e1fb6bc95c9c1d63fbe218f5f34581edabfeb291138eb84b71fc9b76212` |
| Creator manifest | 15,687 | `e9bed91641693f46bdf6fde790868756e75c9a6f5ad98754d4aa5b02ec1aa921` |
| Item articles | 8,576 | `639aaeb04f49e5c5e06daaae7c395bd4691fb68f3ec0d3ddd018e0946e04686d` |
| Resident reservation | 32,768 | `493bc25a922bbd9d321759677134520bbb179413985f0e047df45e6e432664c6` |
| Bootstrap | 212 | `9c20b82708856897c19301bb23e35b84335482f9c10d4dd5ba5c3a3f7fb1d10f` |

`build/notice-treasure-runtime` has the current complete source inventory. Its
module, symbols, and bootstrap retain the initial notice build's binary layout.
The new notice unit is explicitly excluded from permanent resident compilation.
The creator entry uses a 112-byte native stack frame, article lookup uses 32,
and decoder parts use 48, apart from called functions. These are compiler reports,
not a measured complete gameplay stack bound.

## Bound native item articles

`tools/item_articles.py` verifies the supplied REL/symbol map, rebuilds the full
approved name resource, and binds each translated name to its exact English
reference field and associated article entry. N64-specific names use explicit
approvals in `translations/n64-item-articles.json`, including `an N cube shirt`,
`some quest money`, and the bare `1,000 Bells` amount. No vowel heuristic is used.

The immutable profile covers all 3,563 translated storage slots. The 981 remaining
untranslated slots have a rejecting marker, not a guessed article. Four identical
furniture rotations share one entry; the table has 1,703 entries. Each stores an
article byte and the CRC32 of the exact sixteen-byte padded name. Its header binds
the whole name resource. See [item articles](../../specs/ITEM_ARTICLES.md).

The creator uses the same original `800BF10C` conversion as the name loader and
checks the complete field CRC before capture. The native request's byte ten is
reserved zero, not a caller-supplied article. Unknown/mismatched names fail without
publication. Clues that do not name the item do not require item-name/article
reads. The installer requires the exact enabled name resource; the embedded-profile
check rejects changed articles even if the manifest recomputes its own image hash.

## Verification

Forty-five host creator/dispatcher tests pass, including all eighteen templates,
both capitals, all five article choices, every villager identity, sixteen-byte
item names, malformed descriptors/identities, overlap guards, every selected
cartridge-read failure, article/name failures, missing resources, and recovery. Earlier NPC, Mom,
departed, event, HRA, postal, museum, shop, and quest-reply dispatch tests run through
the new first dispatcher and pass.

Six article source/runtime/installer tests pass. They cover every 16-bit native
ID, placed conversions, unknown entries, every changed byte of each known directly
addressed name, source/provenance mutations, missing original approvals, and changed
installed-name configuration. The same six tests and all 45 creator tests pass
with AddressSanitizer and UndefinedBehaviorSanitizer. Five artifact tests bind
independent builds, sources, resources, loader entry, unchanged resident code, and
the previous quest-reply creator. Four retained initial-reader evidence tests pass
without replaying native calls. The unchanged decoder retains its five passing
host/sanitizer tests; this article change does not repeat that completed batch.

Current logs are under `build/noticeboard-treasure/`: `article-tests.log`,
`article-creator-tests.log`, `article-sanitizer-tests.log`,
`article-creator-sanitizer-tests.log`, `article-artifact-tests.log`,
`article-initial-reader-retention-tests.log`, and both article-creator build logs.
Retained decoder logs are `decoder-tests.log` and `decoder-sanitizer-tests.log`.
Cross-compiled notice
helpers are in `mips/`; their object SHA-256 is
`fccc10a6bdaad414aed228a0c56e3c2b1721aa188b7cf429b6055a2cb87614f4`.

## Completed native execution

`tools/notice_treasure_scenario.py` binds the current installed ROM, source helper
instructions, native pitfall profiles, RNG seeds, full names, and complete
source-model records. Its owner batch is `build/smoke-notice-treasure-05`;
the complete reader batch is `build/smoke-notice-treasure-reader-01`.
Both are terminal successful runs with audio disabled, no screenshots, no save
seeds, no permitted FlashRAM/Pak writes, and no Expansion Pak enabled.

The owner executes the actual scheduler `800A5F08`, placement, deposit callback,
both fixed bridges, native allocator, and cartridge-loaded creator. It verifies
18 templates times two capitalizations times two buried-object kinds: 72 exact
96-byte publications and RTCs. All 25 native pitfall shapes appear. The fixture
provides one eligible unit in a controlled field, familiar `Octavian`, and a
six-byte town name. Pitfalls come from original RNG selection; ordinary cases
substitute wide-name item `11FC` at the original placement call. The random
furniture selector is not exercised.

Eleven additional cases pass: allocation failure before each transaction phase,
missing catalogue, missing names, creator CRC failure, unsupported hole profile,
no eligible unit, early hour, recent burial, already checked date, and no familiar
animal. Actual null malloc returns are observed under bounded heap pressure.
Phase-two failure restores the exact foreground/flag values without needing
another allocation. Every successful case checks the whole saved payload against
only its intended burial, complete post/RTC, and buried-date edits. RNG draws,
unrelated text fields, detached creator state, heap accounting, code, and guards
are retained. All 171 calls and 1,829 assertions pass.

The reader loads the native submenu owner and complete English reader from the
cartridge. Its separate fixture supplies exactly the same 72 records verified
above; it does not perform normal menu navigation or share the owner run's live
field state. All complete cache bodies, page spans, saved records/RTCs, 72 native
draws, 9,148 glyphs, and 36,592 vertex positions pass. These selected real-name
records fit single pages. All 157 calls and 410 assertions pass. The larger
fixture uses auxiliary size `D000` and graphics state at `4000`, avoiding the
initial fixture's overlap. L/R handling supports longer cases, but this batch
does not establish new native multi-page treasure evidence.

Both batches execute cleanup, restore their complete saved payload and globals,
free fixture allocations, reload their checkpoints, verify scratch RAM is zero,
and shut down gracefully. FlashRAM and Pak retain the established blank hashes:
`b5a41c3758763bbec72769fab4a2533bf2db0b6312d93d25a695f9e4b9e02260`
and `ab2a6e04fd3ceb36594f1216c888a1b8bd0a3ba0a94f715a7c7601e98c49ec51`.
This is not save/reload or hardware acceptance.

| Evidence | SHA-256 |
| --- | --- |
| Owner results, 2,711 records | `352d439d23a1fec0107fa0486bb3a00698d43d9011a1eba29379adccd156a3b7` |
| Owner scenario | `bc702ef981c0b8241b9c2fb8df8d716102b800fd6c1e4dc8eb390e0f1687fdbb` |
| Owner checkpoint | `441127269857d9a9aae3c03c3bf7e79133ececbf08557e098ef2eba43e48a368` |
| Reader results, 720 records | `adc8c1ad1ba716ba23b3b557316d4895dcb8bfa1b794490e581d79b1d798beef` |
| Reader scenario | `9b5540227bbc765e2f7f173f349847c7de20814dedee3f556945fa629cbaadba` |
| Reader checkpoint | `09c837cabb70d93a0c81e3808336fe7aee22c265a5eeccf3a5a67cde494ae6d9` |

Logs under `build/noticeboard-treasure/` are `native-owner-entry.log` and
`native-reader.log`. Five frozen-result tests bind both completed runs and the
actual published/read records. Four retained initial native evidence checks pass
without replay. Seven scenario/transport tests and six page tests pass, including
the independent native fixture layout. `native-evidence-tests.log` and
`native-initial-evidence-retention.log` retain the evidence-check results.

Earlier owner attempts `01..04` are terminal fixture/debugger failures, not
acceptance. The installed ares JIT does not reliably stop at the chosen
mid-basic-block call sites. The successful observer uses actual callee entries
and post-call block starts, removes stopped breakpoints before resuming, and
rearms shared entries between phases. No native game-code fix is inferred from
those failed observations. The reader batch succeeds without a retry.

## Remaining execution and text

Continue all forty-one seasonal bodies with actual native event/calendar/venue
matching, complete English fields, creation, and full reader installation.
Retain source meaning where donor IDs differ; do not import unrelated Groundhog
Day, Harvest Festival, Meteor Shower, or daylight-saving announcements. Remaining
normal scheduling, ordinary random furniture selection, normal menu controls,
old saved automatic posts, saving/reloading, resource retry across gameplay,
human review, and hardware acceptance are not established by these fixtures.
Do not replay the completed native initial or treasure batches. The complete
translation, review, patch-only release, title art, and keyboard stretch goals
remain active; this integration is not project completion.

## Native burial evidence and implementation direction

Native placement is `8008EA5C..8008ECA0`, SHA-256
`3009f5d79b645a51c8c86bac40ac88a41e8e3181a5885b72194db969fea6f766`.
Its frame is 152 bytes. It selects among thirty eligible acres, with foreground
base `8012D148`, 512 bytes per acre. Buried flags start at `801362DC`, 32 bytes
per acre. The call at `8008EC44` passes the foreground pointer, item, column, row,
buried-flag pointer, and eligible-unit count to `800A3E34`.

The deposit function is `800A3E34..800A3F70`, SHA-256
`c98de5761cb2d728ad36c720331480b947db4d6d465ba68b43a598ed1c846373`.
It chooses one eligible empty unit. Ordinary treasure writes the item halfword
at `800A3EE8` and its buried-row halfword at `800A3F14`. Pitfall `2512` instead
calls the native hole-number helper and writes `002A + hole_number` at
`800A3F30`, without changing buried-row flags. With no available hole number,
it writes nothing. Placement still returns success after calling this void
function, so that result alone does not prove burial. The scheduler explicitly
selects pitfalls at `800A6110..800A6134`; this branch is reachable.

A scan of every extracted native file finds only these direct calls:
`800A6214 -> 800A5E58`, `800A6170 -> 8008EA5C`, and
`8008EC44 -> 800A3E34`. This inventory does not exclude computed indirect calls.
The old town helper is also called at `800A6400`; do not reclaim it together with
the treasure-only field helper.

The compiled before-burial transaction snapshots the chosen acre's
512 foreground bytes and 32 flag bytes, invokes the unmodified deposit function,
then reduces the actual change to a small undo record. It retains that record
until complete post creation/publication succeeds and restores immediately inside
the loaded transaction if deposit changes an unexpected set of fields. This handles
duplicate items elsewhere and pitfalls without guessing which object was placed.
Allocation/read failure before this transaction runs does not call burial. Later
creator failure reaches the fixed undo stores even if allocation fails.

This implementation is not installed code. Verify native lifetime/stack ownership,
RNG and animal/template retention, cleanup, and eligibility in the combined batch.
The 352-byte scheduler frame has formatter scratch at `D0..F7`
available once native formatting is removed; its candidate list starts at `FC`.
A 164-byte staging copy at `68` would corrupt that list. Keep loader staging in
its wrapper's own frame; copy only verified compact output/undo data to the parent.
