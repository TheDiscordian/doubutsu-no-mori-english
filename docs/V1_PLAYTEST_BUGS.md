# V1 human playtest fixes

## Human acceptance

**All user-reported findings V1-01 through V1-23 are fixed and human-accepted.**
The user explicitly confirms every reported issue is fixed and ordinary
save → restart → reload works across many reloads of the same save.
[The acceptance record](checkpoints/V1_HUMAN_ACCEPTANCE.md) preserves the report
and its scope, including the reported v0 corrections. Do not request repeat
checks of these unchanged fixes. Earlier ROMs, saves, and test records stay intact.

The confirmation does not identify an exact ROM checksum or every cross-version
loading direction. It is real-game hardware evidence, not inferred acceptance
from emulator checks or unchanged formats. The newer RC7/RC8 labels are outside those
earlier sessions.

## Accepted reported fixes

| ID | Reported issue | Accepted correction |
| --- | --- | --- |
| V1-01 | Press Start corruption on boot and return | Corrected linear source tiles |
| V1-02 | Missing keyboard sounds/background | Sound feedback and corrected GC frame |
| V1-03 | Bulletin-date slash graphics | Separate slash texture cleared |
| V1-04 | Japanese house camera hint | Exact English GC Camera texture |
| V1-05 | AM/PM precedes the time | Reordered geometry, native timekeeping retained |
| V1-06 | Japanese tune notes and misplaced OK | GC A–G / ? textures and OK placement |
| V1-07 | Japanese letter-editing bubble | GC English address prompts |
| V1-08 | Recipient list shows らっきょ instead of Limberg | Shared identity-based English reader for all 216 villagers |
| V1-09 | Mail/board caret spacing, early wraps, and jumbled editor text | Proportional pixel layout |
| V1-10 | Japanese letter To/From | GC stock defaults, custom text retained |
| V1-11 | Japanese shop cash heading | GC Your Bells texture and geometry |
| V1-12 | Inventory money digits compressed left | Money-only scale/origin correction |
| V1-13 | Japanese first-time-player option | Complete GC I'm new |
| V1-14 | Keyboard corners, escaping hints, misaligned glyphs, and sparse symbol pages | Corrected UVs/offset, contained hints, ink-based placement, and one symbol page |
| V1-15 | Japanese shop currency unit | Separate GC Bells texture |
| V1-16 | Stray pixels below idle pm | Texture-edge clamping |
| V1-17 | Clipped glyph edges and descender artifacts in names/options | Transparent-border polygon correction |
| V1-18 | Exposed top rows in building transitions | Enlarged native transition mesh |
| V1-19 | Displaced SP blocks for ordinary spaces | Ordinary-space marker suppression |
| V1-20 | RC3 crashes loading existing RC1/RC2 towns | Dedicated Expansion Pak font region |
| V1-21 | Japanese catalogue currency unit | Exact GC Bells texture |
| V1-22 | Japanese catalogue Not for Sale | Complete English reader with bounded display |
| V1-23 | Japanese repayment heading and confirmation | Complete GC Your Loan / OK |

The recipient result accepts the reported defect and shared fix; it does not
claim the user separately tested all 216 villagers. Correct English names,
player names, saved identities, and saved capacities remain preserved.

V1-20 remains a defect in the preserved RC3 cartridge itself; do not use RC3
as a fallback. The copied RC2 save reproduces RC3's 304-byte-free allocation
failure and loads with 25,216 bytes free after the font moves. Human acceptance
closes the reported loading defect and ordinary persistence check, not a matrix
of every possible version pair. See the [memory specification](../specs/FONT_EXPANSION_MEMORY.md)
and [RC4 package evidence](checkpoints/V1RC4_PACKAGE.md).

Implementation and native evidence remain in the [letter UI](checkpoints/V1_LETTER_UI_FIXES.md),
[keyboard](checkpoints/KEYBOARD_RC1_FIX.md), [HUD](checkpoints/RC1_TEXT_HUD_FIX.md),
[font](checkpoints/FONT_POLYGON_EDGES.md), [transition](checkpoints/TRANSITION_EDGES.md),
and [catalogue/repayment](checkpoints/RC4_MENU_LABEL_FIXES.md) checkpoints.
Their historical pending-human-test statements do not override current acceptance.

## Source-identified findings

These omissions come from source review, not human bug reports. The user's
confirmation does not establish their ordinary appearance or development-menu
access. None requires deleting data or invoking a save action to inspect wording.

| ID | Additional finding | Implementation and remaining check |
| --- | --- | --- |
| V1-24 | Japanese tune confirmation | Complete GC Are you sure? / Yes / No in RC6; four focused checks pass; ordinary appearance pending |
| V1-25 | Japanese Pak note-deletion instruction | Centred Erase a Pak note in RC6; four focused checks pass; ordinary appearance pending |
| V1-26 | Native title controller warning and erase label | Complete English in committed title-warning stage; four focused checks pass; appearance pending |
| V1-27 | Nine labels in separate player/save gamestates | Complete English in committed gamestate stage; six focused checks pass; access and appearance unverified |
| V1-28 | Japanese development scene/loading/setting text | All 76 strings translated in scene-menu follow-up; focused checks pass; native appearance/access unverified |

The [RC6 handoff](checkpoints/V1RC6_PACKAGE.md) contains V1-24/V1-25.
The [V1RC7 handoff](checkpoints/V1RC7_PACKAGE.md) adds the committed
[title-warning](checkpoints/TITLE_WARNING_TEXT.md) and
[gamestate](checkpoints/GAMESTATE_MENU_TEXT.md) stages with verified packaging.
Controller detection, menu actions, allocations, and saved formats are unchanged.

The [scene-menu follow-up](checkpoints/SCENE_MENU_TEXT.md) closes that owner's
Japanese text without enabling its controls. The [current RC8 package](checkpoints/V1RC8_PACKAGE.md)
contains this batch and every preceding correction, with verified standalone
patch application and offline instructions.
Lucky-bag Japanese decoration is intentionally retained, matching English GC
and the user's explicit choice. It is not an open bug.
The N64-grey keyboard redesign remains V2 work.

## Verification policy

Prioritise new concrete crashes, save damage, blocked progression, or visual/text
defects. Preserve accepted fixes and GC wording, line/page breaks, and timing.
Use focused checks for changed code and shared consumers; do not rerun accepted
unchanged workflows or maintain the percentage tool as a separate project.
Sound calls can be checked without playing audio through the user's equipment.
Source checks, native execution, and human acceptance retain distinct evidence.
