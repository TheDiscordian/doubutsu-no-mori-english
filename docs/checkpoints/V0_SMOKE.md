# Combined v0 verification

## Candidate

The current candidate is `build/classic-letters-pilot`, built from revision
`e5fbf80`, with ROM SHA-256
`31c85f23c996b70bd7a4779b43f1039716a77c84806dfa5a7dd52e3780d50860`.
The retained-classic and reserve-letter checkpoints contain its completed
integration evidence. Inventoried phrase replacement is complete; structural
zero-filled slots remain untouched. Title artwork and a GameCube-style keyboard
remain v1 work.

## Active checks

The single combined regression invocation is
`python3 -m unittest discover -s tests -v`, logged in
`build/v0-regression.log`. Retain the complete first result, classify failures,
and rerun affected tests after fixes rather than repeating the whole suite.
Existing legacy-fixture failures are not automatically game defects or passes.

`tools/v0_smoke_scenario.py` reuses the existing name/town/train/arrival scenarios
without screenshots. The combined emulator run `build/v0-gameplay-01` passes
218 recorded steps in a fresh isolated game with the candidate ROM.
`tools/validate_runtime_smoke.py` passes all ten acceptance checks: four-MiB
memory, process survival, complete long choices and selected answers, English
player/town entry, town-field insertion, and train arrival. The resident end
guard is intact, and shutdown is graceful. This run does not establish ordinary
save/restart, later tutorial jobs, apology submenu entry, or full menu/mail/board
coverage. Record actual outcomes before calling those checks passed.

## Patch-only packaging

`tools/package_v0.py` packages the exact candidate, a guarded Python patcher,
checksums, and private playtest/provenance notes. It verifies reconstruction and
the N64 boot checksum before writing a new archive. It includes neither a ROM
nor extracted disc assets, and does not create a public release. Five focused
tests pass, covering actual candidate reconstruction, all three input byte
orders, corrupt-input rejection, exclusive output creation, deterministic
archives, and the exact allowed package contents. The notes retain pending
checks; creating the archive does not mark those checks passed.

## Remaining handoff work

Complete the bounded ordinary menu/editor/mail/board and save/restart checks
where existing fixtures permit. Keep the per-batch 30-minute new-harness budget
and one justified retry for setup failures. Fix actual crashes, memory corruption,
or save damage; do not classify an unexplained failure as setup trouble. Prepare
the patch, revision/checksums, real memory requirement, and concise known-issues
and untested-areas notes for human playtesting. Broad player/hardware/seasonal
testing follows the handoff rather than blocking the build needed for it.
