# V3 house-gift checkpoint

The [reward adapter](../../specs/V3_VILLAGER_REWARDS.md) includes installed
imported furniture in both native house-gift scans. Native exclusions, room
boundaries, random-selection order, rotations, list storage, and identity-based
retrieval are retained. No new heap or saved fields are needed.

Current experimental cartridge:
`build/v3-villager-rewards-01/animal-forest-v3-asset-loader.z64`.

- ROM SHA-256: `07ce3743aac471e6672d78b3fcb55bc02d76b88d0df4b3806e7e265e1ab63a03`.
- UPS SHA-256: `f6f90d91264cd69e6aff614dd12a59137d4671bcb77c32a3f4e5be238b47f6ef`.
- Prefix SHA-256: `16e201fbc4d66a470dcd33ef099c3b11859212a2dc8648be320aa6e07829267c`.
- Reward code SHA-256: `ec75f80d03e61ac501542bc742b9b8340a9519bc3d771610a0b3eac1d0c3c69a`.

ABI 26 retains the 48-KiB resident reservation. The new helper is 552 bytes at
`80463A00..80463C27`; its largest individual compiled stack frame is 56 bytes.
The existing selection code, full house data, and other installed resources
are unchanged. All imported move-in flags remain disabled.

## Focused verification

All four host/cartridge tests pass in 1.518 seconds. They cover mixed original
and imported items, both pilots and rotations, native excluded categories,
unknown/disabled imports, row/column boundaries, missing layers, invalid draws,
no-candidate RNG preservation, exact source guards, compiled bounds, startup
CRC/ABI, retained dependencies, patch reconstruction, and import-free V2.

The initial native run, `build/v3-villager-rewards-native-01`, passes all 45
recorded steps. The installed selector returns both rotated imports while
rejecting excluded native furniture and out-of-room cells. Empty/disabled
candidate sets preserve RNG. Non-empty sets consume exactly one native draw.
Using Cheri's actual installed room, the original list-population caller stores
each imported barrel with its complete ID, and the original personal-identity
getter retrieves it. Other list slots, input room, live identity records,
pointer table, memory guards, and complete resident prefix are intact. Temporary
globals are restored, the fixture is freed, the emulator checkpoint is restored,
and shutdown is clean. No game save is written and source saves are untouched.

These are native function checks, not an ordinary furniture-gift conversation
or proof of the full acquisition/persistence route. Continue ordinary villager
construction, conversations and visits, remaining data readers, save/profile
integration, furniture lifecycle, and broader donor content. Both V2 patchers
remain unchanged; V3 development source continues on GitHub.
