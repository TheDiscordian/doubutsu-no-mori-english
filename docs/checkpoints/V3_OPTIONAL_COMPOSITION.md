# V3 local optional composition

## Implemented scope

The [composition specification](../../specs/V3_OPTIONAL_COMPOSITION.md) and
`tools/v3_optional_composition.py` implement local per-entry selection for all
twenty installed villagers and six logical items. Selection is additive and
uses the existing fixed registry; the three mannequin representations are
automatic shirt dependencies, not independently selectable entries.

The source is pinned ABI 60, SHA-256
`55a715831671c989aa465fbf6d04c49caa975a761105ffa1f3acecd10ac7b8cf`.
The resolver reads actual installed defaults and house-layer contents. Punchy
requires the cherry shirt and speed bag; Cheri requires both barrels; Maelle
requires her red aloha shirt. Every required item appears in the receipt, with
the villager that requires it. Duplicate and reordered selections resolve to
the same profile and ROM. Unconverted identities, standalone mannequins, and
furniture rotation aliases are not accepted as independent selections.

The composer changes only the actual enable flags, metadata presence, saved
profile, prefix CRC, and header checksum. Furniture needs its native enabled
word changed in addition to the save profile; otherwise unselected stock would
remain available. All instructions, assets, fixed IDs, physical file positions,
and allocations remain. Nonempty variants retain the complete resource storage;
no resource-size saving or compact per-selection loader is claimed.

Empty selection returns the exact stable V2-11 cartridge. Selecting every
installed development entry returns the exact full ABI-60 cartridge, with no
changed bytes. This is not a claim that every donor item is implemented.

## Focused verification

Six checks pass in 3.004 seconds. They cover actual dependency derivation,
order/duplicate independence, removal of no-longer-required items, every native
enable field, complete reversal of the declared writes, unchanged file ranges,
preserved demand-loaded resources, prefix/N64 CRCs, rejection of overlapping
or tampered writes, and exact all/empty outputs.

The real format-2 C decoder accepts equal/larger composed profiles and rejects
missing villagers or dependencies with `-7`, leaving the save and output state
unchanged on rejection. This is codec evidence, not ordinary cross-profile
save/restart/reload. Source saves and the stable V2 cartridge remain untouched.

## Current artifact

`build/v3-optional-profile-02/animal-forest-v3-asset-loader.z64` selects Maelle
and Punchy, with the red aloha shirt, cherry shirt, speed bag, and both required
mannequins. It retains 64-MiB ROM and 8-MiB RAM requirements.

- ROM SHA-256: `c5fc510dfe2fb637f674916141ca2d70c1e65a81c42de02db582c4bae0586dbb`.
- UPS SHA-256: `1e63c0843a5ca65382df146db28e3df275cbf2d735f4edaac2e806eda40912d9`.
- Saved-profile SHA-256: `a056114a80c5a10c1509ef8a101c07aebeeb61146085dcc47fc1860e1da5b35a`.

The builder verifies the original Japanese input and full UPS reconstruction
before creating a fresh output directory. The receipt includes the requested
and required identities, fixed destinations, selected save bits, original
converter-source fingerprint, output hashes, and every guarded cartridge write.
The final artifact includes consistent selected/enabled flags in its matching
build report. Its ROM, selected profile, and UPS exactly match the initial
composition used by the native run below; no old game build is replayed.

The first native check, `build/v3-optional-profile-native-01`, passes all
42 records: fifteen explicit memory assertions and nineteen asserted native
function returns. Result SHA-256:
`4972341bf9c7012cb7be1b684a69185157ff7c98600daf67f1c2e12562ea2cab`.
`tests/scenarios/v3_optional_composition.json` verifies startup CRC acceptance,
selected/excluded native item readers, complete six-personality candidate
counts, both selected full names, restored temporary appearance history,
unchanged save state, and final guards. The matching emulator checkpoint is
restored and final fault/translation guards pass before graceful shutdown.
No navigation, ordinary saving, audio, or older-game replay is attempted.

## Remaining scope and compatibility

Neither web patcher changes. Browser conversion/composition and selection UI
remain work and stay unserved until user testing and approval. Unconverted donor
content, complete ordinary villager/item gameplay, and existing unresolved
speech/persistence checks remain required for V3.

Imported saves require V3 with all saved dependencies enabled. Smaller profiles
are rejected, not migrated. Do not load imported saves in V2. Preserve save
backups and keep codec acceptance separate from ordinary loading evidence.
