# Text coverage classification

## Scope and meaning

`tools/text_coverage.py` classifies every record in the 29 native banks against
an explicit candidate file. Native ROM verification, candidate source hashes,
unique IDs, known banks/indices, and candidate encoding are mandatory. This is
an inventory, not a replacement for the ROM builder's command/capacity checks.
The report identifies its exact input hashes and writes no game text into the
repository. Generated reports stay under ignored `build/` paths.

Separate sixteen-byte item resources, embedded interface strings, and images
are outside this report's scope. Their own inventories remain required.

## Categories

Record classification reads native text tokens, not a regular expression that
erases unknown glyphs or commands. Raw/truncated tokens require decoding review.
Two-byte glyphs remain visible and require mapping review. A record with only
whitespace and recognised commands has `no_visible_static_text`; it may still
display inserted names or affect gameplay. Dynamic insertions are recorded
separately. Never treat these records as unreachable, translated, or safe to
remove merely because they contain no static words.

The exact native placeholder label `ダミー`, optionally followed by a number,
is classified as `development_placeholder_text`. Any surrounding Japanese words
prevent that classification. This describes the text only: it does not establish
that the record is absent from player-facing code paths. Placeholders still need
an explicit translation or documented reachability decision.

Other records distinguish Japanese, Latin, and number/symbol-only static text.
Japanese script detection requires kana letters, not punctuation alone. The
English reference uses the shared `ー` glyph as a dash; that does not make the
surrounding words Japanese. Every non-ASCII static code point remains listed
separately for glyph/punctuation review, including that dash.
Candidate presence and candidate text categories are separate from source
categories. An identity match, successful encoding, or English-looking candidate
does not constitute translation review. All records retain unestablished
reachability; main messages retain their control-flow audit requirement.
The report makes no completion claim and does not infer a reviewed count from
candidate statuses, provenance, or absence of Japanese characters.

## Reproduction

Run `python3 tools/text_coverage.py --rom <verified-native-ROM>
--translations <generated-candidates.json> --output build/coverage`.
Each bank gets a per-record JSONL file; `summary.json` contains category counts
for all sources, present candidates, and records without candidates. Portable
tests cover unknown/truncated text, dynamic-only records, exact placeholders,
stale/duplicate edits, and both original and reference provenance forms.
