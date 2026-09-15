# Complete fire sound conversion

## Result

`tools/v3_fire_audio.py` converts both actual GAFE01-r0 camping fire loops against
the current tent-loader cartridge. The local output contains complete native
SFX sequence 199, font 140, and wave bank 5 replacements. It does not install
them or enable fire options. Both served web patchers remain V2.

Each source program contains two layers: a sustained continuous sample and ten
crackling notes with real rests and loop targets. Complete source hashes pin
both programs and all twelve instrument components. The parser accounts for
every command, pointer, instrument, envelope, and padding byte. It rejects
unrecognised instructions, malformed loops, invalid durations, missing data,
and misaligned envelopes. Native interpreter functions and font selectors are
verified against the supplied current cartridge and pinned donor.

Both missing instruments have complete ADPCM waves, loop state, predictors,
envelopes, and tuning. None matches a complete instrument or sample in native
SFX fonts 139–141. They occupy spare table words 72/73 in font 140. All 72
existing instruments, including the speed bag, compare identically after the
append. Their original pointed resources remain in place.

The level dispatcher is distinct from triggered sound groups. A new 128-entry
table preserves all 68 original level targets, registers donor IDs `5C/5D`, and
makes unassigned entries terminate safely. Each new channel explicitly selects
font 140 and large-note mode. All five internal pointers and both instrument
operands relocate; the original notes, timing, rest lengths, velocities, decay,
and transposition remain. No code or file in either patcher changes.

## Artifacts and checks

Output: `build/v3-fire-audio-02/`.

- Report SHA-256: `fe3a4bd43eb5118960585719c0dbec0ccd187c276c1a9c263d2df6794f4f3746`.
- Sequence: 20,176 bytes, SHA-256
  `aca1498ce7ec474657820fd84605fa6b995384db30bb81727c9dda8665f52840`.
- Font: 11,280 bytes, SHA-256
  `1f746f660b7f62040134b40dea58681b312545ddab33367f9bb2e1e229512ea7`.
- Wave bank: 2,982,480 bytes, SHA-256
  `a504a0ca5ae138db2229ccd36ee87ea8d01edafb49e5bf6deee233e21644add8`.

`python3 -m unittest tests.test_v3_fire_audio -v` passes **seven tests in 0.113
seconds**. They cover complete donor dependencies, actual native instruments,
all two-layer notes/rests/loops, pointer-only relocation, all retained resources,
reserved level IDs, malformed-data rejection, deterministic outputs, and capacity.
The first preflight had a two-byte endpoint/one-byte operand-address error in
the verifier's dispatch window; correcting the window permits conversion. No
cartridge was emitted or modified by that failed preflight.

No native synthesis, physical audio playback, ordinary fire interaction, or
original-hardware verification is claimed. Existing tent artifacts and saves
are unchanged. No native harness is constructed for this data-only step.

## Installation requirement

The sequence grows by 432 bytes, font by 352, and streamed samples by 21,360
including alignment. Conservative permanent allocation rises by **800 bytes**
to **109,312**. The current permanent pool has 108,544 bytes and just 32 spare;
the converter reports the 768-byte shortfall explicitly.

Native `audiomgr_proc` allocates and passes `47A00` bytes; fixed/permanent sizes
are `1D800/1A800`. A 1-KiB coordinated increase to total, fixed, and permanent
preserves session/cache capacity and supplies the missing space. Check both
actual allocation immediates and the three size settings, then verify real
initialization. This is a proposed allocation change, not an installed fix.

The current wave file has no adjacent physical space. Its existing VROM range
has room for the added samples. A full-file relocation can preserve all existing
waves and append the new data without another directory entry. Account for
wave 2's separate physical resource inside the V3 blob when rebinding the native
initializer/header offsets. Verify native unsigned base addition and every final
physical range before relying on a wrapped relative offset. Do not copy the
whole 3-MiB wave bank into the 1.6-MiB remaining import-resource reservation.

Continue safe audio installation and full fire rig/billboard/scroll callbacks,
then true four-cell bonfire integration and summer-camper acquisition. The full
V3 content, ordinary gameplay/persistence, browser implementation, and later
e/e+ assessment remain work; this conversion does not reduce that scope.
