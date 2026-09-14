# V3 speed-bag callbacks and complete hit-sound conversion

## Completed implementation

The constructor, move, and draw callbacks are implemented and compiled, and
execute against the actual N64 keyframe/drawing engine in private emulator
storage. The donor's complete hit-sound program, envelopes, instrument, loop,
predictor book, and ADPCM sample are extracted and assembled into bounded audio
resources. Neither component is installed as a selectable item yet.

The native state mapping matters: silence appearing/disappearing states
**5, 6, 13, 15**. Copying donor enum values 12–15 would silence native movement
states while playing sounds during two native transitions. Full native room
owner binding and checked instruction windows protect this mapping.

## Artifacts and evidence

Private current cartridge: ABI 44,
`build/v3-clothing-catalogue-01/animal-forest-v3-asset-loader.z64`, SHA-256
`1f53456846a8f7f6ed9cd327ffc06e0e2f8d0253466a2bcdcb8e62b2cd1dab00`.
The cartridge itself is unchanged; the test constructs a guarded private actor,
copies the new callback text, and binds the checked 3,728-byte animated object.
No ABI 45 build is implied.

`build/v3-speed-bag-callbacks-01/code.bin` contains 472 bytes, SHA-256
`69204f52e3c2ce1599408e621e5e2e8460dc1b1730749e345a66b32c69f04730`.
The immutable registered Docker compiler produces constructor/move/draw offsets
`000/094/148`; maximum callback stack use is 48 bytes. All eleven absolute calls
are validated fixed external JALs. The artifact is linked to a private sound
observer at `8019ADE0`, not a production sound implementation.

- `build/v3-speed-bag-callback-tests-01.log`: five focused checks pass on the
  initial run. These cover relocations/rejections, full native contract,
  actual compiled dependencies, and the converted object's rig offsets.
- `build/v3-speed-bag-callbacks-native-01`: setup stops before allocation or
  callback execution. The fixture incorrectly reads cache-function reference
  bytes from the main code file instead of the boot image. Three genuine main
  engine-window comparisons pass; the cache comparison fails. No game defect
  is inferred from this reference-address error.
- `build/v3-speed-bag-callbacks-native-02`: the one justified retry uses the
  existing boot-proof helper and includes the native skeleton's opaque and
  translucent segment commands. All **103 records / 72 assertions pass**,
  including checkpoint restoration and graceful shutdown. No further setup
  retries or historical builds are tested.

The native run establishes:

- Constructor pointer resolution, joint/morph buffers, speed, and changed flag.
- Complete nine-component poses at frames 1, 57, and 69, using actual native
  interpolation and the complete converted rig.
- First-hit start, two evaluations while running, retrigger sound after both
  evaluations, reset/re-evaluation at the existing speed, and last-frame stop.
- Correct sound-eligibility checks for all four native transitions and retained
  eligibility for native movement states 12 and 14. The sound observer captures
  the full actor-position pointer and frame before reset; it synthesises nothing.
- Actual native drawing of both joints in both matrix-buffer parities, exact
  model-view/display-list commands, and both opaque/translucent segment updates.
- Unused joint/morph/matrix storage, complete object, allocation/stack guards,
  full save runtime, resident prefix, translation guard, and fault pointer.
- All segment bases restored, private allocation freed, complete emulator
  checkpoint restored, and normal silent process shutdown.

This closes the earlier asset batch's missing native pose evidence without
rerunning its abandoned standalone fixture. It does not establish ordinary
interaction, GPU appearance, or audio synthesis.

## Sound resources

`build/v3-speed-bag-audio-01/` contains:

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| `speed-bag.soundfont.bin` | 208 | `9118f3857978579f2935a30bdf882b65053528f1e6b804f32c782b81bab209aa` |
| `speed-bag.wave.bin` | 11,062 | `228e4965358c5a8f1744b620a1b75df81b09cbecf8c6fb1777cfca91b5c86b23` |
| `speed-bag.sequence-fragment.bin` | 27 | `731ca242908c0c46fd94bd0f190641e594aa33448ca6b5d4fdb26e17c36be529` |

`build/v3-speed-bag-audio-tests-01.log`: five focused checks pass on the initial
run. Complete source-resource hashes, instrument ranges/tuning, both envelopes,
loop state, predictor dimensions, every rewritten font pointer, three sequence
bindings, boundary rejection, and changed-resource rejection are checked.

The source is donor sequence 242 / sound `0176`, bank 154 / instrument 103 /
wave 5. The native numeric ID is not a match; native group one has 97 entries,
and its selector-one bank has 71 instruments. The full 11,062-byte sample is
absent from the native wave-five resource. No substitute sound is installed.

## Next implementation

Integrate the actual sound resources into the native sequence/font/wave readers
and measured audio allocation, then bind the real sound entry. Reserve callback
RAM, install the profile/vtable/model loader, and connect stable speed-bag item
identity/readers and Punchy's complete house. Ordinary acquisition, placement,
interaction, persistence, and appearance remain open. No imports become
selectable on the strength of this component check alone.

No user save, stable V2 ROM, local/public patcher, deployment workflow, service,
repository visibility, or trailer is changed. V3 source remains on
`v3/optional-imports`; both patchers await the user's V3 testing and explicit
approval.
