# Current progress

## Builds

The supplied private artwork playtest is
`build/releases/v1-artwork-playtest-03.zip`, with local ROM
`build/title-stall-combined-01/animal-forest-title-preview.z64`.
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

The corrected four-MiB v0 remains at
`build/v0-hardware-fixes-02/animal-forest-halfwidth.z64`. Both complete Nook
conversation fixes and the Shrine wording are retained in every current build.
See [the hardware-bug checkpoint](checkpoints/V0_HARDWARE_BUGS.md).
Existing ROMs, packages, and the user's saves remain untouched.

The [post-v0 rebuild command](checkpoints/V1_REBUILD.md) recreates all 26 artwork,
screen, keyboard, and title stages without retained intermediate artwork ROMs
or precompiled overlay directories. Its final ROM/UPS/report match package `03`.
The corrected v0 and source inputs remain prerequisites; the clean-clone base
translation and public toolchain setup recipes remain release preparation work.

## Implemented scope

The combined candidates include proportional Latin rendering, complete known
English text and its name/letter/editor consumers, the English animated title,
and GameCube-style keyboard with native N64 controls and saved capacities.
Screen work covers map, inventory, clock, collections, catalogue, bulletin board,
town tune, birthday, Controller Pak, editor confirmation, warning windows,
mail/repayment, and gyroid service responses.

Building/event artwork includes seasonal shops, Nookington's main and doorway
signs and clearance banners, police signs/posters, Redd's summer sign, SOLD OUT,
both dump signs, fishing props, the fortune table, countdown units, and the
shared stall. Native shrine identity, event rules, and saved
formats remain. The [feature notes](V1_TITLE_PLAYTEST.md) describe the packaged
build; [remaining artwork](ARTWORK_REMAINDER.md) records the newest work and
neutral texture sets already inspected.

## Remaining work and evidence limits

Use [the completion queue](WORK_QUEUE.md). The lucky-bag decorative-writing
choice is pending; the English GC donor itself retains Japanese. The stall
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
