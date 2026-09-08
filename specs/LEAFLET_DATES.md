# Leaflet dates and remaining notice/measurement consumers

## Current scope

`tools/audit_date_callers.py` checks the verified native ROM's direct date calls
against actual instructions in the built cartridge. The leaflet pilot has
23 direct calls across eight formatter entries: seventeen target the resident
English formatters, two use the complete English leaflet hour at the original
entry, and four retain native formatting. The installed calls belong to main
dialogue, ordinary resident preparation, and shop/Redd leaflet preparation. This inventory
does not establish indirect/inlined uses or imply that a changed target proves
correct formatting, capacity, publication, or gameplay.

The leaflet integration and remaining groups are:

| Consumer | Native calls | Required presentation |
| --- | --- | --- |
| Shop renewal leaflet | `809584B8` month, `809584D4` day, `809584F0` year | Complete month, ordinal day, and year in fields 0/1/2 |
| Shop sale leaflet | `8095BB0C` month, `8095BB2C` day, `8095BB4C` hour | Complete date and AM/PM time in fields 17/18/19 |
| Redd leaflet | `8095BB94` month, `8095BBB4` day, `8095BBD4` hour | Complete date and AM/PM time in fields 0/1/2 |
| Automatic notice date builder | `800A639C` month, `800A63BC` day | Month, one separating space, and ordinal day as one field |
| Fishing measurements | `809D6724`, `80A902EC` number-with-unit | Full English measurement and spacing, after native unit identity is checked |

The native suffix formatters are year `800C4084`, month `800C40F8`, weekday
`800C4168`, day `800C41B8`, hour `800C4228`, minute `800C42E8`, second `800C4350`,
and number-with-unit `800C43B8`. Weekday/minute/second have no remaining native
direct caller in the current pilot. This does not authorise unrelated string-bank
changes or remove the need to inspect other entry references.

## Native stack/storage evidence

All stack offsets and addresses here are hexadecimal. Whole function disassembly
establishes the following layouts; changed call targets alone are insufficient.

Shop renewal `809583B0..809585F4` has a `148`-byte frame. Day is at `sp+88`, month
at `sp+8C`, and year at `sp+90`; the mail record starts at `sp+9C`. Date input is
copied at `sp+74`. The month is copied into handbill storage before day and year
are formatted. A nine-byte month would overlap the later year temporary, not
currently live year data. The installed patch reuses that sequential scratch
span; twelve native date-block cases verify the complete fields, later year
local, and surrounding guards. Native time subtraction and shop-level branches
remain unchanged; the date-block fixture does not execute those branches.

Shop sale `8095BA60..8095BB80` has a `70`-byte frame. The saved incoming event
pointer is at `sp+70`; item name scratch is `sp+44`, hour `sp+50`, day `sp+58`,
month `sp+5C`, and the earlier one-byte item count is at `sp+60`. Count and item
fields are published before date formatting. Nine month bytes fit below the
incoming pointer but reuse the already consumed count storage. The hour's
eight-byte span before the day temporary fits the longest English time of seven
bytes. Item and selected-date identities must not change.

Redd preparation `8095BB80..8095BBFC` has a `30`-byte frame. Saved return address
is `sp+14`; hour is `sp+1C`, day `sp+24`, month `sp+28`, and the event pointer is
saved at `sp+30`. A nine-byte month at the existing address would corrupt that
pointer, which is reloaded for day and hour. Moving only the month input/output
pointer pair to `sp+18` gives nine bytes before the day field, reusing the hour
temporary before hour formatting. Both pointer words are changed, and the complete
cartridge-loaded preparer passes valid/invalid-date and surrounding guard checks.

Notice date `800A6384..800A63F8` uses a `28`-byte frame, four-byte temporary at
`sp+24`, length temporaries at `sp+20`/`sp+1C`, and saved incoming destination/day
at `sp+28`/`sp+30`. Both month and day use that same temporary. The original
output concatenates them without a space. The complete English combined result
can need fourteen bytes. Its local, final caller buffer, and ten-byte handbill
setter all require coordinated work; widening only the local cannot preserve
the complete date. The supplied English `mNtc_make_auto_nwrite_day_string` uses
a 24-byte local and inserts the separating space; its callers use a larger
buffer and wider free-string storage.

## Full AM/PM time

The existing resident `af_format_hour` deliberately provides only the numeric
hour for main-dialogue insertion. The English leaflet formatter must additionally
preserve the supplied `a.m.`/`p.m.` text and the space before it. Invalid hours
use midnight; midnight and noon both use twelve. The complete result needs up to
seven bytes. Do not substitute the numeric-only routine at the two leaflet sites.

