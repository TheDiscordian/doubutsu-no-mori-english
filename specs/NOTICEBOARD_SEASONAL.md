# Complete seasonal notice wording and native integration requirements

## Current implementation

`tools/notice_seasonal.py` provides all 41 complete English bodies for native
`01A4..01CC`. Its compiled creator and reader preserve native IDs in the existing
96-byte notice envelope and eight-byte saved RTC. The immutable supplied English
catalogue is unchanged. The complete ROM installs creation, failure-safe
publication, and full reading together. The application counter verifies those
installed resources before crediting the 41 source bodies once. Controlled native
creation, posting, same-session retry, and complete reader execution pass.
Normal gameplay, persistence, and hardware acceptance remain requirements.

Twenty-one bodies retain their matched GameCube wording and manual layout
unchanged. Fifteen adapt a matched reference for native facts. Five are original
translations because the supplied English notice group has no matching body:
Doll Festival stock, White Day mail, the blossom forecast, Children's Day stock,
and thirteenth-night moon viewing. `REFERENCES`, `EDITS`, `WRITTEN`, and `REASONS`
are the executable review definitions. A generated JSON file alone does not
approve changed text; builders must reconstruct the definitions from bound inputs.

The factory verifies the exact original ROM, registered catalogue-four bytes,
original calendar/preparer/scheduler instructions, and schedule/lunar tables.
Every result records the Japanese source hash, selected English reference ID and
encoded hash, final body hash, provenance, native free-field mask, and posting
date where scheduled. Every final field mask matches its Japanese source.

## Matching and native adaptations

Same-number donor bodies are not a reliable match. The mapped group deliberately
excludes donor Groundhog Day, Meteor Shower, Harvest Festival, and daylight-saving
notices. Important native differences are:

| Native ID | Retained meaning |
| --- | --- |
| `01A6/01A7` | Valentine's reminder/complaint, matched to donor `01A7/01A8` |
| `01A8` | Doll Festival; complete approved item name `hinaningyo` |
| `01A9` | White Day mailbox reminder from Pelly |
| `01AA` | Blossoms about 70% open by April 1st, best around the fifth |
| `01AB` | Cherry Blossom Festival at the shrine plaza |
| `01AC` | Copper joins aerobics at the upcoming Spring Sports Fair |
| `01AD` | April 20th Spring Sports Fair, not the vernal equinox |
| `01AE` | Spring sports timetable, matched to donor `01AC` |
| `01AF` | Children's Day stock; complete approved `samurai suit` name |
| `01B0` | Rainy season begins in mid-June, not late June |
| `01B3` | Final summer fishing Sunday is still ahead, not already finished |
| `01B5/01B6` | July 25th–August 31st, 6 a.m. aerobics at the shrine |
| `01B7` | Every Saturday in August, 7 p.m. fireworks; not July 4th |
| `01BA/01BC` | Both native moon-viewing occasions, with independent full dates |
| `01BD` | Fall sports message from Pelly, not Pete |
| `01BE/01BF` | Native October sports date and original daily timetable |
| `01C5/01C7` | Cold affects vegetation; the severe snow forecast is for tomorrow |
| `01C8` | Christmas Eve gifts, mailbox room, and not interrupting Jingle |
| `01CA` | New Year's shrine visit, not an absent wishing well |

Matched span edits preserve every manual newline outside complete rewrites.
The Spring Sports Fair date/venue adaptation retains the source's six-line
structure. All eight fully written/reworked bodies use six explicit lines,
including the intentional blank line in the second moon-viewing notice.
The twenty-one unchanged bodies retain all original spaces and glyph pairs.
Display wrapping may add continuation rows to fit full fields, but does not
delete characters or replace manual layout with automatic prose reflow.

## Native fields and scheduling

Native date selection `800A62EC..800A6384` scans 39 scheduled entries, indices
`0..38`. The dates at `8010B4B0..8010B4FE` are month/day halfwords. It chooses
the current or previous year with a 6 a.m. boundary. Bodies `01CB/01CC` remain
inventoried and translated even though this selector does not schedule them.
The GameCube's 43-entry ID/date table must not replace this N64 structure.

