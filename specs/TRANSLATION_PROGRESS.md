# Combined translation progress

Run `python3 tools/translation_progress.py` from the repository for the quick
overall text-replacement approximation. It selects the newest completed ROM
build and rereads its actual contents. `--build <directory>/build.json` selects
a particular build. Hash mismatches fail instead of reporting stale results.

The single percentage is the original Japanese text volume with its English
replacement applied, divided by the total inventoried original Japanese text volume. Weight
is non-whitespace source characters, not English length. Each original text ID
counts once, even when multiple English resources replace it. Identical text in
distinct native slots retains each slot's weight. Development labels count too.

The total combines dialogue, choices, general strings, item names, villager and
special-character names, catchphrases, letter headers/bodies/footers, embedded
name-entry prompts, keyboard labels, 39 embedded inventory action-label records,
thirteen category/present/question records, and eight inventory mail/quest
description records (including the canonical Museum spelling).
The two embedded festival-stall cancellation labels also enter the shared total.
Eight embedded map records also enter the total, including landmark labels,
the post-office continuation, and the vacant-house label. Their source weights
remain in older builds. Credit requires the complete installed English map
label image, source-bound GC wording/line positions, retained resident-name
cache, drawing calls, relocation, and allocation. Splitting English into two
lines does not create extra original IDs or duplicate the bank-name resources.
They keep their original weights in older builds; English credit requires the
installed full choice routine, appended labels, allocation metadata, and resident
choice/name dependencies. Connecting stall item names does not multiply their
original bank IDs or finish unconnected item readers elsewhere.
Inventory records enter the denominator in older builds too; complete English
credit requires the installed label image, callbacks, full-name loader, font,
relocation, and shared allocation checks. Repeated references to one menu label
do not multiply its weight; original numeric-only records add no Japanese weight.
Category/present/question credit also requires the complete selected tag profile,
copy/draw bounds, source pointers, and minimum question width. Older base profiles
retain the same source denominator without gaining that credit.
Description credit requires the complete English composition, full-name storage,
drawer, relocated quest resolver, and shared allocation. Native suffix subspans
do not count again, and displaying a name in another menu adds no duplicate
name credit. The saved Museum identity remains native while its display is English.
Wider name resources map back to their original source IDs. Merely installing
the English resource is insufficient: an ID with known readers still using its
Japanese representation is not fully applied. The item-name, display-name, and
catchphrase resources have partially connected readers, so their resource-only
replacements are recorded as pending, not credited. English already replacing
the native bank entry retains its credit; short complete names are not penalised
because other names need wider storage. Finishing a family's remaining readers
must also add their installed-code verification to the counter before enabling
that route's credit. This is a conservative per-original-record approximation,
not an occurrence count or fractional credit for each connected reader.
See `EXTENDED_ITEM_LOADER.md`, `DISPLAY_NAMES.md`, and `CATCHPHRASES.md` for reader
boundaries. A saved Japanese identity used only as an internal lookup key is not
an untranslated display. Testing or layout polish alone does not withhold credit.

The persistent general-field extension receives installed-code verification
before counting a build that includes it. Its completed main-message paths do
not multiply existing item IDs or finish the remaining shared-choice readers;
resource-only item replacements retain pending status until all required
player-facing paths are connected. No new source weight is invented for this
storage and reader integration.

Letter credit includes installed ordinary replacements and
the catalogue parts selected by installed NPC-reply, fortune, renewal,
sale/Redd event, Mom, departed-villager, villager-event, HRA welcome/advice/score,
catalogue-order/raffle-ticket, museum notice/fossil, spotlight/reopening notice,
letter-quest reply, villager secret, and complete Snowman gift
routes. Unavailable Mom, birthday, and score bodies do not receive complete-letter credit in the
default catalogue-two variant. The counter reads the compiled creator's selected
catalogue and each verified route's complete IDs. Catalogue-four glyphs receive
credit only with the exact installed font and complete reader; unknown pairs
remain uncredited. The denominator and duplicate-ID rules do not change.
Catalogue presence alone does not credit unused letters or GameCube-only IDs.
Reader and NPC capture/delivery patches are checked against installed bytes;
actor images and resources are bound to the completed build report.

The home-gyroid default credits original `string:055C` once through its complete
four-line English variant only when the actual selector actor, allocation,
relocations, custom formatter, and both default/custom messages are verified in
the cartridge. Reusing a reserve adds no duplicate weight. Normal save/reload
testing remains acceptance work and does not change the text-application count.

This deliberately remains a quick approximation, not an exhaustive new audit.
Other embedded interface strings and text-bearing artwork still need inventory
expansion. Unknown glyph/undecodable source categories are reported, not silently
declared translated. Empty replacement text receives no automatic credit.
The town-name suffix is an explicit exception: its exact empty English reference
and unchanged native constructors must pass `town_suffix.verify_installation`
before original `string:01E4` receives credit for the intentional omission.
English application is not a judgement of wording quality, gameplay, testing,
polish, or hardware readiness. Those do not add to or subtract from this
text-replacement percentage. A missing connection that leaves Japanese text in
a player-facing reader is application work and does withhold full-record credit.

Generated `build/translation-progress/latest.json` records the numerator,
denominator, measurement time, ROM hash, and inventory limitations.
`entries.jsonl` records original IDs, source hashes, credited replacement routes,
and pending routes with reasons, without reproducing game text. Schema two also
records pending-only source weight and records, without adding another percentage.
Both outputs remain ignored. The original
`text_coverage.py` is a narrower candidate-bank diagnostic, not the overall
progress answer. Always rerun this combined tool when asked for progress.
