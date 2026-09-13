# Completion queue

## Compact N64 keyboard presentation

The [key-only tray and attached N64-style sections](../specs/KEYBOARD_V2_LAYOUT.md)
are complete in **V2-10**, at `build/v2-keyboard-polish-10-final/`.
R Space and Z Page exchange places, as do the A/B and C-button groups.
Analytic antialiased corners give the grey shells smooth edges without the
bright top stripes. Seven cartridge checks and one ordinary native input and
appearance pass verify the changes; existing memory allocation is retained.
N64 button colours/shapes, animated stick and held-button feedback, complete
editor/input behaviour, and museum/credits fixes remain intact. Only the
visible case-alteration/order combo hints are removed, not their shortcuts.
The [polish checkpoint](checkpoints/KEYBOARD_V2_POLISH.md) owns exact evidence
and remaining hardware/other-caller acceptance; no implementation is pending.

## Current V2 corrections

**V2-10** retains the faraway museum recipient label and the credits
drawing-buffer correction. The [focused verification](checkpoints/V2_PERFORMANCE_FIXES.md)
passes on V2-08's unchanged resources, including all sixteen credits pages, sampled
fades, unchanged geometry, and native museum/villager/player identity handling.
The [ordinary K.K. Western performance](checkpoints/KK_ORDINARY_PERFORMANCE.md)
also completes, with no measured frozen interval of at least 0.5 seconds across
the recorded 156-second sequence. No all-song or exhaustive hardware test is
claimed. No save migration is required; do not reopen accepted V1 save tests.

## Publication

The existing development repository contains the complete website and reviewed
patch data. The repository is public; GitHub Pages validates and deploys
main-branch pushes through Actions. Keep the repository
name. The [publication guide](WEB_PORTAL.md) describes the automatic workflow
and matching YouTube description URL. Do not change repository visibility or
edit the released trailer.

## Local browser patcher and map correction

The [portal](WEB_PORTAL.md) is running at **http://127.0.0.1:8073/**, serving
`build/web-portal-05/site`. Browser-only patching of both verified game inputs
produces current V2-10. The [map correction](../specs/MAP_TOWN_SUFFIX_FIX.md)
omits the independent Japanese `むら` image beside the town name without save,
code, allocation, or unrelated-art changes. The released trailer is untouched.
Implementation and focused verification are complete; user portal feedback,
and new hardware findings guide further work.
Do not change repository visibility or publish game inputs.

## Released trailer

The local portal uses the user's YouTube upload `UloFru4K4Q8`, loading only on
Play with sound requested. Its redundant MP4 export is preserved outside the
served folder; the original trailer remains unchanged. The integration and
verification are recorded in [the YouTube checkpoint](checkpoints/PORTAL_YOUTUBE.md).

The [YouTube upload resources](promotion/YOUTUBE.md) include a revised thumbnail,
a suggested title, unlisted/release descriptions, and an optional pinned comment.
The thumbnail uses flat, regular lettering and the retained green background;
handoffs contain one upload image, and the user accepts the revision. The user's
YouTube upload is linked in the portal. Release copy includes the patcher address,
`https://thediscordian.github.io/doubutsu-no-mori-english/`.
This resource work does not edit the trailer.

The [released trailer](checkpoints/TRAILER_TOWN_REVISION.md) is preserved at
`build/trailer-cut-05/Animal Forest English - Trailer.mp4` and visually reviewed.
It uses the native opening music, one name-entry keyboard sequence, translated
storefronts and interiors, and the map, catalogue, loan, inventory, and notice-board
screens. Opening and closing identifiers are the only added captions. Production checks and
full decode pass. The user has released the video; do not edit or re-render it.
No further trailer production is queued, and no physical audio playback occurs.
The [V2 hardware feedback batch](checkpoints/KEYBOARD_V2_FEEDBACK.md) is
implemented in `build/v2-keyboard-06`: directional stick tilt, visibly held
buttons, keyboard-wide horizontal glyph alignment, and leftward label/control
adjustments. Six focused checks and the bounded current-build native check
pass within the documented limits. The user has not yet accepted these fixes
on hardware; that does not block private trailer production.

## V2 keyboard

The [N64-inspired keyboard](../specs/KEYBOARD_V2.md) is implemented on V1 Final:
grey shading, native N64 button icons and pressed feedback, and a left-side
stick graphic. The accepted key layout, sounds, proportional editor, controls,
and saved capacities remain intact. The current development ROM is
`build/v2-keyboard-polish-10-final/Animal Forest English V2.z64`, retaining the
map-suffix correction and adding the compact N64-style layout.

The [polish record](checkpoints/KEYBOARD_V2_POLISH.md) owns current checks,
exact artifacts, and limits. The [ordinary work record](checkpoints/KEYBOARD_V2_ORDINARY.md)
retains the earlier accepted editor evidence. Do not repeat resolved setup work.

Remaining V2 game work is concrete playtest feedback, including other keyboard
callers and hardware acceptance of the corrections. No known V2 game change
is awaiting implementation. This does not reopen V1 save testing or
block the available development build. Do not invent further RCs, public
packages, or speculative artwork tasks while awaiting findings. Keep V1 Final
unchanged. Publish only the reviewed website files, not local game inputs.

The [private offline V2 handoff](checkpoints/V2_PRIVATE_PACKAGE.md) is complete
at `build/v2-private-bundle/V2-Development-patch.zip` targets `v2-keyboard-05`;
use the current ROM/adjacent UPS for the feedback corrections. Its three package checks
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