| Field | Native consumer IDs | Complete English capture |
| --- | --- | --- |
| 0 | `01AC/01B0/01B4/01C7` | Six-byte town identity, no Japanese village suffix |
| 1 | `01A8/01AF/01C1` | Complete shop name, up to sixteen bytes |
| 2 | `01BA` | First lunar date, full month, one space, ordinal day |
| 3 | `01BC` | Second lunar date, independently computed, same full format |
| 4 | `01BE` | Native October sports date, same full format |

The original common preparer `800A63F8..800A6450` captures the town with a
Japanese suffix and the shop at ten bytes. Those are not acceptable English
snapshot fields. The original annual preparer `800A6450..800A6548` converts two
lunar dates from the pairs at `8010B504`: month/day `08/0F` and `09/0D`, then
derives the October sports date. Do not substitute the donor's autumnal equinox.
The native batch checks actual helper execution and complete date capture for
2001; source binding alone is not proof of calendar behaviour.

The old combined date formatter has a four-byte temporary, no separating space,
an eight-byte caller buffer, and a ten-byte handbill setter. Widening one of those
alone corrupts or truncates English. Capture each complete date in the new
creator's owned workspace, retaining the native year and calendar calculations.
The longest general full-date field is fourteen bytes. See
[date capacity evidence](LEAFLET_DATES.md) for the exact old stack layouts.

The scheduler `800A65C4..800A680C` prepares at most five pending posts. Its
formatter call at `800A6778` receives `01A4 + native_index`; the native writer
immediately follows at `800A6780`. Pending year/index state is changed before
creation. A failed English allocation/read must not publish a partial post or
silently consume an undelivered notice. Runtime integration must preserve the
original retained-post policy while keeping the failed notice available for
retry. Merely skipping the writer on failure is insufficient.

## Compiled decoder and private creator

`compiled_resource` reconstructs the approved text from bound native/reference
inputs and produces 6,143 body bytes, 41 twelve-byte entries, and four complete
sixteen-byte shop fields. Generated data stays ignored and read-only in the
on-demand creator/reader. The shop fields retain the actual supplied notice names:
`Nook's Cranny`, `Stop 'n Nook`, `Nookway`, and `Nookington's`. Do not substitute a
remembered name from a different resource.

`runtime/notice/seasonal.[ch]` validates native identity, catalogue four, the exact
field mask, plain nonempty field bytes, and six-/sixteen-/fourteen-byte bounds.
It decodes the existing compact envelope in disjoint aligned scratch, checks the
selected compiled body and CRC, and uses the existing complete mail formatter.
Output is published only after complete validation. Unsupported/damaged records
retain the existing close/reopen error path; they never become manual text.

`af_notice_seasonal_create` is the first complete creator dispatcher, falling back
to the retained treasure owner and earlier letter creators. Its twelve-byte
descriptor is `AFNS | BE16 native ID | BE16 posting year | 00 00 00 F3`. It also
requires a disjoint readable sixteen-byte identity pointer and zero remail,
condition, and foreign arguments. The creator retains the 5,344-byte workspace.
It writes all 164 destination bytes only after packing and complete decoding.

Town capture uses the six-byte saved identity without a suffix. Shop capture calls
the native level getter `800C165C` and selects its complete compiled field.
Lunar conversion calls `800D60E4` with private four-byte input/output structures:
posting year, `08/0F` or `09/0D`. A zero return keeps the original lunar month/day,
matching the native fallback outside its supported table. Sports capture calls
`800D5CF8(year,10,14)` and uses `weekday ? 15-weekday : 8`. Full month, one space,
and ordinal day are formatted into owned sixteen-byte scratch. No global free
fields, calendar input tables, saved timestamp, or scheduler state are modified
by the creator. Calendar mocks establish this call contract, not native calendar
execution or astronomical accuracy.

## Failure-safe publication and reader installation

`overlays/notice/seasonal_owner.s` provides the 176-byte bridge at `800A6384`,
with zero padding through `800A6544`. A conservative scan of every stored,
decompressed DMA file finds the two external helper calls at `800A66C8/800A671C`
and six internal helper jumps/branches; no aligned literal or nearby LUI/address
pair enters the reclaimed helpers. Both external calls are removed. Exact source
guards and instruction encoding bind this reuse; it is not a general indirect
reachability proof.

