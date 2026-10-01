# Doubutsu no Mori English

## Objective

Build a complete English translation for the Japanese Nintendo 64 release, with
halfwidth Latin text and original hardware compatibility. Keep claims tied to
recorded tests. An emulator boot does not establish hardware compatibility.
An Expansion Pak requirement is acceptable if needed for the complete translation.
Four-MiB compatibility is not a release requirement. Document and test the actual
memory requirement; permission to use eight MiB does not itself change heap bounds.

V3 is only the optional GameCube villager/item import pipeline. Finish shared
extraction/conversion, stable additive identities, bulk asset/data installation,
item/villager runtime behaviour and persistence, English text, and independent
browser/offline selections. Regular items are importable and obtainable through
the regular item pool. Read `specs/V3_OPTIONAL_IMPORTS.md` and the active V3 queue.
Rewards that fit existing systems are in scope for V3 item acquisition. A reward
or special-item label does not itself make an item V4 work. Defer acquisition
only when it requires an unavailable entirely new feature or building, rather than
extending an existing or already-built system. Items depending on those deferred features should not be
importable before they are obtainable. Their conversion/resources can be prepared
in V3; prepared or installed resources do not make them importable. Do not invent
substitute regular stock or unrelated gifts for special items.
Building new systems, including Able Sisters/custom designs, the Museum building,
island facilities, and savings accounts, is V4 work. Already-built features can
stay in V3; do not remove, disable, or isolate them merely to enforce the version
boundary. This does not require completing unfinished feature ports or establish
that their item acquisition works. Preserve existing experimental code/resources;
assess each acquisition path by
its actual dependencies instead of excluding all mail, holiday, or golden-tool
rewards. Do not demand policies for new V4 systems as V3 prerequisites.
Design-dependent sign boards remain deferred. Ordinary item behaviours, including
fish/insects/fossils, remain V3 import work. This boundary governs subordinate specifications,
checkpoint continuations, and stored goal wording.
There is one deployed patcher: the public website. Localhost is an ordinary
website preview; running it as a service gives it no special status. Use "the
deployed patcher" for the public website and "the local preview" for localhost.
Never describe these as two patchers or two deployments.
Use `v3/optional-imports` for experimental implementation, preserving the stable
V2 cartridge and deployed patcher. Imports need complete gameplay and
persistence support; an extracted name or disabled web option is not completion.
Do not repurpose existing villagers/items or assign IDs by checkbox order.
V3 development source may be pushed to GitHub on `v3/optional-imports`.
The local preview serves V3 for the user's import-selector review and playtesting.
Keep the deployed patcher on the latest verified stable V2 corrections until the
user has tested V3 and explicitly approved public publication. GitHub source
publication, developer verification, a private playtest handoff, and serving the
local preview do not authorise updating the public recipe or assets. The V3
public publication hold does not apply to V2 fixes. Preserve the stable V2 exports.

## Workflow

- Read `docs/PROGRESS.md`, `docs/V0_PLAN.md`, and the relevant specs before making
  changes. `docs/V0_PLAN.md` governs pre-v0 priorities and test scope; broader
  acceptance lists do not turn every pending test into a v0 prerequisite.
- Keep ROMs, extracted game assets, legacy distribution contents, saves, and
  generated patches in ignored directories. Commit original tools, translation
  edits, specifications, provenance records, and test fixtures made for testing.
- Use existing official translations where the original identity matches;
  otherwise use an identified human fan translation before writing new text.
  Keep per-text authorship and source references in the single
  `translations/provenance.json` catalogue, including assistant-written text
  without a human translation source. Unknown provenance is unresolved, not
  evidence of human authorship or an unavailable translation. Preserve actual
  N64 identities and record necessary platform adaptations explicitly.
- Never distribute a full ROM. Public releases contain patches and instructions.
- The existing development repository is the public source and GitHub Pages
  repository; keep its name. The exact reviewed browser recipe, manifest, and
  poster under `web/` are the only generated game-derived publication assets
  tracked for Pages. Other generated patches/assets and all ROMs/saves stay
  ignored. The Pages workflow validates while private and deploys only when
  the user makes this repository public. Never change visibility as preparation.
- Preserve third-party licensing and authorship; do not assume an unlicensed
  archive grants permission to relicense its code or translations.
