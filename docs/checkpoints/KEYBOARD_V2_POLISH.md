# V2 keyboard control swaps and rounded-shell polish

## Deliverable

V2-10 addresses the three V2-09 findings: R Space and Z Page exchange places,
the C-button/Cursor section sits above A/B Type/Del, and the controller shells
have smoothly filtered curves instead of coarse steps and bright top stripes.
N64 colours, native button/stick artwork, pressed poses, all editor controls,
key positions, and the hidden combination shortcuts remain intact.

- ROM: `build/v2-keyboard-polish-10-final/Animal Forest English V2.z64`.
- ROM SHA-256: `64335524d2159b5715a73f331c741e11ea12b9a98c67a5903905e406765ddb01`.
- Original-ROM UPS: `build/v2-keyboard-polish-10-final/Animal Forest English V2.ups`.
- UPS SHA-256: `f08d3f1b6a07d514fb43277af5ad808bb4d0670fdd2ad9cf252feac1d4121063`.
- Construction receipt SHA-256: `f1a31c68b6ecfb0e1ad611bb8bb13d4b0bdbf71a9cc99f2d6b1d7c2197e57d72`.

## Cause and implementation

The previous shell renderer divides each part into sixteen flat rectangles.
On larger grips, each rectangle spans several native pixels, making the curve
visibly stair-stepped. Its first band's shade is 242, abruptly brighter than
the following band's 218, producing the reported light stripe.

The replacement uses one analytic 16×16 quarter-circle, supersampled 8×8 per
texel and stored as a 128-byte I4 mask with sixteen coverage levels. Nine-slice
rectangles and native bilinear filtering preserve rounded corners at each
part's radius. The existing I4 material supplies both soft alpha and edge
shading. Grey primitive `(223,226,230)` and environment `(174,177,181)` colours
replace the top-band highlight. Native button, font, and GC tray pixels are
unchanged; the tray uses the coordinated grey material.

Tray drawing shares one texture-rectangle loop while preserving all four
donor orientations and bounds. This and the compact mask keep the 38,448-byte
editor within its existing 8,192-byte rounded suffix reservation. No pool or
resident module grows. At most 63 shell texture rectangles replace the 112
band rectangles and their per-band state commands, reducing drawing commands.
All font-space guards remain active. Over-budget development compiles are
preserved and rejected before a handoff ROM is written.

## Focused verification

Seven `tests.test_keyboard_v2_layout` tests pass in 4.397 seconds. They bind the
current sources and complete original-ROM UPS reconstruction, compare the
entire input prefix at two relocation bases, verify moved button/letter tables,
check corner coverage/symmetry and compiled texture identity, retain donor
tray pixels, and enforce the unchanged allocation. Every unrelated resource
is compared against both the V2-08 construction input and the V2-09 handoff.
This is static comparison, not another old-build gameplay test.

`build/v2-keyboard-polish-native-01/` cold-boots the exact V2-10 ROM in silent,
isolated ares, using ordinary controls to reach name entry. The existing
scenario adds one B-held capture and completes all 45 result entries. Empty
name, eight-MiB, resident-guard, and native-fault-zero checks pass, followed by
graceful shutdown. No user save is opened or changed.

The screenshot skill guides review of all nine captures: neutral, diagonal
stick, A/typing, B/deletion, L/lowercase, Z/symbols, R/space, C-right/caret,
and same-build neutral restoration. The moved controls and their held poses
are visible, captions fit, the curves are smooth, and the bright top stripes
are absent. Original-hardware appearance remains a human judgement.

- Native results SHA-256: `2b37349dbb6a4a05df3ef5f12f2c449b8a3a23b114b7e272f6cdbf87df357ad8`.
- Native run identity SHA-256: `1bc7f720f2d5b6ea264720dcdff1ca849b2eb270aa2735f54f799ed0350557a1`.

## Browser patch and compatibility

The local export is `build/web-portal-05/site`; tracked `web/release/` and the
Pages staging pins match V2-10. Recipe SHA-256 is
`c97f4986ea30ec07519e7f6653fc0f155667f2c85b21abf278248cd98e70be8d`.
It contains 23,093 commands, copies 2,783,780 bytes from the GameCube donor,
and occupies 1,889,823 compressed bytes.

Five Pages packaging tests and eleven JavaScript patch tests pass.
`build/web-portal-check-10/` records real silent Chromium downloads from CISO,
sparse ISO, and a Pages-style subpath. Each matches the exact ROM above, in
0.63, 0.60, and 0.80 seconds respectively. Cancellation, incorrect inputs,
stale-download clearing, and three responsive widths pass, with no browser
errors or non-local requests. Website copy and the released trailer are intact.

Save formats are unchanged. V2-09 → V2-10 and V2-10 → V2-09 compatibility are
expected without migration; those loading directions are not freshly exercised.
Earlier builds and saves remain preserved. Expansion Pak, 128-KiB FlashRAM,
and RTC remain required. The museum/credits correction, accepted V1 behaviour,
and all other keyboard callers retain their existing evidence and limits.
