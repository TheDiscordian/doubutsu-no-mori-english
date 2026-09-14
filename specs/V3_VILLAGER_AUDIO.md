# V3 villager melody support

## Scope

The [complete-roster converter](V3_COMPLETE_VILLAGER_AUDIO.md) supplies all twenty
additional melody fragments and four required new instruments. The
[expanded runtime](V3_COMPLETE_AUDIO_RUNTIME.md) installs those resources and
retains the protocol described here. Its new-instrument playback evidence
remains unresolved; the historical pilot checks are not proof of that playback.

`tools/v3_asset_loader.py --villager-audio` installs the pilot NPC draw routes
and Cheri/Punchy's donor melody programs. It widens the native voice paths to
retain the full donor IDs, while keeping the original instruments, samples,
audio threads, sequence interpreter, and synthesis code. It does not enable
move-ins or establish complete in-world villager behaviour.

## Verified donor conversion

`tools/v3_villager_audio.py` reads the supplied GAFE01 revision 0 disc. It checks
the DOL SHA-256
`e3166b15b810ff20397784fc83b2eb053db5d0c2a9e22ac2ead63a645881d150`
and `audiorom.img` SHA-256
`3a631dac1a2abb0d5449f85d9b41b7a6346b582d5ac04b73e87aa65ebe66d93f`.
DOL reads use the eighteen actual file/RAM section mappings. Reject overlapping
sections and reads crossing their bounds.

The 299-entry size/offset arrays are at donor RAM `800A9B98`/`800AA044`.
Sequence header `800CCA40` identifies fragment container 248 at audio-sequence
offset `B2180`, size `1D580`. Cheri uses voice 285, fragment offset 116384,
448 bytes; Punchy uses voice 286, offset 116832, 288 bytes. Preserve each entire
fragment, including its padding and nineteen unsigned sixteen-bit track offsets.

The two pilot command layouts have actual native counterparts: `EB` selects
bank/instrument, `78` starts a relative note program, and `FF` terminates tracks.
Cheri additionally uses `E3`/`E2`/`E1` vibrato commands. Large notes retain their
donor pitch, variable-width duration, and velocity. The converter validates
operand widths, relative targets, terminators, and the 1,536-byte native slot
limit. Matching a native command layout does not replace donor operands.

The `EB` bank operand is a **selector**, not the actual bank ID. Selector 3
resolves to bank 2 in both main-control sequence maps:

| Main control sequence | Bank map |
| --- | --- |
| GC 242 | 2, 155, 154, 153 |
| N64 199 | 2, 141, 140, 139 |

All four pilot instruments, 0, 1, 48, and 49, match in that bank: pitch ranges,
decay, envelopes, tuning, ADPCM waveform data, loop records, and predictor
coefficients. Their shared wave bank is 2. The fragment container's own bank
map is not the map used to play its copied fragments. The original N64 sequence,
instrument-bank, and waveform resources remain unchanged.

## Native runtime

Configuration/blob ABI 3 retains the draw variant's 16-KiB reservation at
`80460000..80463FFF`. No ordinary heap growth or actor resizing occurs.

| Reservation | Purpose |
| --- | --- |
| `80462900` | 43 eight-byte source/size entries for IDs 256–298 |
| `80462B00..80462B1F` | Sixteen mutable full-ID track tags, initially `FFFF` |
| `80463000..804631BF` | Cheri's resident fragment |
| `804631C0..804632DF` | Punchy's resident fragment |
| `80463FF0..80463FFF` | Existing end guard |

Absent imports have zero source/size entries and cannot start playback.
The source check rejects unknown IDs, missing data, oversized or misaligned
lengths, and sources outside the owned reservation. Original IDs use the native
size/offset tables and checked container 205 instead of the imported table.

Native audio-global base is `801494E0`. The sequence-header pointer is at
`8014BD30`; group-zero sequence data is at `8014CBA8`. Before modifying playback,
validate the loaded main-control sequence prefix `FB0006003A10` and RAM bounds.
Tracks 6, 7, and 15 own 1,536-byte areas at sequence offsets `3A10`, `4010`, and
`4610`. Other tracks are rejected.

Retain native synchronization: send stop, clear the old note count, flush audio
commands, wait for audio, and revalidate the sequence pointer. Copy the complete
fragment and add the destination offset to all nineteen track pointers. Set
the notes pointer, low-byte audio port tag, and start command. Copy on every
start, as the donor does, so a shared voice can safely start on different tracks.

Original fragments still use native `Nas_FastCopy` at `800EB978` with cart
medium 2. Imported resident fragments use a bounded CPU copy. The native helper
does **not** support RAM medium 0: its lower PI routine returns without queuing
completion, leaving the blocking receive waiting. Never route RAM assets
through that helper. Sequence instructions are interpreted on the CPU; the
native implementation also edits relocated pointers on the CPU.

Patch the upper bound in `Na_VoiceSe` (`800F91FC`) to 299. Preserve sixteen bits
through `Na_Inst` (`800FCE80`) and `Na_MelodyVoice` (`800FD280`), including the
stack store/reload across native track selection. Replace melody start
`800FCEEC` and full-ID count `800FD0D4` with the bounded resident helpers.
Preserve native track selection: ID 0 → 6, ID 255 → 7, other IDs → 15.
Do not copy the donor's separate ID-254 behaviour implicitly.

Audio ports remain eight-bit. The count helper requires both the owned full-ID
tag and native low-byte port to match. Consequently, native voice 29 cannot
masquerade as imported voice 285, or vice versa. Clearing note count in the
synchronized stop phase prevents reporting an old count under an aliased tag.

## Verification boundary

The [checkpoint](../docs/checkpoints/V3_VILLAGER_AUDIO.md) records exact builds,
five passing focused checks, and the combined silent native audio/draw pass.
The native test invokes actual public melody entries, verifies all copied bytes
and nineteen pointer relocations, observes consumed audio ports, checks both
directions of a low-byte alias, and restores its emulator checkpoint. It also
checks both loaded NPC overlays and their real patched draw/constructor tails.

No physical audio listening test, complete villager conversation, move-in,
house, or save/reload of an imported identity is claimed. Saved layouts are
unchanged, but imported-profile and cross-version compatibility remain unverified.
Use disposable saves. Stable V2 and both patchers remain unchanged.
