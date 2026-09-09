# Combined translation progress

Run `python3 tools/translation_progress.py` from the repository for the quick
overall text-replacement approximation. It selects the newest completed ROM
build and rereads its actual contents. `--build <directory>/build.json` selects
a particular build. Hash mismatches fail instead of reporting stale results.

The single percentage is the original Japanese text volume now represented by
English, divided by the total inventoried original Japanese text volume. Weight
is non-whitespace source characters, not English length. Each original text ID
counts once, even when multiple English resources replace it. Identical text in
distinct native slots retains each slot's weight. Development labels count too.

The total combines dialogue, choices, general strings, item names, villager and
special-character names, catchphrases, letter headers/bodies/footers, embedded
name-entry prompts, and keyboard labels. Wider name resources map back to their
original source IDs. Letter credit includes installed ordinary replacements and
the catalogue parts selected by installed NPC-reply, fortune, renewal,
sale/Redd event, Mom, departed-villager, villager-event, HRA welcome/advice/score,
catalogue-order/raffle-ticket, and museum notice/fossil routes. Unavailable
Mom, birthday, and score bodies do not receive complete-letter credit in the
default catalogue-two variant. The counter reads the compiled creator's selected
catalogue and each verified route's complete IDs. Catalogue-four glyphs receive
credit only with the exact installed font and complete reader; unknown pairs
remain uncredited. The denominator and duplicate-ID rules do not change.
Catalogue presence alone does not credit unused letters or GameCube-only IDs.
Reader and NPC capture/delivery patches are checked against installed bytes;
actor images and resources are bound to the completed build report.

This deliberately remains a quick approximation, not an exhaustive new audit.
Other embedded interface strings and text-bearing artwork still need inventory
expansion. Unknown glyph/undecodable source categories are reported, not silently
declared translated. Empty replacement text receives no automatic credit.
English replacement detection is not a judgement of wording quality, complete
caller behaviour, gameplay, testing, polish, or hardware readiness. Those do not
add to or subtract from this text-replacement percentage.

Generated `build/translation-progress/latest.json` records the numerator,
denominator, measurement time, ROM hash, and inventory limitations.
`entries.jsonl` records original IDs, source hashes, and credited replacement
routes without reproducing game text. Both outputs remain ignored. The original
`text_coverage.py` is a narrower candidate-bank diagnostic, not the overall
progress answer. Always rerun this combined tool when asked for progress.
