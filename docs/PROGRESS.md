# Current progress

## Builds

The first original-hardware V1 playtest of `title-stall-combined-01` reports
corrupt Press Start graphics, broken mail/board editor spacing, remaining
Japanese interface/name readers, and keyboard polish needs. The
[bug list](V1_PLAYTEST_BUGS.md) is the current implementation priority. Existing
host/emulator checks do not override these observations, and later artwork-only
packages must not be described as correcting them.

An [intermediate Press Start correction](checkpoints/V1_FIRST_PLAYTEST_FIXES.md)
is built at `build/v1-playtest-fixes-01/animal-forest-title-preview.z64`. It fixes
the donor's incorrectly converted pixel storage without code/allocation changes;
three focused source/retention/patch tests pass. The remaining playtest findings
stay open, and this is not yet the combined fix handoff.

The next [editor correction](checkpoints/V1_FIRST_PLAYTEST_FIXES.md) is built at
`build/v1-editor-pixel-fix-03/animal-forest-title-preview.z64`. It retains that
title correction and aligns draft wrapping, caret, and vertical navigation with
the English read layout. Four focused sanitizer/font/ROM checks pass, along with
16 native calls and 45 assertions with intact guards and restored checkpoint.
Original-hardware rechecking remains; Japanese labels and the keyboard
background are still open. This is an intermediate candidate, not a completed
playtest-fix package.

The [HUD correction](checkpoints/V1_HUD_LABEL_FIXES.md) adds the English GC
Camera and Your Bells images and moves AM/PM after the idle time. The combined
intermediate is `build/v1-hud-label-fix-02/animal-forest-title-preview.z64`.
Four focused checks pass; this data-only batch preserves CPU code, allocations,
timekeeping, and saved data. Remaining playtest findings stay open.

The [notice/tune correction](checkpoints/V1_NOTICE_TUNE_FIXES.md) removes the
two obsolete date slashes, installs the GC A–G/? note images, and places OK at
the GC coordinates. The combined intermediate is
`build/v1-notice-tune-fix-01/animal-forest-title-preview.z64`; four focused checks
pass. The reported inventory Bells-digit sizing joins the active bug list.

The supplied private artwork playtest is
`build/releases/v1-artwork-playtest-05.zip`, with local ROM
`build/title-civic-interior-combined-01/animal-forest-title-preview.z64`.
It requires an Expansion Pak. Its patcher/reconstruction tests pass, and the
[package checkpoint](checkpoints/V1_PLAYTEST_PACKAGE.md) records hashes,
source revisions, contents, and limitations. It is not a public release or
original-hardware certification.

The package includes the
[GC-style festival stall](checkpoints/STALL_ARTWORK.md), using one shared mesh
and a reflected second placement inside the original allocation. Three focused
tests, the title combination, and the full combined counter pass. A
[controlled native graphics preview](checkpoints/EVENT_ARTWORK_PREVIEW.md)
renders both placements and the fortune table with intact memory guards and
restored checkpoint. The visible surfaces are inspected; the stall preview's
lowest edge is clipped by its framing. Ordinary
stall appearance, lighting, both placements, and event acceptance remain.

The [shop-interior batch](checkpoints/SHOP_INTERIOR_ARTWORK.md) installs seven
exact GC English sign textures across the ordinary, raffle-day, and upstairs
Nookington rooms. Five focused checks, title combination, and the full counter
pass. Every unrelated resource, native room vertex, drawing command, saved
layout, and shop rule remains unchanged. Ordinary room appearance remains
playtest work; the tiny original information-notice wording remains an explicit
transcription gap, not an uninstalled English image.

The [civic-interior batch](checkpoints/CIVIC_INTERIOR_ARTWORK.md) installs the
exact English GC wanted/recruitment posters and postal MAIL bag in two native
rooms. Five focused checks, seventeen counter unit tests, the complete combined
counter, title combination, and patch packaging pass. The three images fit
existing native slots with no palette, geometry, command, gameplay, or save
changes. Ordinary room appearance remains playtest work.

The corrected four-MiB v0 remains at
`build/v0-hardware-fixes-02/animal-forest-halfwidth.z64`. Both complete Nook
conversation fixes and the Shrine wording are retained in every current build.
See [the hardware-bug checkpoint](checkpoints/V0_HARDWARE_BUGS.md).
Existing ROMs, packages, and the user's saves remain untouched.

