# V0 hardware playtest corrections

## Priority and retained input

The user reports a whole-conversation loop in Nook's first furniture-delivery
job with Buzz: delivery succeeds, Buzz gives furniture and talks, and then the
conversation returns to its opening dialogue and repeats indefinitely. Fixing
conversation completion and tutorial progression is the first priority.
Preventing only repeated item writes does not satisfy this report.

Preserve `build/classic-letters-pilot/animal-forest-halfwidth.z64`, SHA-256
`31c85f23c996b70bd7a4779b43f1039716a77c84806dfa5a7dd52e3780d50860`.
Build corrections separately and preserve every unrelated English resource.
Do not modify the user's saves. Title-preview work remains separate.

## Investigation

The native first-job overlay at VROM `00814FA0`, original RAM `8091CB30`,
contains the reward handler at `8091D2D0`. The native handler leaves
`talk_step` at reward step seven and schedules the personality-specific advice.
The manager's ordinary wait detects continuing-message endings and dispatches
the current step again. The installed cranky advice `08F8` uses `01` and an
explicit continuation to `2B05` to fit the full English into bounded records.
The added transition re-enters the reward handler and overwrites the intended
continuation. The original-owner comparison below reproduces that failure in
native execution; the fix advances the owner state rather than filtering items.

Related split furniture advice uses `08F4 → 0921` and `08FA → 2B06`.
Letter-sharing advice also has added continuations. Its pending finish step
clears the manager's message number, then replaces the intended continuation
with zero. This affects `0910 → 0A26` and `0912 → 2B47`; a fourth native
instruction correction selects the existing no-operation state after the
post-view completion handler. Its native comparison below verifies both the
original failure and corrected continuation. Existing isolated message-loader
tests do not execute the quest owner's conversation state.

## Other reported corrections

- Map: replace the incorrect "Wishing Well" with "Shrine". The current words
  are emitted by `tools/map_labels.py`, not baked into a texture. Separate the
  GameCube donor evidence from the N64-specific output correction.
- Signs, bags, building signs, map, inventory, and time-setting screens: identify
  remaining Japanese text and artwork. Extract matching English GameCube assets
  from the supplied disc where compatible; preserve N64-specific locations.

## Verification and delivery

The first-job-only correction is
`build/v0-first-job-fix-01/animal-forest-halfwidth.z64`, SHA-256
`6c44e1d71b7d3d13864c576138ad983a4c9747a1bf2e97d268fc576ba3fa8811`.
The UPS SHA-256 is
`69b03f18928acb2623acc4fbc5513f8801efa52ee320b88865c5c3af9883222e`.
The [implementation specification](../../specs/FIRST_JOB_PROGRESSION.md) describes
the three instruction changes. All four focused host tests pass, including
independent MIPS assembly, exact relocation, rejected damaged inputs, retention
of every other installed resource, and complete patch reconstruction.

`build/v0-first-job-native-02/results.json` passes 256 recorded steps: 70 native
calls, 170 fixture assertions, complete checkpoint restoration, the final
resident guard, and graceful silent shutdown in four MiB. The original owner
reproduces `08F8 → 08F8` with a repeated takeout request. The corrected owner
completes all six personality paths, including `08F4 → 0921`, `08F8 → 2B05`, and
`08FA → 2B06`. Each retains the full loaded English, one reward/handoff request,
the reward inventory state, and completed quest progress; each reaches the real
normal message-disappearance request. No dialogue record is changed.

The fixture runs the actual native owner dispatcher, reward handler, shared
takeout-request code, ordinary wait, message loader, and normal continuation/
closure functions. It uses synthetic isolated quest/player/NPC records and
positions the cursor at the real message endings. It does not execute ordinary
NPC animations, walk back to Nook, save a town, or establish hardware acceptance
of the correction. The user's save is untouched.

The first native attempt stops on a Python fixture error after loading both
overlays: a serialized list was treated as a mapping. The corrected retry above
passes. No further setup retry or exhaustive tutorial harness is required for
this batch.

## Combined correction

`build/v0-hardware-fixes-01/animal-forest-halfwidth.z64` combines the unchanged,
tested owner fix with the source-bound one-line Shrine correction. ROM SHA-256:
`90c1280d768132a07002bcf44ceefa1f8f872606f3ac186e069af64f5db38980`.
UPS SHA-256:
`b1c07490c635a310674f7197828aa8f46cf7123316d6b70cc93ab16cd4c63494`.
The complete map image remains 27,072 bytes; its relocation, code, names, icons,
and allocation are unchanged. Only the shrine record, line length, and Y position
change. The [map specification](../../specs/MAP_LABELS.md) preserves the GC donor
evidence separately from the corrected N64 wording.

This intermediate build retains the later letter-advice defect and is not the
recommended correction handoff. Keep it as an independently verified map and
furniture baseline for the final build below.

## Complete first-job correction handoff

`build/v0-hardware-fixes-02/animal-forest-halfwidth.z64` adds the single-instruction
letter-advice correction while retaining the furniture fix, Shrine label, and
all other resources. ROM SHA-256:
`b93a54b8804f262e1c05e7dabcd6aac4f5b47d637c69d94264f058c12dbdbd35`.
UPS SHA-256:
`378400869b2b4965f6a5641a23c861fbc5a1d0b98e445ab43d88a6a548cbc3ea`.

`build/v0-first-job-letter-native-01/results.json` passes 155 steps, 43 native
calls, and 99 fixture assertions. The original owner demonstrably replaces the
cranky continuation `0A26` with message zero. The corrected `090C`,
`0910 → 0A26`, and `0912 → 2B47` paths retain complete English and completed
quest state, make no inventory changes or furniture requests, and reach normal
conversation disappearance. Heap/stack/resident guards, singleton restoration,
full checkpoint restoration, and graceful silent shutdown pass. This new
game-defect correction uses the existing fixture and passes its first native
execution attempt. It is not a repeated furniture or full tutorial run.

The four-MiB ROM retains native owner sizes and save layouts. Reuse the passing
furniture evidence for the unchanged reward handler; the fourth instruction
belongs only to the later post-letter-view handler. The full map, runtime,
English records, and every other installed resource are retained. Ordinary
hardware tutorial replay, animations, and saving remain human checks. The
remaining Japanese interface/artwork is the next implementation batch.

All nineteen focused host/artifact tests pass: nine first-job checks, four
map-label checks, and six patch/package checks. These include independent MIPS
assembly for both corrections, source rejection, two-base relocation,
complete resource retention across both combined builds, recorded native-result
validation, final patch reconstruction, and separate correction playtest notes.
The GitHub repository remains private. The patch archive is being prepared from
the committed source revision; no ROM or extracted game art is committed.
