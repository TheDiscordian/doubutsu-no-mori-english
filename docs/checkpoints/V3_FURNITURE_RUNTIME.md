# V3 furniture loader checkpoint

## Completed batch

The two converted static furniture pilots are installed with stable identities,
bounded resident profiles, expanded native profile/bank readers, and model DMA.
Native original profile allocation, model loading, shared ownership, and cleanup
remain in use. The [specification](../../specs/V3_FURNITURE_RUNTIME.md) records
the exact table, relocation, RAM, and ROM-tail design.

No furniture is offered as selectable or playable yet. Shared item readers,
ordinary acquisition/placement, appearance/collision, and saved-item/profile
integration remain work. The public and local V2 patchers are unchanged.

## Construction

```sh
python3 tools/v3_asset_loader.py --furniture --output build/v3-furniture-loader-03
python3 -m unittest tests.test_v3_furniture_runtime -v
```

The combined cartridge is
`build/v3-furniture-loader-03/animal-forest-v3-asset-loader.z64`, 32 MiB, SHA-256
`d15880f8879828964b27cbaba0246b5b2a8a212b4d551a3b0d17a4cc913331ff`.
Its `build.json` records all source/compiler/resource hashes and explicit
not-playable status; `asset-loader.ups` reconstructs the current output from the
verified original N64 ROM. ROMs, assets, patches, and reports remain ignored.

Two earlier guarded construction attempts produced no cartridge. The first
identified the already-installed V2 English name edits in the room owner; the
patcher now binds that exact owner and preserves both edits. The second found
the native DMA directory full. The installed models use the existing V3 file's
ROM-only tail, with no extra rows and no additional resident RAM. Those logs
remain in the ignored build directory; neither native source limits nor hash
checks were disabled.

All **five focused tests pass**, with no skipped local tests. Sanitizers cover
helper bounds, selection, bank ownership, failed transfers, and ABI-5 startup
rejection. Cartridge checks cover two modeled live relocations, retained name
patches, full composition, UPS reconstruction, and exact import-free V2 output.
Unchanged older-build tests are not replayed.

## Native check

```sh
python3 tools/emulator_smoke.py \
  --rom build/v3-furniture-loader-03/animal-forest-v3-asset-loader.z64 \
  --output build/v3-furniture-native-01 \
  --scenario tests/scenarios/v3_furniture.json --expansion-pak \
  --no-initial-screenshot --seconds 150 \
  --xvfb /home/discordian/Games/OpenRSC/headless/vendor/usr/bin/Xvfb
```

The first native attempt passes **86 recorded steps**, including:

- Complete resident prefix and real native-relocated room overlay/BSS.
- Both model loads through the ordinary native bank selector, with every asset
  byte checked and unused bank padding unchanged.
- Both index/rotation mappings, unavailable IDs, bank limits, occupied-bank and
  free-bank scans, existing-bank re-DMA, and native last-user bank release.
- Original furniture index zero's real native profile allocation/relocation and
  complete model transfer through the retained native function bodies.
- Native destruction frees the original profile and preserves the imported
  resident profiles; bank reset restores the complete startup resident prefix.
- Allocation, bank, stack, and translation guards remain intact; no faulted
  thread is present. Checkpoint restore and resumed execution pass.

The fixture is written and run within the 30-minute harness budget, with no
setup retry needed. It uses private Xvfb, disabled audio, an isolated blank save
directory, and no game save/Controller Pak write calls. Emulator-created blank
storage files stay inside that directory; existing saves are never opened.

The fixture does **not** construct a placed furniture actor or render a room.
Ordinary appearance, collision, pickup, acquisition, house visits, save cycles,
and hardware tests remain unclaimed. There is no V3 playtest handoff in this batch.

## Next work

Connect the stable item identities to shared classification/name/value readers,
inventory and placement paths, and safe saved-item/profile handling. Complete
one furniture pilot through ordinary gameplay before batching further furniture.
Cheri's house depends on these models; Punchy's speed bag still requires its
actual animation/interaction port, and his shirt needs additive artwork.