The [post-v0 rebuild command](checkpoints/V1_REBUILD.md) recreates all 28 artwork,
screen, keyboard, and title stages without retained intermediate artwork ROMs
or precompiled overlay directories. The complete 28-stage public-image execution
passes and matches package `05`'s ROM/UPS and approved title-report profile.
The [isolated base recipe](checkpoints/V0_REBUILD.md) also passes all sixty-one
stages from an empty build directory, regenerating corrected v0 from clean source
checkouts and the three supplied inputs. Its final ROM/UPS/report exactly match
corrected v0.
The retained complete source-to-v1 run passes all twenty-six package-`03` stages
inside that clean checkout. See the
[combined rebuild evidence](checkpoints/V1_REBUILD.md).

The [published compiler setup and complete clean rebuild](checkpoints/PORTABLE_TOOLCHAIN.md)
also pass all 87 package-`03` stages with exact final ROM/UPS matches. Build reports retain
the actual public image identity; separate comparison fingerprints preserve
compatibility with the older approvals. Building no longer depends on the local
development Docker image. Source inputs remain local and separately licensed.

## Implemented scope

The combined candidates include proportional Latin rendering, complete known
English text and its name/letter/editor consumers, the English animated title,
and GameCube-style keyboard with native N64 controls and saved capacities.
Screen work covers map, inventory, clock, collections, catalogue, bulletin board,
town tune, birthday, Controller Pak, editor confirmation, warning windows,
mail/repayment, and gyroid service responses.

Building/event artwork includes seasonal shops, Nookington's main and doorway
signs and clearance banners, police exterior/interior signs/posters, the postal
MAIL bag, Redd's summer sign, SOLD OUT,
both dump signs, fishing props, the fortune table, countdown units, and the
shared stall. Native shrine identity, event rules, and saved
formats remain. The [feature notes](V1_TITLE_PLAYTEST.md) describe the packaged
build; [remaining artwork](ARTWORK_REMAINDER.md) records the newest work and
neutral texture sets already inspected.

The [additional structure inspection](checkpoints/NEUTRAL_STRUCTURE_ARTWORK.md)
finds no readable Japanese wording in the selected train, vacant-lot-sign,
Katrina-tent, and Gracie-car textures. The region warning is already English.
Their native artwork is retained and verified in both relevant cartridge copies;
this is review progress, not newly applied English text.

The [regional review and source-matching inventory](checkpoints/REGIONAL_ARTWORK_REVIEW.md)
resolve the island-cottage donor as GC-only and confirm that the native gloom
effect and three shop drapes contain no Japanese wording. Their native assets
remain unchanged. A read-only matching tool now links supported N64 material
candidates to named GC texels and records unmatched candidates and excluded
formats/readers. It helps target remaining inspection; it does not grant text
credit or claim complete artwork coverage. No replacement ROM is needed for
this review-only work; playtest `05` remains the current candidate.

## Remaining work and evidence limits

Use [the completion queue](WORK_QUEUE.md). Lucky-bag Japanese decoration is
intentionally retained at the user's request, matching the English GC donor.
It is not an outstanding translation task or new English credit. The stall
adaptation still needs ordinary appearance acceptance. Other unreviewed game images
are not declared complete by the scoped seasonal-prop inspection.

The embedded warning drawing probe remains incomplete after its permitted setup
retry; do not repeat that setup batch. Birthday and gyroid controlled drawing,
title/START/low-memory, and corrected keyboard input have passing native evidence
on the exact builds/checkpoints documented in their records. Retention checks
preserve unchanged implementations; they do not turn that evidence into a fresh
ordinary playthrough of a newer ROM.

Normal tutorial replay, menu/editor/transaction use, save/restart,
return-to-title/existing-save cases, travel, events, and original-hardware
acceptance remain human playtest work. Confirmed crashes, save damage, and
memory corruption must be fixed; test-infrastructure limits do not waive them.
Preserve GameCube wording, intentional line/page breaks, and timing during polish.
Public release still needs provenance review and explicit release approval.

## Translation measurement

Run `python3 tools/translation_progress.py` for one fresh combined approximation.
It verifies the newest completed cartridge and counts installed English against
inventoried Japanese source characters across dialogue, names, letters, and
interface/artwork text. Do not report the bank-only diagnostic as whole-game
progress, reuse an old figure, or mix testing effort into replacement coverage.

[Counting rules](../specs/TRANSLATION_PROGRESS.md) retain explicit inventory
limits, including the tiny untranscribed stall labels. The installed stall model
is verified even though those labels receive no invented character weight.
Generated reports and the per-record ledger live in `build/translation-progress/`.

## Detailed records

Exact implementation and test results live in [checkpoints](checkpoints/),
[specifications](../specs/), and the preserved
[implementation record](PROGRESS_RECORD.md) and [queue record](WORK_QUEUE_RECORD.md).
Build-specific historical instructions in those records do not override this
current state or the [bounded testing policy](V0_PLAN.md).
