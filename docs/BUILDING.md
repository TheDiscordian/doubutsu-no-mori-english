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
pilot. It writes the ROM, UPS patch, checksummed build manifest, and diagnostic
atlas files under `build/pilot/`. Candidate and rejection reports live under
`build/candidates/`. Nothing in those directories is committed.

`make opening` builds only the four original dialogue drafts plus the renderer
and English-first keyboard. `make halfwidth` builds only the renderer experiment.

To rebuild a particular candidate set without regenerating references:

```sh
python3 tools/build.py \
  --rom 'local/rom/Doubutsu no Mori (Japan).z64' \
  --translations build/candidates/translations.json \
  --english-keyboard --output build/pilot
```

The supported input ROM hash, relocation addresses, and command policies are in
[the framework specification](../specs/TEXT_FRAMEWORK.md). Wrong inputs, stale
edits, unknown commands, and unsafe expansion fail the build.

## Silent emulator tests

`tools/emulator_smoke.py` requires ares, Xvfb, FFmpeg, X11, and XTest. Pass an
explicit `--xvfb` path if the existing binary is outside PATH. Every test requires
a fresh `--output` directory, copies the ROM, disables audio, isolates saves,
and enforces a bounded process lifetime. It never reads or replaces a user save.

Use `--scenario tests/english-keyboard-scenario.json --seconds 410` for the
English-entry sequence. Generated `results.json` records ROM hash, message
snapshots, memory assertions, and captures. The controller test mapping is in
[validation](VALIDATION.md). Emulator process survival alone is not a pass.

`make test` runs all tests. The four retail-input integration tests are skipped
when the source ROM is absent; synthetic format and safety tests still run.

`python3 tools/check_keyboard_assembly.py` separately verifies the embedded
name-cursor patch against its assembly source using the pinned Docker toolchain.
