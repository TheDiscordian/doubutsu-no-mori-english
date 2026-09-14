# Complete V3 villager audio installation

## Implemented boundary

`tools/v3_all_audio_runtime.py` installs all twenty donor melodies and the four
additional instruments in ABI 53. Existing villagers, instruments, artwork,
physical audio-file locations, save/profile formats, and both V2 patchers are
retained. Move-in flags remain disabled. Native loading and melody handling
have passing evidence; playback of the four new instruments remains unresolved.
Do not describe these components as complete playable villagers.

## Resources and memory

The [complete converter](V3_COMPLETE_VILLAGER_AUDIO.md) supplies the pinned
twenty-voice bundle. Its compact font shares a verified identical 52-byte
envelope with the original bank, preserving every envelope point. The four new
instruments retain their actual samples and all other sound properties.

| Range | Purpose |
| --- | --- |
| `80462900..80462A57` | Existing 43-entry melody source/size table |
| `80462B00..80462B1F` | Existing full-ID track tags |
| `80473500..8047396B` | Expanded melody helper, 1,132 bytes |
| `8047F000..8048149F` | Complete twenty-melody payload, 9,376 bytes |
| `80481FF0..80481FFF` | Expanded package guard |

The source table installs IDs 260–277 and 285–286; all other imported slots
remain empty. Every fragment retains its full length and nineteen track
pointers. The helper preserves the existing synchronization, native-source
path, CPU copying of resident sources, full-ID tags, low-byte alias rejection,
and original track choices. Its source bounds cover only the new melody span.
Stack frames remain 64 bytes for start and 32 bytes for count.

The two original melody hooks at `800FCEEC` and `800FD0D4` target the new helper.
The old helper is left intact, preserving every other linked entry in the
crowded main prefix. Accessory code at package offset `100..4EB` is unchanged;
the new helper fits the checked empty interval beginning at `500`, before the
accessory registry at `1000`.

The existing package at VROM `02270000` grows from `C000` to `F000` bytes,
extending its resident range to `80481FFF`. Startup checks the larger descriptor,
CRC, header, and final guard. Its 880-byte code still fits the existing slot.
The main `C000`-byte prefix remains unchanged in size. This adds 12,288 resident
bytes, without growing ordinary heaps or saved fields. Original accessory
objects and their original end guard are retained.

## Streamed font and waveform addressing

| Resource | VROM in V3 blob | Physical ROM | Bytes |
| --- | --- | --- | --- |
| Expanded bank 2 | `02280000` | `01F4DD60` | 16,192 |
| Expanded wave 2 | `02284000` | `01F51D60` | 384,336 |

These resources are not copied into the resident package. The ordinary audio
loader loads the font and streams samples through its existing PI path.
The native initializer adds a physical group base to each audio-header source
offset; it does not use the VROM directory to resolve those audio entries.
Bank 2 and wave 2 therefore receive offsets to their new physical resources
relative to the unchanged bank/wave initializer bases. This supports the actual
audio loader without relocating the complete original audio files.

Header `80114730` has source offset `00E72780`, size `3F40`, and instrument
capacity 88. Header `80115050` has offset `00E1B040` and size `5DD50`.
The empty instrument slot 83 remains empty; instruments 0–82 are retained,
and donor instruments 84–87 are added. The native loader's complete relocated
font, including all sample addresses, matches the expected resource.

The V3 file is the final live physical allocation. Composition extends it in
place into checked zero padding to 925,008 bytes, updates only its directory
row, and retains every existing file identity and physical start. All other
native code changes are limited to the two melody hooks and two audio headers;
the translation module receives the checked startup/configuration update.
The cartridge remains 32 MiB. CRC and complete UPS reconstruction pass.

## Audio capacity

All seven permanent sequence/font entries require 108,512 bytes under conservative
32-byte alignment, within the original 108,544-byte permanent heap. The 32-byte
remainder is small: future audio additions require a new capacity review, not
unchecked appends. Total/fixed/permanent heap settings and cache policies remain
unchanged. Native execution observes five loaded resources using 74,368 bytes;
the static inventory also includes the two resources absent from that scene.

## Verification boundary and continuation

Fourteen focused tests pass. Native checks prove startup, complete font
relocation, actual physical headers, melody pool copies/relocations, full-ID
handling, and the previously unfinished accessory guard tail. Two bounded
playback attempts do not observe a completed transfer for the four new
instruments. The final post-audio guard checks are therefore not reached.
This is unresolved playback evidence, not a passed synthesis test or an
established fixture-only failure. The
[checkpoint](../docs/checkpoints/V3_COMPLETE_AUDIO_RUNTIME.md) records both runs.

Continue full text/defaults, houses, and town behaviour. During the next
meaningful combined native check, inspect the actual note-layer progress and
sample requests to resolve the missing playback evidence. Do not replay the
passing font/attachment checks or start another setup loop. Ordinary conversation,
GPU appearance, move-in, persistence, and hardware acceptance remain open.
