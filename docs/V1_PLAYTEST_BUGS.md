# V1 human playtest fixes

## Reported build

The user tested `build/title-stall-combined-01/animal-forest-title-preview.z64`
on original hardware. The Press Start corruption occurs on both first boot and
returning to the title. Later artwork-only packages are not evidence that these
reported runtime defects are corrected. Preserve this ROM and the user's saves.

## Open findings

| ID | Finding | Status |
| --- | --- | --- |
| V1-01 | Press Start shows corrupt graphics on first boot and return | Corrected linear source tiles installed in fix build 01; hardware recheck pending |
| V1-02 | Keyboard lacks navigation/button sounds and a GC-style background | Native navigation/page sound call restored in pixel-editor candidate; background and audible hardware check pending |
| V1-03 | Bulletin-board dates retain unwanted slash graphics | Pending binding of date artwork and draw commands |
| V1-04 | House camera-control hint is Japanese | Pending native reader/image binding |
| V1-05 | Idle clock shows `am 11:36`, not `11:36 am` | Pending layout correction |
| V1-06 | Town-tune notes are Japanese and OK is too far right | Pending note labels and control placement |
| V1-07 | Opening a letter for editing shows a Japanese bubble | Pending prompt binding |
| V1-08 | Letter recipient list shows `らっきょ`, expected Limberg | Pending recipient reader and existing-save name handling |
| V1-09 | Mail/board editor caret advances too far, wraps early, and jumbles text; saved display is correct | Pixel-layout candidate built; four host/ROM checks and 16 native calls/45 assertions pass; hardware recheck pending |
| V1-10 | Letter To/From text remains Japanese | Pending label/reader binding |
| V1-11 | Nook shop's blue cash bubble still says `もってるおかね` | Pending label/reader binding |

Fix the broken title and editing display first, then the remaining English
application gaps and keyboard polish. Preserve saved capacities and GameCube
wording, line/page breaks, and timing. Do not count an installed English resource
as a completed reader when this report demonstrates Japanese output. Record
confirmed bindings in the shared progress verification as they are established.

The Japanese lucky-bag decoration stays, matching the English GC release and
the user's explicit choice. It is not an open bug. Keyboard input/layout received
positive human feedback; this does not validate multi-line editor layout.

## Verification

Use focused checks for changed code and shared consumers, plus one combined
private fix candidate. Do not repeat unrelated event/artwork tests. Sound calls
can be checked without playing audio through the user's equipment. Original-
hardware rechecking follows delivery; it does not block producing the fix build.
No reported issue is marked fixed merely because a host or emulator test passed
before this human report.
