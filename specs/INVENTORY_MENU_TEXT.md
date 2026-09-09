# Embedded inventory category and confirmation text

## Sources and complete wording

Extend the installed inventory image with thirteen original text records:
nine six-byte catalogue categories at `80879148`, wrapped-present text at
`8087913C` (five bytes), the throw-away question at `80879068` (five bytes),
and the two-line confirmation at `80879070/80879074` (four/six bytes).
All addresses are linked within the original tag overlay.

Use the supplied GameCube `mTG_catalog_str` as nine complete ten-byte rows,
`present_str$820` as the seven-byte `Present`, and the full thirteen-byte
`mTG_tag_str_suteruno` question. Preserve exact reference capitalization and
padding. The English reference's other two confirmation records are question-
mark placeholders. Translate the original `ホントに` / `いいですか?` as
`Are you` / `really sure?`, retaining two displayed lines and the original
confirmation/cancellation actions. Do not import GameCube-only design-loss
prompts which have no corresponding native branch in this renderer.

## Buffer and drawing boundaries

The catalogue category copy changes stride six to ten and copy length six to
ten; its native ten-byte string field does not grow. Its measurement call uses
the installed font-aware cell helper with a ten-byte bound. The wrapped-present
copy changes from five to seven bytes in the same initialized ten-byte field.
The existing sixteen-byte ordinary-item renderer retains the initializer's
space padding in the adjacent unused field. No sender, saved, or page array
dimensions change.

The three question lines draw directly from appended immutable text, so their
draw lengths change without an intermediate-buffer expansion. Original colours,
scale, sixteen-pixel line spacing, line count, menu order, and actions remain.
Both new confirmation lines fit the native six-cell width; verify using the
installed metrics rather than character count.

The throw-away menu must have enough width for its question, not just its
shorter English Yes/Quit options. In the type-25 dimension branch, replace the
unconditional branch at `8086FB78` with an owned width clamp and return to
`8086FB88`. Preserve the delay-slot height write. The clamp only increases the
measured width to the question's rounded-up pixel width and never reduces a
wider option. This also resolves the too-small question window produced when
only the action labels receive proportional measurement.

## Image and ownership

Retain the original inventory image as the validated base profile. Append a
32-byte clamp and aligned immutable strings; patch only the bound copy/stride/
draw words, source pointer pairs, category measurement call, and clamp branch.
Keep old action records, helpers, callback identities, and original BSS addresses.
Reuse original HI16/LO16 source-pointer relocations, and append relocation rows
for the two new hook targets and clamp's internal return jump.

The expanded profile uses the same inventory DMA pair and verifies actual
resident growth against the owner editor's reservation. Catalogue allocation
uses the actual selected inventory size, not a stale base-profile constant.
Older completed builds remain verifiable under their original profile.

The combined counter inventories these thirteen source records in every build
and credits the installed complete text once. Already credited action labels,
names, letters, and dialogue gain no duplicate weight.

## Verification

Verify complete source/reference hashes, exact old/new words, source-pointer
relocations, independent clamp assembly, original-base reconstruction, all new
text and bounds, rejection of partial mutations, shared allocation, actual
cartridge/UPS reconstruction, and original-ID accounting. Reuse existing font
helper evidence; no new all-menu native harness is required. Representative
category selection, present display, throw-away/cancel, and confirmation joins
the combined v0 safety pass. These checks do not establish hardware acceptance.
