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
nor the main V3 lock is changed. The explicit V3 proposal below includes the fix.

## V3 integration

The shared installer consumes the complete ABI-115 lock and emits ABI 116 at
`build/v3-translation-headers-02/`. The Museum correction and ordinary/snapshot
reader's missed imported-name bound are installed without replacing any
imported item, artwork, behaviour, profile bit, or saved format. Both composition
paths use the report's explicit corrected V2-12 pin for empty selections.
The main ABI-109 lock and both served V2 patchers remain unchanged.

- ROM SHA-256: `eb54b77ffcb15095f356c6ae94d241d472dc70f08289099b05ef6067acd25850`.
- Report SHA-256: `dc18227d25731e5d24cc51a8c4808fb2497bab6c23b566b950fd03addd752c61`.
- UPS SHA-256: `23ede226d256e51d3fe7c50edae917306c1fc7e0e994260be08bd3208f7b6884`.
- Explicit lock: `build/v3-translation-headers-02/build-lock.json`.

The editor gains 1,536 bytes within its existing unused reservation. Its complete
output equals the corrected V2 editor except for the two expected 216-to-238
name bounds, including the retained old header and newly appended header.
The common resource-tail builder preserves all existing resource identities and
keeps the catalogue/shop tail reusable by subsequent imports. The resident
reader retains every V3 change and fixed export address. Its only additions are
the checked Museum adapter/entry and bound at `80198548`.

Seventeen focused checks pass: five translation-specific checks and twelve
existing composition checks targeted at ABI 116. Host sanitizer checks cover
the complete 216- and 238-index editor ranges, Museum editing/animation states,
fallbacks, geometry, and immutable state. Cartridge checks cover complete
unrelated resource retention, allocation bounds, rejected reader/baseline
damage, original-ROM UPS reconstruction, future resource-tail reuse, and
correct empty/all/subset composition. The first new cartridge assertion wrongly
looked for a literal `Museum` string; the compiler uses immediate stores. The
corrected assertion compares the entire editor against the fixed V2 code with
only the two expected bounds changed, and passes. Fourteen representative
browser/offline profiles match through the existing Node comparison.

`build/smoke-v3-translation-readers-01/` passes on its first attempt: 57 result
records, 35 component assertions, and four final fault/memory-guard assertions.
It loads and relocates the complete new board from the actual cartridge, checks
the resident adapter and complete reader, and executes Museum, player,
unsupported-type, original villager, first/last imported villager, and
out-of-range name cases. Source identities, destination guards, and live save
memory remain intact. The fixture frees its allocation, restores its checkpoint,
resumes, and verifies zero fault plus resident/equipment/save-state guards.
No code is uploaded; the isolated emulator is silent and exits successfully.
Results SHA-256:
`27adab94f21c5667038ac21ea8ab01165e7ee4d920691522a29826b1c560c3f2`.
This focused V3 component run deliberately does not execute graphics comparison;
it does not turn the older V2 rendering fixture into a passing test.

The private export `build/v3-translation-browser-01/` contains 112 choices and
both updated reconstruction recipes. The existing silent real-worker check at
`build/check-v3-translation-browser-01/` reads both original games as browser
File inputs and matches the offline result for:

- Empty selection: exact corrected V2-12.
- All installed choices: exact ABI-116 ROM above.
- Punchy plus camping selection:
  `5a62afa645c9d3a45ca912a3c58685aad88b8f7b8a579b634184f180c566c996`.
- Two-fan subset:
  `b489decf5bb4500f9cc579aa0e0112475d89f5b15ce64d62ef81f4d35252d027`.

Worker termination, unknown-option rejection, corrupt-plan rejection, no page
errors, and local GET-only requests also pass. The temporary server shuts down;
the export is not a served patcher. Results SHA-256:
`8fc0467be6bb04947c0df2273eec9c9f58e7ed4ef9d70c1740e08d6ae853c0f5`.
The full interface's prior invalidation-fixture issue is not retested or closed
by these worker results.

Imported save compatibility retains format 2: keep matching/equal-or-larger
profiles, do not load imported saves in V2, and do not treat removing imports as
migration. Ordinary cross-profile reload, mail appearance, and hardware remain
unverified. Reuse the completed equipment same-profile persistence evidence for
unchanged save code; no historical-build replay is needed. The independent
seasonal-copy failure remains unresolved and prevents main-lock promotion or a
playable V3 handoff. Continue ordinary acquisition and ordering/delivery on this
explicit proposal, preserving that blocker.
