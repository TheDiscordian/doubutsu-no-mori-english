# V3 campsite scenery checkpoint

## Result

Complete native assets for the summer-camper tent exterior, projected shadow,
interior, and separate scene lantern are built in `build/v3-campsite-art-01/`.
They retain 30,880 total bytes, all 527 vertices, 369 triangles, 36,416 texels,
and 128 palette entries. The actual projected-shadow flags and descriptor are
checked. Both dynamic segment-8 bindings remain explicit requirements for the
runtime owner. The [specification](../../specs/V3_CAMPSITE.md) records the exact
materials and missing scene/event/conversation dependencies.

This is an asset milestone, not an installed scene or playable acquisition
route. The current full cartridge remains
`build/v3-fire-runtime-02/animal-forest-v3-asset-loader.z64`, SHA-256
`e2a8ddfb41b7ad7d111cf666dc4b4706046d6edff1fe88968e925603a9345ad5`.
Its 59 offline experimental options, ABI 70, saved format 2, and all allocations
remain unchanged. Neither local nor public patcher changes.

## Artifacts

| File under `build/v3-campsite-art-01/` | Bytes | SHA-256 |
| --- | ---: | --- |
| `exterior.n64scene.bin` | 6,960 | `6b44fc60069c6909a637a078cb5a463a4056e7d3fd99ca5a2921a883623226bd` |
| `shadow.n64scene.bin` | 800 | `1961620809af4849ae7301e56015ff59571d36ee491961c8a7af82c5919f9a5a` |
| `interior.n64scene.bin` | 19,872 | `34211a356606d7adbf01ef655c847d067bbf9c6e0ee1a146738bf279a15400ce` |
| `lantern.n64scene.bin` | 3,248 | `7b920ca7cd74f94554dfd322c2c8af8cc95ea28c4591debf2d8804579b8739dd` |

Report `art.json` SHA-256:
`e34166e906e8ba9edc35a14468a473222adb9005844b4a6988e012255fe30529`.
Source and compiler identities are included in that report. Inputs are the
supplied GAFE01-r0 disc, pinned decoded REL/symbols, and the existing Docker
MIPS image. Generated assets and command sources remain ignored local files.

## Executed checks

Build:

```sh
python3 tools/v3_campsite_art.py --output build/v3-campsite-art-01
```

Focused verification:

```sh
python3 -m unittest tests.test_v3_campsite_art -v
```

All five tests pass in 2.144 seconds on the initial test run. They check complete
resource preservation and deterministic hashes, every converted face and
pointer, native material/colour state, the CI4-to-I4 LUT switch, both lantern
tiles/palette banks/TMEM allocations, dynamic window/projected-vertex bindings,
the genuinely empty room translucent list, and rejection of wrong sources or
missing references. No historical cartridge tests or emulator runs are repeated.
New test construction remains within the 30-minute batch budget.

No runtime scene draw, GPU appearance, ordinary camper conversation/reward,
entry/exit, persistence, or hardware behaviour is verified by these asset tests.
The interior is 19,872 bytes and must not be loaded into the smaller furniture
bank; scene storage/loader integration remains explicit work.

## Corrected continuation

The earlier speculative lantern/sleeping-bag behaviour TODO is removed after
checking the actual donor profiles and their generic consumers. Collectible
lantern `iam_tak_tent_lamp` at `.data:926FC` resolves only to
`obj_tent_lamp_offT_model` at `AAC740`. Sleeping bag `iam_ike_tent_sleepbag01` at
`.data:92AD0` resolves only to its model at `84E8D0`. Both 52-byte donor profiles
have null callbacks and zero contact/interaction fields. Current native profile
scalar fields match. The generic furniture consumers use those flags for light
switches and beds; neither collectible asks for those actions. The animated
`ef_tent_lamp` is instead the scene lantern converted in this batch.

Continue the actual campsite scene/exterior/event adapter, English camper
conversation and enabled reward routing, and ordinary gameplay/persistence.
Then continue the other requested V3 imports and browser composition. Do not
mark the full V3 goal complete at this asset milestone. V3 source can be pushed
on `v3/optional-imports`; both served patchers remain V2 until user testing and
explicit approval. No save-format or cross-build compatibility claim changes.
