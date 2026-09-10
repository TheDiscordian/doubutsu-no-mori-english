# Completion queue

## Next work

The V1-17/V1-18 follow-up is implemented in the packaged
[V1RC3 candidate](V1RC3_PLAYTEST.md). The [polygon font correction](checkpoints/FONT_POLYGON_EDGES.md) and
[building-transition correction](checkpoints/TRANSITION_EDGES.md) have passing
focused and controlled native checks. The committed two-stage replay, two
package tests, and archived standalone patcher pass. Use this combined candidate
for the next original-hardware playtest; do not repeat unchanged native checks.
Preserve existing ROMs and saves; original-hardware appearance remains pending.

The V1RC1 hardware follow-up V1-13 through V1-16 is implemented in the packaged
[V1RC2 candidate](V1RC2_PLAYTEST.md): first-time-player wording, GC keyboard
corner/hint layout and key alignment, one supported-symbol page, shop currency
units, and idle AM/PM edge clamping. The complete three-stage rebuild, focused
checks, controlled native keyboard drawing/guards, and standalone patcher pass.
Hardware appearance remains acceptance work. Keyboard sound feedback is
accepted. Preserve V1RC1, V1RC2, and the user's saves. V2 stays deferred.

The [V1 human playtest findings](V1_PLAYTEST_BUGS.md) take priority over additional
artwork discovery and event acceptance. The first sixteen findings have scoped
corrections retained in V1RC3, alongside the two edge fixes. The
[package checkpoint](checkpoints/V1RC3_PACKAGE.md) identifies the exact local
ROM, patch, and source revision. Implementation and controlled drawing evidence
do not establish acceptance of every reported case. Next:

- Prioritise remaining Japanese wording/artwork and concrete playtest defects.
  Percentage-tool maintenance is deferred at the user's request; use existing
  inventory only when it helps find text still needing replacement. Do not spend
  implementation time updating the percentage or its candidate selector.
- Retain the [completed full regression result](checkpoints/V1RC1_REGRESSION.md):
  2,103 tests, 25 failures, and 75 errors. Fix relevant historical fixture
  selection/generation without weakening guards or overwriting artifacts;
  inspect remaining failure causes and rerun affected checks. Counter-only
  expectation maintenance stays deferred. Do not restart the entire suite or
  claim it passed. The title metadata comparison has a passing scoped correction
  with independently matching overlay/relocation binaries; retain that result.
  The [core runtime fixture follow-up](checkpoints/RUNTIME_FIXTURE_FOLLOWUP.md)
  also closes five historical errors with passing evidence for 69 selected
  checks. Preserve the verified fixture selections and unchanged guards; do not
  rerun that completed batch or mark other failures resolved by association.
- Retain passing pixel-editor, letter UI, and corrected keyboard native evidence.
  The current keyboard probe completes drawing, save/guard checks, fixture
  release, and checkpoint restoration. Do not repeat unchanged native batches.
  Preserve the older RC1 partial result separately, without relabelling it.
- Recheck ordinary letter opening/defaults, recipient selection, all reported
  screen appearances, keyboard feedback, and inventory digits on the playable
  candidate. The shared recipient fix covers all villagers, not only Limberg;
  preserve correct English names, player names, and saved identities.
- Retain the verified [hiring-notice correction](checkpoints/SHOP_HIRING_NOTICE.md)
  included in V1RC2, without repeating the unchanged room inspection.

Broader remaining work follows the combined-fix integration:

1. Perform bounded ordinary appearance acceptance of the shared festival stall
   and fortune table when a suitable isolated scene is available. Retain both
   stall placements, correct lighting/culling, original shadows/collision, and
   unchanged event behaviour. Do not turn scene setup into an exhaustive event
   harness. The [stall checkpoint](checkpoints/STALL_ARTWORK.md) records passing
   host/combination checks and the deliberate reflected-mesh adaptation. The
   [controlled native preview](checkpoints/EVENT_ARTWORK_PREVIEW.md) passes;
   do not rerun it for unchanged models or mistake it for ordinary event proof.
2. Preserve the lucky-bag Japanese decoration, matching the English GC release
   and the user's explicit choice. This applies to all three menu icons and the
   native world-bag picture. Do not reopen it as missing English or count retained
   artwork as translated; [the bindings](ARTWORK_REMAINDER.md) are documented.
3. Keep the combined private playtest package aligned with checked corrections
   and artwork batches. V1RC3 retains the shared-stall candidate, seven English
   Nookington interior signs, police-interior posters, and postal MAIL bag. Preserve
   earlier artifacts and all explicit evidence limits; use verified source/ROM/
   UPS/report hashes and execute the standalone patcher before handoff.
