# Complete seasonal notice wording and native integration requirements

## Current implementation

`tools/notice_seasonal.py` provides all 41 complete English bodies for native
`01A4..01CC`. Its source-model records preserve native IDs in the existing
96-byte notice envelope and eight-byte saved RTC. The immutable supplied English
catalogue is unchanged. This is reviewed text and host formatting, not installed
creation or reading; none of these new routes earns application credit yet.

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
Actual native helper execution and complete date capture remain required; source
binding is not proof of calendar behaviour.

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

## Validation and remaining work

Six source/model tests cover all identities, 82 body/capitalization records,
matching, native facts, exact manual-break retention, complete field bounds,
source mutations, and invalid saved identities. The C page-planner suite also
checks all 82 new bodies against an independent layout model and verifies that
all text is reachable, including complete names and fourteen-byte dates.
No native seasonal execution or installation is claimed.

Next add the complete C decoder and creator route, full private field capture,
failure-safe scheduler/publication handling, and coupled reader installation.
Keep old initial/treasure identities and saved envelopes compatible. Then build
the complete translation ROM, verify all earlier resources, and run one bounded
seasonal batch. Normal gameplay, old saves, save/reload, review, hardware,
patch-only release, and the title/keyboard stretch work remain project requirements.
