# Completion queue

## Next work

The V1RC1 hardware follow-up V1-13 through V1-16 in the
[bug list](V1_PLAYTEST_BUGS.md) is the immediate implementation priority:
first-time-player wording, GC keyboard panel/corner and hint layout, a single
supported-symbol page, shop currency units, and idle AM/PM stray pixels.
Keyboard sound feedback is accepted. Pause unrelated artwork discovery and
percentage work; preserve V1RC1 and the user's saves.

The [V1 human playtest findings](V1_PLAYTEST_BUGS.md) take priority over additional
artwork discovery and event acceptance. All twelve findings have scoped
corrections in the packaged [V1RC1 candidate](V1RC1_PLAYTEST.md), reproduced by
the complete seven-stage `v1-fixes-rebuild-01`. The archived standalone patcher
passes; [the checkpoint](checkpoints/V1RC1_PACKAGE.md) identifies the local ROM
and patch. This is implementation progress, not acceptance of every reported
case. Next:

- Prioritise remaining Japanese wording/artwork and concrete playtest defects.
  Percentage-tool maintenance is deferred at the user's request; use existing
  inventory only when it helps find text still needing replacement. Do not spend
  implementation time updating the percentage or its candidate selector.
- Finish the running regression pass recorded in
  `build/v1rc1-regression.log`. Two early academy test setup errors reject stale
  historical `build/runtime-module` fixtures before exercising V1RC1. Correct
  fixture selection/generation without weakening source-inventory guards or
  overwriting retained artifacts; classify other failures and rerun affected
  checks. Do not restart the entire running suite or claim it passed.
- Retain passing pixel-editor and letter UI native evidence. The background
  probe has reached its setup retry limit: native drawing returned and geometry
  passed, but later guard checks remain unrun after a classified comparator
  error. Record this limitation; do not repeat the unchanged fixture batch.
- Recheck ordinary letter opening/defaults, recipient selection, all reported
  screen appearances, keyboard feedback, and inventory digits on the playable
  candidate. The shared recipient fix covers all villagers, not only Limberg;
  preserve correct English names, player names, and saved identities.
- Retain the verified [hiring-notice correction](checkpoints/SHOP_HIRING_NOTICE.md)
  for the next combined candidate. It follows V1RC1 in
  `build/v1-shop-notice-fix-03` without replacing the user's V1RC1 test artifact.
  Continue remaining artwork and concrete reported defects before packaging
  another candidate; do not interrupt the current hardware test for one placard.

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
   and artwork batches. V1RC1 retains the shared-stall candidate, seven English
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

Current artifacts are in [progress](PROGRESS.md). Exact prior work remains in
[checkpoints](checkpoints/), [the implementation record](PROGRESS_RECORD.md),
and [the queue record](WORK_QUEUE_RECORD.md). Those records retain broad evidence
and historical task IDs without directing completed work to be repeated.
