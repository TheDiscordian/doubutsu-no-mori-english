# V3 villager house checkpoint

## Source review and installed data

The [house specification](../../specs/V3_VILLAGER_HOUSES.md) defines the native
resources, source checks, item mappings, and fixed layer reservations.
The three ignored `build/v3-house-assets-*` reports record extraction and the
completed identity review. The intermediate missing-match status is resolved:
the five common items are verified existing furniture, not new imports.
No text translation or percentage tooling is changed for this review.

Both pilots' wallpapers and floors match their complete native colour images.
Cheri's two layers have complete installed item mappings, including both V3
barrels. Punchy's speed bag and cherry-shirt dependencies remain unimplemented;
his room is not installed. Both new villagers still have move-in selection
disabled. Existing houses, surfaces, furniture, and the public/local V2 patchers
are unchanged.

Current house-development cartridge:
`build/v3-house-layout-01/animal-forest-v3-asset-loader.z64`.

- ROM SHA-256: `8c7dbf467319221f150735e35ed87a09fc219f5e4268e53a1ae9bac2b148b223`.
- UPS SHA-256: `126f9b352001ffd9bff46c3f1251c9f94f9688aeada76f861071310e73335fbd`.
- House table SHA-256: `b7263c3219a17c59330c68da8e9a61af0ea09005ba7655fdc72fd0584e188b3a`.
- Foreground SHA-256: `bf489fdc9607af5cf98c133cd445519fc2a96c9102a38d86f7ef33651dbb3abd`.

The five source words, table prefixes, donor-layer payloads, and unchanged
runtime helpers are verified in the focused tests. The first host run exposes
a test expectation that overlooked the intentional ABI header word. That check
is corrected to verify ABI 23 and compare the entire remaining resident prefix
against the retained parent digest. No cartridge change is needed for that
test correction.
The corrected host run passes all five tests in 4.718 seconds.

## Native execution and remaining integration

Both bounded native attempts target this cartridge. Neither establishes native
house loading. `build/v3-house-native-01` verifies the resident prefix, then the
title-scene heap rejects the 233,472-byte fixture allocation. No house routine
runs. This does not demonstrate an ordinary house-loader allocation failure:
the fixture duplicates the full foreground while the title owns its heap.

The single corrected retry, `build/v3-house-native-02`, uses a 12,288-byte
fixture and only the two appended foreground records. Its allocation succeeds,
but the test runner rejects the DMA call because the fixture omits the required
boot-function proof. The exception occurs before that function executes.
The checked DMA proof is added for the next useful combined integration check;
no third attempt is made in this batch. No house consumer is marked passed.

The combined ABI-25 selection run at `build/v3-villager-selection-native-01`
passes appended foreground DMA and all 498 sparse pointers. Its house-position
assertion expects tile centres rather than the verified native tile origins.
The single corrected house-only retry,
`build/v3-villager-selection-house-tail-01`, passes all 42 recorded steps on
`build/v3-villager-selection-01/animal-forest-v3-asset-loader.z64`.
Complete native house-table initialization, both imported layer selections and
transfers, restored globals, guards, checkpoint restoration, and clean shutdown
pass. The installed house resources retain the hashes above. No source save is
modified. These focused calls do not exercise the ordinary scene's complete
foreground allocation or establish a house visit.

Continue remaining ID-bounded villager readers,
ordinary conversations/house visits, saved identity/profile handling, and
Controller Pak transport. The native furniture reward-selection scans still
need explicit imported-item consideration; building the correct room does not
by itself connect every interaction. Keep the complete furniture lifecycle and
Punchy's actual animated/clothing dependencies open. Broader donor batches and
optional browser composition remain part of the same full V3 goal.
