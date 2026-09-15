# Camping actor assets and four-cell reader checkpoint

## Completed work

The three callback-owned camping objects convert completely: campfire, bonfire,
and tent model. Complete meshes, all palettes/textures, two-texture flame
materials, full fire rigs, dynamic segment dependencies, and both tent-light
palette endpoints are retained. Source callback, identity, acquisition, and
metadata checks are executable rather than inferred from the object names.

The shared native item-reader source supports the bonfire's four-cell footprint
behind an explicit new compile flag. The original ROM and donor tables agree;
the native compile fits the existing resident code reservation.

**No new cartridge or selectable actor is claimed.** ABI 68 remains the current
56-option experimental integration. These three complete assets await their
native callbacks and subsequent cartridge/composer integration. Neither served
patcher, the stable V2 cartridge, main, nor Pages changes.

## Local artifacts

All generated binary content remains in ignored `build/` directories.

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| `build/v3-camping-actor-art-01/campfire.n64obj.bin` | 8,000 | `c9904baeaf1fcaf903daa9cf14cfeecf5a43d355446d8c49f1206f6ff4b0bf2c` |
| `build/v3-camping-actor-art-01/bonfire.n64obj.bin` | 6,032 | `aed67322525e5ece8e17c5be59986a82d1269e4d8421f8985adde0128cd6cfb7` |
| `build/v3-camping-actor-art-01/tent-model.n64obj.bin` | 4,288 | `b56aeeb6e542e9742706ca510e054fdb81f87a82e91b9ff684ed669d32c14af7` |
| `build/v3-camping-actor-art-01/art.json` | — | `f94d22e36cf9b774ae892a9e3492e3bda44267c8e35d043f62d053157b92ece9` |
| `build/v3-four-cell-items-01/items/code.bin` | 1,020 | `baf6957601fea4fc0829382bbc21604ade478479e9f0f6375c6e4d49e2f0317d` |
| `build/v3-four-cell-items-01/items.json` | — | `05b6156848c88706f5be2d3ab0ca90f65a342a3892b01d298a01629912539cc1` |

Total assets: 18,320 bytes, 376 vertices, 203 triangles, 12,032 texels, and
112 palette entries. No object exceeds its current 9,216-byte native bank.

## Verification

Twenty-one focused checks pass across the completed runs:

- Seven complete camping-actor conversion/source tests: every texel, palette
  entry, and vertex; compiled face/texture/state/pointer bounds; both TMEM
  allocations and shifts; full rigs and null tracks; all tent parts and light
  endpoints; real gameplay metadata; rejected unreviewed dependencies.
- Five strict shared-parser/profile tests, three synthetic speed-bag conversion
  tests, and the shared two-coordinate water-material test.
- Three four-cell tests: actual original/donor table and selector, current-code
  preservation, compiled entry/reservation checks, and ASan/UBSan execution of
  the shared item and sparse-profile readers. The C test covers six identities,
  all four rotations, five anchors including signed limits, eight rejection
  conditions per identity, write guards, and native fallbacks.
- Two focused existing multi-cell reader tests retain one/two-cell behaviour
  and all three clothing records without the new four-cell flag.

The first host C test compilation rejected fixed-width string initialisers under
the installed GCC warning policy. The fixture now copies exactly 16 name bytes
from separately terminated strings; the corrected sanitised execution passes.
There was no native emulator run or new native harness construction in this
batch. GPU appearance, callbacks, acquisition, and persistence are not verified
by these host checks.

## Resume details

Use the [camping actor specification](../../specs/V3_CAMPING_ACTORS.md), current
ABI 68 report in `build/v3-camping-runtime-01/build.json`, and full cartridge:
`build/v3-camping-runtime-01/animal-forest-v3-asset-loader.z64`, SHA-256
`3967dedabca6e65a97f57273028aaa19b0b24ed72b405f2498d5a4fce6a1cd29`.

Compiled four-cell entry points:
name `80483000`, type `804831A0`, size `80483204`, placement `8048324C`,
price `80483390`. Rebind all five bridge targets during installation, rather
than relying on unchanged placement/name offsets. Nothing past `804833FC` is
occupied by this new helper, but other callback reservations must be checked
against the actual package before reuse.

Native segmented object offsets:

| Object | Models | Animation / joints / skeleton |
| --- | --- | --- |
| campfire | body `1360`, flame `1E20` | `1F00` / `1F14` / `1F38` |
| bonfire | body `1070`, flame `1660` | `1748` / `175C` / `1780` |
| tent model | green `C50`, body `D18`, detail `E00`, light `FF0` | none |

Tent on/off palettes are at offsets `20`/`40`, each 32 bytes; the static palette
at offset zero equals the off endpoint. Fires require segment 9 scrolling and
a camera-facing flame, not only their rig. Native sound IDs remain unmapped.
The tent's native private-state location must be established; its GC palette
pointer and float offsets lie outside the 0x740-byte native actor.

ABI 68 leaves 1,714,240 bytes before the English choice bank at `025F0000`.
The current resident package, model pool, 3,389-entry DMA directory, save codec,
and both patcher deployments remain unchanged. Native setup remains limited to
the initial attempt plus one justified retry and the documented harness budget.