- Validate the input ROM hash before modifying anything. Build into a new file.
- Run MIPS tooling in Docker. Host Python tooling uses the standard library or uv.
- Fail on unknown control codes, unrepresentable text, buffer overflow, unexpected
  patch bytes, and unsupported ROM revisions. Never truncate text silently.
- Keep save format changes out of the initial rendering work.
- Emulator tests must be silent, isolated from existing saves, and time bounded.
- `/usr/bin/ares` lacks `QPassSignals:10`, needed to pass normal libultra lazy-FPU
  exceptions in newly created native threads. Use the local N64 build at
  `build/ares-n64-debugger/rundir/bin/ares`, whose pinned source supports it.
  Pass `--ares-debug-settings developer` to the scenario runner for that build;
  its debugger settings use `Developer/DebugServer*`, not the older path.
  Its build instructions and identity are in `specs/V3_CONSOLE_DISK.md`.
  Do not repeat the unsupported-command probe, substitute CPU-register edits, or suppress real
  memory/illegal-instruction faults. Retain ordinary native fault checks.
- Document what is complete, what is experimental, and what is untested.
- Every release-candidate handoff states save compatibility with the preceding
  candidate. Explicitly warn before using a build whose saves cannot safely be
  loaded by a previous version; distinguish forward and backward compatibility
  and any required migration. Do not infer completed save/restart testing merely
  from unchanged saved formats. Preserve existing saves and candidate ROMs.
  Cross-version save compatibility is preferred, not mandatory. A necessary
  format change is acceptable with an explicit warning; unintended crashes
  remain stability defects independently of that preference.
- Do not create further release candidates. Finish remaining V1 work in the
  development build, then name the next release `V1 Final`. Preserve existing
  RC artifacts and accepted results. Package once the V1 implementation and
  bounded verification are complete; keep public publication approval separate.
- Do not expand V1 into a review of neutral tools, room surfaces, effects, or
  fish/insect artwork. Leave those assets unchanged unless actual lettering or
  a concrete translation defect is identified. Hypothetical untranslated art
  is not a reason to delay `V1 Final` or build more inspection tooling.
- Keep progress updates in chat and describe concrete completed work. Never
  open render-md windows or wait for the user to read one. Do not repeat an
  unchanged completion percentage.
- When asked for total translation progress, run `python3 tools/translation_progress.py`
  and report its single fresh combined approximation. Names and letters belong
  in the same total as dialogue. Do not reuse the bank-only diagnostic or mix
  testing/polish effort into the text-replacement figure. See
  `specs/TRANSLATION_PROGRESS.md` for the counting rules and inventory limits.
  English resources with known player-facing readers still using Japanese are
  pending application, not fully credited. When counter maintenance is in scope,
  its installed-route verification and pending family rules must reflect the
  completed readers. A stale counter is not evidence about a newer cartridge.
- Defer percentage-tool maintenance unless it directly helps find untranslated
  text. Remaining English application, artwork, and concrete playtest defects
  take priority. Do not spend a work batch updating percentage reporting alone.
- For GameCube importing progress, run `python3 tools/v3_import_progress.py` and
  report its fresh combined content-weighted percentage, not the translation
  percentage or an estimate of remaining work hours. All item categories and
  villagers belong in this figure. See `docs/IMPORT_PROGRESS.md`; do not maintain
  a separate completion checklist or substitute selectable counts for importing.
- Prioritise complete English content and playable sections. Batch verification
  around meaningful changes; record difficult edge cases for the later bug pass
  instead of repeatedly attempting them while bulk implementation waits.
- New V3 furniture uses `tools/v3_furniture_pipeline.py` and the checked current
  build lock. Extend shared format/behaviour categories rather than
  adding per-item Python definitions, family switches, installers, or native
  scenarios. Read `specs/V3_FURNITURE_PIPELINE.md`; keep unsupported dependencies
  explicit. Use the shared representative batch probe and retain passing
  unchanged evidence. The local Xvfb executable is
  `/home/discordian/Games/OpenRSC/headless/vendor/usr/bin/Xvfb`; pass it explicitly
  when it is absent from PATH.
- Keep one active category-wide implementation task in `docs/WORK_QUEUE.md`,
  with its complete player-facing path and remaining consumers. Implement shared
  changes across every matching record, including required individual behaviours.
  A completed table or hook stays complete; the category stays unfinished until
  its connected path works. Do not turn each dependency into a separate
  implementation, testing, and reporting cycle.
