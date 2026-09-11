# Completion queue

## Active work: V2 keyboard

The [N64-inspired keyboard](../specs/KEYBOARD_V2.md) is implemented on V1 Final:
grey shading, native N64 button icons and pressed feedback, and a left-side
stick graphic. The accepted key layout, sounds, proportional editor, controls,
and saved capacities remain intact. The private development ROM is
`build/v2-keyboard-05/Animal Forest English V2 Development.z64`.

Four current cartridge checks pass. Ordinary name entry, space/caret/deletion,
and Start completion pass before the final redundant-label removal. Isolated
screenshots cover representative held N64 controls. The final change removes
the crowded left-side `Move` label while retaining the stick and bottom hint;
artifact checks cover that removal without another native replay. The
[ordinary work record](checkpoints/KEYBOARD_V2_ORDINARY.md) owns the evidence.
Retain the earlier controlled native checks; do not repeat resolved setup work.

Remaining V2 work is concrete playtest feedback, including other keyboard
callers, remaining pressed states, and hardware acceptance. No known V2 change
is awaiting implementation. This does not reopen V1 save testing or
block the available development build. Do not invent further RCs, public
packages, or speculative artwork tasks while awaiting findings. Keep V1 Final
unchanged. No public release is authorised or queued.

The [private offline V2 handoff](checkpoints/V2_PRIVATE_PACKAGE.md) is complete
at `build/v2-private-bundle/V2-Development-patch.zip`. Its three package checks
and bundled standalone patcher pass. No further packaging is queued without
a concrete cartridge or documentation correction; preserve this handoff and
do not use packaging as a substitute for the remaining human acceptance.

## V1 Final

All tracked findings V1-01 through V1-29 have implementations. The
[human acceptance record](checkpoints/V1_HUMAN_ACCEPTANCE.md) closes every
reported V1-01 through V1-23 issue, the reported v0 corrections, and repeated
ordinary save/restart/reload. Do not reopen those accepted cases.

The complete development ROM is
`build/main-diagnostic-text-01/animal-forest-diagnostic-text.z64`. It retains
all RC8 content and adds the [thirteen diagnostic literals](checkpoints/MAIN_DIAGNOSTIC_TEXT.md).
That stage has passing focused checks, committed construction, and full UPS
reconstruction. No known tracked V1 finding awaits implementation.

The [V1 Final handoff](checkpoints/V1_FINAL_PACKAGE.md) is complete at
`build/v1-final/Animal Forest English V1 Final.z64`, with patch-only archive
`build/v1-final/V1-Final-patch.zip`. Three new package checks pass, and its own
standalone patcher recreates the complete final ROM. Preserve these results;
do not create more RCs, repackage without a change, or repeat final verification.
Existing RC artifacts and saves remain intact. Public publication approval and
the recorded redistribution decisions remain separate from the local handoff.

The [requirements audit](checkpoints/V1_FINAL_REQUIREMENTS_AUDIT.md) confirms
the implemented and packaged scope, separates retained evidence from fresh
execution, and records the remaining whole-game-review/publication limits.
It identifies no unapplied tracked V1 finding and does not queue more testing,
neutral-artwork inspection, or repackaging. Public publication needs the user's
direction; new concrete playtest findings can justify further V1 changes.

## Work that can change V1

- Fix concrete new text, layout, artwork, or gameplay defects when identified.
  Crashes, save damage, memory corruption, and blocked progression take priority.
- Preserve GameCube wording, intentional line/page breaks, and timing. Do not
  reflow dialogue broadly or redesign the accepted keyboard during finalisation.
- Keep the final package self-contained: offline patch instructions, sources,
  compiler/source guide, manifest, checksums, save/memory requirements, and
  explicit known limits. The source-build guide points to the final diagnostic
  suffix output, not the older correction-only directory.

Neutral tools, room surfaces, effects, and fish/insect artwork stay unchanged
unless actual lettering or a concrete translation defect is identified.
Broad inspection of those assets is not V1 work and does not delay the final
release. Preserve [completed artwork findings](ARTWORK_REMAINDER.md) without
repeating them. Lucky-bag Japanese decoration intentionally matches English GC
and the user's explicit choice; the shrine remains the native shrine.

## Verification boundaries

Use existing passing source/native evidence for unchanged code and resources.
Do not re-test old builds, launch the full historical construction chain, repair
old test fixtures, resume exhausted harnesses, or maintain the percentage tool
without a concrete current need. Preserve the actual historical full-suite
result; do not claim it passed.

The 61-stage base, 28-stage artwork, nineteen-stage correction, and final
data-only suffix have recorded construction evidence. The composed 109-stage
command is not presented as a newly executed end-to-end run. Package checks
target only the final artifact and its bundled patcher.

Source-identified V1-24 through V1-29 labels retain their recorded verification
limits. Do not enable debug controls, create a town, spawn items, delete Pak
data, or invoke save operations merely to inspect wording. Prior human
acceptance is not fresh execution of these additional labels.

Broader seasonal/event/travel/Pak combinations, individual dialogue layouts,
and ordinary appearance of both adapted festival-stall placements remain
human-playtest work. The controlled stall preview already passes. These
untested cases are not automatically passed, but they do not block the build
that enables further testing. The [validation record](VALIDATION.md) and
[bounded policy](V0_PLAN.md) preserve the evidence and safety requirements.

## Public publication

The source repository remains private. The [release checklist](RELEASE_PREPARATION.md)
and [provenance review](checkpoints/RELEASE_PROVENANCE_REVIEW.md) distinguish
technical readiness from redistribution rights.

- Preserve third-party attribution, licence exclusions, and actual input roles.
  Tooling licences and patch checks do not grant Nintendo-content permissions.
- Obtain the user's public-publication approval and resolve the recorded
  redistribution review before a public upload or repository visibility change.
- Publish only the approved patch package and accompanying documentation/hashes,
  never ROMs, input archives, extracted assets, saves, or emulator checkpoints.

## V2

The [N64-inspired keyboard](../specs/KEYBOARD_V2.md) is the active work. Its
grey N64-controller background, matching button art, and left
control-stick image must preserve V1's accepted sounds, key positioning,
proportional editing, N64 controls, and saved capacities.

## Evidence

Current artifacts are in [progress](PROGRESS.md). Exact implementation and
verification results are retained in [checkpoints](checkpoints/),
[the implementation record](PROGRESS_RECORD.md), and
[the queue record](WORK_QUEUE_RECORD.md). Historical instructions in those
records do not direct completed work to be repeated.
