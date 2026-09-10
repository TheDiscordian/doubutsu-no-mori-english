# GameCube keyboard background correction

Combined ROM: `build/v1-keyboard-background-fix-01/animal-forest-title-preview.z64`.
SHA-256: `63794bd31fe5c7c9ae786b15a41d6a80c2390c890b2edd963ace9a9e5edb8d37`.
UPS: `b0316888443f92bc2a56aa3eeec8f49a8278bf834bb8e495278ac1d2bff975bb`.
This retains every preceding playtest correction and requires an Expansion Pak.
The previous ROMs, extracted inputs, and the user's saves remain unchanged.

The beige rectangle is replaced with the two exact converted GC keyboard-frame
textures. Four shaded, curved quadrants retain the donor colours, clamping,
alpha, and reflected directions, enlarged to surround the existing N64 hints.
The [fix contract](../../specs/V1_PLAYTEST_FIXES.md) records exact bindings and
the deliberate size adaptation. All forty keys, native controls, and saved
capacities remain. No new art is invented and no font atlas is changed.

## Verification record

Three focused tests passed in 2.630 seconds. They check complete donor identity,
installed pixels, source derivation, corrected hint encoding, actual compiled
material stores/equations, full cartridge/UPS retention, native DMA indices,
two relocation bases, and the signed shared-pool bound. The three letter UI
checks also passed after the shared compiler accepted optional source inputs.

Native attempt `build/v1-keyboard-background-native-01` loaded and verified the
complete editor. A fixture overlap guard then stopped the test before loading
the parent: its 67,376-byte BSS had not been included in the reserved fixture
space. This is a classified setup failure; no game instruction failed.

The one corrected retry, `build/v1-keyboard-background-native-02`, loaded both
complete overlays and called the appended draw with the real cartridge-loaded
matrix callback. Drawing returned with its stack restored. The checks before
the failure confirmed bounded graphics storage, four expected corner rectangles,
all forty unchanged key rectangles, both donor texture pointers, and no beige
fill command. The next check incorrectly demanded identical packed GC/N64
combine words. The native macros repeat the donor equation in both cycles;
the GC encoding only fills its first cycle. Actual compiled instructions and
independent field decoding establish that both native equations match the GC
material. The comparison is corrected, but this native batch is not rerun.

This is **partial native evidence**, not a passed complete scenario. The later
glyph-count, save/guard, fixture-release, and checkpoint-restore checks were not
reached in that retry. The isolated emulator shut down after the assertion;
the user's saves were never used. No audible output or user-facing preview was
opened. Ordinary screen appearance and original-hardware checking remain.

The seven-stage correction rebuild passes at `build/v1-fixes-rebuild-01`, with
the same final ROM and UPS. It compiles each changed overlay and graphics command
from sources, passing the runtime report explicitly instead of using a retained
compiled editor. Its exact receipt is `fixes.json`; inputs and source hashes are
recorded in `inputs.json`. The checked artwork/title baseline and supplied game
sources remain explicit inputs; this does not claim another complete base rebuild.

Current-cartridge progress verification, combined patch packaging, and the
assembled-candidate regression pass remain in the completion queue. Do not
substitute the older artwork-only package for this corrected candidate or repeat
unrelated tests to fill these evidence gaps.
