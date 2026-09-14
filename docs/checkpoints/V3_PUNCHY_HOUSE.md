# V3 Punchy house and starting outfit

## Implementation

The combined private variant installs Punchy's complete donor house at fixed
actor index 237 (`E0ED`). Its row is `02012714037E037F`; foreground layers
490/491 map to 894/895. The layout retains the rotated speed bag `3352`, all
ordinary furniture/structural markers, and K.K. Love Song `2A23`. Both room
surfaces have complete exact native matches, wall 39 and floor 20. Original
surfaces, clothing banks, all 218 native house rows, and all 432 native
foreground rows remain unchanged. Cheri's installed layout is retained.

The 436-row foreground needs 225,848 bytes. It moves from `011AB000` to
`03F60000..03F97238`, inside the checked reservation ending at `03FA0000`.
Its native DMA directory identity remains fixed; adjacent files are preserved.
Eight checked words connect house-table and foreground bounds. Native heap
bounds stay unchanged; the foreground request grows by 2,072 bytes over native,
and the 498-entry sparse pointer allocation grows by 160 bytes.

Punchy's default row keeps donor shirt `24BF` and applies the separately
imported `34BF`. Both complete artwork hashes and the selected profile bit
are required. A shared runtime predicate calls the real clothing-source reader:
missing/disabled/wrong garment metadata cannot initialize the villager or
make that villager eligible for selection. All twenty move-in flags stay zero.
Both pilots have installed house/default dependencies; ordinary gameplay is
not inferred from those dependencies.

The first construction hits the existing 1,536-byte text-code bound. The
expanded writer is placed in the unused gap after the pilot melodies:
188 bytes at `804632E0`, below selection at `80463400`. The main text code is
1,480 bytes before the `80464600` item bridges, and selection is 1,504 bytes
before rewards at `80463A00`. Both retain checked non-overlap. The permanent
48-KiB prefix, actual melodies, item bridges, rewards, animated callbacks,
models, and saved state do not grow.

## Artifact and compatibility

`build/v3-punchy-house-02/animal-forest-v3-asset-loader.z64`, ABI 50.

- ROM SHA-256: `55cb90c0cc9eac32aa6e180051f1791072cfa6dd5ba1c6b8a72a413f6211e060`.
- UPS SHA-256: `584902c15f707529a64f16f1ca6c8812a80d4c7712e218ea982fb3780e654d5c`.
- Foreground SHA-256: `8b8d2f7b30dc4f207fda508a2dcf5ba4850f35306c4fffab168ac75b91eeb157`.
- House table SHA-256: `2f946ffbca35e6be44b2de77a0646b6c0c1223759fc41edb13510f4b74cf0137`.
- Default extension SHA-256: `1f665913c43b67768f500182ae366f0710d2f6bacbb1c142d4bd264b87524ee3`.

ROM remains 32 MiB and requires an Expansion Pak. The saved profile and format
are unchanged from the preceding ABI-49 speed-bag gameplay build; compatibility
in either direction is expected but ordinary cross-build reload is unverified.
Earlier builds missing speed-bag/clothing dependencies reject these saves;
never use experimental V3 saves with V2. Source saves and earlier ROMs stay intact.
This artifact is not an accepted gameplay handoff while the native result below
is unresolved. Both web patchers remain on V2; only V3 development source is
tracked on GitHub.

## Focused verification

`build/v3-punchy-house-tests-01.log`: all seven tests pass.

- Actual C default/name/phrase code plus the actual clothing reader under
  address/undefined-behaviour sanitizers; all three Punchy initializers and
  seven missing/invalid dependency cases preserve exact write boundaries.
- Full source-bound conversion, original house/layer preservation, both fixed
  imported rows, speed-bag rotation, donor music, and native DMA identity.
- Complete loader address pairs and resource bounds, adjacent native-file and
  surface/clothing retention, and exact unmodified saved profile.
- Installed code matches the compiled sections, including the outlined writer;
  retained melodies, item bridges, reward code, animated callbacks, and model
  storage match the preceding build. No older cartridge is executed.
- Missing rotated-item dependency and missing clothing-profile bit are rejected
  before mutating caller code/data.
- Full current cartridge composition, UPS reconstruction, output hash, and the
  exact import-free V2 result.

`build/v3-punchy-house-build-01.log` records the rejected text-code overflow;
`build/v3-punchy-house-build-02.log` records successful current construction.
The size guard is preserved, not weakened.

## Unresolved native result

Both `build/v3-punchy-house-native-01/` and `...-02/` stop at the foreground
arithmetic window before layer/default checks. The encoded and resident words
are the expected LUI/ADDIU start/end pairs. The expected end is `03F97238`,
size `00037238`, and quotient/remainder 436/0. Both runs instead report end
`03F9E470`, size `0003E470`, and quotient/remainder 492/232. The difference is
exactly one extra `7238`, the end address's low half.

The first attempt enters the actual native window through the debugger. The
one setup retry verifies the installed instructions, copies the twelve
PC-independent words to private scratch storage, flushes caches, and uses the
existing isolated instruction-window method. It observes the same mismatch.
Neither result establishes whether the cause is the emulator/debugger or an
ordinary game path. Do not label this a proven harness defect, alter the
expected count to pass, or treat the later unexecuted checks as successful.
The native runner uses `/usr/bin/ares`, SHA-256
`347d5d352dc7d3a3aab1f9a5d6d2782ac0b23b84cb7ae85299a3c65cdd9b964b`.

The setup retry allowance is exhausted. Preserve this evidence; the next
useful classification is ordinary scene execution or independently justified
inspection of instruction execution, not another identical debugger replay.
Full foreground allocation/layer transfers, outlined native initialization,
ordinary house visits, move-in, and persistence remain unverified. Treat the
loader discrepancy as unresolved for any playable handoff. Unrelated donor
conversion and item lifecycle work can continue. No physical audio is emitted.
