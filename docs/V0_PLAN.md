# V0 delivery plan

## Scope and order

V0 is the complete base translation build supplied to the user for playtesting.
Finish the main text and its runtime integration, perform bounded safety checks,
and deliver the patch. The human playthrough requires that build; it is never a
prerequisite for producing or handing it over. V0 is not a claim of exhaustive
gameplay review or original-hardware certification.

This document governs pre-v0 work selection and test scope. The full-project
queue, validation matrix, and individual specifications retain their correctness
requirements and evidence, but their outstanding acceptance lists are not all
v0 blockers. Do not make every subsystem's full test matrix a prerequisite for
starting the next translation batch.

## Remaining implementation

- Finish the remaining general/interface strings, letter text, and accented
  names, using the existing inventory rather than starting another full audit.
- Connect the remaining full-name and input/display consumers so installed
  English text reaches the player without clipping or unsafe wider writes.
- Close actual integration defects, including any found in the installed
  owner-message editor. Batch related changes before native verification.

Keep unused/debug-only records explicitly identified in the work queue. Do not
silently remove them from the translation goal or counting denominator. Preserve
GameCube wording, manual line/page breaks, and timing intent. Title artwork and
the GameCube-style keyboard are v1 stretch goals, not unfinished v0 features.

## Bounded verification

- Retain all build safeguards: source identity, installed-resource checks,
  command and buffer limits, relocation/allocation bounds, ROM checksums, and
  patch reconstruction. Do not disable assertions to get a passing build.
- For each meaningful implementation batch, select the existing focused tests
  for the changed data/code and affected shared consumers. State the risk and
  stopping condition briefly in the work record. Data-only changes do not demand
  another complete native execution matrix for unchanged loaders or renderers.
- Reuse recorded passing evidence when the relevant code, resources, and
  dependencies are unchanged. Identify the tested build; do not relabel old
  evidence as fresh execution. Rerun when a relevant change or new bug warrants it.
- Prefer one representative combined native check over a new per-record or
  all-combinations harness. Add cases for a concrete uncovered risk or reproduced
  defect, not merely to accumulate more proof of already checked behaviour.
- For a testing-setup failure, allow one initial attempt and at most one retry
  after a concrete setup correction. Cap new harness construction/debugging at
  30 minutes per implementation batch, not per case. Changing a timeout, fixture
  name, or invocation does not reset that budget. Do not replay a completed
  prefix just because a later case fails when a safe focused resume is possible.
  These limits govern testing infrastructure, not attempts to fix actual game
  defects. A game crash, save damage, or memory corruption must be fixed before
  v0, with focused verification of the fix.
- At that limit, record the build, failing step, evidence, suspected game-versus-
  harness cause, and next useful check. Continue unrelated implementation.
  Inconclusive tests stay inconclusive; they are neither successful tests nor
  established game defects. Do not assume an unexplained failure is a harness
  problem. Keep possible game failures unresolved until classified, and retain
  credible crash/save/memory risks as v0 blockers. Continuing unrelated work
  does not waive those blockers or permit shipping past them.
- Run the existing full regression suite once for the assembled handoff
  candidate. Fix failures and rerun the affected tests; repeat the full suite
  only when a shared change warrants it. Documentation-only changes require
  document/diff checks, not a ROM rebuild or gameplay tests.

## Handoff checks and blockers

Use one bounded combined smoke pass on the assembled candidate to check boot and
ordinary progression, representative menus and changed editors, mail/board
reading, and a normal save/restart. Reuse existing scenarios and isolated saves;
do not construct an exhaustive player walkthrough as an automation prerequisite.
Check the actual configured RAM requirement; an Expansion Pak is permitted.

Known crashes, save corruption, memory overwrite, blocked basic progression,
failed build safeguards, and unfinished main translation/integration are v0
blockers. A harness limitation or an untested season/home/item combination is
not by itself a demonstrated game defect. Retain missing evidence honestly;
do not infer safe persistence from a blank save or restored emulator checkpoint.

Deliver the patch, source/output checksums, revision, memory/compatibility notes,
and a concise known-issues and untested-areas list. Use separate test saves and
keep the user's existing saves untouched. ROMs and extracted assets stay local.

## After the v0 handoff

The human playthrough supplies broad gameplay and original-hardware bug reports.
Handle those reports and line-layout/wording polish in the follow-up fix pass.
Full seasonal/calendar/travel matrices, exhaustive combinations, and independent
hardware acceptance do not delay creation of the build needed for that testing.
They remain documented acceptance work, not automatically passed checks.

V1 adds the English title/image replacements and GameCube-style keyboard.
Public distribution retains its provenance and release requirements; a private
v0 playtest handoff does not assert public-release approval or finish the goal.
