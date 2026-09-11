# V1 human playtest fixes

## Reported build

The user tested `build/title-stall-combined-01/animal-forest-title-preview.z64`
on original hardware. The Press Start corruption occurs on both first boot and
returning to the title. Later artwork-only packages are not evidence that these
reported runtime defects are corrected. Preserve this ROM and the user's saves.

## Open findings

The user reports a further original-hardware session on RC4. New catalogue and
repayment findings take priority over remaining speculative artwork discovery.
That session is not treated as acceptance of every earlier finding or as a
documented save/restart test.

| ID | RC4 finding | Status |
| --- | --- | --- |
| V1-21 | Catalogue currency text beside prices remains Japanese | Exact 32×16 GC Bells image installed; source/retention checks pass, hardware recheck pending |
| V1-22 | Unorderable catalogue items show `ひばいひん` | Complete GC `Not for Sale` reader bypasses the small native buffer; both adapter branches pass native argument capture, hardware recheck pending |
| V1-23 | Post-office repayment screen retains Japanese heading and confirmation text | Complete GC `Your Loan` / `OK` installed and centred in existing slots; focused checks pass, hardware recheck pending |

See [the RC4 menu-label specification](../specs/RC4_MENU_LABELS.md). Preserve
the already installed repayment Cash/Payment/You still owe/Bells images and
catalogue top/bottom controls; inspect the remaining reader paths as part of
this correction. Currency arithmetic, item availability, and saves stay native.
The [correction checkpoint](checkpoints/RC4_MENU_LABEL_FIXES.md) records five
passing focused checks and the bounded native adapter run. The latter captures
font arguments without drawing; it is not screen-appearance acceptance.
All three corrections are included in the packaged
[V1RC5 handoff](checkpoints/V1RC5_PACKAGE.md).

Two further omissions are identified by source review, not a new human report:

| ID | Additional source finding | Status |
| --- | --- | --- |
| V1-24 | Town-tune confirmation retains `ホントに?`, `うん`, and `やっぱやめる` | Complete GC `Are you sure?` / `Yes` / `No` installed in separate follow-up; four focused checks pass, ordinary appearance pending |
| V1-25 | Controller Pak manager retains its Japanese note-deletion instruction | N64-specific `Erase a Pak note` installed and centred in separate follow-up; four focused checks pass, ordinary appearance pending |

The [V1RC6 handoff](checkpoints/V1RC6_PACKAGE.md) includes both corrections and
retains all RC5 fixes. The earlier named RC5 remains unchanged. Note-selection/
deletion and save behaviour remain native; no destructive Pak operation is run
as a test. Both findings still require ordinary appearance acceptance.

V1-26 is a further source finding, not a human report: the native title's
missing-controller warning and retained erase-save menu label remain Japanese
in RC6. The [title-wording correction](checkpoints/TITLE_WARNING_TEXT.md)
installs complete English, preserves the power-off instruction, and centres
all three warning lines. Four focused checks pass; native rendering and hardware
appearance remain unverified. This follow-up is not yet in the named RC6 handoff.
Controller detection, menu actions, and saved formats are unchanged.

V1-27 is a source finding in the separate player-selection and save-menu
gamestates: nine headings, status labels, and destination labels retain Japanese.
The [gamestate correction](checkpoints/GAMESTATE_MENU_TEXT.md) applies complete
English with six passing focused checks. It retains saved identities, actions,
metadata, allocation, and original slot numbers, with longer display copies
bounded inside existing storage. Ordinary access and hardware appearance remain
unverified; this follow-up is not yet in the named RC6 handoff.

V1-20 (critical, corrected candidate; hardware recheck pending): RC3 fails to
load both the user's RC1 and RC2 saves, while a new file works. The copied RC2
save reproduces an overlay-manager out-of-memory fault in RC3, with only 304
bytes free for a requested 528-byte relocation allocation. The same save loads
in RC2. Moving the unchanged bordered font into its own Expansion Pak region
allows the corrected candidate to load that save with 25,216 bytes free and no
faulted thread. Native font/title/module guards remain intact; four focused
loader/resource checks pass. See [the memory specification](../specs/FONT_EXPANSION_MEMORY.md).
The committed replay, package tests, and archived standalone patcher pass;
V1RC4 is available for hardware rechecking. The original
save is preserved locally; the SD card is no longer needed. Cross-version
compatibility is preferred, not required, and must not be confused with fixing
this unintended allocation crash. Save formats are unchanged; untested loading
directions and manual save/restart remain explicitly unverified.

V1-19: on V1RC3, entering spaces in a name inserts the correct spaces and moves
the caret correctly, but also draws one displaced `SP` block per space. The
name-window draw loop at `80884794` still draws these markers using twelve
pixels per character. English GC `mLE_set_dl` draws markers only for its separate
wide-space code, not ordinary spaces. Correct the shared name-window rendering
without changing stored names, the proportional caret, or keyboard Space labels.
The single-branch correction has four passing focused instruction/resource tests
and is packaged with the memory correction in V1RC4. Native marker drawing and
original-hardware rechecking remain pending.

V1-17: the user reports clipped left-edge columns on names/options and extra
bottom pixels on descenders such as `g`; speech usually looks correct. The
specific cartridge revision for this observation is not confirmed. Compare
the native polygon and rectangle paths independently. A transparent-border
polygon correction is implemented in the [font-edge candidate](checkpoints/FONT_POLYGON_EDGES.md),
with four focused tests and the complete controlled native comparison passing.
Original glyph ink, speech, advance widths, and saved formats remain unchanged.
Original-hardware appearance rechecking remains pending.

