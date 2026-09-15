# Aloha garment and outfit checkpoint

## Corrected output

ABI 55 installs both actual aloha garments and all eighteen islander outfits.
The complete source and runtime contract is in the
[specification](../../specs/V3_ALOHA_OUTFITS.md).

- ROM: `build/v3-aloha-outfits-03/animal-forest-v3-asset-loader.z64`.
- ROM SHA-256: `53e94b2cfdc960854bb2520e9bc381886e57fb8051f1bf10e34ef8514b76208c`.
- UPS: `build/v3-aloha-outfits-03/asset-loader.ups`.
- UPS SHA-256: `4f592995e45992effa7183c468e404ce816df0394e4d6b818fc9c15ab75dab3a`.
- Full villager metadata SHA-256: `ede1348fa387b0f3104af4e3d18c0ab9af16f0ea67ac0ff5adb78767e6f9ca52`.
- Shared package SHA-256: `53a3a0c31798fdfba6ee07c7bcb2628fdd8b14f1bdae2e83e4f87204a73d9133`.
- Save/item resource SHA-256: `b6ae17a1d2bfa9f5879afa41459e1d490ac4af35e7f0bf769ebdf1472e0a0d18`.

Construction: `python3 tools/v3_aloha_runtime.py --output build/v3-aloha-outfits-03`.
The previous artifacts remain preserved. This is an implementation artifact,
not a complete V3 playtest handoff; move-in flags remain disabled.

## Actual boot defect and correction

The first native attempt on `v3-aloha-outfits-01` stops before fixture execution.
Its faulted thread is `80145630` (graph thread), saved PC `80029AF4`, with the
deliberate DMA-error crash address `11111111`. The separate read-only diagnostic
is retained in `build/v3-aloha-fault-01/results.json`; successful diagnostic
completion is not a passing game boot.

Disassembly identifies a live texture destination in `t1` across the original
lookup calls. The new lookup uses `t1` as its return accumulator, invalidating
the existing compiler's known-callee assumption. Four register-preserving
bridges fix that boundary. Review also identifies two folded single-record
assumptions in the name and price readers; five checked instruction edits fix
those. These are game-code fixes, not relaxed assertions or test workarounds.

The intermediate `-02` link is rejected by the existing space assertion because
the assembler expands 64-bit stores as register-pair macros under its default
register setting. Explicit `.set gp=64` generates the intended N64 instructions.
No `-02` ROM is produced. The corrected `-03` helper is 1,076 bytes and fits the
existing reservation. Tests compare all four complete bridge instruction streams.

## Focused checks

`python3 -m unittest tests.test_v3_aloha_runtime -v` passes all seven tests in
9.549 seconds on the corrected cartridge:

- Complete source-bound garment images, palettes, names, donor prices, fixed
  identities, and all original texture/palette banks.
- Actual three-record shared reader and all twenty complete default initialisers
  under address/undefined-behaviour sanitizers, including malformed/disabled rows.
- Only the eighteen applied-outfit fields change in the villager table.
- Independent per-player clothing ownership and exact profile dependencies,
  using the unchanged format-2 codec and independent reference encoding.
- All four complete 64-bit-preserving bridges and their exact hook targets.
- Name/price fixes, descriptor CRCs, and retention of unrelated instructions/data.
- Physical-file retention, startup bounds, ROM checksum, and UPS reconstruction.

## Combined native verification

The corrected cartridge passes the silent isolated run:

```sh
python3 tools/emulator_smoke.py --rom build/v3-aloha-outfits-03/animal-forest-v3-asset-loader.z64 --output build/v3-aloha-native-03 --xvfb /home/discordian/Games/OpenRSC/headless/vendor/usr/bin/Xvfb --expansion-pak --no-initial-screenshot --scenario tests/v3-aloha-native.json --seconds 240 --port 19386
```

It boots without a fault, loads the complete prefix/shared package/profile, and
executes the real shared DMA and item readers for both aloha garments and the
cherry shirt. The original N64 garment at `1A` remains distinct. Full images,
names, prices (including zero), categories, and checked NPC indices pass.
Maelle, O'Hare, and Punchy pass all three actual native initialisation entries,
with complete 1,344-byte comparisons and retained hometown/phrase/default fields.
Disabling only red preserves blue and cherry, rejects the unavailable name/type,
and prevents partial default writes. Unknown clothing requests preserve output.
All fixture/stack/module guards, immutable code/resources, complete saved state,
restored globals, final fault checks, and checkpoint restoration pass.

Results: `build/v3-aloha-native-03/results.json`, SHA-256
`9a0ca373ae03606fb774a65eee0e04c4f2c9d063f5f185cc2792384a5ff7e7a6`.
The run contains 109 records and 55 passing assertions. It does not claim ordinary shirt acquisition,
GPU appearance, villager arrival, or save/restart/load. No physical audio is
played; the separate new-instrument playback issue is not retried in this batch.

## Next work

Connect aloha display/catalogue/acquisition consumers, islander houses, and
explicit town-compatible behaviour. Retain separate save backups: earlier
profiles missing the new garments reject this build's saves. Ordinary cross-build
loading is not newly verified. Source may be pushed on `v3/optional-imports`;
both web patchers remain V2 pending user testing and explicit approval.
