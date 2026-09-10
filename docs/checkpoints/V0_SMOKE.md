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
The invocation completes with eleven failures and seventy-five errors; the
[classification and focused corrections](V0_REGRESSION.md) retain its full result.
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

The generated private archive is `build/releases/v0-playtest-candidate.zip`,
SHA-256 `9c5235c4346ba8c3df1013a110946c515b09856204027b53aaabf4ab9303b016`.
Its packaging revision is `2db8e7f`. The archive is extracted into
`build/releases/v0-application-check`, and its included command-line patcher
successfully creates `animal-forest-english.z64` from the verified retail input.
The resulting SHA-256 equals the candidate above. ROMs remain outside the ZIP.

## Ordinary progression boundary

`build/v0-housing-01` reuses the prior housing inputs without reaching housing:
the player is still on the arrival platform. It records 63 steps, controller
movement, intact guards, and graceful shutdown; inventory remains closed. This
is not a housing or menu pass. The read-only follow-up
`build/v0-town-observation-01` locates the live station character (`D00E`).
`build/v0-arrival-guide-01` approaches that character using ordinary controller
input and observed positions, opens English message `0831`, expands the complete
town field, closes the dialogue, and retains the memory guard. No actor position,
schedule, or progression fields are written by the debugger.

The bounded southward route in `build/v0-platform-exit-01` does not leave the
platform: the player reaches Z 862 while the station character remains active.
There is no demonstrated crash or memory failure, but these timed routes do not
prove outdoor/tutorial progression or ordinary saving. Do not loop the same
route or count the unused submenu as opened. A verified exit route or human
playtest is needed for further ordinary gameplay evidence.

## Playtest handoff and remaining checks

The user has the candidate ROM path for experimental original-hardware
playtesting. The handoff states that hardware, normal saving/reloading, and
regression clearance are unverified and asks for a separate backed-up test save.
Keep this exact ROM stable while collecting reports; v1 title builds are separate.

Complete the bounded ordinary menu/editor/mail/board and save/restart checks
where existing fixtures permit. Keep the per-batch 30-minute new-harness budget
and one justified retry for setup failures. Fix actual crashes, memory corruption,
or save damage; do not classify an unexplained failure as setup trouble. Prepare
the patch, revision/checksums, real memory requirement, and concise known-issues
and untested-areas notes for human playtesting. Broad player/hardware/seasonal
testing follows the handoff rather than blocking the build needed for it.
