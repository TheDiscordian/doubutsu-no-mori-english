# Native-specific item-name checkpoint

## Installed scope

`build/native-items-pilot/animal-forest-halfwidth.z64` includes 22 source-bound
original name entries covering 63 wide fields, including two converted clothing
aliases. Thirty-one fields also fit original ten-byte storage. All earlier
13,567 ordinary edits and 3,500 wider item fields remain exact; the complete
totals are 13,598 ordinary edits and 3,563 wider fields. Only DMA files `010F4000`
and `02A00000` change relative to the complete gyroid-name ROM. Runtime code,
letter data, actors, fonts, saved structures, and memory layout do not change.

The [specification](../../specs/NATIVE_ITEM_NAMES.md) describes the source-bound
original-name path, honest project-authored provenance, complete wording,
unchanged capacities, and inferred native aliases. It covers unused furniture,
N64-specific shirt designs and console labels, native quest objects, yellow
cosmos, and the empty-slot label. Donor and original approvals cannot overlap.
No GameCube source is invented for these translations.

## Verified checks

The four initial schema/retail checks pass in 1.966 seconds. The wider
`build/native-item-names-regressions.log` run has sixty selected tests: 58 pass
in 41.175 seconds, with the two current-artifact checks skipped because the full
ROM build is still running when that process imports its tests. Those two checks
subsequently pass separately in `build/native-item-names-artifact-tests.log`
in 16.823 seconds. All sixty selected checks therefore have passing results.

Coverage includes every original source/name/rotation/alias, both capacities,
malformed approvals, changed provenance and self-reported hashes, removed
metadata, altered alias conversion, and shortening rejection in both builders.
Complete-ROM tests reconstruct the resource and UPS, retain every earlier edit
and non-item file, and credit exactly these 63 original IDs without changing the
combined denominator. Earlier ordinary-name, gyroid, and song native evidence
is checked without replaying those batches. No full-project regression claim
follows from these focused checks.

The completed silent native batch `build/smoke-native-items-01` passes all
143 calls and 135 assertions in 429 records. Every planned call argument,
return expectation, full output buffer, stack/adjacent/module guard, and final
checkpoint check passes. All 22 original identities and 31 original-width
fields are included, along with the shared loader boundaries and failure cases.
Isolated FlashRAM and Pak retain blank contents, and shutdown is graceful.
The run has a 600-second bound, with audio, screenshots, user save seeds, and
game-save writes disabled. The frozen result test checks the complete plan
without replaying it. Normal display, saving, and hardware remain unverified.

## Artifacts

- ROM: `acac5a494b961425839e5d978d9b3f7e95985abe67fe0f894b36ea46bc11be8b`.
- UPS: `daac045977d67ba3c93c0c0d4832490a2e78c8f45c3cc3431f7af5125f4b9d98`.
- Wider resource: `69e7bf2e099e652463deecd3a1416f09774c9b4b4810bfc3cfd104956eff4add`.
- Ordinary candidates: `dca244a0f3652cc4942c4a9f2b79d9c68ea738886ff86ccef8dbd920c3e139f7`.
- Native scenario: `30122819528a33eb0c78859ec612fca8ea19a4b62bd9d17a385a8c8aee718a16`.
- Native results: `c583f9dbeddf423a8bf273aac736c24cb23c8303023ef469658ce07d1b47347d`.
- Restored checkpoint: `831660324d826efedfbf13789122d18e3fd376b7e214684829df75c94ddd814f`.

## Reproduction and continuation

Use the complete [gyroid-name recipe](GYROID_ITEM_NAMES.md), changing only the
candidate/resource/output paths to `build/native-items-candidates`,
`build/native-items-resource`, and `build/native-items-pilot`. The generators
load the versioned original-name registry by default. Generate the native batch:

```sh
python3 tools/native_item_scenario.py --output build/native-items-scenario.json
```

Continue remaining supplied-name identities, numbered shirts, accented names,
full-width inventory/catalogue/other destinations, noticeboard and general text,
review, ordinary save/travel/gameplay acceptance, patch-only release preparation,
title-first artwork, and GameCube-style keyboard work. Original-hardware
compatibility requires actual hardware evidence. The full project remains active.
