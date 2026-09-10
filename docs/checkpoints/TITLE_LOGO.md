# Animated English title checkpoint

## Candidate and implementation

The separate current preview is
`build/title-logo-expansion-preview-03/animal-forest-title-preview.z64`, SHA-256
`a69f8ca9cdde8eece5d85e9b0a97ab70e31ebd58bb8164a16ab84ed29fb440f7`.
Its UPS SHA-256 is
`717ec8ce41cc0b2c7cc32bd7e0d2007434c55da5e52c2b31d4bf4620f19d8430`.
It requires an Expansion Pak and is not the v0 hardware-playtest handoff.

The [runtime specification](../../specs/TITLE_RUNTIME.md) defines the complete
292,320-byte overlay, 1,968-byte actor instance, three animations, segmented
assets, graphics reservations, native transition retention, and dedicated
Expansion Pak ownership. Original C/assembly/build tools are versioned; Nintendo
assets, cartridges, and generated patches remain local and ignored.

The stable v0 ROM at `build/classic-letters-pilot/animal-forest-halfwidth.z64`
remains SHA-256
`31c85f23c996b70bd7a4779b43f1039716a77c84806dfa5a7dd52e3780d50860`.
Do not overwrite it while the user is playtesting.

## Investigation and fixes

- `build/title-logo-native-01` failed to locate the title owner, without enough
  retained diagnostics to identify the cause. `title-logo-native-02` added
  read-only metadata and actor-list evidence; the game was running, but the
  title allocation was absent. `title-logo-allocation-01` established a valid
  scene arena with only 194,000 free bytes, insufficient for the initial
  292,304-byte overlay. This was an implementation defect, not a passing test
  or an assumed emulator problem.
- `title-logo-expansion-native-01` showed that updating only the DMA-listed
  boot file left the initially executed code unchanged. The installer now
  updates the guarded fixed physical startup copy as well, recomputes checksums,
  and tests complete equality between the two installed boot copies.
- `title-logo-expansion-native-02` loaded the entire expected overlay at
  `80400010`, retained both allocation guards, constructed the title actor at
  `802CF020`, and completed all three animations. It rejected graphics error
  three after 926 main-logo draws. The matrix allocator incorrectly rejected
  valid eight-byte-aligned native graphics tails. The current adapter reserves
  alignment padding before checking capacity. The corrected run below passes;
  the previous rejection is not relabelled as a full pass.

These tests are silent, isolated, read-only observations with no save injection
or visual/hardware approval. The original and intermediate preview artifacts
remain available for comparison. Do not retry the old allocation failure or
repeat the old Press Start-only native check.

## Verification and next work

Six focused title installation/allocation/relocation tests pass against the
corrected candidate in 10.785 seconds, including independent compilation and
full retention of v0 resources. Five existing Press Start checks pass in 6.373
seconds. Two existing NPC-show relocation tests and thirteen debugger
memory/thread/startup tests pass with the explicit optional eight-MiB model;
default four-MiB validation is unchanged.

`build/title-logo-expansion-native-03` passes twelve recorded steps with silent
graceful shutdown. It reads back all 292,320 relocated overlay bytes and the
complete native tile bank; the actor is `802CF020`, image `80400010`, tile bank
`802CF7E0`. All three frame controllers finish at 121, phase is two, background
opacity is 220, 1,118 main-logo draws are recorded, and the error state is zero.
Unused joint slots and the actor/Expansion Pak/resident guards remain intact.
Detected RAM is eight MiB. START reaches complete English message `09C7`
(583 bytes, no cut), and the recorded title metadata has a cleared loaded-image
pointer and zero loaded instances after the transition. Both high-memory guards
are still intact. The isolated cartridge files are not proof of normal saving.

The host source/command checks and native execution do not prove the title looks
correct. Complete visual comparison, return-to-title/existing-save behaviour, and a clear
missing-Expansion-Pak warning. Continue the GameCube-style keyboard and retained
v0 regression-fixture cleanup. Ordinary save/restart and original-hardware
acceptance remain unverified; the title preview does not certify either.
