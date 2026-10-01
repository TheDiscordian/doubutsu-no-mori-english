# Complete V3 villager audio installation

## Implemented boundary

`tools/v3_all_audio_runtime.py` installs all twenty donor melodies and the four
additional instruments. Existing villagers, instruments, artwork, and
save/profile formats are retained. Native loading, melody handling, selection
of all four added instruments, and matching sample transfers pass. The original
GameCube and N64 tune controllers share the held-note rule; preserve their
timing rather than extending unheld notes to reach later instrument changes.
The public deployed patcher stays on V2; the local preview serves experimental V3.

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
relative to their checked initializer bases. The current wave initializer map
is `fire_sound.wave_headers`; the older complete-audio receipt is not the current
wave-group placement. Unsigned native base addition retains external wave two's
absolute address even when the complete wave group is above it.

Header `80114730` has source offset `00E72780`, size `3F40`, and instrument
capacity 88. Header `80115050` has offset `FED416B0` and size `5DD50` in the
current full selection, resolving to physical `01F51D60`.
The empty instrument slot 83 remains empty; instruments 0–82 are retained,
and donor instruments 84–87 are added. The native loader's complete relocated
font, including all sample addresses, matches the expected resource.

The current full selection uses a 64-MiB cartridge and an Expansion Pak. Audio
resources remain local and ignored. CRC and complete UPS reconstruction are
checked by the shared composition path.

## Audio capacity

The current complete item/villager selection's seven permanent sequence/font
entries require 118,688 bytes under conservative 32-byte alignment, within the
118,784-byte permanent heap. Future audio additions require a new capacity
review, not unchecked appends. These figures include imported item audio; the
four villager instruments do not themselves enlarge the ordinary heaps.

## Verification boundary and continuation

Native checks prove startup, complete font relocation, actual physical headers,
melody pool copies/relocations, full-ID handling, and accessory guards. The
current-build note trace additionally proves native selection and matching
sample transfers for every added instrument. Require actual instrument selection
as well as sample transfers: DMA read-ahead can include a neighbouring waveform
before that instrument plays. Melodies and the checked 864-byte save/profile
region stay unchanged;
post-audio guards, zero fault state, checkpoint restoration, and shutdown pass.
The [checkpoint](../docs/checkpoints/V3_COMPLETE_AUDIO_RUNTIME.md) records exact
current evidence and the earlier missing observations' test-tune cause. The
controller source comparison and current cartridge check retain the original
held-note and stop rules. No audio game-code repair is required.

Ordinary in-world conversation, listening, and hardware acceptance are not
claimed by this controlled silent tune test. Continue the remaining connected
visiting and current save-cycle checks under the active V3 task; do not replay
unchanged font/attachment checks or redesign the original audio behaviour.
