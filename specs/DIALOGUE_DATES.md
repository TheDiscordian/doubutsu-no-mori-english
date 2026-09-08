# English dates prepared by resident conversations

## Native scope and storage

`--english-dialogue-dates` connects the ordinary resident-dialogue overlay's
year/month/day preparation to the existing resident English formatters. It covers
the overlay's reunion dates, converted lunar dates, event reminders, and
[complete birthday item fields](BIRTHDAY_FIELDS.md). The RTC,
schedule, calendar conversion, saves, and other actors' helpers remain unchanged.

The overlay is VROM `00815B70`, RAM `8091D7B0`, with 17,968 file bytes and
352 BSS bytes. Relocation VROM `0081A1A0` has 2,240 bytes. Complete original
hashes and sections are shared with [NPC letter-show evidence](NPC_MAIL_SHOW.md).
Both file sizes and BSS size stay unchanged.

The helpers clear a ten-byte BSS buffer at `80921E08`, format a value, and pass
the actual length to native `mMsg_Set_free_str` (`8009D6D0`). The message window
has twenty ten-byte free fields at `+38`. English months use at most nine bytes,
ordinal days four, and years four. Padding remains spaces; input widths,
caller-selected field numbers, and neighbouring fields are preserved.

| Helper | Replaced call | English function |
| --- | --- | --- |
| Year `8091D954` | `8091D980`, originally `800C4084` | `af_format_year` |
| Month `8091D9B8` | `8091D9E4`, originally `800C40F8` | `af_format_month` |
| Day `8091DA1C` | `8091DA48`, originally `800C41B8` | `af_format_day` |

The functions reuse [English formatter semantics](ENGLISH_DATES.md). Globally
shared native formatters are not replaced.

## Lunar conversion and leap month

Calendar helper `8091EBB8` reads the year at `80136FC2`, calls the supplied native
conversion on the requested month/day, and prepares caller-selected free fields.
The reminder routine calls it at `80920028` for lunar eighth-month day 15 into
fields 16/17, and at `80920044` for ninth-month day 13 into fields 18/19.
Native `lbRk_ToSeiyouReki` is `800D60E4`; `lbRk_ToKyuuReki` is `800D6218`.

Commands `3C/3D` select fields 16/17 through handlers `800A1690/800A16B8` and
common insertion `800A134C`. They must remain the calculated event date, not the
current date of the conversation.

### Actual old-calendar quiz request

Quiz `246D` begins with `0C 07 0001`. The native command writes quest row nine,
slot seven. The ordinary demo dispatcher at `809215E4` reads the manager's
16-bit type/value at `+1AC/+1AE`; table `80921D88` entry seven points to
`80920F20`. Value one prepares the two moon-viewing pairs in free fields 11/12
and 13/14, then converts the current RTC month/day through `800D6218` and
`8091EBB8` into free fields 15/16. Other values do nothing. This is a distinct
caller from the reminder routine's fields 16/17 and 18/19.

Native current day is `80136FBF`, month `80136FC1`, and year `80136FC2`.
Command `3B` selects free field fifteen through `800A1668`; `3C` selects field
sixteen through `800A1690`. Neither is an item/birthday field. The quiz therefore
requires the complete English ordinary-date patch, not an English text-only
substitution or the globally unrelated calendar formatters.

Complete source-bound ranges:

- Calendar order `80920F20..80920FAC`:
  `9bf9caeea2fb53a6fcd19f14919da05bd6ca1b85ec63d0efa93afbb56f540c9c`.
- Dispatcher `809215E4..80921618`:
  `2d8086d5a521c3b80975007d2a9c71d1e327b96bcc6337a7cb835306616bc344`.
- Ten-entry table `80921D88..80921DB0`:
  `bf46ef90ed07efe5040c9382dd3f247769c475398261e07859f5e7319049f890`.

The complete supplied English quiz keeps every word, newline, pause, native
request, field, and branch. Its canonical native menu receives the separately
bound `0025/0051` contextual labels: affirmation reaches `2472`, denial reaches
`2476`. The final displayed payload is the complete supplied reference, 81
stored/157 conservatively expanded bytes. Its generic two-free-field width
warning remains visible; the complete actual month/day values are not shortened.

