# Doubutsu no Mori English

## Objective

Build a complete English translation for the Japanese Nintendo 64 release, with
halfwidth Latin text and original hardware compatibility. Keep claims tied to
recorded tests. An emulator boot does not establish hardware compatibility.

## Workflow

- Read `docs/PROGRESS.md` and the relevant specs before making changes.
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
