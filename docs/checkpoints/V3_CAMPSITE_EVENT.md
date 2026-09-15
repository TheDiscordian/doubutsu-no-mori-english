# V3 summer-camper event module

## Result

`overlays/v3/campsite_event.c` implements the donor calendar adjustments,
scene-continuation rows, camper selection, and start/stop lifecycle through
explicit adapter operations. `tools/v3_campsite_event.py` verifies the actual
donor calendar and native contracts, then compiles the module. This is source
implementation, **not an installed event or a new cartridge**. The current ROM
and offline composer remain ABI 72. Both served patchers remain V2.

Artifact: `build/v3-campsite-event-module-01/`.

- MIPS code: 1,600 bytes; SHA-256
  `40e6ffcff6785731df5f0816347a0cacb553ebb55f2e778dd2a3f807973399f8`.
- Report SHA-256:
  `5ac5cd78bd79040c823dedf38b5179fd563dd98397c50b77634118936b64e785`.
- Actual donor row SHA-256:
  `9358ece6417d9c874bf3cb56694533950779490a5f2bcc04c67d8052532af334`.
- Proposed code address: `804A2100`; largest individual stack frame: 72 bytes.
  No writable globals or BSS. The linker address is not an allocated, loaded,
  or executable reservation in ABI 72.

## Executed verification

Three unique focused tests pass in `tests.test_v3_campsite_event`:

1. Actual complete donor calendar and five native function contracts, extracted
   row agreement, and changed-input rejection.
2. MIPS artifact/source hashes, code bounds, and explicit uninstalled status.
3. ASan/UBSan host execution of the calendar, selector, and event lifecycle.

The initial host run rejected a fixture that encoded June 30 as hexadecimal
day `30` (decimal 48). The fixture was corrected to `1E`; the single justified
retry of the affected test passed. No production-code correction was needed
for that test failure. No emulator test or historical cartridge replay ran.

The host check covers Saturday/Sunday hour masks, inclusive ending hour 14,
month and year boundaries, leap days, subtraction landing on day zero,
summer-month template changes, non-summer inactivity, inside-tent all-day rows,
exit-frame one-time activity, disabled content, and the work-sequence gate.
Date decoding and event insertion are mocked engine operations: these results
do not establish native event-directory integration or annual gameplay coverage.

Selection retains the donor's six-personality shuffle and 236 swaps, uses the
existing eligibility operations, skips unavailable/disabled/test identities,
and records the selected full identity in two big-endian bytes. Tests cover
new allocation, resume without choosing again, re-registering the same visitor,
greeting-state retention, stop/cleanup calls, exhausted save areas, and invalid
saved identities. Native masked-character allocation and saved-game persistence
are not executed by this host check.

## Verified integration constraints

- Donor schedule table: `.data:441C`, 134 twelve-byte rows. Camper is row 55,
  `.data:46B0`, event 24. Complete row: `06BE004906B8000E00000018`.
- Native date decoder: `8007F1A8`. Native `after_n_day` at `8007DE2C`
  checks the wrapped sign bit but misses a resulting zero day. The GameCube
  source also checks zero. The module supplies that missing boundary handling
  without modifying the native helper used by other events.
- Native daily event table: `80139F98`, sixteen sixteen-byte records.
  Type index: `8013A098`, seventy bytes; native initialization ends at
  `8013A0DE`. The adjacent named BSS must not be treated as free storage.
  Daily cleanup/type loops at `8007F640` and `8007F660` stop at 70.
  Event 70 is proposed, not safe to pass to the unextended native directory.
- Native schedule update: `8007F358`; original source table is
  `80104B60..80104F2C`, eighty-one twelve-byte records. Preserve every native
  event and the job, scene, active-hour, and cleanup behaviour.
- Native save allocation: `80080080`; lookup: `8008033C`. Five shared areas
  have 48-byte strides, eight-byte headers, and forty-byte payloads. The camper
  identity needs two payload bytes, but safe type-directory/lifecycle support
  is required before reserving a new event. No save-format growth is installed.
- Native event NPC records are five twelve-byte aliases, not the donor's
  complete masked animals. A real, separately owned native `Animal` (`528`
  bytes) and default/identity/conversation readers remain necessary. Do not
  borrow a saved town resident or register `D08F` against an unextended table.
- The installed town selector's private eligibility function is redirected to
  the explicit town-policy bridge. Bind through that policy so selected
  islanders remain consistent with town adaptation and disabled imports stay
  excluded; do not restore the legacy donor-growth-only predicate.

## Next implementation

Connect a checked resident allocation, additive native event directory, manager
callbacks, and complete visitor Animal/identity/default/greeting readers.
The module preserves the donor's calls on save-allocation or mask-registration
failure; the native placement adapter still needs a checked failure policy
before a playable handoff. Do not infer a usable camper from the lifecycle's
return value alone.

Then connect actual English conversation states and selected camping rewards,
scene lighting/sounds, and ordinary combined entry/exit/persistence testing.
The unresolved ABI-72 exterior allocation check remains open for that combined
batch. No current artifact is a completed V3 playtest handoff or authorisation
to update either web patcher.
