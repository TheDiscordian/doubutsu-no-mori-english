# Residual general-string translation

## Complete groups

`tools/residual_general.py` supplies 140 complete entries in the existing general
bank: the test label, AM/PM labels, six compact date units, seven compact weekdays,
25 unused catchphrases, 68 fortune phrases/outcomes, three trash labels, twelve
birth-year animals, twelve zodiac signs, and four shop-tier names. It changes 127
stored rows; the other thirteen already agree with the complete selected wording.

The supplied GameCube disc supplies 104 complete values with exact bank/decoder
hashes. Its fortune order is checked against the installed 1,088-byte phrase
resource, zodiac/animal names against the complete resident arrays, and shop
names against the source-bound seasonal names. No GameCube-only entries are
inserted and no native index changes. The test label is complete, not clipped
to its Japanese byte count.

`translations/n64-residual-general.json` supplies 36 explicit original values.
Twenty-three unused catchphrases have only `TRANSLATE` or empty donor records;
their native meaning or sound is translated directly. The two usable donor
catchphrases retain `pweeen` and `silly`. None of these 25 IDs is selected by the
216 native default rows, so no saved catchphrase, borrowed key, or live default
changes.

## Compact compatibility dates

The old suffix helpers have small fixed destinations. Their complete English
compatibility units are `yr/mo/d/h/m/s`; maximum number-plus-suffix sizes remain
within six/four/four/six/four/five bytes respectively. Weekdays use the conventional
three-letter forms within the native five-byte destination and four-byte length
scan. AM/PM bank labels retain the donor's full `a.m./p.m.`; the installed leaflet
hour code supplies its own complete time and does not consume the old suffix.

These compatibility rows do not replace active month names, ordinal dates,
weekday names, or time formatting. The installed resident/letter/notice owners
retain full GameCube English wording, spaces, manual breaks, and timing. No
formatter instruction or live date route changes.

## Wider values and existing consumers

The unchanged bounded loader accepts at most 64 bytes and stages at most 72
aligned bytes in its 80-byte temporary. All new stored values fit this contract.
Their Japanese byte counts do not grant general permission to expand caller
buffers.

The actual installed fortune actor selects its full sixteen-byte owned phrases;
its old ten-byte calls are not the active formatter. The installed birthday entry
jumps to the complete resident name/date owner. The complete seasonal publication
bridge reclaims the old narrow date/shop helper region and removes its old
external calls. All these bytes and resource bindings are checked before applying
the corresponding general-bank copies. Other unselected test/trash records do
not redirect any caller. Existing live readers, fonts, saved fields, message
selection, RNG, and all source resources remain unchanged.

## Intentional English omissions

The thirty quantity rows `0593..05A1` and `05B1..05BF` are correctly empty in
English. The complete 120-entry counter group already contains these omissions.
Before crediting them, verification checks the exact Japanese sources, complete
English group hash, actual empty values, and unchanged count-selection code,
destination capacity, category graph, and family table in all five installed
shops. A deleted sentence, whitespace replacement, wrong ID, different Japanese
source, or another route cannot obtain this permission.

Combined accounting labels these exact replacements as intentional omissions.
The general-bank update newly replaces 724 source characters; correcting credit
for the already-applied thirty omissions accounts for another sixty. Neither
change adds a source ID or changes the denominator.

## Installation and bounded checks

The data-only build follows `build/unused-names-pilot`. Only general-string data,
offsets, and repacking metadata differ. Exact cartridge reconstruction retains
all preceding resources and reports, including the complete accented names and
mail consumers. Verification unwinds these two-file data updates to check the
unchanged strict predecessor profiles; it never relaxes their code guards.

Focused checks cover all 140 values, compact capacities, exact references,
unaltered bank rows, installed wider consumers, deliberate omission guards, all
cartridge resources/indices, patch reconstruction, and combined accounting.
No new native harness is required for unchanged code. Ordinary gameplay and
normal save/restart remain in the assembled v0 smoke.
