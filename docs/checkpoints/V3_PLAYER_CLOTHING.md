# V3 player clothing checkpoint

## Implementation

The [clothing specification](../../specs/V3_CLOTHING.md) covers the three
source-checked player startup/change-clothes entry hooks. Both native clothing
buffers, object banks, transfer sizes, and saved field widths remain intact.
Imported artwork is available to these resource readers, but ordinary item
menus/acquisition and the clothing save registry remain required. Punchy's
defaults and move-in eligibility remain disabled.

## Artifacts

`build/v3-player-clothing-01/animal-forest-v3-asset-loader.z64`, ABI 30.

- ROM SHA-256: `6f376337d1f104fd9893d6d38a8cabcf879601592c9af19b76bee2f8b73a3ae2`.
- UPS SHA-256: `33fac463e44b3dcccbe6c18bec675faf530d08219aaffd576e30e66ed5c5e65d`.
- Resident prefix SHA-256: `f20fb02e1cf96cc6ba5c665322e5a408edec23918276df4b6166b2edbaba058c`.
- Combined asset helper SHA-256: `3f1ee445c3cfd54e0edf5d4cb814f4a1b68732387a38e31f1f08ec0be068cb0d`.

Combined asset code is 3,312 bytes, adding 420 bytes inside its existing
reservation. Its loaded prefix remains `C000`, complete DMA file `F220`.
Startup and clothes-changing helpers use 40-byte frames. NPC helper entries,
both NPC owners, clothing metadata/artwork, and the saved profile are unchanged.

## Verification

Three focused tests pass in 1.517 seconds. They check source selection,
double-buffer indices, fallback without saved-field modification, invalid
arguments, exact texture/palette writes, missing-bank rollback, full original
function hashes, entry edits, other retained cartridge resources, unchanged
NPC owners/profile, and UPS reconstruction.

The initial `build/v3-player-clothing-native-01` run completes all 47 recorded
steps and exits normally. A private `3000`-byte allocation supplies a native
bank controller, private-data fixture, two complete garments, and guards.
The four startup calls execute actual native registration and DMA, yielding
bank indices `0,2,1,3`, an original `24BF` first buffer, and the actual imported
`34BF` second buffer. Complete controller/bank records and all 1,088 garment
bytes match independent expectations.

Changing to the imported shirt updates the first buffer and switches to it;
changing to native `BF` updates the second and switches back. Unknown `10C0`
does not toggle or write. A missing inactive bank restores the active selector
and leaves both garments intact. Saved private fields and bank records remain
unchanged. All original globals are restored, all guards pass, the resident
prefix matches, and the fault pointer is zero. The private allocation is freed,
the emulator checkpoint restored, and no game-save writes are performed.

The [NPC queued-check limit](V3_NPC_CLOTHING.md) remains explicitly unresolved;
this batch does not replay its completed foreground prefix or claim queued
completion. Next implement the clothing profile/ownership records and ordinary
item consumers, then verify the combined gameplay paths. Both web patchers
remain V2 pending user testing and explicit approval.
