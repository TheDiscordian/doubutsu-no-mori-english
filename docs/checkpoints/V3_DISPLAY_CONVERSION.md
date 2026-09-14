# V3 global clothing conversion checkpoint

## Artifact and installed change

`build/v3-display-conversion-01/animal-forest-v3-asset-loader.z64`, ABI 43.

- ROM SHA-256: `ba48944648a10baa0b8f36d6063af36c68bae9dba7a30b118bb2c0c166620436`.
- UPS SHA-256: `4453bd2cab0ca4af7443bae1c583cf5acf649202643b3657e88a161ab1f388ef`.
- Resident prefix SHA-256: `ae79ce7fcfd74b77785369411a638707b18114c2c6513e6370cf178065d16693`.
- Conversion code, 160 bytes: `7e816c74338683f0017f8d97360ca2c7c277c3f6ba445dccff934998582fb8a8`.

The [specification](../../specs/V3_DISPLAY_CONVERSION.md) records forward
`34BF -> 3AFC` and inverse `3AFC..3AFF -> 34BF`, guarded by the complete
selected display profile. Both native conversion bodies are retained through
checked entry bridges. All other item groups keep their original functions.
The first build succeeds with the pinned Docker toolchain. The resident prefix
remains 49,152 bytes, complete DMA resource 65,440 bytes, and RAM requirement
8 MiB. No original asset, save code, profile, scoring image, or heap changes.

## Focused checks

`build/v3-display-conversion-tests-02.log`: two tests pass in 2.623 seconds.

- Sanitized wrappers check every sixteen-bit item with both selection states,
  preserving the original full argument for native fallbacks. Only the selected
  pocket identity and four display aliases are intercepted.
- The cartridge check verifies complete helper code/padding, both entry edits
  and bridges, original native body hashes, complete retained main code outside
  those entries, the entire restored resident prefix, unchanged secondary/save
  code and profile, all other resources, actual startup CRC/ABI, and UPS output.

The initial host check rejected the HRA generated-assembly source hash: its
`.incbin` line contains the new output directory. The corrected comparison
excludes only those path-dependent source hashes for HRA/feng shui and still
compares their complete compiled reports and actual cartridge resources.
No runtime code changes for this test correction; no old ROM is replayed.

## Native combined check

`build/v3-display-conversion-native-01` passes all 157 records on its initial
run using `tests/scenarios/v3_display_conversion.json`. The emulator is silent
and isolated, restores its checkpoint, resumes, and shuts down normally.

- Both actual global entries convert the selected garment correctly, including
  full-width arguments and all four display orientations.
- Native clothes, fish, insects, umbrellas, static furniture, original range
  edges, and invalid/adjacent IDs keep their original results. The native
  overlap at clothing item `24FF` is deliberately preserved, not remapped.
- Removing either the display or garment selection bit rejects both new
  conversions. The complete resident profile/code and secondary resource are
  restored, and stack/translation guards and the fault pointer pass.
- The actual expanded HRA overlay loads and relocates correctly. All 2,051
  assigned metadata rows and native series counts match the independent
  predictor; mixed-layer construction masks and five recommendations pass.
  Seven complete base-point evaluations cover the four mannequin rotations,
  both retained imports, and safe handling of the one-past-native marker.
- The actual expanded feng shui overlay passes nine complete item evaluations
  and three complete room evaluations. The garment has its verified neutral
  donor colour for every orientation, with retained original point rules.

This closes the previously pending scoring tail without replaying the
unchanged HRA register-window suite or earlier item/collection exercises.
It is component execution, not ordinary room placement, catalogue ordering,
save/restart, or original-hardware evidence.

## Ordinary placement check

The current-build copied-town fixture seeds pocket zero with `34BF` and its
ownership using the existing fixture creator. The original save is retained.
`tests/scenarios/v3_display_placement_gameplay.json` uses ordinary controller
inputs to enter the house, select Drop, and pick up the mannequin; it does not
inject a game function or edit live items. The initial
`build/v3-display-placement-gameplay-01` run passes all 22 records and shuts
down normally, with no setup retry:

- The current cartridge cold-boots the copied format-2 town and retains all
  fifteen expected pocket items. The fixture save SHA-256 is
  `85cf01b63dfb0cc8e184329208db56bbb769d7ea22b5da1b681ee60893cb037c`.
- Ordinary controls enter the house at `(120, 40, 220)`, move to placement
  position, open inventory, and select Drop. Pocket zero becomes empty; the
  other fourteen pockets, every condition, and worn native shirt remain intact.
- Runtime display index 1,727 has bank index `01` after placement, proving
  that the imported mannequin loader is active in the ordinary room scene.
- A four-frame B press and ninety subsequent frames return complete item
  `34BF` to its original pocket. The display bank index becomes `FF`, with all
  other pockets, conditions, wallet, debt, and worn clothing unchanged.
- Translation guards and the fault pointer pass before and after pickup.
  The final same-ROM emulator checkpoint is retained for continuation.

No screenshot or visual inspection is performed; this is ordinary room
placement/pickup and model-bank evidence, not an appearance-polish claim.
The source save retains SHA-256
`d489736e39abc7eff1c5b5085bf52e679186f2882a0247339e11603799b80b60`.
A seeded pocket is not a shop purchase, and emulator checkpoints are not
ordinary FlashRAM save/restart evidence. Rotation and placed-save persistence
remain unverified. No physical audio is emitted.

## Compatibility and next work

Complete save code, format 2, selected profile, and runtime layout match ABI 42.
Same-profile forward/backward compatibility is expected, not established by a
new ordinary reload. Older profiles lacking the display bit reject new saves;
V2 and format-1 builds remain incompatible. Preserve existing save backups.

Complete ordinary rotation/persistence and actual clothing catalogue
rows with their preview-specific readers, then remaining acquisition and villager
integration. Both web patchers stay V2 pending user testing and explicit approval.
