# V3 HRA checkpoint

The [HRA adapter](../../specs/V3_HRA.md) connects the two static furniture pilots
to native evaluation, construction-theme completion, and missing-item selection.
Current cartridge: `build/v3-hra-03/animal-forest-v3-asset-loader.z64`.

- ROM SHA-256: `fb4f0a00f366e5d6c0d71513552fc66d503a39d1a55290653eb185ebaf541df4`.
- UPS SHA-256: `91fec2b373e4af4d2ed64021c01c3affa0ff1e0493380b298d8b2290e960910f`.
- Expanded owner: 27,152 bytes, SHA-256 `50522ec7cb3256ba18a790634748757944f2ef5b19bc64fcf6a943dbe773104f`.
- Relocation: 1,184 bytes, SHA-256 `45856f506a3890f715e5a4fe622445bb37042c176cc7e9c13d852edd4adffa56`.
- Suffix: 10,176 bytes, SHA-256 `4ceaaf6ccc9e293ff35079c62f443fdf0fac4a9cb26e6574c7e3e0aab10dfe04`.
- Converted metadata SHA-256: `eb75912781d7525ebc330dae67f01874f6e8af56fc448b585711afa5f59f6b50`.
- ABI 19; no extra permanent memory, DMA-directory entry, or saved field.

```sh
python3 tools/v3_asset_loader.py --hra --output build/v3-hra-03
python3 -m unittest discover -s tests -p test_v3_hra.py -v
python3 tools/emulator_smoke.py \
  --rom build/v3-hra-03/animal-forest-v3-asset-loader.z64 \
  --output build/v3-hra-native-03 \
  --scenario tests/scenarios/v3_hra_scoring.json --expansion-pak \
  --no-initial-screenshot --seconds 120 \
  --xvfb /home/discordian/Games/OpenRSC/headless/vendor/usr/bin/Xvfb
```

## Executed evidence

Three focused tests pass on the current cartridge. They check actual donor
conversion for empty, each single-item, both-item, and reversed selections;
all retained native metadata; exact changed code and scheduler words;
complete retained English score wrapper; zeroed original BSS; unchanged DMA
indices/adjacency; rejected source/selection/relocation changes; complete
composition/UPS reconstruction; and exact import-free V2.

The initial native check, `build/v3-hra-native-01`, records 86 passing full-register
windows over all forty detours. These cover original furniture, both selected
imports, and representative disabled/unknown/below-bound cases, including lower
register aliases, branch-likely delay effects, full integer/floating registers,
HI/LO, and return/stack state. All expanded metadata assignment, series counts,
and mixed-layer completion masks also pass. Its missing-item tail fails because
the new C caller passes an item ID to the shared runtime-index predicate.
This is an implementation defect, not a harness failure. The caller is fixed.

An independent source review also identifies GC's extra birth-category bit.
The converter repacks birth and surface fields into the native layout rather
than copying the donor record unchanged. The targeted corrected native run at
`build/v3-hra-native-02` passes all five missing-item selections and both complete
base-point calculations, without replaying the passing register-window prefix.

The final native run at `build/v3-hra-native-03` adds a source-identified boundary
safeguard: the original upper bound admits marker `1ECC`, just past the real
947-row table. An inert OTHER/unobtainable row prevents that marker from writing
past the 55-series completion buffer. It remains neither collectible nor scored.
The final run records **46 steps, thirteen native calls, and 25 passing assertions**:

- Actual native DMA/relocation of the complete moved owner matches the independent
  model, including the cleared original BSS area.
- Native initialization assigns all 1,267 metadata rows and all 55 series counts
  correctly, with 21 construction groups and the complete mixed-layer mask.
- Five native missing-item selections return haz-mat barrel, oil drum, the first
  native construction item, no match, and no disabled-oil match as expected.
- Three complete native base-point calculations retain the empty-room wall/floor
  baseline, add the actual imported/native acquisition weights, and leave the
  one-past marker at zero points. The marker adds no series-completion bit.
- Native/compiled code, the resident prefix, fixture/stack/translation guards,
  and fault pointer pass. The live owner pointer is restored, the fixture freed,
  and checkpoint restoration and graceful exit pass.

The final C entry is eight bytes shorter, moving the appended detours without
changing their compiled 4,880-byte contents. Their complete contents compare
equal to the initial passing native window batch at the respective symbol
offsets. Current owner relocation and full native scoring execute the moved
targets; the unchanged window semantics are retained evidence, not a new replay.
Harness construction/debugging stays within thirty minutes. No setup retry or
old-candidate execution is used; subsequent runs target actual code/data fixes.

## Limits and next work

No physical audio, original-hardware run, user-save write, FlashRAM/Pak write,
ordinary house evaluation/mail delivery, or placement/pickup cycle is performed.
The on-demand image now requests 10,176 more bytes; ordinary gameplay allocation
remains to be checked in the combined lifecycle test. Earlier English-mail,
shop, catalogue, and persistence evidence applies to their unchanged code.

Next: the separate native feng shui evaluator, then ordinary acquisition/payment,
placement/pickup/persistence and villager houses/selection. Controller Pak profile
transport and the broader donor catalogue remain work. V3 development may be
pushed to GitHub; both web patchers remain V2 pending user testing and approval.
