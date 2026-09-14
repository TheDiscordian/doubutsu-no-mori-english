# Complete English-donor villager audio

## Scope

`tools/v3_villager_audio.py --all-villagers` converts the twenty additional
villagers' complete melody fragments and builds the four missing instruments.
The roster comes from the pinned complete-artwork manifest. The existing
DOL/audio hashes and original N64 hash remain mandatory. Default invocation
retains the two-pilot converter and its exact fragment output.

The [runtime installer](V3_COMPLETE_AUDIO_RUNTIME.md) connects the complete
bundle, expanded source storage, and font/wave headers. Native loading and
melody handling pass; actual new-instrument sample playback remains unresolved.
No move-in flag or web patcher changes.

## Melody preservation

The twenty fragments total 9,376 bytes, with 380 channel/note tracks and 1,064
notes. Full source fragments, all nineteen unsigned track offsets per fragment,
pitch, duration, velocity, rest timing, instrument changes, vibrato operands,
terminators, and original padding are retained. Each fragment fits the native
1,536-byte track slot. Individual fragments range from 288 to 640 bytes.

The strict extended parser accepts channel bank/instrument selection `EB`,
relative note start `78`, vibrato `E3/E2/E1/D7`, and termination `FF`. Its note
programs accept duration/velocity notes `40..7F`, rests `C0`, instrument changes
`C6`, and termination `FF`. It rejects unknown instructions, malformed targets,
missing operands/terminators, zero durations, invalid velocities/instruments,
overlapping tracks, and unrecognised padding. No donor note is simplified into
the pilots' single-note pattern.

Compatibility is checked against the actual inspected N64 interpreter, not an
unrelated short melody template. Complete function hashes, dispatch entries,
and operand-width tables are pinned in `extended_native_interpreter`:

| Native operation | Address |
| --- | --- |
| Variable-width duration reader | `800F3484` |
| Note command interpreter / `C6` handler | `800F3760` / `800F3910` |
| Rest / large-note handlers | `800F42D0` / `800F43D4` |
| Channel interpreter | `800F4870` |
| Vibrato rate / depth ramp / rate ramp / delay | `800F4C58` / `800F4C70` / `800F4C98` / `800F4CC0` |

The donor interpreter is the pinned checkout's
`src/static/jaudio_NES/internal/track.c`; command constants are in
`include/jaudio_NES/audiocommon.h`. Static interpreter comparison is not a
native execution or listening test.

## Additive instrument bank

The melodies use 29 instruments. Twenty-five have exact native counterparts,
including full envelopes, tuning, waveform data, loop state, and predictor
coefficients. Donor IDs 84–87 have no matching native instrument. Preserve their
actual resources rather than substituting a similar native sound.

The resulting bank keeps all 83 original instruments at IDs 0–82, leaves 83
empty, and installs the four donor instruments at their actual IDs 84–87.
The bank header's instrument capacity must become 88 when installed. The
original bank has no drum or sound-effect tables. Its expanded pointer table
requires a 16-byte shift of original data from offset `160` onward. Every
instrument/envelope/sample/loop/predictor pointer is adjusted once; waveform
offsets and tuning values are not treated as bank pointers.

All complete original instrument descriptions are compared again after the
shift. The four compiled additions are compared against the complete donor
descriptions. Long envelopes retain every point through their actual terminator;
unknown control flow is rejected. All new structures are 16-byte aligned.

The four additions share a verified identical 52-byte envelope already present
in the original font. The font grows by 592 bytes, from 15,600 to 16,192.
The waveform resource retains
the entire original prefix and appends the four ADPCM samples, with alignment:
376,752 → 384,336 bytes, growth 7,584. These file sizes are not a claim about
runtime audio heap usage. New samples keep codec flags, tuning, loop records,
and predictor coefficients. Bank and wave IDs remain 2.

## Runtime installation

The [installer](V3_COMPLETE_AUDIO_RUNTIME.md) preserves full-ID tags, native
synchronization, nineteen-pointer relocation, and CPU copying. It installs
larger bank/wave resources with checked physical addresses and updated counts,
without moving the original audio files or growing the audio heap. Its
checkpoint records the passing loading checks and unresolved sample-transfer
observations. Preserve all user saves and keep both served patchers on V2.
