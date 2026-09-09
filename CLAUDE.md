# Doubutsu no Mori English

## Objective

Build a complete English translation for the Japanese Nintendo 64 release, with
halfwidth Latin text and original hardware compatibility. Keep claims tied to
recorded tests. An emulator boot does not establish hardware compatibility.
An Expansion Pak requirement is acceptable if needed for the complete translation.
Four-MiB compatibility is not a release requirement. Document and test the actual
memory requirement; permission to use eight MiB does not itself change heap bounds.

## Workflow

- Read `docs/PROGRESS.md`, `docs/V0_PLAN.md`, and the relevant specs before making
  changes. `docs/V0_PLAN.md` governs pre-v0 priorities and test scope; broader
  acceptance lists do not turn every pending test into a v0 prerequisite.
- Keep ROMs, extracted game assets, legacy distribution contents, saves, and
  generated patches in ignored directories. Commit original tools, translation
  edits, specifications, provenance records, and test fixtures made for testing.
- Never distribute a full ROM. Public releases contain patches and instructions.
- Preserve third-party licensing and authorship; do not assume an unlicensed
  archive grants permission to relicense its code or translations.
- Validate the input ROM hash before modifying anything. Build into a new file.
- Run MIPS tooling in Docker. Host Python tooling uses the standard library or uv.
- Fail on unknown control codes, unrepresentable text, buffer overflow, unexpected
  patch bytes, and unsupported ROM revisions. Never truncate text silently.
- Keep save format changes out of the initial rendering work.
- Emulator tests must be silent, isolated from existing saves, and time bounded.
- Document what is complete, what is experimental, and what is untested.
- Keep progress updates in chat and describe concrete completed work. Do not
  open repeated status renders or repeat an unchanged completion percentage.
- When asked for total translation progress, run `python3 tools/translation_progress.py`
  and report its single fresh combined approximation. Names and letters belong
  in the same total as dialogue. Do not reuse the bank-only diagnostic or mix
  testing/polish effort into the text-replacement figure. See
  `specs/TRANSLATION_PROGRESS.md` for the counting rules and inventory limits.
- Prioritise complete English content and playable sections. Batch verification
  around meaningful changes; record difficult edge cases for the later bug pass
  instead of repeatedly attempting them while bulk implementation waits.
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
