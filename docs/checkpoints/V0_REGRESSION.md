# V0 regression classification

## Full invocation

The one full invocation of `python3 -m unittest discover -s tests -v` completes
1,874 tests in 3,757.525 seconds with eleven failures and seventy-five errors.
The complete original output remains in `build/v0-regression.log`. This is not
a passing suite. The invocation includes historical milestone fixtures as well
as current production checks; it is not 1,874 gameplay scenarios on v0.

The stable v0 ROM remains `build/classic-letters-pilot/animal-forest-halfwidth.z64`,
SHA-256 `31c85f23c996b70bd7a4779b43f1039716a77c84806dfa5a7dd52e3780d50860`.
It is handed to the user as an experimental private hardware-playtest candidate,
with separate-save instructions and the unverified save/restart, hardware, and
regression limits. Neither this handoff nor the errors below establish a hardware
pass. Do not overwrite that ROM while the user is testing it.

## Error classification

Every reported error is a Python validation rejection, not a recorded emulator
crash or sanitizer report. Source/profile rejection still means the affected
test did not reach its intended check; it is not a pass.

| Error records | First rejecting dependency |
| ---: | --- |
| 27 | `build/runtime-module` no longer contains the current source inventory. It is missing twelve source files and has two changed source hashes. The current `notice-seasonal-runtime` inventory matches. |
| 25 | Historical NPC creators fail the current complete-source/profile check. The retained fortune/leaflet, postal, museum, snowman, and glyph/interior fixtures predate source and layout changes. |
| 14 | Historical item resources predate current native-name approvals. For example, `alias-items` still calls herabuna `brook trout`; current approval rejects that obsolete donor wording. |
| 4 | Event, renewal, fortune, and leaflet installers reject old resident source inventories before installation. |
| 3 | Historical generation-probe/module bindings differ. Event and renewal creator sources match, but their bound resident hashes do not match the modules selected by the tests. |
| 1 | The retained fortune actor has matching current sources but different bound resident hash/import addresses from the selected historical cartridge. |
| 1 | The original name scenario expects 22 approvals/63 fields while its default loader now includes 43 approvals. |

Do not edit artifact hashes, remove validation, or rename these failures as
successful checks. The remaining fixture work needs matching source/module
recipes or scoped historical evidence, without altering the handed-off ROM.

## Corrected assertions

Eight affected tests pass in `build/v0-regression-accounting-rerun.log`, taking
142.814 seconds. Their production code and build guards are unchanged:

- Native-name generation checks all 43 approvals and their 45 short/128 full
  fields. The alias-mutation test only treats an actual placed alias as an alias;
  direct design clothing approvals do not have an alias conversion to mutate.
- The resolved-identity approval test selects its thirty-entry stage explicitly,
  rather than accidentally adding the four later design approvals.
- Message/rendering diagnostics and shop-letter accounting use the complete
  751,284-character inventory, retaining their exact per-record change checks.
- The opening-guide check compares credit with its actual predecessor, retaining
  the pending-reader condition and rejection of changed installed metadata.

Three assertion failures still need focused follow-up: the date-call rejection
test is stopped by an older creator before reaching its intended target check;
the native-species word-profile rejection is stopped by an older resident source
inventory; and the species accounting assertion predates pending-application
tracking. These are retained as unresolved checks, not waived validation.

## Next work

Repair matching test prerequisites and rerun only the affected tests. Do not
repeat the hour-long full invocation for assertion or documentation fixes.
Continue the title/keyboard implementation independently. A reproduced game
crash, save defect, or memory overwrite requires a fix and focused verification;
these fixture diagnoses do not exempt future game failures.
