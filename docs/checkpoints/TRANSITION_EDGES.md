# Building-transition edge correction

The combined font/transition candidate is
`build/v1-transition-edges-01/animal-forest-edge-fixes.z64`, SHA-256
`b8a4608b62c098b334dcbe5c87ad2483406c559ba3dbcd2ed26fd64ee27368f0`.
Its UPS has SHA-256
`27895f1412a60a5cb6ba2388b4db3a85fbd3c82c4167790f7ea0f6202a0f2796`.
The [specification](../../specs/TRANSITION_EDGES.md) binds the native mesh,
projection, and single changed scale float. Font-edge resources and all prior
RC2 corrections are retained.

Three focused `test_transition_edges.py` tests pass. They establish the sole
four-byte changed range in main code, retained unrelated resources, fixed-point
screen coverage, source rejection, and complete 32-MiB patch reconstruction.
No additional allocation, transition-timing change, scene change, or saved-format
change is introduced by the transition correction.

## Native reproduction and correction

Both native checks run silently with the same compiled fixture, SHA-256
`bb277ac6e7a24651dfd05e65aca6f57390281aee7a9235f9de7e8199112d20ba`.
They draw to guarded, test-owned framebuffer `80600000`, call the actual native
startup/type/draw routines, and use unchanged cartridge meshes and texture.

`build/transition-native-before-02/results.json` completes thirteen steps and
140 draws. The uncorrected closed wipe leaves **1,908 nonblack pixels**,
including two complete top rows, two columns at each side, and one bottom row.
This reproduces the reported thin top strip without relying on a screenshot
of an unrelated scene.

`build/transition-native-after-02/results.json` completes twenty-five steps:

| Shape/state | Draws | Nonblack pixels | Edge result |
| --- | ---: | ---: | --- |
| Centre, closed | 125 | 0 | Every edge black |
| Left, closed | 148 | 0 | Every edge black |
| Right, closed | 167 | 0 | Every edge black |
| Centre, midpoint | 164 | 29,508 | Every edge black; centre opening remains |
| Centre, open | 176 | 76,800 | Entire white background visible |

The midpoint is inspected directly from the native RGBA5551 framebuffer.
Both tests retain complete fixture code/assets, resident/title/scratch guards,
and saved data, restore their isolated checkpoints, and shut down cleanly.
These establish controlled native coverage, not ordinary building-entry or
original-hardware acceptance.

The initial `before-01` run already reproduces 1,908 exposed pixels. The initial
`after-01` run obtains fully black closed frames for its first two shapes, but
later samples contain title-scene graphics. Those samples are not accepted as
transition measurements. The justified setup correction uses a dedicated
offscreen framebuffer and explicit initial render state, then restores the
normal target. Its complete retry passes as recorded above; no extra ROM fix
or weakened acceptance check is needed.