The bridge uses 240 stack bytes: 164-byte creation staging, a sixteen-byte private
identity, a twelve-byte descriptor, outgoing arguments, and saved return address.
It copies only the successful 96-byte message into the original pending post,
retaining the eight-byte timestamp. The unchanged native writer then appends or
shifts the complete 104-byte post. Only after that return does the bridge store
the current loop index/year in the runtime posting cursor.

The posting cursor at `80137918..8013791F` belongs to Common runtime state,
outside the FlashRAM payload `80126EA0..8013681F`. Native initialization derives
the cursor from the save-check time. Retaining this cursor proves same-session
retry, not pending-notice persistence across saving and reloading. Persistence
of an interrupted backlog remains an explicit acceptance requirement.

The old pre-publication cursor stores at `800A66C4/800A66CC` are removed.
`800A6778` calls the bridge. The old writer pair at `800A6780/800A6784` becomes
`beq v0,zero,800A67E4` plus an inert delay slot. Failure exits before the loop
increment, completion flag, or checked-date copy. The successfully published
prefix remains committed, and the failed notice remains pending for retry.
The native maximum-five backlog selection, schedule dates, timestamp construction,
and no-pending treasure branch remain unchanged.

The complete reader tries initial, treasure, and seasonal restoration with the
same temporary workspace and two existing full-body caches. Manual whitespace,
full fields, all continuation pages, and native control precedence remain.
Its complete size is 24,304 bytes with 720 relocation bytes. Appended code ends at
offset 14,768, read-only data precedes cache offset 21,856, and original BSS keeps
its addresses. The submenu growth reservation is 20,480 bytes, producing a
234,880-byte dominant pool sum. This is 4,096 more than the treasure-only profile;
the smaller profiles and their exact compiled identities remain verifiable.
The resident module/bootstrap and four-MiB address bounds are unchanged.

`--english-notice-seasonal` requires the seasonal reader, complete seasonal
creator, and treasure installation. The installer validates actual cartridge
configuration/code/resources, exact scheduler edits, reader relocations, pool
instruction, and complete source approvals before publishing replacement maps.
The combined counter uses this same installation verification, not a source-only
approval file. The full local recipe is `bash tools/build_seasonal_pilot.sh`.

## Validation and remaining work

Six source/model tests cover all identities, 82 body/capitalization records,
matching, native facts, exact manual-break retention, complete field bounds,
source mutations, and invalid saved identities. The C page-planner suite also
checks all 82 new bodies against an independent layout model and verifies that
all text is reachable, including complete names and fourteen-byte dates.
All 54 creator, six decoder, and fourteen combined-reader tests pass normally
and with address/undefined-behaviour sanitizers. They cover every body and both
capitals, complete fields, calendar call/fallback contracts, every body-byte CRC
fault, malformed/overlapping buffers, earlier dispatchers, complete page access,
mixed cached text, failure/retry, and unchanged saved posts.
Six creator artifact tests and eleven owner/reader/installation/accounting tests
pass, including independent builds, three relocation bases, precise source
guards, partial-install rejection, actual-hook removal, full ROM/UPS retention,
and exactly 41 newly credited source IDs.

The completed silent native owner batch passes all 78 scheduled body/capital
cases, four unscheduled direct creations, and five interrupted-backlog positions
with exact-prefix retention and suffix retry. It executes the original calendar,
shop getter, scheduler, writer, and cartridge-loaded creator, with 359 calls and
513 assertions. The controlled year-2001 calendar produces October 1st and
October 29th for the two lunar dates, and October 8th for the sports date.
These are observed native results, not an external astronomical claim.

The separate reader batch passes all 82 complete bodies, 84 native draws,
11,930 glyphs, and 47,720 vertex positions. Its two continuation-page draws
preserve all source characters. The larger fixture uses a `F000`-byte auxiliary
allocation with game/graphics state at offset `6000`, beyond the complete reader.
All 183 calls and 466 assertions pass, with both batches restoring state and
checkpoints, retaining blank isolated saves, and shutting down gracefully.
Eight frozen-evidence tests retain these results without replaying game calls.
The reader uses controlled owned submenu storage, not normal initialization or
the enlarged production pool. Native fallback-year/date-boundary/all-shop-tier
and null-allocation edge checks remain, alongside normal gameplay, old saves,
save/reload, review, hardware,
patch-only release, and the title/keyboard stretch work remain project requirements.
