# Seven Western furnishings: source conversion

## Completed batch

Seven complete objects and their gameplay metadata are converted and verified.
The [specification](../../specs/V3_WESTERN_ITEMS.md) records identities, graphics,
acquisition, scoring, and the remaining capacity/runtime work. Both saddle-fence
opaque parts and the well's three double-mirrored materials are retained. No
ROM, save, installed item, composer profile, or served patcher changes.

Artifacts:

- `build/v3-western-art-01/art.json`, SHA-256
  `ffd098a0bb47a6f759dabdf55983aa71d6d4d7d5c78ce3062c8584d05503b0e6`.
- `build/v3-western-items-01/items.json`, SHA-256
  `56060a69e04d81211ff163b56e46c5206df3be47e0773e6ac2d4827cc6ec0227`.
- Seven prepared 32-byte item records, SHA-256
  `a2b5d07acd0580c431ff7c7b6ccb753a8bf50442375ebae8af16695246f5a2a6`.

| Object | SHA-256 |
| --- | --- |
| tumbleweed | `26d9cc3626020cce04694799a5ee780e0e9cc1be4ea8af32c750f30b3c6b2e94` |
| cow skull | `d373c14b5a24afe7130013c5a66c3827fc5b18f448ddfd81bd267cd9361b5c12` |
| saddle fence | `46edc82db7109e3202ba07d048331e72ac0812cbc18040965d2b9e9db1682ebb` |
| western fence | `c5a93917a460a6acdba32ab3f24b572dba888a9f445b6ebb3faf80f70fb716aa` |
| desert cactus | `f10bba41b5a6409af894f1717f865aebec038ab5ed1af0e2d10861b9d7683430` |
| wagon wheel | `dc196724077633a328183e570711318939ef95ffdcb2e3c86e8403ab92a798cc` |
| well | `bce7d9549cece143b1fc3fbc5f8f3838eb73e7e57b6b9de0e5435259f627af34` |

## Verification

The first focused run passes all twelve checks in 5.857 seconds: four new
Western art checks, two metadata checks, five shared parser/profile checks, and
the shared tall-texture/material-update check. Native compiled command streams
retain all 295 faces in order, every material state and pointer, full vertex
loads, all 23,808 texels, and complete palettes. Independent tile inspection
checks actual compiled masks/wrapping and both opaque profile slots. Malformed
descriptors, unsupported parser-mode combinations, and modified donor inputs
are rejected. The shared pixel fixture now resolves explicit texture-symbol
exceptions while retaining its independent GX addressing comparison.

The seven models occupy 24,192 bytes and retain 463 vertices. The saddle fence
is 5,216 bytes: 96 beyond the currently installed bank capacity. This is a
known installation prerequisite, not a shipped DMA overflow. No native gameplay
scenario or previous cartridge is replayed for this conversion-only batch.

## Next batch

Resolve the actual bank allocations, stride, DMA limits, catalogue preview, and
memory budget, then install the complete Western batch and individual offline
options. Preserve event rewards for saddle fence and well. Keep mailbox banking
and the remaining donor families in the queue; this batch does not complete the
V3 goal or authorise a patcher update.

Current full cartridge remains ABI 64 at
`build/v3-garden-runtime-02/animal-forest-v3-asset-loader.z64`, SHA-256
`436c5cec2aeb1d9f34d1fb71217ec62a6ef232d91573e0112d7055c65345f1d0`.
