# V3 initial-default checkpoint

## Delivered development batch

`build/v3-villager-defaults-01/animal-forest-v3-asset-loader.z64` installs
Cheri's verified starting defaults through all three native initialization
entries, plus bounded personality lookup for Cheri and Punchy. It retains
the pilot artwork, draw, audio, and full-name/phrase integrations. No villager
is enabled for move-ins and no web-patcher change is made.

| Artifact | SHA-256 |
| --- | --- |
| ROM, 32 MiB | `8eb997c4115f851f03a40b986ed083fd095d9152e9db6aee682ebcd499dae55b` |
| Adjacent `asset-loader.ups` | `06dfcfd3ae484eeb37b81e9feb9a7b60b73918e8c569dba2d20b4f49e1ccb5f1` |
| Complete V3 blob | `5477a2ec1bb73ad31b8efe344aa8f6f7e89e37af7fe719aa59a43dede9ae9f1d` |

Build reports bind complete sources, donor resources, clothing mappings, hooks,
compiler output, CRC, and UPS reconstruction. The text/default helper is 1,536
bytes at `80464000`; individual helper frames are at most 24 bytes, with nested
and delegated calls additionally checked against native fixture stack guards.
The ABI-4 blob remains 32 KiB, original heap growth is zero, and the
translation-only composition still returns exact stable V2-11.

## Identity result and implementation

All 1,024 decoded pixels of Cheri's yellow bar shirt match native `2498`, uniquely
among 256 native shirts. Both complete converted texture and palette match their
native records. The builder retains the complete native clothing banks.
Punchy's cherry shirt (`24BF`) matches none of those native colour images. His
starting defaults remain unavailable pending a real additive clothing import;
the code does not give him the different native item sharing that number.

Four new native hooks use guarded return bridges at `80462F40..80462F7F`.
Imported initialization does not index the original defaults array or pass a
GameCube phrase index to a native string loader. Cheri receives her stable actor
ID, peppy personality, verified shirt, full-phrase reference, and current hometown.
Every unrelated byte in the saved animal structure is retained. Native ordinary
and test defaults continue through their original code, with the indexed route
retaining its original test-ID exclusion. Missing/incomplete imports are no-write.

The [specification](../../specs/V3_VILLAGER_DEFAULTS.md) documents field offsets,
clothing conversion, the original table's two real test records, and saved-value
limits. Metadata now stores the verified native shirt in its final two bytes.

## Verification

`python3 -m unittest tests.test_v3_villager_text -v` passes **six tests**, no skips,
in 1.361 seconds. These cover sanitized host text/default contracts, original
fallback and missing-input guards, ABI-4 startup/cache bounds, complete installed
metadata/code/bridges, actual clothing dependency gating, source hashes, retained
native resources, full patch reconstruction, and import-free V2 retention.

`build/v3-villager-defaults-native-02/` completes **69 recorded steps**, exit 0,
on this exact current cartridge, using private Xvfb with audio disabled and no
seed save. FlashRAM/Pak writing is not enabled. Native checks include:

- All three Cheri initialization entries, comparing the complete animal buffer
  against exactly the permitted writes, including untouched name-ID/other fields.
- Initialized identity and phrase reaching the shared English dialogue readers.
- Both imported personalities, original/test personality fallback, and invalid IDs.
- No destination changes for missing imports or Punchy's pending outfit, through
  each initialization route.
- All three original initialization routes, including a full-table test villager,
  with the actual native default/string DMA path retained.
- Actual complete native 512-byte yellow-bar texture and 32-byte palette DMA.
- All actor, animal, output, defaults-table, clothing, and stack guards; complete
  immutable blob, translation guard, unchanged land source, and no faulted thread.
- Mandatory checkpoint restore, resumed game operation, and clean shutdown.

Results SHA-256:
`81da2fcbefca85d757f4f3bf3dd30769ad80c50825a2f600d339c1e757c79ad8`.
Run receipt SHA-256:
`4503b09badaa8987a03635f92fa3f37f6755d48b9271f941b2770984b545fb75`.

The initial native attempt, `v3-villager-defaults-native-01`, passed the functional
checks but failed its lower stack guard. The fixture placed that guard at
`8019C080` inside its own clothing output `8019BEE0..8019C0DF`. The observed
guard hash exactly matches the expected texture slice at offset 416. This is a
verified test-buffer overlap, not evidence of a game stack overwrite. Moving the
clothing fixture to `8019B610` and palette to `8019B830` permits the one justified
retry above, which passes. No cartridge code changes between those attempts.
The first attempt remains recorded separately, not relabelled as passed.

Existing native audio/draw and shared borrowed-phrase evidence remains applicable
to unchanged implementations; no historical cartridge is replayed. These are
component checks, not an ordinary move-in, full NPC construction, house visit,
save/reload, or original-hardware acceptance.

## Next work and compatibility

Continue Cheri's house/layout data and remaining bounded identity/selection
readers, then ordinary town gameplay and profile-aware persistence. Punchy's
cherry-shirt import is an explicit clothing dependency. Umbrella asset identity
and ordinary rain handling remain to be connected/verified; the native saved
animal does not have the donor's saved umbrella byte.

The existing V3-only default references do not enlarge saved fields, but saves
containing them require compatible V3 metadata and must not be loaded in V2.
Imported ordinary save/profile handling remains unfinished. Development uses
disposable saves; user saves and prior cartridges remain preserved.

V3 source can be pushed to GitHub. Public and local patchers stay V2 until the
user tests V3 and explicitly approves switching the patcher. This batch is not
a public release or a playable-import handoff.
