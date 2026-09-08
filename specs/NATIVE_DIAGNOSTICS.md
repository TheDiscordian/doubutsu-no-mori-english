# Complete native diagnostic text

## Scope and meaning

`translations/n64-diagnostic-labels.json` contains all 99 native records in
three exact diagnostic families: 28 rumour-pattern labels, 68 script-bug labels,
and three gyroid debug notices. These are not ordinary conversations. None is
automatically declared unreachable or available as a continuation slot.

The batch fills 73 missing entries and corrects 26 partial reference imports
in `2720..2739`. Those English imports said only Cranky Guy extra, omitting
the actual Script bug description and diagnostic number. All 68 script-bug
labels retain the number printed by the native source, not a number inferred
from the record ID. For example, `2956` prints `10581`, despite its ID being
decimal `10582`; the translation does not silently renumber it.

Rumour-pattern labels retain their original 1/2 variants and final `00`.
`092F/0930/0931` retain notices identifying `2351/2352/2353`, a page wait/clear,
the request to report the message if it appears while debugging, and the native
By Eguchi credit. Their legacy and GameCube same-ID records instead contain
save/menu actions. Those actions are not part of the original notices and must
not be imported. Every diagnostic retains its native commands and final `00`.

## Independent complete-text guard

`tools/native_diagnostics.py` recognises only complete native diagnostic
wordings. Whitespace can vary for recognition; added prose, another personality,
missing numbers, unexpected pattern numbers, raw data, and unmapped tokens do
not become recognised labels. Printed ASCII digits, including leading zeros,
are retained verbatim by the definition.

The shared `validate_entry` path independently checks recognised main-bank
diagnostics in both generation and ROM building. Their native commands must
match the definition, and the replacement must match the complete canonical
English payload. Partial labels, changed numbers, altered controls, and unrelated
menus fail even under the looser presentation/reference policies. A declaration
of sequence policy alone cannot bypass validation: the separate complete,
hash-bound sequence permission is still required. No sequence allocation is
introduced here. Ordinary native source hashes remain mandatory.

The diagnostic guard is deliberately separate from `placeholder_text.py` and
the established coverage-classification catalog. This does not move source
characters out of the existing volume denominator or claim that English-looking
text has completed semantic/gameplay review. The explicit `diagnostic_kind` and
`printed_number` metadata keep these 99 records separate from original dialogue
and the generated development-label drafts. The 26 corrections
gain no additional source-volume credit over their earlier English-looking text.

## Verification boundary

Portable tests cover exact recognition, complete payloads, printed numbers,
leading zeros, false positives, unsupported native structures, raw/glyph data,
policy bypass rejection, and unchanged coverage categories. Retail tests scan
the entire main bank to prove all 99 recognised records are covered, verify every
source and command, and check the gyroid credit/pages and absence of save actions.
All diagnostic expansion bounds fit at 35–113 bytes without layout warnings.
Both build modes include the complete labels.

The isolated native batch loads every complete new/corrected record and checks
headers, adjacent/module guards, and restored state. The combined batch passes
all twelve focused tests, all 632 regression tests, and 116 cartridge loads
with 350 assertions across 589 recorded steps. It does not reproduce the
script bugs that these diagnostics describe, establish actual callers, execute
save menus, or prove hardware compatibility. Exact run results remain in
`docs/WORK_LOG.md`; runtime/glitch investigation and full review remain required.
