# Current progress

## Builds

The current private playtest is **V1RC3**, with local ROM
`build/v1rc3/Animal Forest English V1RC3.z64` and patch-only archive
`build/v1rc3/V1RC3-patch.zip`. The standalone archived patcher and two package
tests pass, and the cartridge matches the complete two-stage
`v1rc3-rebuild-01` follow-up. The
[package checkpoint](checkpoints/V1RC3_PACKAGE.md) records hashes and source
revision. An Expansion Pak is required. V1RC1, V1RC2, and the user's saves are preserved.
The [bug list](V1_PLAYTEST_BUGS.md) separates implementation from hardware
acceptance; this is not a completed public release or hardware-certified build.

V1-17's [font-edge correction](checkpoints/FONT_POLYGON_EDGES.md) has four
passing focused tests and controlled native drawing/guard checks. V1-18's
[transition correction](checkpoints/TRANSITION_EDGES.md) has three passing
focused tests and native reproduction/correction checks for all three closed
shapes and the centre open/midpoint states. The original two-row top gap is
reproduced; corrected closed shapes leave no exposed framebuffer pixels.
Neither finding is accepted on original hardware.

Retained V1RC2 corrections include the complete GC `I'm new` player option, separate shop `Bells`
unit, and PM texture-edge clamping. Four focused text/HUD tests pass; their
[checkpoint](checkpoints/RC1_TEXT_HUD_FIX.md) records bindings and limits.
The [keyboard follow-up](checkpoints/KEYBOARD_RC1_FIX.md) corrects corner
directions/placement, contains hints, centres key-label ink, and combines all
supported symbols into one page. Six focused tests and the controlled native
drawing check pass (five calls/thirty assertions), preserving save data, memory
guards, and accepted sound code. The full prior editor and font pixels remain.

The separately built [hiring-notice correction](checkpoints/SHOP_HIRING_NOTICE.md)
at `build/v1-shop-notice-fix-03/animal-forest-title-preview.z64` follows V1RC1.
It omits the Japanese Nook 'n' Go placard as in English GC, changing only its
two-triangle command. Four focused checks and complete patch reconstruction
pass. This correction is also included in V1RC2.

Installed corrections cover Press Start pixels, proportional mail/notice editing,
navigation sound calls, Camera/Your Bells images, AM/PM placement, date slashes,
town-tune labels/OK, inventory money sizing, letter prompts/defaults/recipient
display, and the GC-style shaded keyboard background. The recipient reader
supports all 216 villager identities; Limberg is the reported example, not a
hard-coded exception. Player names and saved identities remain unchanged.

Focused source/ROM/patch checks pass for each batch. The pixel editor has
passing native call/guard evidence. Letter UI checks verify representative
recipient names and native prompt/default handling with saved data and guards
retained. The corrected background has complete controlled native drawing and
guard evidence; ordinary appearance remains unverified. See the
[letter](checkpoints/V1_LETTER_UI_FIXES.md) and
[keyboard](checkpoints/KEYBOARD_RC1_FIX.md) checkpoints. The older RC1 background
probe remains a separate partial result, not retroactively passed evidence.

Remaining work prioritises concrete human playtest defects. The
[full regression](checkpoints/V1RC1_REGRESSION.md) finishes with 25 failures and
75 errors across 2,103 tests, primarily rejecting historical fixtures or older
accounting expectations. A scoped title-metadata correction and independent
binary comparison pass. The [core runtime fixture follow-up](checkpoints/RUNTIME_FIXTURE_FOLLOWUP.md)
closes five historical errors, with passing evidence for 69 selected checks
across eight test files and unchanged source/provenance guards. The suite as a
whole is not passed. Further fixture repair remains scoped follow-up work, and
counter maintenance stays deferred. Ordinary letter opening, screen appearance, and hardware
rechecking remain acceptance work. Broad human playtesting cannot block the
build that enables it; confirmed game crashes or data corruption must be fixed.

The retained artwork-only reference package is
`build/releases/v1-artwork-playtest-05.zip`, with local ROM
`build/title-civic-interior-combined-01/animal-forest-title-preview.z64`.
It does not include these human-playtest corrections. Its patcher/reconstruction
tests pass, and the
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
formats remain. The [V1RC3 notes](V1RC3_PLAYTEST.md) describe the current packaged
build; [remaining artwork](ARTWORK_REMAINDER.md) records artwork work and
neutral texture sets already inspected.

The [additional structure inspection](checkpoints/NEUTRAL_STRUCTURE_ARTWORK.md)
finds no readable Japanese wording in the selected train, vacant-lot-sign,
Katrina-tent, and Gracie-car textures. The region warning is already English.
Their native artwork is retained and verified in both relevant cartridge copies;
this is review progress, not newly applied English text.

The [house artwork review](checkpoints/HOUSE_ARTWORK_REVIEW.md) also retains the
native walls, roofs, doors, and decorative oval plaques. The inspected English
GC plaques retain the same central decoration. Both native cartridge copies,
season/type selection, and copyright artwork are checked; this is completed
scoped inspection, not newly translated text.

The [regional review and source-matching inventory](checkpoints/REGIONAL_ARTWORK_REVIEW.md)
resolve the island-cottage donor as GC-only and confirm that the native gloom
effect and three shop drapes contain no Japanese wording. Their native assets
remain unchanged. A read-only matching tool now links supported N64 material
candidates to named GC texels and records unmatched candidates and excluded
formats/readers. It helps target remaining inspection; it does not grant text
credit or claim complete artwork coverage. No replacement ROM is needed for
this review-only work; the combined playtest-fix build remains the current candidate.

## Remaining work and evidence limits

The [prop/shadow/effect review](checkpoints/PROP_EFFECT_ARTWORK_REVIEW.md)
inspects 34 additional native images and the matching English GC umbrella
decoration. These designs remain native; no newly applied text or changed ROM
is claimed. Native/GC I8 inspection support and three focused decoder tests
resolve six previously unsupported gradient-mask views. Four dynamic-palette
candidates remain explicit leads, not completed visual inspection.

The [additional room/item review](checkpoints/ROOM_ITEM_ARTWORK_REVIEW.md)
inspects 48 images: one hiring notice is corrected separately, and 47 neutral
images remain native. This includes seventeen selected Katrina-interior images;
it is scoped review evidence, not a claim that every game image is reviewed.

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

Percentage-tool maintenance is deferred at the user's request. Use existing
inventory when it helps find untranslated text, not as a separate progress-tool
project. The shared counter is `python3 tools/translation_progress.py`; its
candidate selector misses the correction recipes and named release candidates. Do not report an
older cartridge's result as current. The combined approximation counts installed
English against inventoried Japanese source characters across dialogue, names,
letters, and interface/artwork text. Do not report the bank-only diagnostic as
whole-game progress, reuse an old figure, or mix testing effort into replacement
coverage.

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
