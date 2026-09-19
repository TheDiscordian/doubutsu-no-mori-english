# Museum letter-header correction checkpoint

## Deliverable

- Local ROM: `build/v2-museum-header-12-final/Animal Forest English V2.z64`.
- Local patch: `build/v2-museum-header-12-final/Animal Forest English V2.ups`.
- ROM SHA-256: `a09373b051cbcd93991e5dd6cb17a238a2afb1e2e2d7694d75408d24a55d4eee`.
- UPS SHA-256: `c68572a7997cdc9ead5c19cc81be85905b27ff163d788002e23d8b4e7d617ee6`.
- Preserved input: V2-11, SHA-256
  `8bbd1955536a2a3ac9f76d6f323842f5ce25c037e1ff5fd3da9f28d6dfe20507`.

The reported omission was real: the museum recipient picker had an English
case, while the editing and resident reading headers still fell back to the
canonical saved Japanese name. Both header implementations now resolve the
museum's type without changing that saved identity. The official GameCube
wording and every display locator share one provenance entry.

## Verification

The final focused invocation passes 14 checks in 3.650 seconds. `git diff --check`
and Python syntax compilation pass.

The focused host checks cover the editor under AddressSanitizer/UBSan, ordinary
and generated museum headers, incoming museum replies, all 216 villager names,
and player/unsupported fallbacks. The first combined command lacked the tests
directory on `PYTHONPATH`; the corrected invocation passes.

Four current-cartridge checks and six catalogue checks pass: exact original-ROM
UPS reconstruction, all unrelated DMA resources retained, fixed resident
addresses, bounded descriptor padding, unchanged old board code except its entry
jump, owner allocation and relocation, no save/delivery changes, and official
source attribution. The feature-option build retains the same ROM and patch
hashes as the first corrected build, keeping the native component evidence valid.

Native attempt one, `build/museum-header-native-01/results.json`, successfully
loads and relocates the complete board and confirms the cartridge-loaded adapter.
The fixture then incorrectly supplies an external-code proof for a resident
function, which the debugger rejects before executing that function.

The justified retry, `build/museum-header-native-02/results.json`, verifies the
resident code explicitly and uses the debugger's resident-call path. The museum,
player, unsupported identity, and villager cases execute successfully, retain
the source identity and output guards, and restore the stack. The new editor
header entry also returns with the stack restored. The run then stops at the
fixture's graphics-arena assertion: it observes the separate credits font list,
but the letter renderer uses the ordinary two-dimensional graphics list and
does not need vertex allocation. This is not evidence of a game buffer overflow.
The partial run contains 15 passing assertions in 26 records; its results
SHA-256 is `67ce038f6259006d55c0f42843db3ee9f5bed62d69f42f5a736404bf19854b9f`.

The fixture now selects the correct graphics list and records its actual bounds,
but it has not been rerun: the setup retry allowance is exhausted. Complete
render comparisons, end-of-fixture guards/checkpoint restoration, ordinary
in-game appearance, and original-hardware confirmation remain unverified.
Do not report the partial native run as a complete pass. No user save was used;
both emulator runs were silent and isolated.

## Compatibility and next action

Saved formats and all fossil identification/delivery code are unchanged.
V2-11 ↔ V2-12 compatibility is expected without migration, including existing
museum letters; a new cross-version save/reload cycle is not claimed.
The user can confirm the museum name while composing and reading a letter.
Existing V2 builds and saves are preserved. Neither served patcher, GitHub Pages,
nor the V3 lock is changed. Carry the fix into V3 before its next tested handoff.
