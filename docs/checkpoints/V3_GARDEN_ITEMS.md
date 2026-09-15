# Six garden decorations: source conversion

## Completed work

All six complete models and their donor gameplay metadata are converted and
validated. Exact identity/profile/name bindings, special acquisition routes,
non-power-of-two texture heights, mirrors, face/lucky/surface flags, and feng
shui penalties are retained. No import is installed or enabled by this batch.
The [specification](../../specs/V3_GARDEN_ITEMS.md) records runtime requirements.

Artifacts:

- `build/v3-garden-art-01/art.json`, SHA-256
  `07c873050eed3cc1e4a60ba5142eaa54d9e6c38fb934fa44b7492adfee4be917`.
- `build/v3-garden-items-01/items.json`, SHA-256
  `d690e700f7312a895b457f42651cace6b3a895eb5c8a2d9cfd5290938de2ff9c`.
- Six 32-byte prepared item records, SHA-256
  `70c5bff1b773663f15be5d8f50f74e7149a3ebb6075d873daad99467396a6e84`.

| Object | SHA-256 |
| --- | --- |
| birdhouse | `39638d65b0e4879e86dfed67bbe9db39a378b1db1b375bd4b91ab3acabee78f1` |
| bird feeder | `cab7148b304081f02d313817fa6ffd9c92932bcd9a0460e86c735045eaafc67d` |
| Mr. Flamingo | `800504a52e055a6a921f184f1615b03d69704caa9475d1c0776d52a3c29ec828` |
| mailbox | `a8c552e2edd1a7cd7b2633a1eab096852d50f783c70c6156711d269049f08398` |
| garden gnome | `5bc33d163176bdf5f8c7aa878413d8685ea6ae57918c46185be18a6981e192d2` |
| Mrs. Flamingo | `ef64366aa6428a6adbfc75b2ee2b56a552cd5537c02558d1d2249bc789e1cee2` |

## Checks

Six focused new checks pass: four garden-art checks and two metadata checks.
The actual compiled objects preserve every pixel, palette entry, vertex, triangle,
material state, and native texture/load bound. Native tile descriptors retain
all eight non-power-of-two axis uses and the birdhouse's standalone material
update. All objects fit 4-KiB slots and existing 5,120-byte model banks.

Ten shared synthetic parser/profile checks pass for unchanged static,
construction, speed-bag, and accessory modes. The initial invocation has two
module-import setup errors; one correction imports the new fixture through the
test package and supplies the existing tests directory for the historical
construction fixture. Only the previously unexecuted checks are retried.
The corrected six-check art/construction run passes in 4.851 seconds; the separate
two-check metadata run passes in 3.777 seconds. No native scenario or old gameplay
build is replayed for this source-only batch.

Native HRA backyard-series installation and mailbox category 19 are deliberately
pending. Ordinary lottery/post-office acquisition is not replaced by shop stock.
No cartridge, save, ROM directory, or web recipe changes; neither served patcher
changes. The current full ROM remains the aloha-corrected ABI-62 integration.
