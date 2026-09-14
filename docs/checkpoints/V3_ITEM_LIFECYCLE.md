# V3 item lifecycle work record

## Initial bounded batch and placement defect

Use the current `build/v3-feng-shui-02/animal-forest-v3-asset-loader.z64`
cartridge, SHA-256
`3a99e5fd7870b7d03a3dbcd203f41a8dc9dd4069cccddf8d65e15c06ba5831ce`.
Stage a disposable copy of the preserved town with a daytime emulator RTC.
Neither the source save nor the host clock changes. Public/local patchers and
the trailer remain untouched. Captures use only the private X display.

Check an ordinary acquisition route, inventory/model rendering, placement,
rotation/pickup, and persistence using the assembled pilot implementation.
Reuse passing native component evidence; this is not a full historical replay.
Any fixture-seeded item must be identified as such, not called an ordinary
shop purchase. Separate emulator checkpoint continuity from real FlashRAM
save/restart evidence. Keep all generated captures/saves/checkpoints ignored.

Test-harness construction/debugging has the usual thirty-minute cap. Allow one
justified setup correction/retry and retain passing prefixes. Record unresolved
findings and continue independent villager/content work at the cap; actual game
crashes, save damage, or memory errors remain defects to fix, not waived tests.

Arrival scenario: `tests/scenarios/v3_lifecycle_arrival.json`. The game loads
the copied cartridge save through normal controls; its matching-ROM checkpoint
is for focused continuation only.

The first build reaches the town, inventory, and home interior without a detected
CPU fault. Empty pocket slots 4 and 5 receive `3224` and `32B8` through one
four-byte, frame-paused test write, with the player pointer, original empty
slots, and normal item conditions checked first. Existing items remain intact.
No native function injection is used during these ordinary controls.

The initial navigation follows the outside wall because the house needs a
diagonal facing direction and A interaction, not simply northward movement.
The corrected interaction reaches the interior at `(120, 40, 220)`.

`build/v3-lifecycle-place-barrel-01` reveals an actual missing index conversion.
The ordinary room menu shows the complete English haz-mat barrel name and leaf.
Selecting Drop and then pressing B leaves native item `1224` in pocket slot 4,
not the imported `3224`. The room-drop helper at linked `80871B44` strips the
type nibble and divides by four, passing index 137 rather than 1161 to both
native furniture callbacks. The classification adapter alone does not fix this.
This is a game defect, not an inconclusive controller test, and it blocks a
playable import handoff until corrected and checked.

The fix replaces the six-word index sequence `80871B6C..80871B83`. It uses the
existing checked expanded-index query for enabled imports and retains the
native low-twelve-bit calculation for every other sixteen-bit input. Runtime
room code, allocation, artwork, HRA, feng shui, saved formats, and stable IDs
remain unchanged. The new tag continuation preserves full-width registers.

Corrected build: `build/v3-placement-index-01/animal-forest-v3-asset-loader.z64`,
SHA-256 `5dd08ea450e2ad0b598959c9d4d5893f035649c5e1e37f3a875727da48d6c25b`.
Three focused current-cartridge checks pass: complete declared tag changes,
source/relocation guards, retained dependencies and code, resident bounds/CRC,
UPS reconstruction, deterministic composition, and import-free V2.

The first focused native-window check stops at a stale test-setup parent hash:
the old menu-only fixture predates the assembled icon/catalogue parent changes.
It does not reach the new instruction window. The one justified retry binds
the current composed parent digest instead; old menu/hand tests are not replayed.
Ordinary placement is checked on a fresh boot of the corrected ROM, not a
cross-ROM emulator checkpoint.

The corrected native index-only check in `build/v3-placement-index-native-03`
passes all seven full-register windows in 34 steps. The intermediate `-02`
invocation is rejected before launch because its requested seed lacks a FlashRAM
file; it executes no test. The successful run uses a fresh boot and retains the
old menu/hand evidence without replaying those tests.

Ordinary placement on the corrected ROM succeeds in
`build/v3-lifecycle-current-01` and its checkpointed continuation `-02`.
The hazard barrel appears with the correct textured model and its expanded bank
index is active. Pocket slot 4 becomes empty without altering slot 5's oil drum.
Pickup remains unsuccessful, including the frame-bounded follow-up in
`build/v3-lifecycle-pickup-01`. Fault and translation guards pass. This exposes a
second genuine defect, not a reason to keep guessing controller timing.

## Inlined inverse-ID correction

The room's tile lookup at `80945FC8` reconstructs `2224` from runtime index 1161,
not `3224`. The same inlined calculation occurs in collision at `80943CA0` and
model re-DMA at `8093BBF0`. The previously adapted named inverse function does
not cover these inlined expressions. All three now use the selected import's
full ID while preserving each original unchecked fallback and continuation.
The [identity specification](../../specs/V3_FURNITURE_IDENTITY.md) records exact
windows, preserved registers, guards, and the unchanged save compatibility.

Current corrected cartridge:
`build/v3-room-identity-01/animal-forest-v3-asset-loader.z64`.

- ROM SHA-256: `129113cb34d44bab4c62395fd2eb3d51cdb6931f779fc5276d103138f06cf238`.
- UPS SHA-256: `8f16140143d0f91f697a79c0d081efcb09835794599f7de78129778dd243a437`.
- Room owner SHA-256: `ce4e0ebfb38f5118bb94f9347ddc771e04331562ed9decd91482689751578b19`.

Four focused checks pass: actual C conversion and disabled/native fallback;
the complete six-word owner change and source guards; bounds, dependencies,
retained assembled components, and startup CRC; full composition, UPS
reconstruction, and import-free V2. Native instruction and ordinary pickup
results are recorded below when available.

`build/v3-room-identity-native-01` passes on its first run: 42 steps, including
18 full-register windows across all three changed sites. Cases cover both
selected imports, native index 1, native boundary 947, disabled oil drum, and
index 65535's original unchecked arithmetic. Actual owner loading/relocation,
complete resident prefix, caller stack, HI/LO, floating-point registers, guards,
allocation cleanup, checkpoint restoration, and graceful shutdown pass.

`build/v3-identity-arrival-01` cold-boots the corrected ROM with the disposable
daytime save and reaches the town. `build/v3-identity-placement-01` continues
that matching-ROM checkpoint and passes 24 recorded steps. Ordinary controls
enter the house, open the inventory, choose the imported hazard barrel, and
place it. The complete textured model is visible and runtime bank index 1161
is active. A single four-frame B press picks it up: the model disappears and
pocket slot 4 returns to `3224`, with slot 5 still `32B8`, all original pocket
items unchanged, and every item condition zero. No game function is injected.
Both fault and translation guards pass, as does graceful emulator shutdown.

The final matching-ROM checkpoint has SHA-256
`c008e2af8d07ee9cb156e1ce0a277edb68182a1781fdaafea60deb94b4cec865`.
The original source FlashRAM still has SHA-256
`d489736e39abc7eff1c5b5085bf52e679186f2882a0247339e11603799b80b60`.
The two pocket items are explicitly fixture-seeded, not shop purchases.
This completes the reported placement/pickup defect checks, not an ordinary
save/restart, a shop payment, rotation, or a second-item gameplay test.

Keep the passing current checkpoint and stop extending the controller harness
in this batch. Continue the independent villager-house implementation. Ordinary
acquisition/payment, placed-item rotation/persistence, Controller Pak transport,
and the full villager pilot remain open. Neither web patcher changes.