4. Address concrete human playtest bugs immediately, prioritising crashes,
   save damage, memory corruption, and blocked progression. The Nook furniture
   whole-conversation loop and letter-advice cleanup are already fixed and
   natively tested; do not restart those investigations without new evidence.
5. Translate additional genuinely unreviewed text-bearing artwork as identified.
   Preserve native cultural structures and GC source intent. The scoped neutral
   prop inventory is not a claim that every image in the game is reviewed.
   Obtain reliable tiny-label transcriptions before assigning character weight.
   The two original interior information notices share this transcription limit;
   their complete English GC textures are already installed. Do not reopen the
   completed seven-sign batch or rerun its unchanged rendering checks.
   The three civic-interior images are also installed and verified; do not repeat
   that batch. The regional house-panel lead is a GC-only island cottage, and
   the bound native gloom effect contains no Japanese. Three unmatched shop
   drapes are also neutral; retain them without repeating the inspection.
   Use `tools/artwork_matches.py` and the [scoped inventory](ARTWORK_REMAINDER.md)
   to select additional remaining screen/item images. The
   [prop/shadow/effect review](checkpoints/PROP_EFFECT_ARTWORK_REVIEW.md) closes
   34 further native textures and confirms the English GC umbrella motif is
   retained. Do not repeat those images. Its four player/effect candidates need
   dynamic palette binding before visible artwork can be claimed reviewed.
   The
   [room/item review](checkpoints/ROOM_ITEM_ARTWORK_REVIEW.md) closes the selected
   Katrina-interior, clock/furniture, and mechanical-detail textures; retain them
   without repeating that inspection. The identified hiring notice is corrected
   to match English GC's omission. Check current installed resources first;
   unmatched originals include images already translated by earlier batches.

## Human playthrough and polish

The build exists so the user can test it. Broad acceptance does not block the
build that enables testing. Keep these outstanding checks explicit:

- Ordinary tutorial progression, including both corrected Nook advice paths.
- All changed menus and editor callers, including mail, board, catchphrases,
  apology, and song input; gyroid navigation and transactions.
- Normal save/restart, existing-save and return-to-title paths, longer displayed
  names, RTC, travel, and Controller Pak workflows.
- Dates, seasons, events, and both placements of changed seasonal props.
- Real console, flash cartridge, Expansion Pak, and Controller Pak behaviour.
- English wording and line layout, preserving GC line/page/timing intent.

Use the existing [bounded testing policy](V0_PLAN.md). Reuse passing evidence
for unchanged implementations. A setup failure gets one justified retry, with
at most thirty minutes of new harness work per implementation batch; unresolved
checks stay unresolved. Actual game defects do not get a retry cap or waiver.
The embedded-warning native setup batch has reached its retry limit and must
not be replayed unchanged.

## Public release

- Keep source-inventory limitations explicit. Percentage-tool maintenance is
  not a release-preparation priority unless it helps locate untranslated text.
- Complete provenance/redistribution review; do not relicense legacy work or
  claim the tooling licence covers Nintendo assets.
- Prepare patch-only reproducible artifacts, verified application, hashes,
  source revisions, compatibility notes, and explicit known issues.
- Preserve the verified [portable compiler setup](checkpoints/PORTABLE_TOOLCHAIN.md).
  The complete public-image rebuild passes. The
  [61-stage clean base recipe](checkpoints/V0_REBUILD.md) and
  [28-stage post-v0 recipe](checkpoints/V1_REBUILD.md) eliminate retained generated
  resource, compiled-overlay, and translation-ROM dependencies. Do not repeat
  those complete builds for unchanged code or documentation-only edits.
- Obtain release approval and record human/hardware acceptance. Private playtest
  packaging does not publish a release or certify the entire game.

## V2, only after V1 is complete

The [N64-inspired keyboard request](../specs/KEYBOARD_V2.md) is deferred:
retain a GC-like layout, use a greyer N64-controller-inspired background and
matching N64 button images, and add the stick image on the left. Do not begin
this redesign during V1 fixes, review, or acceptance. Keep V1-14 focused on
the current corner orientation/placement, text bounds, glyph positioning,
and single symbol page.

Current artifacts are in [progress](PROGRESS.md). Exact prior work remains in
[checkpoints](checkpoints/), [the implementation record](PROGRESS_RECORD.md),
and [the queue record](WORK_QUEUE_RECORD.md). Those records retain broad evidence
and historical task IDs without directing completed work to be repeated.
