# Construction furniture conversion and gameplay-data preparation

## Completed

Seven complete opaque-only furniture models and their source-verified
names/prices, ordinary stock membership, placement shape, HRA properties, and
feng shui colours are prepared. The shared shop/scoring builders accept the
reviewed rows and retain the existing native and imported rows in combined
table-generation checks. Runtime installation remains the next implementation
step; no new playable cartridge or served option is claimed.

Specification: [V3 construction furniture](../../specs/V3_CONSTRUCTION_ITEMS.md).

## Local artifacts and source identity

- Art directory: `build/v3-construction-art-02/`.
- Art report SHA-256:
  `d2ca46dd3dff8dde4243a69c5e0fc44df66a27df3caf396681ddf58dc4311197`.
- Item metadata: `build/v3-construction-items-01/items.bin`, 224 bytes,
  SHA-256 `d6fe8cfc6bf84f1e179d5e24c428757b576c44c658cbafa721c02c0ecf63b98d`.
- Item report SHA-256:
  `0d788fa813d7d768280920f78555770f709377d0b98f3f4338511d02ada03a7b`.
- Actual donor REL SHA-256:
  `29306a927eee861b073c571408393f99cb384048684eee4bff3d219725429837`.
- Pinned donor symbols SHA-256:
  `e5267b989d235655c51885bd2a660b3e8c2cbd46d60b2b3c46166d337c7bca87`.
- Cached identity sheet SHA-256:
  `7fcfb2d7ac3c30c3c69650ed61ae253c9589be0fba4b3aff09a334770da32be0`.
  Rows 2538, 2539, 2540, 2544, 2546, 2547, and 2552 have no native AF ID/name/
  indoor-image mapping. No linked images or sheet instructions were fetched.

The source paths and Docker image remain those of the pinned import project.
Generated donor assets, metadata binaries, and reports stay ignored. Only source,
synthetic tests, hashes, and documentation belong in GitHub.

| Object | SHA-256 |
| --- | --- |
| wet roadway sign | `55c284543312f844d820236027758581dfdabae9e442616421f54eae21502302` |
| detour sign | `343624b73303f2dd233c882d9e4998a290a456ff404f79a5913a0d296db74067` |
| men at work sign | `3ace8867f47858ab35b3681928052b2f469003d88fa7b3aeb444d12691acc79e` |
| flagman sign | `a3b9d4cd2a8e17a49540097cd654ac48cdfdf637eb4e428af6e15745b353f982` |
| jersey barrier | `0d2ccfa8a6e139d90e7e168efa06b22eadfd8e9690e9ffdf9417a4741b090bb7` |
| speed sign | `b7ad346de5839811f5c68ef61e25d884f50e574632f892af01f0e218d2d9f99d` |
| saw horse | `6e7172d2bdacabfac7a06b6a4507466f04d5422ad9c6d3fd5daa7ae3feb02e32` |

## Focused verification

Risk: silent geometry/material loss, missing opaque-only profiles, incorrect
shop grouping/scoring bits, and damage to the default two-object converter.
Scope: source and compiled-asset checks plus combined table generation. No
emulator navigation or old-candidate replay is needed for uninstalled assets.

- Five construction-art tests pass in 4.861 seconds. They compare every texel,
  palette entry, vertex field, and triangle, decode all native display lists,
  verify material boundaries and mirrored tile fields, check exact profile
  layers and buffer bounds, and reject unsupported state.
- Seven shared static-art checks pass in 1.860 seconds. The default two objects
  retain their complete verified output; default parsing remains strict.
- Three item/stock/rejection tests pass on their initial run. The scoring test's
  guessed expected group count of 26 fails against the actual count of 28;
  direct native-table inspection establishes 19 original + 2 existing + 7 new.
  The corrected scoring test alone passes in 1.299 seconds. No passing cases are
  replayed for that expectation correction.
- Combined generated scoring tables change only the seven selected rows;
  native rows and the existing barrel/drum/speed-bag rows are retained. All ten
  ordinary stock additions preserve every original list and remain independent
  of selection order. Duplicate, mismatched, and unknown identities fail closed.

The initial partial art directory `build/v3-construction-art-01/` stops at the
jersey barrier's unsupported explicit tile extent. The completed `-02` build
implements and verifies that required donor operation; it does not omit it.
Neither build runs a game or demonstrates a game crash.

## Next implementation and unchanged boundaries

Install a scalable static-item table, fixed registry/ROM rows, names/price
readers, and selected shop/scoring/profile data for all seven together. Connect
the local optional composer only after those actual runtime records exist.
Keep source identities stable, preserve original saves, and retain the separate
V3 gameplay/persistence issues already tracked in the active queue.

The ABI 60 cartridge and current optional profiles remain unchanged. There is no
save-format change in this batch. V3 stays on its GitHub development branch;
both web patchers remain V2 pending the user's testing and explicit approval.
