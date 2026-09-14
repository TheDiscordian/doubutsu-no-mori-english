# Complete V3 villager-audio bundle checkpoint

## Result

All twenty additional English-donor villagers have complete converted melody
fragments. The four missing instruments include their actual envelopes, tuning,
ADPCM samples, loops, and predictors. All 83 original instruments are retained
and checked after pointer adjustment. The twenty melodies use 29 instruments,
380 channel/note tracks, and 1,064 notes. No melody is shortened.

The bundle is `build/v3-all-villager-audio-01/`, produced by:

```sh
python3 tools/v3_villager_audio.py --all-villagers --output build/v3-all-villager-audio-01
```

- Manifest SHA-256: `ecd385d3bcde1c023d7d368d3a807dee38c2eade61de756cb93494ceca7b71f1`.
- Twenty melody fragments: 9,376 bytes total; exact individual hashes are in the manifest.
- Font: `villager.soundfont.bin`, 16,256 bytes, SHA-256
  `3d61ef716e849e874180fe492e03a6553669b24b3edde9dfeb6c4f28200f6a6e`.
- Wave: `villager.wave.bin`, 384,336 bytes, SHA-256
  `5196c332930d298eb5ac8f58c5a8a254bd2b8109ef7c7de1cf6b14841863c2cf`.

The [specification](../../specs/V3_COMPLETE_VILLAGER_AUDIO.md) records the exact
parser, inspected native interpreter, added instrument IDs, and bank layout.
The font grows by 656 bytes and the waveform file by 7,584 bytes; runtime
allocation and installation remain work.

## Verification

Nine focused tests pass across the complete-audio suite and retained pilot host
checks. The combined invocation completes eight tests successfully; one synthetic
mutation test initially targets valid operand values by incorrect indices. Its
corrected targeted rerun passes. No converter/runtime failure is identified.

- Complete actual donor outputs, all twenty fixed voice identities, exact
  original pilot-fragment retention, and nineteen tracks per fragment.
- All original and four donor instruments retain complete sound descriptions.
- Inspected native interpreter/dispatch pins and rejection of changed sources.
- Multiple notes, rests, two-byte durations, instrument changes, vibrato, and
  rejection of every truncated prefix of a synthetic track.
- Full track-table/padding bounds and long-envelope point preservation.
- Retained pilot parser, DOL mapping, and sanitizer-backed native/imported
  loading protocol and full-ID handling. No old cartridge is replayed.

The current ROM is unchanged ABI 52. The additional melodies and extended
font/wave are not installed yet. No physical audio is emitted, no new native
playback or hardware acceptance is claimed, and no save format changes.
Both V2 patchers, their services, and the released trailer remain unchanged.

Next install the complete audio bundle with bounded resident storage and actual
audio cache/allocation checks. Include the corrected accessory guard tail in
that meaningful combined test; do not repeat its passing transform prefix.
