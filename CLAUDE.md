# Doubutsu no Mori English

## Objective

Build a complete English translation for the Japanese Nintendo 64 release, with
halfwidth Latin text and original hardware compatibility. Keep claims tied to
recorded tests. An emulator boot does not establish hardware compatibility.
An Expansion Pak requirement is acceptable if needed for the complete translation.
Four-MiB compatibility is not a release requirement. Document and test the actual
memory requirement; permission to use eight MiB does not itself change heap bounds.

V3 adds optional GameCube villagers and items to the translated game. Read
`specs/V3_OPTIONAL_IMPORTS.md` and the active V3 queue before import work.
Use `v3/optional-imports` for experimental implementation, preserving the stable
V2 cartridge and public/local patchers. Imports need complete gameplay and
persistence support; an extracted name or disabled web option is not completion.
Do not repurpose existing villagers/items or assign IDs by checkbox order.
V3 development source may be pushed to GitHub on `v3/optional-imports`.
Do not switch either the local or public web patcher to V3 until the user has
tested the build and explicitly approved the switch. GitHub source publication
does not authorise updating either patcher's recipe, assets, or service.
Developer verification and a private playtest handoff do not satisfy that approval.

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
- Keep progress updates in chat and describe concrete completed work. Do not
  open repeated status renders or repeat an unchanged completion percentage.
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
- Prioritise complete English content and playable sections. Batch verification
  around meaningful changes; record difficult edge cases for the later bug pass
  instead of repeatedly attempting them while bulk implementation waits.
- New V3 furniture uses `tools/v3_furniture_pipeline.py` and the checked current
  build lock. Extend shared format/behaviour/acquisition categories rather than
  adding per-item Python definitions, family switches, installers, or native
  scenarios. Read `specs/V3_FURNITURE_PIPELINE.md`; keep unsupported dependencies
  explicit. Use the shared representative batch probe and retain passing
  unchanged evidence. The local Xvfb executable is
  `/home/discordian/Games/OpenRSC/headless/vendor/usr/bin/Xvfb`; pass it explicitly
  when it is absent from PATH.
- Prioritise completing general import pipelines and bulk category coverage
  before unique-item behaviour or visual detail. Prepare supported artwork and
  shared records even when a separate behaviour is unfinished; retain explicit
  readiness and keep incomplete gameplay out of selectable imports. Extend a
  shared category once for all matching records. Reuse passing tests for
  unchanged components and defer unique-item verification to its implementation.
- After primary importing is complete, finish gold-tree leaf/cut effects and
  the full golden-shovel acquisition route. These remain required V3 work;
  deferring them does not remove them from completion criteria.
- Use existing focused checks once per meaningful change. Reuse passing native
  evidence for unchanged code/resources; do not add exhaustive per-record or
  all-combinations harnesses without a concrete uncovered risk. For a testing-
  setup failure, allow one initial attempt and one retry after a concrete setup
  correction. New harness construction/debugging has a 30-minute budget per
  implementation batch; record unresolved results and continue unrelated work
  at that limit. These limits do not apply to fixing actual game defects.
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