The month-13 branch's five-byte Japanese literal has only eight bytes before
a live jump table at `80921BE0`. Instead of overwriting that table or shortening
the English, the patch uses the resident ten-byte `af_leap_month` value,
`leap month`, and passes length ten. Its old pointer's HI/LO relocation entries,
`45001464/46001468`, are removed so native loading does not shift the fixed
resident address. The remaining 550 entries retain their order and the file
length is unchanged. Six date instructions change: three formatter calls,
the address pair at `8091EC14/8091EC18`, and the length at `8091EC28`.
The birthday entry adds a guarded jump and delay-slot nop at `80921324/80921328`,
making eight changed words in the complete installed overlay. No birthday
relocation is added or removed; its native dispatch table remains unchanged.

The native conversion table covers 2000–2032. Out-of-table dates and failed
conversion handling remain boundary-audit work. This patch does not extend the
table or claim those cases are safe.

## Installation contract

`tools/dialogue_dates.py` verifies complete original files, the resident-module
identity/bounds, the full literal, expected instructions, and relocation pair.
Overlapping patches fail. The builder installs both files before dependent text.
Moon-viewing drafts declare `runtime_requirements: [ordinary_dialogue_dates]`.
Validation compares both complete installed files, not just an option or text
metadata. Missing patches and unknown/duplicate/malformed requirements fail.
The candidate generator takes the same `--english-dialogue-dates` option and
requires the resident module. Without it, dependent drafts are recorded in
`drafts-withheld.json` and excluded from output; they are not replaced with
incompatible GameCube references. The ordinary non-module build remains usable.

Reviewed references may declare the same exact requirement in their identity
approval. The candidate generator withholds a dependent reference when the
option is absent and records `runtime_requirement_unavailable`; enabled edits
carry the explicit requirement. The builder consults both the edit and the
reviewed identity independently. Omitting candidate metadata or supplying an
empty list cannot remove the identity's dependency. Explicit reference lists
must name this supported requirement and belong to a main-message approval.
Both complete installed files remain mandatory; unknown or malformed lists fail.

The NPC letter-show harness recognises only this exact extra patch and derives
the corresponding relocated image. Unrelated overlay changes remain rejected.
The actual letter-show handlers and saved-letter inputs are unchanged.

## Verification

Host tests check all eight words, two removed relocations, unchanged sizes, two
relocation bases, source/module/literal bounds, overlap rejection, complete
dependencies, and all four festival command sequences. Portable tests cover all
retail-width formatter inputs and the ten-byte nonterminated leap-month field.

The native batch uses owned heap memory and the real cartridge overlay loader,
comparing complete relocation and zeroed BSS with an independent expectation.
Fifty-three preparations cover months, days, ordinal exceptions, years, bounds,
ten-byte scratch contents, and unchanged neighbouring fields. Thirteen conversions
cover both moon-viewing dates across six years and the native 2001 leap month.
Six full festival-message loads and eight actual date insertions cover all four
drafts and two years for each dated message. Complete save retention, RTC-year
restoration, heap/stack/module guards, freeing the allocation, and checkpoint
restoration pass. Normal resident selection, final rendering, full seasonal
coverage, and original-hardware acceptance remain separate requirements.

`calendar_quiz_test_scenario.py` combines date preparation and every contextual
answer case into one isolated checkpoint. Six current-date cases cover 2000,
2001's leap-month start, 2004's February 29, 2026, 2030, and 2032. Each executes
the actual quiz request, checks the complete quest table, invokes the real
relocated demo dispatcher, compares all twenty free fields against independently
called native conversions, and inserts both complete quiz fields. Two non-one
orders check the no-op branch. The complete manager, clock, saved game, code,
heap/stack/module guards, actor-order pointer restoration, and allocation lifetime
are checked. Exact completed results belong in the work log. This does not
execute normal request polling, calendar scheduling, quiz rewards, or hardware.

The completed combined run passes 496 calls, 294 explicit expected returns, and
822 memory assertions over 2,039 recorded steps. It includes all six quiz dates,
two no-op orders, 53 preparer cases, thirteen earlier and eighteen direct quiz
conversions, twelve date-message loads, twenty date insertions, 48 answer
selections, and 44 contextual branch cases. All guards, saved-game/clock retention,
allocation freeing, one checkpoint restore, silent shutdown, and blank isolated
saves pass. All 700 regression tests pass, including thirteen date/dependency
tests. A separate complete-layout audit checks all 403 month/day combinations;
the widest date line is 88 pixels. The generic free-field warning remains.
