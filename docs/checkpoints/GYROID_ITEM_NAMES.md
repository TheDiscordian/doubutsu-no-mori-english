# Gyroid item-name checkpoint

## Installed scope

`build/gyroid-items-pilot/animal-forest-halfwidth.z64` includes all 127 complete
supplied English gyroid names across 508 rotation slots. Thirty-one complete
names also fit the original ten-byte loader, adding 124 native slots. Every
earlier ordinary/wider candidate remains: totals are 13,567 ordinary edits and
3,500 wider item slots. Only item-name DMA files `010F4000` and `02A00000` change
relative to the complete selected-song-title ROM. All letters, runtime, actors,
font, saved layouts, and memory budgets remain unchanged.

The [identity specification](../../specs/GYROID_ITEM_NAMES.md) records bilingual
family/size checks, fourteen independently resolved reference spelling
discrepancies, and the complete-width/remaining-caller boundary. Each approval
binds both supplied game sources. The downloaded corroborating reference is
ignored, and no web request is required to build the translation.

## Verified checks

All 51 tests in `build/gyroid-items-final-tests.log` pass in 39.733 seconds.
The checks cover every name/source/rotation, both capacities, independent
shortening/provenance rejection, all earlier candidates, exact complete ROM
and wider resource, unchanged non-item files, UPS reconstruction, loader and
field regressions, and the frozen ordinary-name/song native evidence. The
combined counter adds exactly these 508 original IDs with no lost earlier
credit and no denominator change. No full-project regression claim follows.

The completed silent native batch is `build/smoke-gyroid-items-01`, running the
complete ROM and `build/gyroid-items-scenario.json` under a 600-second bound.
It selects all 127 wider identities and 124 short rotations, retaining shared
loader boundaries, unaligned output, rejected capacities/headers, disabled
resources, guards, and restored checkpoint. All 344 calls and 336 memory checks
pass in 1,032 records. Every planned call argument, return expectation, full
buffer, guard, and final restored checkpoint agrees with the executed results.
Isolated FlashRAM and Pak retain blank contents, and shutdown is graceful.
Audio, screenshots, user save seeds, and game-save writes are disabled.
The frozen result test checks the complete plan without replaying the batch.

## Artifacts

- ROM: `f92f0d0bbdd514180423d42c53946d12cc5ed38610afe2c914c7d89b2953f561`.
- UPS: `232efbb18aea3b9c3c241e375b72da38dae9fd9ea88a03a43896fb7eeaadf113`.
- Wider resource: `0689a09ebd494c7f1f6ef59be23d85a1538e3dc7ec9d12d6f953f98ddd9760d6`.
- Ordinary candidates: `ce4899d94b969de25fa3c858a91556e5fbf77b8c7f757683d693bb945567275b`.
- Native scenario: `8cae35fe6a7cd9ebc42daa65c179b787649375fbe873b715809b22000df4168c`.
- Native results: `6ab0fcd50499beae61467d43a944f7dc2a8269dc8c199fd4d451dbb9803cf347`.
- Restored checkpoint: `9fddaf7b8734c5f1f0616e75e238e5262d5fdf4ea7910448ff10e4d056a9bbd4`.
- Bilingual HTML snapshot: `7c184bd0d2ddb6207211132100d610deb0616c3e0b754b4dcd3953892746734e`.

## Reproduction and continuation

Use the [ordinary-name candidate recipe](ORDINARY_ITEM_NAMES.md), outputting
`build/gyroid-items-candidates`, and generate `build/gyroid-items-resource`
with `tools/extended_items.py`. Preserve the full
[selected-song ROM recipe](SONG_ITEM_NAMES.md), changing only those two input
paths and output `build/gyroid-items-pilot`. Generate the exact native batch with:

```sh
python3 tools/gyroid_item_scenario.py --output build/gyroid-items-scenario.json
```

Continue remaining item identities/native-specific names, accents, wider
inventory/catalogue/other callers, noticeboard and general text, review, normal
save/travel/gameplay acceptance, patch-only release preparation, title-first
images, and the GameCube-style keyboard. Original-hardware acceptance requires
actual hardware evidence. The complete project remains active.
