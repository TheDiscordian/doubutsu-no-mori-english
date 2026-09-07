# Human playthrough and bug reports

## When this applies

The human playthrough follows the broadly complete translation build. Current
experimental milestones are not that final handoff. Development continues with
batched automated crash, save-integrity, text, and regression checks; difficult
isolated cases do not repeatedly hold up unrelated content work.

The playtest package needs a patch, input/output checksums, exact build revision,
compatibility notes, and a linked known-issues list. Keep original saves backed
up and test with a separate town/save copy. ROMs, extracted game text, saves,
and detailed captures remain outside versioned release content.

## Playing and reporting

Play normally through the introduction and jobs, then exercise shops, errands,
house upgrades, mail, the board, and ordinary saving/reloading. Menus should
perform the action named by their English labels. Record naturally encountered
dates, visitors, and events; seasonal coverage and Controller Pak travel remain
separate matrix items when the ordinary playthrough does not encounter them.
An emulator session and an original-console session are distinct evidence.

One report per issue is easiest to fix. Include whatever is available:

- Build revision or patched-ROM checksum; console or emulator, RAM size, and
  flash-cartridge/firmware or emulator version.
- Location, speaker/menu, in-game date/time, and whether the town is new or
  loaded from an existing save.
- The last few actions, what should have happened, and what actually happened.
- Exact text or a photo/video for untranslated text, bad names, layout, or a
  menu that performs the wrong action.
- Whether the issue happened once or repeats; a pre-issue save copy if available.

Do not spend the playthrough repeatedly chasing a difficult reproduction.
Report the observation and continue with unrelated areas when safe. For apparent
save corruption or a crash during saving, preserve the test files before another
save attempt; the last known-good backup is separate evidence.

## Fix and acceptance pass

Record reports in the work queue with their build and evidence. Prioritise crashes,
save damage, blocked progression, and wrong menu actions ahead of cosmetic layout.
Group fixes by affected system, run relevant automated checks once per meaningful
batch, and list the fixes and remaining issues with the next test build.

No report is silently treated as fixed because it cannot yet be reproduced.
English-looking text is not proof of correct meaning, and successful isolated
function calls are not ordinary gameplay proof. The
[validation matrix](VALIDATION.md) and [completion queue](WORK_QUEUE.md) remain
the release checklist; planned human or hardware tests are not marked passed.
