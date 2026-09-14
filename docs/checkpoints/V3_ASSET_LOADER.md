# V3 additive object-loader batch

## Result

The [V3 asset loader](../../specs/V3_ASSET_LOADER.md) loads both converted villager
texture objects through the native synchronous object-loading path. All 410
existing object-bank entries and every existing cartridge DMA index survive.
The startup/helper code uses no additional ordinary heap space.

This is an internal development cartridge, not a playable-villager release.
Punchy and Cheri have texture banks, but no imported draw rows, actor IDs,
voices, move-ins, houses, or save identities are enabled. V2 remains the stable
cartridge and public/local patcher output.

## Current artifacts

Directory: `build/v3-asset-loader-02/`.

| Artifact | SHA-256 |
| --- | --- |
| `animal-forest-v3-asset-loader.z64` | `6dac058878e9d85bae65702f0b14e0349d7ba39d9cb06a2dce7222a7313d89b4` |
| `asset-loader.ups` | `6c76495c106d3070ebe7362b10138a958dcf2481862f3235f11fdd856d24639f` |
| V3 runtime blob | `78891d64d41d411e06dbd94d7eec34021d18c35c406daede68c1bfac28e9301d` |
| Generated native scenario | `cfaa895d8488f77b0d6f632a6f51bc8f3d5b946e35cd9ffb3424b4f5af452e55` |

The ROM remains 32 MiB. The startup helper occupies 432 bytes within its 1-KiB
reservation; the object helper occupies 384 bytes. The upper-memory blob is
8,192 bytes, including the 430-entry object table. Existing font/title and
ordinary heap reservations remain unchanged. The first development build is
preserved; the current build explicitly normalises the native 16-bit argument
before indexing the table, including callers with nonzero upper argument bits.

Construction uses the pinned Docker toolchain and supplied donor:

```sh
python3 tools/v3_asset_loader.py --output build/v3-asset-loader-02
python3 tools/v3_asset_loader_scenario.py --output build/v3-asset-loader-02/scenario.json
```

Use fresh output paths for new construction. Generated scenarios include local
game assets as exact DMA expectations and must remain ignored, like the ROMs.

## Focused checks

`python3 -m unittest tests.test_v3_asset_loader -v`: **five tests pass** on the
current batch, with no skips. These include host address/undefined-behaviour
sanitizers, source rejection, original-resource and DMA-index preservation,
actual imported textures, empty composition, and complete UPS reconstruction.
The empty composition is exact V2-11, not a merely similar no-import build.

Current native run: `build/v3-asset-loader-native-02/`.

- Twenty explicit memory assertions and six native calls pass.
- The complete V3 blob matches after cold startup and the object hook is installed.
- The ordinary synchronous scene loader transfers the existing cat model,
  Cheri's texture bank 426, and Punchy's texture bank 429. Every output byte and
  complete test-arena field matches. Native DMA/completion owns the transfers.
- Empty bank 410 and out-of-range bank 430 return failure without changing the
  test arena. The direct status call with argument `123401AD` correctly uses
  bank 429 after native low-sixteen-bit conversion.
- Translation, font, and V3 guards remain intact; no faulted thread is recorded.
  The isolated emulator checkpoint is restored before normal execution resumes.
- The run uses disabled audio and no screenshots. No user save is used.

Native results SHA-256:
`94096d4ab9d465d398ae7622a650e57b419ca19de83f46b7a62efcc54f858a0b`.
Run provenance SHA-256:
`3a5ed77455f67c7486e4562816f7c3252767d5dacbea37ea58ca10539b0d419d`.

The current cartridge also passes the existing six-assertion no-Expansion-Pak
scenario in `build/v3-asset-loader-no-pak-02/`, preserving the low-memory stop
path without a fault. Results SHA-256:
`16cab4f8e368ba00bf035738f24dc6b1f6c0825884419b749c4a29c28975785a`.

No complete villager rendering/animation, ordinary imported gameplay,
save/restart compatibility, or original-hardware verification is claimed.
Use disposable saves for V3 development. No import profile is ready for a user
save; future enabled-ID/profile compatibility remains unverified.

## Next action

Use the installed texture-bank assignments for native draw rows only after
resolving donor voice IDs and the expanded NPC index route in both NPC overlays.
Preserve original special-character records and test IDs. Continue names,
catchphrases, personalities/defaults, houses, move-in selection, conversations,
mail, departure, and persistence to finish the ordinary-villager pilot. The
furniture pilot, bulk imports, browser composition/selections, and e/e+ work
remain in the active queue.
