# V3 campsite scene-loader checkpoint

## Result

ABI 71 installs complete campsite scene/field resources and all four converted
scenery objects. Native scene 35 has a separate descriptor and field row;
original indices 0–34 remain intact. The engine constructs the room's actual
field, collision, foreground exits, and camper placement through its normal
allocation/DMA routines. The full 19,872-byte interior fits its 40,960-byte
background buffer, without using a furniture bank.

The resident package adds 8 KiB, including 580 bytes of scene callbacks and a
4,096-byte checked data packet. Startup checks the expanded CRC and invalidates
the new instruction reservation. Normal heaps and model-bank allocations stay
unchanged. The source/interface/memory contract is in
[V3_CAMPSITE](../../specs/V3_CAMPSITE.md).

The native gameplay overlay and relocation resource retain their VROMs and DMA
slots but move from compressed original storage into the checked import region.
The status-selector hook preserves its arguments; the room-sound switch keeps
the full original mapping and adds the tent. Its replaced local call loses
exactly one obsolete relocation, retaining all other 127 records. The actual
native loader successfully relocates the resulting complete overlay and BSS.

This is installed scene-loading work, not an enterable campsite or a complete
import release. Event/exterior, camper registration, English conversations,
selected rewards, and scene lighting/floor sounds remain required. Neither
local nor public browser patcher changes. Source can be pushed on
`v3/optional-imports`; patcher changes require user testing and explicit approval.

## Artifacts

Full ROM, local only:
`build/v3-campsite-runtime-03/animal-forest-v3-asset-loader.z64`

- ROM SHA-256: `fc8a8682c58f61841f23996bacccf2daa98eefda2c6f9e65aa4e472713834ea9`.
- `asset-loader.ups`: `55b483e228f1a5c2cf8b3567fb09bc92c4a689d97350f18b14f83d719b3b484a`.
- `build.json`: `1295caaa47575b241ce5cbfe5fbb3d9448f6e21af6e970d5ed7171baf256d2d2`.
- Prepared `build/v3-campsite-scene-02/scene.json`:
  `edcb19b571173e8b6f435e46f8d82577a6aa0f0c5a28edc2f9d58aa266ff1818`.
- Resident callbacks: `744685bfa708808c700dabac0fb22ac0a6878766cf8ede0c7020763e03cc1735`.
- Complete packet: `dcc7913fd2d634f1c0424bdcf65df23791321e11564222a4c8165caa53a8e008`.

Ten-item camping subset, local only:
`build/v3-optional-campsite-01/animal-forest-v3-asset-loader.z64`

- ROM: `9a64cc9c3f68142e37d8c57b897d0e9c69c9ba8e4836905eac79f2a6d5a1297c`.
- UPS: `66912edf21364921e57342005ae97366da530498822f59f538c89ddd64ad738e`.
- Build report: `38e6a6c1437d94454ced018b39d70ce0ca1ade4d3580cbb82a58022cfc7b5ec3`.

The offline composer pins the full ABI 71 cartridge and its larger package.
All 59 experimental options remain available individually; all selected returns
the full cartridge, and no selections returns exact stable V2. Selected-only
package CRCs and report hashes stay consistent. Runtime scene data is retained
in nonempty profiles; eventual campsite event activation must test the selected
camping content rather than appearing for unrelated import choices.

## Executed verification

Build commands:

```sh
python3 tools/v3_campsite_scene.py --output build/v3-campsite-scene-02
python3 tools/v3_campsite_runtime.py --output build/v3-campsite-runtime-03
python3 -m unittest tests.test_v3_campsite_runtime tests.test_v3_optional_composition -v
```

All 15 focused/composition tests pass in 10.683 seconds. New C callback/startup
fixtures use AddressSanitizer and UndefinedBehaviorSanitizer. They cover the
complete original scene/acoustic mapping, packet-header rejection, invalid field
inputs, correct native setter arguments, and expanded startup cache maintenance.
Cartridge checks cover full source preservation, exact hook locations, six
changed file owners including the DMA directory, only its three authorised
entry changes, resource moves, complete packet/guards/CRCs, and ROM checksum.
Composition checks retain actual dependencies, fixed identities, selected
catalogue/scoring, exact all/empty output, and current saved codec behaviour.

The initial ROM comparison expected five changed owners but omitted the
directory resource itself. The corrected check verifies its complete contents
after allowing only BLOB, gameplay, and relocation entries. This was an expected
directory update, not an unexplained game-resource difference.

Silent current native test:

```sh
python3 tools/emulator_smoke.py \
  --rom build/v3-campsite-runtime-03/animal-forest-v3-asset-loader.z64 \
  --output build/v3-campsite-native-02 \
  --xvfb /home/discordian/Games/OpenRSC/headless/vendor/usr/bin/Xvfb \
  --expansion-pak --no-initial-screenshot \
  --scenario tests/scenarios/v3_campsite_scene.json --seconds 240 --port 19277
```

The corrected run passes 57 records, 24 actual calls, and 30 explicit assertions.
`results.json` SHA-256:
`c611e6f9ac4e300250d392e309fd6638c945352782dbacdb73106e00ab6bc6fb`.

It executes actual gameplay-overlay relocation, original/new/rejected scene
selection, retained acoustics, and complete `mFM_MakeField(35, A000, 1)`.
The resulting field retains all 256 collision records, all foreground cells and
both exits, the compact camper load row, correct native model bindings, and
ROM range. Actual synchronous DMA loads the entire room model with untouched
allocation padding. Complete resident prefix/package, save runtime, private
allocation guards, and translation guard remain intact. All private allocations
are freed, the saved scene restored, and the complete machine checkpoint
reloaded before the final fault/guard checks and graceful shutdown.

The first native attempt completes field construction but stops before the
standalone model DMA: the fixture omitted a verified boot-code range for that
call. No DMA call executes at that failure. The one justified retry adds the
original complete 124-byte DMA function's pinned hash and passes. Test target
restrictions remain intact. New harness work stays within the 30-minute batch
budget; unchanged fire/asset/native scenarios are not replayed.

The first installer attempt rejects an edit to a compressed owner before making
a ROM. The installer now moves both reviewed resources safely. An intermediate
build also contains an incorrect linked-overlay fallback; it is superseded by
the full resident sound mapping in the pinned `-03` cartridge. It is not a
deliverable, and no successful test is attributed to that intermediate ROM.

## Compatibility and continuation

Saved format 2, selected identities, and the saved import profile remain
unchanged. Imported saves require matching/superset selections; never load those
saves in V2 or a profile missing imported dependencies. Codec acceptance is not
proof of ordinary cross-build Save & Quit/restart compatibility. No user save is
modified by this isolated test.

The test does not enter through a tent door, spawn/register the masked camper,
draw the room on the GPU, run conversations/rewards, or establish persistence
or hardware behaviour. Continue the actual exterior/event/NPC integration and
scene lighting/floor sound, then combine entry, conversation/reward, exit, and
save checks. Other donor content, ordinary import gameplay, and browser
composition remain within the open full V3 objective.
