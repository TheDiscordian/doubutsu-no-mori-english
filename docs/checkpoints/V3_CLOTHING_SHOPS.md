# V3 clothing shop category checkpoint

## Implementation

The native shop category reader now recognises selected `34BF` as clothing
category 2, through the installed shared category-12 garment validator.
Unknown and disabled `34xx` items return minus one. Native items, imported
furniture, and the original sixteen-bit argument conversion retain their
behaviour. This does not yet add the garment to random stock or the catalogue.

Current build: `build/v3-clothing-shop-category-01/animal-forest-v3-asset-loader.z64`,
ABI 36.

- ROM SHA-256: `958165c43bb59288d980a5c5a0ccf803baf5cfcb36b377078558e5ca1e64871c`.
- UPS SHA-256: `6bf6d13eac360bae17291496717e870e10d50dd2fa24b9a8d8cdaac53d7632b9`.
- Resident prefix SHA-256: `8ae4472a7f8a06953647f3aaf23d391dcd96f1aca5034cf00995ef9dd278709c`.

The helper occupies 116 bytes at `80469C00..80469C73`, with a 24-byte C frame.
The installer and linker both stop at `80469D00`, before the existing room
identity code. The item-category dependency is bound to the installed entry
`8046744C`. There is no new allocation, persistent field, or resource growth.
Save format 2, profile, ownership, garment artwork, and player/NPC loaders are
unchanged. The preceding ABI-35 clothing save is compatible; older format-1
V3 builds and V2 cannot load these format-2 saves.

## Verification

Two focused tests pass: sanitized clothing/non-clothing contracts and current
cartridge composition. Restoring only the shop helper and ABI restores the
complete preceding resource blob. All other game resources except the startup
configuration owner are identical, including stock, menus, player wearing,
artwork, save code, and selected profile. UPS reconstruction passes.

The initial native check `build/v3-clothing-shop-category-native-01` passes
23 records. Eight complete native category calls cover original clothing,
selected clothing, original high-argument truncation, disabled clothing, two
unknown clothing IDs, and both furniture imports including a rotation.
The complete prefix is restored, both guards pass, the fault pointer remains
zero, and the checkpoint is restored before graceful shutdown. The test does
not modify stock, acquire an item, or validate an ordinary purchase.

The preceding [wearing checkpoint](V3_CLOTHING_WEAR.md) retains the ordinary
inventory/wearing/gyroid-save/fresh-reload evidence for unchanged code.

`build/v3-clothing-drop-pickup-gameplay-01` loads the preceding ABI-35 saved
town and successfully changes back to the original shirt, returning `34BF`
to the first pocket. Its subsequent cursor sequence does not drop the item,
so that assertion fails; it provides no ground/pickup evidence.

The corrected `build/v3-clothing-ground-gameplay-01` starts from a freshly
copied, reviewed shirt-in-pocket fixture. It selects Drop from the actual menu,
empties the first pocket, and displays the ground object with intact guards
and a zero fault pointer. Pickup without approaching the selected free tile
does not recover it. The focused continuation `v3-clothing-ground-pickup-01`
overshoots: the player moves from `(2128,1488)` to `(2381,1622)` before pressing B.
The guards/fault checks still pass, but the item remains out of the pocket.
Pickup and its full saved identity remain unverified, not established game
defects or successful tests. Keep the same-ROM checkpoint from the corrected
Drop step for a later frame-based approach; do not replay the cold-boot prefix.
No further movement retries belong to this implementation batch.

## Remaining work

Connect actual donor-backed garment stock, catalogue rows/ownership/previews,
the displayed mannequin representation, and complete ordinary buy/sell and
drop/display persistence. Keep the queued NPC and second-owner evidence open.
Punchy's initialization and move-in eligibility remain disabled. Both patchers
stay V2 until user testing and explicit approval.
