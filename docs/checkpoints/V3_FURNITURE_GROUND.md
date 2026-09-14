# V3 furniture ground checkpoint

## Implementation and outputs

The [ground adapter](../../specs/V3_FURNITURE_GROUND.md) connects both reviewed
native drop-flag paths and the complete ground-descriptor selector. The haz-mat
barrel and oil drum retain their full identities and rotations. The 264-byte
helper uses the existing resident reservation; no owner allocation grows.

```sh
python3 tools/v3_asset_loader.py --furniture-ground --output build/v3-furniture-ground-01
python3 -m unittest tests.test_v3_furniture_ground -v
```

All three focused checks pass without skips. The current combined cartridge is
`build/v3-furniture-ground-01/animal-forest-v3-asset-loader.z64`, SHA-256
`ab9a36d11d38e5f8c669b88640552461a0f0722f452a4e15e964ef541d4f9027`.
The adjacent UPS has SHA-256
`a4791b6eea25069059519cdee233c250094f35378769b4127634eafe2ab8ba04`.
The helper SHA-256 is
`1dcf836edcfd8404a24f59c81ecc592f6b915c58fff16e2ec7e62a533c5dd1eb`.
All generated ROMs, patches, extracted data, and compiler reports stay ignored.

## Native verification

```sh
python3 tools/emulator_smoke.py \
  --rom build/v3-furniture-ground-01/animal-forest-v3-asset-loader.z64 \
  --output build/v3-furniture-ground-native-01 \
  --scenario tests/scenarios/v3_furniture_ground.json --expansion-pak \
  --no-initial-screenshot --seconds 150 \
  --xvfb /home/discordian/Games/OpenRSC/headless/vendor/usr/bin/Xvfb
```

The first attempt passes all 57 recorded steps, within the 30-minute harness
allowance and without a setup retry:

- Actual native loading/relocation of the complete current owner and BSS.
- Twelve full-register windows across all three detours, covering original
  furniture, both selected imports, and a disabled oil drum. GPRs, HI/LO, floating-
  point registers, stack restoration, and both branch outcomes pass.
- Six native drop-flag paths produce `0200` for the original control and both
  imports, preserving item IDs. These run through flag selection, not the full
  drop animation or field write.
- Four complete native descriptor calls select the furniture row and drawing
  entry 47 for original/enabled furniture, or the fallback row for a disabled
  import. The 12-byte output and retained padding are checked.
- The complete resident prefix, owner/BSS, input records, stack/allocation/
  translation guards, and faulted-thread checks pass. The original owner pointer
  is restored, the fixture is freed, and checkpoint restore/resumed execution pass.

No ordinary drop/pickup, complete ground graphics submission, save/reload, or
hardware acceptance is claimed. The fixture uses private Xvfb, disabled physical
audio, and blank isolated storage. Existing saves, stable V2, both web patchers,
and the trailer remain untouched. Earlier passing evidence for unchanged helpers
is retained without replaying previous builds.

## Next concrete readers

Two shared pocket queries still compare the raw high nibble to the requested
furniture type: `mPr_GetPossessionItemIdxFGTypeWithCond_cancel` at `800B8128`
(124 bytes), and `mPr_GetPossessionItemSumFGTypeWithCond_cancel` at `800B8544`
(424 bytes). Both inspect 15 halfword pockets at private + `14` and their two-bit
conditions at private + `34`. The sum function is unrolled in the actual binary;
patching only its first type comparison would be incomplete. Preserve other
requested types and null-pointer behaviour when adapting furniture searches.

`mPr_SetItemCollectBit` at `800B88EC` currently ignores type 3. Its actual
furniture bitfield starts at private + `AF0`, not the stale `108` offset comment
in the upstream header. The native bitfield has 30 words; donor indices 1161 and
1198 cannot be written into it. Catalogue support needs properly saved extension
storage and corresponding readers, not an unchecked native bitset index.
