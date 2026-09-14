# V3 accessory-runtime checkpoint

## Output

ABI 52 installs all twenty imported draw records and all sixteen joint-attached
accessories in both NPC owners. Shared immutable storage and frame-local matrices
avoid new actor allocations or saved fields. All move-in flags remain disabled;
this is an implementation artifact, not a playable-import acceptance claim.

- ROM: `build/v3-accessory-runtime-01/animal-forest-v3-asset-loader.z64`
- ROM SHA-256: `18af2aad25285b9ab5bc01a9a47ed9a79e9b819fb9fa3c63e81699118043c4fc`
- UPS: `build/v3-accessory-runtime-01/asset-loader.ups`
- UPS SHA-256: `cfeb3c20645c035406db6fc0a655ac9f2af6422bc0b021cdeb118eff803ad561`
- Package SHA-256: `649e1b6fd2d3dcf7329788d547f8b116e6a6f7ab244144c2707792f644167075`

Construction: `python3 tools/v3_accessory_runtime.py --output build/v3-accessory-runtime-01`.
The [runtime specification](../../specs/V3_ACCESSORY_RUNTIME.md) owns the
memory map, donor adaptation, and hook design. Resident usage increases by
49,152 bytes; ordinary heaps, actor/save layouts, and cartridge size do not grow.

## Focused verification

`python3 -m unittest tests.test_v3_accessory_runtime -v` passes all seven tests
in 7.992 seconds. Host C checks use sanitizers and cover original callback
arguments/returns, both joints, scale correction, matrix/segment restoration,
missing next-frame joints, null matrices, full/boundary graphics buffers,
invalid scales and registry rows, startup descriptor/header/guard validation,
cache maintenance, repeated initialization, and no-eight-MiB rejection.

Cartridge checks verify every complete accessory object, twenty donor-bound
draw records, unchanged pilots, both exact JAL edits with preserved relocations,
allowed physical changes, package bounds, profile retention, N64 CRC, and full
UPS reconstruction.

## Native execution: partial

The first silent isolated run uses `tests/v3-accessory-native.json` and writes
`build/v3-accessory-native-01/results.json`. It records 43 steps and 28 passing
assertions, with no failed assertion. Actual MIPS execution verifies:

- Complete startup-prefix and accessory-package transfers.
- Both owners' complete Maelle/Yodel draw-record copies with retained tails.
- Real native skeleton traversal for Maelle's head joint 25 and Yodel's torso
  joint 13, using a bounded synthetic 26-joint rig.
- Donor scale correction, fixed-point graphics matrices, actual lighting/setup
  commands, attachment display lists, restored segment 6, and CPU world-matrix
  restoration. Expected translations are `(157,283,409)` and `(133,247,361)`.
- Original-character fallback and rejection when the graphics buffer has too
  little room after the ordinary skeleton command.

The final null-matrix call returns, but its checker requests a zero-byte
debugger read and raises `ValueError: Invalid debugger memory range`. The
null-output assertion and subsequent package/profile/allocation/stack/furniture
guard tail therefore do not execute. The fixture restores the temporary CPU
segment/matrix state and frees its private heap in cleanup.

The checker now reads the untouched 16-byte sentinel for an empty expected
command stream. A tail-only retry is available without replaying the passing
transform cases. Its attempted invocation with
`--seed-state build/v3-accessory-native-01` is rejected before emulator startup:
the interrupted first run has no exported `test.flash`. This consumes the
single setup retry; no third attempt is made in this implementation batch.

Carry the corrected null/guard tail into the next meaningful combined test,
using a fresh isolated boot rather than requiring that missing save export.
Keep these missing results open. Synthetic CPU/command checks do not establish
GPU appearance, ordinary NPC callbacks, animation, scene visits, save/restart,
or original-hardware operation.

## Compatibility and continuation

Profile and saved formats are unchanged from ABI 51. Ordinary cross-build
loading is not newly verified, and V2 or earlier incompatible V3 profiles
must not consume imported saves. Existing user saves remain untouched.

Continue remaining voices, full text/defaults, house dependencies, explicit
town behaviour, and ordinary appearance/persistence. Accessory installation
does not enable move-ins. V3 source stays on `v3/optional-imports`; both V2
patchers and the released trailer remain unchanged until the user's approval.
