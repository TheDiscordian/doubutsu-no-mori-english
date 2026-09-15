# Islander arrival-house checkpoint

## Output

ABI 56 installs all eighteen authentic islander arrival rooms alongside the
two complete pilot houses, with existing native furnishings and exact matching
wall/floor artwork. The [specification](../../specs/V3_ISLANDER_HOUSES.md)
records the arrival-versus-gift-layout distinction, padding conversion, and memory.

- ROM: `build/v3-islander-houses-02/animal-forest-v3-asset-loader.z64`.
- ROM SHA-256: `e18e7ce0e52a745dbffc964b9c38122d11e0ac6a38433377ed9098c760c861b7`.
- UPS: `build/v3-islander-houses-02/asset-loader.ups`.
- UPS SHA-256: `a0c077f3ba12a54031d9d24bbe444c120ab762db0ea545ea8ce9d984a2e5c814`.
- House-table SHA-256: `55e00e3a3da85a9f0a59d25a5e0c12e9da0a3e92f0842cfba4d933a0dd35b2be`.
- Foreground SHA-256: `24cc2f7566a38653ba9a7893e0c58fcb76688df4a5982dd21a34223a22d00dcb`.
- Blob SHA-256: `8c3584ff19bdd1c5b3f0f0fd5dc64ace097843bd9be547cac45fcbd12781628f`.

Construction: `python3 tools/v3_islander_houses.py --output build/v3-islander-houses-02`.
The initial `-01` artifact has the same cartridge hash; `-02` completes the
build report's forty appended-layer records and remaining-work fields before
native verification. Neither is a full V3 playtest handoff; move-ins remain off.

## Focused verification

`python3 -m unittest tests.test_v3_islander_houses -v` passes all five tests in
13.031 seconds:

- Reconstruct every arrival room from the pinned donor, including complete
  wall/floor comparisons and all eighteen reviewed furniture identities.
- Preserve original and pilot house records and foreground layers; apply all
  eighteen new records and thirty-six layers into fixed slots.
- Retain furniture positions/orientations and exact outside-room padding masks;
  reject island gift placeholders and avoid importing furnished wishlist rooms.
- Verify both foreground address operands, unchanged resident runtime/profile,
  actual allocation growth, shared read-only storage, and sparse-table bounds.
- Compare every permitted physical write, retain other file locations, validate
  startup/ROM checksums, and reconstruct the complete cartridge from its UPS.

## Native verification

The first combined silent run passes on the corrected complete report:

```sh
python3 tools/emulator_smoke.py --rom build/v3-islander-houses-02/animal-forest-v3-asset-loader.z64 --output build/v3-islander-houses-native-01 --xvfb /home/discordian/Games/OpenRSC/headless/vendor/usr/bin/Xvfb --expansion-pak --no-initial-screenshot --scenario tests/v3-islander-houses-native.json --seconds 240 --port 19386
```

The reused native house fixture loads all forty appended layers from the new
physical location and validates all 498 pointers. It initialises four complete
NPC house records (native, Maelle, Ankha, Punchy), retains the source animals,
and executes actual main/secondary selection and full transfers for three
imported rooms. The immutable foreground, resident prefix, fixture/stack/module
guards, restored globals, fault checks, and checkpoint restoration pass.
There are 57 records and 35 passing assertions. Results:
`build/v3-islander-houses-native-01/results.json`, SHA-256
`b8b8506c35b9594d9d556fc0e4b77a90f66bd607ed1902181b69b91724e41966`.

The fixture uses 36 KiB temporarily; it does not duplicate the complete scene
foreground while the title owns its heap. Actual ordinary house visits and the
scene's increased 18,648-byte allocation remain unverified, not passed by
inference. No user save is loaded or changed, no physical audio is emitted, and
the unrelated new-instrument playback issue is not retried.

## Next work and compatibility

Integrate explicit ordinary-town behaviour and remaining gameplay readers, then
test combined arrivals, visits, and persistence. The aloha items still need their
display/catalogue/acquisition consumers. Keep the audio issue explicit.
ABI 55 and ABI 56 have identical save profiles and formats, but ordinary
cross-build loading is not newly verified. Preserve existing saves and use
disposable copies. Both web patchers stay V2; only development source is pushed
to `v3/optional-imports` until user testing and explicit approval.
