# V3 NPC draw and full voice-ID transport

## Implementation

The [draw specification](../../specs/V3_NPC_DRAW.md) defines the installed routes,
record conversion, stable actor registry, and required audio continuation.
Both NPC overlays route new pilot IDs to separate 100-byte records. Cheri uses
actor `E0EA`, bank 426, voice 285; Punchy uses `E0ED`, bank 429, voice 286.
Native ordinary/test/special rows remain unchanged. Constructor-tail hooks
assign the full voice to the existing actor's 32-bit `+0930` field.

The optional draw variant loads a 16-KiB ABI-2 blob. Startup uses 432 bytes;
the combined asset/draw/voice helpers occupy 908 bytes. The draw helper's stack
frame is 136 bytes, below the original copy routine's 144 bytes. No heap bounds,
actor sizes, saved layouts, overlay lengths, or relocation tables change.

This is not a playable imported-villager build. Audio engine support, names,
defaults/catchphrases, houses, move-ins, dialogue, and persistence remain work.
Items and browser selection remain pending. Stable V2 and public/local patchers
are unchanged; no user saves are used or modified.

## Artifacts

Directory: `build/v3-npc-draw-02/`.

| Artifact | SHA-256 |
| --- | --- |
| `animal-forest-v3-asset-loader.z64` | `da8fc7f0272b5085bab6051924600c38d610e794a72a4da2d33f0a73eee207de` |
| `asset-loader.ups` | `d818233c866e396323b0a932d0acb617e201832d0bb18e61b72f6c37d9b9a09b` |
| V3 blob | `1adfda4ab8b69f4de7d9fb71dd88c9fa55521826569b0238311c9d2cae9c39e9` |

Build into a fresh ignored directory:

```sh
python3 tools/v3_asset_loader.py --npc-draw --output build/v3-npc-draw-02
python3 -m unittest tests.test_v3_npc_draw -v
```

The current ROM remains 32 MiB. Original-resource preservation, complete UPS
reconstruction, and exact V2 output for empty composition are checked. The build
report binds all source hashes, overlay hook hashes, imported records, and assets.

## Focused checks

Seven host/cartridge tests pass: native/test/special/event lookup, all twenty
reserved slots, full voice IDs, DMA alignment, bounds and untouched destinations,
startup/CRC/guard/no-Expansion-Pak failure paths, actual cartridge records,
only-approved edits, original relocation and DMA identities, source hashes,
UPS reconstruction, and the import-free baseline. Address and undefined-behaviour
sanitizers cover the C helpers. Six tests passed together on the corrected build;
the additional native-fixture proof/relocation check passed separately.

Native checks are silent, use no screenshots, and use only disposable emulator
state. No audio audition, complete gameplay/save cycle, or hardware test occurs.

### Found and corrected game defect

`build/v3-npc-draw-native-01/` exposed a real game fault before the fixture ran.
The initial helper sent native DMA directly to its caller's draw destination.
An actual destination was `8014769C`, aligned to four rather than eight bytes.
The native DMA alignment error deliberately faulted at `80029AF4`, address
`11111111`; the captured fault-thread pointer was `8003FFF8`.

The correction restores the original aligned staging/copy contract. A host
test now rejects any DMA destination not aligned to eight bytes and supplies an
unaligned output deliberately. The corrected ROM boots, records no fault, reaches
the native graph frame entry, and contains its complete expected 16-KiB blob.

### Incomplete deeper native fixture

`build/v3-npc-draw-native-02/` passed startup/blob checks but could not allocate
the fixture's `26000` bytes: the captured scene's largest free block was `258D0`.
The bounded setup retry reduced the fixture to its actual `24C00` requirement.
`build/v3-npc-draw-native-03/` successfully allocated that block, but the runner
rejected the overlay-loader call because it lacked the required boot-code proof.
Neither setup failure is a demonstrated game allocation/overlay defect.

The fixture now includes the pinned complete loader/cache proofs and both
overlays' reviewed biased table-base relocation constants. A focused host check
validates those proofs and relocation of both complete images. Native execution
is not repeated again in this batch: its allowed setup attempts are exhausted.
Full native draw results, constructor-tail results, final guards, and checkpoint
restoration remain **unverified**, not passed. The isolated test processes exited;
their disposable files are retained. The fixed cartridge's cold boot and complete
startup-blob checks are the only completed native evidence from this batch.

The final native-attempt results are bound by SHA-256
`d9c61fd1967bbcd46623543b1a96249bb0b9613a51a349273022b206514e3c16`;
run provenance is
`3bd44419d00c76e67c0c86a0788d991e0cc1b8b434a8327b1189d73a83e1a978`.
The fixture source includes the later, host-checked proof correction, so these
results do not claim execution of that revised fixture.

## Next work

Integrate the donor melody fragments and wider native voice/sequence readers.
The specification records exact source/target addresses and discovered constraints
so tracing need not restart. Continue ordinary names/defaults/house/selection and
saved-identity support. Run the corrected combined draw/tail fixture with the next
related runtime implementation batch; do not restart an old-build replay.
V3 saves/profile compatibility remains unverified and requires disposable saves.
