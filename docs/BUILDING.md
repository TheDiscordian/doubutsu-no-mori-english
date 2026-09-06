# Building and reproducing tests

Run commands from the repository root. Python 3 uses only its standard library.
Input preparation additionally uses `7z`; source bootstrap uses Git. Inventory
the local machine before installing tools. Disassembly uses the existing pinned
Docker toolchain listed in [sources](SOURCES.md); ordinary builds do not need it.

## Inputs

`tools/prepare_inputs.py` accepts `--n64-archive`, `--legacy-zip`, and
`--gamecube-archive`. It extracts only the expected members, verifies the retail
ROM and legacy patch, and refuses to replace differing existing inputs.

Expected local files:

- `local/rom/Doubutsu no Mori (Japan).z64`
- `local/legacy/AFProjectDistro/NAFE-WIP-2_12_2010.ups`
- `local/gamecube/Animal Crossing (USA, Canada).ciso`

`python3 tools/check_references.py --bootstrap` initialises the pinned N64
submodule and fetches the pinned GameCube reference checkout if missing.
`make references` verifies both pins and tracked source cleanliness.

## Outputs

`make pilot` runs the tests, validates inputs, extracts inventories and GameCube
reference text, generates candidate edits, and builds the English-first keyboard
and sixteen-byte choice runtime pilot. It writes the ROM, UPS patch, checksummed build manifest, and diagnostic
atlas files under `build/pilot/`. Candidate and rejection reports live under
`build/candidates/`. Nothing in those directories is committed.

`make opening` builds only the four original dialogue drafts plus the renderer
and English-first keyboard. `make halfwidth` builds only the renderer experiment.

To rebuild a particular candidate set without regenerating references:

```sh
python3 tools/build.py \
  --rom 'local/rom/Doubutsu no Mori (Japan).z64' \
  --translations build/candidates/translations.json \
  --english-keyboard --english-runtime --output build/pilot
```

The supported input ROM hash, relocation addresses, and command policies are in
[the framework specification](../specs/TEXT_FRAMEWORK.md). Wrong inputs, stale
edits, unknown commands, and unsafe expansion fail the build.

## Silent emulator tests

`tools/emulator_smoke.py` requires ares, Xvfb, FFmpeg, X11, and XTest. Pass an
explicit `--xvfb` path if the existing binary is outside PATH. Every test requires
a fresh `--output` directory, copies the ROM, disables audio, isolates saves,
and enforces a bounded process lifetime. It never replaces a user save. An
explicit `--seed-save <test-directory>` copies cartridge saves into a fresh run;
the source directory stays unchanged. `--seed-state <test-directory>` resumes
an emulator checkpoint only when its recorded ROM matches the tested ROM.
Checkpoints are not FlashRAM save/reload validation.

Use `--scenario tests/english-keyboard-scenario.json --seconds 410` for the
English-entry sequence. Generated `results.json` records ROM hash, message
snapshots, memory assertions, and captures. The controller test mapping is in
[validation](VALIDATION.md). Emulator process survival alone is not a pass.

The long-choice and town-arrival sequence uses
`--scenario tests/runtime-choice-scenario.json --seconds 500`. Afterwards,
`python3 tools/validate_runtime_smoke.py <test-directory>` verifies the recorded
long rows, selected answer, name limits, town substitution, and arrival message.
The final emulator checkpoint supports continued exploration with the same ROM.

Use `tests/emulator-state-roundtrip-scenario.json` to test the checkpoint
mechanism itself. It deliberately writes a marker to unused-at-boot choice RAM,
saves state, changes the marker, reloads, and verifies restoration. These test
markers are never translation edits or release content. Successful runs close
ares normally and record the hashes of the flushed cartridge files.

`make test` runs all tests. Retail-input integration tests are skipped
when the source ROM is absent; synthetic format and safety tests still run.

`python3 tools/check_keyboard_assembly.py` separately verifies the embedded
name-cursor patch against its assembly source using the pinned Docker toolchain.
`python3 tools/check_runtime_assembly.py` verifies the choice-width routine.
`python3 tools/audit_choice_callers.py --rom '<retail-ROM-path>'` repeats the
complete DMA caller and reclaimed-code reference scan.
