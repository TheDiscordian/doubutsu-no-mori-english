# Complete seasonal English text and pending runtime integration

## Completed source work

All 41 native seasonal/general board bodies `01A4..01CC` have complete reviewed
English definitions in `tools/notice_seasonal.py`: 21 unchanged supplied English
references, fifteen native-specific reference adaptations, and five original
translations. The [seasonal specification](../../specs/NOTICEBOARD_SEASONAL.md)
records calendar, venue, speaker, field, publication, and presentation constraints.
The source review retains both native moon-viewing dates, April 20th spring
sports, October fall sports, every-Saturday-in-August fireworks, White Day,
Doll Festival, Children's Day, and the shrine.

`python3 tools/notice_seasonal.py` generates the source-bound review and 82
complete body/capitalization record models at `build/noticeboard-seasonal/review.json`.
Its SHA-256 is
`be21b930f1a0e12ddf15e23b0d88c454673f05738280b544f7886759a9f4c4c4`.
Each entry records its source/reference/output identity and original posting
date. The longest expanded sample is 170 bytes. The five original bodies and
three complete rewrites retain six explicit lines each; span adaptations preserve
their matched reference's manual newline counts.

All six review/model tests pass. All seven C page-planner tests pass, including
the new 82-case comparison against independent expected rows. Logs are
`build/noticeboard-seasonal/review-tests.log` and `page-tests.log`.
One initial test incorrectly required every English notice to exceed 96 bytes;
the 96-byte sports timetable disproves that assumption. The corrected test checks
the exact complete body and capacity without imposing an unnecessary minimum.
No translation was shortened to satisfy a test.

## Current cartridge and evidence

The newest complete ROM remains `build/notice-treasure-pilot`, SHA-256
`df1ef97f9376e4cb0f0cdfc7e8845de837f61a1d9427334333b69a8f3c5f035d`.
These new seasonal definitions are not installed or credited by the combined
application counter. The completed native treasure owner/reader batches and their
limitations remain in the [treasure checkpoint](NOTICEBOARD_TREASURE.md); do not
replay them or the completed initial board batches.

## Next work

1. Implement bounded C seasonal decoding for native IDs, with the correct mapped
   source/adapted body and exact field mask. Preserve immutable catalogue four
   and old initial/treasure saved identities.
2. Capture complete shop/town names and both native lunar dates plus the October
   sports date in owned workspace. Retain source calendar calls and the original
   year; bypass the old insufficient combined-date buffers without widening only
   one temporary or mutating unrelated free fields.
3. Install creation and reading together. Handle allocation/read failure before
   publication without consuming the pending notice: the native scheduler
   advances year/index state before its formatter/writer calls.
4. Build the full ROM/UPS, retain every earlier translation resource, and run one
   bounded seasonal batch with full reading, failure/retry, and restoration.
5. Continue remaining general text/names, full-name callers, gameplay/save
   compatibility, review, available validation, patch-only release, title art,
   and GameCube-style keyboard work. The overall goal remains active.