V1-18: the user reports that the silhouette-shaped transition on building
entry leaves one or two scene-pixel rows visible along the top instead of
covering the screen in black. The [transition correction](checkpoints/TRANSITION_EDGES.md)
enlarges the native mesh beyond all screen edges without changing timing or
scene logic. The old two-row gap is reproduced; all three corrected closed
shapes cover the entire framebuffer. Three focused tests and controlled native
save/guard checks pass. Original-hardware rechecking remains pending.

V1RC1 hardware findings have scoped corrections in V1RC2, with original-
hardware rechecking pending. The user accepts keyboard sound feedback. The
corrected frame has complete controlled drawing evidence; neither that check
nor the earlier partial test establishes ordinary appearance acceptance.
Preserve both candidates and the user's saves.

| ID | V1RC1 follow-up | Status |
| --- | --- | --- |
| V1-13 | Player selection retains an option resembling `はじまて` | Actual `はじめて` reader now copies complete GC `I'm new`; focused relocation checks pass, hardware recheck pending |
| V1-14 | Keyboard top-right is too low, bottom-right is upside-down, hints escape the frame, symbol pages are mostly empty, and key glyphs fit poorly (`_`, `1`, `0` are examples) | Corrected corner UVs/offset, centred hints, shared ink-based glyph placement, and one supported-symbol page installed; six focused tests and native draw/guards pass; sound feedback accepted, hardware appearance recheck pending |
| V1-15 | Two Japanese currency characters remain after the shop cash amount | Separate `ベル` image replaced with exact GC `Bells`; amount/heading retained, hardware recheck pending |
| V1-16 | Idle `pm` has a vertical line of stray pixels below the `m` | PM wraps its p descender at the right edge; compiled clamp correction installed, hardware recheck pending |

The [text/HUD corrections](checkpoints/RC1_TEXT_HUD_FIX.md) and
[keyboard follow-up](checkpoints/KEYBOARD_RC1_FIX.md) are combined in
the packaged [V1RC2](V1RC2_PLAYTEST.md), reproduced by the complete three-stage
follow-up. The original V1RC1 is preserved.

| ID | Finding | Status |
| --- | --- | --- |
| V1-01 | Press Start shows corrupt graphics on first boot and return | Corrected linear source tiles installed in fix build 01; hardware recheck pending |
| V1-02 | Keyboard lacks navigation/button sounds and a GC-style background | Sound feedback accepted; GC frame's reported corner/hint defects corrected under V1-14; complete controlled native drawing/guards pass, hardware appearance recheck pending |
| V1-03 | Bulletin-board dates retain unwanted slash graphics | Separate slash texture cleared in notice/tune candidate; English date reader retained |
| V1-04 | House camera-control hint is Japanese | Exact English GC Camera texture installed in HUD candidate; hardware recheck pending |
| V1-05 | Idle clock shows `am 11:36`, not `11:36 am` | Existing digits/AM-PM geometry reordered in HUD candidate; timekeeping and blink unchanged |
| V1-06 | Town-tune notes are Japanese and OK is too far right | Exact GC A–G and ? textures plus GC OK placement installed; melody rules unchanged |
| V1-07 | Opening a letter for editing shows a Japanese bubble | Both native address prompts use GC English wording; native translation/drawing checks pass, ordinary opening recheck pending |
| V1-08 | Letter recipient list shows `らっきょ`, expected Limberg | Identity-based English reader installed for all 216 villagers; Limberg, an already-correct NPC, and a player pass representative native checks; hardware recheck pending |
| V1-09 | Mail/board editor caret advances too far, wraps early, and jumbles text; saved display is correct | Pixel-layout candidate built; four host/ROM checks and 16 native calls/45 assertions pass; hardware recheck pending |
| V1-10 | Letter To/From text remains Japanese | Exact stock draft defaults normalised to GC To/from; native helper checks preserve custom text, read mode, and identities; ordinary constructor recheck pending |
| V1-11 | Nook shop's blue cash bubble still says `もってるおかね` | English GC Your Bells texture, load, and label geometry installed in HUD candidate; hardware recheck pending |
| V1-12 | Inventory Bells digits are compressed into the left side of their bubbles | Money-only X scale/origin corrected; three focused checks pass, hardware appearance recheck pending |

Fix the broken title and editing display first, then the remaining English
application gaps and keyboard polish. Preserve saved capacities and GameCube
wording, line/page breaks, and timing. Do not count an installed English resource
as a completed reader when this report demonstrates Japanese output. Record
confirmed bindings in the shared progress verification as they are established.

The Japanese lucky-bag decoration stays, matching the English GC release and
the user's explicit choice. It is not an open bug. Keyboard input/layout received
positive human feedback; this does not validate multi-line editor layout.

The recipient-name report identifies one observed wrong name, not an entirely
Japanese list or a complete survey of all villagers. The fix must address the
shared cause across villagers without assuming that all names are wrong or
hard-coding Limberg as the only possible affected identity. Correct English
names, player names, and saved identities must remain intact.

## Verification

Use focused checks for changed code and shared consumers, plus one combined
private fix candidate. Do not repeat unrelated event/artwork tests. Sound calls
can be checked without playing audio through the user's equipment. Original-
hardware rechecking follows delivery; it does not block producing the fix build.
No reported issue is marked fixed merely because a host or emulator test passed
before this human report.