- Map the missing consumers once, then work through that map. Run cheap compiler,
  bounds, and source checks during implementation; batch native integration checks
  around the connected change. Reuse unchanged resources and passing evidence.
  Do not rescan unrelated categories or rebuild prepared assets without a concrete
  dependency or defect. Fix discovered game defects without postponing them to
  make the batch look complete.
- Internal build locks and commits are durability checkpoints, not new tasks or
  completion claims. If interrupted, record the exact next consumer and resume
  the same task; do not restart unchanged tests or start a fresh audit. Keep
  detailed technical evidence in its existing build reports. Update the current
  queue and progress once per connected batch or necessary handoff, rather than
  repeating each sub-step across several documents. Report newly usable paths
  and remaining work, not receipt counts as a substitute for usable content.
- Importing includes extraction, conversion, bulk installation, and working
  item behaviours, including item-specific behaviours. Do not impose a rule
  postponing item-specific work until all shared categories are finished.
  Regular items enter the regular item pool. Rewards that fit existing systems
  remain V3 acquisition work; do not blanket-defer gifts, mail, holiday rewards,
  or golden-tool rewards by name. Building an unavailable new acquisition feature
  or building belongs to V4; already-built features can stay in V3. Prepare supported artwork and shared records without
  implementing those deferred features. Items with incomplete behaviour or
  unavailable acquisition should not be selectable. Report prepared pipeline
  coverage separately from importability; preparation does not enable an item. Extend a
  shared category once for all matching records. Reuse passing tests for
  unchanged components.
- Substantial N64/GameCube behaviour differences are explicit WebUI choices,
  not silent decisions to keep one version. Follow the behaviour-choice contract
  in `specs/V3_OPTIONAL_IMPORTS.md`; share a setting across the affected mechanic
  where appropriate, and implement both behaviours rather than offering a
  cosmetic toggle or treating an unfinished port as a completed alternative.
- V3 completes the import pipeline for items and villagers. Once that pipeline
  is complete, verify and hand it over.
  Do not continue into new buildings or entirely new V4 features. Existing-system
  rewards are not automatically excluded from V3. Retain already-built features
  rather than removing them to enforce that boundary. Preserve installed item
  behaviours and existing evidence without expanding unrelated feature checks.
- Use existing focused checks once per meaningful change. Reuse passing native
  evidence for unchanged code/resources; do not add exhaustive per-record or
  all-combinations harnesses without a concrete uncovered risk. Time-bound each
  emulator run. After a setup failure, identify a concrete correction or missing
  diagnostic before retrying. If a corrected retry remains inconclusive, record
  the exact evidence and change the diagnostic approach instead of repeating
  unchanged setup. Continue autonomously to classify unresolved failures and
  verify the current deliverable; elapsed setup time and retry counts are not
  permission gates and do not require the user to authorise more testing.
  Preserve failed attempts and passing unchanged evidence. Do not disguise
  repeated work as a fresh batch, weaken safeguards, or expand the project scope.
  This current policy governs older fixture-budget and retry-limit wording in
  specifications, checkpoints, and work records.
  Confirmed crashes, save damage, and memory corruption block v0. Unexplained
  failures that could be game defects remain unresolved until classified;
  never assume a harness cause or mark an incomplete test passed.
- Do not re-test old candidate builds. Preserve recorded results and target
  verification at changed code and the current deliverable. Do not queue a
  complete historical-build replay as final-V1 work. Historical fixture
  maintenance is not a release task unless a concrete current build/game
  failure makes the affected check relevant. Human-accepted fixes and ordinary
  save/restart/reload stay closed unless a new defect is reported.
- Produce and hand over v0 before the human playthrough. Comprehensive gameplay,
  hardware, and polish acceptance cannot block the build that enables that work.
  English title artwork and the GameCube-style keyboard belong to v1.
- A human playthrough supplies broad gameplay bug reports after the main work.
  Automated checks concentrate on crashes, save corruption, broken text, and
  obvious regressions. Do not claim that planned playthrough as completed proof.
- Use public names only in committed files. Use Commonwealth punctuation.

## Project map

- `tools/`: original extraction, validation, build, and test tooling.
- `runtime/` and `overlays/`: bounded resident code and on-demand native overlays.
- `translations/`: translation edits and review state.
- `specs/`: verified formats and implementation design.
- `docs/`: current progress, source provenance, and validation requirements.
- `upstream/af/`: pinned N64 decompilation submodule.
- `local/`: ignored inputs and reference checkouts.
- `build/`: ignored generated outputs and reports.
