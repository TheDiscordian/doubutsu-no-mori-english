# Private selection interface checkpoint

## Implementation

The unserved export at `build/v3-browser-interface-02/site/` contains an actual
selection page, not just the worker probe. The checked source is under
`experimental/imports/`; no deployed `web/` file or running service changes.

The page offers name/donor-ID search, category filtering, individual checkboxes,
select/clear visible, and select/clear all installed choices. All 101 choices
start off. Villager dependencies remain visibly checked and identify the parent
villager; the build summary lists automatically included shirts/furnishings.
Removing a parent recomputes closure from explicit selections.

The exporter runs the shared checked furniture scan and generates 164 unavailable
entries with actual reasons, excluding all installed choices. Existing custom
imports are not downgraded by a narrower static-converter scan. This is explicitly
the 3xxx furniture queue, not a complete donor inventory or proof that every
candidate is absent from N64. These records have no selection controls.

Nonempty builds require acknowledgement of a separate test save and retained
profile. Warnings explain that removing imports is not migration and imported
saves must not load in V2 or older builds missing their identities. ROM and JSON
profile downloads share the output hash prefix. No input file or save is edited.

The UI validates both file fields on every change, terminates active workers,
revokes old download URLs, resets save acknowledgement when inputs/selections
change, and ignores stale worker messages. Filtering alone does not change the
selection. A new shared bounded bundle reader serves the UI and worker; the
worker requires the exact displayed plan hash before reading the user's games.
The page uses relative static URLs, restrictive CSP, no external resources or
embeds, no storage, no uploads, and no audio.

## Verification and stopping points

Nine existing synthetic composition tests pass. Four current-build Python tests
pass, including eleven browser/offline equivalent profiles and the new complete,
disjoint, nonselectable source-derived review catalogue. Source/report pins,
checked output bounds, and the actual current ABI-93 cartridge remain unchanged.

The first real UI check reaches search/category/all/clear, review reasons,
keyboard selection, dependency inclusion/removal, file selection, and save
acknowledgement. Its progress predicate is a string expression that Playwright
tries to evaluate under the page's restrictive CSP. The test fails because
`unsafe-eval` is forbidden. The correction uses function predicates; neither the
page CSP nor the server CSP is weakened.

The single justified retry at `build/v3-browser-interface-check-02/` passes that
prefix, active-build cancellation, and rejection of a manually delivered late
worker result. The subsequent real selected-import build downloads both files:

- `villager-and-seasonal-subset.z64`: SHA-256
  `00dfbda48b1fa115c13bb0c1a027c1379365f65a0f0b0a1181657d15739bbad5`.
- `villager-and-seasonal-subset.json`: SHA-256
  `35c94b2976f5a1f4f225f6bb0c42f50ed886cc4bbfd4a0035c619e844242a163`.
- Requested: Punchy `00EB` and snow bunny `31D4`.
- Required: cherry shirt `24BF` and speed bag `3350`.

The downloaded ROM matches the independent offline composer and the downloaded
profile's output hash. The next assertion reads `inner_text()` from the checksum
inside a closed `<details>` panel and obtains an empty string. A separate minimal
DOM-only diagnostic reproduces `inner_text() == ''` while `text_content()` returns
the exact stored content. The assertion is corrected to `text_content()` for the
next meaningful integration batch. No third full UI attempt is made.

These are two classified harness failures, not observed bad ROM output. They
still prevent a complete UI test claim. Checks after that point remain
unexecuted: selection/file-change URL revocation, no-import UI download,
selection-change cancellation, invalid-input persistence, stale-plan rejection,
and 320/375/768/1440-width overflow checks. Those implementations remain present;
source inspection is not substituted for their pending execution. No broad
visual approval, mobile acceptance, or game/hardware testing is claimed.

Both temporary test servers shut down in `finally`; neither V2 service changes.
The failed runs retain their directories and downloaded artifacts, and have no
completed `results.json`. The earlier worker-only results remain attached to
their own export, not relabelled as this UI's complete acceptance.

## Artifact identities and remaining work

- Complete source ROM:
  `fe9b175801c5b1d7eb00b7ddf23d01d4fd164643cd01d9f2f6270d7e89f8598e`.
- Generated composition plan:
  `f8aeeaed3a02d1697202a3ec96929f57f4574b1b2fd7aa623fbc95f074a5af1f`.
- Generated review catalogue:
  `9520552617f5705c18011bbcaa5c6b6adf7e5f5f3ab3e00a3e9e3c115cc89f87`.
- Interface bundle manifest:
  `f922ff518702679ab6515b224ec66928b8d6202a4336784b830a7df8b3c9eaf3`.
- V3 recipe:
  `c38022a588edfef59564f418d4ae41ba3e15743144838b4a8b7c970607284aaa`.
- Interface module:
  `ddd63b55d35861f0d5cb19efbb6d1345c622b1be518d6998114eb456d78202a3`.

Continue shared item/category and native runtime implementation without another
browser replay in this batch. Include the remaining UI checks with the next
meaningful interface integration change. Browser-native artwork conversion,
fuller donor classification, ordinary imported gameplay/persistence, and hardware
playtesting remain part of the V3 goal. Installed development choices are not
declared fully accepted imports. The export is private and unserved; the user
must test V3 and explicitly approve before either patcher switches.