`overlays/leaflet_dates/hour.c` replaces the original hour formatter body
(`800C4228..800C42E8`, 192 bytes) with 156 bytes of independently compiled original
code and a zero-filled tail. It calculates the complete time without imports,
division, relocations, mutable globals, or a stack frame. It writes exactly the
returned six or seven bytes; the unchanged native setter pads the final field.
The main-dialogue numeric-only call remains separate. Null destinations are
rejected without writes.

`tools/leaflet_dates.py` verifies the original whole actors, relocation files,
hour body, all three external direct hour calls, and absence of aligned literal
or direct interior references across the native DMA inventory. Dynamic/computed
references are not proven absent by that scan. Current resident source/code,
linked import addresses, complete compiled-hour identity, and conflicting patches
are checked before replacement maps change. Seven month/day/year call words,
two Redd scratch-pointer words, and the original hour body change. Actor frames,
file/BSS sizes, relocation data, saved layouts, and resident allocation do not grow.
The build option is `--english-leaflet-dates build/leaflet-dates`; it requires
the current resident module and English runtime.

## Source identities

Shop actor: VROM `0084D180`, linked RAM `809583B0`, 3,712 bytes, SHA-256
`412cc3f59962c1c5276fecb6081ffe3d3c7f6e69f201b152e6277a1fd1f57258`.
Relocations: VROM `0084E000`, 128 bytes, sections `(3216,496,0,0,23)`, SHA-256
`8e2dd79ceec1961a5bdee84fb01c9189e1532872b44efe64ce68603da28b462a`.

Event manager: VROM `00850680`, linked RAM `8095B8B0`, 27,264 bytes, SHA-256
`6883daac345e8aefd3c35ca1da307a3d198b76a470cee25b99e92aa0f030707d`.
Relocations: VROM `00857100`, 1,472 bytes, sections `(25424,1808,32,304,362)`, SHA-256
`515aa6085bb16b56ea051bfc2afe8e04551eca176a7f47bb6f0140b08fc73c49`.

The supplied English executable has these reference functions:

| Function | Bytes | SHA-256 |
| --- | ---: | --- |
| `aSL_SetShopRenewalChirashi_Notice` | 412 | `76d2569d8b9abfaa60c93a4285006b1efa05895c8f4060cc23395e1b38f49446` |
| `aEvMgr_actor_set_shop_handbill_str` | 304 | `b4e33b81b177d0f51a4af98b7408ffd17cee131c35052b9d2a1f0a4820492169` |
| `aEvMgr_actor_set_broker_handbill_str` | 172 | `006f97f4eee056b20da18b4b0675abe1fa7010bd8e8a7f64f35d5d0d3bec3d1c` |
| `mNtc_make_auto_nwrite_day_string` | 144 | `51427f54c5ad0e8fe4cb963d6b06cc32d9b76f54fb29497c0c181253f8d9fa4d` |
| `mString_Load_HourStringFromRom` | 220 | `5dbd604d57d8b273e4016f04e3eb0be0d0631bd814480a60979496179521f3e6` |

## Implementation and acceptance order

1. Full month/day/year and AM/PM field preparation is installed and passes the
   scoped native batch. Validate ordinary schedule/actor traversal separately.
2. Connect complete letter creation and publication at the actual owner boundaries.
   Generic classic loading into separate pointers cannot alone establish final
   snapshot ownership or protect against later native metadata/edge copies.
3. Extend notice combined-date capture and output together, preserving the GC space
   and full fourteen-byte maximum; keep full shop-name capture in the same audit.
4. Check fishing units against native measurements and the English reference.
5. Batch native field preparation, full snapshot/readback, failure retention,
   schedule boundaries, and saved metadata. Normal delivery/playthrough remains
   separate evidence from synthetic CPU fixtures.

## Executed validation

The audit output is `build/audits/date-callers-leaflet.json`. Four focused audit
tests check direct decoding, installed caller classifications, unexpected targets,
and altered same-address hour code. Six formatter/installer tests cover every
byte hour at sixteen unaligned offsets, invalid full-width inputs, supplied
English suffix identity, actor relocation at two bases, complete code mutations,
and atomic dependency/overlap rejection. The regression batch passes 895 tests;
the fourth audit test is additional to that batch.

The silent native batch passes 256 hour values and null rejection, twelve renewal
date blocks, twelve complete sale preparations, and 33 complete Redd preparations.
It executes 354 calls and 1,141 memory assertions, plus one post-restore assertion.
Whole actors/relocations, shared field restoration, live save, heap accounting,
guards, checkpoint restoration, blank FlashRAM/Pak, and graceful shutdown pass.
Renewal uses a test-only entry/exit in owned relocated code and does not execute
mailbox mutation or publication. Sale tests retain native ten-byte item names;
they do not establish wider item capture. Full letter creation, ordinary delivery,
notice output, fishing units, gameplay presentation, and hardware remain required.
The [work record](../docs/checkpoints/LEAFLET_DATES.md) pins artifacts and evidence.
