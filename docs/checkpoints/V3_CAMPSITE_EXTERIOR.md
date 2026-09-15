# V3 additive campsite exterior

## Implemented

ABI 72 installs the full exterior actor in the existing campsite reservation.
The new resident actor `CA`, foreground `5849`, and marker `F127` do not replace
the igloo, native actors, or building identities. All 201 native descriptors
remain intact. Native creation uses the new descriptor only for `CA`; the
existing 201-active-actor limit stays.

The complete 3,168-byte code fits `804A0360..804A0FBF`, with 64 bytes spare. The
496-byte actor/profile/door/collision packet fits at `804A1800`; all surrounding
scene records and guards remain intact. Package size stays 192,528 bytes.
Startup verifies its CRC and invalidates the complete callback reservation.
No additional permanent RAM or normal heap/model-bank limit is introduced.

Each tent retains the fixed `2D8` native structure-pool stride and owns 7,776
heap bytes: all 6,960 exterior bytes, all 800 shadow bytes, and a 16-byte guard.
Callbacks implement allocation/DMA failure cleanup, foreground reservation and
buried-item recovery, the complete nine-cell collision shape, player-facing
door requests, outside return coordinates, scene-35 entry, and daylight window
fading. Complete window and projected-shadow data live in checked frame storage;
misaligned/exhausted graphics arenas do not submit partial draws.

The native Structure setup pointer calls the resident selector; non-tent IDs
continue through the existing loaded controller. Only its two changed HI/LO
relocations are removed; the other 120 stay. Both complete moved files retain
their VROM and DMA slots. Original igloo executable/resources remain unchanged.
The native birth controller forwards all `5xxx` IDs to that callback and ignores
`Fxxx` markers. `F127` therefore does not spawn another actor.

Setup checks the actual ten camping-item selection rows. Offline composition
retains 59 experimental options, deterministic fixed identities, exact all/V3
output, and exact empty/V2 output. Both served patchers remain V2.

## Artifacts

- Full ROM: `build/v3-campsite-exterior-runtime-01/animal-forest-v3-asset-loader.z64`.
  SHA-256: `61d9bec4ac698420f20df7a062b13d8bf3619989fc78b357245d6ade4589abdf`.
- UPS: `build/v3-campsite-exterior-runtime-01/asset-loader.ups`.
  SHA-256: `d12ba5091ab0ecc24ee192c502e5fedd2260fbf848adfd3bcd5c3352b42ec6f0`.
- Build report SHA-256:
  `24fa37a4cd3bb5b5ace06cc10bfedf001b29a0ac2c0e905618f1a60c741fbc8b`.
- Ten-item subset: `build/v3-optional-campsite-exterior-01/`.
  ROM SHA-256: `368883fdf6c2de2609aef22067cc12794c7f889864512dbdb98b50a33c9c9f70`.
- Compiled callback SHA-256:
  `82ef38e5dbffc9a74fe48af00d3b628a6efadf66c8b216231699bf14b91c1901`.

These ignored local artifacts are not a complete-import playtest handoff.

## Executed verification

Four focused integration checks and twelve current-composition checks pass.
The first callback-fixture invocation used the wrong blob-relative artwork
offsets and read empty input. Correcting those two offsets made its single retry
pass. The sanitised C test executes all complete callbacks, full asset copies,
buried-item handling, all nine collision calls, selection gating, door bounds,
entry/exit metadata, fades, retained frame data, allocation failures, graphics
limits, and idempotent cleanup. Startup's ABI-72 CRC/cache check also passes.

Cartridge checks cover exact changed-owner scope, retained native descriptors
and igloo, complete scenery retention, unchanged surrounding packet bytes,
all remaining relocation records, unchanged DMA slots/count/terminator, package
and ROM checksums, and unchanged save profile. The builder verifies full UPS
reconstruction from the pinned original ROM.

The silent native test is **partial**, not a construction/gameplay pass:

- Attempt 1 stops in the host relocation reference before loading the controller.
  Two actual native address constants lie outside the nominal overlay: the
  `809BD87C` setup-table bias and `80A03528` unrolled-loop terminal pointer.
  Both are verified in original instructions; neither is dereferenced directly.
- The single corrected retry records 20 results, ten completed native calls,
  and eight passing assertions. Actual full controller relocation/BSS,
  resident descriptor selection, native setup registration, and all nine unused
  actor-pool slots pass. The real scene field constructor returns.
- The probe then rejects the field's background-buffer pointer at its allocation
  bound, before tent construction. The rejected value was not recorded in that
  run. The tool now includes rejected allocation addresses in diagnostics, but
  no third attempt is made. The 135,168-byte private fixture may contribute to
  allocation pressure; that is a hypothesis, not a classified harness failure.
- Native tent construction, complete DMA, drawing, destruction, final guards,
  and checkpoint restoration are **not** established by this run. The isolated
  process exits; no user save is used. Retain the failure as unresolved.

Retry results: `build/v3-campsite-exterior-native-02/results.json`, SHA-256
`df0cfa32a3ffdf87f9511330551bda963b81be6ec44dbb05f465bb969cd205d4`.
No further native retries or historical cartridge tests belong to this batch.

## Next work and compatibility

Continue the summer-event lifecycle, saved camper identity, English greeting
and reward conversations, selected reward filtering, and separate scene lamp,
room lighting, and floor sounds. The next meaningful native/gameplay batch must
capture the failed allocation value and available memory, then exercise the
completed campsite route. Do not treat event acquisition or ordinary entry as
finished because the exterior callbacks compile.

Save format 2 and selected identities remain unchanged. The codec accepts equal
or larger profiles and rejects missing dependencies. Ordinary cross-build
save/restart compatibility is unverified. Preserve test saves and never load
an imported save in V2. Natural gameplay, GPU appearance, persistence, and
original-hardware acceptance remain open. The full V3 goal continues, including
other donor families, playable imports, and browser composition.
