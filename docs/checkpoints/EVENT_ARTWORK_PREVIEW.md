# Controlled N64 event-artwork rendering

The exact combined `title-stall-combined-01` cartridge has a passing controlled
graphics run at `build/event-artwork-preview-native-02`. No production ROM,
package, actor/event code, or user save is changed by this check. The test uses
a fresh silent eight-MiB emulator and restores its complete checkpoint.

The twenty-four recorded steps include 100 left-stall draws, 120 reflected
right-stall draws, and 116 fortune-table draws. Each model uses the installed
native commands and complete unchanged building object, not a host imitation.
All code/object/depth/scratch boundaries and the resident/title guards remain
intact. The test callback reports zero errors, no native thread is faulted, the
original title callback and unused scratch guards return after checkpoint load,
and shutdown is graceful. The resulting blank isolated cartridge files do not
establish normal in-game saving.

The three captures are inspected locally. Both stalls show the striped awning,
balloons, pinwheels, and mirrored placement without visible missing faces or
obvious lighting inversion in the shown surfaces. The preview framing clips the
lowest part of the stalls; it is not full silhouette acceptance. The complete
fortune table shows its cloth, tray, coins, and cards. The fixed preview light
and orthographic camera are not native seasonal scene conditions. Original
collision, shadows, event scheduling, and ordinary appearance remain untested.
No floating report window, live-desktop capture, or audio is used.

| Evidence | SHA-256 |
| --- | --- |
| Cartridge | `128f19b734565e5e0c3af15aaf1fef8fb066155039404a2bfdd29efe8010bf19` |
| Complete installed building object | `3990f10e3f1881cea88848e0a04b05f71a7cea5b5b94a018883a45dcb4dd0d2f` |
| Independently compiled 672-byte test callback | `07ca93bc15d2cf2f1c984d32ecc1813645726e6f0a31f4b20bcdb80c8249a308` |
| `results.json` | `77f939d3970ac3c2e901e83506bdc2c426fea75fd0b24ebf95a63a92357c800d` |
| `stall-left.png` | `f12839d4edb1f6aded518f89cdeeb804a60d1566a6a9b79a1e05cc52b3083412` |
| `stall-right.png` | `a73d8c9cd0d31743578e11fff88ff816e7b8406c624877dabf94c6a584de849c` |
| `fortune-table.png` | `5f7d2bba95da5f086960319b67cd1ed9ebb53a1e234ecf70b7c53c1a43390d26` |

The first native attempt, `event-artwork-preview-native-01`, stops before drawing
a model because the fixture incorrectly treats the static graphics pool as a
heap allocation. The rejected callback sets its error flag and writes no model
commands. The corrected fixture checks the two actual overlay arenas inside
`gGfxPools` at `801540C0`, with pool size `20410`, overlay offset `18F08`, and
8192-byte overlay capacity. Its permitted setup retry is the successful run
above. This failure is in test-only code; the playtest ROM is unchanged.

Three focused host tests pass in 0.923 seconds, including independent Docker
compilation, signed fixed-point matrices, complete source/code binding, occupied
scratch rejection, guard failure, all selections, and restoration checks.
Thirteen existing debugger memory/startup/thread tests pass in 0.004 seconds.
The host fake's draw counters are fixtures, not native rendering evidence; the
separate recorded emulator run supplies that evidence.

The [preview specification](../../specs/EVENT_ARTWORK_PREVIEW.md) contains the
memory layout and test limits. To reproduce a relevant changed batch, generate
the scenario with `tools/event_artwork_preview.py --output <fresh-local-folder>`
and run its `scenario.json` through `tools/emulator_smoke.py` with the exact
cartridge, `--expansion-pak`, `--no-initial-screenshot`, and `--seconds 100`.
Do not repeat this passing probe for unchanged model data.
