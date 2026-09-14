# Complete villager-text checkpoint

## Output

ABI 54 installs the complete twenty-villager name/catchphrase table and the
expanded saved dependency profile. It preserves the two pilots' defaults,
every original villager, all audio/accessory resources, and disabled move-in flags.

- ROM: `build/v3-all-villager-text-01/animal-forest-v3-asset-loader.z64`.
- ROM SHA-256: `eb611e2bade707270d8c72cd11349b344fecb3cd262918c31a4ffc1303ac8101`.
- UPS: `build/v3-all-villager-text-01/asset-loader.ups`.
- UPS SHA-256: `9f6344c7f63d9b0eb3086db7e14063ffb0bd98e90910ff0c6b0daccb3787755a`.
- Complete metadata SHA-256: `12fc1c5e0df98d0c47317f7911514ddc6169da065f474654c3f4d930a0a62549`.
- Selected profile SHA-256: `0536dae9399022469a4f2168abd9d0b212a99f7a9f23426a7ffb5a0393d9af4a`.

Construction: `python3 tools/v3_all_villager_text.py --output build/v3-all-villager-text-01`.
The [specification](../../specs/V3_COMPLETE_VILLAGER_TEXT.md) records the full
roster, six-byte alias policy, actual shirt dependencies, and compatibility.
The cartridge stays 32 MiB, and resident/ordinary memory allocations do not grow.

## Focused checks

`python3 -m unittest tests.test_v3_all_villager_text -v` initially passes four
of six checks. Two test inputs incorrectly pass mutable byte arrays to APIs
requiring immutable bytes. Those fixture types are corrected; the two affected
checks pass in 2.890 seconds. No ROM change is needed.

All six checks now have passing evidence:

- Reconstruct all twenty complete source-bound rows and retain exact pilot data.
- Resolve every full name, six-byte compatibility key, and ten-byte phrase through
  the actual C text and generated-mail readers under address/undefined-behaviour
  sanitizers. Verify borrowed phrases, disabled aliases, personality, missing-outfit
  no-write handling, and adjacent guards using the installed metadata.
- Reject saved-alias collisions against all 394 actual native mail aliases and
  between imported names. Flossie and Annalise recover their full names. The
  final source-reconstruction check also verifies all twenty phrase references
  are unique and disjoint from the original translated default keys.
- Compare both aloha shirts against every original N64 garment; neither matches.
- Execute the actual unchanged format-2 codec: accept the preceding subset profile,
  encode against an independent reference, reject the new profile under the older
  selection without writing, and accept the new profile under the new selection.
- Verify exact allowed cartridge changes, retained file locations and sizes,
  startup CRC, ROM checksum, and complete UPS reconstruction.

## Native execution

The first silent isolated run passes all 168 records / 90 assertions:

```sh
python3 tools/emulator_smoke.py --rom build/v3-all-villager-text-01/animal-forest-v3-asset-loader.z64 --output build/v3-complete-text-native-01 --xvfb /home/discordian/Games/OpenRSC/headless/vendor/usr/bin/Xvfb --expansion-pak --no-initial-screenshot --scenario tests/v3-complete-text-native.json --seconds 240 --port 19386
```

Results: `build/v3-complete-text-native-01/results.json`, SHA-256
`c7bdb2341f0234e456299812130f44e7ff85e4ee2e2979b12bc1b795e525a645`.

The representative roster is O'Hare, Flossie, Annalise, and Plucky: apostrophe,
seven/eight-byte names, and the longest new phrase. The actual name/actor-name
readers, six-byte writer, native reset and setter, full default/borrowed phrase
readers, and real dialogue insertions pass. Native/original/special fallbacks,
short-output rejection, the complete immutable prefix, all 864 saved-state bytes,
stack/fixture/translation guards, and fault checks pass. The checkpoint restores,
the game remains running, and the emulator shuts down cleanly.

This is not ordinary villager arrival or a full save/restart/load test. No physical
audio is played. The unchanged new-instrument playback issue remains unresolved;
it is not retried by this text check.

## Next work and compatibility

Import the actual `241A` and `241B` aloha shirts, then connect islander default
initialization, houses, and explicit town behaviour. All eighteen retain their
donor islander permission and incomplete-outfit zero field; none becomes eligible
for ordinary move-in merely because its name is installed.

The expanded text profile is a new dependency set, not a new save layout. Earlier
pilot-only V3 builds reject saves written with it; V2 must not load imported saves.
The codec accepts the preceding subset, but ordinary cross-build loading is not
claimed. Preserve all existing user saves and use separate test saves.
Both web patchers stay V2 pending user testing and explicit approval. Only V3
development source is pushed to `v3/optional-imports`.
