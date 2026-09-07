# English dates prepared by resident conversations

## Native scope and storage

`--english-dialogue-dates` connects the ordinary resident-dialogue overlay's
year/month/day preparation to the existing resident English formatters. It covers
the overlay's reunion dates, converted lunar dates, and event reminders. The RTC,
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

The month-13 branch's five-byte Japanese literal has only eight bytes before
a live jump table at `80921BE0`. Instead of overwriting that table or shortening
the English, the patch uses the resident ten-byte `af_leap_month` value,
`leap month`, and passes length ten. Its old pointer's HI/LO relocation entries,
`45001464/46001468`, are removed so native loading does not shift the fixed
resident address. The remaining 550 entries retain their order and the file
length is unchanged. Only six instructions change: three formatter calls,
the address pair at `8091EC14/8091EC18`, and the length at `8091EC28`.

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

The NPC letter-show harness recognises only this exact extra patch and derives
the corresponding relocated image. Unrelated overlay changes remain rejected.
The actual letter-show handlers and saved-letter inputs are unchanged.

## Verification

Host tests check all six words, two removed relocations, unchanged sizes, two
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
