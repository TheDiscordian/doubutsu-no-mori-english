# Complete inventory labels and item names

## Native boundaries

The tag overlay at VROM `00777AE0`, linked `8086F310`, has 41,600 file bytes
and 288 BSS bytes. Its adjacent relocation file is `00781D60`. The shared
submenu owner's metadata row is at `2CB0`; preserve its constructor, destructor,
procedure setter, and original BSS addresses.

The 44 definitions at `80878F08` select arrays of pointers to eight-byte labels
followed by a four-byte action callback. Their distinct source records are at
`80878AE0..80878CA8`, including an unselected numeric record. Keep all original
menu indices, pointer-array order, and callback identities. Append sixteen-byte
English labels followed by the same callbacks, redirect the original label
pointers, and change only the action dispatch's callback offset from 8 to 16.
The maximum-label reader and both label renderers need sixteen-byte bounds.

Use complete labels from the supplied GameCube executable through explicit
symbol/callback matches. The English reference's unknown deletion label is not
a translation: use the original English draft `Delete` for native `けす`.
The price prompt retains its native numeric placement; `Price:` and `Bells`
use explicit native-layout adaptations rather than importing GameCube control
bytes into plain label fields.

## Ordinary item names

The item-tag initializer clears ten bytes at tag `44` and six bytes at `4E`.
The ordinary-item branch runs only with question/mail type byte `2` equal to
zero. In that branch the adjacent six-byte sender field is unused, so the full
sixteen-byte span `44..53` can hold the complete item name. No tag structure,
save field, allocation, or unrelated name-loader destination is widened.
Question/mail branches retain their separate six-byte name fields and renderer.

Redirect only the item-name load at `808701EC` to a sixteen-byte adapter for
the installed full-name resource. The ordinary item renderer's length at
`808783AC` becomes sixteen. Present and catalogue-name branches retain their
original copies and the initializer's space padding. Do not globally replace
the native ten-byte item loader.

## Geometry and ownership

Use the installed font advances to measure the non-padding text. Convert the
result to the native window's twelve-pixel units, rounding upward so no glyph
is clipped. The maximum-label and ordinary-item width calls use this helper;
other string-length calls retain their original semantics. Existing positioning,
colours, animations, selection, input, and dialogue timing stay unchanged.

Append code/data after the original BSS and move the complete overlay/relocation
pair together to reserved VROM addresses. The added aligned tag size plus the
installed owner-editor growth must fit its existing 8-KiB shared submenu
reservation; verify both dominant and alternative allocation sums. Preserve
every other owner metadata row and native relocation. No extra resident-module
or saved bytes are needed.

## Verification scope

Verify complete source/reference identities, labels and callback order, patched
lengths/dispatch, ownership, relocation, the unchanged original BSS, and the
complete ROM/patch. Use focused host checks for proportional widths and bounds.
Run one representative native inventory/selection check in the combined v0
pass; do not create a new exhaustive all-menu/all-item harness. Normal inventory,
mail/quest transitions, price placement, and hardware remain acceptance work
until executed, following `docs/V0_PLAN.md`.
