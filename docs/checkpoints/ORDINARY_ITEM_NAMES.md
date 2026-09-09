# Ordinary item-name checkpoint

## Installed scope

The complete ROM at `build/ordinary-items-pilot/animal-forest-halfwidth.z64`
installs 209 additional complete English names across ten ordinary item families.
All earlier 13,393 ordinary candidates and 2,783 wider names retain their exact
contents and provenance. Fifty new names also fit ten-byte native storage,
giving 13,443 ordinary edits and 2,992 wider slots. Item-only totals are 839
ordinary slots/302 reference identities and 2,992 wider slots/1,050 references.

The [specification](../../specs/ORDINARY_ITEM_NAMES.md) records the complete
selection, displaced song/month/seed identities, capacity boundaries, and
remaining accents/native-specific/design work. No name is shortened to fit.

Only DMA resources `010F4000` and `02A00000` differ from the complete quest-reply
ROM. Every other text, runtime, letter, actor, font, and configuration payload
is unchanged. Input ROMs, extracted references, generated names, and ROM/UPS
outputs stay ignored. The UPS reconstructs the full output from the original ROM.

## Validation

`build/ordinary-items-tests.log` passes all 38 tests in 23.468 seconds. The checks
cover all new source/reference identities, both capacities, every previous edit,
exact installed full/short names, all unchanged DMA files, UPS reconstruction,
all native item IDs through the portable loader, resource rejection, five item
fields, and the reproducible 392-call/384-memory-assertion scenario. The combined
counter retains its denominator and all earlier credit. The already-Latin native
`GB` name does not add Japanese-source translation credit.

Two initial resource-test fixtures require updates: the fishing-rod fixture must
include its newly explicit approved reference ID, and module-dependent tests
must select `AF_TEST_RUNTIME_MODULE=build/shop-notice-runtime`. Both corrected
checks pass without changing production guards. Two additional historical
floor/wall artifact tests reject their older creator-source hashes under the
current verifier; those older ROMs are not rebuilt. Current-ROM tests check
retention of every earlier name and resource. No all-project regression claim
is made from this focused batch.

The assigned silent cartridge batch is `build/smoke-ordinary-items-01`. It uses
the complete ordinary-name ROM, the existing silent boot, and
`build/ordinary-items-scenario.json`, with a 900-second bound. Collect its
terminal result before claiming native acceptance; do not restart an unobserved
live process. No audio, screenshots, user save seeds, or game-save writes are
enabled. Normal name display, wider callers, saving, and hardware remain.

## Artifact hashes

- ROM: `617d03f851ec74994d6840e632b85ebe6e6eb8869c8f58ebe18cf6cf062a2fd5`.
- UPS: `8f840c0d4861cde47ddfa062947079f8d7d3afc1de39da9ee560ae301fa2dadd`.
- Wider resource: `96a9869e2850696ad7ca027967be7383e6ac7bb1015bbd4bf16690e57b05c5a7`.
- Ordinary candidates: `9e0eddce8a9d63030b22837d7790cd0e206643a822ba3475211c33b294d8a437`.
- Native scenario: `0724570c2a68328abd671e594e8f865e67dfef165b9f588f0a0569a64506155e`.

## Reproduction and continuation

Use the complete [floor/wall candidate recipe](FLOOR_WALL_NAMES.md), selecting
`--runtime-module build/shop-notice-runtime`, output
`build/ordinary-items-candidates`, and the current unchanged mail font. Generate
the wider resource with `tools/extended_items.py`, output
`build/ordinary-items-resource`. Preserve the complete
[quest-reply ROM recipe](QUEST_REPLY_LETTERS.md), changing only those two content
paths and output `build/ordinary-items-pilot`.

Generate the exact combined native batch with:

```sh
python3 tools/ordinary_item_scenario.py --output build/ordinary-items-scenario.json
```

Continue full-name display/insertion callers, accented and native-specific names,
noticeboard/general text, review, normal gameplay/save/travel acceptance,
patch-only release preparation, and the title/keyboard stretch goals. The native
K.K. song-title setter at `80AA4794..80AA47E8` still creates a ten-byte local;
the existing complete item-ID wrapper can replace that path without resident
growth. Song-request input remains a different ten-byte saved-event/editor path.
