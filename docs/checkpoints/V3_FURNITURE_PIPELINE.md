# Automatic furniture pipeline checkpoint

## Shared material-trigger profile integration

ABI 170 at `build/v3-material-trigger-profiles-02/` stages three complete
ordinary records through the shared furniture-profile installer: coin `3314`,
? block `3318`, and fire flower `332C`. Their actual installed material renderer,
switch-trigger moves, complete artwork, official names, and prices are bound
together. No per-item installation script or graphics recompilation is added.
The existing six-object prepared bundle is the input; the three other objects
are explicitly deferred because their lifecycles remain incomplete.

The first build rejects the mixed bundle because the profile inventory omitted
legacy `1xxx` resources. The shared inventory now includes unmapped legacy source
rows, allowing full validation and an explicit pending result for Mouth of Truth.
This does not enable its destination or bypass its unfinished behaviour. The
second build succeeds without changing any prior candidate or input.

The three new native profiles have null generic model/rig fields and point to
the shared material vtable. Their sound/material records agree on identity and
installed lifecycle. Profile flags and saved selection bits remain zero.
The ordinary importer checks these bindings before moving on to the real missing
acquisition route. A renderer-only record, missing move binding, or absent sound
profile flag still fails. Source artwork descriptors stay reusable and unchanged.

Three `MaterialProfileIntegrationTests` pass on the first invocation in 16.737
seconds. They verify complete profiles, official names/prices, inactive bits,
unchanged old tables, exact artwork/runtime reuse, pending lifecycle refusal,
metadata reaching acquisition, unchanged saves, all/empty composition, and UPS
reconstruction. There is no new emulator run: the complete equipment module,
shared packet, artwork, and audio are identical to ABI 169, whose passing native
audio/relocation evidence is retained. This is not a new native GPU or ordinary
furniture-interaction result.

There are 26 staged profiles and 136 selectable choices. Import blob size stays
4,360,256 bytes; free space stays 1,931,200 bytes. RAM, saved format 3, selection
requirements, main ABI-109 lock, and both served V2 patchers are unchanged.
Acquisition, the other pending lifecycles, and ordinary gameplay remain required.
Primary import support still precedes required gold-tree completion.

```sh
python3 tools/v3_furniture_install.py --refresh-runtime \
  --base-lock build/v3-material-trigger-runtime-04/build-lock.json \
  --furniture-profiles build/v3-material-frames-prepared-01 \
  --output build/material-profile-reproduction
PYTHONPATH=tests python3 -m unittest test_v3_room_materials.MaterialProfileIntegrationTests -v
```

- ROM SHA-256: `c903f37ddc6165f9dec0bcf2f1c9483d7472c5e252a1e80f04aecdb6df05c253`.
- UPS SHA-256: `d303d24f507071b32002a85cd050215aa268b9d490d5350f50009084df2fbccf`.
- Report SHA-256: `b64a6a6d606db64e9366ee18f87bbb61a5c65c126150d2fbc234559ad67c7f66`.

## Incremental shared furniture audio

ABI 169 at `build/v3-material-trigger-runtime-04/` connects the existing
switch-trigger behaviour to the complete material drawing of coin, ? block,
and fire flower. The same complete move-function verifier serves ordinary and
custom-drawn furniture; no object-specific behaviour implementation is added.
`build/v3-material-trigger-audio-prepared-02/` contains their complete source
programs, instruments, and samples. All existing artwork is reused in place.

The importer accepts further audio batches. It verifies every existing table
entry and program, preserves mapped IDs/priorities, rejects occupied slots, and
reuses an already installed source program only if its complete binding agrees.
Eight sound objects now share the runtime, and the complete font has 82
instruments. The three new native words are bound from source `017A`, `017B`,
and `017F`; existing five mappings do not change. The shared room packet code
is unchanged from ABI 168. The material vtable gains the existing sound-move
entry, with complete lifecycle readiness recorded only for those three objects.
Ordinary profiles and acquisition remain pending; no new choices are enabled.

Complete wave storage grows by 25,920 bytes. Its in-place path encounters
unclaimed nonzero bytes after the current archive, followed by live overlays.
Those bytes are not discarded. The shared allocator moves the full 5,566,960-byte
archive to checked zero space at physical `032106B0`, preserving logical VROM
`01A50000`. All six wave headers and the real native base load are updated;
external wave two retains its absolute physical location. The old archive at
`03800000`, all scenery/menu overlays, and their relocation resources stay intact.

No audio heap growth is needed. Conservative permanent headroom is 352 bytes.
The import blob is 4,360,256 bytes, leaving 1,931,200 bytes in its reservation.
Saved format 3, selection bits, 136 choices, 26 rigs, 23 staged profiles, the
main ABI-109 lock, and both served V2 patchers remain unchanged.

Development build failures are retained:

- `v3-material-trigger-runtime-01`: discovery annotated the move receipt inside
  the artwork descriptor; installer correctly rejected the mismatch. Discovery
  now validates a copy, and preparation `-02` keeps graphics descriptors intact.
- `-02`: the first append reached additional installed scenery owners not in
  the old blocker inventory. Their complete receipts join the permitted owners.
- `-03`: the now-identified owners were not the only obstruction; nonzero
  unclaimed gap data also prevents an append. Complete zero-gap relocation
  supplies the general solution. No guard is removed or old data overwritten.
- `-04`: complete build and UPS reconstruction succeed.

Four `IncrementalBatchTests` pass on the first test invocation in 5.458 seconds.
They check shared non-mutating discovery, changed-source rejection, complete
retention of all 79 previous instruments, all three new instruments/programs,
all eight priorities and mappings, repeat dependency reuse without duplication,
changed-slot rejection, whole-wave relocation and every waveform group,
the actual base-load address, unchanged scenery owners, allocation, callback
bindings, saved profiles, all/empty composition, and full UPS reconstruction.

The first silent native check at `build/v3-material-trigger-native-01/` passes
75 records and 50 assertions, including 45 inside the shared audio probe.
It verifies actual relocated headers, native pools, full tables/programs,
all 82 loaded instruments and sample pointers, the newly mapped callback,
lazy-loaded packet, real priorities, singleton suppression, and sample DMA for
source `017A` and retained `8179`. The incremental probe selects its new batch
and omits the already-passing unchanged state-condition matrix. Work/stack
guards and saved profile remain intact; checkpoint restoration and clean exit
pass. Audio is disabled; no supplied save or write permission is used.

This does not prove ordinary furniture interaction, acquisition, material GPU
appearance, PCM/listening quality, or hardware behaviour. Retain those limits
while continuing primary profile/acquisition integration. Gold-tree effects and
full golden-shovel acquisition remain required afterwards.

Reproduction uses fresh output paths:

```sh
python3 tools/v3_furniture_pipeline.py convert --representation audio --assets-only \
  --category material-frame-assets \
  --base-lock build/v3-material-frames-runtime-02/build-lock.json \
  --output build/material-audio-preparation-reproduction
python3 tools/v3_furniture_install.py --refresh-runtime \
  --base-lock build/v3-material-frames-runtime-02/build-lock.json \
  --furniture-audio-art build/v3-material-trigger-audio-prepared-02 \
  --output build/material-audio-runtime-reproduction
PYTHONPATH=tests python3 -m unittest test_v3_furniture_audio.IncrementalBatchTests -v
```

Hashes:

- ROM: `e10f6628db63198a0a40efe3aec7711fc6eb0a250b189852be4dc1c701ba4a74`.
- UPS: `f95cd6cc70df42aacc90ce53c13d8e716729a703137f0389127c46edc05e8ed7`.
- Report: `b3c6cb9e20d90dde62e94e6b4b256998f299357cf8a9b946c1a5ed1323df0b47`.
- Native results: `170a9249b5eca7ebceb63060649166e7d970a8f6e37d2af34db92c0d32695ee9`.

## Shared material-frame renderer

ABI 168 at `build/v3-material-frames-runtime-02/` installs one data-driven renderer
and the complete six-object batch from `v3-material-frames-prepared-01`. All
17,104 artwork bytes are reused; no graphics compiler is run. The complete
draw callback, matrix helper, native actor bounds, switch field, room-owner
argument, and catalogue null-room contract are checked against the actual inputs.

The native packet contains 2,912 bytes of code within its existing 4-KiB code
space. Six 40-byte material rows and their header fit the existing table tail;
capacity is eleven rows. The bootstrap uses 793 bytes of its existing 1,536-byte
reservation. No resident allocation, model-bank size, actor stride, or saved
field grows. The import blob is 4,326,848 bytes, with 1,964,608 bytes remaining.

The renderer retains repeated palette entries, every full texture frame, source
model order, unsigned and signed division/wrapping, separate preview/room frame
selection, room switch stopping, and private-state faces. Mouth of Truth uses
reviewed additive destination `3C30`/1804, not donor index 1014 in the native
table. Worksheet row 2392 has no native identity/name/model/texture fields, and
neither approved translation mapping contains donor furniture `03F6`.

Four focused `test_v3_room_materials.py` checks pass on their first invocation
in 10.138 seconds. The sanitizer check executes the actual C renderer using all
six generated records, including unsigned wrap/signed division, room/preview
differences, both switch states, negative face-state inputs, full draw order,
complete immutable resources, crowded/misaligned arenas, malformed tables,
and actor guards. Cartridge checks compare the complete installed objects and
packet, retain every previous profile/resource/save, reject forged lifecycle
readiness, and reproduce the UPS, all-selected, and translation-only outputs.
`checks.log` records the result. The first build has identical ROM/patch content;
the second adds accurate adapter/artwork and pending-native report fields.

No native emulator run is claimed, and the failed title-screen allocation
fixture is not repeated. GPU appearance, actual effects/audio, and acquisition
remain pending. These six resources have no ordinary profiles or enabled choices.
The existing 136 choices, 26 room rigs, 23 staged profiles, saved format 3, main
ABI-109 lock, and both served V2 patchers remain unchanged. Gold-tree effects and
full golden-shovel acquisition remain required after primary import support.

Reproduction:

```sh
python3 tools/v3_furniture_install.py --refresh-runtime \
  --base-lock build/v3-shared-fixed-clock-profiles-01/build-lock.json \
  --material-frames-art build/v3-material-frames-prepared-01 \
  --output build/material-runtime-reproduction
python3 -m unittest discover -s tests -p test_v3_room_materials.py -v
```

Hashes:

- ROM: `8cb691cc707d506b0b1e4f16672f7863e3ec2871ff6122cd8c25271c2e8288fc`.
- UPS: `b93cc9c4eb13f18e6241a6a58d496d7f34049a813313c880cd0674befb6547a7`.
- Report: `700a38bf9d63e08fa1abdf91319c184fac25f2aa044f35606ad3ea93914505a6`.
- Native packet: `db470c489164483a3ce13fc97db647f1295a18c04a56a49a0dfcfdc83b9eb493`.

## Shared material-frame resource preparation

`build/v3-material-frames-prepared-01/` prepares six complete objects through the
ordinary bulk converter, with one compiler container and no native runtime
change. The build uses the ABI-167 proposal as its explicit base:

```sh
python3 tools/v3_furniture_pipeline.py convert --assets-only \
  --category material-frame-assets \
  --base-lock build/v3-shared-fixed-clock-profiles-01/build-lock.json \
  --output build/material-frame-reproduction
```

The batch succeeds on the first compiler invocation. The shared converter gains
typed dynamic texture/palette bindings, full frame-bank extraction, and exact
texture-off/on transitions; it does not flatten animation into a still model.
Full draw instructions, address pairs, bounded branches, helper targets, source
selectors, and complete frame tables establish each resource contract. The
graphics converter retains all original lists, texels, geometry, alpha, draw
order, and material commands. Lifecycle behaviour remains pending, not removed.

| Donor identity | Official name | Object bytes | Material selection retained |
| --- | --- | ---: | --- |
| `1FD8` | Mouth of Truth | 3,968 | Two face textures; actor-state low bit |
| `3298` | festive candle | 4,448 | Two flame textures; frame divided by two |
| `3314` | coin | 1,984 | Seven-entry palette sequence; frame divided by eight |
| `3318` | ? block | 3,168 | Seven-entry palette sequence; frame divided by eight |
| `331C` | starman | 1,120 | Four palettes; frame divided by ten; room switch gate |
| `332C` | fire flower | 2,416 | Four palettes; frame divided by twenty |

Total: 17,104 bytes. Coin/block duplicate palette entries remain in their
seven-entry sequences. Palette and texture resources are stored once, without
shortening those sequences. All time-driven selectors preserve the donor's
separate room and preview counter choice in their descriptors; N64 timing and
renderer integration are not installed by this resource preparation.

Manifest SHA-256:
`9deb0ce737d8e2c9824cfb6bbb3fb68b87a11f3302116eb532fcf10dfd0df8e2`.

Three `MaterialFrameResourceTests` and the existing dynamic-palette format check
pass. The first combined invocation reports three passes and one failed cache
lookup: the test requests `3010` from a bundle which actually contains `3020`.
That fixture key is corrected, then the affected complete-art test and the
extended invalid-binding test pass in 0.914 seconds. This is not a cartridge or
graphics failure. Passing unchanged checks are not replayed. `checks.log` keeps
the invocation/results record.

Checks compare every texture sample, complete palette conversion, vertex,
triangle, material/tile state, dynamic pointer, and texture enable transition.
They preserve frame-table repetition and draw order, reconstruct cached complete
objects, and reject changed code/calls/relocations, missing frame entries, wrong
material types, absent resources, invalid segments, and forged runtime readiness.
The unchanged static/translucent, fading, and keyframe categories still reuse
their existing complete cached objects. Official names are credited in
`translations/provenance.json`.

Native metadata/profile creation refuses these prepared-only objects. The shared
renderer, actual lifecycle behaviour (including sound, surprise/rumble, player
colour requests, and coordinated switches where present), and acquisition remain
required. No emulator is run for this resource-only change. The current ABI-167
cartridge, 136 experimental choices, saved format 3, main lock, and both served
V2 patchers remain unchanged. Primary importing still precedes required
gold-tree effects and full golden-shovel acquisition.

## Shared fixed and indexed clock integration

ABI 167 at `build/v3-shared-fixed-clock-profiles-01/` installs harvest clock's
complete rig through the existing shared clock runtime, then stages its ordinary
profile, official name, and price. There is no item-specific installer or runtime
branch. The native clock code is unchanged, SHA-256
`41f20bc9ba96b3b97770c1ae89317404fed83bc3fda385a58c40f02aef214bc2`.
The existing clock record parameters select hour/minute joints three/four.

Fixed resource discovery now promotes a clock only after proving the complete
move callback is one keyframe step, destroy is a no-op, and repeat initialization
has its actual source speed. The full donor initializer at `00000A24`, length
124, has SHA-256 `5c600ed1925e67be3f776252b5cb4617389ee5612133e188505d05ba28e3bd7c`.
All relocations and its `1.0`, `0.0`, integer-conversion, and `0.5` constants are
checked. Source initialization supplies `0.5` before the constructor's first
play, then the constructor reassigns `0.5`. Native initialization supplies `1.0`;
the existing adapter sets `0.5` before playback, producing the same first-frame
evaluation. Two source move steps per native update preserve running speed.
The complete source clock joint callbacks are already checked by discovery.

Preparation automatically skips current, verified staged profiles unless an
explicit selection requests them. Thus this shared-category invocation avoids
rebuilding all fifteen station clocks:

```sh
python3 tools/v3_furniture_pipeline.py convert --assets-only \
  --category indexed-loop-clock-rig \
  --base-lock build/v3-shared-translucent-imports-01/cartridge/build-lock.json \
  --reuse-assets build/v3-fixed-keyframe-rigs-prepared-01 \
  --output build/fixed-clock-reproduction
```

The recorded `build/v3-shared-fixed-clock-prepared-01/` contains one reused
3,744-byte object, with zero artwork compiler containers. Its fresh profile
records the verified clock category; the earlier prepared-only metadata does
not confer eligibility. Manifest SHA-256:
`090d9024e09291e49e7d29088433c7de9599e96c24f7c43b0452712b7bbabef1`.

The normal `tools/v3_furniture_install.py --refresh-runtime --room-rigs-art`
path installs the resource/table row at
`build/v3-shared-fixed-clock-runtime-01/` (ABI 166), then the same builder's
`--furniture-profiles` path produces the ABI-167 proposal. Both use the prepared
directory above and their preceding explicit build lock. Both succeed on the
first attempt. Complete asset storage uses checked retired space; the blob stays
4,309,744 bytes with 1,981,712 bytes free. There is no resident allocation growth.
The packet now has 26 rig rows; inactive furniture staging has 23 records.

Three focused current-build tests pass in 7.988 seconds:

```sh
python3 -m unittest tests.test_v3_room_rig_runtime.FixedClockIntegrationTests -v
```

The final build's `checks.log` records the result. Checks cover complete source
lifecycle/initializer dependencies and negative changes, reuse of the entire
original model/animation object, unchanged clock runtime code and previous
records/resources/audio, exact packet encoding, inactive readers/selection bits,
source acquisition rejection, complete UPS reconstruction, and full/empty
composition. Empty selection retains V2-12; all reproduces the current proposal.
The 136 selectable choices remain unchanged. No native replay is needed for
unchanged clock code; earlier native live-hand/timing evidence is retained, not
reported as a new test. This new model's ordinary gameplay, acquisition, GPU
appearance, persistence, and hardware remain unverified.

Final hashes:

- ROM SHA-256: `3a05ae197111405302e53b7e0f14800374897fc6dde15ac13d50bd9bb78171b6`.
- UPS SHA-256: `0ddba54385a9c3d5c5f79551eb9a49fe7b62ecfdffcee1566c7c6024d21f83b9`.
- Build report SHA-256: `9f8c877a2fee72a11bed6fdda1c2da0abf9ace624fa54147baa5f7833bbb3f51`.

Save format 3 and selected profile requirements are unchanged; this disabled
record adds no new saved identity requirement. Ordinary cross-build reload is
not newly tested. The main ABI-109 lock and both served V2 patchers remain
unchanged. Harvest acquisition remains a required dependency before activation.
Other fixed rigs retain their actual pending behaviours, and gold-tree effects
and full golden-shovel acquisition remain after primary importing.

## Shared static-callback resource preparation

The bulk importer prepares direct profile models independently of pending
move-only code. This is a shared structural category, not an item-name allowlist
or a decorative replacement for an interactive item. Complete model slots and
exactly one move callback are required. Custom drawing, creation, destruction,
DMA, and dynamic profile resources remain outside this category. Known complete
switch-sound callbacks keep their existing checked adapter.

```sh
python3 tools/v3_furniture_pipeline.py convert --assets-only \
  --category static-models-pending-move \
  --base-lock build/v3-shared-translucent-imports-01/cartridge/build-lock.json \
  --output build/static-callback-reproduction
```

`build/v3-static-callback-resources-prepared-01/` compiles four complete objects
in one existing Docker toolchain container, totalling 17,168 bytes:

| Donor | Official name | Bytes |
| --- | --- | ---: |
| `1FAC` | piggy bank | 3,472 |
| `31CC` | ukulele | 3,456 |
| `3244` | barbecue | 5,760 |
| `3324` | cannon | 4,480 |

Prepared manifest SHA-256:
`09cb8b27a921059ffc8bb357f7f73c75de018c98d8c1e9498623010bf380b93b`.

The single provenance catalogue records each official name's donor table/index
and encoded hash. Complete geometry, palettes, textures, material states, and
source profile scalars are preserved. The callback descriptor retains its source
symbol, offset, full function hash, relocations, and explicit pending status.
Prepared static artwork does not include or certify dynamically spawned effects,
the ukulele melody, piggy-bank money logic, or cannon/barbecue sound/effects.
Those remain required gameplay implementation, not optional omissions.

Unimplemented scale/contact/interaction fields can be preserved for this
prepared-only category, with explicit `pending_profile_fields`. Structural and
finite/bounds checks remain. Implemented categories still reject fields outside
their supported semantics. Metadata and native profile construction reject the
entire pending category, including forged installed-runtime annotations.
The complete-art cache can reuse these objects after a real behaviour category
is implemented; preparation never supplies a shortcut to installation.

Three focused tests pass in 0.806 seconds:

```sh
python3 -m unittest tests.test_v3_furniture_pipeline.PendingMoveResourceTests -v
```

The prepared directory's `checks.log` retains the output. Checks independently
compare every compiled model's vertices, triangles, textures, material state,
and native commands with the donor; validate complete cache reuse and name
credits; reject extra lifecycle/dynamic-texture dependencies; retain unsupported
fields without allowing installation; and reject malformed scale values.
The existing switch-sound category is checked for dispatch and guard retention
because its shared discovery path changes. No old cartridge, emulator, or
gameplay test is replayed.

No ROM is rebuilt and no import is enabled. ABI 165 remains the explicit
cartridge with 136 experimental choices and saved format 3. The main ABI-109
lock, saves, and both served patchers remain unchanged. Primary conversion,
behaviour, and acquisition work continues before required gold-tree completion.

## Shared fixed-keyframe resource preparation

`build/v3-fixed-keyframe-rigs-prepared-01/` contains four complete constructor
rigs prepared together by the ordinary importer. The discovery category checks
the full fixed constructor, actual stop/repeat helper, paired skeleton/motion
addresses, finite initial speed, and complete standard or live-clock drawing.
Resource records preserve initial playback before assigning speed; this differs
from some existing room callbacks and must not be silently reordered later.
Models, skeletons, motions, and names come from actual source bindings, not an
item-definition list. Complete constructor resources do not certify pending
move/destroy behaviour, sound, or dynamically spawned effects.

```sh
python3 tools/v3_furniture_pipeline.py convert --assets-only \
  --category fixed-keyframe-rig-assets \
  --base-lock build/v3-shared-translucent-imports-01/cartridge/build-lock.json \
  --output build/fixed-rig-reproduction
```

The recorded batch compiles all four objects in one existing Docker compiler
container, totalling 15,776 bytes. No graphics or animation arrays are reduced.

| Donor | Official name | Bytes | Joints/visible | Frames | Initial mode/speed |
| --- | --- | ---: | ---: | ---: | --- |
| `1FC4` | tiger bobblehead | 5,312 | 2/2 | 101 | stop / 0 |
| `3018` | stone coin | 3,168 | 3/2 | 100 | repeat / 0 |
| `32F0` | harvest clock | 3,744 | 5/3 | 13 | repeat / 0.5 |
| `33B8` | judge's bell | 3,552 | 7/4 | 10 | stop / 0.5 |

Official name sources are in the single provenance catalogue. The prepared
manifest SHA-256 is
`449eaaec63aa5a2acf2160714ac5ba5125744611e4c16c8ab9ecc61e506c60b9`.
The seven-joint bell is retained whole; the existing room runtime's six-joint
limit is not weakened. Its native work capacity remains an integration task.
The clock's actual before/after joint callbacks and common clock fields are
checked and recorded. Unknown extra drawing, including the torch's fire and
billboard dependencies, stays rejected rather than losing those effects.

`RESOURCE_CATEGORIES` permits preparation and complete suffix/cache handling.
The separate implemented `RIG_CATEGORIES` list does not include this category.
Ordinary metadata, profile construction, and room-resource installation all
refuse the prepared-only category. An alleged installed-runtime binding cannot
turn pending code into completed behaviour. Remaining callbacks retain their
actual source symbols, offsets, full-code hashes, and relocations, without a
claim that their semantics have been ported. Cache reuse regenerates current
profile/readiness records, so future category implementation can reuse complete
graphics and keyframes without inheriting a stale eligibility claim.

Three focused tests pass in 1.919 seconds:

```sh
python3 -m unittest tests.test_v3_furniture_rigs.FixedResourceTests -v
```

`checks.log` in the prepared directory retains the output. Checks cover every
new graphics resource, vertex/triangle/material, skeleton/motion pointer, and
complete animation array; stop/repeat and clock bindings; negative constructor,
drawer, relocation, speed, and joint-callback changes; complete cache reuse;
official-name credits; and all three installation gates. Changed pending move
code changes its recorded hash but remains explicitly unimplemented. The two
existing storage constructor categories are checked only for dispatch retention;
old cartridge, native, or gameplay suites are not replayed.

There is no ROM rebuild, new choice, saved-format change, or emulator run. ABI
165 remains the explicit proposal, the main ABI-109 lock is unchanged, and both
served patchers remain V2. Actual interactions, sounds/effects, acquisition, GPU
appearance, persistence, and hardware for these four objects are not established.
Continue primary categories/acquisition and reuse these complete resources when
their behaviour groups are integrated. Required gold-tree effects and full
golden-shovel acquisition follow the primary importing work.

## Shared IA16 and translucent materials

ABI 165 at `build/v3-shared-translucent-imports-01/cartridge/` adds complete
Moai statue artwork through the ordinary importer. The same shared converter
also prepares complete tissue and bottled-ship artwork; those two identities
remain unavailable until destination and acquisition work is complete. There
is no model-specific converter or installer, and no texture/effect reduction.

The material extension handles native IA16 textures using the donor's GX IA8
four-by-four blocks. Each source pixel stores alpha before intensity; native
output reverses the pair and untile order without reducing either channel.
The actual donor executable's format table at `800AAFC0` maps IA/16 to GX IA8.
Its complete texture-conversion function at `8004BBA8`, length `318`, confirms
the pair order and block layout. Corresponding decompiled code is
`local/ac-decomp/src/static/libforest/emu64/emu64.c`.

Two complete two-cycle transparency expressions are accepted by their command
words, `FC11FE04 FF0FF3FF` and `FC341604 5FFEFFF8`. Source primitive/environment
colours and alpha remain intact. Native compiler macros emit the expressions;
unknown expressions, extra texture dependencies, and conflicting formats still
reject. The shared material category also accepts the source fog/translucent
render mode `E200001C C81049D8`. Mixed CI4/IA8/IA16 models switch palette lookup
correctly and retain the upper TMEM palette region. The existing 2-KiB texture
limit remains in force.

Reproduce preparation with a fresh output directory:

```sh
python3 tools/v3_furniture_pipeline.py convert --assets-only \
  --category legacy-static \
  --base-lock build/v3-legacy-mapped-imports-03/build-lock.json \
  --reuse-assets build/v3-legacy-static-prepared-01 \
  --output build/legacy-materials-reproduction
```

The recorded `build/v3-legacy-materials-prepared-01/` batch contains eight
objects, 29,168 bytes: five unchanged cached objects and three newly compiled
objects in one compiler container. Tissue is 2,368 bytes, bottled ship 6,192,
and Moai statue 4,048. Every model, texture, vertex, triangle, and material is
retained. Official names have source entries in `translations/provenance.json`.
Prepared artwork cannot bypass the ordinary eligibility/installation checks.

Moai's actual non-dummy donor profile, missing native correspondence, absence
from approved existing mappings, and membership in `ftr_listJonason` establish
the reviewed ordinary souvenir identity. Its append-only reservation maps donor
`1FC8`/index 1010 to native `3C2C`/index 1803. The existing Gulliver reward route,
non-orderability, readers, placement, scoring, and optional composition consume
the shared source/destination records. Existing destinations are unchanged.

```sh
python3 tools/v3_furniture_pipeline.py import \
  --base-lock build/v3-legacy-mapped-imports-03/build-lock.json \
  --category legacy-static --reuse-assets build/v3-legacy-materials-prepared-01 \
  --output build/shared-translucent-reproduction
```

The ordinary import reuses Moai's complete compiled object, with no artwork
compiler container. The runtime builder succeeds on its first attempt. There
are 136 experimental choices: 20 villagers, 89 furniture, 24 equipment parents,
and three shirts. Four golden tools remain disabled. The blob is 4,309,744
bytes with 1,981,712 bytes free; no resident allocation or saved format changes.

Eight focused checks pass. Three format tests cover all 65,536 intensity/alpha
pairs, complete blocks, native stride/LUT handling, both expressions, and
negative format/dependency mutations. Two prepared-art/source tests independently
compare every converted pixel, palette, vertex, triangle, material command,
native pointer, and compiled texture state in the eight-object batch. They also
verify the actual donor format table and full texture-conversion function.
Three current-cartridge mapping tests pass in 6.631 seconds, covering source
metadata, installed destination records, acquisition, retained resources and
allocations, and four browser/offline profiles: empty, all, selected mapped
content with a villager, and that villager without the new batch. The final
mapping output is retained in
`build/v3-shared-translucent-imports-01/mapped-checks.log`.

The earlier mapping-test completion output was unavailable after session
continuation, so those three current-cartridge checks were run once with a
durable log. No native scenario, old cartridge, audio test, or prior gameplay
suite was replayed. The title-screen arena allocation failure recorded below
remains unresolved; this batch does not retry that setup or claim native
changed-item execution. Ordinary gameplay, GPU appearance, save/reload of these
new objects, and original hardware remain unverified.

Output hashes:

- ROM SHA-256: `65ee309b1e2b237e20f9d8b05fde28f53b7ab28782671a806f470963e4b4c71e`.
- UPS SHA-256: `de3c339e7c4b4aab814c47e6aa36185249e3cf45328da4a2745457a43b0079d8`.
- Build report SHA-256: `9d16acf6228de4a1489f9dc842712255d8fea2b0da54ba38b370744f3afdab88`.
- Prepared artwork manifest SHA-256: `4f043d4dcab4a3d503e6136aa050e9d5081a2b4c35841fd8540ba446e149ba45`.

Format 3 remains unchanged, but saves using the new destination require a
profile containing that item and cannot be loaded in older builds or V2. The
main ABI-109 lock and both served patchers remain unchanged. Continue primary
import categories and acquisition first; gold-tree leaf/cut effects and full
golden-shovel acquisition remain required afterwards.

## Shared source-to-destination mapping

ABI 164 at `build/v3-legacy-mapped-imports-03/` installs the supported ordinary
legacy souvenir category through the existing bulk importer. Source and native
indices are separate throughout conversion, cache reuse, names/prices, placement,
sound categories, scoring, catalogue framing, acquisition, and composition.
The seven literal registry reservations preserve native items, all garment
reservations, and existing balloon displays:

| Donor | N64 destination | Official name |
| --- | --- | --- |
| `1FA0` | `3C10` | shogi piece |
| `1FB4` | `3C14` | tribal mask |
| `1FD0` | `3C18` | pagoda |
| `1FD4` | `3C1C` | fishing bear |
| `1FDC` | `3C20` | Chinese lioness |
| `1FE0` | `3C24` | Tower of Pisa |
| `1FEC` | `3C28` | Tokyo Tower |

Identity review uses the pinned worksheet's complete missing native ID/name/
model/texture correspondence, actual non-dummy donor profiles and English names,
and absence from the approved native translation/dependency mapping. These are
ordinary souvenir objects, not parent/display aliases. The actual donor list
places all seven in `ftr_listJonason`; existing native Gulliver reward code uses
that shared route. Names retain their official credits in the single catalogue.
Other legacy identities, including paintings and chocolates, remain in review.

The batch reuses all seven complete cached models, 29,712 bytes total, without
an artwork compiler container. The normal runtime builder compiles its shared
code and installs profiles, names, prices, source placement/sound categories,
catalogue framing/non-orderability, HRA/feng-shui metadata, and selected reward
records. There is no per-item installer, behaviour script, or native scenario.
There are 135 experimental choices: 20 villagers, 88 furniture, 24 equipment,
and three shirts. The import blob is 4,305,696 bytes with 1,985,760 bytes free.
Resident allocations do not grow. Four golden-tool parents remain disabled.

The integration exposed two stale shared-builder guards. The catalogue now
validates and retains both existing pool increments: 64 bytes for inventory
joints and 384 for the balloon menu. The complete bed functions remain unchanged;
their guard now checks those five functions and all four expanded table bindings
instead of rejecting unrelated changes elsewhere in the room owner. Altered
bed functions still fail. Build attempts `01` and `02` stopped at those guards
before producing a cartridge; `03` is the completed proposal.

Reproduce with a fresh output directory:

```sh
python3 tools/v3_furniture_pipeline.py import \
  --base-lock build/v3-shared-room-profiles-02/build-lock.json \
  --category legacy-static --reuse-assets build/v3-legacy-static-prepared-01 \
  --output build/legacy-mapped-reproduction
```

Five focused checks pass in 27.742 seconds:

```sh
python3 -m unittest tests.test_v3_furniture_pipeline.LegacyDiscoveryTests \
  tests.test_v3_furniture_pipeline.MappedIdentityTests -v
```

They cover complete cached-art validation, reviewed identities, source tables,
new destination records, negative identity/function corruption, retained previous
assets/records/staging/equipment/saved format, unchanged native allocations, and
cartridge checksums. Three browser/offline cases (empty, all, mixed mapped items
with a dependent villager) agree, including selection-order independence. Empty
output remains the pinned V2-12 image; all reproduces the current V3 image.
No served website is updated or started by these checks.
The installed placement/scoring/saved-bit assertions are extended and their
affected source/destination check also passes in 3.729 seconds; unchanged
graphics and browser cases are not replayed.

Native verification is **incomplete**. The shared existing scenario at
`tests/scenarios/v3_furniture_batch.json` runs silently with isolated state and
an Expansion Pak. Both `build/v3-legacy-mapped-native-01/` and `-02/` pass startup,
placement-table/guard, and catalogue-framing-table/guard checks. The first native
test allocation requests 135,168 bytes and returns zero. The one justified retry
sizes the arena from actual owner/relocation extents, requests 112,496 bytes, and
also returns zero. Both stop before changed-item reader, model, acquisition, or
ownership execution. No save is written. This is an unsatisfied test allocation,
not evidence of a cartridge crash or successful gameplay. Do not replay the same
title-screen setup; retain missing execution evidence for a later combined
playable-context test. The shared probe also limits reward tests to changed
categories instead of replaying every earlier NPC route.

Output hashes:

- ROM SHA-256: `6b438d1481a84599de89a475119f2c0cc586b716cf018fc061f3f1045dade5ca`.
- UPS SHA-256: `37e9f9ba700e10e3d9b4f1f8854d731383789024643acf98382403ef790ba093`.
- Build report SHA-256: `121b800bb49b83b9531ef8473d5cb8877e9dceba5bd84e277dadde42dec826b5`.

Save format 3 is unchanged; saves using these additions require their selected
destinations and are not compatible with older builds or V2. Ordinary gameplay,
save/reload for the added items, GPU appearance, and original hardware remain
unverified. The ABI-109 main lock and both served patchers are unchanged. Required
gold-tree effects and golden-shovel acquisition follow primary import completion.

## Legacy donor discovery and bulk artwork

The ordinary pipeline includes all 148 `1xxx` worksheet entries whose four
native-correspondence fields are unresolved, as well as the existing 242 `3xxx`
entries. Four of those legacy records are already classified balloon displays.
Other records include dummy resources, fish/insect/umbrella/NES representations,
and ordinary furnishings; this is not a claim of 148 new imports. All remain in
review until actual representation and native identity are established. Legacy
metadata fails before any source profile index can be treated as an additive
N64 destination. Existing native items and registry reservations remain intact.

The supported static subset is prepared in one compiler batch:

```sh
python3 -B tools/v3_furniture_pipeline.py convert --assets-only \
  --category legacy-static \
  --base-lock build/v3-shared-room-profiles-02/build-lock.json \
  --output build/legacy-static-reproduction
```

`build/v3-legacy-static-prepared-01/` contains twelve complete objects totalling
46,272 bytes: basic/scary/quaint/classic paintings, shogi piece, chocolates,
tribal mask, pagoda, fishing bear, Chinese lioness, Tower of Pisa, and Tokyo Tower.
No new item-specific converter or model description is introduced. Full artwork,
source scalars, official name records, and pending mapping reasons remain in the
normal prepared format, reusable by the ordinary importer once prerequisites
are implemented. Their official name entries are in the single provenance
catalogue. Complete art receipt SHA-256:
`42ef9f99bd262c6840c0b2f50a661359157585d314b0c47eb3fc5cbf45252800`.

Two focused tests pass in 18.778 seconds. They check default discovery against
the full verified worksheet, retained `3xxx` rows, explicit alias/dummy handling,
all twelve source names, source-bound cache reconstruction, and installation/
destination rejection. The existing independent complete-artwork verifier checks
every texel, palette, vertex, and triangle in the new batch. No old cartridge or
native scenario is replayed: these changes prepare assets and broaden discovery,
not executable ROM consumers. The current ABI-163 ROM, choices, saves, main lock,
and both served patchers remain unchanged.

Continue identity review and shared additive mapping/metadata before enabling
these entries. Other legacy records retain their actual conversion/behaviour
gaps, including the holiday bottled ship's unsupported colour combiner. Required
gold-tree work remains after primary importing.

## Shared holiday reward preparation

`build/v3-holiday-rewards-prepared-02/` contains the complete donor holiday
program and a relocatable N64 o32 selection/handover kernel:

```sh
python3 -B tools/v3_furniture_pipeline.py convert \
  --representation rewards --assets-only --category holiday \
  --output build/holiday-reproduction
```

The compiler derives all 28 event rows and 65 candidate entries from the actual
donor's fixed gifts, complete selector jump table, random bounds, and code.
It checks complete function hashes and dependencies for gift selection, station
selection, furniture index conversion, pre-give, and give. The source branch
table's relocation targets are bound independently of its zero-filled raw data.
The output retains fifteen diary choices (the original off-by-one), fifteen
stations, nine flowers, Toy Day's gender-dependent pair, and every fixed gift.
The 370-byte `AFHG` table contains donor IDs, not invented native mappings.

The shared C kernel validates the complete table, exposes available variant
counts through a checked resolver, creates bounded transient offers, and
rechecks the source variant/native mapping/receipt before committing. Missing
or disabled items are unavailable; complete selections retain source variant
order/distribution. A failed pocket insertion never marks a trophy. Repeated
handover calls cannot award another gift after that player's receipt is marked.
The caller supplies the validated player, real normal-condition insertion,
catalogue registration, and existing format-3 trophy operations. No new saved
field is introduced by the kernel.

Three focused tests pass in 0.735 seconds. Complete source mutation checks
cover code, external/data dependencies, tables, random ranges, and changed
valid-looking selector targets. Address/undefined-behaviour sanitizers cover
all selector forms, complete and sparse choices, unrepresentable/out-of-range
requests, unchanged failed output, changed selection, tampered offers, duplicate
receipts, independent four-player state, full pockets, and malformed tables.
The actual Docker toolchain compiles a big-endian ELF32 MIPS relocatable object
with no unresolved external symbols. Stack reports show at most 80 bytes for
an individual kernel function, before caller/callback stack requirements.

No RAM address is assigned and no ROM is rebuilt: actor/calendar/dialogue,
selected native identity mappings, actual delivery-trigger bindings, catalogue/
scoring activation, and ordinary gameplay remain required. Native component
tests for an uninstalled kernel would not demonstrate those missing routes;
the current ABI-163 ROM and its accepted component evidence are retained.

Following the complete holiday program also exposed a discovery gap: bottled
ship `1FC0` is a gift with no reviewed native mapping, but the default furniture
scan covers `3xxx` and four explicitly known legacy balloon aliases. A source-
worksheet check finds other legacy entries requiring classification, including
ordinary furniture, dummy resources, and parent/display dependencies. They are
not automatically new furniture and must not overwrite same-numbered N64 items.
The primary queue now explicitly requires broad legacy discovery and stable
additive mapping after identity/representation review.

- Prepared receipt SHA-256: `375ec29617200dea9a4297ef4ab7925c2f23cd5bd169652fe4ebae9bfc9acbd2`.
- Complete program SHA-256: `474eb2e54e967b8f05de6f561ec4dac2eafa75711568e0013607f2e6998fb778`.
- Relocatable kernel SHA-256: `b1c0bc38c473705960d3638ff06af087e75b2749cdda9cedc0614ca5318d8147`.

No choices, ROMs, saves, main build lock, or served patchers change. Gold-tree
completion remains required after primary imports, not replaced by this work.

## Shared ordinary profile staging

ABI 163 at `build/v3-shared-room-profiles-02/build-lock.json` connects all
fifteen station clocks, both Harvest storage objects, and five sound-trigger
objects to fixed ordinary furniture profiles, official English names, and donor
prices through one shared adapter:

```sh
python3 -B tools/v3_furniture_install.py --refresh-runtime \
  --base-lock build/v3-furniture-trigger-runtime-03/build-lock.json \
  --furniture-profiles build/v3-indexed-clock-rigs-prepared-01 \
  --furniture-profiles build/v3-storage-rigs-prepared-01 \
  --furniture-profiles build/v3-switch-sound-prepared-01 \
  --output build/profile-reproduction
```

All seventeen complete rigs retain their VROMs and resources. The five complete
sound models add 12,352 bytes; the shared import reservation has 2,015,504 bytes
free. The complete room packet, equipment code, and audio resources remain
unchanged, and there is no extra resident allocation. The twenty-two official
names have source entries in the single `translations/provenance.json` catalogue.

Both profile/item enable flags and saved profile bits remain off. The native
initializer leaves their profile-table entries null, and their item readers
refuse access. This matters because the ordinary profile reader checks record
flags/pointers, not the saved selection bit independently. These are staged
integration records, not additional playable choices or acquisition substitutes.

The normal importer binds checked current lifecycle records before metadata
discovery. All 22 pass that prerequisite and stop at their real acquisition
gaps: two belong to `ftr_listHarvest`, and twenty have direct event/distribution
sources rather than a supported ordinary stock/reward list. The normal builder
can promote checked staged rows without duplicating their complete models once
the remaining acquisition/catalogue/scoring prerequisites exist. The importer
uses the same complete prepared-artwork validator for static objects and full
rig/motion suffixes. Shared room-category reservation guards read the furniture
selection bits at the correct blob offset (`0x20 + 32 + slot/8`).

Four focused host/cartridge tests pass in 14.807 seconds. They cover every new
inactive record, retained previous records and complete resources, all staged
reuse paths, refusal of changed bindings, actual acquisition gaps, the current
installed static batch's shared validator, individual name provenance, unchanged
128-choice composition, and exact no-import V2-12 output. The first host run's
resource comparison incorrectly treated the DMA directory's own file as
immutable; the corrected check permits only the four declared directory rows.
No cartridge correction was needed for that test setup error.

The silent native retry at `build/v3-shared-room-profiles-native-02/results.json`
passes 127 records and 112 assertions (107 inside the shared category check).
All 22 complete inactive records and null startup lookup pointers pass. One
representative per category is enabled only inside the paused fixture to check
the actual name, price, size, and profile readers and full profile-directed model
DMA. Disabled names perform no write. The fixture restores every temporary
record/pointer, retains the saved profile, passes guards, restores the checkpoint,
and exits cleanly. Existing clock/storage/audio behaviour checks are retained,
not rerun. Ordinary acquisition, room interaction, GPU appearance, save/restart,
and original hardware are not established by this component test.

The first native setup reached all 66 record/pointer comparisons, then attempted
a debugger call directly into upper RAM, which the harness forbids. The single
retry uses the existing checked low-memory jump-bridge pattern. The initial
failure remains at `build/v3-shared-room-profiles-native-01/`; it was a rejected
harness call, not a game exception. Test construction and correction stayed
within the 30-minute batch limit.

- ROM SHA-256: `c2f0eff4e5cf95b9bf91e72ecc83d3f14d1b04bebbb16a864585d8a78630ddb4`.
- UPS SHA-256: `f160ca28c43df12e12bfb4e5953b5904de5b0bf9177fef94287ecdf8fa3b58a7`.
- Build receipt SHA-256: `988cff3c5a5c2ec1d5c78b6df583f5493459c9289e7d72aa5caf382d552f5d94`.
- Native results SHA-256: `5c538e5059c29bd66bff4c8878bd557587db1f757a775d9704020274afa4e684`.

Format 3 and the selected profile are unchanged. Imported saves still require
their matching or compatible larger import profile; V2 and older formats are
not valid destinations. This is not a playtest-release handoff. The main
ABI-109 lock and both served patchers remain unchanged. Continue shared import
and acquisition categories before required gold-tree leaf/cut effects and full
golden-shovel acquisition; the four golden choices stay disabled.

## Shared furniture trigger audio runtime

ABI 162 at `build/v3-furniture-trigger-runtime-03/build-lock.json` installs all
five prepared furniture sound programs through the shared runtime refresh:

```sh
python3 -B tools/v3_furniture_install.py --refresh-runtime \
  --base-lock build/v3-clock-category-runtime-02/build-lock.json \
  --furniture-audio-art build/v3-furniture-trigger-audio-02 \
  --output build/v3-furniture-trigger-runtime-03
```

The complete 20,848-byte sequence contains extended 128-entry group-one and
group-four tables, retaining every previous entry/program. Priority-equivalent
slots map pipe `0178→016A` and mushroom `8179→816B`; the other three logical
IDs remain. The shared native priority table is unchanged. Complete source
callbacks determine all five records and retain excluded states 12–15, the
exact `changed==1` condition, actor position, and the owner's unchanged flag.
The shared room packet uses 1,880 code bytes and five sound rows in previously
unused table space; the bootstrap is 669 bytes. Its existing 8-KiB reservation
and the equipment allocation do not grow.

The first native check found a real donor/native difference: the N64 trigger
dispatcher ignores the `8000` single-instance flag. Its complete disassembly
confirms there is no duplicate check before free-slot allocation. The corrected
shared callback checks all six live native slots for the complete flagged word
before dispatch. This is a category rule, not a mushroom-specific installer.
The first check's 39 passing assertions and one failure remain recorded at
`build/v3-furniture-trigger-native-01/results.json`; that proposal is not current.

The complete 12,064-byte font retains 74 instruments and adds five; the complete
wave-five resource is 3,019,472 bytes. The wave group retains its complete prefix
and physical start at `03800000`, growing by 36,992 bytes. The shared allocator
moves complete owners `007829E0` and `03950000` into checked free tail space,
retaining their contents and virtual identities. It rejects unknown blockers,
nonzero unowned gaps, prefix changes, and virtual/physical overlap. Every changed
owner is extracted again from the final cartridge and compared in full.

The actual permanent-resource headers require 2 KiB more audio allocation.
Both malloc arguments and total/fixed/permanent pool settings grow together;
session capacity and the fixed remainder stay intact. Conservative permanent
headroom is 864 bytes. The import blob occupies 4,263,600 bytes, with 2,027,856
bytes free. No saved format, profile bit, selected option, main lock, or served
patcher changes. There remain 128 experimental choices; ordinary sound-object
profiles and source acquisition are not enabled by audio installation.

Seven focused audio checks and the shared room-category sanitizer check pass.
The initial complete-DMA-owner test incorrectly compared the DMA directory's own
owner against its pre-relocation contents; correcting that expectation passes
the affected check. After the actual singleton correction, the three current
cartridge tests pass in 6.094 seconds and the affected sanitizer check in 0.480
seconds. Checks include complete original resource retention, source priorities,
all five timings/envelopes/flags, guarded state dispatch, all six duplicate
positions, unchanged saves/choices, empty/full composition, and UPS reconstruction.

The corrected silent native run at `build/v3-furniture-trigger-native-02/`
passes 93 records and 61 assertions, with a restored checkpoint and clean exit.
It verifies actual resource headers and all three allocation pools, every new
program and both complete tables, full native relocation of all 79 instruments,
lazy-loaded callback code, rejected states, untouched actor memory, and guards.
Two representatives then use the real positioned sound callback and native
dispatcher, preserve their priorities, transfer actual donor sample data, and
verify singleton suppression. The callback condition checks use an isolated
argument recorder; actual playback checks restore the original dispatcher.
No existing save is used, no FlashRAM write is requested, and no physical audio
is played. Ordinary room interaction, acquisition, full PCM/listening, and
original hardware remain unverified. Retain these components without replaying
unchanged audio during the acquisition batch.

- ROM SHA-256: `6e3780d606d0d548736071331524374c894f0b1e8992ec7b664232eabaedf927`.
- UPS SHA-256: `d9c99a9d536399661886ccb407f341a03e4341246f44d1b8a45adec98ca3e83a`.
- Build receipt SHA-256: `92739671a1d2f3aafff9d91bb195740383175fba7681dccfa630beafce93dc78`.
- Native results SHA-256: `df144c0bdb7fd3cf0ee069220552f8c202e0cd90e89ebeb329c3f2b13b13624e`.

Continue shared profiles/acquisition and remaining bulk import categories.
Required gold-tree leaf/cut effects and full golden-shovel acquisition follow
primary importing. This is not a V3 playtest handoff or public release.

The following importer-only update repairs a stale ordinary furniture preflight:
`audio_contract` assumed chair sounds still used their original table/font
addresses. The actual complete resources are retained after the audio batch.
The check now resolves current headers and tables and verifies complete original
instrument/sample/envelope/tuning identity, programme bytes, and binding. One
focused current-cartridge test passes in 1.019 seconds, accepting all four
unchanged chair sounds and rejecting a deliberately corrupted dispatch entry.
No cartridge bytes change; no additional emulator run is needed.

## Shared furniture trigger audio preparation

`build/v3-furniture-trigger-audio-02/` prepares complete audio for the five
source-discovered sound-triggered objects: green pipe, flagpole, super mushroom,
koopa shell, and noisemaker. The shared pipeline selects records by callback
category, not an item list:

```sh
python3 -B tools/v3_furniture_pipeline.py convert \
  --representation audio --assets-only --category switch-trigger-sound \
  --base-lock build/v3-clock-category-runtime-02/build-lock.json \
  --output build/v3-furniture-trigger-audio-02
```

All five instruments are absent from the current native sound fonts; matching
sound numbers do not supply the missing samples. The generic converter retains
complete note programs and instruments, adding five source instruments to font
140 while preserving all 74 existing entries. The pointer table grows by 32
bytes, and every original bank-relative pointer follows; wave offsets and tuning
remain unchanged. Shared complete resources are deduplicated. The pipe retains
all three notes; the mushroom retains its `8000` single-instance flag.

The complete font is 12,064 bytes (784 bytes larger); the complete wave resource
is 3,019,472 bytes (36,992 bytes larger). Five relocatable programs are 17, 11,
11, 33, and 11 bytes, including all original source padding. The aligned font
allocation grows by 768 bytes. Current permanent audio headroom is 192 bytes,
so at least 576 additional bytes are needed before adding sequence/table growth.
No native sound ID, header, priority, heap setting, or callback changes yet.

Four focused checks pass in 0.582 seconds. They cover complete repeated-note
retention and malformed-program rejection; synthetic three-range instruments,
pointer-table growth, resource deduplication, deterministic source ordering, and
malformed-font rejection; all five actual programs/instruments, complete source
reconstruction, every existing instrument/sample retained, and singleton flags;
and changed cartridge/interpreter or unsupported sound-group rejection. The
final aligned-capacity accounting change reruns only its affected check, passing
in 0.225 seconds. The final source-receipt output has identical generated audio
to the first output. No emulator, historical build, or audible test is run: the
current cartridge is unchanged.

- Manifest SHA-256:
  `0a0825a9ee3a4078e6dc134658aa4372ca29fbbbad5b5170f5fef8beb9e6935a`.
- Complete prepared font SHA-256:
  `7cd1ba7d21ff562822c736b2a6428b26dddbc5b7da84a8c95d4bd4f503a7d2a0`.
- Complete prepared wave SHA-256:
  `f21c37a316bcd4592961f2712e226cbc9510c6316c99cf1b93476f16058b3efa`.

Next integrate shared native trigger slots and source priorities, expanded
permanent allocation, complete physical audio resources, and one move callback
for the category. Donor IDs cannot be copied directly: they exceed the reviewed
native group-one/group-four tables, where unchecked reads reach unrelated data. Preserve original
programs and the source single-instance flag through the mapping. Ordinary
profiles/acquisition remain separate work. ABI 161, 128 experimental choices,
saved format 3, the main lock, and both served patchers remain unchanged. Required
gold-tree completion stays after the primary importing work.

## Bulk storage and complete clock installation

The explicit proposal is ABI 161 at
`build/v3-clock-category-runtime-02/build-lock.json`. The shared importer expands
its checked contiguous reservation from `02200000..025EFFFF` to
`02200000..027FFFFF`, then installs all fifteen complete prepared clocks through
the same room-category installer. The blob occupies 4,230,688 bytes, leaving
2,060,768 free. Complete clock models/motions occupy 104,720 bytes. The 25-row room
packet retains the eight balloons and two storage rigs; its engine and 8-KiB
resident reservation do not grow. No assets are recompiled, reduced, or dropped.
Ordinary clock/storage profiles and acquisition remain pending, so these records
do not add selectable choices.

English choices and general strings retain their complete text, offset tables,
directory indices, and physical locations. Only their virtual bases and verified
native base-load pairs move, to `029E0000` and `029F0000`. The directory remains
3,389 entries with its sole terminator; no new entry is consumed. Both complete
native functions and every matching native-core upper-half load are checked.
Future batches must validate the relocated resources/readers to use the expanded
bound. The module at `02800000` and unrelated resources remain intact.

The initial combined check exposed a real final-string DMA failure: the last
five-byte string requires an eight-byte native transfer, crossing its unpadded
resource end. The corrected capacity adapter extends the declared end by three
verified zero bytes. It rejects occupied/nonzero/out-of-ROM padding and preserves
all text and offsets. The failing proposals remain diagnostic artifacts, not
current build locks or handoffs.

Four focused tests pass in 7.775 seconds:

```sh
python3 -B -m unittest discover -s tests -p test_v3_resource_capacity.py -v
```

They verify complete text/core/directory and unrelated-resource retention;
changed consumer, occupied destination, and forged-bound rejection; all fifteen
complete clock objects and descriptors beyond the legacy limit; unchanged room
engine, save runtime, existing artwork, and zero ordinary profile slots; full UPS
reconstruction; and unchanged 128-choice composition with exact all/empty output.

Native evidence is bounded and accumulated without replaying passed prefixes:

- `build/v3-bulk-storage-native-01/` stops at a test-only call-permission error.
  The corrected test uses the ordinary native text loaders.
- `build/v3-bulk-storage-native-02/` passes thirteen assertions covering choices,
  general strings, addresses, invalid choice rejection, and buffer guards before
  reaching the real final-string DMA defect. Those passed components are retained;
  this run is not a complete pass.
- `build/v3-bulk-storage-native-03/` uses the corrected ABI-161 cartridge and
  resumes at the final string, then runs the new clock category. It passes all
  200 records / 153 assertions, with zero failed assertions and graceful exit.
  The three source-rig representatives execute complete native model/motion DMA,
  lazy packet loading, independent construction, source half-step timing, live
  hour/minute Z-angle subtraction and wrapping, and complete skeleton drawing.
  Matrix/work/graphics guards, the full 912-byte save/profile state, restored live
  fields, restored emulator checkpoint, CPU/module/save guards, and exit pass.

The focused scenario is generated from the existing storage generator, keeping
setup plus the failed boundary and subsequent untested category. No new per-item
scenario or historical-build replay is used. All emulation is silent, isolated,
and time bounded. A restored checkpoint is not a game save/restart test. Ordinary
acquisition, room interaction, GPU appearance, and hardware remain unverified.

- ROM SHA-256:
  `f08a670cb3b59d87d3ca9a3a40e5e41730353e7ce42cb36daa677a837294738b`.
- UPS SHA-256:
  `eac927a707c529827311b58280ba05127ee50ae0ee82f445643a9edc8008327f`.
- Build receipt SHA-256:
  `5972cb292b89f8eb3232b01211b35c0e243c0647519df90f4966535054962c2a`.
- Focused native results SHA-256:
  `ba00b15a67eed9f89511367d26bdc92cb5f167a11d6c4853d5f0ced6c89c83ff`.

Saved format 3 and selected identities remain unchanged from ABI 159; cross-build
ordinary reload is unverified. Imported saves still require a matching or larger
profile and must not be loaded in V2/older formats. The main ABI-109 lock and both
served patchers remain unchanged. Continue primary shared conversion/integration
and acquisition, then complete the required gold-tree leaf/cut effects and full
golden-shovel acquisition. Golden choices remain disabled until their route works.

## Shared room-category runtime

The recorded ABI-159 proposal is at
`build/v3-room-categories-runtime-03/build-lock.json`. It extends the shared
room engine for switch-driven rigs, clocks, and native storage callbacks.
The same records/validator/compiler serve all three categories. Both complete
Harvest storage objects join the eight retained balloon rows; their ordinary
profiles/acquisition remain disabled. Clock descriptors and behaviour are
supported, but complete clock resources are not installed yet.

The 1,576-byte engine and up to 128 twenty-four-byte records occupy a checked
8-KiB packet at `804B8000`. A 545-byte bootstrap replaces the old room code and
retains the stable vtable. Startup clears its checksum cache; the first callback
loads and validates the complete packet before execution. Existing scene actors,
model banks, profiles, selections, and saved formats do not grow or change.
The packet and 9,568 bytes of storage artwork reuse a verified retired module;
the contiguous import resource still has 2,800 bytes free.

Five focused checks pass: category behaviour under address/undefined-behaviour
sanitizers; complete packet/code/assets/patch reconstruction and retained data;
128-entry encoding with a 25-row mixed-category fixture; unchanged 128-choice
composition with exact import-free/full outputs; and parent-alias retention plus
complete native storage profile generation. The final source-receipt build
produces the same cartridge as the tested build, so unchanged native evidence
applies without replaying it.

The first silent emulator attempt stops on an overbroad whole-module comparison.
The corrected retry records differences only at the scenery cache `804ADFEC`
and the live balloon-actor descriptor word `804AEA5C`. The new room reservation
matches in full. `build/v3-room-categories-native-02/results.json` records 120
steps and 96 passing assertions, including 92 component assertions: both complete
asset transfers, actual lazy DMA/checksum loading, native stop-mode construction,
independent actor state, complete skeleton drawing, matrix/graphics/work guards,
null-room storage suppression, unchanged save/profile prefix, and restoration.
After checkpoint restoration, CPU and module guards pass. The final scenario
check incorrectly uses format-2 guard address `8046C350`; format 3 uses
`8046C380`, and the former address is now reward-state storage. The test and
full-state comparison are corrected, but no third run is made. This is passing
component evidence, **not** a complete scenario/exit verification. Ordinary
opening/closing, acquisition, GPU appearance, and hardware remain unverified.
No save is supplied, written, or modified.

- ROM SHA-256:
  `ed2122947445b3f1f76c452535303780f6f2eb5808a66de34b9494e7ed759e46`.
- UPS SHA-256:
  `0b3d27574f4ba2572b3fa7abf3a0c41475b6dfa7933f49350c122629e70a3f2f`.
- Final receipt SHA-256:
  `593c8cc033d93251e23f30c6113893048b635e45fe55be65e325d44997530de4`.
- Native component results SHA-256:
  `ecc8fba65e722d217be91a348040595abc5d5028e1f312073b9cb9d98e79cef4`.

The bulk-storage checkpoint above closes this batch's storage dependency while
preserving its completed component evidence. Ordinary storage interaction and
acquisition remain separate work.

## Open/close storage category

`build/v3-storage-rigs-prepared-01/` contains the complete Harvest bureau and
dresser, 4,864 and 4,704 bytes respectively, compiled together in one container.
Shared source discovery retains the actual storage flags, stop-mode skeletons,
opening limits, and nullable room callback. The bureau has five joints/three
visible lists and a twelve-frame motion; the dresser has three joints/two visible
lists and a ten-frame motion. Neither animation is flattened or truncated.

- Manifest SHA-256:
  `6973affeda63d9d2753b628fdca0b6733e81bdbfbdf71f77e1c5b9d696b8082b`.
- Two focused tests pass in 1.780 seconds: source behaviour/dependency guards,
  non-finite limit rejection, complete graphics/keyframe comparisons, prepared
  cache reuse, and refusal to install unfinished resources as ready items.
- No emulator replay, ROM change, save change, choice, or patcher update.

The native room engine has the corresponding shared opening/closing callback;
connecting that category and its actual acquisition route remains work. There
are 69 prepared records among the 101 remaining non-alias, non-dummy furniture
candidates. ABI 158 remains the current explicit cartridge. Gold-tree completion
follows the primary importing work and remains required.

## Switch-triggered sound category

`build/v3-switch-sound-prepared-01/` prepares green pipe, flagpole, super mushroom,
koopa shell, and noisemaker in one compiler container. The shared category derives
all profile models and the move-only sound rule from source, without per-item
production definitions. Objects occupy 2,288, 2,144, 2,144, 3,312, and 2,464 bytes.

Two complete 88/92-byte callback forms retain the source actor-state exclusions,
switch equality, positioned sound call, and full sound word. The mushroom's
`8179` singleton encoding is not truncated to `0179`. Profile geometry keeps all
opaque layers; the callback is not silently removed. Other lifecycle/draw/DMA
effects and unknown callback implementations reject.

- Manifest SHA-256:
  `e7f6daba1b7d2cf34e4b08930daa3972f74f400b397be2a071496ebac175825c`.
- Two focused checks pass in 2.583 seconds, covering source conditions, singleton
  encoding, additional-effect rejection, complete graphics comparisons, current
  pending reasons, and refusal to install the prepared bundle.
- Native sound equivalence/conversion, actual callback integration, and source
  acquisition remain required. No audio is played and no native replay is run.

Sixty-seven of the 101 remaining non-alias, non-dummy furniture candidates now
have prepared artwork. This is not a selectable-import count. No ROM, save,
choice, main lock, or served patcher changes; ABI 158 remains the explicit build.
Continue primary category work before required gold-tree completion.

## Indexed looping clock rigs

`build/v3-indexed-clock-rigs-prepared-01/` prepares all fifteen station models
through `indexed-loop-clock-rig`, using the existing shared geometry/keyframe
converters and one compiler container for all 45 visible model sections.
The three complete source tables contain sixteen entries each; the last entry
duplicates the fifteenth model rather than supplying another item identity.
Each variant retains five joints, three visible models, its constant palette,
and the complete 100-frame motion. Object sizes are 6,720, 8,368, and 5,856 bytes
for the three groups of five variants; no art is resized or discarded.

Complete source functions `fNSN_ct`, `fNSN_mv`, `fNSN_dw`, `fNSN_dt`, and both
joint callbacks establish the category. Paired table dependencies, bounded
selectors, actual keyframe/matrix helper calls, the `0.5` repeat speed, and
the clock owner are checked. Before drawing, source joint three subtracts the
hour angle and joint four subtracts the minute angle about Z. These rules remain
explicit metadata for the required native runtime adapter, not a claim that
converted assets already execute clock behaviour.

- Manifest SHA-256:
  `9831b2e618d322f59e9f13c47e4a98bf6cd40190038929fb3c81439cf274bc42`.
- Three focused source/prepared checks pass in 4.735 seconds: complete category
  discovery, changed code/table/speed rejection, every converted texture/vertex/
  triangle, complete keyframe arrays/pointers, cache reuse, and installer refusal.
- No emulator replay, ROM change, save change, new choice, or patcher update.

The remaining non-alias, non-dummy furniture inventory has 101 candidate records;
62 now have complete prepared artwork. Native clock lifecycle and source
acquisition remain unfinished. Continue primary category work before required
gold-tree completion. The current explicit cartridge remains ABI 158.

## Bulk compilation and prepared reuse

`build/v3-bulk-prepared-02/` rebuilds current descriptors for 95 complete prepared
objects: 93 reused from verified bundles and two newly compiled in one existing
Docker container. Reuse reconstructs the full object from regenerated source
resources, checked emitter/model sections, and complete rig/animation suffixes.
Cached metadata never supplies current eligibility. Prepared-only bundles still
cannot enter the installer directly. Source hashes, model bounds, paths,
section lengths, and conflicting cache entries reject before installation.

The constant-palette sequence category covers both fishing-trophy variants
without per-item production definitions. Complete compiled donor callbacks at
`002CEEB4` and `002CFADC` have the same checked 180-byte instruction pattern after
normalising paired addresses and the matrix-helper call. Both complete cup/base
lists and their distinct 16-colour palettes survive. Each native object is 3,744
bytes. Their source acquisition route remains unfinished; neither is enabled.

- Combined manifest SHA-256:
  `a3835d2b9aa80120995510f29d8b690c1a614e912b1052fe8870541f2493609c`.
- Fishing trophy object SHA-256:
  `1a5a04e40c38f66e7442588fb6a9dea960613df14e8862592149571c3ca38898`.
- Angler trophy object SHA-256:
  `8fd28f98d97744aa7b621309f40031afd4e7647ed151dd91666a5baedf1b3b44`.

The initial 93-object pass uses zero compiler containers. The combined pass uses
one for both new objects and all four model sections. Five batch/reuse checks
pass in 2.442 seconds, including invalid requests, incomplete output, source/hash/
layout rejection, and complete reconstruction without compilation. The initial
cache implementation rejected absent rig metadata against an empty rig record;
the comparison now uses the writer's actual empty-record convention. No asset
bytes or safety requirements are relaxed.

Three focused category and prepared-batch checks pass in 22.404 seconds. They
cover complete trophy palette/model dependencies, reject changed callbacks,
compare all 95 complete converted texture/vertex/triangle resources to the donor,
and verify that acquisition gaps and installer rejection remain intact. No
native replay is needed because no cartridge code or resources change.

No runtime code, ROM, save, selected choice, main lock, or served patcher changes.
The explicit cartridge remains ABI 158. General import category work has priority;
gold-tree effects and ordinary acquisition remain required afterwards.

## Shared planting sparkle

ABI 158 at `build/v3-shared-tree-sparkle-02/build-lock.json` connects gold-sapling
planting effects through all four seasonal callers. The original N64 KIGAE_LIGHT
owner, native bounce timing, foreground commit, and callback cleanup remain.
The complete donor functions provide each season's effect position. The native
effect ID is 87, not the donor's 86, and its native lifetime is 15 frames.

- ROM SHA-256:
  `3c450cd665e79c372a94d30ee77aed0480086968268d2bf64bf9f0c8d8bae443`.
- Report SHA-256:
  `6f8a4c4822358b2f291ad2598d80466a8064ea945849f53614055d687e9c7433`.
- UPS SHA-256:
  `36370a1bf31740afbdd39b4e90676964a2afbcc5b1f2f82e7a81e486875fb346`.

The shared refresh consumes the ABI-157 field lock. Packet code occupies 9,788
of the existing 12,288 bytes; bootstrap, equipment, seasonal banks, owners,
allocations, saved formats, and 128 experimental choices stay unchanged. The
field/insect adapter now validates cumulative installed patches when rebinding.

Nine focused checks passed in 8.077 seconds on `sparkle-01`, including sanitized
selected/unselected rules and missing context, complete source/native functions,
seasonal relocation, existing consumers/resources/saves, UPS reconstruction,
all choices, and the exact V2-12 import-free output. `sparkle-02` corrects only
the report's inherited `planting_effect_installed` flag; its complete ROM and UPS
match the tested build. No native replay is needed for that report correction.

The first silent native run, `build/smoke-v3-tree-sparkle-01/`, passes 39 assertions
before one incorrect fixture timing expectation. It executes all four seasonal
completion functions with exact effect positions and original commit arguments,
checks callback cleanup, and verifies ordinary-item, disabled-profile, and
unfinished-bounce fallbacks. The fixture then expects amplitude `0.09` to complete
after a boundary crossing. Retail N64 damping is `0.4`, so the actual result
`0.036` correctly exceeds the `0.02` threshold. The mistaken fixture used the
GameCube's `0.2` damping assumption. No game code is changed to satisfy it.

The single focused retry at `build/smoke-v3-tree-sparkle-remaining-01/` uses
amplitude `0.04` and runs only the remaining timing/effect/restoration checks.
It passes 67 records and 43 assertions. The original bounce retains phase
acceleration `3000`; actual native effect initialization retains position,
priority, lifetime, and the no-clothing-offset/no-gravity argument. Complete
code, saved import data, guards, restored state/checkpoint, and clean exit pass.
Foreground commits and effect creation are explicit argument-recording doubles.
No live-town mutation, rendered effect, ordinary acquisition, or hardware result
is claimed. No user save is opened or modified.

- Initial partial results SHA-256:
  `d3b30b40b3e36361cd505761e3bfb4bb02e13d0af8176ac100c35e4e62687378`.
- Focused retry results SHA-256:
  `1416176317a25f91ce38ba4d3bf42474f1693238b603c099bfc1166c695c8ef6`.

Complete gold-tree leaf/cut effects and ordinary acquisition remain unfinished;
all four golden choices stay disabled. The next priority is shared bulk-import
categories rather than further golden-tool detail work. Keep both served V2
patchers and the main ABI-109 lock unchanged. Format-3 imported saves require
matching or equal-or-larger profiles and must not be loaded in V2 or format-1/2 V3.

## Shared field clearing and insect habitats

The ABI-157 proposal is `build/v3-shared-tree-field-01/build-lock.json`.
The shared gameplay installer adds selected gold trees to the existing clearing
helper and both native insect-habitat consumers. It introduces no item-specific
installer, asset conversion, browser choice, or memory allocation.

- ROM SHA-256:
  `29819bd234f0440e2e191de351585cb7bbb985a333b6deccd4b8fb04d6375aea`.
- Report SHA-256:
  `716dc833f9553a4da99af5bf521e83053597a5e6b73e323a14424c6900ef87e3`.
- UPS SHA-256:
  `baff9ffca8731d4963d89ab12243e3d6a0cbc1e193483517b06ec5ff1e2de609`.

Build command:

```sh
python3 tools/v3_furniture_install.py --refresh-runtime --scenery-gameplay \
  --base-lock build/v3-shared-tree-felling-01/build-lock.json \
  --output build/v3-shared-tree-field-01
```

Complete source and native functions establish the original N64 layout:
`mSDI_PullTreeUnderPlayerBlock` clears cells `7,8,23,24` through
`mSDI_PullTreeUT`. The GameCube's six-cell path is not the native layout and is
not copied. All five native helper callers, including the cliff-column caller,
remain unchanged. Core `800C3398` uses the shared lazy loader and retains native
families while adding selected `0863..0868`, exactly the gold range in the donor
helper. Hidden contents, stumps, and dead saplings remain excluded.

The complete native insect owner at `00821B40` retains its 10,400-byte resident
size and original 1,072-byte relocation. The original tree request `0804..0804`
recognises selected `0867,0868,007F,0080`, excluding gold bee trees. Acre scans
and actual candidate-cell insertion share this predicate; native ranges,
scheduling, border exclusions, species, coordinates, random selection, and
on-tree cockroach metadata remain. A 60-byte gate occupies reclaimed scan code;
one new jump relocation fits existing padding. All existing packet consumers,
including installed seasonal camera references, rebind to the new code safely.

Code occupies 9,296 of the existing 12,288 bytes. Bootstrap remains 848 bytes,
equipment remains 72 KiB, and complete seasonal banks remain 32,864 bytes each.
No save/profile field, owner allocation, resource, source text, or choice changes.
The main ABI-109 lock and both served V2 patchers remain unchanged.

Seven focused checks pass in 7.500 seconds:

```sh
python3 -m unittest tests.test_v3_tree_player -v
```

Sanitizers cover all sixteen-bit identities, selected/unselected clearing and
habitat requests, every scan position, border exclusions, invalid dimensions,
immutable queries, and guarded writes. Cartridge checks bind complete source/
native functions, exact owner changes and relocations at two bases, current
camera/player rebinding, allocations, unchanged resources/saves, complete UPS
reconstruction, all 128 experimental selections, and exact V2-12 empty output.
Python compilation and `git diff --check` pass.

The first silent native run passes 106 records and 69 assertions:

```sh
python3 tools/emulator_smoke.py \
  --rom build/v3-shared-tree-field-01/animal-forest-v3-asset-loader.z64 \
  --output build/smoke-v3-tree-field-01 \
  --scenario tests/v3-tree-field-scenario.json \
  --xvfb /home/discordian/Games/OpenRSC/headless/vendor/usr/bin/Xvfb \
  --seconds 180 --expansion-pak --no-initial-screenshot
```

- Results SHA-256:
  `e7d6d6818f5ed96ef71f447cd127c66fa490042428d99a478767013ae3d61db4`.

The actual core helper loads the complete packet and clears only supported
identities. The actual four-cell entrance caller clears a temporary mixed acre
while retaining the two additional cells cleared only by the GameCube layout.
The complete insect owner loads and relocates from the cartridge. Actual acre
scans check selected gold, native trees, flowers, borders, exclusions, and null
input. Three executions of the original candidate-selection function choose
the expected real gold/native cells, set the spawn flag and tree metadata,
and leave foreground data intact. No insect actor is created or simulated.
Complete code, saved import data, fixture guards, and fault state pass. World
acre, profile, code/cache, stack guards, equipment, and checkpoint restore;
the emulator resumes and exits cleanly. No user save is opened or modified.
This is component evidence, not ordinary spawning, acquisition, GPU appearance,
live-town clearing, cross-version reload, or hardware verification.

Next implement complete gold-tree leaf/cut effects and planting sparkle, then
exercise the ordinary acquisition route. Keep all four golden-tool choices
disabled until their full routes work. Format-3 saves require matching or
equal-or-larger profiles; never load imported saves in V2 or format-1/2 V3.

## Shared final felling and conversation camera

The ABI-156 proposal is `build/v3-shared-tree-felling-01/build-lock.json`.
The shared scenery gameplay installer connects final gold-stump acceptance
and all four seasonal conversation-camera predicates. No per-item installer,
additional choice, asset conversion, or allocation is introduced.

- ROM SHA-256:
  `b2db9a0fb6139178e2b45d188473b3ca9d75bb1d38ffc4df828f2c40ef4081e2`.
- Report SHA-256:
  `d469757d134997a2bbecdddcdb19d6cf15278f47a8ac50a2d3eeb2de5566a153`.
- UPS SHA-256:
  `551e0adc43939523a5f88e7ff05ef9433d67e60f692556428f3b8fd4ac431854`.

The final axe consumer at `808CA548..808CA558` uses the existing register-saving
gate with query three. It accepts original stump IDs `1..4` and selected gold
stumps `007B..007E`, leaves the returned real ID in `v0`, and supplies the Boolean
in `a0`. The original stack store, height lookup, terrain offset, foreground
update, and later effect call remain. Complete donor/native function contracts
and all retained player-query patches are validated before rebinding. Twelve
jump relocations follow the original relocation order; no owner grows.

Investigation resolves the earlier height-lookup question: both complete
`obj_hight_table_item0_nogrow` implementations already return the same neutral
record for gold stumps. Their three twelve-byte records match. Native code
`800A5AC8..800A5B4C` and data `8010B478..8010B49C` remain unchanged. No identity
substitution or speculative geometry patch is needed.

Each seasonal move callback binds its actual HI16/LO16 function reference to a
shared wrapper; two relocation records per owner are removed. The complete
original predicate remains callable in its loaded owner. The wrapper adds the
three actual donor medium/large/full gold descriptors, `first_index+2..4`, only
when the golden-shovel profile bit is selected. Small trees, saplings, stumps,
other objects, and unselected gold retain the native answer. Source cedar/palm
families are not enabled. All complete native move functions and donor predicates
are checked, including Xmas's longer move function and different reference pair.

Code occupies 8,824 of the existing 12,288 bytes. Bootstrap remains 848 bytes,
equipment remains 72 KiB, and seasonal banks remain 32,864 bytes each. Saved
format, choices, source text, owner sizes, and scene/resident allocations do not
change. The main ABI-109 lock and both served V2 patchers remain unchanged.

Five focused checks pass in 6.778 seconds:

```sh
python3 -m unittest tests.test_v3_tree_player -v
```

Sanitizers cover all sixteen-bit player IDs and selected/unselected camera
fallback forwarding. Cartridge checks cover complete source/native retention,
all twelve player relocations, all four callback pairs at two relocation bases,
unchanged geometry/resources/saves, full UPS reconstruction, all 128 experimental
selections, and exact V2-12 for empty selections. Python compilation and
`git diff --check` pass. Unchanged old native components are not replayed.

The first silent native run passes 172 records and 88 assertions:

```sh
python3 tools/emulator_smoke.py \
  --rom build/v3-shared-tree-felling-01/animal-forest-v3-asset-loader.z64 \
  --output build/smoke-v3-tree-felling-01 \
  --scenario tests/v3-tree-felling-scenario.json \
  --xvfb /home/discordian/Games/OpenRSC/headless/vendor/usr/bin/Xvfb \
  --seconds 180 --expansion-pak --no-initial-screenshot
```

- Results SHA-256:
  `15c07a1ee54c2ed36cd7367861e6695978ee1318a11df9f21c0514938b62cdb2`.

The actual player owner executes its final stump branch and lazy loading.
Selected smallest/largest gold stumps and native stumps reach the original
foreground call with the real identity, original position, and native update
flag. Unselected gold and an uncut tree take the rejection branch. The original
height lookup executes and returns the neutral record. The fixture injects the
stump result, skips terrain mutation, and stops before foreground mutation and
effects; it does not claim a full axe swing, tree commit, or acquisition.

All four complete seasonal owners load and relocate from the cartridge. Their
actual callback references resolve to the shared wrappers. The three accepted
gold indices, small/sapling/stump exclusions, native objects, and unselected
fallbacks execute with the original native predicate as the reference. Fixture
guards, save data, player code, equipment, restored pointers/profile/code cache,
checkpoint restoration, final fault/guards, and clean exit pass. No user save is
used or modified, audio is disabled, and no code is changed in the cartridge.
New harness work is below twenty minutes; no retry is needed.

Next implement complete source gold-tree effects and planting sparkle, plus
the remaining shop-path and insect consumers. The source effect owner reuses
ordinary seasonal tree models/motions after normalizing gold variants, with
a distinct gold status/palette and gold leaf flags. Bind the complete native
dependencies before reusing them; do not substitute green effects. Small-tree
and leaf-effect drawers also use the gold palette. The shop path touches only
six cells in acre `(2,2)`; the insect source accepts mature/reward/Bell/furniture
gold trees but excludes bee trees and the acre's two-cell border. Preserve those
rules when extending the shared consumers. Golden choices stay disabled until
ordinary acquisition works. Effects, ordinary gameplay, persistence, and hardware
are not established by this component run.

Format-3 matching/equal-or-larger profiles remain required. Do not load imported
saves in V2 or older format-1/2 V3 builds. Preserve backups and all previous ROMs.

## Shared player tree queries

The ABI-155 proposal is `build/v3-shared-tree-player-02/build-lock.json`.
The existing shared scenery gameplay refresh connects player tree eligibility
and bee handling without adding a per-item installer or enabling unfinished tools.

- ROM SHA-256:
  `5aab16914859630dbaa6ffcc92af99baf4e6a5ff1031c225f6404e3baab5bbf7`.
- Report SHA-256:
  `b9a43b2b8f1ba7b2a4e85ca64beaee29cdfbf01ca26a6ae278e116c4608af6bf`.
- UPS SHA-256:
  `b9907efde2fa718152b758d0ac084ec72f3b1ca22b78aaf0a0184d73abb64728`.

Eight complete donor functions and matching unchanged native functions bind
three axe-target checks, nearby-tree selection, touch/shake sound eligibility,
two shovel reactions, the shake action, common bee release, and the axe drop/
stump helper. The native solid category contains sixty identities; its small-tree
subset contains ten. Shared masks are extracted from the original predicates.
Selected gold trees extend those categories without accepting unsupported donor
palm/cedar families, saplings, dead trees, or stumps. Small gold trees are solid
but do not gain the larger trees' touch sound. Selected gold bees retain their
actual `0081` identity through native callbacks.

Eleven installed calls share a 364-byte gate at linked player `808B6934`, inside
one replaced inline predicate. Inert delay-slot metadata supplies the source
register, result register, and predicate kind without consuming another live
register. The gate preserves the other live integer registers, HI/LO, floating-
point registers/control, and the caller's stack; its own frame is 256 bytes.
It uses the existing verified packet loader before dispatch. Original target
coordinates, nearest-tree selection, height/distance/angle filters, callback
permissions, animation checks, and five-frame bee timers remain.

The packet is 8,544 bytes within the existing 12,288-byte reservation. Seasonal
banks stay 32,864 bytes, bootstrap stays 848 bytes, and equipment stays 72 KiB.
No owner/relocation file, import blob, scene allocation, save field, source text,
or selection catalogue grows. All seasonal/daily/core references bind the new
packet, and both player-action and player-motion owner receipts are updated.
The main ABI-109 lock and both served patchers remain unchanged.

The first host/cartridge invocation catches an actual implementation defect:
sorting the expanded relocation list groups HI16 and LO16 records separately,
breaking the native loader's register-cached high/low pairing. The installer
now retains the entire original ordering and appends only the eleven new jump
relocations. Build `01` is not a deliverable. Build `02` passes all four focused
checks in 6.211 seconds:

```sh
python3 -m unittest tests.test_v3_tree_player -v
```

AddressSanitizer/UBSan covers every sixteen-bit ID with selected and unselected
profiles, solid/shakeable/bee queries, ignored upper argument bits, and unsupported
queries. Cartridge checks bind complete source/native functions and masks, retain
all instructions outside declared windows, relocate every query at two addresses,
retain original relocation ordering, validate live owner receipts and unchanged
resources/allocations/saves, reconstruct the full ROM from UPS, retain all 128
experimental choices, and reproduce exact V2-12 when imports are disabled.

The initial silent native run, `build/smoke-v3-tree-player-01/`, is partial:
58 records, 46 passing assertions, and one failed fixture-guard assertion. It
verifies the complete actual relocated player text, all eleven installed call
sites, expected results, live integer/HI/LO/floating-point register preservation,
lazy packet loading, native/unselected and small-tree fallbacks, common bee
callbacks, axe drops/stump returns, real identities, and the permission-controlled
five-frame bee timer. The final guard overlaps the test's cut-result recorder:
`actor+13A0` equals old `out+32`. The observed hash is exactly the callback's
recorded four words `0,2,3,0`, not unexplained game memory damage.

- Initial partial results SHA-256:
  `2c5c106e6ea8078cd8a7af36e8ac594ac86a2e6e0cf1cbd8ad32d7c287d18f32`.

The corrected layout separates actor, output, clip, code, and guard intervals,
with an explicit overlap assertion. The one justified retry uses the focused
consumer scenario instead of repeating the passed eleven-query/register prefix:

```sh
python3 tools/emulator_smoke.py \
  --rom build/v3-shared-tree-player-02/animal-forest-v3-asset-loader.z64 \
  --output build/smoke-v3-tree-player-consumers-01 \
  --scenario tests/v3-tree-player-guarded-scenario.json \
  --xvfb /home/discordian/Games/OpenRSC/headless/vendor/usr/bin/Xvfb \
  --seconds 180 --expansion-pak --no-initial-screenshot
```

The retry passes 67 records and 52 assertions, restores all modified state and
the complete emulator checkpoint, checks final fault/save/equipment guards, and
exits successfully. New harness work stays below ten minutes. Common bee release
retains null/type/coordinate rejection and facing fallback. Axe calls preserve
counter/drop arguments, return the original tree before exhaustion and gold
stump `007E` at exhaustion, and delay bee release through the native permission
check. No user save is loaded or modified; both runs are silent and isolated.

- Focused consumer results SHA-256:
  `6a197178437db8ea4255f3d2e848430e00a1fb7c58701f3a909b42daec9bbc2a`.

Drop and cut-count callbacks are explicit isolated stubs. These results do not
prove ordinary target selection, actual landing/bee actors, complete felling,
ordinary acquisition, save/restart, rendered appearance, or original hardware.
Retain the passed query prefix and corrected consumer result; do not replay them
without changed code. The ABI-154 seasonal fixture remains partial, not closed by
these player checks.

Next connect the final axe-felling caller: native `808CA548..808CA558` accepts
only stump IDs `1..4`, followed by the geometry lookup at `800A5AC8`. Returning
gold stump `007E` alone does not commit the new foreground. Preserve real saved
identities while adapting the geometry query. The donor's `ac_effectbg.c` has
gold-specific size variants, status flag, tree/leaf resources, and cut handling;
port those dependencies before routing gold variants into the native effect
owner. Also retain planting sparkle and the remaining shop-path, camera-limit,
and insect consumers as required work. Reuse the installed complete tree art.
All four golden choices stay disabled until complete ordinary acquisition works.
Format-3 matching/equal-or-larger profile restrictions remain; imported saves
must not be loaded in V2 or older format-1/2 V3 builds. Preserve backups.

## Shared seasonal tree interactions

The ABI-154 proposal is `build/v3-shared-tree-interactions-04/build-lock.json`.
The existing scenery gameplay refresh supplies complete gold-tree drop records
to the native seasonal drop engine and connects all axe-hit-count initializers.
It adds no individual-item installer, browser option, or replacement identity.

- ROM SHA-256:
  `276e63f303dbb119b6dc8aed352c9f57b3f588b26edef6e42a7ecadedeb12272`.
- Report SHA-256:
  `da51f53c390a828e572c147af5e16b592f3efc642d860b40e7b22a54dacdc68c`.
- UPS SHA-256:
  `aed6d4bbefc23de64ed8da350b3f9229de8c889aabea9db1392c6c59ada75e80`.

Twelve complete donor functions and eight complete source tables bind drop,
bee, and cutting behaviour across all four seasons. Each native thirteen-row
drop prefix matches the donor exactly. Source gold Bell/furniture/bee/shovel
rows append once in shared read-only code data; selected profiles expose them,
while unselected profiles expose only the original thirteen rows. The original
native drop loop, random furniture selection, landing machinery, held-item
windows, coordinates, and foreground setter remain. Gold Bell trees share native
money luck. The bee predicate preserves the native argument and complete
actor-create/failure/delete flow. Every gold drop leaves a spent gold tree;
the source shovel record drops actual item `223B`.

The shared cut-count adapter first runs the complete original initializer, then
overlays only eight gold records in the transient 256-cell counter array. All
nine references are installed: two cherry, three winter, two Xmas, and two
ordinary. Native counters and foreground cells are untouched; original hit
decrement and stump conversion remain. Four table-reference relocation rows and
the respective cut-call rows are removed per seasonal owner. Other relocation,
original tables, owner dimensions, and actual native drop callbacks remain.

The packet occupies 8,232 bytes in a 12,288-byte reservation at
`804B5000..804B7FFF`, adding 4 KiB. Bootstrap stays 848 bytes; equipment stays
72 KiB. Existing retired cartridge storage holds the packet without import-blob
growth. Complete scenery assets, scene allocations, saved fields, provenance
text, and all 128 experimental choices remain unchanged. All installed seasonal,
daily, growth/stump, and world-query references bind the new code addresses.

The first three build attempts stop before producing a ROM: one typed source
hash contains an extra character; the initial native-retention comparison omits
the already-installed held-item landing hooks; the corrected comparison then
finds the ordinary owner's older recorded pre-hook words. The final guard checks
current hook words against the installed receipt, checks original instructions
against the verified retail ROM, and compares all remaining native bytes. No
retention check is disabled. The fourth build succeeds.

Four focused tests pass in 6.228 seconds on their first invocation. Host
AddressSanitizer/UBSan covers every sixteen-bit identity, selected/unselected
drop spans, bee predicates, money luck, all gold cut counts, native-counter
retention, original foreground preservation, all four wrappers, and guarded
writes. Cartridge checks bind complete donor/source/native records, all nine
initialization callers, exact retained owner contents, relocation at two
addresses, existing landing hooks, storage/memory limits, full original-ROM UPS
reconstruction, retained format-3 fields, unchanged choices, and exact V2-12
import-free output.

Native verification is **partial**, not passed. The first silent attempt,
`build/smoke-v3-tree-interactions-01/`, asks the native heap for 96 KiB and receives
null before installing fixture data. The one justified retry reduces the private
allocation to 92 KiB, still bounding the complete owner/relocation and fixture.
`build/smoke-v3-tree-interactions-02/` passes 28 assertions in 57 recorded steps
before its failed assertion and cleanup. It loads the complete packet and actual
relocated cherry owner, checks selected/unselected axe counts and unchanged cells,
and runs shovel, ordinary/lucky Bells, furniture, and bee drop control flow with
correct six-argument forwarding, counts, resulting gold identity, and bee profile.

The failing deletion assertion is a confirmed fixture overlap: the 24-byte actor
creation recorder begins at `out+96`, while the old deletion recorder begins at
`out+112`. Recording the actor's fifth argument (`BF800000`, or `-1.0`) writes
that deletion slot. The observed hash exactly matches those four bytes. The
recorders are separated and an explicit interval-overlap check is added, but
the corrected fixture is not rerun: the batch's setup-retry allowance is spent.
Harness work remains below thirty minutes. No game implementation change is
made to accommodate the fixture failure.

- First attempt results SHA-256:
  `c8abd36f6977b66a42dd9ab4eb3c671a790097c5502429f2ef13ec3fb1a402a2`.
- Partial retry results SHA-256:
  `62d0ad3843e0f4b6bb43b1ff1e55d608f68aeb8aff557978d36ff948295b2a37`.

Field access, item landing, furniture selection, terrain height, foreground
commits, and actor creation/deletion are explicit fixture doubles. Cleanup
restores modified state/code and frees the allocation, with returned calls;
final restoration comparisons, fault/guard checks, checkpoint restoration,
the other three seasonal native paths, failure branches, and the unchanged
native-fruit sample are not reached. Do not claim complete native execution,
real landing/actors, ordinary acquisition, save/restart, or hardware proof.
No user save is used or modified; emulator audio stays disabled.

Next connect the player's actual collideable-tree and bee-tree predicates and
shake/axe/bee timing. The source's `m_player_main_shake_tree.c_inc` gates the
drop callback with `IS_ITEM_COLLIDEABLE_TREE`, and delays bee release through
`IS_ITEM_BEE_TREE`. Installed tool-button predicates alone do not cover those
foreground checks. Also connect planting sparkle and the remaining shop-path,
camera-limit, and insect-tree consumers. Reuse complete installed seasonal assets
and passing unchanged evidence; do not restart the acquisition dependency chain.
The source sparkle lives in `bIT_actor_drop_move_plant`; seasonal offsets are
`(13,33,10)` in Xmas. Native plant completion is owner `+3928..3A84`, with foreground
at drop `+0E`, position `+14`, and completion clearing callbacks `+0/+4/+8`.
The native camera-limit routine is referenced by the move callback; confirm each
season's actual reference before extending its descriptor range.

All four golden-tool choices remain disabled until complete ordinary acquisition
works. Format-3 matching/equal-or-larger profile restrictions remain; do not load
imported saves in V2 or older format-1/2 V3 builds. Preserve backups. The main
ABI-109 lock and both served patchers remain unchanged.
See the [interaction design](../../specs/V3_SCENERY.md#seasonal-shakedrop-and-axe-hit-initialization).

## Shared tree world queries

The ABI-153 proposal is `build/v3-shared-tree-world-02/build-lock.json`.
The shared scenery gameplay installer connects collision geometry, shovel-removal
eligibility, and NPC walkability for imported gold trees. It retains actual native
terrain calculation, complete original routines, original-ID exclusions, and
saved foreground identities. No individual-item installer or new choice is added.

- ROM SHA-256:
  `c301c71d9931a5ab15c84e870c50024b6f483a7ce90229a0fe69da7fbf709806`.
- Report SHA-256:
  `b5f377c157bc8faee2527ed47d08ea46bc21d5813387dd4ca581485f299ce8f6`.
- UPS SHA-256:
  `fec9f21af1270c505bb8234f22e6459845b34953056f3708da586cb0317831da`.

Three complete donor and three complete native functions are hash-bound, together
with source collision dimensions. Core entries `8006C980`, `8008C964`, and
`8008D7B0` use one ABI-preserving resident gate. Lazy loading retains the original
fifth stack argument; fallback stubs replay exact displaced prologues. Twelve
solid imported states use complete native geometry through a temporary unit copy.
Inclusive exclusions use the real ID, never the temporary geometry ID. Neither
the source unit nor saved world data is changed. Native callers, the removal
callback table, terrain helpers, and original routine bodies remain intact.
Selected saplings/dead saplings/stumps allow removal; only initial saplings add
NPC walkability. Unselected/native IDs retain their complete original behaviour.

The packet occupies 7,516 bytes of its existing 8,192-byte reservation. Bootstrap
size stays 848 bytes; equipment stays 72 KiB. Seasonal and daily consumers bind
the new code addresses. No relocation rows, resource/scene allocations, saved
fields, provenance text, or any of the 128 experimental choices change.

The first build exposed a compiler-generated `memcpy` dependency in the temporary
unit copy; the explicit eleven-word prefix copy and flags copy avoid that missing
runtime dependency. The corrected build links successfully. Four focused tests
pass in 6.873 seconds on their first invocation: host AddressSanitizer/UBSan covers
all sixteen-bit IDs, selection, exclusions, immutable units, argument forwarding,
and bounds; cartridge checks bind complete functions/prologues, retained owner
code and relocation, storage limits, original-ROM patch reconstruction, optional
composition, unchanged saves/choices, and exact V2-12 import-free output.

The first silent native run, `build/smoke-v3-tree-world-01/`, passes 132 records
and 118 assertions, restores its checkpoint, and exits cleanly. Actual core entry
dispatch loads the complete packet, preserves stack arguments, and uses native
terrain queries. All twelve solid gold states match the complete corresponding
native columns. Real-ID exclusions, non-solid saplings, dig eligibility, NPC
walkability, existing growth/stump dispatch, and unselected/native fallbacks pass.
No game helper is replaced with a fixture stub. Complete packet/module contents,
input units, allocation/stack guards, restored profile/cache/packet, and zero
fault are checked. The private allocation is freed before checkpoint restoration.
No user save is used or modified, and emulator audio is disabled. Harness work
stays within the batch's thirty-minute limit; no native retry is needed.

- Results SHA-256:
  `35126cd76afa789785a95fa244443df5a1bd3ef61ffffa8e405d86cfdf2d95c1`.

This is component verification, not ordinary walking/digging, shaking/cutting,
acquisition, rendering, save/restart, or hardware proof. Full cutting/shaking/drop
and planting effects remain; audit tree-specific field/insect consumers while
connecting those routes. All four golden-tool choices stay disabled pending
complete source acquisition. Format-3 matching/equal-or-larger profile restrictions
remain; do not load imported saves in V2 or older format-1/2 V3 builds. Preserve
backups. The main ABI-109 lock and both served patchers remain unchanged.
See the [world-query design](../../specs/V3_SCENERY.md#collision-removal-and-npc-walkability).

## Shared hidden tree contents

The ABI-152 proposal is `build/v3-shared-tree-contents-01/build-lock.json`.
The same shared scenery gameplay installer connects daily hidden-content
recording, counting, and refilling for selected spent gold trees. It reuses the
installed packet, bootstrap, owner lifetime, and seasonal banks; it adds no
item-specific installer or selection. All native scheduling and quantities stay
intact. Complete donor tables supply the gold identities, preserving ordinary
trees and excluding saplings, dead trees, and trees still carrying a shovel.
The donor's additional cedar behaviour is not imported implicitly.

- ROM SHA-256:
  `3da7cb11681c38f1288efb5f09d0ee55fe015ffe2ed3b082605ca4772b0391f7`.
- Report SHA-256:
  `48efde92a0d80fd97ded064667d13d6e3e63880579f2b4f2a51c0cbdff73151a`.
- UPS SHA-256:
  `5a85e2f25e195b22d5342986eacd89f334102a0b7c69a034d714c2c31f9c8b10`.

Thirteen full donor functions, four complete source family tables, nine full
native owner functions, and the complete core count/change helpers are checked.
Eight actual owner call/table references connect four shared consumers. Only
four internal relocation rows are removed; direct core calls have none. Both
daily callback arrays use the new money counter. Native record wrappers retain
their structure offsets; complete bee/furniture/Bell schedulers retain acre
distribution, quotas, and random sampling. Original core/holiday users remain
unchanged. All earlier growth, planting, native families, and imported-house
protections remain installed.

The packet is 6,812 bytes within its existing 8,192-byte reservation. The
bootstrap remains 848 bytes; the equipment module remains 72 KiB. Complete
seasonal banks, owner dimensions, scene allocations, save/profile fields, and
128 experimental choices remain unchanged. Code fits the existing retired
cartridge reservation without growing the import blob. No player-facing text
is introduced; no new provenance entry is needed.

Four focused tests pass in 6.351 seconds on the first invocation. Host
AddressSanitizer/UBSan checks all sixteen-bit identities, record/count offsets,
selected/unselected behaviour, complete acre counts, source-width wrap,
mixed-family random choices, protected shovel trees/saplings, native fallbacks,
and guarded writes. Cartridge checks bind complete source/native functions,
actual callback inventory and relocation at two addresses, unchanged original
schedulers and house protections, memory/storage bounds, complete patch
reconstruction, retained save fields/choices, and exact V2-12 import-free output.

The first silent native run, `build/smoke-v3-tree-contents-01/`, passes 75 records
and 50 assertions, restores its checkpoint, and exits cleanly. Actual daily
entry loading verifies the full packet. Native record wrappers and Bell-counter
bindings execute with isolated structures. The real complete refill schedulers
then process a temporary thirty-acre mixed grove, producing five bee trees, two
furniture trees, and thirty Bell trees. Eighteen ordinary and nineteen gold trees
change to their own family's hidden states. Bee contents occupy all five
columns; furniture contents occupy two. Every sapling and shovel-bearing tree
remains unchanged. Existing records/quotas prevent a second refill without
consuming RNG. Unselected refill falls back to the actual native routine.

All temporary world cells, original RNG, profile, owner pointer, packet/cache,
scene selector, and test stack are restored and checked. Owner code/data and
the whole equipment module remain intact; memory guards and zero fault pass.
The owner's own scratch BSS is allowed to change during its normal scheduling.
No user save is used or modified, and all emulator audio is disabled.
New harness work took under ten minutes; no retry was needed.

- Results SHA-256:
  `ef60cd7aa2d81b3359915571562a2f8ad1a4370a595be5961bdcc5cefc929717`.

This is not ordinary tree shaking, acquisition, a full live-town renewal,
save/restart, GPU appearance, or hardware proof. Next connect world collision,
cutting/shaking/drop, and planting effects. All four golden-tool choices remain
disabled pending their complete source acquisition routes. No arbitrary reward
substitute is introduced. Format-3 matching/equal-or-larger profile restrictions
remain; imported saves must not be loaded in V2 or older format-1/2 V3 builds.
Preserve backups. The main ABI-109 lock and both served patchers remain unchanged.

## Shared daily tree growth

The ABI-151 proposal is `build/v3-shared-tree-daily-01/build-lock.json`. The shared
scenery gameplay stage connects the actual daily-growth owner without changing
its loaded size, layout, or existing imported-house protections. Complete donor
contracts supply gold growth/death, four-direction and cross-acre neighbours,
sapling recording/counting, and source-priority thinning at the 32-tree acre cap.
Original native families retain their original growth/environment/flower routines.
Selected gold trees participate in neighbour blocking in both directions.
Dead gold saplings are removed from the thinning candidates and clear on the
next applicable daily update. Source counter widths and random selection remain.

- ROM SHA-256:
  `598ba67b71b479e549a56581feea7faa94a156d74fd154724e937fca729be01d`.
- Report SHA-256:
  `654c73f736d4e858dd5b4f39642e8f2e60abdf753e90a25b8900626f22c86688`.
- UPS SHA-256:
  `43ae31830681a36bb1dcf327ab954545709fde80c3f2564db168cc58878446f4`.

Daily owner VROM `00970920`, relocation `009754A0`, linked RAM `80AB07C0`, and
loaded pointer `80100C5C` retain their native allocation and lifetime. Five
existing call/table references use shared callbacks: neighbour checking,
ordinary plant processing, initial sapling bits, candidate counting, and thinning.
Only those references' relocation rows are removed. The native renewal entry
loads and verifies the shared code before resuming its displaced prologue.
The complete core loader remains unchanged, as do all original helper routines.
Seven complete native and nine complete donor consumers are bound by hashes;
the callback inventory rejects unexpected references.

The packet is 5,948 bytes, requiring an 8,192-byte reservation at
`804B5000..804B6FFF`, a 4-KiB increase. Its full data remains in the existing
retired-module cartridge reservation. The bootstrap/fallback image remains
848 bytes; the existing cache word and guards retain their addresses. All three
complete seasonal banks, seasonal owners, equipment module, save/profile fields,
and 128 choices remain. The import blob and scene allocations do not grow.

Four focused checks pass in 6.992 seconds on their first invocation. Host
AddressSanitizer/UBSan covers growth/cap/day boundaries, dead clearing, every
neighbour direction and cross-acre edge, parity rules, native/unselected
fallbacks, sapling bookkeeping, native-first removal priority, random selection,
eight-bit full-acre wrap, and write bounds. Cartridge checks bind complete
source/native contracts, unchanged original helpers/house protections, actual
relocations at two addresses, packet/cache/guard storage, complete UPS
reconstruction, retained choices/save fields, and exact V2-12 empty output.
No new player-facing text or diagnostic source credit is required.

The first silent native run, `build/smoke-v3-tree-daily-01/`, passes 97 records
and 75 assertions, restores state/checkpoint, and exits cleanly. The real patched
renewal entry loads the complete packet and executes the original non-field
early return; this deliberately prevents renewal of the live town. The actual
daily consumers then run on isolated acre arrays. They cover day/cap growth,
death/clearing, mature/spent stability, native and gold neighbours in both
directions, cross-acre sapling parity, actual native RNG removal priority,
candidate recording/counting/dead exclusion, unselected fallback, unchanged
neighbour identities and loaded owner code, memory guards, and zero fault.
The owner pointer, packet, cache, profile, scene selector, RNG state, test stack,
and complete equipment module are restored. No user save or ROM is used as a
mutable test file, and no speaker/headphone output is emitted.

- Results SHA-256:
  `7d4526df0ef43d6b2c65484ebcecde8fc57cf05a3f556ab156f144c6d03304f6`.

This is not a full live-town renewal, ordinary planting/acquisition, GPU
appearance, save/restart, or original-hardware result. Reuse prior component
evidence for unchanged planting, growth-table, and seasonal-rendering behaviour.
Next connect world collision, full cutting/shaking and the selected shovel drop,
planting sparkle, and daily hidden-content recording/replenishment for spent
gold trees. All four golden-tool choices stay disabled until their source routes
are complete. No placeholder acquisition route or replacement native identity
is introduced.

Format 3 keeps matching/equal-or-larger profile requirements. Imported saves
must not be loaded in V2 or older format-1/2 V3 builds; preserve backups.
No new cross-version reload claim is made. The main ABI-109 lock remains
`f69d44334f40335c687816ece1abf0f0d1d213ccfb52bbb433f889ff606428ef`;
both served patchers and existing ROMs/saves remain unchanged.
See [the daily-growth design](../../specs/V3_SCENERY.md#daily-growth-death-and-overcrowding).

## Shared planting and tree-state runtime

The ABI-150 proposal is `build/v3-shared-tree-states-02/build-lock.json`.
The shared scenery gameplay stage connects selected shovel burial to the donor's
gold sapling in all four seasonal owners, and connects core growth/stump queries
to complete donor state tables. Original native families retain their complete
original consumers. The four internal burial calls lose only their corresponding
relocation record; the original burial functions remain available for fallback.
Existing foreground placement and planting animation stay with the native caller.
This is not complete ordinary gold-tree acquisition; the four tool choices remain
disabled pending daily growth/death, collision, cutting/shaking, sparkle, and drop.

- ROM SHA-256:
  `ac9d7e39045a1401b297d2492d02702f02aa7d729f0844d7b15e0554764f9c7a`.
- Report SHA-256:
  `0db3c8223a35068cc55dfdd1f217bfdf81e4f0432c64c3322bd61f65ddba0322`.
- UPS SHA-256:
  `f8a3e088a0ed458d3f67659210c6b33b967a966a3ed277257762882cd0f8bb1f`.

The shared packet grows from 2,892 to 3,872 bytes, still within its existing
4,096-byte reservation. Its cartridge storage remains inside the first declared
retired module; all three complete seasonal banks remain unchanged. The existing
equipment module's bootstrap reservation contains an 848-byte implementation,
including native prologue stubs at `804ADFC0`/`804ADFD0`. The cached CRC at
`804ADFEC` starts zero and is set only after verified DMA and cache maintenance.
Tree queries can load the packet before a seasonal actor exists. The equipment
module, startup size, scene allocations, profile bits, and saves do not grow.
Build 01 provisionally reserved an unnecessary second page; build 02 retains the
existing page after the compiled code proves it fits. Both ROMs are identical;
only build 02's receipt records the correct unchanged reservation.

Four focused tests pass in 6.174 seconds on the first invocation. The host fixture
uses AddressSanitizer/UBSan for negative/zero/large elapsed days, growth caps,
mature/spent stability, every stump size, flag narrowing, all other sixteen-bit
native IDs, selection, all four burial adapters, and bounded output writes.
Cartridge checks verify complete donor functions/tables, native core/owner
retention, relocation at two addresses, lazy-load stubs/cache placement, retained
guards/artwork, complete UPS reconstruction, 128 unchanged choices, and exact
V2-12 empty-selection output. No diagnostic text or source-credit entry is added.

The first silent native run, `build/smoke-v3-tree-states-01/`, passes 150 records
and 100 assertions with restored state/checkpoint and clean exit. It clears the
packet/cache and owner pointers in paused test memory, then enters the actual
patched native growth function. Complete DMA/CRC loading succeeds with no owner.
Native and selected gold growth/stump cases pass, including `INT_MAX` elapsed
days. All four complete owners load and relocate, then their actual burial
adapters pass sixteen selected/unselected/shovel/fruit/hole cases. Output bounds,
positions, stack/fixture guards, zero fault, entire restored equipment module,
and the final save/equipment guards all pass.

- Results SHA-256:
  `8ff7da4f69f33bcf9cdd7cac7351008ddbc80a357dd54ab307c97dd844a7787e`.

The profile bit is enabled only in paused test RAM and restored; no user save or
served patcher is changed. The fixture calls burial helpers, not the complete
ordinary burial interaction. No GPU appearance, daily-growth cycle, save/restart,
or original-hardware claim is added. Reuse unchanged seasonal resource/render
evidence without replaying old builds. The next owner is `m_all_grow_ovl`, VROM
`00970920`, relocation `009754A0`, linked RAM `80AB07C0`, loaded pointer `80100C5C`;
its existing imported-house protection edits must survive the growth extension.

Format 3 retains matching/equal-or-larger profile requirements. Imported saves
must not be loaded in V2 or older format-1/2 V3 builds; preserve backups.
The main ABI-109 lock remains
`f69d44334f40335c687816ece1abf0f0d1d213ccfb52bbb433f889ff606428ef`.
Both served patchers, existing builds/saves, and all 128 choices remain unchanged.
See [shared scenery](../../specs/V3_SCENERY.md#shared-planting-and-tree-state-rules).

## Shared seasonal scenery runtime

The ABI-149 proposal is `build/v3-shared-scenery-04/build-lock.json`. The shared
runtime installer consumes the prepared scenery category, retains complete
native owners, and supplies all fourteen gold-tree type records in each season.
Each scene bank includes complete body and shadow objects, all source positions,
ordered descriptors/lists, fourteen palettes, the eighteen-term selector, and
explicit CPU/graphics/callback relocation tables. No individual-item installer,
replacement native identity, or enabled golden-tool choice is added.

- ROM SHA-256:
  `be67ec87c84a651111b6ae88592f2461973d45e48430bfd88f4a198cc2f737a8`.
- Report SHA-256:
  `ace6955ebb5dfd25364ebb7d397e05adfb389469b45f442fe1018f3cf1f17b06`.
- UPS SHA-256:
  `e51f81804b299c0867fe7234840127595b429880e67fefdb87e0066686312ed0`.

Three 32,864-byte cartridge banks serve the four seasonal owners, with Xmas
sharing winter. Each uses verified retired module storage; the first reservation
also holds a 2,892-byte shared code packet. Existing live resources remain
protected through explicit reservations in the report. The import blob does not
grow. A 267-byte bootstrap fits unused equipment space before the retained ground
guard; the equipment module and startup allocation remain unchanged. Shared code
reserves `804B5000..804B5FFF`; each loaded seasonal owner adds 32,864 bytes of BSS.
Owner resident totals are cherry 74,688, winter 74,832, Xmas 75,872, and ordinary
74,624 bytes. Original actors and start-index array capacities do not grow.

The constructor loads and CRC-checks the code and data, binds callbacks to the
current owner, relocates CPU/graphics pointers, and calls the original native
constructor. The body callback updates its active palette using the native term
query and retains the original material/matrix/geometry order. Ten checked unused
descriptor slots follow the native NONE sentinel, without overlapping any
installed held category. Future category work must preserve those reservations.
The full original native foreground tables have 112 low and 84 environmental
entries; the fourteen imported IDs overlap neither. Native types retain their
original classification routine through an owner-local trampoline, while
unselected imported types use the safe empty row. This does not permit loading
a saved import under an incompatible profile.

Four focused checks pass. The host fixture uses AddressSanitizer/UBSan and covers
all owner lifetimes, pointer/graphics/callback fixups, selection/fallback, every
calendar term, reinitialization, malformed resource bounds, CRC/DMA failure,
and unchanged guards. Cartridge checks verify complete prepared resources,
every declared relocation, native data/code retention, relocated allocations,
retired-storage ownership, future reclamation protection, official composition,
128 retained choices, UPS reconstruction, and exact empty-selection V2-12.
All five new failure messages carry assistant authorship in the single source
catalogue; no donor translation is claimed for those diagnostics.

The first preflight found the previous module's retained guard inside the
proposed bootstrap range and correctly rejected it. The range now stops before
that guard. Initial resource rebasing rejected a valid interior vertex-array
load; the shared bank packer now requires its full aligned, bounded source slice.
The first test invocation also used a nonexistent composition module name; it
was corrected to the existing composer. No game defect or native fixture retry
was encountered. Builds 02–04 have identical cartridge and UPS hashes; the final
receipt includes diagnostic credits and general output-path support. Native
evidence from build 02 therefore covers the unchanged final cartridge, without
replaying historical candidates.

The first silent native run, `build/smoke-v3-scenery-01/`, passes 237 records and
122 assertions, then exits cleanly. It uses actual cartridge DMA and overlay
relocation for all four complete owners/banks, checks every relocated byte and
palette, resolves all 56 selected foreground cases with guarded output, executes
unselected and ordinary-item fallbacks, and calls all four actual body drawers.
Material/geometry lists, graphics bounds, memory guards, saved-state restoration,
checkpoint restoration, and the final zero-fault check pass. The fixture enables
the existing golden-shovel profile bit only in paused test RAM and restores it;
neither the browser options nor on-disk saves are changed.

- Native results SHA-256:
  `a5adc47f9854b92dbd81d458b5465472f21c66e2671ad084ffc7c9ad5f6c5038`.

The component run does not execute a full seasonal constructor, adjusted-shadow
drawing, GPU appearance comparison, ordinary tree acquisition, save/restart, or
hardware playthrough. Do not infer those from successful body-list generation.
Next implement native world collision, shining-hole shovel planting,
growth/death, cutting/shaking, and the selected golden-shovel reward. Keep all
four golden-tool choices disabled until their actual source routes work.

Format 3 and existing saved identities/profile bits are unchanged. Imported saves
still require matching/equal-or-larger profiles; do not load them in V2 or older
format-1/2 V3 builds. No new cross-version reload claim is made. The main ABI-109
lock remains `f69d44334f40335c687816ece1abf0f0d1d213ccfb52bbb433f889ff606428ef`;
both served patchers and existing ROMs/saves remain unchanged. See
[the specification](../../specs/V3_SCENERY.md).

## Shared seasonal scenery preparation

`build/v3-scenery-gold-tree-01/` contains the complete converted artwork
dependency for the donor's golden-shovel tree route. One table-following scenery
adapter feeds the shared graphics compiler. It retains all fourteen foreground
identities across cherry, ordinary, winter, and Xmas owners, forty descriptors,
52 body-list uses, and 24 shadow-list uses, deduplicated to 37 native objects.
Growth sizes, the dead sapling, all four stumps, position arrays, shadow lengths,
adjustment flags, and every source palette/term remain represented.

The objects total 65,632 bytes and 199 triangles; all fourteen converted palettes
add 448 bytes. Each season references nineteen objects totalling 29,408 bytes.
These are prepared resource sizes, not an installed memory measurement. Runtime
rendering/allocation, growth/death, collision, cutting/shaking, selected-only
reward acquisition, ordinary appearance, and hardware remain unimplemented or
unverified. No tool choice is enabled by preparation.

- Asset report SHA-256:
  `3e4247f0285b741cfff3e758d853d39fc1e962a0d7ca3eb2fcabcfec5fc4ec79`.
- Inventory SHA-256:
  `a11d26ae1ae74ebc3559f2ca4f64b6dfdd24e0b34209dbcc53c5223ccb832c33`.
- Native palette bank SHA-256:
  `c819376b0eb34110a36c2d1ef976754236ade95408316be85683611dfbf53887`.

The shared converter supports explicit caller-owned palette slots and complete
caller-loaded vertex arrays. Default furniture/equipment requirements remain
unchanged. Gold bodies retain slot eight; shadows retain the caller's adjusted
vertices rather than loading a static replacement. Complete consumer hashes,
draw callbacks, ordered parts, unused-list rejection, source/output hashes, and
strict prepared formats constrain the category. No per-item converter is added.

`python3 -m unittest tests.test_v3_scenery -v` passes six checks in 2.101 seconds.
The reused complete-artwork assertion independently compares every texture
pixel, vertex field, native triangle, command state, texture stride/wrap/shift,
and palette slot with the source. Additional checks cover all 224 palette
colours, the full term selector, cross-season identities, shared roots,
unknown/conflicting inherited state, changed consumers/callbacks/shadows,
missing resources, invalid selections, and rejection by unrelated installers.
Seventeen shared-format checks pass in 0.964 seconds. The existing ordinary
installed-model emission check also passes, retaining its exact generated code.
Syntax compilation and `git diff --check` pass.

The first scan rejected legitimate null rows in the full drawing table. The
adapter now requires aligned relocated roots and zero stored pointers while
retaining unused rows; selected descriptors still require every actual
dependency. Conversion then completed in one build. No emulator fixture was
needed or run: this batch installs no runtime code and does not replay old builds.

The current cartridge remains ABI 148 at
`build/v3-shared-balloon-menu-04/build-lock.json`. The main ABI-109 lock, existing
ROMs/saves, format-3 compatibility restrictions, and both served V2 patchers are
unchanged. Continue shared seasonal rendering and the real planting/growth/shake
route using these assets; do not reconvert them or treat seeded pockets as
acquisition. See [the specification](../../specs/V3_SCENERY.md).

## Shared ordinary balloon menu

The ABI-148 proposal is `build/v3-shared-balloon-menu-04/build-lock.json`.
All eight selected balloon parents gain the donor outdoor `Grab` / `Let Go` /
`Quit` menu through the shared category installer. Indoor placement, restricted
fields, present/quest priority, and unselected/native items retain their proper
menus. The four golden-tool choices, 128 experimental options, main ABI-109
lock, and both served V2 patchers are unchanged. This is not a hardware handoff.

- ROM SHA-256:
  `9b310665f095ac42483a4830b3ffd37491f5a3cc570230113c891337e87487d1`.
- Report SHA-256:
  `93b18b506db4ee018173f71aeeb07ec471ed9f8abc56035a366f418a310f0a01`.
- UPS SHA-256:
  `c04a4d7bc6b0e549095c6d5a756cd339807d2a9bc70594331f403c7d0885da48`.

The 680-byte menu group occupies `804AFBF0..804AFE98`, inside unused existing
module space. Type selection starts at `804AFBF0`; the callback is `804AFCD8`.
It calls the existing release queue before consuming a pocket item, preserving
items when the selected shape or owned actor is unavailable. Accepted releases
use the actual pocket setter, return-tag initializer, and close/sound path.
Native exchange mode inserts the current hand item into the vacated slot.
The existing wrapped-import pocket hook and furniture-menu hook remain intact.

The tag owner grows by 400 bytes to 44,784 bytes, with a 3,760-byte relocation
resource. A complete copied 44-row table plus the new row at `8087A070` retain
all original callbacks and translated text. All sixteen table references move,
including dynamic money-menu writes. Only the wrapper call loses its internal
relocation; the new resident callback is deliberately not relocated.
The shared-menu reservation grows by 384 rounded bytes. Complete owner hashes,
declared sizes, DMA identities, cartridge-tail bounds, and unused destination
space constrain the shared resize/storage path. No save/profile/module growth
or new asset conversion occurs. The official label has one provenance entry.

### Verification and corrections

`python3 -m unittest tests.test_v3_balloon_menu -v` passes four checks in 6.955
seconds. The sanitizer fixture covers all shapes, four field contexts, all
present/quest flags, profile rejection, ordinary/exchange consumption, rejected
queue item retention, invalid slots, absent pointers, and call ordering. The
cartridge checks verify complete source/native helpers, official attribution,
all original rows at two relocation bases, exact code/owner changes, allocation,
unchanged resources/saves/options, all/empty composition, UPS reconstruction,
and reusable resource tails. Syntax compilation and `git diff --check` pass.

Builds `01` and `02` stop before output on incorrect donor-relocation tuple
ordering and an overstrict stock-helper comparison. The verifier now checks the
complete original helpers plus their exact previously installed V3 hooks; no
unknown differences are accepted. The first source test compared in-memory
tuples with serialized lists; normalizing that representation fixes the test.

Inspection of the actual native selector identifies a real address error in
build `03`: the current field byte is `80136EA1`, not the saved town-data area
at `80126EA1`. Build `04` derives the field address from the original MIPS loads
and supplies that checked value to the compiler. No affected build is handed off.

### Native evidence

The initial fixture, `build/smoke-v3-balloon-menu-01/`, verifies startup and the
complete installed module but cannot allocate its unnecessarily large 135,168-
byte test block. Native malloc returns zero. No menu callback is executed.
The corrected fixture shares disjoint temporary parent/overlay fields and uses
118,784 bytes, retaining bounds and guards. This is a fixture allocation issue,
not evidence that the real menu's 384-byte increase fails.

The justified retry, `build/smoke-v3-balloon-menu-02/`, runs build `04` and passes:
92 records, 55 component assertions, and four startup/final assertions.
Results SHA-256:
`20d343582e7019076326c3a546b9ba8edf9357a062f4eb95d161517f0127a2ac`.

It loads and relocates the actual complete expanded tag owner, checks first/last
shape classification in all four fields, present/quest priority, and unselected
fallback. Actual native cursor movement reaches all three rows and stops at
both ends. Actual native A dispatch selects `Let Go`, reaches the resident
handler through the installed label callback, transfers only the selected
pocket item through the native setter, initializes return-tag state, closes the
menu, and queues the complete balloon release union. Both ordinary emptying and
exchange replacement pass. Saved import state, player, and complete code remain
intact; touched state and the checkpoint are restored, fault/memory guards pass,
and the isolated silent emulator exits cleanly. No user save or physical audio
is used, and the fixture performs no FlashRAM writes.

The fixture uses a classification jump bridge and a test-only final close
callback. It does not render the menu, replay full flight, or establish ordinary
gameplay or hardware appearance. Reuse the unchanged release/look/fall/actor
evidence instead of rerunning those components.

### Next work and compatibility

Continue source acquisition events, including gold-tree growth/drop, collection
completion NPC/events, and perfect-town acquisition. Keep golden tools disabled
until their full ordinary routes are implemented. Retain the explicit gameplay/
hardware gaps. Format-3 saves still require matching/equal-or-larger import
profiles and must not be loaded in V2 or older format-1/2 V3 builds. No migration
is added here; preserve backups. Empty selection remains exact corrected V2-12.

## Shared balloon release, exchange, and fall

The ABI-147 proposal is `build/v3-shared-balloon-release-04/build-lock.json`.
It connects all eight balloon shapes to the native creature action, donor
tracking/continuation, fall/get-up handoff, and inventory exchange. Ordinary
inventory `Let Go` selection remains unfinished. The four golden-tool choices,
main ABI-109 lock, and both served V2 patchers remain unchanged. This is not a
playable V3 handoff or original-hardware verification.

- ROM SHA-256:
  `0fc8b305c38e1a6b971552a519f5a811af928d3ba16c764d8aaa2e8a58343479`.
- Report SHA-256:
  `2d706106ab5d401384133fe164f18fe54733ad5e708070311c44f4f92d8c0666`.
- UPS SHA-256:
  `98bd56c5d30f16cdfbf659186671ef8e6c6259b3ff7ebe05264f852f12807bd7`.

`tools/v3_balloon_release.py` extends the shared category installer, binding
complete donor release/get-up, equipment setter, submenu setter, and exchange
functions plus checked native APIs. Two actual action-81 callback values and
four native instruction windows connect the consumers. Only the displaced
Look JAL loses its internal relocation. Unrelated owners, resources, callbacks,
save/profile data, and 128 experimental options remain intact. The actor's
unused player-extension words hold continuation and fallen shape, so the
player remains `13B0` bytes with no further scene or permanent allocation.

The request/setup/transition/queue group occupies 1,656 bytes at `804B1100`;
the public queue is `804B1680`. Look occupies 820 bytes at `804AEAA0`, and
fall/get-up 552 bytes at `804ACBE0`. Exchange grows from 760 to 868 bytes at
`804AD650`. All fit previously unused reserved suffixes. Existing actor,
descriptor, category/held/room artwork, deferred rewards, and end guards retain
checked bounds. Native fish/insect setup and Look remain the fallback.

### Verification and build work

Five focused tests pass in 8.903 seconds:
`python3 -m unittest tests.test_v3_balloon_release -v`.
Two sanitizer fixtures cover all shapes, exact source pose offsets, deferred
flags, rejected/foreign requests, source head limits and angle wrapping,
pending/hidden flight, minimum timing and continued waiting, get-up pose loss,
missing/unselected actor retention, title-demo equipment protection, native
creature fallbacks, and all-shape exchange queue/warning routing. Cartridge
checks bind complete source/native functions, every installed code/hook/table
change, one removed relocation, resource retention, unchanged saved formats,
all/empty optional composition, 128 choices, UPS reconstruction, and tail reuse.
Syntax checks and `git diff --check` pass.

Build `01` contains release/look/fall. Build `02` stops before output because
the new fixed queue-entry linker assertion lacks its required in-section
semicolon. Build `03` stops before output because dependency validation also
compares a private static helper's address. The corrected installer checks
public shared symbols only; it retains exact code/size/source checks. Build `04`
adds the queue and balloon exchange. No failed proposal is handed off.

### Native evidence

`build/smoke-v3-balloon-release-01/` on build `01` passes on its first attempt:
114 records, 74 component assertions, and four startup/final assertions.
The cartridge-loaded callbacks and actual relocated player hooks execute new
release setup for first/last shapes, complete union/flag transfer, native body
setup, source position/frame/speed, pending/hidden continuation, exact two-step
head smoothing, source fall pose, equipment clearing, no-loss missing-actor
recovery, source-priority get-up handoff, and native priority rejection.
The full player and flying actor, animation banks, live save/profile data, and
other touched state are restored. Stack/memory guards pass; the checkpoint
restores, resumes, and exits cleanly without a CPU fault. Results SHA-256:
`b00a41b3f8b4f787841f4559a22a754297d06cfe2c89528ca31d354198cb46d7`.

Look and fall binaries are unchanged in final build `04`, with SHA-256
`f7f2fe8eeadd044f3b2d26e468e5030a59363d67ee9175db66fbf0279ef27cf8`
and `7ba78eecb0090738312f2278d1b8c233b7b1d2d7acd1c345cce0196b28804984`.
Reuse that evidence; do not replay the completed prefix for the added queue.

`build/smoke-v3-balloon-exchange-01/` uses final build `04` and passes on its
first attempt: 86 records, 53 component assertions, and four startup/final
assertions. It loads the complete actual tag owner, verifies the complete
equipment module with its one live actor count, and executes the installed
exchange entry for first/last shapes with and without the deferred reward.
The queue, complete request fields, source menu-close direction, two changed
registered callbacks, current release setup, flying-actor request, and idle or
reward continuation all pass. It restores the player, flying actor, banks,
live state, and checkpoint; fault/guards pass and the emulator exits cleanly.
Results SHA-256:
`50e32adb523e4829127e0f28eff91cce8c5018640d0c322e44804b7407d36dd5`.
The result's legacy `actual_registered_callbacks: 4` field counts four verified
slots; this focused variant executes only the two release callbacks. The fixture
now distinguishes verified slots from executed callbacks without rerunning it.

These are silent, isolated component checks with test-only jump bridges. The
exchange fixture stubs menu close and supplies the completed-flight condition;
the separate release fixture verifies the actual pending/hidden Look decision.
No user save, physical audio, or FlashRAM write is used. Ordinary menu interaction,
a full real-time release/fall sequence, GPU appearance, and hardware remain
unverified. Retain the existing actor/model/physics evidence; no replay of those
unchanged components is needed.

### Next work and compatibility

Install the donor outdoor `Let Go` tag row and pocket-transfer handler, retaining
room placement indoors and present/quest priority. Reuse the public queue; check
actor availability before removing an item. The official label is in donor
`mTG_tag_word_fly`, REL data `00082A50`; add its locator to the single provenance
catalogue when the label is installed. Continue source gold-tree, event/NPC
completion, and perfect-town acquisition afterward; do not enable golden tools
before their complete paths work.

No new save migration is introduced. Format-3 imported saves still require
matching/equal-or-larger selected profiles and must not be loaded in V2 or older
format-1/2 V3 builds. Preserve backups. Empty selection remains exact corrected
V2-12. No ordinary save/restart or hardware claim is added by this batch.

## Shared flying-balloon actor

The ABI-146 proposal is `build/v3-shared-balloon-actor-04/build-lock.json`.
The shared installer adds complete donor flight/hide behaviour for all eight
shapes, private model/motion banks, reflection drawing, and player creation.
All 128 experimental choices, four disabled golden tools, saved format/profile,
main ABI-109 lock, and both served V2 patchers remain unchanged. Ordinary release,
exchange/look continuation, and fall/get-up consumers are still required; this
is not a playable V3 handoff.

- ROM SHA-256:
  `492c4e42e3bad66807bd138a0be12759bea0c42b76a6d1620f98d536824a3e81`.
- Report SHA-256:
  `338e3fa6642aace40118ccacdcd22541e1a7b42cd8983c12c2647f12cae15e3b`.
- UPS SHA-256:
  `b4ff499e6dfffdd75b23c765803918f2411d14167b2cb9cd84f28d56ff757a24`.
- Code SHA-256:
  `fe20a698c5bb50f63f66fe08150b11286ce965eb703b542e3e9a2e68ae0e1767`.

The 2,268-byte code group uses `804AC300..804ACBDC`; the 96-byte native
descriptor/profile uses `804AEA40..804AEAA0`. Both occupy checked unused space
in the existing 72-KiB module. Descriptor lookup adds `CB` while retaining `CA`,
the `C9` sentinel, and all original descriptors. The core player allocation at
`8010BCEC` grows sixteen bytes to `13B0`. Ctor call `808DD79C` dispatches the
wrapper and removes only relocation `4402AA4C`; other player code and relocation
remain. The new actor owns `2080` bytes including complete 5,728-/1,440-byte
banks. Additional selected-profile scene allocation is 8,336 bytes; no permanent
reservation or heap limit grows. Failed allocation leaves a null player slot.

`python3 -m unittest tests.test_v3_balloon_actor -v` passes four checks in
8.068 seconds. The sanitizer check includes the actual shared equipment-selector
implementation, all shapes, both pose-entry modes, motion/hiding, segment
retention, each transfer-failure boundary, allocation failure, no-selection,
and invalid-shape fallback. Cartridge checks bind complete donor actor/profile,
source/native APIs, complete retained resources, exact code/descriptor/hooks,
one removed relocation, unrelated owners, unchanged saves, all/empty composition,
128 options, UPS reconstruction, and reusable resource-tail ownership.
Syntax compilation and `git diff --check` pass.

### Native evidence and corrections

The first run on build `01` reaches real actor creation and flight setup, then
catches a wrong loader API: the implementation called the origin-offset reader
instead of the VROM reader, so model contents differ. This is an actual code
defect, not a harness exception. The fix uses `800B1650`, checks transfer bounds,
and pins all three actual resource API bindings. No affected build is handed off.

`build/smoke-v3-balloon-actor-02/` on corrected build `02` passes actual ctor/
descriptor identity, independent loading for all eight shapes, both entry poses,
two representative reflection drawers with four source lists each, donor
half-step movement, animation speed/frame, source height-based hiding, segment
and matrix restoration, and work/graphics/stack guards. It contains 100 records
and 71 passing assertions, then hits a fixture type error parsing a hexadecimal
item ID. Results SHA-256:
`e4d89f871d943bb229f12abcfbf47c1f9965baa1e2b1e28f89c31fe1fb16ae43`.
Build `03` has the same ROM as `02`, with strengthened build receipts.

The corrected fixture on build `03` reaches the disabled-profile case and finds
another actual code defect: treating the kind-or-minus-one selector result as
a boolean accepts `-1`. Its 101 records contain 71 passing assertions; the full
run is not a pass. Results SHA-256:
`a97f89cf4dd69624557688366d825dc3a8b60055d1374e36b475863fbbb83073`.
Build `04` requires the exact selected kind `91+shape` for both construction and
release. Host tests use the real selector, not a boolean stand-in.

The final native scenario targets changed selection and cleanup rather than
replaying the completed model/physics/drawing prefix. Object-code sections for
`load`, `source_step`, and `af_v3_balloon_main` are unchanged between `03` and
`04`; the entire drawing object retains SHA-256
`5b8b93a02a67886362136fa5bf25339dd35dc941efe800f1b42381e9f0674424`.
Reuse the prior component evidence for those unchanged implementations; do not
describe either interrupted full fixture as successful.

The focused command is:

```sh
python3 tools/emulator_smoke.py \
  --rom build/v3-shared-balloon-actor-04/animal-forest-v3-asset-loader.z64 \
  --output build/smoke-v3-balloon-selection-01 \
  --scenario tests/v3-player-balloon-selection-scenario.json \
  --xvfb /home/discordian/Games/OpenRSC/headless/vendor/usr/bin/Xvfb \
  --seconds 180 --expansion-pak --no-initial-screenshot
```

The focused current-cartridge run completes successfully with 41 records and
26 passing assertions. Results SHA-256:
`64e13bacd0e4ff0bc7cf00c4ef783a5ff0f97d04ab46a33bbbc32662218c3cdd`.
It verifies actual
player-created actor ownership, rejects an unselected shape without changing
its actor, accepts the independently enabled eighth shape, retains saved data,
restores the complete actor and live state, restores its checkpoint, resumes,
checks the fault/save/equipment guards, and exits cleanly. The fixture uses small
test-only jumps to actual loaded upper-memory code, not replacement game code.
All emulator runs are silent and isolated; no user save or FlashRAM write is used.
GPU appearance, normal scene teardown, ordinary release/fall interaction, and
original-hardware behaviour remain unverified. Format-3 incompatibility and
matching/equal-or-larger profile requirements remain unchanged.

### Next action

Connect the owned actor to the shared release setup, source head tracking and
continuation result, exchange branch, and tumble/get-up handoff. Preserve native
fish/insect behaviour and deferred golden-shovel settlement. Do not clear an item
when the player lacks its flying actor, and do not label room-form placement as
source balloon release. Keep source acquisition events and all four disabled
golden choices in scope. See [the specification](../../specs/V3_BALLOON_RELEASE.md).

## Shared reward inventory exchange

The ABI-145 proposal is `build/v3-shared-reward-exchange-02/build-lock.json`.
The shared installer connects normal-drop/empty-hand rewards and deferred bury/
fish/insect completion, preserving the native placement, warnings, animations,
and actual request permissions. It carries one source flag through existing
submenu/request/main unions, with clearing on ordinary requests and no write
after rejected requests. All 128 experimental choices, four disabled golden
tools, saved format/profile, memory reservations, main ABI-109 lock, and both
served V2 patchers remain unchanged.

- ROM SHA-256:
  `ad0a50c1f19f9826cf4f528440a8f6e1606a1ed2479b3eb17ae10cd2d0060037`.
- Report SHA-256:
  `bd684073a418be6085841aaad47c61d89fd3b23d970d858c1e3cc3eb5e88be7d`.
- UPS SHA-256:
  `36356f6d77ef25c20c4d7d7d2427aa5ebfb5190da8456c71ac32b8e5bd15fcd7`.
- Exchange code SHA-256:
  `c138971221125ec793f85e18d9179abb2472b0e23881ed5f8269a1fbef690a95`.
- Deferred code SHA-256:
  `5cba56ae9d86356ccfb29ee003888259588ce99914739d8289e40b6fe7caf4f7`.

The 760-byte exchange group occupies `804AD650..804AD948` (exclusive end), after
the complete ground adapter. The 944-byte deferred group occupies
`804AE690..804AEA40`, after complete event-stock code. The older linker limits
are tightened to protect these shared suffixes from future growth. The final
build regenerates source receipts for those limits; its complete ROM and UPS
equal the first build, preserving the native evidence below without a rerun.
There is no resource truncation or allocation growth.

Seven instruction windows and four actual callback entries change. All native
relocations and all other owner/resource bytes are retained. The tag entry keeps
its original frame, and its resident bridge uses the actual return PC to resolve
native tag helpers. The new C exchange uses the existing wrapped-parent mapper,
source completion query, and selected-parent predicate. It preserves full hand
and menu identities, existing creature-index conversion, placement failure,
warnings, menu-close arguments, and source sound behaviour. Ordinary and
selected golden shovels both satisfy the burying-equipment check.

The flag lives at submenu `+20`, request `D70`, and active action `D20`. Ordinary
core bury/fish/insect setters clear it. The native common player request clears
only actions 63/81, preserving other action unions. Actual submenu/setup table
callbacks copy the flag after accepted requests and retained native setup.
Flagged burying cannot use the native early-movement escape before animation
completion. Fish/insect release uses 42 native updates, corresponding to 84 source
updates, then idle or celebration with the source priority and timer clamp.
Full balloon flight and its Look result remain unimplemented, not substituted
with this fish/insect continuation. No text is added; provenance is unchanged.

Two sanitizer and three cartridge/composition checks pass initially in 8.473
seconds and on the final source-receipt build in 9.853 seconds:

```sh
python3 -m unittest tests.test_v3_reward_exchange -v
```

Host tests cover incoming/outgoing/selected/completed/wrapped cases, empty hand,
normal drop and source sound, fish/insect requests, successful/failed placement,
ordinary/golden shovel burying, unchanged failed-warning requests, accepted and
rejected flag transfer, original setup, flagged/unflagged interruption rules,
all release-delay updates, boundary retry/clamp, and null arguments. Cartridge
checks bind ten complete donor functions and all native APIs, reject changed
source/core/player/tag data, check exact instruction/table changes and every
unrelated resource, retain all relocations/saves/selections, reconstruct the
original-ROM UPS, verify all/empty profiles, and retain future resource-tail reuse.
Python syntax checks and `git diff --check` pass.

The first silent native attempt passes 142 result records and 92 assertions:

```sh
python3 tools/emulator_smoke.py \
  --rom build/v3-shared-reward-exchange-01/animal-forest-v3-asset-loader.z64 \
  --output build/smoke-v3-reward-exchange-01 \
  --scenario tests/v3-player-reward-exchange-scenario.json \
  --xvfb /home/discordian/Games/OpenRSC/headless/vendor/usr/bin/Xvfb \
  --seconds 180 --expansion-pak --no-initial-screenshot
```

Results SHA-256:
`9aee900077a7e5db3d66ecac8ba78cff15871107e71f28e3aeac787f2d973b3b`.
The cartridge-loaded tag is completely relocated and its actual entry runs the
empty-hand, fish, and insect branches for selected, completed, and disabled
profiles. The native core setters, common player request, four installed
submenu/setup callbacks, and both actual transition entries execute. Clearing
is limited to the relevant actions; rejected requests preserve the old flag.
Native setup selects the intended actions, burying waits for animation end,
release waits until its sampled boundary, and completion selects the proper
idle/reward request. The saved celebration remains unmarked until settlement.

The fixture uses test-only jump bridges to the installed callback pointers and
a test-only menu-close callback that records its arguments. Bury setup uses
item zero; release setup receives an existing actor to avoid spawning a creature
into this component fixture. Those limits are explicit: no ordinary ground
placement, burying an actual item, spawned-creature lifecycle, full menu
interaction, balloon flight, FlashRAM write, or hardware is claimed. Complete
module/state/stack guards, actor/motion-bank/native-payload/profile/reward/
submenu/audio-state restoration, checkpoint restoration, resumed game, and clean
exit pass. Audio is disabled and no user save is used. The native fixture passes
within the harness budget without using a retry.

Next implement the complete source balloon release actor, its Look/continuation
rules, and exchange/tumble consumers. The current exchange still uses its prior
placement path for balloons, which is not source release behaviour. Gold-tree
growth/drop, collection-completion NPC/event support, and perfect-town reward
acquisition remain required. Keep all golden choices disabled until their full
paths work. Format-3 saves require a compatible build and matching/equal-or-larger
profile; older format-1/2 builds and V2 cannot load them. Preserve backups.

## Shared reward collection consumers

The ABI-144 proposal is `build/v3-shared-reward-pickup-01/build-lock.json`.
The shared player-action stage connects all four non-exchange collection tails
to the source golden-shovel celebration, using an active-player completion query
shared with subsequent event/menu consumers. It retains native item transfers,
animations, early returns, full-pocket paths, and the source's different priority
settlement ordering. The 128 choices, four disabled golden tools, format-3 saves,
main ABI-109 lock, and both served V2 patchers remain unchanged.

- ROM SHA-256:
  `328f8ef72408fdc5e6fb5808754e95a7bc7342758d482337934f978a180fdcc6`.
- Report SHA-256:
  `0f94512ef6606b2bd073482e01cf14a194a0814462e8045ace21fb90807b18df`.
- UPS SHA-256:
  `92c9c83c697491c1a2f92bf4f0630a9dd52934bb616565f1283dfbf6c9f051a8`.
- Code SHA-256:
  `916153c8f9591cbe856f5a8d00dd2e09d3610fb6cf17812b0395ac5673bd9881`.

The complete 424-byte helper fits `804B2620..804B27C8` (exclusive end), between
retained requests and bobber artwork. The query at `804B2764` supports all four
reward types and four player slots, returns minus one for unknown identities,
and never marks completion. Four checked 28-byte native tails call pickup at
`804B2620`; eight old JAL relocations are removed. All remaining owner bytes,
relocations, resources, callbacks, profiles, and saved formats are retained.
The complete source/native bodies, APIs, actual action bindings, and incoming
control-flow guard are checked. Native Putaway is action 62, not donor action
63; the installer uses the actual native setup/main pointers. No new English
text is introduced, so the single provenance catalogue remains unchanged.

One sanitizer and three cartridge/composition checks pass on the first run in
6.404 seconds:

```sh
python3 -m unittest tests.test_v3_reward_pickup -v
```

They cover four-player/type queries, invalid arguments, selection/repeat
rejection, source priority order, denied requests without idle fallback,
unchanged actor/game data, complete source/native bindings and damage rejection,
exact installed tails/relocations, unrelated resource retention, unchanged
saves/selections, all/empty composition, UPS reconstruction, and future resource
tail reuse. The mock selected-kind value was then corrected from a generic
accepted kind to the actual shovel kind 90; that host test passes again.
Python syntax compilation and `git diff --check` pass.

The first silent native attempt passes 141 result records and 102 assertions:

```sh
python3 tools/emulator_smoke.py \
  --rom build/v3-shared-reward-pickup-01/animal-forest-v3-asset-loader.z64 \
  --output build/smoke-v3-reward-pickup-01 \
  --scenario tests/v3-player-reward-pickup-scenario.json \
  --xvfb /home/discordian/Games/OpenRSC/headless/vendor/usr/bin/Xvfb \
  --seconds 180 --expansion-pak --no-initial-screenshot
```

Results SHA-256:
`d75155d24a0f92dfa85e5496ac8c27354ed151d5da64789201c3dd7ee765cdac`.
The shared probe calls each complete cartridge-loaded native transition, with
actual relocation and native request APIs. It checks first pickup, repeated and
unselected shovel pickup, ordinary items, animation-not-ended returns,
higher-priority rejection, and the three original full-pocket exchange requests
with complete position/item data. All four players and reward types resolve
through real saved flags. A query-only test jump bridge reaches upper memory;
there are no substituted callback tables or fabricated result functions.
The four golden-tool options remain disabled in the cartridge: the fixture
temporarily selects the shovel in both live and working profiles, then restores
the original profile, reward state, actor, native payload, active pointer, and
common flags. Module/state/stack guards, checkpoint restore, resumed game,
and clean exit pass. No user save, physical audio, or FlashRAM write is used.
The native check passes without a retry and within the 30-minute harness budget.

This is direct transition evidence, not ordinary pickup, full-menu interaction,
source acquisition, or original-hardware proof. The unchanged Putaway inventory-
opening branch is checked as retained code but is not executed by this fixture.
The next shared batch must carry the donor's exchange reward condition through
normal drop, empty-hand, buried-item, fish/insect release, and balloon release
endings. Native Putin lacks the source deferred flag and needs actual state/
transition integration. Do not replace these timings with an immediate reward.
Gold-tree growth/drop, event director/NPC collection rewards, and perfect-town
acquisition remain required. Keep all golden choices disabled until their full
paths work. Format-3 saves still require a compatible build and matching or larger
profiles; older format-1/2 builds and V2 cannot load them. Preserve backups.

## Shared reward action registration

The ABI-143 proposal is `build/v3-shared-reward-actions-01/build-lock.json`.
The shared category installer registers all twelve source callbacks for actions
118–120: both golden-tool celebration variants and the golden-axe waiting action.
It connects source-priority requests, the submenu callback, the axe delay,
existing messages/animations/fanfares, and persistent settlement. Ordinary
source acquisition events remain unfinished; the four golden-tool choices stay
disabled. The 128 experimental choices, format-3 saves, profiles, allocations,
main ABI-109 lock, and both served V2 patchers remain unchanged.

- ROM SHA-256:
  `be64382472c2cba2d132ade0a9aff709ddcb770cadf343d26cc5576bcbf5dedd`.
- Report SHA-256:
  `4f2198c301447045790eb32e16ba938de93c90290914dfefcc6d104414540054`.
- UPS SHA-256:
  `5d209b6cb4254626e13ab8a5ab5516d08257173f31862345910f9a56ee4a0b29`.
- Request code SHA-256:
  `c385d18bcd1035324820eacb043a901e486f86768cef34bbb349b7beb5931c4c`.
- Waiting code SHA-256:
  `5c34771fa003edda98dff67ecca6222a4214169688ba62841b776cdc0cdf7bde`.

The 308-byte request group fits `804B24E0..804B2614`, before existing bobber
artwork. The 668-byte waiting group fits `804B3C90..804B3F2C`, before the icon
guard. The complete module, prior code, and zero reservations are verified;
all unrelated table entries and resources remain. No native owner or relocation
changes. Complete donor table consumers and callbacks are re-resolved and bound
before installing pointers. The existing shared native dispatcher handles both
resident callbacks and the unchanged native net-reset callback.

Requests preserve source priorities 31/34/33 for submenu/event/axe wait and the
actual native permission/priority predicates. A rejected request does not alter
its requested type. The wait uses the native equivalent of the source interval,
retains complete per-frame behaviour, and supplies the donor's WAIT1 continuation
predicate, absent from the native initializer. Both animation frames continue
when valid; otherwise the source restart/morph applies. The complete 320-source-
update delay becomes 160 native updates, then requests celebration on the next
update. Rejection retries without restarting the timer. See
[the specification](../../specs/V3_REWARD_ACTIONS.md).

One sanitizer and three cartridge/composition checks pass on their first run,
in 7.081 seconds:

```sh
python3 -m unittest tests.test_v3_reward_actions -v
```

They cover every reward type/request route, denied and missing-actor paths,
unchanged actor bytes, priorities, complete wait duration and retry, all source
continuation branches, null inputs, complete source/native bindings, changed
source/API rejection, all twelve actual callback slots, remaining null actions,
retained tables/resources/save code, exact empty/all composition, all 128 choices,
original-ROM UPS reconstruction, and future resource-tail reuse. Python syntax
compilation and `git diff --check` pass.

The first silent native attempt passes 73 records and 53 assertions:

```sh
python3 tools/emulator_smoke.py \
  --rom build/v3-shared-reward-actions-01/animal-forest-v3-asset-loader.z64 \
  --output build/smoke-v3-reward-actions-01 \
  --scenario tests/v3-player-reward-actions-scenario.json \
  --xvfb /home/discordian/Games/OpenRSC/headless/vendor/usr/bin/Xvfb \
  --seconds 180 --expansion-pak --no-initial-screenshot
```

Results SHA-256:
`199df8822e4375eb1a7a2c66b8716d3ca396a0500fd3017b45378e7dfaf07a84`.
The shared representative probe uses the actual loaded player owner and actual
registered setup/main tables without substituting callback slots. It executes
both celebration variants, native priority rejection, sampled axe-delay
boundaries, the wait-to-celebration-to-idle transition, and actual persistent
settlement for shovel, net, and axe. The complete shared module remains unchanged.
Stack/bridge/state guards, restored actor/motion banks/native payload/flags/BGM,
checkpoint restoration, resumed game, and clean exit pass. The fixture uses
test-only jump wrappers for resident requests and simulates completed message
state; it does not claim a complete player conversation, normal acquisition,
full native delay playback, FlashRAM I/O, or original-hardware verification.
No user save is used, and no physical audio is played. Native fixture work took
less than five minutes; the retry allowance is unused.

Next connect the source collection-completion event director/NPCs, perfect-town
reward conversation, gold-tree route, and remaining shovel pickup/submenu
consumers. Keep original source conditions and official dialogue; do not replace
missing events with shops or arbitrary gifts. Format-3 saves still require a
compatible build and matching/equal-or-larger profile; older format-1/2 V3 builds
and V2 must not load them. No save-format change occurs in this batch.

## Shared reward persistence

The ABI-142 proposal is `build/v3-shared-reward-state-02/build-lock.json`.
The shared player-action installer adds separate saved trophy/celebration flags,
the complete persistent settlement callback, and player-delete clearing. All
128 experimental choices and selected identities remain. The four golden-tool
choices stay disabled pending action registration/request routes and source
scene/NPC/tree acquisition. The main ABI-109 lock and both served patchers remain
unchanged; empty selection is exact V2-12.

- ROM SHA-256:
  `eb0bd296424761992553b88ac654609db7e38a1f6ce57b68c4f11d7bc6769f29`.
- Report SHA-256:
  `2b10f9e7f2782f2c10eb6f5cb7c67d7a029c17c9918e06179233b48844649f47`.
- UPS SHA-256:
  `3bfde87c0b0dab6e188d2fca6c80fd5da244f39c4b671cb324a07a63796f6418`.
- Reward helper SHA-256:
  `41b93de3d76df183cc59d9b57fd0a50c4bbe51afabcc1edc9b0d32ebdb000e09`.
- Extended codec SHA-256:
  `329a52be7f396502d2a7fd2b294741e501026b13782eecd668647c6c623afd07`.
- Rebuilt save runtime SHA-256:
  `167a0d8c91d9f1f78a5a1a76c02c259d70894b0c525d296001ebef412f292f4c`.

Format 3, registry 2, adds 48 bytes without moving existing profile/catalogue
fields. Each player has 33 trophy bits and four independent celebration bits.
The working state is 880 bytes; the complete runtime state is 912 bytes with
guards at `8046C380`. Valid NAFJ and format-1/2 banks migrate with new flags clear
and prior ownership retained. Older format-1/2 builds reject format-3 saves.
Matching/equal-or-larger profiles remain required; never load imported saves in
V2. Preserve backups. Offline receipts and private browser exports use the
actual format-3 report warning; no served export is rebuilt.

The 772-byte helper reuses the checked retired codec body at `8046B408`, keeping
all live public entries and original native bridges. The 2,248-byte codec at
`8046D000` retains the item-reader boundary at `8046D8DC`. Startup actually loads
the complete 12-KiB codec/item-reader/lamp resource at VROM `024A1080`; its suffix
is retained exactly. The 1,867-byte runtime retains every entry address. No ROM
blob, module, heap, or permanent reservation grows. Details and source semantics
are in [the specification](../../specs/V3_REWARD_SAVE.md).

Five focused codec/host/cartridge checks pass:

```sh
python3 -m unittest tests.test_v3_save_rewards -v
```

The first combined invocation passed both codec and both cartridge checks, but
the sanitizer fixture failed compilation because renaming the included earlier
test's `main` removed its implicit successful return. Adding an explicit return
fixed the fixture; rerunning only `RewardStateHostTests` passed. No completed
cartridge checks were replayed. The separate `RewardCompatibilityNoteTests`
check passes in 0.050 seconds and covers the new export warning and retained
older-format wording. Python syntax compilation and `git diff --check` pass.

Checks cover complete independent format-3 encoding, all three migration inputs,
older codec rejection, profile additions/removals, illegal/reserved flag bits,
CRC/payload binding, unchanged failure outputs, overlapping buffers, all four
players/all 33 trophies/all four celebrations, independent catalogue data,
new-town reset, prepare/read/commit, player deletion, active-player settlement,
foreign-pointer rejection, and no erase/write on invalid flags. Cartridge checks
bind actual resource/code hashes, complete source functions, stable entry maps,
only declared changes, retained resource suffixes, guards, 128 selections,
empty/all reconstruction, original-ROM UPS reconstruction, and future tail reuse.

The first silent native attempt passes 67 records and 50 assertions:

```sh
python3 tools/emulator_smoke.py \
  --rom build/v3-shared-reward-state-02/animal-forest-v3-asset-loader.z64 \
  --output build/smoke-v3-reward-state-01 \
  --scenario tests/scenarios/v3_save_rewards.json \
  --xvfb /home/discordian/Games/OpenRSC/headless/vendor/usr/bin/Xvfb \
  --seconds 180 --expansion-pak --no-initial-screenshot
```

Results SHA-256:
`febee30b8c0b46a1b3b970ffdfb8b9f1c9342bc71607fd013535e9df2614b244`.
The existing format-aware save fixture verifies the complete loaded prefix and
active extra resource, then executes actual codec/runtime/settlement/private-clear
entries through test-only jump wrappers. Migration, complete format-3 packing,
rejection atomicity, real payload commit, four-player flags, fanfare deletion,
selected-player catalogue/flag clearing, stack/output/state/code guards, and
absence of CPU faults pass. It restores the native payload, expanded state,
active player pointer, BGM state, allocation, and checkpoint, then exits cleanly.
No physical FlashRAM I/O is performed. This does not establish ordinary
save/restart, complete reward acquisition, GPU appearance, or original hardware.
The native retry allowance is unused.

Build guards rejected two overlarge codec compilations before a shared external
validator and single version/registry read fitted the existing boundary. The
first installer proposal rejected the obsolete clothing-resource descriptor
assumption; the corrected installer follows and verifies the active 12-KiB
startup resource. No linker limit, reserved-byte check, or source guard was
relaxed. Native harness construction and execution stayed within the batch's
30-minute limit. Unchanged prior device-worker evidence is retained, not rerun.

## Shared reward controls and fanfares

The ABI-141 proposal is `build/v3-shared-reward-controls-01/build-lock.json`.
It installs the shared golden-tool celebration setup/main and fanfare callbacks
through the existing category installer. All 128 experimental choices, format-2
saves, resource addresses, resident allocations, and official messages remain.
Full persistent settlement and ordinary reward acquisition remain unfinished;
the four golden tools and their reward actions stay disabled. The main ABI-109
lock and both served patchers remain unchanged.

- ROM SHA-256:
  `3371dcfdfe1b3d7f88323604578faacb631622a4420302fcc839aa5ea98b3d87`.
- Report SHA-256:
  `f6312a2cfcb50b71f372c336731324941b616e95dab9288fef28ba8f04812eb2`.
- UPS SHA-256:
  `ad138022ed2a5a70be30628a41998d79a2c4ba710c59983edca84fee38be7c1d`.
- Reward code SHA-256:
  `0ad4ccb353c4781aff3671cc58fe71f2864b708c4806c60caa8d7d379c85a58b`.

The 1,036-byte code group occupies `804B3880..804B3C8C`, preserving the complete
icon prefix and old guard at `804B3FF0`. It connects the installed celebration
motions, source held-item rules, two source turn steps per native update, native
braking, animated/normal facial selection, standing/background checks, held-item
updates, and the installed message phase. The source fanfare selector supplies
axe/net/rod/shovel logical IDs 73/75/76/74. These resolve through native tables
to existing complete fanfares, with no new audio allocation.

The audio audit compares complete native sequences with donor prefixes and
complete native fonts after normalising waveform offsets. All 60 sample headers
resolve to identical full waveform data. Three donor sequences and four donor
fonts have sixteen additional trailing bytes; their receipts preserve those
bytes and do not call them zero padding or a completed conversion. The existing
native files are used unchanged. No physical audio is played.

One sanitizer and three cartridge/composition checks pass on their first run:

```sh
python3 -m unittest tests.test_v3_player_actions.RewardControlHostTests \
  tests.test_v3_player_actions.RewardControlTests -v
```

They cover all reward types and held kinds, source setup/frame call order,
animation/part masks, message-gated exit, null/invalid input rejection, immutable
actor guards, complete source/native/audio bindings, changed-source/API/table
rejection, only the reserved code changing, no resource/save/allocation growth,
unchanged action registration, original-ROM UPS reconstruction, all 128 choices,
exact empty-selection V2-12, and future resource-tail reuse. Syntax compilation
and `git diff --check` also pass.

Native attempt one, `build/smoke-v3-reward-controls-01/`, has 75 records with 57
passing assertions and one failed assertion. All four real setup/motion/fanfare
request/delete pairs, one actual main frame, and saved-data retention pass. The
fixture then incorrectly requires the whole segment table to remain unchanged.
Results SHA-256:
`126cb489285859038d390c70c830cb1fd5867f33b418c08ae4da51be86231eff`.

The unchanged native animation combiner at `80053B54` receives segment six for
both animation layers. Its restoration helper at `80053384` writes the saved
lower-layer base last; this leaves the lower animation bank selected. Both the
retail disassembly and `upstream/af/src/code/c_keyframe.c` establish that normal
effect. It is not new memory corruption. The fixture is corrected to check the
exact lower-bank value and every other segment, then restore the prior table.
No production code or cartridge changes for this correction.

The justified retry, `build/smoke-v3-reward-controls-02/`, narrows execution to
one representative instead of replaying all four completed fanfare pairs. It
passes **46 records and 34 assertions**, results SHA-256
`54d30488f219d7dc82b74f03d474f7a57d540ff25456c87ad24caa2a61720569`.
The complete cartridge-loaded module and actual relocated player code are
verified. A temporary unused native settlement-table slot preserves both real
actor/game arguments; no executable code is uploaded. Real animation setup,
complete motion banks, one frame, timer state, BGM request/delete, exact segment
behaviour, unchanged four-player/V3 saved data, restored actor/banks/BGM/module,
guards, restored checkpoint, resume, and clean exit pass. Audio remains disabled
and only isolated blank saves are used. The one setup retry is spent; fixture
work stays inside its 30-minute budget.

```sh
python3 tools/emulator_smoke.py \
  --rom build/v3-shared-reward-controls-01/animal-forest-v3-asset-loader.z64 \
  --output build/smoke-v3-reward-controls-02 \
  --scenario tests/v3-player-reward-controls-scenario.json \
  --xvfb /home/discordian/Games/OpenRSC/headless/vendor/usr/bin/Xvfb \
  --seconds 180 --expansion-pak --no-initial-screenshot
```

This establishes one actual native animation frame, not full rendered reward
playback, audible fanfare quality, balloon reward playback, ordinary acquisition,
persistent settlement, or hardware. Reuse the preceding complete message/motion/
face evidence. Browser code is unchanged; no fresh browser test is claimed.
Imported saves still require matching/equal-or-larger profiles and must not load
in V2. Next implement separate saved celebration/trophy flags and full settlement,
then source scene/NPC/tree events. Do not enable golden tools from this component
result or change either served patcher.

## Shared reward messages

The ABI-140 proposal is `build/v3-shared-reward-messages-02/build-lock.json`.
It installs the shared golden-tool message phase and all four complete official
donor messages through the existing category installer and text-region repacker.
All 128 experimental choices, format-2 saves, resident allocations, previous
messages/choices, and artwork remain. Golden tools are still pending/disabled.
The main ABI-109 lock and both served patchers remain unchanged.

- ROM SHA-256:
  `d392a1b6b8c39efa2ce33d5ac62c901ae6f36d4507c4378794f54c78699d7a49`.
- Report SHA-256:
  `ab6ca360e739f9231e48fd8ee2ea1cc126f7d0aa18759292a0f8695979137b0d`.
- UPS SHA-256:
  `78ca97cc68312668312c9741648f637cebc7980dff25d53e73e17ac4c5556c12`.

Complete messages `306D..3070` become `2EEB..2EEE`, retaining all encoded wording,
pages, colours, delays, and terminators. The single provenance catalogue credits
each official source. The 604-byte MIPS group at `804B2280` uses existing zero
space before the bobber artwork at `804B2800`, without enlarging the module or
import blob. The first build correctly rejected a proposed `804B2180` placement:
the inventory-bobber helper already occupies that address. The corrected layout
respects both code and artwork reservations; no existing build was overwritten.

One sanitizer and four cartridge/composition checks pass:

```sh
python3 -m unittest tests.test_v3_player_actions.RewardMessageHostTests \
  tests.test_v3_player_actions.RewardMessageTests -v
```

They cover all four types, bounded reset, invalid/null inputs, the source delay,
retry-until-accepted requests, unfinished/finished animation lock behaviour,
report-close completion, actor guards, complete official text retention, one
source catalogue, changed native/source rejection, module/core/resource bounds,
unchanged saves, future text retention, original-ROM UPS reconstruction, all
128 choices, and exact empty-selection V2-12. All five pass on their first run.

The first silent native run `build/smoke-v3-reward-messages-01/` passes **115
records and 98 assertions**, results SHA-256
`3a30e9ab8fe82884abf21a562bd38fea63e3bf392bb77f6f92bfde4abdf3ff2f`.
It validates the complete cartridge-loaded module and actual loaded player code,
then temporarily selects the new callbacks in an unused native table slot.
No executable code is uploaded. Four actual cartridge message loads, all begin
callbacks, native reset, all 21 delay updates, real report requests, accepted/
unlock/wait/complete phases, count rejection, and guards pass. The dispatcher
leaves its second argument equal to one: native reset uses the net type, and
native update uses finished animation; the host sanitizer covers other types
and unfinished animation. Report acceptance/closure is fixture state, not a
normal complete reward event.

The run restores the callback slot, full demo/window state, and emulator
checkpoint, retains all four private-player records and saved V3 state, resumes
with zero faults, and exits cleanly. It uses isolated blank saves and disabled
audio. No setup retry is needed; fixture work is within the 30-minute limit.

```sh
python3 tools/emulator_smoke.py \
  --rom build/v3-shared-reward-messages-02/animal-forest-v3-asset-loader.z64 \
  --output build/smoke-v3-reward-messages-01 \
  --scenario tests/v3-player-reward-scenario.json \
  --xvfb /home/discordian/Games/OpenRSC/headless/vendor/usr/bin/Xvfb \
  --seconds 180 --expansion-pak --no-initial-screenshot
```

Full reward setup/main/settlement, fanfares, persistent reward flags, and actual
scene/NPC/tree acquisition remain unfinished. GPU appearance, ordinary gameplay,
and original hardware are not established by these checks. Browser code is
unchanged; the unserved ABI-137 worker evidence is retained, not called a fresh
ABI-140 browser test. Imported saves require matching/equal-or-larger profiles
and must not load in V2. Continue from this explicit proposal without replaying
the completed message, motion, or facial checks.

## Shared reward motions and player faces

The ABI-139 proposal is `build/v3-shared-reward-motion-03/build-lock.json`.
It installs both complete donor golden-tool celebration motions and generic
per-frame eye/mouth sequences for all installed imported player motions. The
128 experimental choices, saved format, existing resource addresses, and main
ABI-109 lock remain unchanged. The four golden tools remain pending/disabled;
neither served V2 patcher changes.

- ROM SHA-256:
  `d31cde847e46f7dd69c457cd9cba10e60c7d001dfd7a488d9e3c515027472025`.
- Report SHA-256:
  `00594008f0d7ad40f645ecfe30785283013e93744de559899a4adbb966695103`.
- UPS SHA-256:
  `c14e34f9ca3fd961999e19810a03a912c80f19251c3ffa87a4b7a82088d1b2d7`.

The donor setup selects YATTA1 or YATTA3, not YATTA2. Complete resources are
3,136/3,072 bytes with 26 joints and 53 frames, fitting the unchanged 3,848-byte
native banks. The source selector/pointer tables supply all face arrays. Complete
identical arrays deduplicate to 213 bytes, preserving the fall/get-up and reward
timelines. The generic 200-byte reader and 1,272-byte table fit unused space in
the existing 72-KiB module. The native segment resolver accepts resident segment-
zero pointers, verified through the actual player face consumer.

The checked retired audio-sequence tail holds the first motion; the second
appends. The import blob grows 3,072 bytes rather than 6,208, retaining the live
audio sequence and protected English-choice region. Existing player/equipment
resource intervals prevent future reclamation from overwriting motion data.

One sanitizer check and four cartridge/composition checks pass:

```sh
python3 -m unittest \
  tests.test_v3_player_motion_runtime.FaceHostTests \
  tests.test_v3_player_motion_runtime.RewardMotionTests -v
```

They cover both complete converted motions, exact donor timelines, native bounds,
null/malformed inputs, changed-source rejection, retained original resources and
hooks, reclaimed-storage collisions, no save/profile change, exact UPS, all 128
choices, and exact empty-selection V2-12. The first storage fixture incorrectly
expected a live interval to reject the whole operation; the allocator safely
appended elsewhere. The corrected check verifies retention and non-overlap, and
passes. Only that affected check is rerun; the other three passed originally.
The three build outputs have the same ROM hash; later builds bind refined source
guards/comments without changing the installed machine code.

The first silent native run `build/smoke-v3-reward-motion-01/` passes **165
records and 123 assertions**, SHA-256
`70a157f22bae3f9ddf677c1b42b5558960a7779b81a61c1ccdaf44aa33f298c5`.
It uses the actual game-loaded player owner and cartridge readers, verifies both
complete motion transfers and untouched bank tails, and executes 30 native face
frames covering distinct timelines, expression pairs, and frame boundaries.
Only eye/mouth fields change; all segment bases, module contents, allocation
guards, and saved-profile memory remain intact. Calls restore the stack; the
fixture restores its checkpoint, resumes with zero faults, and exits cleanly.
No code is uploaded, user save used, or audible output produced. No retry is
needed; native fixture work is within the 30-minute batch limit.

```sh
python3 tools/emulator_smoke.py \
  --rom build/v3-shared-reward-motion-03/animal-forest-v3-asset-loader.z64 \
  --output build/smoke-v3-reward-motion-01 \
  --scenario tests/v3-player-motion-scenario.json \
  --xvfb /home/discordian/Games/OpenRSC/headless/vendor/usr/bin/Xvfb \
  --seconds 180 --expansion-pak --no-initial-screenshot
```

The actual invocation uses an identical ignored copy of this scenario inside
the proposal directory. Skeletal playback, ordinary reward acquisition,
rendered appearance, and hardware are not established by this component run.
Unchanged browser JavaScript and the ABI-137 worker evidence are retained, not
reported as a fresh ABI-139 browser run. Continue with shared celebration
setup/main/settlement, official message/fanfare support, and persistent reward
flags, followed by the required scene/NPC/tree events. Imported saves require
matching/equal-or-larger profiles and must not load in V2.

## Shared wrapped-gift names

The ABI-138 proposal is `build/v3-shared-present-names-03/build-lock.json`.
All four wrapped aliases use the official `present` name at both native output
widths. Source attribution is in the single catalogue. Existing choices, saves,
allocations, assets, transport, and reward readiness remain unchanged; the four
golden tools stay disabled. The main ABI-109 lock and both served patchers stay
unchanged.

- ROM SHA-256:
  `84e45e710056eaf7877781ef2ffafd20be39abd2591dac86b6666ac74cb313ba`.
- Report SHA-256:
  `d2e77adf6dd7ea3ea46d289e0cb2211c1eee0283dde262a400c376093624ad86`.
- UPS SHA-256:
  `d58222e79a5f9bd3c747f075371e533e1a07fd26be4fbfff117804ceb9ec9166`.

The initial build stopped correctly when the shared reader needed 772 bytes in
its 768-byte reservation. Moving the tiny identity normaliser into existing
unused equipment code space leaves a 712-byte shared reader and 184-byte legacy/
normaliser adapter. No allocation expands. The `-02` build generated the four
missing official credits; `-03` verifies them and produces the same ROM.

One sanitizer check and four cartridge/composition checks pass:

```sh
python3 -m unittest \
  tests.test_v3_display_aliases.HostTests.test_native_shared_readers_with_synthetic_categories \
  tests.test_v3_player_actions.PresentNameTests -v
```

These cover all selection masks, ten/sixteen-byte bounds, unaligned destinations,
null/short/wide rejection, ordinary fallback, source names/credits, complete
cartridge hooks and unchanged resources, save/profile retention, exact UPS,
idempotent shared readers, 128 choices, and exact all/translation-only output.
One cartridge fixture initially assumed an absent `clothing_profile` report key;
removing that fixture-only assumption makes the affected check pass.

The first silent native run `build/smoke-v3-present-names-01/` passes **101
records and 60 assertions**, SHA-256
`33f5652e6404d5c6d58a9e75e7e39fa0b290676d706e9e55e1ccbdce7be4d8a6`.
It calls both actual cartridge entries for all four selected/disabled aliases,
checks exact bounded output and zero gift prices, retains ordinary present/net
names, and checks code, complete live-save memory, extension state, stack guards,
restored selections, checkpoint restore, zero faults, and clean exit. No code is
uploaded, user save used, or audible output produced. No retry is needed.

The complete native field setters match the original cartridge: 324 bytes at
`8008A81C`, SHA-256
`33ba2059735f9dd36b8a937fe3b2e8633a0ecfcd92ffef19c03c75794e2c78d2`,
and 116 bytes at `8008AA24`, SHA-256
`9fe9499a066d010cbf4bb39fd29f15f7ab9217e20784bfd624a1d2e7f55cec85`.
They store complete item halfwords after coordinate checks, without indexing an
item table. The unchanged 136-byte save-identity region at `8008EF0C` has SHA-256
`8754bfd6d4f7e944996d8649b9f33255123d0b6b3f7aaaabbc5b853bafe00835`.
Inspection of `save_codec.c` confirms payload retention apart from signature/
checksum; no new saved field or item filter is needed for these aliases.

Retain the ABI-137 transport and real-browser-worker results for unchanged code;
do not describe that export as an ABI-138 browser run. Acquisition/reward demos,
ordinary wrapped exchange/save gameplay, rendering, and hardware remain open.
Imported saves still require matching or larger profiles and must not load in
V2. Continue with shared reward implementation rather than replaying components.

The following acquisition audit compares the four actual current seasonal
owners with the complete donor tables. Each native table has thirteen rows,
matching the first 104 donor bytes; the following twelve bytes are three `-1.0`
floats, not additional rows. All four donor tables have 21 rows with identical
168-byte contents, including the golden-shovel drop. The native actor table also
lacks the donor gift director, masked gift NPC, Farley, and mayor entries.
This changes the next action from looking for a direct existing reward hook to
adding the required shared event support. The source director setup is
`.text:113888`, 364 bytes, SHA-256
`c1607d6b35ce0d49980c282e889b23e09cb162fa4c157e30eed087ce702395fb`;
its retirement is `.text:113C34`, 208 bytes, SHA-256
`14fa1ac18871adfdcefc1c880370700ab5ecbbd25efe271810611baec2834ab6`.
Farley's reward callback is `.text:2225F0`, 84 bytes, SHA-256
`552e62284912d7431dfa6cf3e44fe05d1f984c56fbd85d6f75e5b312b61c1511`.
No runtime reward is installed by this audit. The next shared batch needs the
celebration dependencies, followed by real event/tree routes and persistent
reward state; existing collection ownership is not equivalent to trophy receipt.

## Shared wrapped-gift transport

The explicit ABI-137 proposal is
`build/v3-shared-wrapped-parents-03/build-lock.json`. Shared source-derived
records connect the four golden-tool wrapped identities across native direct/
free pocket insertion, hand construction, field exchange, and category lookup.
The 128 experimental choices, saved profile, official text, and exact V2-12
no-import output remain unchanged. Golden-tool rewards and options stay disabled.
The main ABI-109 lock and both served patchers remain unchanged.

- ROM SHA-256:
  `b5e35a39bbee583fad2e98ecac6b6b89bca2b8bbd4e72c777a1b5fd2c793f3c4`.
- Report SHA-256:
  `7bac03e7438cbbaa7b42a5c80fe3aa1b999fd2ef7c3a3fcecc187df5ee89b66d`.
- UPS SHA-256:
  `da29665024e32cb7bcde24e54f98d1784491053f58fb37f323dafc0b56bf0111`.

The 1,132-byte adapter and 32-byte table occupy a checked retired-sequence
extension, bringing the module to 72 KiB without moving old resources. The final
guard is `804B4FF0`; all earlier guards remain. The category reader uses 412 of
its reserved 512 bytes. Selected aliases map to existing present category 14,
never the native out-of-bounds miscellaneous index. Pockets contain actual
parents plus condition one; disabled aliases cannot insert invalid pocket items.
Full pockets retain native rejection, and wrapped insertion does not prematurely
credit collection. Normal and quest exchange conditions keep the parent identity.

The initial build correctly stopped at the import-blob growth guard: placing
the complete uncompressed hand owner there would cross protected English-choice
VROM `025F0000`. The shared installer now stores compressed/resized owner copies
in checked unused physical cartridge space, retaining their logical DMA IDs and
all old bytes. The complete 9,216-byte hand owner moves; the tag owner updates in
place. The import blob does not grow, and no overlap guard is relaxed. The final
allocator also accounts for any proposed new physical blob end before placing
external copies. The preceding `-02` ROM has the same output hash; `-03` records
the stricter shared allocator source and is the authoritative proposal.

One host sanitizer check and four current cartridge/composition checks pass:

```sh
python3 -m unittest \
  tests.test_v3_player_actions.WrappedHostTests \
  tests.test_v3_player_actions.WrappedParentTests -v
```

The host check covers mappings, selection masks, conditions, damaged headers,
strict identities, native fallback, and bounded category handling. Three initial
cartridge checks pass; the relocation check exposes a fixture omission, not a
ROM failure. Its corrected model includes the hand's 768-byte BSS and original
biased Bell-table base (`808742A8 + item*4`); the affected check then passes.
Together these bind complete donor functions/table, native regions, all four
hooks, two relocation bases, module retention, allocation/zero-space rejection,
actual DMA extraction, unchanged unrelated resources/save profile, exact UPS
reconstruction, future parent-table regeneration, all/empty composition, and
unavailable-option rejection. No native or cartridge guard is weakened.

The first silent native run at `build/smoke-v3-wrapped-parents-01/` passes
**308 records and 202 assertions**, SHA-256
`e122c865df8974ebb9275685d774dd01fa2489a188a7fb51a737b371c710d3b7`.
The existing shared collection scenario exercises actual current-cartridge
pocket APIs for four isolated resident records, all four aliases, ownership,
conditions, full pockets, disabled selections, and category lookup. It loads
both complete hand/tag owners through the native DMA/relocation loader, then
executes 14 actual hook windows with full-width live GPRs, HI/LO, FP state, and
private memory guards. Actual relocated hand-condition writes, untouched owner
code, restored profiles/player state, checkpoint restoration, zero faults, and
clean shutdown pass. The established lower-memory call bridge is the only
uploaded executable fixture. No user save or audible output is used. Harness
work stays within its 30-minute budget; no native retry is needed.

The current private export is `build/v3-wrapped-parents-browser-01/`. The real
browser worker reads the two supplied games and matches offline empty/all/
mixed/equipment outputs. Empty output is exact V2-12; all output is the ABI-137
ROM above. Cancellation, unknown-option and corrupt-plan rejection, no browser
errors, local GET-only requests, and temporary-server shutdown pass. Results at
`build/check-v3-wrapped-parents-browser-01/results.json` have SHA-256
`32427ac8070cebd203ee5add2b9cfa76be913b0c8a11670df279641162214f07`.
The export stays unserved. This does not close the separate full-interface test.

Remaining work: finish wrapped field/name/save consumers and source-backed tool
acquisition/reward demos before enabling any golden-tool choice. Full ordinary
exchange, reward gameplay, visual appearance, save/reload, and hardware are not
proven by these component checks. Format-2 imported saves require matching or
larger profiles and must not be loaded in V2. This batch makes implementation
and verification progress; the full V3 objective remains incomplete.

## Shared golden-tool parent category

The explicit ABI-136 proposal is
`build/v3-shared-tool-parents-01/build-lock.json`. The shared category refresh
installs all four golden-tool parents, names/prices, icons, ownership bindings,
and complete catalogue models together. The 128 experimental choices and saved
profile are unchanged; the four tools remain pending acquisition and reward
demos. Neither served V2 patcher nor the main ABI-109 lock changes.

- ROM SHA-256:
  `cd4b7467a650cd3933eb357af837d71f72062591ee00893d1999d15fafd5ab2f`.
- Report SHA-256:
  `26881ef568a6a9bf98051f6b44e4d98a0b40886cd7e455516a5f8bd28c96ef21`.
- UPS SHA-256:
  `4c765b554ba9fb00cddb54073d747f0e8bf97fec9073e51ba5c6767e8dfd1618`.

Source aliases identify parents `2239..223C` and their four complete prepared
catalogue models, adding 4,928 ROM bytes. Active selector records use native
kinds and `passive=False`; ordinary tools and worn axe states are not additional
imports. All official names share the existing provenance catalogue. Ordinary
room drops retain the parent IDs. The complete model count is 28, but the actual
umbrella catalogue still has 32 original plus 24 ready rows, with no unreachable
golden entries added to completion counts. The installer and composer share the
same readiness/dependency calculation and verify pending models and profile bits.

The equipment module grows from 64 to 68 KiB through the generalized checked
retired-sequence reservation. It verifies the actual live relocated sequence,
its native header, all affected resource bounds, and the zero destination.
Old addresses and both earlier guards remain. Four complete icons use 2,176 of
4,080 available bytes at `804B3000`; the new final guard is `804B3FF0`. Old icon
resources retain their exact addresses/data through recorded allocation order.
The compiled reader preserves public entry addresses and validates complete
aligned palette/texture bounds. The menu hook follows its relocated private
implementation. Pool accounting remains 280,640 of 280,768 bytes.

One sanitizer check and four focused cartridge/composition checks pass:

```sh
python3 -m unittest \
  tests.test_v3_held_catalogue.HostTests.test_shared_icon_extension_bounds_and_active_selection \
  tests.test_v3_held_catalogue.ToolParentTests -v
```

The initial invocation passes three checks and exposes two incorrect fixture
expectations: inverse-parent metadata is not all zero, and private helper calls
move within the fixed-address compiled reader. Those expectations are corrected;
the two affected checks pass in 2.270 seconds. The ROM does not change. Coverage
includes complete regeneration/source credits, icon data/bounds, old resource
retention, guarded allocation, complete models, inactive pending choices,
unchanged save profile, unrelated DMA resources, UPS reconstruction, all choices,
exact V2-12 empty selection, and invalid pending-dependency rejection.

The first silent native run at `build/smoke-v3-tool-parents-01/` passes **182
records and 117 assertions**, SHA-256
`6c507f5fe7234e55c6acd72fc8f5a5f0e07208401b7900b1da6f0a0d6fbcddc1`.
It loads the actual catalogue/menu owners and complete equipment readers from
the cartridge. All four tool names/prices, ownership/inverse aliases, active
selectors, complete catalogue transfers/framing, and ten icon cases pass.
Disabled/profile/wrapped handling, original categories, live register retention,
stack/resource guards, state restoration, checkpoint reload, and clean exit pass.
The fixture temporarily supplies pending profile/list data after checking that
the real list excludes those tools; it also uses the established entry-animation
stub and upper-memory call bridge. No ordinary acquisition, GPU appearance,
save/reload, or hardware claim follows. No user save or audible output is used.
Native harness work finishes within its 30-minute budget without a retry.

The unserved export `build/v3-tool-parents-browser-01/` has 128 choices. The real
browser worker reads both supplied games and matches offline empty/all/mixed/
equipment profiles. Empty output is exact V2-12; all output is the ABI-136 ROM
above. Cancellation, unknown choices, damaged plan rejection, no browser errors,
local GET-only traffic, and server shutdown pass. Results at
`build/check-v3-tool-parents-browser-01/results.json` have SHA-256
`a224cf47bb362e1a1f75e826281bb5391011d9b64a321c4c8398efde5b5c2777`.
The separate full-interface fixture is not rerun or relabelled as passing.

Continue shared source-backed acquisition, reward demos, and wrapped presents.
Do not enable golden choices merely because their resources/readers are ready.
The follow-on source/cartridge audit identifies the three unchanged pocket/hand/
exchange consumers and the donor's four wrapped aliases. Those aliases exceed
the original 30-entry miscellaneous table; the native category reader has no
bound. The donor uses existing present category 14 and stores actual parents
plus condition in pockets. Exact hashes, offsets, current relocated tag owner,
and source reward routes are recorded in the
[acquisition contract](../../specs/V3_HANDHELD_ITEMS.md#golden-tool-acquisition-and-wrapped-identities).
This narrows the next implementation to shared decode/encode/category handling,
with reward demos and saved flags still required. No runtime code changes follow
from this audit, and no additional native run is needed for these notes.
Format-2 saves retain their matching-or-larger profile requirement and must not
be loaded in V2. Broad gameplay and hardware remain open. This batch makes
implementation and verification progress; the full V3 objective is incomplete.

## Shared golden-tool inventory previews

The explicit proposal is ABI 135 at
`build/v3-shared-tool-previews-01/build-lock.json`. It retains all 128 experimental
choices, fixed identities, complete existing assets, format-2 saves, and exact
V2-12 empty-selection output. No golden-tool choice is enabled. The main ABI-109
lock and both served V2 patchers remain unchanged.

- ROM SHA-256:
  `116346e16a9e3928dc07d87e509b48d38b89f1192070b19c9d0b64e55ec50537`.
- Report SHA-256:
  `d5cb050c356169821503422cfebb86a7c94601c30c4025a8c29c432c2a4fe2d5`.
- UPS SHA-256:
  `6b95da4235c2e7a860370812b10a9807a0294f95ff18ffbde350a1ee63e2c31d`.

Shared source aliases and preview tables supply all four golden-tool records,
without selecting items first or maintaining a per-item installer. The axe and
shovel use the installed static models; net and rod use their complete rigs and
native timing/drawers. Existing preview entries and code addresses remain.

The rod's inventory accessory is a distinct native-format donor asset. Both
ordinary and golden lists match the original N64 command program after resource
pointer normalization. The ordinary donor palette, texture, and vertices exactly
match the N64 resources, establishing native RGBA5551/linear-CI4 storage rather
than the usual Dolphin data. The shared converter retains the golden resources
and full 27-triangle geometry. The 960-byte accessory occupies `804B2800`; the
56-byte pointer helper occupies `804B2180`. Only the two-instruction native
pointer load changes. The complete native rod function retains its skeleton,
transforms, segment setup, and matrix allocation. No module/bank/BSS/save/profile
allocation grows, and every old imported resource stays intact.

Four focused checks pass in 7.499 seconds:

```sh
PYTHONPATH=tools:tests python3 -m unittest test_v3_inventory_rigs.ToolPreviewTests -v
```

They cover complete source-derived rows, unchanged old categories, models/motions,
animation/joint/bank limits, full native-format resource preservation and rebasing,
rejected malformed commands/pointers/truncation, exact module/owner changes,
occupied reservation rejection, unrelated DMA resources, original-ROM UPS
reconstruction, unchanged saved profiles, all 128 selections, and exact empty
output. Python syntax and `git diff --check` pass.

The first silent native run, `build/smoke-v3-tool-previews-01/`, loads and draws
all four tools, then fails a fixture assertion about the common-resource segment.
The fixture put its pointer at overlay `10028`, missing the native segment base's
additional `D0`. Native instructions `8087E2DC/8087E308/8087E3BC` establish the
actual location `100F8`. This is a fixture setup error, not an accessory pointer
or renderer failure. The corrected retry uses that actual offset; the ROM is
unchanged.

The retry, `build/smoke-v3-tool-previews-02/`, passes **132 records and 116
assertions**. Results SHA-256:
`0faf70b7493538d27e1d92565094eded8fd803dad73d9ca0717e427378a78063`.
It loads/relocates the complete inventory owner from the cartridge, runs the
actual model/animation loaders and initializer, and executes the native preview
table lookup and draw dispatcher for each new tool. It checks complete transfers,
joint/morph pointers, native timing, every expected joint/accessory display list,
matrix allocation and stack balance, and the rod's common-resource segment.
The changed ordinary-rod pointer window also returns its original model while
retaining all live registers. Module/profile state and guards remain intact;
checkpoint restoration, zero CPU fault, final guards, and clean exit pass.
No code is uploaded for these cases, no user save is used, and audio stays silent.
The test-harness work takes under the 30-minute budget; the justified retry is
spent. Do not replay unchanged checks.

This is component execution, not GPU rendering, ordinary inventory interaction,
acquisition/reward demos, tool gameplay, persistence, or hardware confirmation.
Continue shared parent/name/icon/catalogue and acquisition integration before
enabling golden-tool choices. Imported saves still require matching-or-larger
profiles and must not be loaded in V2. This goal turn makes implementation and
verification progress; the overall V3 objective remains incomplete.

## Shared golden-shovel digging

The explicit proposal is ABI 134 at
`build/v3-shared-shovel-effects-02/build-lock.json`. It retains 128 experimental
choices, complete assets, fixed identities, format-2 saves, and exact V2-12
no-import output. No golden-tool choice is enabled. The main ABI-109 lock and
both served V2 patchers remain unchanged.

- ROM SHA-256:
  `07a3ad9e636b64eb1ef94fb097223c273a73e517af53dc2a6cfef252384e5459`.
- Report SHA-256:
  `786fcaf06c441bd06bf61ff612b75051fac31c55668af37bb747be0222f52354`.
- UPS SHA-256:
  `ca2b058be20a732e77f8581e0865a7c031e9da083153a7d140008343fcca774f`.

The real core call reads golden kind 90 from the actual caller's player, passes
the original item/position arguments, and executes native digging before the
new effect. DIG at a new eligible spot can generate 100 Bells on the source's
10% roll. Ordinary digs also update the previous position. Other status/item
handling, downstream collision/action logic, and RNG use remain native.

The 384-byte helper and twelve-byte state use a checked 4-KiB module extension,
bringing the equipment allocation to 64 KiB. Retired sequence ownership and the
actual live moved sequence are verified before reclaiming storage. All earlier
module bytes, constants, state, code addresses, assets, and guards are retained.
Startup covers the new allocation. There is no ROM growth or saved/profile/actor
format change. The first build attempt stops before compilation because the
new frame assertion names `800B4064` instead of the actual store at `800B4060`.
The corrected exact-instruction assertion builds successfully in fresh output.

The sanitizer-backed host test passes. Four current-cartridge checks pass in
6.148 seconds, covering complete source/native consumers, the sole four-byte
core hook, retained old code/assets/sequence, CRC/guards/startup length, rejection
of occupied/unowned/changed sequence storage, every unrelated resource,
original-ROM UPS reconstruction/checksum, the all-selected 128-choice build,
and exact empty selection. Commands:

```sh
python3 -m unittest tests.test_v3_player_actions.SelectionHostTests.test_shovel_effects -v
python3 -m unittest tests.test_v3_player_actions.ShovelEffectsTests -v
```

The first silent native run at `build/smoke-v3-shovel-effects-01/` passes
**186 records and 174 assertions**, with 29 shovel cases. Results SHA-256:
`868b47a2dd5fde5d2ae93d3855874f066841016ad831d89d49c8859492e3b0bb`.
It verifies the complete cartridge-loaded module, actual hook and item/position
arguments, normal/imported-normal/golden kinds, every dig status, strict
positive/negative position boundaries, Y-only movement, winning/losing native
RNG advances, item output guards, previous-position updates, unchanged player
and saved state, stack/callee-saved registers, restored globals/profile, both
equipment guards, checkpoint restoration, zero fault, and clean exit. No code
is uploaded, no user save is used, and audio stays silent.

Most cases inject a status/item result at the unchanged native function's entry
to isolate the new compiled suffix. The out-of-world negative-X case instead
runs the entire native cancellation path. This is not ordinary terrain digging,
buried-item gameplay, reward animation, acquisition, persistence, GPU appearance,
or original hardware. Reuse unchanged prior tool evidence; do not replay it.
Imported saves need matching-or-larger profiles and must not be used in V2.

Next connect shared parent, inventory, acquisition/demo, and persistence support
before enabling tools; the durability audit below needs no new runtime code.
Balloon release on get-up remains a separate shared dependency.

## Golden-axe durability audit

The complete source damage function at REL text `169188`, 416 bytes, has
SHA-256 `18edb9be71e27e97a0002553a9f637579fb372dca68710cbbcf63203642aa53c`.
Its request caller at `169328`, 348 bytes, hashes to
`33adc9f21083b37a6a5fe38ede518ecd50c26f38c42d86b15a177cf494444973`.
The source frame-15 item change function at `18005C`, 228 bytes, hashes to
`745865c51347f47cb43e837a6b3ffa69b4365758dd94f357be6f4c942a003875`.
The golden item `223A` is not in the accepted ordinary/worn axe set and returns
unchanged. The frame-15 update sees the same item and does not alter equipment,
reset wear, or play break sounds. Ordinary wear forms are not a dependency of
that golden behaviour.

The actual N64 request `808B7CDC..808B7DD8`, 252 bytes, hashes to
`04da44d62527230350e1f29ec8db2ee7799cb3c667a16e2b5dbf622b51c5d4fc`.
Its complete direct-call sequence is input `808B2DE4`, player `800B1C84`,
collision `808B6458`, position conversion `80088344`, tree-swing request
`808CA060`, reflection request `808CAD58`, and air-swing request `808CA9E4`.
There is no intervening equipment lookup, damage update, or worn-item argument.
The complete 4,812-byte swing/air/reflection region `808CA060..808CB32C` hashes
to `53f7ace416bce0118f16197003f29af7f44768d6ba0731799a6fe9a66ae8951c`.
Both regions compare exactly with the original cartridge in ABI 134. Existing
tool-input evidence covers actual kind 44 being accepted as the axe family.

No new axe-wear patch is needed for the golden import, and no ordinary N64 axe
durability change is justified by this feature. This audit does not establish
the golden parent's complete inventory/acquisition path or ordinary chopping/
reflection gameplay. Continue those consumers rather than adding a redundant
wear implementation or repeating unchanged tool-input tests.

## Shared golden-rod response

The explicit proposal is ABI 133 at
`build/v3-shared-rod-effects-01/build-lock.json`. It retains 128 experimental
choices, complete assets, fixed identities, the 60-KiB module, format-2 saves,
and exact V2-12 no-import output. No golden-tool choice is enabled. The main
ABI-109 lock and both served V2 patchers remain unchanged.

- ROM SHA-256:
  `769f282b11d571cada3a0c33d9c5d9218b96c7bc1a1b8452cee3d5ffcff43edd`.
- Report SHA-256:
  `11dafdcb317dd1b858d485a9af9cc7274c605a341267cd04645673bb7c4ff71d`.
- UPS SHA-256:
  `775fc03bbbee6eada8f20185ebe1668e9a01afa4fa8782c64bcdda996ca88a9c`.

Both native fish owners use the same source-verified normal/golden response
classes. A shared angle wrapper preserves their live signed target angle and
conversion factor, and lets the native comparisons decide the result. A shared
bite wrapper preserves normal durations and supplies golden durations in N64
timing units; it retains the original speed reset, work fields, and fish records.
The actual selected-equipment reader decides kind 88. Unselected imports do not
receive golden values. Detection and approach distances remain unchanged, as
both donor rows agree. Six complete source consumers and both complete original
owners/relocations are checked before installation.

The first build passes. The assembly/data suffix adds 248 bytes at `804A5EE0`,
for a 1,416-byte complete tool image ending at `804A5FD8`. All previous code,
constants, public entries, resources, and native player bytes remain. Four
instruction windows change across the two fish owners, removing six obsolete
relocations. Resident, actor, save, and profile allocations do not grow.
The compressed special-fish owner and relocation use the existing shared-tail
allocator, adding 8,816 ROM bytes and moving the catalogue/shop tail intact.

Four focused cartridge checks pass. The three structural/source checks pass in
the initial invocation. The fourth initially assumes that the DMA-directory
resource is unchanged; a subsequent assertion also assumes the blob's virtual
end cannot grow. Inspection identifies the existing builder's reported move of
the 8,208-byte owner and 608-byte relocation. The corrected test verifies that
exact growth, unchanged virtual identities and all other resource sizes, physical
directory coordinates, complete unrelated resources, original-ROM UPS/CRC, and
empty/all composition. Its final focused run passes in 5.641 seconds:

```sh
python3 -m unittest \
  tests.test_v3_player_actions.RodEffectsTests.test_ups_composition_and_unrelated_cartridge_resources
```

The complete class is `tests.test_v3_player_actions.RodEffectsTests`. It also
checks both relocated owner bases, all 32 fish records against the donor,
complete normal/golden angle data, all five bite mappings, unchanged earlier
code/addresses, and retained resources/save/profile fields. The test corrections
do not change cartridge code or invalidate the native evidence.

The first silent native run at `build/smoke-v3-rod-effects-01/` passes **190
records and 142 assertions**, including 82 angle windows and 32 complete bite
initializers across both loaded owners. Results SHA-256:
`365c7e2b1b4fcf4bb1c7176c43d97318abc8319687a92d3f0097698b0ee20208`.
It checks normal, imported-normal, and imported-golden kinds; strict positive/
negative boundaries; the angle interval visible only to golden rods; all five
bite classes; and unselected rejection. Complete actor-state comparisons retain
unrelated fields. All calls restore their stacks, the angle windows retain live
state, and current cartridge code is loaded through native DMA/relocation without
code uploads. Guards, saved state, restored globals/profile, checkpoint reload,
zero fault, and clean exit pass. No real user save is used; audio is silent.

This is component execution with temporary equipment data, not ordinary fishing,
tool acquisition/persistence, GPU appearance, or original hardware. Reuse the
unchanged input/motion/net/recovery evidence. Keep tool choices disabled until
their remaining parent/inventory/acquisition consumers are complete. Imported
saves require matching-or-larger profiles and must not be loaded by V2.

Next implement golden-shovel effects through the actual dig-status consumer,
then axe wear and complete parent/acquisition support. Balloon release on get-up
remains an explicit shared dependency. Do not replay completed rod checks.
The source dig-status implementation at REL text `39240` uses a previous-position
vector, updated on ordinary digs too, to gate a 10% chance of 100 Bells for the
golden shovel. Its full caller/status/item path remains required. Only 40 bytes
remain in the current tool-code slot; further effects need checked additional
space, not a reduced mechanic squeezed into that remainder.

## Shared golden-net capture

The explicit proposal is ABI 132 at
`build/v3-shared-net-capture-01/build-lock.json`. It retains all 128 experimental
choices, fixed identities, complete assets, the 60-KiB module, format-2 saves,
and exact V2-12 no-import output. No golden-tool choice is enabled. The main
ABI-109 lock and both served patchers remain unchanged.

- ROM SHA-256:
  `f2e7de5d6898bc39f12f95f632d07d3833ae44a000aa0d0ce93cf0321cbacb2f`.
- Report SHA-256:
  `bd4bca2ff83a4cc96d86ca89ac648aa693885415f44265069c6016c5ba2ea199`.
- UPS SHA-256:
  `9c7b9faab6835e1b9e5eb2bd1e39510c99a8d34560f359f05852409299e57a6c`.

The shared net helper uses actual selected equipment to supply the donor's
radius/span 21/60 for golden kind 46, retaining 15/50 otherwise. The complete
native force routine runs first; invalid candidate counts return without reading
equipment or touching parameter words. The native loop/collision arithmetic
remains, including first-match ordering, signed type output, and requested-radius
endpoint tolerance. Two unused outgoing words carry the dimensions without
shared mutable state. The sole local-capture caller and complete frame code are
checked. Five exact instruction windows change; three obsolete relocations are
removed. No unrelated owner code or resource changes.

The first build passes. The helper adds 184 bytes at `804A5E28`; complete tool
code is 1,168 bytes. All prior bytes, constants, public addresses, complete models,
bank sizes, profile fields, and saved formats remain. No translation text changes.

Four focused checks pass in 5.878 seconds:

```sh
python3 -m unittest \
  tests.test_v3_player_actions.SelectionHostTests.test_source_net_parameters \
  tests.test_v3_player_actions.NetCaptureTests
```

They cover sanitizer execution across native/extended/invalid kinds and counts,
forced-catch priority, bounded parameter stores, immutable actor state, exact
native instruction/relocation retention at two loaded bases, unchanged assets/
profiles/save code, original-ROM UPS reconstruction/CRC, and empty/all composition.

The first silent native run at `build/smoke-v3-tool-effects-01/` passes **244
records and 179 assertions**, including 53 analytical collision cases. Results
SHA-256: `51ac3c73fc5d0f567e8eadab8cec41bf16b548d660dfbdaeddd4b7b984c5ce53`.
It enters the actual relocated cartridge candidate loop for normal net, imported
normal net, and imported golden net. Radial boundaries, candidate radii, both
endpoint limits, golden-only radius/span, diagonal spans, overlapping candidates,
the eighth candidate, invalid counts, and forced catches all pass. The extra
radial bonus does not incorrectly enlarge endpoint tolerance. An unselected
golden selector cannot enlarge capture. Actor state, saved state, output guards,
the complete equipment module, restored globals/profile, fault/memory guards,
checkpoint restoration, and clean exit pass. No code is uploaded or user save
used; audio is silent. No setup retry is needed.

The fixture uses temporary selectors and synthetic collision candidates. It
does not prove ordinary catching, golden-tool acquisition/persistence, GPU
appearance, or original hardware. Existing complete input/motion/recovery
evidence remains valid and is not replayed. Keep tool choices disabled pending
their actual remaining consumers. Imported saves require matching-or-larger
profiles and must not be loaded by V2; profile removal is not migration.

Next implement both fish behaviours' golden-rod response through shared source
tables, then shovel effects, axe wear, and inventory/parent/acquisition support.
Source fishing search distances are identical for normal/golden rods; the real
differences are wider detection angles and longer bite windows. Resolve native
consumers/time-step units before installing them. Balloon release on get-up
remains a separate actual behaviour dependency.

The following source audit resolves both unnamed native fish owners for the
next shared stage. Original VROM `00828C50`, linked at `809317D0`, has SHA-256
`f07d956992ec2058942a0429c762294466db9d938333594d847dabb1a851c79c`;
VROM `009591D0`, linked at `80A98F60`, has SHA-256
`c5ba6a401a620eb537db976bee409bde3bc3c4568a51105379e575b9a607ae22`.
The existing Docker disassembler creates ignored reference outputs at
`build/disassembly/fish-ordinary/` and `build/disassembly/fish-special/`.
All 32 native size/search/bite records independently match the checked donor
tables after normal bite-class resolution. Native frames are not the donor's
doubled initializer counts. Exact consumers and values are in the
[rod specification](../../specs/V3_HANDHELD_ITEMS.md#shared-golden-rod-response).
This audit installs no rod behaviour and requires no replay of passing net tests.

## Shared net transitions and tool recovery

The explicit proposal is ABI 131 at
`build/v3-shared-tool-transitions-01/build-lock.json`. It retains all 128
experimental choices, complete assets, fixed identities, the 60-KiB module,
format-2 saves/profile, and exact V2-12 no-import output. The main ABI-109 lock
and both served V2 patchers remain unchanged.

- ROM SHA-256:
  `5333def11ffaefda03cf7d691b3ece236e14c49cf90a5f8d1b2ae4f3de12374d`.
- Report SHA-256:
  `4df8c1bd42dec18c8ad489cfe59e5f094a859be6ab222a87de471ef3e0f325d4`.
- UPS SHA-256:
  `11a39fd71688a9b701e95d0b817fab1394d330187aed03a440067e53757b0066`.

Four remaining net consumers compared the real kind directly with native kind
one. Their single visible-kind call now uses the existing family reader, so
original and imported nets can reach slip/swing/pull requests and slip exits.
Priority, controller semantics, requested actions, and non-net fallbacks remain
native. Four obsolete local-call relocations are removed.

The shared recovery implementation preserves actual kinds and complete models.
Original net recovery uses native animations six/five; imported nets use actual
source resources 27/26. Both retain stopped playback and native callbacks five/
six. Non-nets retain default motions and repeat mode; rods retain the earlier
bobber-lifetime correction. Two eight-byte prologue hooks install this category
without changing owner dimensions or any other relocation.

The first build passes. Recovery adds 296 bytes after the exact existing tool
code and constants; the combined image is 984 bytes. All old public addresses,
assets, selectors, profile bits, native draw callbacks, and saved formats remain.
No translation text or golden-tool choice is added.

Four focused checks pass in 6.132 seconds:

```sh
python3 -m unittest \
  tests.test_v3_player_actions.SelectionHostTests.test_shared_tool_motion_mapping \
  tests.test_v3_player_actions.ToolTransitionsTests
```

They cover sanitizer execution of recovery across original/extended kinds,
complete previous animation mapping, immutable unrelated state, all six exact
consumers, four relocation removals, two loaded-owner bases, old code/constant
retention, complete resource/save/profile retention, original-ROM UPS/CRC checks,
and exact empty/all composition.

The first silent native run at `build/smoke-v3-tool-transitions-01/` passes **255
records and 218 assertions**. Results SHA-256:
`88546e31c8b915715f82df16998bcd796994d9c8a807bf2b1e425d36b50ef9b6`.
The existing shared fixtures execute only the changed transition/recovery paths:
original net, original non-net, both extended net kinds, and imported rod
recovery. Actual native requests, priorities, rejected equal-priority requests,
held-A/released-A/completed-slip branches, hidden/unselected rejection, actual
recovery model/motion loading, stopped/repeating modes, real-kind retention, and
bobber lifetime pass. All calls restore the stack; memory guards, retained live
save state, restored temporary globals/profile, checkpoint reload, and clean exit
pass. No code is uploaded and no real user save is used; audio remains silent.
The fixture uses synthetic equipment selectors, not enabled golden-tool options.

The source audit also identifies balloon release in its get-up routine. It needs
the separate flying actor/shape and equipped-item removal, which are not native
net behaviours and are not installed here. The receipt makes that omission
explicit. Complete ordinary gameplay, GPU appearance, golden effects, acquisition,
and hardware remain unverified; do not convert these component results into
playable-tool certification. Retain the passing evidence without replaying it.

Next implement golden-net capture, then both fish actors' golden-rod response,
shovel effects, axe wear, and complete inventory/parent/acquisition routes through
shared adapters. Native capture functions are `808CC54C..808CC7B4` and
`808CC7E0..808CC988`; donor functions are at REL text `182CA8`/`182F6C`.
The source uses radius/span 21/60 versus ordinary 15/50. Preserve native forced
capture, candidate ordering, output identities, and normal-tool geometry.
Imported saves require matching-or-larger profiles and must not be used in V2.

## Shared tool animation setup

The explicit proposal is ABI 130 at
`build/v3-shared-tool-motion-02/build-lock.json`. It retains all 128 experimental
choices, complete assets, fixed identities, the 60-KiB equipment allocation,
format-2 saves/profile, and exact V2-12 no-import output. The main ABI-109 lock
and both served V2 patchers remain unchanged.

- ROM SHA-256:
  `de1bba6c5880871348b3685e300e5a0cdd813cbf035ed0073807d736c6899263`.
- Report SHA-256:
  `20c36d8d1d5bbb5164566ff2a6c1383f4ff849a4ce7ca69d91159f76a7fd5d78`.
- UPS SHA-256:
  `1898031f7a9e0bbd932993481ab48ddd107c9136e43ec26534dddeccf45d7ad4`.

The native action setup formerly required exact ordinary-tool kinds and native
animation indices. The shared adapter accepts the actual imported family, maps
all seven net and six rod motions to the installed complete donor resources,
and stores the actual imported kind. Rod-aware movement retains its supplied
speed. The native model loader's final rod comparison no longer destroys the
bobber merely because an imported rod changes animation. Other kinds retain
the original destruction path. Original-tool indices and timing remain intact.

The native net/rod drawers already match the donor skeleton contracts: six
net joints/three display lists, five rod joints/four display lists, net joint-three
angle callback, and rod joint-four tip callback. Their complete code and callback
tables remain untouched. No new renderer or reduced asset substitutes for them.
The adapter occupies 688 bytes at `804A5A50`; two entry hooks and one lifetime
call change. Relocation data, owner dimensions, earlier action code/constants,
profiles, save code, and all installed resources remain unchanged.

Four focused checks pass in 5.915 seconds:

```sh
python3 -m unittest \
  tests.test_v3_player_actions.SelectionHostTests.test_shared_tool_motion_mapping \
  tests.test_v3_player_actions.ToolMotionTests
```

They cover sanitizer execution, all thirteen mapped motions, ordinary/extended
tools, timing and retained actual IDs, rejected mismatched/hidden kinds and
extreme inputs, exact installed hooks at two relocation bases, retained complete
assets/code, original-ROM UPS reconstruction, CRCs, and exact empty/all optional
composition. The first build stops on a wrong report-key lookup before code
installation; the corrected build uses the existing bank-allocation receipt.
Two new composition-test API mistakes are corrected without changing the ROM.

The first silent native run at `build/smoke-v3-tool-motion-01/` passes **128
records and 102 assertions**, including 98 fixture assertions plus startup/final
guards. Its results SHA-256 is
`eec55763f0247777bf65c59175e30dc3bcc036244b2e4d9bf8134ff35a5cdd73`.
The existing representative rig fixture runs only the changed tool paths, not
old pinwheel/balloon scenarios. Actual cartridge code loads native and imported
net/rod models and motions, keeps actual kinds, selects the proper callbacks,
retains bobber lifetime, and preserves rod walking speed. Both imported rigs
emit every expected source joint display list. Memory/stack/matrix guards, saved
state retention, restored temporary selectors/profile, checkpoint reload, and
clean emulator exit pass. No code or real user save is supplied to the fixture;
only isolated selector/actor data is synthetic. Audio remains silent.

This is component evidence, not GPU appearance, ordinary net/fishing gameplay,
golden effects, acquisition, persistence, or hardware verification. Tool choices
remain disabled. No English wording changes, so provenance is unchanged.

Next audit/adapt the remaining action-request and tumble/get-up kind checks
through shared family machinery. Source locations are
`m_player_main_{swing_net,pull_net,slip_net,tumble,tumble_getup}.c_inc`.
Then connect golden-net capture radius/span, both fish-actor golden-rod response
paths, shovel effects, axe wear, and complete inventory/parent/acquisition routes.
Do not replay completed input or motion fixtures for unchanged code. Preserve
matching-or-larger V3 save profiles; imported saves must not be loaded in V2.

## Shared tool input predicates

The explicit proposal is ABI 129 at
`build/v3-shared-tool-controls-02/build-lock.json`. It retains 128 choices, all
installed artwork, fixed identities, the 60-KiB equipment allocation, format-2
saves/profile, and the corrected V2-12 no-import baseline. The main ABI-109 lock
and both served V2 patchers remain unchanged.

- ROM SHA-256:
  `ab3197986d49b6f5f7cdcb58ab0746b05467e6eb602d814a0ba9d8a140650a16`.
- Report SHA-256:
  `a8b753115a50f18e71c73220cff69591543fe34bc887c8041954b9b816f0acc3`.
- UPS SHA-256:
  `2bb79e4978753672f7f174ae96411fe124bb453dd59f80009cb6a31a5676563c`.

The ordinary N64 axe/net/rod/shovel input functions compare only original kind
values. The source GameCube functions use tool families including worn axes and
golden variants. One shared 132-byte adapter at `804A59C8` calls the actual
native visible-equipment reader, then classifies its result only for these input
predicates. Pickup and tree shaking receive valid non-tool classification for
imported passive equipment. The separate umbrella-spin input is unchanged.
Actual equipment IDs, kinds, renderer/effect decisions, saved identities, and
selected-only lookup remain intact.

The existing `--refresh-runtime --player-actions` path installs the change. Six
complete source/native consumers and the complete current owner are checked.
Exactly six JAL instructions change, and their six obsolete local relocations
are removed. The owner/relocation allocations stay fixed. All old action code,
constants, public entries, callbacks, tables, and resource bindings retain their
values. The complete action image occupies 2,636 bytes in its 4-KiB reservation.

The first build rejects movement of the existing constant pool caused by adding
another ordinary text section. The adapter's dedicated appended section keeps
that pool and all prior instructions intact; the corrected build passes the
exact-retention guard. The unsigned range calculation also avoids signed overflow
for rejected extreme inputs. Neither issue produced a distributed cartridge.

Four focused checks pass in 6.174 seconds: sanitizer execution across all signed
kind values and action arguments, extreme-value rejection, complete donor/native
consumers, all 79 source category bindings, actual hooks and relocations at two
owner bases, retained old code/resources/identities, unchanged profiles/saves,
unrelated DMA resources, original-ROM UPS reconstruction, and exact empty/all
composition. Golden-tool IDs are explicitly absent from the choice catalogue.
No translation wording is added, so the single text provenance catalogue stays
unchanged.

The first silent native attempt verifies the complete module and loaded player
owner, then stops because the generic debugger's direct-call proof is limited
to four-MiB code addresses. The fixture is corrected to enter through the actual
relocated N64 controller functions, whose installed calls reach the Expansion
Pak adapter. It neither relaxes the debugger's restriction nor uploads code.

The single justified retry at `build/smoke-v3-tool-controls-02/` passes 128
records and 106 assertions (102 fixture assertions plus startup/final guards).
It executes all six actual input functions with original axe/net/rod/shovel
kinds and representative golden-tool, balloon, and fan kinds. Net held-A versus
other tools' triggered-A, released input, pickup/tree shaking, hidden-item and
scene rejection, disabled-profile rejection, and unmodified real kinds pass.
All native calls restore the stack. Selected profile, equipment source, input
data, selector row, and scene are restored; save state and module/heap guards
are intact. The checkpoint is restored and emulation exits cleanly. Results
SHA-256:
`3b8348896fdfce276db1010005fede6265e52b4a0dd8c073c03f8d2f92f9d641`.

This run uses title-demo controller input and temporary isolated selector data
for the extended kinds. It is not ordinary tool gameplay, golden effects,
acquisition, a save-cycle test, or hardware verification. No user save is used
and no FlashRAM test write is requested. The setup retry allowance is spent;
retain this passing result instead of replaying it.

Next connect source-correct net/rod held and inventory consumers through the
existing shared adapters, then special effects and parent/acquisition consumers.
The donor's net capture code distinguishes radius 21/span 60 from ordinary
15/50. Ordinary and special fish actors have golden-rod detection/approach/bite
consumers; the shovel forwards a golden flag into digging. Axe wear and golden
acquisition/demo state also need source/native comparison. All these are required
before enabling tool choices; the control adapter does not declare the imports
complete. Keep matching-or-larger V3 save profiles, never use imported saves in
V2, and preserve the current patchers until user testing and approval.

## Shared room gameplay repairs

The current explicit proposal is ABI 128 at
`build/v3-room-parent-gameplay-fix-04/build-lock.json`. It keeps all 128 choices,
source artwork, fixed identities, 60-KiB equipment allocation, format-2 saves,
and the corrected V2-12 no-import baseline. Neither served patcher nor the main
ABI-109 lock changes.

- ROM SHA-256:
  `71173f07d0e7a3a88f68217eb86d69ee6ffc924df28e437feb43c831274fe5ba`.
- Report SHA-256:
  `dcbbbf6b6eeb99eebddeb1be2a2e833d3a8290c799e1fec4b12cbf081204d932`.
- UPS SHA-256:
  `d76f2d640be2a3f68c059a730136792b8bae56f6fb7b8fe7cc2b9fcce4198626`.

Ordinary room placement exposed an invisible model. The real actor, complete
model bank, and animation were present, but its matrices stayed empty: the
drawer rejected a valid graphics tail at `80168008`. Native graphics allocation
uses eight-byte alignment. The shared drawer now accepts both valid parities,
while rejecting four-byte alignment and insufficient command/matrix space.

Source-derived room metadata also needs footprint eligibility. All eight real
room forms now retain source size zero (one cell) and eligibility byte one.
The selected parent's profile still gates access; names, prices, ownership, and
choices remain on the parent. Catalogue-only forms retain their zero metadata.
Actual native footprint-reader tests cover all four orientations and disabled
metadata/profiles. This confirmed metadata defect is distinct from the first
unsuccessful pickup attempt, which did not establish a game pickup defect.

The rebuild uncovered a separate shared-owner integration error. The icon update
copied its predecessor's menu over the rebuilt catalogue owner, restoring a
descriptor 16 bytes shorter than the actual catalogue. The shared installer now
merges disjoint edits against the same predecessor, rejects conflicting edits,
checks complete catalogue bounds, and hashes the actual combined menu in the
icon receipt. Migration accepts only the exact diagnosed ABI-127 owner and
catalogue hashes. Unknown mismatches still reject. Same-category refresh is
supported without adding choices or duplicating resources.

Nine focused host checks and three current-cartridge checks pass. The latter
also verify same-category refresh leaves the installed module unchanged, all
eight source footprints, complete model/profile retention, actual owner bounds,
icon hook/receipt, unrelated DMA resources, UPS reconstruction, and exact
empty/all/two-balloon composition. An obsolete same-category rejection assertion
is replaced with retention checks. The latest three-check invocation passes in
10.601 seconds. `-03` and `-04` produce the same ROM and UPS; `-04` corrects the
icon-owner receipt and common refresh branch. Gameplay uses that identical ROM.

The existing combined native check at
`build/smoke-v3-room-parent-gameplay-fix-01/` passes on its first attempt:
216 records and 151 assertions, complete catalogue loading/relocation, all 24
parent conversions and source order, representative animated constructors and
icons, register/memory guards, saved-state retention, checkpoint restoration,
and clean exit. Results SHA-256:
`a0989ed0382e75d67da8823e462e59d38b3df2a78e7be4485fab340a1656fd7d`.

### Ordinary balloon placement, pickup, and persistence

The isolated two-balloon ROM in `build/v3-room-parent-gameplay-profile-02/` has
SHA-256 `7a25088a41e6a4653cf0cb89884bd9c81cee0828e5c20fa70a9e64a4195b6746`.
It selects only parents `2244` and `224B`, avoiding unrelated imported-villager
scene checks. The copied fixture seeds red balloon `2244` and its ownership;
this is not ordinary acquisition. The original town remains unchanged at
SHA-256 `d489736e39abc7eff1c5b5085bf52e679186f2882a0247339e11603799b80b60`.

The unchanged outdoor equip path in `build/v3-room-parent-equip-01/` completes
normally on ABI 127: correct name/icon, parent `2244`, native kind 91, pocket
removal, actual held red balloon, and guards. Its put-away path also succeeds.
The repaired drawer does not alter those resources or actions; do not replay
that result merely to attach a later build label.

`build/v3-room-parent-place-02/` cold-boots the corrected profile, enters the
house, and places native room form `3C00` at `8012A4A6`. The captured room now
visibly contains the red balloon and its string. Its immediate pickup assertion
fails with the player off-centre and about 53 units from the actor. The checkpoint
before pickup is retained. The single navigation retry at
`build/v3-room-parent-pickup-01/` resumes that same ROM/checkpoint, walks normally
to the balloon, and successfully picks it up. Pocket zero returns to `2244`, the
room field clears, other pockets remain intact, and fault/memory checks pass.
It exits cleanly with 17 records; results SHA-256:
`326b29c996be33daf72b9d48998e7aa91742cf3d842a8a555dc7c63dd3169f32`.
This resolves the pickup navigation failure without another game-code change.

`build/v3-room-parent-save-01/` branches from the retained placed checkpoint and
uses the normal gyroid Save & Quit flow, returning to the title. Its 21 records
pass, including the room identity and fault/module guards. Both actual FlashRAM
banks match independent format-2 re-encoding with the selected profile, empty
first pocket, and red-balloon ownership retained. The game save is
`test.flash`, SHA-256
`71a1fbbd99eae51e4d90ab0447121b4f0ebc0c8b726507b3a8dbc8dcae282021`.
Results SHA-256:
`2e437f35b5002074d8c20c2d8c715ccc64592ba530d5ce517da2511b1eddf555`.

The fresh process at `build/v3-room-parent-reload-01/` uses only this actual game
save, not an emulator checkpoint. It loads the expected pockets, room identity
`3C00`, complete model bank, and room guards. The captured room visibly contains
the saved balloon. Its additional post-reload pickup assertion fails after
navigation ends with a rightward input followed by a one-frame north input;
the item remains placed. Facing/navigation is a possible cause, not an
established diagnosis. This run has 17 records and five passing explicit reads;
results SHA-256:
`ce06bf87e728f24e4620f3e19b04e8897d1cff96cd1dd26e3476b645f890ccc3`.
No final checkpoint, post-pickup guards, or clean-exit result is recorded. Do not
report the full scenario as passed, infer a save defect from it, or replay the
successful cold-boot prefix solely for another input attempt. The bounded
navigation allowance is spent. Retain post-reload pickup as unresolved alongside
the passing separate pickup and demonstrated saved-object reload.

Ordinary acquisition, other category gameplay, full imported-villager scenes,
and original hardware remain open. Save formats do not change, but imported saves still
require matching or larger profiles and must not be loaded in V2. Continue
shared net/rod/golden-tool actions; preserve completed checks and the unchanged
models rather than adding per-item installers or repeating historical builds.

## Shared animated room-parent category

The existing complete-category refresh connects all eight balloons alongside
the sixteen fan/pinwheel parents. It consumes prepared/source records and the
already installed room resources, without a per-item definition, graphics
recompilation, duplicate model, new resident allocation, or changed saved format.

- Explicit lock: `build/v3-room-parent-category-06/build-lock.json`, ABI 127.
- ROM SHA-256:
  `e081dea749ea8372a8b67a59fc0635b95fe8a3b3868a51819794e77e0fb5c94c`.
- Report SHA-256:
  `3a8199501bd6211d28e11fb9133b502b3e67d8693dabc029eb2e1219ff139f3f`.
- UPS SHA-256:
  `57758f9df8319ecb2ab1ea7f2b98abfc206369f8d730f88f18ac2aa7ab46c23e`.
- Choices: 128 total, including 24 equipment parents. Room/catalogue forms are
  dependencies, not separate options. Native umbrella rows remain 32; the
  equipment catalogue contains 56 rows including those original umbrellas.
- Code: expanded furniture 1,976 bytes, parent readers 1,716 bytes, room
  lifecycle 1,072 bytes, each within its checked existing reservation.
- Complete icon descriptor/texture data: 2,016 bytes; three complete palettes:
  96 bytes at `804A67A0`, after parent code and before the descriptor table.
- Conservative menu requirement: 280,640 of 280,768 bytes. The existing
  inventory-work increase is retained, not applied a second time.

Source catalogue membership uses the donor indices, not the assigned native
destinations. Older source representations `1FF0..1FFC` map to `3C00..3C0C`;
`3000..300C` retains its canonical mapping. All eight source positions 48–55
survive. The eight new forward aliases convert balloons indoors; fans and
pinwheels still drop as parents. Existing garment aliases and every old parent
record remain. Sparse profiles delegate names/prices/ownership to selected
parents and bind the complete room vtable. Pickup restores the parent identity.

Actual catalogue actors retain a catalogue index 1024 above the imported room
index. The shared lifecycle accepts both verified contexts; native catalogue
construction and animation timing remain in control. The icon helper retains
its fixed public entry points, complete source artwork, and pointer bounds. The
menu's private hook is rebound to the newly compiled assembly entry while its
existing inventory-allocation metadata survives.

Initial builds reject an icon reservation short by 64 bytes and a catalogue
rebuilder that expects the pre-inventory menu endpoint. The shared palette
reservation and checked retained-pool handling resolve both. A reversed delta
assertion in the new pool guard is corrected before any cartridge is generated.
The first complete build (`-05`) and final provenance-complete build (`-06`)
have the same ROM and UPS hashes. Eight official names receive their actual
donor table/index/hash entries in the single `translations/provenance.json`.

Ten focused checks pass in 12.173 seconds. They cover complete source categories,
all destination/context mappings, retained old records/resources, full reused
models and sparse profiles, forward/inverse aliases, real catalogue ordering,
complete palette/texture bytes, bounded native readers, both room/catalogue
actor indices, unchanged unrelated DMA resources, original-ROM reconstruction,
128 choices, exact all/empty output, a mixed new-ID subset, and rejection of
incomplete dependencies. The first host comparison needs JSON tuple/key
normalisation; the corrected test passes without a cartridge change.

The first combined silent native run at
`build/smoke-v3-room-parent-category-01/` passes 216 records and 151 assertions.
It executes all 24 ownership/conversion pairs, actual native catalogue list
construction and ordering, four complete preview transfers, real animated
constructors, full English names/prices/framing, disabled-item hiding, original
umbrella retention, seven pocket-icon drawing cases, full-width hook registers,
memory guards, restored source/save state, checkpoint restoration, and clean
exit. Results SHA-256:
`ff02df062d499dbad733fde9bd3379a92105b8a45a3125c98a3ca7712704ab2d`.
No user save is used, and no test FlashRAM write is requested.

The private export `build/v3-room-parent-browser-01/` contains 128 options and
both donor-backed recipes. The actual worker at
`build/check-v3-room-parent-browser-01/` matches offline empty, all-installed,
villager/item, and equipment profiles, including an older-range balloon's mapped
identity. Cancellation, unknown selection, corrupt-plan rejection, local GET-only
access, absence of browser errors, and temporary server shutdown pass. Results
SHA-256: `6534874ed0f3adb13b7a3870904b251bfe0255e8502fcbc37c589f02b0c83165`.
This does not close the pending full-interface acceptance check.

Eight saved-profile bits are added; format 2 and saved record layouts remain.
Older profiles lacking the imports reject these saves. Keep separate tests;
never load imported saves in V2 or treat removing choices as migration. Ordinary
acquisition/equip/room placement/pickup/save, GPU appearance, and original
hardware remain unverified. Next use a bounded ordinary combined pass, then
continue remaining net/rod/golden-tool categories. Both served V2 patchers and
the main ABI-109 lock remain unchanged.

## Shared room-rig runtime

The shared runtime refresh installs all eight complete prepared room models and
one source-derived lifecycle implementation. No per-item script, reduced asset,
new resident allocation, or changed saved field is introduced.

- Explicit lock: `build/v3-room-rigs-runtime-03/build-lock.json`, ABI 126.
- ROM SHA-256:
  `febced937539f3f03777ddb98da7de952708ce21cba3d0d175b577a43c52c3d0`.
- Report SHA-256:
  `f217bb2b737ffbf75cc1c49858093a636c97bb4715f5634f4ab9ed09d186314e`.
- UPS SHA-256:
  `eddacfa7fafe3e1d174618df8c99c2e25b6c62e82bfaabcdf3c1f94be083975d`.
- Code: 1,056 bytes at `804B1800`; immutable descriptor table at `804B1E00`
  and vtable at `804B1FA0`, within the existing 60-KiB equipment module.
- Artwork: 44,400 bytes in a verified retired 53,248-byte equipment block.
  The allocator checks the immutable predecessor chain and 3,903 live ranges;
  no current resource, English-choice boundary, or existing import is overwritten.
- Source `1FF0..1FFC` uses reserved additive destination `3C00..3C0C`;
  source `3000..300C` retains its canonical mapping. Profiles remain empty and
  their selection bits remain off.

The runtime uses the native keyframe constructor, looping initializer, evaluator,
and skeleton renderer. Each N64 update performs two source movement steps and
consumes an interaction pulse once. The source zero/0.5/1.25 speeds and 0.01 step
are retained. Per-instance state occupies eight otherwise unused morph-work
bytes after the seven required vectors; the native tail and matrix banks are
untouched. Drawing submits all five visible model lists with the real parent
transform and current matrix-bank parity, checking both command streams first.

Four focused checks pass in 7.289 seconds: sanitizer timing/interaction/bounds,
stable noncolliding destination reservations, complete installed assets and
code/table/retired-space bindings, existing-resource retention, original-ROM UPS
reconstruction, all 120 choices, unchanged saves, and exact V2-12 empty output.
Two initial builds fail before cartridge generation on a signedness warning and
the missing shared compiler entry registration. Both implementation errors are
corrected in this build.

The first native fixture stops before DMA because the test runner lacks a proof
for the boot-resident transfer function. The one corrected retry adds the full
verified original-function proof. `build/smoke-v3-room-rigs-02/` passes 116
records and 89 assertions, including 84 component assertions. It covers the
smallest/largest complete resources, actual cartridge DMA, two independent
instances, native keyframe pointers/frame timing, switch/peak response, every
model list, both matrix parities, unused work/tail retention, balanced matrix
stack, all private/work/graphics guards, retained saves, checkpoint restoration,
and clean exit. Results SHA-256:
`ffa1ecadaf21d756657426a5633e128b68f726311c11c97746bb571e4e8f535a`.
No user save is used. GPU appearance, ordinary room placement/pickup, gameplay,
FlashRAM persistence, and hardware are not established by this component test.

Next extend the existing parent-category installer to consume these installed
assets, callback-bearing sparse profiles, source catalogue membership, forward
room conversion, inverse pickup, and optional selection. No additional graphics
conversion is required. Keep all eight parent choices off until that integration
is complete. Both served V2 patchers and the main ABI-109 lock remain unchanged.

## Shared indexed room-rig preparation

The automatic furniture pipeline discovers the source `indexed-switch-rig`
callback category and prepares all eight complete room balloons in one command.
`tools/v3_furniture_rigs.py` binds all four lifecycle functions, both effect-free
joint callbacks, actual helper calls, source speed constants, and the complete
relocated skeleton/motion tables. Models are selected by the verified source
index rule, not a per-item Python definition or copied held model.

- Prepared output: `build/v3-indexed-room-rigs-prepared-01/`.
- Asset-report SHA-256:
  `06215bb037c4b7cbd8fa06715d9a5ee83490ee1af8c6991eef91e2cf340efb69`.
- Eight objects, 44,400 bytes total: five at 4,656 and three at 7,040 bytes.
- Every object retains six joints, five visible model lists, and a complete
  61-frame animation. Each fits the 9,216-byte native room model bank.
- Source representations: `1FF0..1FFC` and `3000..300C`, with their existing
  parent IDs and room/collection conversion contexts retained.
- Current cartridge remains ABI 125 at
  `build/v3-balloon-inventory-02/build-lock.json`; no room runtime is installed.

The shared keyframe module now supplies joint-model descriptors to both held
and room converters. Its animation packer supports an explicit aligned suffix
offset while retaining the default zero-offset format. All graphics continue
through the established complete texture/material/vertex/triangle converter.
No source joint, animation channel, reflection coordinate, IA8 alpha, or list
is discarded. Room and held rigs remain distinct source resources.

Source profile/name discovery accepts the older donor furniture range, but the
ordinary scan only adds older IDs proven by room aliases. It does not duplicate
existing native furniture or assign destination IDs. Prepared objects retain
official name/table/hash references and remain rejected by ordinary installation;
there is no new applied translation or change to the sole provenance catalogue.

Four category checks pass in 6.371 seconds: complete table/range/name discovery,
rejected changed code/dependencies/constants/effectful callbacks, aligned motion
packing, and complete compiled models/skeletons/keyframes. Independent texture,
vertex, material, triangle, matrix-binding, and all relocated-pointer comparisons
pass across the eight actual assets. The first malformed-table fixture removed
a relocation without rebuilding its lookup index; correcting that fixture gives
the intended rejected incomplete table. This is not a cartridge defect.

Seventeen affected shared keyframe/held-converter checks pass in 5.812 seconds,
including unchanged previously prepared resources. Four shared furniture checks
pass in 17.427 seconds, covering prepared-only rejection, retained indexed
sequences, original profile scalars/footprints, and unsupported lifecycle/sounds.
No native emulator run is needed for this converter-only change; the unchanged
ABI-125 component evidence is retained, not replayed.

Next install the actual room lifecycle: per-instance source speed/target,
interaction response, complete looping keyframe playback, and native drawing.
Connect context-correct room placement and parent pickup, all eight collection
representations, and optional profile readers. Reserve additive destination
identities for the four older source IDs without reusing native items. The
44,400-byte batch exceeds the current 19,632-byte append space; use checked
retired-resource reuse or verified storage expansion, retaining the English
choice boundary at `025F0000`. Do not reduce assets to avoid that work.

Both served V2 patchers, main ABI-109 lock, current cartridge, saved formats,
and 120 experimental choices remain unchanged. Prepared art is not gameplay,
GPU appearance, ordinary acquisition/persistence, or hardware verification.

## Shared balloon inventory previews

The shared inventory adapter installs all eight balloon previews, including
source WAIT animation selection, seven-joint/eight-vector work, native reflection,
and all four drawn joint lists. It retains all prior preview entry addresses,
tables, timing, and resource identities. Parent choices remain disabled.

- Explicit lock: `build/v3-balloon-inventory-02/build-lock.json`, ABI 125.
- ROM SHA-256:
  `84b4f55a3b501a05387bb33d3132b30c51bfef0a0260cdd1ed416fdb08460495`.
- Report SHA-256:
  `24b0f96b36ed9fd38594fb708ed4e3a84f2013011c9622053849c82459647917`.
- UPS SHA-256:
  `eb8a496e502c434ba81748dd42f533771f892d7c6a80b050a418e0171d773868`.
- Inventory code: 824 bytes in the existing 1,024-byte reservation.
- Preview records: 24, including eight balloons, eight pinwheels, and eight fans.

The first build stops before cartridge generation because an old pinwheel-only
animation-type check rejects the type-four balloon idle motion. The corrected
category check validates both real types and their joint counts. No art is
truncated or replaced, and no new allocation or saved field is introduced.

Three focused tests pass in 7.917 seconds. They verify regenerated source
records, the actual source animation remap, old timing/entry retention, rejected
short work buffers/missing actions/bad motion/foreign callbacks, exact table and
code changes, unchanged unrelated DMA resources, original-ROM UPS reconstruction,
all 120 existing choices, retained saves, and exact no-import V2-12 output.

The first silent native run, `build/smoke-v3-balloon-inventory-01/`, passes
141 records, including 103 component assertions and four final fault/memory
checks. The shared fixture selects smallest/largest models per draw category:
two balloons and two retained pinwheels. It executes actual cartridge-loaded
inventory initialization, complete model/motion DMA, source-correct first-frame
timing, four/two joint lists, reflection/matrix allocation, graphics/stack/work
guards, and unchanged source state. Scratch is freed, the checkpoint restored,
and the isolated emulator exits cleanly. Results SHA-256:
`ad482d7658f57ab0f9f152c619cdbd23b8e6aef47f82daaa4b5d98df63dbb20b`.
No ordinary inventory interaction, GPU appearance, hardware, or new save/reload
claim follows from this component test. No user save is touched.

Next implement shared animated room representations and their context-correct
parent conversions. All eight source balloons become room furniture indoors;
four use older donor IDs `1FF0..1FFC`, requiring additive destination mappings.
Their actual room rigs and switch-driven speed response are separate from held
models. The ordinary static fan/pinwheel catalogue adapter cannot substitute for
them. Keep parent choices off until these dependencies are installed.

The main ABI-109 lock, both served V2 patchers, 120 experimental choices, and
format-2 saves are unchanged. Imported saves require matching/equal-or-larger
profiles and remain unsuitable for V2. No source text or provenance changes.

## Shared balloon actions

The shared `--player-actions` refresh installs the complete source balloon
main/draw category in `held_rigs.c`. It retains all pinwheel/fan resources and
choices while adding source setup, the missing hand delta, lean/walking/string
motion, spring timing, pause handling, reflection setup, and four-joint drawing.
It does not add per-item scripts or expose incomplete balloon selections.

- Explicit lock: `build/v3-balloon-actions-02/build-lock.json`, ABI 124.
- ROM SHA-256:
  `265dd75fb6aed76305c8abd323f90bfd2cb3ef899f1f6d479f713cc8f5c089df`.
- Report SHA-256:
  `b8048dd1958e80c92289b8b5caadc49147b10872467cac7beca31604e105e6ad`.
- UPS SHA-256:
  `cf9c480aa95af9285cac186cae44b153c6f0f65af03740ce3b92c06b5ea07da5`.
- Player allocation: `1370` to `13A0`, with 48 transient bytes at `+1370`.
- Module: `E000` to `F000` bytes; compiled rig code is 4,336 bytes.
- Loop-volume state: `804B1FE0`; module guard: `804B1FF0`.
- Audio sequence: all 20,240 bytes retained at a new checked ROM location;
  actual sequence header updated, with no audio data or heap-budget changes.

The new allocation follows both expanded work arrays, rather than overlapping
an existing native tool or saved field. The hand callback preserves its original
position/matrix operations. The native frame controller's duration is `A20`,
not `A18`; source and native layouts were verified before integration.
Two source substeps use half the native measured hand delta/speed. The GameCube
GX-only texture-edge threshold callbacks are adapted to native RDP alpha
coverage in the converted materials, not emitted as unsupported N64 commands.

Five focused checks pass in 6.335 seconds. Three sanitizer executions cover
retained ordinary/pinwheel behaviour, balloon setup across all eight kinds,
same-category transitions, 8,000 motion updates, paused drawing, scale changes,
hand/matrix tracking, and state bounds. Two cartridge/composition checks verify
exact player/core changes, callback rebinding, intact relocated audio, complete
unrelated-resource retention, module bounds/guard, original-ROM UPS
reconstruction, all 120 choices, and exact V2-12 no-import output.

The first silent native run, `build/smoke-v3-balloon-actions-01/`, passes 148
records and 96 assertions. It verifies actual cartridge-loaded code, player
allocation, ordinary setup, two representative pinwheel rigs, and two complete
balloon rigs (native model indices 40 and 45). Both balloons emit all four source
joint lists, produce frame `26.9150009` and speed `-0.0810415`, preserve duration,
consume the second substep, and retain their parent matrix. Actual hand callback,
animation-bank playback, graphics/stack/player/bank guards, saved-state retention,
checkpoint restoration, and final guards pass. The emulator exits cleanly.
Results SHA-256:
`ef7fba993fe3865cb897c861daafafce869b4cc8525650fb0f2d816ee810b9d3`.

The existing shared probe is extended by category, not by individual item.
Its retained `representative_rigs: 2` summary counts the pinwheel pair; the two
additional `held_balloon_native_draw` records contain the balloon evidence.
The summary generator now reports both category counts and their total for
future runs; no replay is needed for that metadata correction.

This is native component execution, not GPU-rendered appearance, ordinary
balloon gameplay, hardware verification, or new acquisition/save evidence.
The five focused tests and native fixture are bounded checks of this change;
passing unchanged bank/inventory allocation evidence is retained without replay.
The first compiled build is preserved locally; the second exposes the actual
balloon setup callback for direct native verification and is the current lock.

Next extend the shared inventory adapter with balloon-specific reflection
drawing and complete preview records, then run the existing parent-category
expansion and optional composers. No additional model conversion is required.
The 120 choices, complete installed resources, format-2 save layout, and exact
V2-12 empty selection remain. Imported saves require matching/equal-or-larger
profiles and must not be loaded in V2. The main lock and both served patchers
remain unchanged. No source text is added; provenance is unchanged.

## Shared inventory joint capacity

The shared `--player-actions` refresh extends the inventory's independent joint
work when installed equipment requires more vectors. It changes two initializer
pointers, the BSS relocation size, both actual submenu-owner extents, and the
common aligned allocation. It does not install a per-item adapter or new preview
record. Existing code, table entries, assets, callback meanings, and saves remain.

- Explicit lock: `build/v3-inventory-capacity-02/build-lock.json`, ABI 123.
- ROM SHA-256:
  `49a353fda4c39c293c11f3575832e195848039c10c749afc583db16bab888a31`.
- Report SHA-256:
  `26d368cab7a7261885679af5025d2ee3872e7a6c8e0ed79ef2ba20f259075c99`.
- UPS SHA-256:
  `fe37e6697dd46760cadefcb292b7a104911059e531796a0f13622b0be95b569c`.
- BSS: `5E0` to `640` bytes, with 48-byte arrays at `+5E0/+610`.
- Resident overlay: `47A0` to `4800` bytes; shared pool adds 64 bytes after
  native 64-byte allocation rounding. Both metadata rows end at `80881C80`.
- Build `v3-inventory-capacity-01/` has the same ROM and patch; `-02` binds
  the final source with an additional signed-immediate boundary rejection.

Four focused checks pass in 6.446 seconds. They reproduce the installed update,
verify exact initializer/metadata/BSS/pool changes, exercise relocation at two
addresses, reject damaged ownership and unsafe allocation words, preserve every
unrelated resource and the complete equipment module, reconstruct the original-
ROM UPS, and retain all 120 choices, profile bits, and exact no-import V2-12.

The first silent native check stops at a fixture guard placed in the loader's
relocation workspace. Its observed bytes are the correct relocation header,
`00003D30 000003F0 000000A0 00000640`, not a runtime array overflow. The
corrected fixture protects the relocation workspace end before loading and
the BSS end after relocation has finished using that space.

The single justified retry at `build/smoke-v3-inventory-capacity-02/` passes
99 records and 83 assertions. It verifies complete cartridge loading/relocation
and zeroed expanded BSS, ordinary-net timing, smallest/largest installed
pinwheel initialization and joint drawing, matrices/graphics bounds, both new
work pointers, and untouched state. A temporary otherwise-disabled table slot
then supplies a real seven-joint balloon and its complete animation to the
native initializer. All eight vectors are written; the morph buffer, old short
arrays, and guards remain intact. All changed table data is restored, the
complete module compared, scratch freed, checkpoint restored, final fault and
memory guards checked, and the isolated silent emulator exits cleanly.
Results SHA-256:
`76936d59f549002db71535203a354a6180d8a9b8ae50a81b5e911443fd99c114`.

The temporary table data is a capacity probe, not a supported balloon preview
or ordinary gameplay. No uploaded code, user save, public/local patcher, or
main lock changes. Equal-profile ABI-122/123 save compatibility is expected;
fresh cross-build game reload and hardware are not claimed. Imported V3 saves
remain unsuitable for V2.

Next implement the complete balloon main/setup/draw behaviour from
`local/ac-decomp/src/game/m_player_item_balloon.c_inc` and its separate inventory
drawer in `m_inventory_ovl.c`. Both source drawers set joint-specific texture-edge
alpha and reflection; a null-callback pinwheel drawer would omit those details.
Keep behaviour, preview records, selection, and ordinary interaction explicitly
pending. Do not replay the completed capacity checks without a relevant change.

## Shared rig capacity and resource extension

The shared equipment installer extends existing rigs with all twelve complete
net/rod/balloon models. It derives categories and joint capacity from source
bindings, retains all existing resources, and installs no new selectable parent.
The proposal contains all 50 equipment resources, including twenty animated
models. Models are reused from the prepared bundle; nothing is reconverted.

- Explicit lock: `build/v3-rig-capacity-03/build-lock.json`, ABI 122.
- ROM SHA-256:
  `e539da80e8755d10c7da1cfc84343db0e5bcce353a0fc071155516b3480829fd`.
- Report SHA-256:
  `67a9f0faca2890a1efc9b86136a7fd847525f49f351f00eb9c3cc21d9aa5e5dc`.
- UPS SHA-256:
  `7d0c6f2d1b703681cac8cb31f3de270a9c071025d5f97a8e3d056403de4a3fa5`.
- Outdoor banks: two times 7,168 bytes; scene arena `949C0`, an additional
  3,840 bytes relative to the preceding proposal, 5,568 over the native arena.
- Transient player: `1310` to `1370` bytes; two eight-vector arrays at
  `+1310/+1340`, with four checked initializer pointer changes.
- Module: unchanged 56-KiB reservation and public entries, updated in place at
  blob offset `3BD350`.
- New model bytes: 46,976, stored in the checked retired ABI-117 module at
  blob offset `3B0350`, whose 53,248-byte extent does not overlap live resources.

Six focused checks pass in 9.569 seconds: complete new and retained resources,
source categories, all model/motion bounds, exact bank/profile/initializer
changes, original-ROM UPS reconstruction, unrelated resource retention,
source-mutation rejection, repeatable further joint growth, retired-range hash
and live-overlap rejection, unchanged public entries/guards, and exact all/empty
composition. Sanitizer readers cover original, 5,248-byte, and 7,168-byte limits;
the added exact-capacity boundary check passes in a subsequent 0.879-second run.

The current silent native retry at `build/smoke-v3-rig-capacity-02/` passes
116 records and 93 assertions, including 89 component assertions. It loads
the complete actual player owner/module, alternates six complete model/animation
transfers, executes the native player initializer and animation update for a
five-joint rod and seven-joint balloon, verifies both enlarged work arrays,
retains the old short arrays, and checks memory guards and unchanged save state.
The allocation is freed, checkpoint restored, fault/module guards checked, and
the emulator exits cleanly. Results SHA-256:
`05ab6545da858935ff4a529b3886fda4ce76b81ca856b585fe676ea01c272dec`.

The first native attempt reaches full eight-vector playback but its fixture
requests a zero-length unused-tail read for the largest rig. The debugger
rejects that read; the correction skips the absent tail. Its 97 records/79
passing assertions remain partial at `build/smoke-v3-rig-capacity-01/`, SHA-256
`bcf94fc5cda5204869d4287fa8fb038275ccf5a4b06a199cd24ba7d348c44fdc`.
The single justified retry succeeds. No uploaded code or user saves are used.

Build attempts `v3-rig-capacity-01` and `-02` stop before producing a cartridge:
the first lacks the `u32` import, and the second correctly detects exhausted
import VROM space. The completed installer safely reuses a verified retired
module instead of appending another current copy or overlapping choice data.
Both failed output directories are preserved.

The 120 experimental choices, format-2 profile, inventory tables/bank, existing
actions, and translation-only V2-12 output remain unchanged. Equal-profile
ABI-121/122 compatibility is expected without migration; a fresh cross-build
game save/reload is not claimed. Imported V3 saves remain unsuitable for V2.
The main lock, local/public patchers, and original ROMs/saves are unchanged.

Continue with balloon actions, the inventory's separate joint storage and
complete previews, then parent/acquisition support. Net/rod behaviour and
golden-tool differences remain open. Native component checks do not establish
ordinary interaction, GPU appearance, acquisition, persistence, or hardware.
Do not rerun completed bank/playback checks without a relevant change.

## Shared joint-matrix and IA8 conversion

The shared format converter prepares the remaining twelve animated equipment
roots: ordinary/golden nets and fishing rods plus eight balloons. It retains
all skeleton joints, material state, articulated vertex-cache operations,
matrix loads, complete texels/alpha, and triangles. No per-item converter or
static substitute is added. Existing pinwheel assets are reused, not rebuilt.

- Prepared bundle: `build/v3-held-matrix-prepared-02/`.
- Receipt SHA-256:
  `76d32952d729f2c495e8bb31e465bdcd075823f6fb71db85a24b67e541aa43bf`.
- Twelve complete objects: 46,976 bytes, 1,219 vertices, 850 triangles, 46 lists.
- Combined model/animation bounds: nets 4,320/4,336 bytes; rods 2,960 bytes;
  five balloons 4,784 bytes and three balloons 7,168 bytes.
- Nets: six joints/three shown; rods: five/four; balloons: seven/four.
- Shared scan: 34 convertible model roots, comprising 14 static and 20 animated.

`prepare_models` derives the visible-matrix limit for each model from its
skeleton and joint bindings. `parse_model` retains partial cache destinations
and checks every triangle against initialised slots. Matrix references must
use the exact model-view load and segment `0D`, aligned to 64 bytes, within
already published visible joints. The native skeleton drawer's segment setup
and matrix publication order are confirmed in `upstream/af/src/code/c_keyframe.c`.
The common compiler preserves those loads and their positions among vertex loads.

The texture adapter untile-orders GX IA4 and swaps intensity/alpha nibbles to
N64 IA8, preserving all levels. The supplied donor executable's complete format
table confirms IA/8 maps to GX IA4; the donor `emu64::texconv_tile` implementation
confirms the nibble ordering. Native commands retain IA8 width/stride, disabled
palette lookup, wrapping, shifts, primitive/environment colours, and combiners.

The runtime validator now takes explicit source categories and joint-vector
capacity. Its existing caller retains category 22/seven vectors and accepts the
unchanged complete pinwheel bundle. It rejects the new categories by default;
an explicit eight-vector validation can verify the complete new bundle without
installing it. This prevents a new converter from silently changing an older
runtime installation's required or permitted category.

Thirty-five focused checks pass in 10.395 seconds, using
`V3_ANIMATED_HELD_BASE=build/v3-held-category-02` and the animated-held, shared
format, donor format-table, static-held artwork, and furniture-format tests.
They compare every native texture sample, vertex, triangle and its matrix
association, material format/stride/LUT, model binding, and skeleton field.
They reject uninitialised cache slots, future/unaligned/wrong-segment matrices,
bad alpha/texture sizes, missing resources, and insufficient joint capacity.
The current installed resources and previously prepared pinwheel/static models
remain unchanged. Python parsing and diff checks pass.

The first conversion invocation passes a relative output path to a helper that
requires an absolute repository path. It stops before compiling a model; its
partial output is preserved at `build/v3-held-matrix-prepared-01/`. The corrected
absolute-path invocation produces the complete `-02` bundle with the pinned
Docker compiler. No emulator run is needed for this converter-only change.

No ROM, saved data, main lock, or served patcher changes. These are prepared
models, not twelve new playable imports. Continue from the explicit ABI-121
cartridge: extend the shared resource installer, bank and joint/morph capacity,
real balloon/tool behaviours, inventory, parent records, and acquisition before
enabling the remaining categories. Existing format-2 profile restrictions remain.

## Seasonal setter-copy diagnosis

The focused check uses the unchanged ABI-121 cartridge at
`build/v3-held-category-02/`, SHA-256
`42fa74a2f66cfe28a4f81c1e4a718cbee86ed963e487982972f46ed9d63d7253`.
It classifies the recorded setter-copy stack mismatch as dependent on the
installed emulator's breakpoint boundary. No cartridge change is needed for
the tested copy/return operations; the emulator's internal cause is not proven.

`build/smoke-v3-ground-copy-01/results.json` reproduces the mismatch with exact
PC/SP observations. Stopping at the cherry setter's internal return instruction
reports SP `804D1108`, one 264-byte frame above expected `804D1000`, despite the
complete code containing only one matching stack adjustment. Results SHA-256:
`ae798e210bd286af012e73d5cbf74ea7cf9a7733ca57f79d92dc438c723a244e`.

The one justified retry, `build/smoke-v3-ground-copy-02/results.json`, checks
SP before the adjustment and after the complete epilogue at an external return
address. All four actual cartridge-loaded seasonal owners return with the
correct stack. Each clears its full local array, retains the incoming common
pointer, copies all 108 indices (107 in winter), preserves the next array, and
sets its completion flag. Private guards, the complete equipment module, zero
CPU fault, restored owner/profile/scratch state, heap release, and checkpoint
reload have passing evidence. The fixture scratch area follows the module's
actual extent, avoiding the old fixed address inside the larger 56-KiB module.

The retry records 75 results and 57 passing assertions. The overall process
still exits unsuccessfully: the final translation-guard expectation contains
only three words for a 16-byte read. The actual read contains the correct four
guard words. The literal is corrected, but no further complete run is made;
the retry/harness budget is spent. The final equipment-guard read after checkpoint
reload and the ordinary successful-exit path are unexecuted. Do not relabel this
partial run as a complete pass. Results SHA-256:
`fdfa9f93739a4e6fccdd981f66cebef1e3076f05fc6080b35cab29c9e38ed712`.

The focused mode deliberately skips category classification, constructors,
drawing, and ordinary gameplay; its result reports zero constructed index arrays
and imported descriptors. The existing full probe shares the corrected copy
window but has not been replayed. Remaining seasonal rendering and ordinary
gameplay checks stay open. Both runs are silent and use isolated checkpoints;
no user saves, cartridge code, main lock, or served patchers change. Continue
shared equipment conversion/integration from the explicit ABI-121 lock.

## Shared parent category expansion

The shared catalogue refresh connects all eight pinwheels in one source-derived
category batch. It extends existing selector, parent-name/price, icon, collection,
catalogue, and optional-profile records, preserving all eight fans. Existing
animation, sound, player, inventory, event, and seasonal code stays unchanged.
Prepared models are reused; only eight new catalogue representations are appended.
No per-item installer, extra resident allocation, or saved-format change is added.

- Explicit lock: `build/v3-held-category-02/build-lock.json`, ABI 121.
- ROM SHA-256:
  `42fa74a2f66cfe28a4f81c1e4a718cbee86ed963e487982972f46ed9d63d7253`.
- UPS SHA-256:
  `474abb4daab5723ae20cbfa657dcdf34a5c0a4665fc021a5849560e781ec79c6`.
- Build receipt SHA-256:
  `53def547f634fcd37adbff01d78f47bd5f54190e1d1f0959f471a3002587392e`.
- Equipment module SHA-256:
  `e45074629539ba60b93e1be32c34b8a7d6cb8bf1156c124991620ca03af7ff7c`.
- Choices: 120, including 16 equipment parents; representations are not choices.
- Catalogue: 48 umbrella-category rows, including 32 originals; 62,928 loaded
  bytes, 736 relocation bytes, 280,576/280,704 conservative pool use.
- Pocket artwork: 1,568/2,048 reserved bytes; equipment module: unchanged 56 KiB.

Six focused checks pass in 10.731 seconds:
`tests.test_v3_held_catalogue.CategoryRefreshTests` and
`tests.test_v3_held_selection.CategorySelectionTests`. They regenerate complete
source categories, reject missing dependencies and changed modules, check exact
data-only changes and untouched owners, preserve existing models/profiles,
relocate the complete catalogue, verify official name credits, reconstruct the
UPS, check all/empty/individual compositions, and execute the format-2 save
codec for equal/superset/missing profiles. Python parsing and diff checks pass.

The first native catalogue run at `build/smoke-v3-held-category-01/` passes
128 records/86 assertions. It executes actual catalogue loading, relocation,
collection, donor ordering, representative full English names/prices, complete
model transfers, disabled-parent hiding, retained original umbrellas, guards,
state restoration, checkpoint restoration, and clean exit. Results SHA-256:
`616d836634ea95522a129758cec3a955752886e709dd2279fd98f99b934b7305`.
This run uses build `v3-held-category-01`; `-02` tightens a source-inventory guard
and emits the identical ROM/patch. Its passing native evidence is retained,
not replayed. Neither run claims GPU appearance or ordinary ordering/delivery.

The shared event-menu probe selects a source category and derives its price,
message, identities, and stock slots from installed records. Its first run,
`build/smoke-v3-category-purchase-01/`, passes 36 assertions through pinwheel
choices, the 680-Bell price, and full-pocket/short-funds rejection, then times
out during successful purchase. The old fixture supplies a heap-allocated
private-player pointer and changes only the current profile, violating the
installed collection reader's actual-player-slot and matching-live-profile
requirements. Its results are retained, SHA-256
`6250012029b74134948829c03c6e0a8f2600fb773ebd7a1a8d0bfc0e90327803`.

The one justified retry uses a backed-up real first-player slot and the actual
save-state reset function, restoring both afterwards. No game implementation
changes. `build/smoke-v3-category-purchase-02/` passes 187 records/75 assertions:
native pocket insertion, two 680-Bell payments, actual collection credit for
both variants, one-time charging, stock consumption, handover requests,
sold-out retention, original wares, guards, restored globals/checkpoint, and
clean exit. Results SHA-256:
`fd627acad495ff059c735e741fd0d1cfcc1aca6f9e0a8c8a87071d4d65a33d88`.
The fixtures are silent and isolated, with FlashRAM writes disabled. These are
native component transactions, not ordinary walking/conversation/purchase
evidence or a save/restart test. The fixture retry allowance is spent.

The unserved export `build/v3-held-category-browser-01/` provides all 120
choices and both donor-backed reconstruction recipes. The actual browser
worker at `build/check-v3-held-category-browser-01/` matches offline outputs
for empty, all-installed, villager/item, and pinwheel/fan selections. It also
passes cancellation, unknown-option rejection, corrupt-plan rejection, no
browser errors, and local GET-only access; the temporary server stops.
Results SHA-256:
`8838af4cfc4f0bb59837ee0039586990a664d40ff4423af76d4cc0ef8e7381af`.
This worker check does not close the previously partial full-interface test.

All previous profile bits remain; eight pinwheel bits are added. Format 2 and
save code stay unchanged. Equal/superset-profile loading has codec evidence;
older builds missing these imports reject their saves. Removing imports is not
migration, and imported V3 saves must not be loaded in V2. Empty composition
returns exact corrected V2-12. No new ordinary cross-version reload or hardware
test is claimed. The main ABI-109 lock and both served V2 patchers stay intact.
The independent seasonal-copy assertion remains unresolved and blocks a playable
handoff. Continue from the explicit ABI-121 lock, classify that recorded window,
and finish remaining shared categories and ordinary gameplay/persistence.

## Shared animated inventory previews

The existing runtime refresh consumes ABI 119 and connects all eight pinwheel
previews through the shared inventory tables. It reuses native skeleton drawing,
keyframe work areas, and the model bank. A small category-aware initializer
adapter supplies the source preview spin speed; original tools retain theirs.
No model conversion, allocation growth, parent enablement, or saved-format
change is added.

- Explicit lock: `build/v3-inventory-rigs-02/build-lock.json`, ABI 120.
- ROM SHA-256:
  `41e6a2117b20af9224b8c6eba33ee1380878c23ba2e3183cd3b9aada241ed33a`.
- UPS SHA-256:
  `37426b4a25902408140ceae459d6915274a1e7e71edda777b8e90b46e125a3dc`.
- Build receipt SHA-256:
  `01422ed630a41eb8c0aa556f0d1b65500d8d5b8a26ba9af4b5aa77d75c9db8d1`.
- Equipment module SHA-256:
  `9fc85d822492efc1225a7a705aae7c0b097e113ca07cab51f34f212d179fe72e`.
- Inventory code: 576 bytes at `804A9000`, SHA-256
  `c0d791248429f7d9752b97a65543f35ff98e0bd4614fc72ef5e70eb908c51b14`.
- Preview records: 16, retaining eight fans and adding eight pinwheels.
- Resident module: 56 KiB; preview model bank: 15,584 bytes, both unchanged.

Three focused current-cartridge/composition checks pass in 6.252 seconds.
They regenerate all source records, validate every table binding, compare exact
permitted changes and the complete speed adapter, retain all other owners/code/
resources, reconstruct the UPS, and verify unchanged 112 choices plus exact
all/empty composition. Source parsing and diff checks pass. Runtime C is
unchanged; no redundant historical sanitizer replay is needed.

The first silent native run, `build/smoke-v3-inventory-rigs-01/`, passes
72 records/56 assertions. Results SHA-256:
`d68ccd3550e03a4c405d38fdc017c73d4ae31ebfdbc83766747a6808c1446d4d`.
It loads and relocates the complete cartridge inventory owner, executes the
actual item-loading/initialization branch for original net kind 1 and imported
kinds 18/24, and checks complete smallest/largest model-plus-animation transfers
with untouched bank tails. The original speed/frame remain 1/2; imported
speed/frame are 15/16. Native work/morph pointers, both actual joint display
lists, two matrix allocations, both graphics streams, matrix-stack balance,
parent transform, all private guards, unchanged saved state and resident module,
checkpoint restoration, final guards, and clean exit pass. No native retry is
needed. New focused test work takes approximately six minutes.

The first build attempt `v3-inventory-rigs-01` stops before producing a ROM:
its new guard expected animation type 2, while the verified pinwheel motion
has source/native type 5. The corrected guard also binds the motion's actual
joint count to the model. Build `-02` is the only resulting cartridge. A test
patch initially listed hunks out of source order and applied nothing; the
correctly ordered patch succeeds before the native run.

This fixture executes cartridge code against isolated inventory state. It does
not establish ordinary menu interaction, selected pinwheel gameplay, GPU
appearance, acquisition, or hardware. Parent choices remain disabled. The
existing fan profile and format-2 save code are unchanged; matching-profile
compatibility with ABI 119 is expected both ways, without a newly claimed
ordinary cross-version reload. Imported V3 saves must not be loaded in V2.
The main lock and both patchers stay unchanged, and the independent seasonal-copy
issue remains unresolved. Continue shared parent/readers/catalogue/selection
integration using the installed category descriptors and prepared artwork.

## Shared held loop sound

The existing `--refresh-runtime --player-actions` route consumes ABI 118 and
installs the complete pinwheel level sound for the shared rig category. No
per-item installer, copied sample, new allocation, or enabled choice is added.

- Explicit lock: `build/v3-held-rig-sound-04/build-lock.json`, ABI 119.
- ROM SHA-256:
  `9bd860fd2cf04da77b54f66ef61ef2babe844c0a9f4b82699761c0d268ebd8da`.
- UPS SHA-256:
  `06fb251a3c01bb8714f42a4648e482ef493f1acd5cdcf5fb17a3dd39784dea83`.
- Build receipt SHA-256:
  `db57fa0fe25944148555e35004fe5ec890949c6ecce8c7cbaf1c29d6e610dd0f`.
- Rig code: 2,192 bytes at `804B0000`, SHA-256
  `988b216a8e84e00b7b81399ab08be34289b17083123fe71cad62ec4231aff2e4`.
- Module: 56 KiB; four gain bytes at `804B0FE0`; guard at `804B0FF0`.
- Sound sequence: 20,240 bytes; 32 added loaded bytes, 192 bytes spare under
  conservative accounting for every permanent resource, no heap growth.

Ten focused checks pass in 6.255 seconds. Shared synthetic parser checks cover
short/long durations, loops to mode or note, complete short envelopes, exact
rebinding, every truncated prefix, invalid control/pointer/velocity/envelope,
and zero elapsed time. Sanitizer checks run the full rig behaviour with and
without sound, including negative/saturated/zero speed and all 256 channel
values. Current-cartridge checks recreate the source conversion, retain every
old sound, bind the complete equivalent sample/loop/predictor, verify exact
code changes and callback rebinding, preserve unrelated resources and save
code, reconstruct the UPS, and retain 112 choices plus exact import-free V2-12.
Python parsing and `git diff --check` pass.

The first silent native attempt, `build/smoke-v3-held-level-sound-01/`, passes
165 records and 50 assertions. Results SHA-256:
`8363ae1f2e3541c3949f4ceaa60746fc86e7b0ab414a30f4043b567421ebc5f7`.
The cartridge-loaded module, patched core call, complete loop program, dispatch,
and actual heap bounds pass. It executes gain for positive/negative/saturated/
zero speeds and actual native volume calls, including the original pause
branch, fade factor, pan, and reverb commands. The actor registers uniquely,
retains its level sound through ten refresh frames, and expires through native
processing after zero-speed updates. Thirteen actual sample-DMA observations
match cartridge data. Private stack/actor/module guards, unchanged saved state,
checkpoint restoration, final guards, and clean exit pass. No FlashRAM writes
or physical audio playback are requested. No ordinary pinwheel gameplay,
listening/PCM quality, GPU appearance, or hardware verification is claimed.
The native probe needs no retry. New focused test work takes approximately
nine minutes, within the batch allowance; retain the passing result.

Build attempts `v3-held-rig-sound-01` through `-03` produce no cartridge: the
new parser initially assumed the loop target included the continuous-mode
command, rejected zero-length alignment padding, and inherited a two-step
envelope minimum inappropriate for the source's attack/hold pair. Those parser
defects are corrected, without changing source timing or inserting envelope
steps. Synthetic tests retain each case. The final `-04` cartridge is the only
sound-enabled proposal. An initial wrapper called nonexistent `main`; the
correct builder entry is `refresh_runtime`.

Continue animated inventory integration, then shared parent/acquisition/
catalogue/selection connections. The native preview initializer already loads
model plus animation into its item bank and owns seven-vector work/morph
arrays. The source windmill callback is an ordinary recursive skeleton draw;
its preview speed needs the native two-source-update conversion. No inventory
changes are installed by this batch.

Save format 2 and existing profile requirements remain unchanged. Matching
profiles are expected to remain compatible with ABI 118 both ways; no new
ordinary cross-version reload is claimed. Imported V3 saves must not be loaded
in V2, and removing imports is not migration. The independent seasonal-copy
issue remains unresolved; the main lock stays ABI 109. Both served patchers,
original saves, and earlier cartridges remain unchanged.

## Shared animated-held actions

The shared `--refresh-runtime --player-actions` adapter consumes ABI 117 and
adds source-based setup, movement/wind response, animation, and joint drawing
for all eight pinwheel kinds. Both held callback tables gain category 22;
original tools, fan callbacks, and all 38 complete equipment resources remain.
It adds no selectable item and does not claim complete pinwheel gameplay.

### Current proposal

- Explicit lock: `build/v3-held-rig-actions-03/build-lock.json`, ABI 118.
- ROM SHA-256:
  `e8bcc7cb059abe4481736a4b7e567a7b615f6ad6be5574bc570298533b72fb81`.
- UPS SHA-256:
  `70445565b3c86c32c2ee07b93506c9f2dea6e53adfce19fa89c48458313ac39b`.
- Build receipt SHA-256:
  `8eeeae97afc77da28b4797f1875418d691e36dde1bc8a1854c7bf804f7aed9a5`.
- Equipment module SHA-256:
  `8e50876aad3b8f2493ea06e4bfdcd69d595da11ce63f64ada43235f281065189`.
- Shared rig code: 1,932 bytes at `804B0000`.
- Module: 57,344 bytes, guard `804B0FF0`, 4,096 additional resident bytes.
- Player allocation: `12D8` → `1310`, 56 additional requested bytes;
  44 bytes of transient state and twelve padding bytes.

The complete native setup base remains intact behind an eight-byte entry hook.
The callback resolves the currently loaded owner, preserves ordinary setup,
and retains same-kind pinwheel speed/frame across player-action changes.
Movement and wind follow the source projections, opposing-wind rule, and speed
limits, adapted to two source intervals per N64 update. Native animation keeps
its actual segment-six switching. The original double matrix banks and recursive
skeleton renderer draw the complete joints; the source tip/axis callback updates
only the new transient state. See the
[contract](../../specs/V3_HANDHELD_ITEMS.md#shared-animated-held-actions).

### Verification and corrected failures

Four focused checks pass against the current proposal in 6.829 seconds:
sanitized setup across original/all imported kinds, same-kind and changed-kind
frame/speed handling, wind direction, motion/rotation, wade suppression, braking,
large-displacement safety, both matrix banks, joint callback updates, and bounds;
complete cartridge change accounting; original resource/relocation retention;
real player/module reservations, callback/bridge instructions, startup extent,
original-ROM UPS reconstruction, future tail reuse, unchanged save/profile,
all 112 existing choices, and exact full/import-free V2-12 composition.

`build/v3-held-rig-actions-01/` is a partial compile output: the first assembly
used register spelling the installed assembler rejects. Correcting the spelling
produced `build/v3-held-rig-actions-02/`, but its setup continuation subtracted
only `538C`, missing the high `20000` of the actual `2538C` displacement.
The silent native attempt at `build/smoke-v3-held-rig-actions-01/` confirmed
startup completion and then froze before reaching the paused game frame. The
emulator log records invalid RDRAM access. This was an actual implementation
defect, not a fixture limitation. The failed ROM hash is
`dd6798958e608c3fa36baf7617758df5c19f3744fd6a4066e5c8e32873130563`;
do not use that artifact. The corrected linker derives the full displacement
from the two native addresses, and a focused check independently binds the
assembled instructions to that value.

The corrected current cartridge boots and reaches native tests. The first run
against it, `build/smoke-v3-held-rig-actions-02/`, verifies the loaded module and
player code, enlarged allocation, original setup/return bridge, actual first-rig
initialization, and wind-driven speed/frame. It stops when the native skeleton
renderer writes its matrix-segment command through the fixture's uninitialized
translucent cursor. Disassembly at `80053124..80053138` proves that every call
writes that stream, including opaque rigs; the test configured only the opaque
cursor. The normal game supplies both streams. This specific fixture defect is
corrected by reserving and guarding the second stream; no game code changes.

The one justified setup retry, `build/smoke-v3-held-rig-actions-03/`, passes:
83 result records, 55 passing assertions, including 50 component assertions.
Results SHA-256:
`2256a200f5e0fca2ff5b2ac20a0f62a7a83c725b4e009ffbb935971053c0c613`.
It checks actual cartridge-loaded player code and the full resident module,
normal setup and return, then complete native skeleton initialization for
resource 50 (smallest) and resource 56 (largest). Both advance from speed zero/
frame one to speed `1.2000000477`/frame `2.2000000477` under controlled wind.
Each emits six opaque commands with its two actual joint display lists, plus
the native translucent segment binding. Both alternating matrix banks, first-draw
position initialization, rod-tip clearing, restored matrix stack/parent matrix,
graphics bounds, memory guards, unchanged saved state, restored checkpoint,
final fault/translation/equipment/save guards, and clean emulator exit pass.
Only an eight-byte test call bridge is uploaded; game code comes from the ROM.
The emulator is silent, uses disposable state, and writes no FlashRAM.

The setup retry is spent. No further replay is needed for this unchanged code.
Retain ABI-117's complete bank/DMA/cache evidence rather than rerunning it.

### Remaining work and compatibility

Complete the source loop-sound dependency and animated inventory previews, then
connect parent acquisition, catalogue, and individual selection through the
existing shared records. Those readiness flags stay false. This probe does not
enable a selected pinwheel, execute GPU rendering, test ordinary item/menu
gameplay, establish hardware appearance, or validate save/restart for pinwheels.

The 112 existing choices, format-2 save/profile, Museum-header correction,
complete artwork, and exact V2-12 import-free output remain unchanged. ABI-117
and ABI-118 same-profile saves are expected compatible both ways; no new ordinary
cross-version reload is claimed. Keep equal-or-superset imported profiles and
never load imported V3 saves in V2. Removing imports is not migration.
The independent seasonal-copy issue remains unresolved; the main ABI-109 lock
is not promoted. Both served V2 patchers and all existing ROMs/saves remain.

## Shared animated equipment banks

The shared runtime importer consumes the complete prepared rig category with
`--refresh-runtime --equipment-rigs`, adding all eight pinwheel models without
reconversion or per-item installers. All thirty existing model/animation records
are retained, yielding 38 equipment resources. The eight actual kind records gain
their shape/motion indices; actions, previews, and optional selections remain off.

The native maximum-size function only considered original models. Its real
callers register two 4,376-byte banks, aligned to 4,384 bytes. Both now receive
5,248 bytes. The scene allocator's request and end calculation both grow from
`93400` to `93AC0`, adding exactly 1,728 bytes, so the remaining object arena
does not shrink. Inventory already owns 15,584 bytes and does not grow. Native
DMA, double-bank ownership/indexing, and menu-return reload remain in place.
The equipment module remains 53,248 bytes; no persistent profile field changes.

Code inspection also identifies a real integration defect: the native loader
can change a model while retaining an equal animation index. Different-sized
models move or overwrite that cached animation. The checked model-DMA call at
`808B5A68` now uses a sixteen-byte assembly adapter to invalidate that bank's
animation index before native DMA. Native code then reloads and re-biases the
animation. It retains the original return path and all overlay relocations.

### Current proposal

- Explicit lock: `build/v3-equipment-rigs-02/build-lock.json`, ABI 117.
- ROM SHA-256:
  `ae0d3c4e9d717e42dc11e6c4b2e34c76adcd9620abe4590a0c03845f42d5b3ae`.
- UPS SHA-256:
  `370176d13295146e5141286508e343f7477e7620f92f2c4d4dfc57c1b30e7e40`.
- Build receipt SHA-256:
  `44199433db54eec5297fc1262c202377b2e7fd846f7277c767657bb60c176ecb`.
- Lock SHA-256:
  `18ab03166db743efc49c3c4c0ea72472212ee80d23579ab9a5c60bce921384c2`.
- Equipment module SHA-256:
  `33cc6e4aa0f71b3eda460dd3e1db09457196414ec2aadad9b72ffcca7a912960`.
- Shared reader/adapter code: 1,480 bytes, below the existing 2,816-byte limit.
- Complete models: 26,272 additional bytes; no reduced or omitted variants.

Both builds succeed on their first invocation. The first proposal,
`build/v3-equipment-rigs-01/`, lacks model-change cache invalidation; it is
preserved as test evidence, not the development continuation point. Its ROM
hash is `968f5df1d9f087b79f0df0794955c937069ae3adf539cd7d7b16441cad731a15`.

### Focused verification

Five host/current-cartridge checks pass on the final proposal in 7.481 seconds.
They cover sanitized original and expanded readers, eight complete prepared
rigs, all thirty original resources, actual default-motion/kind bindings,
allocation arithmetic, all rebound core/owner references, unrelated DMA resource
retention, unchanged module capacity/guards, original-ROM UPS reconstruction,
future tail reuse, the same 112 optional choices/profile, exact full output,
and exact corrected V2-12 import-free output. The same five checks also pass on
the first proposal; the final invocation is justified by the actual loader fix.

`build/smoke-v3-equipment-rigs-01/results.json` passes on its first attempt:
146 records and 120 assertions (117 component assertions). It executes ten
representative original/imported transfers, including the complete largest rig,
the actual native two-bank registration, both banks' sizes/pointers, complete
model-plus-motion transfers, invalid resource rejection, saved-state retention,
memory guards, checkpoint restoration, and a clean emulator exit. Results hash:
`4e4de15fcce2c6133f5c5659fd9e88620f12e4bf1af82f7b9a23c9fa253c9520`.
The final proposal retains those resources/allocation instructions. The changed
cache path has its separate current-build check rather than replaying this pass.

`build/smoke-v3-equipment-bank-switch-01/results.json` passes on its first attempt
against the current proposal: 85 records and 69 assertions (65 component
assertions). It verifies the complete actual game-loaded player owner and
equipment module, then calls native `Change_ItemBank` on an isolated actor.
Six alternating small/small/large/large/small/small loads preserve the shared
animation index while moving its actual data and segment pointers correctly.
Complete model/motion contents, both banks, surrounding guards, saved state,
restored checkpoint, final fault/translation/equipment guards, and clean exit
pass. Results hash:
`34845df0b59b277c1d3bce47e85a5dfd7d9100018bb3d0031915c0a423ab8b2d`.
No setup retry is used. Emulation is silent and uses disposable saves.

The final input guard permits at most six joints in the native seven-vector
work areas, reserving the root translation vector. All installed rigs have
three joints. This guard tightens source preflight only; it does not change
the compiled cartridge or the retained native test evidence.

### Remaining work and compatibility

Next connect complete native rig initialization/drawing and pinwheel behaviour
through the shared action/category machinery, then inventory previews,
acquisition, catalogue, and selected ownership. Do not reconvert these models or
write per-item installers. GPU appearance, ordinary equipping/menu-return,
the larger scene's gameplay/heap behaviour, and hardware remain unverified.
Component transfers do not establish playable pinwheels.

The 112 existing choices, format-2 save/profile, Museum-header correction, and
exact import-free V2-12 remain intact. Same-profile compatibility with ABI 116
is expected both ways, not a newly executed ordinary cross-build reload. Keep
matching/equal-or-larger imported profiles; do not load imported saves in V2
or treat removing imports as migration. No original ROM/save is modified.
The independent seasonal-copy failure stays unresolved, the main lock remains
ABI 109, and both served V2 patchers remain unchanged.

## Complete animated-held preparation

`tools/v3_furniture_pipeline.py convert --representation handheld --assets-only
--category animated-held-model` converts supported complete rigs as one category.
Source discovery, the existing material/geometry compiler, and the shared
keyframe module supply the implementation; there are no per-item installers or
model definitions. Default handheld conversion remains explicitly static.

`build/v3-handheld-animated-prepared-01/` contains all eight pinwheel parents
`224C..2253`, using source resource slots 33 through 40. Every object retains
three joints, two shown joint models, null roots, translations, children, draw
streams, and actual animation bindings. The joint table and skeleton header are
appended after complete artwork; only their pointers change. Shared graphics
remain separate joint lists, never one flattened model.

- Complete object bytes: 26,272; vertices: 560; triangles: 396.
- Six model objects: 2,736 bytes each; the two larger objects: 5,088 and 4,768.
- Maximum matching animation: 160 bytes per parent.
- Combined banks: six at 2,896 bytes, then 5,248 and 4,928 bytes. The two larger
  variants exceed the current 4,376-byte native equipment-bank contract.
- Art receipt SHA-256:
  `82a5b4e31ba342edb9e0670e3df29d348b3306be206969df0a86556162a8f143`.
- Inventory SHA-256:
  `3995f06a716e95620095576dc10385a231631488c7b1b01e2ce51b41f178f863`.

The source scan exposes 22 prepared roots: fourteen static and eight animated.
Net/rod roots retain their unsupported joint-matrix command; balloon roots retain
their unsupported texture format. The complete source motion descriptions and
animations are reused. The output has a separate
`AFV3-ANIMATED-HELD-PREPARED-1` format, rejected by both existing installers.
Neither an artwork-ready row nor these receipts enables an item/profile bit.

The actual Docker graphics build succeeds for all eight objects on its first
invocation. Seven new focused checks pass: complete source categories, every
joint field and pointer across all twenty described rigs, rejected stale or
unbounded bindings, category/selection rejection before output creation, every
converted pinwheel texel/vertex/triangle/material and rig, installer isolation,
and retention of all thirty installed model/animation resources on exact
ABI 116. Source-to-native animation sizes/bindings and object limits agree.
An existing default-static selection-rejection check also passes.

The first test invocation accidentally imports the reusable donor TestCase
class into the new module, so unittest discovers unrelated donor tests after
the seven intended checks. That process is stopped during the extra cases.
The helper import now references its module instead; collection alone verifies
exactly seven tests without executing the suite again.

The corrected explicit invocation runs nine checks in 4.460 seconds: eight pass,
and the older static-artwork snapshot comparison fails because it predates
source acquisition annotation. That field was already added before this batch;
it is not changed graphics. The comparison now checks all static-artwork fields
while excluding acquisition metadata on both sides. This final legacy-fixture
correction is **unexecuted**: the batch's setup retry is spent. Do not claim a
clean nine-test run or replay the archived batch. The new current-cartridge
resource-retention check passes independently. Syntax and diff checks pass.

No cartridge, runtime allocation, save/profile, main lock, or served patcher
changes. No emulator or hardware claim is made for these prepared rigs.
Next extend the shared model/animation allocation and resource readers, retain
both oversized variants, and connect actual skeleton initialization/drawing and
player behaviour before inventory, acquisition, catalogue, or optional selection
can enable these parents. Use the explicit ABI-116 lock for integration; keep
the independent seasonal-copy failure and ordinary acquisition test limits open.

## Ordinary festival acquisition setup

The current target is the ABI-116 two-parent subset at
`build/v3-festival-subset-01/animal-forest-v3-asset-loader.z64`, SHA-256
`b489decf5bb4500f9cc579aa0e0112475d89f5b15ce64d62ef81f4d35252d027`.
It selects `2255` and `225B` through the existing offline composer and the
explicit corrected-header lock. No new game code or item records are installed
by this batch; the main lock and both served patchers remain unchanged.

The shared copied-town fixture's `--event-shop` mode creates
`build/v3-festival-save-01/`, with 10,000 Bells, the source town's original
pockets/stock, and zero imported ownership. Its isolated clock starts at
2026-08-29 20:00, a festival Saturday. The fixture does not seed a fan or
pre-credit its catalogue entry. The independent reference writer encodes both
banks, and the actual C save codec verifies both complete ownership states.
Native payload comparisons permit only signature, checksum, and wallet changes.
The focused fixture test passes on the
ABI-116 build; Python syntax and diff checks pass. The source save remains
`d489736e39abc7eff1c5b5085bf52e679186f2882a0247339e11603799b80b60`;
the fixture save is
`ff7aa2b89733181c8d92f3993d3fa8af67d01cf583b7a92ded1ba7a58e0053c5`.

Normal boot and the player's original inventory/wallet pass in
`build/v3-festival-arrival-01/` (11 records, results SHA-256
`960c5e773026d5de1034408d4cbcba1e3fbe691367694444a238237879e6bee4`).
The pond scene loads vendor `D02C` at `(1420, 160, 2420)` and four original
festival visitors; the vendor's loaded-owner pointer is nonzero and the fault
pointer is zero. These are actual scene actors, not injected component calls.
The bridge/west-bank route uses only ordinary controller buttons, saves matching
emulator checkpoints, and never writes live position, time, schedules, or items.
The west-bank observation confirms ownership byte `8046C0DA` is still zero and
the resident guard is intact.

One navigation script requests a 140-frame hold, exceeding the existing
120-frame limit. It stops at that guard, not a game crash. Splitting that hold
into 120 and 20 frames is the single justified setup retry, recorded in
`build/v3-festival-crossing-02/`. Later route segments reach the actual stall.
The useful pre-interaction checkpoint is `build/v3-festival-near-stall-01/`,
SHA-256 `122573d1e3abbb734b3c3b525f49d8cf3743be3243882d6a5a9f9a194fa765c8`.
Its results contain 11 records, SHA-256
`3092f16a12b22dae15e168aed2a4d2c1bb0ca060c20dc0cd15559e1b433b89c9`.
The player is at `(1298, 160, 2523.1619)` and the vendor/scene render normally.

`build/v3-festival-purchase-01/` remains **incomplete**. The ordinary NPC
approacher stops after 15 observations at roughly `(1365.4568, 2470.9128)`,
74.6129 units from the vendor, with `navigation_stalled`. Twelve bounded A
presses then fail to open a choice: the message stays unloaded and the choice
state stays zero. Its 29-record results SHA-256 is
`a02654d2ec031f6d8df28e9399aa4f627748e135250cbff5a0c496da8c4b7b46`.
The route/item/payment assertions, final guards, handover capture, and final
checkpoint action are not reached. The copied `test.bs1` in that failed run
is its input checkpoint, not a newly saved post-purchase state.

This establishes arrival and scene loading, not a successful purchase or an
identified runtime purchase defect. Do not infer that the menu failed after
activation; activation itself is unobserved. The generic approach targets the
actor centre and does not account for the stall counter. A later meaningful
gameplay batch or human test must approach the actual interaction position and
verify the full transaction. The setup retry is spent; do not repeat this route
under another batch name. Continue shared import implementation, retaining
ordinary payment/handover/earned ownership and catalogue delivery as open.
The independent seasonal-copy assertion remains unresolved. Save format 2
requires the matching/equal-or-larger profile; do not load imported saves in V2.

## Ordinary equipment put-away, drop, and persistence

The target remains the ABI-115 subset at `build/v3-held-subset-01/`, ROM SHA-256
`ce436916f18097cb2ba0b8ae7617489521f563df4e5b79e85bbeda62befafe60`.
Its selected parents are `2255` and `225B`; this representative plays with
`2255`. No cartridge code, profile, artwork, allocations, or patchers change.
The completed preceding inventory/equip batch is committed as `042ae89`.

`build/v3-equipment-drop-pickup-01/` resumes the equipped checkpoint. Normal
inventory inputs remove the fan, restore it to pocket zero, then drop it
outdoors. Every other pocket is retained, equipment kind becomes `-1`, the
fault pointer stays zero, and the ground renderer displays the fan category
artwork. The drop stores the real parent `2255`, not its catalogue alias.

The initial immediate B press does not recover the item: native placement near
the house chooses a more distant free unit. The preserved dropped checkpoint,
SHA-256 `094fa8ca0bd96d8bfc51b4ba08cdf8fa1537f9bc4ef10787c7e2eb2987a37eb4`,
contains the player at `(2128, 1488)` and `2255` in acre `(3, 2)`, unit `(6, 6)`,
world `(2180, 1540)`, field address `8012E014`. Read-only checkpoint inspection
locates RDRAM from the resident guard/header and verifies the eight-MiB memory
size; the current state stores RDRAM at offset 37,972. An initial diagnostic
using an older state-layout offset is rejected and supplies no game-fault
evidence. The actual current checkpoint's fault pointer is zero, and its loaded
ordinary ground owner is at `80253960`.

The justified retry, `build/v3-equipment-recover-01/`, adds bounded ordinary
walking toward that verified point without position writes. It stops at its
24-step limit at `(2164.8132, 1526.1180)`, distance 20.5754, before sending B.
Pickup is therefore **unverified**, not a passed interaction or a demonstrated
game defect. The scenario's corrected 40-step/24-unit limit is unexecuted; the
setup retry is spent. Do not repeat the boot/equip/drop prefix or replay this
retry under another batch name. The retained dropped checkpoint remains the
useful state for a later meaningful gameplay batch or human verification.

Drop-run results SHA-256:
`6b014976043062b8dee418968ee82e33550a38693238fc94f456ed3ad045526e`.
Navigation-retry results SHA-256:
`e309cc554a4edfa24252a95f69b2e2aa122d352f41b58c499acb70d86eff543f`.

The separate persistence path resumes the already verified equipped checkpoint,
not the failed pickup branch. `build/v3-equipment-save-01/` uses normal walking,
gyroid dialogue, Save, house entry, and Save & Quit, and returns to the title
screen. It passes 18 result records, the fault/resident/save-state guards, and
graceful shutdown. Results SHA-256:
`1ddf92c098d294e0d3a1c85a307c6b0e7de3b686a3148bc5e313f7cb368fb4d2`.

The actual 128-KiB FlashRAM save SHA-256 is
`c0afba918a9d6800b1400f6ff3d36d100317425967d38a736c6c368662b652d0`.
Both 64-KiB banks have SHA-256
`df164fcfd1587121391d112c2706a9c3deecf644ea89919c283bd0805d1c630b`.
Each complete bank equals independent format-2 reference re-encoding, covering
the native checksum and payload/extension CRCs. Both contain equipped parent
`2255` at saved offset `40C`, the expected fifteen pockets, the exact selected
profile SHA-256 `ecd2ef57c7f485fbc0cb66d91f84d08a7f9458dd33431d2780a5357c40ed7dbb`,
and only the seeded imported collection bit 84. Ownership is retained, not
newly earned through ordinary reward acquisition.

`build/v3-equipment-reload-01/` starts a new emulator process with that actual
game save through `--seed-save`, without a save-state input. It passes 13 result
records: equipped parent `2255`, player equipment kind 108, all fifteen expected
pockets, collection byte `10` at `8046C0DA`, zero fault pointer, and complete
save-state/resident/equipment guards. The captured outdoor model is visible,
and the process exits gracefully. Results SHA-256:
`32ed5e4bdd3ebbb5d8b2f19cfc4c3ec7a4b151ba3cf8d8ad092c75495858b66c`.
The new equipped checkpoint SHA-256 is
`90eb8ac9f1ad0b3039ad37b41bce4c8ce46bb2d62aaaf3c4bc1265e0b7ea6046`.
This establishes ordinary save/quit/restart/load for this copied town and the
same two-parent profile, not cross-profile migration or every imported item.

Ten focused checks pass across navigation and read-only player/inventory tests.
They cover bounded arrival/stall/dialogue handling, rejected targets/limits,
direction-only input, complete equipment identity, pointer checks, and signed
empty equipment. Python syntax and diff checks pass. Every emulator run is
silent and isolated; no scenario edits live memory. The source save remains
`d489736e39abc7eff1c5b5085bf52e679186f2882a0247339e11603799b80b60`.

Actual reward acquisition, complete pickup, catalogue ordering/delivery,
additional categories/seasons, and original hardware remain open. This ordinary
ground result does not explain the separate cherry setter-copy assertion; keep
that issue unresolved and the main lock at ABI 109. Carry the Museum-header
fix through checked V3 integration before a handoff. Both V2 patchers stay
unchanged. Imported saves require the recorded selected profile; do not use
them in V2 or remove dependencies without a supported migration.

## Ordinary equipment gameplay

The target is the current ABI-115 two-parent subset,
`build/v3-held-subset-01/animal-forest-v3-asset-loader.z64`, SHA-256
`ce436916f18097cb2ba0b8ae7617489521f563df4e5b79e85bbeda62befafe60`.
This batch changes no cartridge code, artwork, profile, or served patcher. The
preceding shared selection batch is committed as `1972def` and pushed on the
experimental branch.

The existing copied-town fixture now accepts an equipment parent from installed
records, not a per-item fixture list. `--equipment-item 2255` generates
`build/v3-equipment-gameplay-seed-01/`, with save SHA-256
`a9e282e7b0301f29b305464aa37684c88a58c82c3f4feafe0ad7446089f11ad8`.
It changes only the first pocket/condition and checked format-2 profile/ownership
envelope in each bank. The source save SHA-256 remains
`d489736e39abc7eff1c5b5085bf52e679186f2882a0247339e11603799b80b60`.
The fixture rejects unavailable parents, changed bindings, and shop-stock use.
Neither a seeded item nor seeded ownership counts as ordinary acquisition.

Five focused checks pass: the new equipment-fixture check covers two non-prefix
parents, both complete save banks, unchanged unrelated saved fields, native
checksums, and actual codec acceptance with only the intended ownership bit;
three read-only player-observation checks cover action/equipment and signed
empty equipment; the existing clothing-stock fixture check passes against the
current full ABI-115 cartridge. No historical ROM is executed. The fixture
test passes in 0.580 seconds, and the other four in 0.178 seconds.

The initial ordinary-controller run, `build/v3-equipment-gameplay-01/`, cold
loads the copied subset town, retains every expected pocket, opens inventory,
and displays `plum fan` with its imported icon and native Grab/Drop/Quit menu.
Its sequence then incorrectly expects Grab alone to equip the fan. Grab puts
the item in the inventory hand; it must be moved onto the miniature player and
confirmed. That assertion fails with equipment kind `-1`. The menu checkpoint
is retained before the failed interaction, so the successful boot is not rerun.
Initial results SHA-256:
`0a7b4227c20a893b14e90f4b5a6d3a720a5ddd7b7086f9c1ac4abe6bdd322a0a`.

The justified corrected run, `build/v3-equipment-gameplay-02/`, resumes that
matching-ROM checkpoint and performs Grab, up, confirm, and close through normal
buttons. It passes 14 result records and exits gracefully. Both player samples
report equipment kind 108; the first pocket is empty and the remaining fourteen
pockets and clothing are unchanged. Captures show the actual plum fan on the
inventory player and outdoor player, including a held-A pose. After release,
the player returns to native idle action 7 without losing the equipped item.
The fault pointer is zero, and the resident/equipment reservation guards remain
intact. No debugger call or live-memory write is used by these scenarios.

Successful results SHA-256:
`1a8d8cf02dba82a7d056847620741f4d4d0b7757506e3709e6c754d89e615dd0`.
Equipped checkpoint SHA-256:
`690802f049b7fcb6b88f6130bb8ba4fc3ea4a4fef079437eabe40b4102eec00f`.
The runs use disabled audio, an isolated X display, copied saves, and an
Expansion Pak. The checkpoint is not ordinary game-save/restart evidence, and
the held-A screenshot is not a complete trace of every animation frame. No
hardware, ordinary purchase/reward, putting-away/drop/pickup, or catalogue
delivery claim follows. The setup retry for this batch is spent; retain the
successful checkpoint and continue the next interactions without replaying boot.

The separate seasonal-copy assertion is still unresolved. Static disassembly
of the current ABI-115 owners confirms the 264-byte frame, 108-entry ordinary
copy, 107-entry winter copy with its three-entry prefix, caller-argument offsets,
and return instructions. This inspection alone does not explain the prior
native stop or prove the whole ground path safe; no further old probe is run.
The main lock remains ABI 109. Carry the Museum-header fix through checked V3
integration before a handoff. Both V2 patchers and all original saves remain
unchanged; imported saves still require their selected profile and are not for V2.

## Shared held-parent selections

The proposed ABI 115 is `build/v3-held-selection-02/`, produced by the existing
runtime refresh with `--held-selection` and the ABI-114 proposal lock. The
initial requested output name already belonged to an earlier preserved selector
build; the fresh `02` directory avoids overwriting it. ROM SHA-256:
`6d34371f15cd05eaca304faa051941e99c5a78b2531f7aab4cf85eec2181b4d2`.
Report SHA-256:
`f0e7bb7358afd747f1cb55b7a662297c42682384856e1e492758d1879b8af416`.
UPS SHA-256:
`5881c5835805739a6fcab77c0010aafc47ad991b040df2f6328123b589ab1e22`.

The shared stage verifies complete installed adapters, model/profile/inverse
records, parent correspondence, and unoccupied canonical bits, then enables
the eight parent bits in a full experimental reference. Other than the ABI,
profile, and startup checksum/ABI configuration, every cartridge resource is
unchanged. There is no new gameplay code, artwork conversion, saved format, or
allocation. The known seasonal-copy issue still prevents promotion/handoff.

Offline and browser composition derive Equipment choices from these same
records. The 112 choices are twenty villagers, 81 furnishings, three shirts,
and eight equipment parents. Displays are not independently selectable. Each
parent owns its representation's enable field and single canonical saved bit.
Selected umbrella entries pack after all 32 original rows, with unused suffix
slots cleared and the native iteration/completion count updated. Names, IDs,
models, and selection ordering remain stable. Both CLIs and the isolated browser
check accept an explicit checked `--base-lock`; the main lock is unchanged.
The private UI adds an Equipment filter and keeps all choices off by default.
Completed representations leave the unavailable-furniture queue in favour of
their actual parent choice. Neither served V2 patcher changes.

Nineteen focused checks pass across the initial combined invocation and the
corrected codec test. The initial combined run had eighteen passes and a fixture
argument error: it called the existing two-argument reference encoder with three
arguments. The corrected check passes, and all three dedicated selection tests
subsequently pass in 6.607 seconds. Checks cover actual installed identities,
non-prefix subsets, count packing, request order/duplicates, rejected display
choices, exact all/empty output, dependencies, changed-source/overlap rejection,
unchanged complete resources, guarded activation, UPS reconstruction, and the
actual format-2 codec's four-player ownership retention and missing-bit rejection
without destination writes. Nine JavaScript unit tests pass. The existing
browser/offline comparison matches complete ROMs for fourteen representative
profiles, including all equipment, sparse equipment, and equipment with a house.

The real CLI builds `build/v3-held-subset-01/` with parents `2255` and `225B`.
ROM SHA-256:
`ce436916f18097cb2ba0b8ae7617489521f563df4e5b79e85bbeda62befafe60`.
The unserved export `build/v3-held-selection-browser-01/` contains the 112-option
plan and both two-game reconstruction recipes. Export receipt SHA-256:
`82866c8ac0144d3131858363f58978d229503406365ec76951f7ad32776aabc8`.
No ongoing server or V3 patcher service is installed.

The first silent Chromium interface attempt stops on a stale fixture assumption
that Lady Liberty belongs in the unavailable list; it is already an installed
import. The justified retry selects a real current review entry instead. It
passes Equipment select/clear, dependencies, cancellation/late-result rejection,
and three actual ROM/profile downloads in
`build/check-v3-held-selection-browser-02/`:

- Equipment subset: `ce436916f18097cb2ba0b8ae7617489521f563df4e5b79e85bbeda62befafe60`.
- Villager/seasonal subset: `21082037bc1d8ff6b2a0018fdfb758121fc5f499c308b12df88988b7277fd519`.
- No imports: exact V2-11 `8bbd1955536a2a3ac9f76d6f323842f5ce25c037e1ff5fd3da9f28d6dfe20507`.

The equipment profile requests exactly `GAFE01-r0/item/2255` and
`GAFE01-r0/item/225B`, with no extra dependencies. Its downloaded JSON SHA-256 is
`8c19e4c182ef26d6cf85b68108567e33b4fb6af197f88c8a8fc5735cb1f6bc03`.
Each downloaded ROM matches the offline output and the worker's reported hash.

The retry then stops at file-change invalidation after re-selecting the identical
disc file. This does not demonstrate that the native input value changed. The
fixture now clears and restores the field to exercise an actual change, but it
has not been rerun: the setup retry is spent. Full file-change invalidation,
later lifecycle checks, final request/error assertions, and complete UI-pass
status remain unverified. No passing final `results.json` is claimed. The server
uses its existing `finally` shutdown path. Do not replay the successful downloads
as another setup attempt. Python syntax and diff checks pass.

The previous catalogue native result applies to unchanged catalogue/equipment
code; no unchanged emulator batch is replayed. Ordinary acquisition, equipped
use/put-away, ground drawing, order payment/delivery, save/restart, and hardware
remain required gameplay evidence. Codec tests accept equal/larger selections
and reject missing bits, but no ordinary cross-profile reload is claimed. Fan
profiles are not backward-compatible with older profiles lacking those bits;
retain separate test saves and never use imported V3 saves with V2. The main
lock remains ABI 109. Next classify the existing seasonal-copy failure and
exercise the current selected build's ordinary gameplay, retaining the separate
Museum-header integration before handoff.

## Shared held-parent catalogue

The proposed ABI 114 is `build/v3-held-catalogue-02/`, built with the shared
runtime refresh's `--held-catalogue-art` option from
`build/v3-held-collection-02/build-lock.json`. The prepared directory is
`build/v3-furniture-indexed-sequence-prepared-01/`; no artwork is reconverted.
ROM SHA-256:
`423404df91fa84dd2faef1a4d7ca8dc5367a112885c88acf8f307ae9223bdf3b`.
Build report SHA-256:
`66081a151bd5046b335a34f4ff37f179f07a10f37b86fe413d59abe55dcf253b`.
UPS SHA-256:
`ab709aa4f0f7d748d0f89f38d7097681a327300a08c9202876ea11c50b4e3159`.

One category adapter installs all eight complete fan catalogue models from the
existing parent/collection records. They occupy 11,136 ROM bytes and canonical
sparse profiles; tag one makes each profile conditional on the selected parent.
Inverse metadata resolves the English name, price, collection, and order pickup
to that parent. No forward room alias is added. The umbrella descriptor points
to all 32 native entries followed by eight imported entries in donor order.
Furniture and clothing lists remain unchanged. Subsequent common catalogue
rebuilds retain the new category table and its actual relocation.

The native initializer performs ordinary construction, model DMA, lighting, and
timer setup, then the checked donor branch supplies scale 1, model Y 0, viewing
height 36, and the parent price. The catalogue is 62,912 bytes with 736 bytes of
relocation; its conservative requirement is 280,512 of the existing 280,704-byte
pool. The expanded furniture reader occupies 1,960 of its 2,048-byte reservation.
No resident/model allocation or saved format grows. The original 52-KiB equipment
module, all profile bits, and 104 existing experimental choices remain unchanged.

Build one stopped because the bank-owner receipt predates later shared placement
patches. The actual bank call matched. Build two binds the complete current
placement-owner/relocation hashes, checks the exact bank instructions, updates
that one call to the new helper, and carries current owner hashes forward.
No hash or instruction safeguard is removed.

Four focused checks pass in 5.053 seconds. AddressSanitizer/UBSan exercise shared
profile gating, all eight representations and rotations, collected/disabled cases,
full preview-field retention, framing/prices, native fallbacks, and rejected
indices. Cartridge checks compare every complete prepared model, sparse profile,
inverse alias, native/category order, three relocation destinations, unchanged
unrelated resources, exact room-call change, equipment retention, current source
receipts, pool bounds, and UPS reconstruction. Python syntax/diff checks pass.
Twelve optional-composition checks pass in 8.907 seconds against this proposal
without changing the main lock; empty selections still reproduce V2-11 exactly.

The first silent native run, `build/smoke-v3-held-catalogue-01/results.json`,
passes 104 records and 70 assertions. Results SHA-256:
`fb738a4a527a0659bd43806f189929b0fe0144cc7fa15d1ea9c9846833312257`.
The shared catalogue fixture loads/relocates the actual complete owner, collects
all eight parent items, constructs their real category list, and selects the
first and last entries through native scrolling/selection. Complete model DMA,
untouched bank tails, full English names, parent prices, source framing, disabled
owned-item filtering, all original umbrella rows, original preview fallback,
allocation/stack/runtime guards, restored globals, checkpoint reload, no CPU
fault, and graceful exit pass. All eight ordinary forward drops retain parent
IDs, while their rotated display inverses return the correct parent. No user
save or audible playback is used, and no test FlashRAM write is requested.

This does not establish GPU appearance, ordinary catalogue payment/delivery,
full equipped gameplay, a save/restart cycle, or original-hardware compatibility.
Same-profile compatibility with ABI 113 is expected in both directions without
migration, not newly demonstrated by cross-build reload. Imported V3 saves remain
unsuitable for V2. Optional parent choices and selected-category count packing
are next; no fan choice is exposed yet. The main lock remains ABI 109 because
the inherited seasonal-copy continuation/stack issue is unresolved. Neither V2
patcher changes. Carry the separate Museum-header correction before handoff.

## Shared held-parent collection

The proposed ABI 113 is `build/v3-held-collection-02/`, built explicitly from
`build/v3-event-menu-06/build-lock.json` with the shared runtime refresh's
`--held-collection` option. ROM SHA-256:
`95abb54f9c1d5ab77931d2f8d1f14dde2c170d8938286a1679a3e1e69986322b`.
Build report SHA-256:
`6c1e20eff8b998aaf622e55dc744290f897e5916903aa9223b0fa633d4b6d010`.
UPS SHA-256:
`f45dbb290919eca76a506084a733b29f74c828436371d289fd9204c5bc17f669`.

One 488-byte adapter connects every installed parent record to native collection
and the existing imported ownership query. Parent IDs and rotated display IDs
share the actual canonical bit, with exact resident-slot lookup, selected-item
checks, existing save guards, and retained native/clothing fallbacks. The
identity helper uses the existing parent reader's checked metadata/selection.
Its original 1,284 bytes remain unchanged; the extended reader totals 1,716
bytes. Both helpers fit the existing 52-KiB reservation. No artwork, original
acquisition function, room conversion, profile bit, or saved format changes.

The source audit corrects an incomplete interpretation of the donor catalogue:
fans do not occur in its furniture list, but all eight occur at umbrella-list
positions 32–39. The complete 64-entry umbrella list also includes pinwheels
and balloons. Source receipts bind all nine category lists, pointer/count
relationships, and the actual collection/room context functions. Parent records
retain their real catalogue category and position for the next shared adapter.
No catalogue entry or preview is installed by this collection-only batch.

Four focused tests pass across the initial run and one corrected JSON tuple/key
comparison. Actual C selection, collection, and save-codec implementations run
under AddressSanitizer/UBSan: all eight parents, all four resident slots, rotations,
idempotence, disabled/malformed inputs, invalid private pointers, player clearing,
native/clothing fallback, format-2 pack/readback, and missing-profile rejection
without destination writes. Cartridge checks cover complete unchanged resources,
all previous held instructions, new compiled code, source bindings, complete
startup CRCs, unchanged profile bytes, and UPS reconstruction. The first build
stopped at a missing compiler-part registration; the second builds successfully.
Python syntax and diff checks pass.

Twelve optional-composition tests pass in 8.698 seconds against this proposal,
without changing the main lock. Empty selection retains exact V2-11; all current
selections reconstruct ABI 113. Current sparse profiles and actual codec
compatibility checks remain intact. No handheld selection is added yet.

The first silent native attempt verifies startup but rejects the fixture's
direct Expansion RAM code proof before executing the reset function. The
existing debugger deliberately limits that API to lower RAM. The justified
retry reuses the menu fixture's allocated, checked lower-RAM jump bridge;
no cartridge change or debugger restriction change is needed.
`build/smoke-v3-held-collection-02/results.json` passes 138 records and 58
assertions, SHA-256
`91ab4410d092e38b5a973fbe50dcd27e561389127648a3483897a4638af24a45`.
It executes actual native pocket insertion for all four resident slots, verifies
separate imported ownership and untouched original furniture bits, rotated
queries and repeated collection, wrapped-condition exclusion, disabled-parent
rejection, invalid-private queries, save/equipment/stack/bridge guards, restored
globals, complete checkpoint reload, and no CPU fault. The emulator exits
successfully. No user save or audible playback is used; no test FlashRAM write
is requested. This batch's native setup retry is spent; retain this passing run.

These are component calls with isolated resident records, not ordinary vendor
conversation, visible catalogue construction, equip/put-away, played save/reload,
or original-hardware evidence. Same-profile compatibility with ABI 112 is
expected in both directions without migration, not established by another
ordinary cross-build reload. Imported V3 saves remain unsuitable for V2.
The inherited seasonal-copy continuation/stack issue remains unresolved; the
main lock stays ABI 109, and both served V2 patchers remain unchanged.

Next install the prepared display models and umbrella-category catalogue readers
from these source-derived records, then optional composition and ordinary
gameplay. Use this proposal lock explicitly. Do not create per-item installers,
reconvert unchanged artwork, or confuse a catalogue representation with an
ordinary room-drop conversion. Carry the separate V2 Museum-header correction
into V3 before its next private handoff.

## Shared event menu and transactions

The proposed ABI 112 is `build/v3-event-menu-06/`, built explicitly from
`build/v3-event-stock-01/build-lock.json`. ROM SHA-256:
`df4113112c3f9838ebbe62438fd337a39256374e143bf5eb6db7554870eccaed`.
Report SHA-256:
`fd3baac1d6de93fb7e7a8c77de27e38d34f49beef74b8e6226d422eeec7bc2e6`.
UPS SHA-256:
`77eca9170865cc3aea36f11cd0557c0fa263e4f0719af4ca95dfaebe8760dcd5`.
The main lock remains ABI 109; this batch does not resolve the inherited
seasonal setter-copy failure or establish a playable handheld handoff.

The existing shared acquisition adapter adds the original/imported stock-route
menu, three-item English pages, native pocket capacity and funds checks,
actual pocket insertion/payment, one-slot consumption, and handover requests.
Every original vendor callback remains available. Native category two keeps
unlimited fruit, while every imported category consumes finite stock. Empty
selections bypass the route selector; sold-out imports do not close the
original stall or refill on re-entry. No item-specific importer is added.

Compiled menu code/labels occupy 2,385 bytes. The equipment reservation becomes
52 KiB with full startup checking and all previous bytes retained. The vendor
gains four transient bytes, from `954` to `958` hexadecimal; saved event data,
profile IDs, and all 104 existing experimental choices remain unchanged.
The request callback and action-setup hook remove exactly four obsolete
relocations. Original owner code, merchandise, prices, and callbacks otherwise
remain intact, apart from the original introduction IDs and actor size.

The original Japanese introductions describe music/gyroids/fruit at
980/1,000/1,280 Bells. The supplied legacy English and official GameCube
introductions describe different goods. Four appended messages retain the
GameCube greeting/question/control structure while adapting the original
merchandise/price pages and adding a source-derived route question. The old
introductions remain for matching imports. Six entries in the one provenance
catalogue credit those messages and both new route labels; authored fragments
are explicit, and human review remains pending. All 12,007 prior messages and
both choice resources are retained. Four existing physical text files move
within their checked region; message/table growth totals 1,040 bytes, without
duplicating the text bank in import storage. Maximum new expanded text is
367 bytes within the existing 1,024-byte buffer.

### Verification

The four focused tests in `tests/test_v3_event_menu.py` pass across the combined
run and one corrected cartridge assertion. Host ASan/UBSan execution links the
actual stock module with the new menu, covering all three category prices,
sparse pages, original delegation, no-selection handling, failed transactions,
single-order purchases, finite balloon stock, handover state, and sold-out
retention. Cartridge checks cover all retained owner bytes, two relocation
bases, allocation/bounds, complete module/startup resources, unchanged profiles,
every old message, new control structure/provenance, unrelated DMA resources,
N64 checksum, and exact UPS reconstruction. Python syntax and diff checks pass.
The initial relocation assertion incorrectly treated the resident no-op action
as owner-relative; the corrected check preserves that resident pointer.

Twelve optional-composition tests pass in 8.721 seconds against this proposal,
without editing the main lock. Actual save-codec profiles, sparse dependencies,
all-selection output, and exact import-free V2 output remain intact.

The first silent native run reaches both routes and imported selection, then
fails its comparison of unused choice-row padding. The native length helper
trims spaces and the row copier retains unused tail bytes. The fixture is
corrected to compare the full visible name and actual length instead; no
cartridge change is needed. The justified retry is
`build/smoke-v3-event-menu-02/results.json`, SHA-256
`4339656f0d8eb763242b75b155f3ece998701fedea10e23c64fb12a9a4263c89`.
It passes all 178 records and 73 assertions, including complete startup/owner
loading, original/imported routes, names/prices, full-pocket and insufficient-
funds rejection, two actual native pocket insertions and payments, repeat-order
rejection, consumed stock slots, handover requests, sold-out state, preserved
original wares, scratch/stack guards, restored globals, full checkpoint reload,
no-fault status, and the resident guard. The emulator exits successfully. No
user save or audible playback is used.

These are direct component calls against isolated event/pocket data, not an
ordinary conversation or played handover animation. The native collection route
does not yet credit imported fan ownership. Do not infer working catalogue
collection, outdoor/room appearance, equip/put-away, save/restart, or hardware
verification. The new-harness setup retry is spent; retain the passing result
instead of replaying it without a relevant implementation change.

### Next work and compatibility

Continue context-correct parent collection/catalogue, using prepared display
models and the existing selected-parent records. Ordinary fan room drops must
retain the parent ID; collection uses its furniture representation. Integrate
optional selection afterwards, and keep unsupported rigs/actions disabled.
Resolve the inherited ground-copy check before promotion or handoff. Carry the
separate V2 Museum header correction into V3 before its next handoff.

Saved format 2 does not change. The appended route field is transient and no
handheld profile bit is enabled. Imports retain their incompatible-with-V2 save
warning; unchanged layouts are not a new save/reload test. Existing ROMs/saves,
the main lock, and both served V2 patchers remain unchanged.

## Shared event stock

The proposed ABI 111 is `build/v3-event-stock-01/`, built explicitly from the
ground-enabled ABI 110 proposal. ROM SHA-256:
`373602d0fa380440d1a2766dd06a011d826c54ca5e9cb562871fba13512da48b`.
Report SHA-256:
`be5c6116624af2df62176508a41d924a7aae05697010845c15c20ca0d08bfbd8`.
UPS SHA-256:
`a04b2ba8c8f8287a0b99c89e9e2877d1a961176b6bd8b4976890add0cb53d631`.
The main lock remains ABI 109. This stock check does not resolve the inherited
seasonal setter-copy failure, and the proposal is not a playtest handoff.

Six complete donor functions and their relocation dependencies provide the
stock/price/message semantics. The source records cover all eight fans,
pinwheels, and balloons, using their actual vendor prices (780/680/480 Bells).
The shared handheld scan annotates these 24 existing identities and still
reports 79 equipment identities/states, fourteen prepared static model roots,
and no newly usable imports. The generated inventory is
`build/v3-event-stock-01/held-inventory.json`.

The compiled shared helper uses 1,680 bytes plus 24 bytes of category records.
The equipment reservation grows to 48 KiB; startup remains inside its existing
bound. The native vendor owner stays 4,720 bytes with its English sixteen-byte
choices intact. Only its constructor's save-initialisation call changes; one
local JAL relocation is removed. All existing owner fields, code, stock, and
allocation metadata remain. The wrapper resolves the live owner before calling
the original save initializer and actual native event getter.

The native event record has a forty-byte payload. Added stock uses its trailing
twenty bytes, not a second event slot or replacement of original goods. Selected
variants retain their slots, empty categories are excluded, and the initialized
count marker prevents sold-out stock from refilling. Unselected imports cause
no tail writes or RNG use. Shared bounded count/index/quote/commit functions
provide the menu contract. They do not grant items or charge money.

### Verification

`python3 -m unittest tests.test_v3_event_acquisition -v` passes six checks in
6.103 seconds. Sanitized host execution covers all three source categories,
sparse pages, prices, complete depletion, repeated initialization, invalid/null
arguments, malformed state/configuration, invalid RNG values, readiness changes,
stale quotes, and protected original event data. Cartridge checks cover the
entire retained owner, two relocation locations, allocation/lookup contracts,
all source mutations, complete module transfer/checksum, unchanged resources,
and exact UPS reconstruction. Python syntax and `git diff --check` pass.

Twelve optional-composition tests pass in 9.229 seconds against the explicitly
pinned proposal, without editing the main lock. They include the actual save
codec, sparse/dependency profiles, all 104 experimental choices, and exact
no-import V2 output. Existing choices and profile bits do not change.

The first silent native run, `build/smoke-v3-event-stock-01/results.json`, passes
68 records with 29 assertions. Results SHA-256:
`a5f4b66c5d24ac5233e6ebeb866fc531d0cc4433496125da76921be76fdaa9d5`.
It checks the complete 48-KiB startup module and relocated vendor, executes the
real original initializer/getter with an isolated existing event record, and
verifies both disabled and sparse-selected stock. Native count, page-index,
quote, consumption, repeated-sale rejection, reinitialisation without restock,
and complete sell-out pass. All scratch guards, original event/profile/owner
restoration, checkpoint reload, no-fault status, and resident guard pass. The
emulator shuts down gracefully. No user save or audible playback is used.

This is component execution, not ordinary vendor interaction, a purchase into
the player's actual pocket, an event rollover, disk save/reload, GPU appearance,
or original-hardware evidence. The constructor wrapper is invoked directly;
cartridge/relocation checks establish its call binding, not a full NPC spawn.

### Remaining integration and compatibility

Connect an explicit imported-wares menu while preserving original merchandise,
source-correct introductions, the native pocket/payment checks, and handover.
Keep source category two separate from the native unlimited-fruit branch.
Source and native introduction IDs overlap despite differing merchandise;
review actual identities and record any text adaptation in the one provenance
catalogue. Do not count the stock helper as completed acquisition or enable
unfinished balloons/pinwheels merely because their stock records exist.

Saved format 2 and all profile identities remain unchanged. The unused event
tail gains stock semantics when imports are selected; its initialized marker
survives owner reload, but ordinary save/restart persistence is not yet tested.
No handheld profile bits are enabled in the emitted cartridge. Import-enabled
V3 saves remain unsuitable for V2. Both served patchers are unchanged. Carry
the separate museum-header fix into V3 before its next handoff.

## Shared seasonal ground runtime

The proposed ABI 110 is `build/v3-ground-categories-02/`. Its ROM SHA-256 is
`6a74b1d25eebb647674cf016305051fe0608d47cd0daae911ac197677fc1cc51`,
report SHA-256 is
`9716d233fb4bd829b186dc748a3b48d279987b7d3fdaf830c69adbf55d627e2b`,
and UPS SHA-256 is
`591eb69b927d6164252c9c49a63ac664ee1360261a6698c03cc1082ecad6e1c1`.
The main build lock stays at ABI 109; this proposal is not a validated handoff.

The shared installer integrates all four seasonal ground owners together,
without another artwork conversion or per-item script. Each receives its full
expanded table, nine complete native descriptors, relocated callbacks,
constructor entry, actor-tail index arrays, and matching setter capacity.
The native global category entry resolves installed, selected parents and
delegates other items directly to the existing translated wrapper, avoiding
recursion. All twelve furniture-type windows now resolve the correct seasonal
loaded owner. Saved format 2, all 104 experimental choices, parent profile bits,
ordinary banks, and both served V2 patchers stay unchanged.

The module is 44 KiB with 1,612 bytes of new code and 144 bytes of configuration;
startup remains 952 bytes. Cherry/ordinary/Christmas gain 1,376 bytes of overlay
BSS and 864 bytes of actor indices; winter gains 1,360 and 856 bytes respectively.
Existing common state, matrix nodes, and Christmas light records do not move.
All four setter frames are 264 bytes. Expanded categories number 108, or 107 in
winter. Source numbering and physical artwork pointers are unchanged.

### Defect found and corrected

The initial proposal `build/v3-ground-categories-01/` faulted before the native
probe reached its game-frame breakpoint. The saved checkpoint independently
showed faulted thread `80145630`, PC `80262D84`, and bad address `00000004`.
The live cherry owner was at `8025BCE0`; its native draw-body instruction at
offset `70A4` dereferenced a null part. The native classification had populated
start index 64 with 118. That is the original `NONE` sentinel, previously outside
the copied/drawn range but now inside the extended arrays.

The correction gives every unused extended slot a real 32-byte no-draw
descriptor. It preserves original sentinel values and comparisons, with zero
ordinary/shadow lists rather than borrowed artwork. Host tests check every
unused row and descriptor. Both subsequent corrected-build runs report no
faulted thread and reach the normal game-frame context. Do not use the first
proposal; it is retained only as local failure evidence.

### Verification and exact remaining check

Six focused tests pass in 5.150 seconds: sanitized complete table construction
and reloaded-owner pointers, category bounds/selection, every native edit,
two relocation locations, all allocation/stack contracts, source mutations,
retained artwork/resources, startup bounds, cartridge checksums, and full UPS
reconstruction. Twelve optional-composition tests pass in 10.601 seconds against
the proposed lock, including the exact no-import V2 output and actual save codec.
The first proposal's earlier passing checks are not evidence for its startup bug.

`build/smoke-v3-ground-categories-02/` verified corrected startup and the entire
44-KiB module, then could not allocate the probe's 212,992-byte scratch block.
This was a test-fixture allocation, not a production allocation failure. The
justified setup retry uses 53,248 bytes of native heap for executable owner data,
plus a checked, saved/restored unowned Expansion Pak gap for fixture data.

`build/smoke-v3-ground-categories-03/results.json` contains 31 records,
16 passing assertions, and one failing assertion. Its SHA-256 is
`ccf951700e8cfc1d3102c1a9cf848e72ef0bc94c525c8c26e67fffeaa914b87f`.
It executes selected/disabled/original categories, loads and relocates the full
cherry owner, builds and compares every original/imported table row and part,
executes the four constructor pointer/count writes, and clears the entire
expanded setter array. The matrix-sentinel comparison also succeeds before
the stopping point. It then fails the setter-copy continuation/stack assertion
at loaded entry `802E3598` (owner offset `5E78`).

That record does not include the observed PC/SP, so the cause is unresolved,
not established as a fixture error. The probe now records PC, SP, stop reply,
and expected values on this failure, but that addition has not been rerun.
The native setup retry and 30-minute harness allowance are spent. Do not repeat
the complete prefix or claim that copy/drawing passes. The other seasonal
execution, complete copy, native graphics lists, final guards, verified scratch
restoration, and checkpoint restoration remain unverified. No user save or
hardware audio was used. Keep the potential copy/memory defect open and the
proposal unpromoted while continuing unrelated shared acquisition work.

Saved formats are unchanged from ABI 109; same-profile compatibility is expected
but has no new ordinary save/reload evidence. Import-enabled saves remain
unsuitable for V2. Carry the separate V2 museum-header fix into V3 before its
next handoff, and preserve both V2 patchers.

## Shared police and handover runtime

ABI 109 at `build/v3-category-runtime-03/` installs all nine complete category
objects through the shared importer. Two 71-entry material/geometry tables keep
all 27 original categories, with imported indices derived as `27 + source type`.
The selected-parent reader keeps disabled/missing extended IDs out of the native
36-entry tool table. Police and handover use the new reader and shared tables;
all four seasonal ground consumers remain required work before enabling imports.

The 40-KiB equipment module grows by 12 KiB, with the previous prefix intact.
Police actors grow by 88 bytes; stack capacity, all 70 start indices, 257 matrix
nodes, trailing item-table offsets, actor allocation, and drawing bounds agree.
The handover actor stays unchanged. Every resource sample, vertex, and command
is retained except the three checked physical-resource pointer relocations per
object. Native material/matrix/geometry ordering remains intact.

- ROM SHA-256: `a55c7ebf3d4c59e0987892536e1ba3565b6a50c73c6aecf743b602015b6e0ca0`.
- UPS SHA-256: `3f5bf4eb38e2aedb87780ec641350ae81a1822e2cf674b6a9cddecc16b0aa1cb`.
- Five focused host/cartridge checks pass in 5.510 seconds: sanitizer-backed
  selected/disabled/malformed category lookup, complete artwork retention,
  fixed source numbering, original table preservation, complete owner changes,
  relocation at two heap locations, allocation bounds, UPS reconstruction,
  checksum/startup, unchanged prior equipment, unrelated resources, and profiles.
- Twelve optional-composition checks pass in 8.940 seconds against this exact
  proposed build lock: import-free V2, select-all, dependencies, sparse choices,
  deterministic output, and the real profile/save codec remain intact.
- Native `build/smoke-v3-item-categories-01/results.json` passes on its first
  invocation: 63 records, 44 passing assertions, no failures. Results SHA-256:
  `3708ae8b02336f0d3a72fb9ed71657a497f7307ee17601e21371b91522efcb5a`.

The silent native run checks the complete startup-loaded module, selected and
disabled categories, original fallback, both actual relocated owners, all 70
police start indices and 257 matrix sentinels, rejection of invalid indices,
original and imported material/geometry dispatch through the real drawing loop,
two handover assignment windows and three table-lookup windows. Memory guards,
profile restoration, full checkpoint restoration, and graceful shutdown pass.
The FlashRAM remains erased and no user save is used. The fixture deliberately
uses an empty field for police classification: terrain queries and full item
acquisition are not claimed. It supplies representative linked matrix records
for drawing, not an ordinary lost-and-found playthrough or GPU image comparison.

Build attempts `-01` and `-02` stop before producing a ROM: the first catches a
transfer-width/texture-format distinction while rebasing CI4 pointers, and the
second catches a duplicated Python receipt keyword. The corrected `-03` build
and focused checks use the actual complete assets and consumer paths.

Saved formats, saved identities, all 104 experimental choices, and both served
V2 patchers remain unchanged. V3 cross-version/profile save compatibility and
original-hardware behaviour are not established by these component tests.
Next integrate all four seasonal ground category tables/arrays and the global
type route, using these installed objects. Then finish acquisition,
collection/catalogue, selection, and ordinary gameplay/persistence. Carry the
V2 Museum header correction into V3 before its next private handoff.

## Shared ground and handover artwork

The `item-category-art` category prepares all nine complete ground/police/
handover representations used by the donor's 43 extra handheld parent/state
records. Source category tables select the artwork; no per-item model list or
new native scenario is introduced. Worn axes remain states, and shared resources
do not create multiple logical imports. Source categories are `19`, `33`,
`37..43`; the receipt records every parent identity and official name locator.

Each complete object contains a 32-byte palette, a 512-byte 32×32 CI4 texture,
four vertices, and separately callable material/geometry lists. Nine objects
occupy 7,344 bytes with 9,216 texels, 144 palette entries, 36 vertices, and
18 triangles. Discovery verifies both complete handover/police table pairs,
all four ground descriptor chains, and twelve complete consumer functions.
It retains the source variant-specific ground bases `68/68/68/70` rather than
assuming every seasonal table is identical.

Artifacts:

- Prepared build: `build/v3-item-category-art-02/`.
- Art receipt SHA-256: `ad60ba447b1ab62f7d996bbae8610b874aad56a95cf34f4e473c72563f4bc21e`.
- Inventory receipt SHA-256: `1abc0d0486e63c416dc7c43465bb849a186adcbec4bbf98d988bbaf3d8661284`.
- Format: `AFV3-ITEM-CATEGORY-PREPARED-ASSETS-1`. Existing furniture and held
  resource installers explicitly reject it; native integration is not implied.

The shared converter first validates the complete joined source model, then
splits its decoded commands into material and geometry lists. The source's
paired texture/tile command consumes two words but one decoded row. The initial
`-01` preparation counts raw words instead, incorrectly moving the vertex load
into the material list before the caller's matrix. The independent geometry
test catches that actual converter defect. The corrected decoder-boundary walk
keeps the vertex load with geometry; `-01` is not suitable for installation.
The initial preparation does not install these objects in a ROM; ABI 109's
police/handover integration above installs the corrected `-02` output.

Six focused category checks pass in 3.368 seconds on the corrected `-02`
preparation. They cover every source pixel, palette colour, vertex field,
triangle, retained graphics command, all parent/category/owner relationships,
rejection of changed consumers, shadows, callbacks, mismatched tables, and
unsupported selections. Joining the emitted lists after removing only the
intermediate return exactly reproduces the ordinary full-model conversion.
A seventh focused check passes in 0.350 seconds, retaining the installed
ordinary furniture batch's generated commands and rejecting material commands
in a geometry-only inherited-state list.

The initial test command also discovers unrelated imported test classes and
uses an incorrect held-installer function name. Its full result is not a pass.
The corrected test module imports the shared checks as a module, calls the real
installer entry, and explicitly selects only the intended category classes.
No emulator or hardware test is claimed for this converter-only batch.

The preparation leaves ABI 108 unchanged; the later runtime batch above retains
its preview/runtime evidence. Saved formats, profile bits, selectable choices,
and both served V2 patchers remain unchanged. Remaining integration covers all
native ground variants before enabling the item-type reader globally.
Do not substitute existing tool-bag artwork for the source fan representation.

## Shared inventory equipment previews

ABI 108 installs source-derived preview records for all eight fan parents
through the existing shared refresh. The separate inventory owner retains its
five original kinds and empty sentinel. Eight expanded tables reuse complete
models and holding poses, and a shared dispatcher resolves original tool
callbacks against the currently loaded inventory owner. No per-item installer,
new profile bit, selectable choice, or saved-format change is introduced.

The 540-byte adapter and its immutable tables extend the equipment reservation
from 24 to 28 KiB. Startup remains 952 bytes. Existing model/animation banks,
all earlier equipment-module bytes, source artwork, and player actions remain.
Exactly sixteen obsolete table relocations are removed; the complete owner and
relocation allocations stay unchanged. The specification records the source,
native ownership, entry points, and bounded layout.

Artifacts:

- Build: `build/v3-inventory-equipment-03/`, promoted in the development lock.
- ROM SHA-256: `25f0ee69193c75230b86b1a96e3d760c1cdc469fedc2a4ec39b3cafe7206122c`.
- UPS SHA-256: `57f84c4c11a52b8c5613f3a873a40beb7c00378cabf70e0cf80a2fa1fb63c4ca`.
- Receipt SHA-256: `0a0f83dcf853beab3f87507ebca4ae2f1be2008d5a1afe401d331fcf19377d35`.

Four focused checks pass across the host/source/cartridge commands. The
ASan/UBSan host check passes in 0.261 seconds. Two of three cartridge checks
pass in the initial 4.195-second invocation; the third incorrectly treats the
ROM file directory as immutable when installing relocated resources. Its
corrected focused invocation passes in 4.681 seconds. No cartridge change is
needed. These checks cover source/table relationships, retained owner bytes,
relocation at two bases, selected-only bounds, preserved resources/profiles,
startup, checksums, and original-ROM patch reconstruction.

Twelve candidate-bound composition checks pass in 8.758 seconds. All selected
imports reproduce ABI 108; empty selections reproduce V2-11. Dependencies,
sparse profiles, catalogue packing, and the actual saved-profile codec pass.
These are component checks, not ordinary save/restart evidence.

The first silent native run at `build/smoke-v3-inventory-equipment-01/` passes
104 records and 79 assertions with no failures. It executes eleven actual
inventory selector cases, two complete model transfers, the complete holding
pose transfer, and four native draw-table/dispatch windows: two imported fans,
the original axe, and the original shovel. Loaded owner/BSS, full equipment
module, private memory guards, no-fault status, restored player/profile, and
checkpoint restoration pass.

The same current-cartridge run completes the prior pocket-icon fixture's
unfinished controls. All seven selected/disabled/wrapped/native cases pass,
alongside full-width register preservation, correct resolved artwork pointers,
guards, unchanged module/owner/segments, and restored state. No old cartridge
is replayed. The combined results SHA-256 is
`f8dc835d59c5803c6ad7436973683093a7fbb57d5cedff1a911e8a3654aa3ea6`.
The isolated run shuts down gracefully with erased FlashRAM; it uses no user
save and plays no audio.

Full inventory construction, outer matrix/segment setup, GPU appearance,
ordinary equip/put-away, acquisition, and persistence remain unverified. No fan
is offered as playable. Next connect the remaining category consumers and
source acquisition, context-correct catalogue/collection, and optional profiles.
No more standalone preview or pocket-icon harness work is required without a
concrete changed dependency or observed defect.

Same-profile ABI 107 saves are expected to remain compatible in both directions;
no new ordinary cross-version reload is claimed. Import-enabled V3 saves remain
unsuitable for V2. Both served V2 patchers are unchanged; carry the museum-header
correction into checked V3 composition before the next handoff.

## Shared pocket icons

ABI 107 installs complete donor pocket artwork and a selected-parent reader
through the existing `--refresh-runtime --player-actions` path. Discovery
consumes the installed parent records and complete relocated tool-icon table,
not a maintained item list. All eight fans share one actual donor palette and
texture. Existing conversion retains all 1,024 indices and sixteen colours;
the descriptor table and deduplicated resources occupy 1,024 bytes at `804A6800`.
The combined parent/icon code is 1,284 bytes, with fixed name/price entries.

One native submenu detour replaces the tool-table HI/LO pair and removes only
those two relocations. The 560-byte relocation allocation, owner allocation,
24-KiB equipment module, startup size, models, motions, callbacks, sound, and
saved format 2 remain unchanged. The hook preserves full-width registers and
HI/LO, resolves the currently loaded owner, retains original descriptor paths,
and emits no drawing commands for a disabled extended parent. No fan profile
bit or logical import is enabled; the optional composer still has 104 choices.

Source category 43 is distinct from the menu's ID-derived tool category two.
The source `mTG_select_tag_decide_item_normal` uses the latter for normal action
menus. The native short item-type table and its actual consumers remain work;
they must not be confused with the now-connected pocket-icon lookup.

Artifacts:

- Build: `build/v3-held-pocket-icons-01/`, promoted in the development build lock.
- ROM SHA-256: `66205bfbf644fbfc7bc6e356d3a24d859e4676162e1b4bd3dc04dad5b21c0781`.
- UPS SHA-256: `bc0f44b421e06034c075f6ce89b90ce8c6a396d038b4bea89c262493b4064cdf`.
- Receipt SHA-256: `a906fb48102cc8dc227ad33c1c50c2a10d98897b59579ec77ee3db2f26054590`.

### Verification and bounded follow-up

Four focused checks pass in 5.713 seconds. They cover complete source artwork,
all pixels/colours, shared identities, bad-pointer rejection, selected-only
bounds under ASan/UBSan, exact declared owner edits, relocations, retained module
regions/profile/resources, startup checksum, native ROM checksum, and original
ROM UPS reconstruction. The initial invocation has two fixture errors: a wrong
patch filename and a mutation removing a cached relocation key. Correcting the
filename and changing the mutation to an invalid relocation section produces
the passing invocation without changing the cartridge.

Twelve current optional-composition checks pass in 8.947 seconds, with the
candidate lock bound inside the test process. All selections reproduce ABI 107;
empty selections reproduce exact V2-11. Sparse choices, actual save codec,
dependencies, catalogue packing, and retained identities pass. Neither patcher
is changed. Python syntax compilation and `git diff --check` pass.

The first silent native run, `build/smoke-v3-pocket-icons-01/`, records fifteen
entries and six passing assertions. Actual parent relocation, imported-hook
register preservation, and the first selected fan's complete 27-command drawing
pass. The disabled fan correctly produces no commands, but the fixture attempts
a zero-length debugger read; the debugger rejects that request. This is a
classified fixture failure, not an observed game fault. Result SHA-256:
`ba4583ce2ab0d10b82846bf194aaabb86bf5c69042060f14d398eb0a99edab82`.

The single corrected retry, `build/smoke-v3-pocket-icons-02/`, records 22 entries,
nine passing assertions, and one failed assertion. Complete loaded code/BSS,
equipment resources, profile, full GPR/HI/LO/floating-point preservation, two
independently enabled fan identities, and disabled drawing pass. The unchanged
gift case emits 27 commands, but the fixture incorrectly expects segmented
`0C012400/0C012420` pointers instead of the emitted resolved `00012400/00012420`.
The original drawing consumer calls native `Lib_SegmentedToVirtual` at
`8009ADA8` for both resources; its source uses `SegmentBaseAddress` at
`801458A0`, not a physical-address mask alone. The gift branch is outside the
modified instructions. This establishes a comparison error, not substituted
gift artwork. Result SHA-256:
`8238a2890f9df5d8c1d406eb456b9585c021c0a50a41d3034f76ac674a5ab78d`.

The fixture now resolves original descriptors through the actual segment table
and retains the correct zero-command case. It is not rerun: the setup retry
allowance is exhausted. Native gift/tool/umbrella comparisons, final guards,
restoration assertions, and checkpoint completion remain unverified. The
`finally` cleanup executes on both failed attempts, but that does not substitute
for the omitted full restoration checks. No display list is submitted to the
GPU, no audio plays, no user save is loaded, and no FlashRAM write is requested.
Do not report either partial run as a complete native pass or hardware evidence.

Continue inventory-screen player-item ownership/selection/drawing and remaining
category/acquisition/catalogue/persistence integration. Reuse passing component
evidence and carry the outstanding native control checks into the next relevant
inventory batch; do not repeat standalone harness attempts here. Same-profile
ABI 106 compatibility is expected in both directions because saved formats and
profile requirements are unchanged, not established by a new ordinary reload.
Import-enabled V3 saves remain unsuitable for V2. The V2 museum-header correction
still needs checked V3 integration before a handoff; both served patchers stay V2.

## Shared parent name and price readers

ABI 106 connects the eight implemented fan equipment records to the existing
public name/price paths through the same category importer. `parent_records`
verifies complete donor tables and consumer functions, price sentinel, and
pointer dependencies. The 1,360-byte `AFHI` table preserves official names,
donor prices, source category 43, canonical collection IDs, and equipment kinds.
All eight official names are credited in `translations/provenance.json`, using
`itemName_tool` and their actual indices. No second source catalogue is created.

The parent reader is 512 bytes at `804A6000`; the expanded display wrapper is
696 of 768 bytes. Names require sixteen writable bytes and selected equipment;
prices retain the native sixteen-bit argument convention. Action code, callbacks,
owner relocation, models, motions, sound, allocations, 104 choices, and saved
format 2 remain unchanged. No fan selection bit is enabled. Donor category 43
is recorded, not installed as an unchecked native menu/icon index.

Artifacts and verification:

- Build: `build/v3-held-parent-readers-01/`, promoted in the main build lock.
- ROM SHA-256: `46bfef14b0849f202bc0569408bc8d6337b889a1677c092c85c28111c48f2e7c`.
- UPS SHA-256: `51c815430898783f4d607ce5bc7f92b76261028386ea774b53b31a2fdcac42dd`.
- Build receipt SHA-256: `544bd16e49375135f37487eb554f5524bef0d344f975c6360f3ce9ec0859f48e`.
- Two cartridge checks pass in the initial 5.839-second command: complete source
  records/provenance, mutation rejection, all declared reader/table bytes,
  retained action module/resources/profile, CRC, and UPS reconstruction. The
  accompanying host fixture fails compilation because a sixteen-character
  string initializer would omit its terminator under the host warning policy.
  That command is not wholly green. The fixture explicitly copies sixteen name
  bytes; its corrected ASan/UBSan check passes in 0.159 seconds, without replaying
  the two passing cartridge checks.
- The shared display-wrapper ASan/UBSan check passes in 0.148 seconds, including
  the extended parent range, native argument widths, exact write bounds, and
  existing synthetic display/garment categories. Four focused checks pass across
  these commands.
- Twelve current optional-composition tests pass in 8.920 seconds. The test
  process binds the candidate lock before running the existing suite. Empty
  selections reproduce V2-11; all selections reproduce ABI 106. Actual codec,
  sparse selections, dependency checks, catalogue packing, and collision guards
  pass. Neither patcher is updated.

The first native run at `build/smoke-v3-held-parent-readers-01/` stops at 23
records/13 passing assertions. Its name-call proof incorrectly uses the harness
escape reserved for code outside the translation module. The harness rejects
that call before executing it. This is a fixture error, not a game failure.
Result SHA-256: `d7a42c2b209979dd72e30d2b0f392ab7fcf7a745f01ccc9e9c51516ef37cb9f6`.

The single corrected retry at `build/smoke-v3-held-parent-readers-02/` uses the
ordinary linked-module call after verifying the complete resident name entry.
It runs the same ROM and passes 112 records with 98 passing assertions. It
exercises the real loaded player selector, native switch returns, rejected IDs,
all eight independent selected/unselected fans, actual public English names and
prices, adjacent name guards, and undersized destination rejection. It verifies
passive/all/blocked permissions, hidden/force-visible priority, forbidden scene
rejection, state restoration, heap/module guards, no CPU fault, checkpoint
restoration, erased FlashRAM, and graceful shutdown. The equipment source is the
title-demo field; ordinary pocket/equip gameplay is not claimed.
Result SHA-256: `98390eafcc39ef4cb632f02f24bbee8f68711350f9b8e2df3d01e95b324b342e`.
Probe SHA-256: `ee253e9a8711f2d764aa7242c3ff533836ff8cfe218b8fb8778dad83d1b9c27f`.

This meaningful reader integration also completes the previously pending
selector/visibility checks; ABI 105 is not separately replayed. No physical
audio, user save, ordinary save/restart, or hardware test is involved.
Same-profile ABI 104/105 compatibility is expected in both directions, not newly
verified by ordinary save/reload. Do not use import-enabled V3 saves with V2.

Continue shared inventory/ground category, menu/icon, and inventory-screen
equipment selector/draw integration. The latter is its own owner and is not
covered by world-player drawing. Then connect acquisition, actual collection/
catalogue representations, optional selection, and ordinary lifecycle/persistence.
No fan is selectable or offered for playtesting yet; both V2 patchers stay intact.

## Shared selected-equipment adapter

The same category importer extends actual equipment selection and passive-item
visibility. `selection_records` combines the source item/kind tables, room aliases,
implemented callbacks, and checked model/animation pairs. It produces all eight
fan records in one 752-byte `AFHS` table at `804A8500`, without a per-item list.
Each item uses its canonical collection display's independent saved-profile bit.
No bit is enabled, no inventory reader/acquisition is installed, and no logical
choice is added. The original native 36-item switch stays intact. Two branch
hooks retain original ordinary/title equipment sources and existing scene,
hidden-item, force-visible, and all-items rules. Only the passive-item branch
adds selected category records. Existing fan callbacks, draw, and poll pointers
are rebound to the new compiled symbols. No relocation record changes.

### Candidate and focused checks

- Unpromoted ABI 105: `build/v3-held-selection-01/animal-forest-v3-asset-loader.z64`.
- ROM SHA-256: `111f011b45793a94d770da86ddb1c9055b226110398478d356e13f4a08d24f5e`.
- UPS SHA-256: `89d248e672843d8fc54da0487c919d7c1d5e4f5d3640e546681f49faa7023e4a`.
- Receipt SHA-256: `700014c5bf2eb88a3b2c5449df29dff15525b111b68f24c75f86345d70ed2ed5`.
- Compiled code is 2,504 bytes, inside the existing 8-KiB code reservation.
  The complete 24,576-byte module, 3,517,632-byte blob, startup, models, motions,
  audio, saved format 2, and 104 choices retain their allocations/identities.
- Current promoted lock remains ABI 104. Same-profile compatibility is expected,
  not a newly verified ordinary save/reload result. Do not use V3 saves with V2.
  Both served patchers remain V2; no playtest handoff is made from this candidate.

The selected-equipment host sanitizer passes in 0.164 seconds: all 16-bit input
IDs, individual fan bits, original passive umbrellas, unsupported kinds, malformed
headers/records, invalid masks, readiness, and permission flags. Three candidate
cartridge checks pass in the 5.576-second combined command, checking actual source
relationships, mutation rejection, complete table bytes, two relocation bases,
retained native switch, callback rebinding, profiles/resources, and UPS/CRC.
That command also names a nonexistent control-test method and therefore ends
with an import error, not a fully green command. The corrected control host
method alone passes in 0.183 seconds; the three passing cartridge tests are not
replayed. A focused original-switch/permission fixture check passes in 0.090
seconds. Six tests pass across these commands.

### Bounded native attempts

`build/smoke-v3-held-selection-01/results.json` stops after 12 records because
the probe requests permission value two, absent from the actual table; its
values are zero, one, and three. It has not called the changed selector yet.
Its result SHA-256 is
`bd3b39823c0962dfee7c318d9d9a288b81811842a33305a0d22ae9f814349b6a`.
The one corrected retry, `build/smoke-v3-held-selection-02/results.json`, stops
after 16 records when the probe expects item `2202` to return kind two. The
actual return is 35, exactly matching the original ROM's switch target and
constant-return instruction. The first two native item returns and retained
stack checks pass. This mismatch is not a cartridge defect.
The retry result SHA-256 is
`f57112a4d796baaec05d7d0e547058fabdac4fd9e10a715dc16001dc91ef59a7`.

The probe now derives expected native kinds from the original complete switch,
checking its hash and constant-return branches; the original last item is also
kind 33, not the fixture's guessed 35. The fixture check covers both mistakes.
No third native attempt is made for this batch. Imported positive selection,
passive visibility, final restoration/guards, and the completed scenario remain
unverified; no successful native or ordinary-equipment result is claimed.
The corrected probe is retained for the next meaningful inventory integration.

Continue parent inventory/names/prices/acquisition, context-correct collection/
catalogue, and optional composition from the candidate's explicit build lock.
Retain the promoted ABI-104 artifact until the changed native path is verified.

## Shared fan action activation

The existing action adapter registers the complete source fan callback group:
compiled setup and movement plus native net reset `808BE140`. Source submenu
and settle callbacks remain null. Four ordinary umbrella polls call the shared
umbrella-then-fan helper with unchanged priority and following input checks;
the umbrella's own repeat call remains native. Four obsolete local JAL
relocations are removed, bringing the total action/held removals to 64. All
original actions remain intact, and fifteen unfinished extended actions reject.

The outside-owner audit checks all three native comparisons against 105. One
is a resource byte-length bound. Equipment-change dispatch only returns
`-1, 7, 8, 9, 10`, so its bound needs no expansion. The native out-of-range
event-position result equals the source fan's zero entry. Complete consumer
bodies, callback registration, source dependencies, and the event table are
bound in the receipt; no unrelated core table changes.

The first full native action-cycle check exposed a real game bug: native speed
one crosses source frames 7.5 and 8 together, and an `else` swallowed the release
check. Repeat wrapping also skipped the idle threshold at 8.5. Independent ordered
event checks now handle the first boundary; a virtual crossed-end coordinate
handles the wrap without changing the rendered frame or advancing animation
twice. This is an implementation correction, not a testing-setup retry.

### Build and verification

- ABI 104: `build/v3-fan-action-dispatch-03/animal-forest-v3-asset-loader.z64`.
- ROM SHA-256: `b7a8964f6d8fa323c2c84712086cdb04949f07de230ac794ba3ae4a9d146d620`.
- UPS SHA-256: `9f2342690162bbe8ecc016022a58c4ee8d74ba92e013246bf5b887c5c1928a25`.
- Receipt SHA-256: `afa35cf9a6cba7f32ec8569ff239e7af3bf1835dd9bfe2a265df78287f74de4e`.
- Action code is 1,944 bytes, retaining the 80-byte dispatch prefix. Module is
  24,576 bytes; startup remains 952 of 992 bytes. Blob is 3,517,632 bytes, with
  611,136 free. No allocation, source model/motion, or sound resource changes.
- Saved format 2 and 104 choices remain unchanged. Same-profile ABI-103/104
  compatibility is expected both ways; the current actual-codec checks pass.
  No new ordinary save/restart or hardware result is claimed. V3 saves are not
  for V2. Both served patchers remain V2.

Four focused current-build checks pass in 5.692 seconds: host sanitizers,
held-A repeat and released idle across the wrap, complete source/callback/audit
contracts, owner relocation at two bases, resource retention, and UPS/CRC checks.
Twelve current composition checks pass in 8.667 seconds, covering exact no-import
V2, all-import ABI 104, sparse choices, dependencies, and the actual save codec.

The initial native result `build/smoke-v3-fan-action-dispatch-01/results.json`
contains 42 records and 24 passing assertions before the missing exit request;
SHA-256 is `55ef474cedc8ba13b49f36162376b0b2256c568d2c75955566b52aaa8c95a213`.
Raw requested-action and post-wrap frame values were not logged in that run;
the diagnosis comes from the boundary logic and the corrected execution.

The corrected result `build/smoke-v3-fan-action-dispatch-02/results.json`
passes 60 records and 37 assertions, SHA-256
`cd413a906a714b6ef08d901d87cc7f3d1d65bc6617884b6c32f7f57e0742f58d`.
Probe SHA-256 is `ea04a39f5e58211f837429005b177374156d40488887d69fb43f98c3bf667f98`.
Actual native setup selects animations 270/0, main dispatch advances the live
actor, frame eight requests movement action eight, and the next dispatch exits
the swing. Net reset, disabled-action rejection, full actor/animation-bank
restoration, guards, checkpoint restoration, and no CPU fault pass. Native
stationary idle and positive equipped-fan input are not claimed. FlashRAM stays
all `FF`, SHA-256
`b5a41c3758763bbec72769fab4a2533bf2db0b6312d93d25a695f9e4b9e02260`.
No audio or user save is used.

That run used build `02`; build `03` only clarifies source comments/indentation
and has exactly the same complete ROM and compiled code. The proof is retained
without another native run. Build `01` is not promoted.

Next connect profile-aware equipment selection, scene/special-action permissions,
parent inventory/names/prices/acquisition, context-correct catalogue ownership,
and persistence. No new logical item is enabled by callback activation alone.

## Shared held-item dispatch

The callback converter handles the two complete donor held-item tables using the
same format/reference/relocation rules as player actions. Native main/draw tables
grow from 21 to 24 entries without changing any original callback. Category 23
contains the source fan's static main/draw behaviour; categories 21 and 22 remain
null until balloon and pinwheel rigs are implemented. This does not select an
item, enable action 109, or add a browser choice.

The original zero-return callback supplies the source fan's empty item update.
Its complete 20-byte native body is checked. Drawing emits the checked model's
display list from either active equipment bank and clears the native rod-tip
flag. Missing resources and invalid banks emit no command. The original outer
drawer retains the hand matrix, scale, opaque stream, and segment-six binding.
The donor balloon-start flag has no native storage; no unrelated field is used.
The source net-angle reset is bound to the equivalent native `808BE140` routine,
but its action-table registration remains pending.

### Build and verification

- ABI 103: `build/v3-held-item-dispatch-02/animal-forest-v3-asset-loader.z64`.
- ROM SHA-256: `d9c84c537a1565986de459667e4428d9d0dadcf79a1f1ea7a1904eb03fd99f0b`.
- UPS SHA-256: `b094874d1378dae030b81ea676792453da85e6fe67b3b483dc2fce742c1964a8`.
- Receipt SHA-256: `de2265f41d8d0a54ab2db52452dc0e51e501e30d929eef907ff0a90eeb7f5842`.
- Code: 1,908 bytes in the unchanged 8-KiB reservation. Both existing dispatch
  entries and their 68-byte prefix remain; a `v1` variant supports native held
  main calls. The 208-byte table block starts at `804A8430` inside the module.
- Four held-table address relocations are removed, retaining original callbacks,
  owner dimensions, and other relocations. Current total removals are 60.
  The existing 17,584-byte player-relocation resource is updated in place inside
  the blob; complete blob checksums include those changes before emission.
- No allocations move or grow. Blob remains 3,517,632 bytes, with 611,136 free.
  Startup remains 952 bytes. Sound programs, complete models/motions, 104 choices,
  and saved format 2 are unchanged. Same-profile ABI-102/103 compatibility is
  expected both ways and the actual codec passes; ordinary save/restart and
  hardware are not newly tested. V3 saves are not for V2. Both patchers remain V2.

Four focused checks pass in 5.822 seconds, including host sanitizers, both model
banks, rejected missing/invalid resources, full source/callback tables,
relocated owner references at two bases, resource retention, checksum accounting,
and reconstructible patch. The existing shared native scenario takes the new
held-category branch instead of repeating the unchanged sound/control tests.
Twelve current optional-composition checks pass in 9.120 seconds, including exact
no-import V2, all-import ABI 103, sparse profiles, dependencies, and the real codec.
The native check's single attempt passes 58 records and 40 assertions. Results at
`build/smoke-v3-held-item-dispatch-01/results.json` have SHA-256
`86e2281bedc2fa7694f181f5f38de9a0cde5e9e3a1334e30212c2e261059fa54`;
probe SHA-256 is `315ab11ef745f66b99a42c8605a51104a4114c61151c73f731d3a9c0b7eac2d5`.
Verified: original/imported main dispatch, null/out-of-range results, complete
tables, actual static draw commands in both banks, invalid-resource rejection,
guards, unchanged profile, and checkpoint restoration. FlashRAM remains all
`FF`, SHA-256 `b5a41c3758763bbec72769fab4a2533bf2db0b6312d93d25a695f9e4b9e02260`.
No audio is played. Full scene rendering and ordinary equipped fan use remain
unverified; the direct draw callback is not presented as either result.

Continue outside-owner action checks, action 109 registration, four ordinary
polling sites, profile-aware equipment selection, parent inventory/acquisition,
catalogue identity, and persistence. Reuse current category records and passing
evidence; do not add per-item installers or replay the unchanged sound batch.

## Shared sound programs and per-frame actions

The existing player-action refresh adapter installs the fan's complete per-frame
callback and `tools/v3_sound_programs.py`, a reusable batch converter for
explicit-bank, single-layer notes with custom envelopes and optional special-mode
pitch sweeps. The source function supplies sound ID `0167`; no per-item sound
script, copied instrument, or extra sample is needed. The converter checks the
complete native instrument identity, interpreter handlers, priority, pointers,
and permanent-resource budget. Occupied slots and unsupported forms reject.

The player callback retains the donor's movement/input/animation/sound/collision/
item/transition order. Sound occurs at frame `1.5` only if animation advances.
The native WAIT initializer advances the same 33-frame motion at speed `1.0`,
versus donor `0.5`; the fan's retained motion and input threshold use native
speed `1.0`. Event coordinates remain unchanged. Common native braking uses
`0.75`, not the donor's per-update `0.32625001`. The native run verifies one-step
frame and morph advancement through the actual live player's skeleton.

### Build and memory

- ABI 102: `build/v3-player-frame-sound-01/animal-forest-v3-asset-loader.z64`.
- ROM SHA-256: `92bffc4eced4cf170922db9080510d347212d65255538f8c8d828cceaf779cc7`.
- UPS SHA-256: `79579190df6845ba6efb7007ed187fec2509dc97e1f6551ebe9978c0a1c55b46`.
- Receipt SHA-256: `fb8a8256883c9640c999290cde48465e6c5a7dad8adf39bc43ba22dab0660a31`.
- Shared action code: 1,772 bytes, maximum direct stack 64 bytes, original
  68-byte dispatch prefix retained, unchanged 24,576-byte module allocation.
- The complete 20,208-byte sound sequence is appended in ROM; all prior sound
  programs retain their offsets. Only the previously empty dispatch entry and
  sequence header change. The sequence adds 32 loaded bytes. The full permanent
  resource inventory requires 109,344 of 109,568 bytes, leaving 224 bytes spare.
- Blob: 3,517,632 bytes, with 611,136 free before English choice resources.
  The three terminal catalogue/shop owners move without content changes. Models,
  motions, player owner/relocations, callback tables, and profiles remain intact.
- Startup: 952 of 992 bytes. The 104 choices and saved format 2 are unchanged.
  Same-profile ABI-101/102 saves are expected to work in both directions; the
  real codec passes, but this is not another ordinary save/restart or hardware
  playthrough. V3 saves are not for V2. Both served patchers remain V2.

### Verification

Six focused checks pass in 5.625 seconds: sanitizer-covered controller/setup/
transition/per-frame order, once-per-crossing sound, stopped frames, native
timing, complete sound conversion, malformed/occupied-slot rejection, resource
retention, CRCs, and reconstructible patch. Twelve current composition checks
pass in 8.411 seconds, including exact no-import V2 and all-import ABI 102.

The single silent native attempt passes all 119 records with 70 passing
assertions. `build/smoke-v3-player-frame-sound-01/results.json` has SHA-256
`7d16d4d8a260bbe68735811d6d722a3640803a28ade742af4227b234f8f9d209`.
The shared probe SHA-256 is
`5ab3dbd8d5c0f8eb721d5ea2228f7febaa3e6bf93903be1797eb6a430a083cf1`.
It verifies actual sequence loading and dispatch, priority 60, fifteen completed
sample-DMA observations, native heap bounds, real-player animation/collision
callback, private and live bank restoration, saved-profile retention, guards,
and checkpoint restoration. The title-demo movement is `(-0.3934426, 0)` and
correctly produces a walk request. Native idle acceptance remains unexecuted;
the host check covers it. FlashRAM remains 131,072 `FF` bytes, SHA-256
`b5a41c3758763bbec72769fab4a2533bf2db0b6312d93d25a695f9e4b9e02260`.

This is component execution, not an ordinary equipped fan or a hardware result.
No audio reaches speakers/headphones; PCM/listening quality is unverified. The
callback tables and input-poll hooks remain off. Continue the shared held-item
main/draw tables, source fan draw and net reset, four ordinary polling sites,
selected inventory/acquisition/profile handling, and outside-owner action audit.
Do not repeat unchanged passing checks or introduce per-item installers.

## Shared fan control flow

The existing `--refresh-runtime --player-actions` mode installs the donor fan's
press/hold controller, priority-checked request, split-body setup, repeat setup,
and end-of-swing transitions. The implementation resolves the actual loaded
native owner on every call. Fifteen complete donor functions and nineteen
native APIs bind the adapter. All eight fans share these functions. No extra
item script, action table, actor allocation, animation bank, or saved field is
added. Callback tables and ordinary input-poll hooks remain unchanged and off
for imported actions. This is not a selectable/playable fan handoff.

The native standard initializer is `808B4A44`, with ten arguments. The reverse
initializer at `808B4B6C` has a different signature. The source fan uses upper
animation 270, native lower WAIT1 zero, half-frame speed, repeat mode, and
explicit mask four. Its start/repeat lower frames and morph values differ.
The native idle request has four arguments, unlike the donor's five; the
extra donor delay is stored but not consumed by its idle initializer. Flag two
is unused by both. The adapter preserves the effective behaviour without
passing the extra float into the native flags field.

### Build and allocation

- ABI 101: `build/v3-player-fan-controls-01/animal-forest-v3-asset-loader.z64`.
- ROM SHA-256:
  `1763e613b3f080a4cacc26cbfa9d244a742b6e34cff077bbc9e142ac4aeeaa38`.
- UPS SHA-256:
  `06fa46e6bba6721d01958b62f9d63386fd64f38b9cb5a3def9bbbf3bb07857ea`.
- Receipt SHA-256:
  `faa4db40813490033dd2ba7d538c9bcedd9b8eb4639689c8dc3fa25e7dde1abb`.
- Shared action code: 1,436 bytes at `804A5000`, inside its existing 8-KiB span.
  The original 68-byte dispatch prefix and both public entry addresses remain.
- Module: unchanged 24,576-byte allocation at `804A3000`, VROM `0253BD00`.
  Shared refresh updates code in place instead of allocating another copy.
- Blob: unchanged 3,497,424 bytes, retaining 631,344 bytes of free storage.
  All models, motions, tables, owners, relocations, and resource locations remain.
- Startup: 952 of 992 bytes, with the updated complete-module checksum.
  The 104 choices and saved format 2 remain unchanged. Same-profile ABI-100/101
  compatibility is expected in both directions and the profile codec passes;
  this is not a fresh ordinary save/restart or hardware test. Do not use V3 saves
  with V2. Both served V2 patchers stay unchanged.

### Focused verification and classified stopping points

Two current host/cartridge tests pass in 5.622 seconds. Address/undefined-behaviour
sanitizers cover all fan kinds, rejected kinds, title/ordinary press and hold,
permission and priority rejection, unchanged actor bytes on rejection,
walk/run/dash speed thresholds, umbrella/fan polling order, both setups, bee
timing, repeat requests, and walk/idle arbitration. The host priority model
retains the native pending-request and already-settled checks. Cartridge checks
bind complete code, source/native functions, deliberate native API corruption
rejection, unchanged tables/artwork/owners/profiles, unchanged allocations,
checksums, and complete patch reconstruction. Twelve current optional-composition
tests pass in 7.783 seconds, including exact no-import V2, exact all-import ABI
101, dependencies, sparse selection, and the actual saved-profile codec.

The silent native probe extends the existing shared player-motion scenario,
using an isolated full-size actor, fake game context, and two native-sized
animation banks. The first attempt stops at the debugger's low-RAM call guard,
before invoking a new function. The single setup retry uses the established
eight-byte low-RAM jump bridge to the cartridge-loaded Expansion Pak code.
No replacement gameplay function is uploaded.

`build/smoke-v3-player-fan-controls-02/results.json` contains 50 records and 22
passing assertions before the final idle expectation fails. Its SHA-256 is
`ec20b8b90916c5a5ef7f3270e209d8a7024a7102d7c841bc405457a4c8dbcecf`.
Verified components include complete module/code relocation, hidden-item
controller rejection, actual priority/request writes, equal-priority rejection,
full setup, eye pattern, frame control/morph, complete swing DMA, explicit mask,
restored segment-six binding, repeat lower-frame retention, zero repeat morph,
and bee timing. The failing field's observed SHA-256 is
`5be0a01e5257e4c08ac57e3d288893e9cc6f8d6fc2d9aff9eab81c0fbf00c384`,
which independently decodes to `(requested action=8, priority=1, pending=1)`.
That is the valid walk request. The original native priority-settling function
does not clear an existing pending request, so an equal-priority idle request
cannot replace walking. The fixture incorrectly assumed the title-demo stick
was idle; this is an expectation failure, not evidence of a game defect.

The corrected fixture reads actual title/ordinary controller movement and checks
the resulting walk or idle branch. It is **not rerun** in this batch. Final
guard checks, checkpoint restoration, native idle acceptance, and a positively
equipped fan controller remain unverified here. Retain the passing prefix and
include those checks with the next actual callback integration, not a third
setup attempt. The isolated 131,072-byte FlashRAM stays all `FF`, SHA-256
`b5a41c3758763bbec72769fab4a2533bf2db0b6312d93d25a695f9e4b9e02260`.
No user save or hardware is touched, and audio is disabled.

### Next shared dependencies

The donor's complete fan sound program is 32 bytes at main-sequence `0812`.
Its bank-154 instrument 12 matches native bank-140 instrument 12, including
all tuning/envelope/loop/predictor data and the 3,726-byte sample. Both priority
entries are 60. Numeric ID `0167` is still outside the original 97-entry native
group and is not a playable registered sound. Extend shared sequence-program
binding with the complete custom envelope and playback operands; do not append
another copy of the instrument/sample. The [specification](../../specs/V3_HANDHELD_ITEMS.md)
records exact identities. Complete the per-frame action/draw/net reset, the four
ordinary polling sites, native selected equipment, acquisition, and profiles.
Keep all unfinished callback entries disabled until their dependencies exist.

## Shared player action tables

The existing importer installs `--refresh-runtime --player-actions` through one
source-derived adapter. All 22 metadata tables and five callback tables in the
native player owner have complete 121-entry storage. Original indices `0..104`
retain every original value and callback. Extra indices `105..120` retain the
donor's actual metadata, including fan action 109, but their callbacks stay null
until implemented. This is action-table/dispatch integration, not working fan
behaviour, additional item selections, or an import handoff.

The source reader indexes actual `.rodata` relocations. The donor's callback
tables contain zero pointer placeholders before relocation; treating those
bytes as null callbacks would lose real dependencies. The fan needs the donor
net-angle reset callback as well as its setup/main routines. Its submenu and
settle callbacks really are null. The complete function/table/relocation
receipts are retained for the next implementation, without per-item definitions.

Twenty-eight table address pairs move to the extended immutable tables;
exactly 56 obsolete HI/LO relocations are removed. The unrelated spatial-search
loop's reference at `808B99D0/808B99D8` remains: it uses the old address as the
exclusive end of the preceding eight-float array. The 27 action limits increase
only alongside complete arrays. Five indirect calls use two shared register
variants which resolve native linked callbacks against the current loaded
player constructor. Imported resident pointers pass through unchanged. The
original table objects, owner size, other relocations, arguments, and stack
contracts remain intact.

Output: `build/v3-player-action-tables-03/`, ABI 100.

- ROM SHA-256:
  `1cffa6906ac85234ee16e1e81b7b18f20fc92cc118ce477a002d5511c8648273`.
- UPS SHA-256:
  `ca38866d3dca1c10d3612d474312a250a042c6242e2587ca2e5447a0523a951c`.
- Receipt SHA-256:
  `f0b4b6d9b21a720f4004be590cd68170facdca3b6cc8e080288764904b8c098c`.
- Shared equipment/action module: 24,576 bytes at `804A3000`, VROM `0253BD00`.
  The original 8,192-byte equipment region remains unchanged; additional code
  and table space uses 16 KiB before the existing furniture pool.
- Dispatch code: 68 bytes at `804A5000`; tables: 5,164 bytes at `804A7000`.
  Both the old internal guard and new end guard remain.
- Startup: 952 of 992 bytes; one checksum-bound transfer and cache flush cover
  the complete module. No actor, animation buffer, ordinary heap, or save grows.
- Import blob: 3,497,424 bytes; 631,344 bytes remain before English choices.

### Verification and remaining work

Risk: stale relocated callback pointers, incomplete tables or relocation
removal, disturbed unrelated table boundaries, and incomplete startup cache
coverage. Six focused cartridge/startup checks and nine shared handheld/source/
art checks pass. They cover both native relocation bases, all original and
extended table contents, pending callback rejection, complete resource retention,
source/bound mutation rejection, patch reconstruction, module bounds, and the
real startup C under address/undefined-behaviour sanitizers. Twelve prospective
current-build composition checks pass, including exact no-import V2, exact
all-import output, sparse profiles, dependencies, and the actual save codec.

The corrected silent native run at
`build/smoke-v3-player-action-tables-02/results.json` passes 173 records and 143
assertions. Result SHA-256:
`29f8c7994066fa88190b06871d9f1ad2e8c455a0f341dd4cf46d72700cd1213c`.
It verifies the complete module and actual game-loaded player code/relocations;
reads representative native/new/invalid action metadata; rejects five unfinished
or invalid requests without modifying their scratch actor; compares an original
net callback with the same callback reached through shared dispatch; and tests
both dispatch-register variants against native and resident targets. The only
uploaded code consists of 16-byte call bridges in isolated heap scratch, not
replacement callbacks. Existing kind readers, representative transfers, all
five masks, profile retention, guards, checkpoint restoration, and graceful
shutdown also pass. The isolated 131,072-byte FlashRAM remains erased. Audio is
disabled; no user saves are touched. The probe source SHA-256 is
`1eb87d3efece12d9f19ded64fbcb7c143f70570489d6507681e024704d5d82e7`.

The first native attempt expected zero for the priority getter's invalid index;
the original native function returns `-1`. Its instructions and observed return
establish a fixture error. The single corrected retry passes without a ROM
change. The initial build's allocation guard also correctly stopped an attempted
in-place update of a compressed relocation resource. The shared importer now
stores changed compressed owners in checked uncompressed storage, keeping their
logical DMA identity and dimensions. Build `03` corrects the existing motion
receipt's relocation-hash field; its ROM/UPS are identical to the tested build
`02`. The six focused current-cartridge/startup checks cover that final receipt;
unchanged native evidence is retained instead of replayed.

The 104 choices and saved format 2 remain unchanged. Same-profile compatibility
with ABI 99 is expected in both directions; ordinary save/restart and hardware
testing are not claimed by this batch. V3 saves remain unsuitable for V2. Both
served patchers remain untouched. No player-facing text is added, so the single
text provenance catalogue needs no new entry.

Continue actual fan controller/request/setup/main/drawing and source-timed sound
using these shared tables. Audit core-library action checks outside this owner,
then connect kind selection, complete inventory/readers/acquisition, and selected
profiles. Fan swing uses animation 270 and explicit mask four. Other toy rigs,
remaining item/villager gameplay, browser validation, and persistence remain in
the full V3 queue; this infrastructure does not replace that scope.

## Shared equipment kind readers

The existing importer's `--refresh-runtime --equipment-kinds` mode connects all
six kind-indexed native readers through one complete source-derived table.
Seventy-nine donor kinds use stable indices `36 + source kind`; all original
kind meanings, tables, and table relocations remain. Sixteen-bit fields preserve
the fan holding animation index 269 without clipping it to a byte. There is no
per-item definition, installer, or dedicated fan test scenario.

Complete donor functions/tables supply holding pose, item routine, model,
equipment animation, tumble, and get-up. The latter two are actual fall/recovery
consumers, not take-out/put-away readers. Four complete source motions 25–28 add
5,744 bytes, retaining their 17-/32-frame timing and all key data. They fit the
original 3,848-byte animation banks. The original eight imported player motions,
fourteen held models, and sixteen equipment motions remain unchanged.

Output: `build/v3-equipment-kinds-runtime-01/`, ABI 99.

- ROM SHA-256:
  `c4c5e56687edeaa2ae0ce6dfd1bc9471f9a8a22c27f4768f85f522c1fbc12749`.
- UPS SHA-256:
  `b94c92dc4eae3a33ddba7ff952f555730b343e618d9e546fa4fad95e162bfcfc`.
- Build receipt SHA-256:
  `bbf6828e4f29a7ce26436d0326893f2c759d8b2f665dc93126399a2b42e10ac9`.
- Shared module: 1,472 code bytes; existing 8,192-byte allocation and VROM
  `02537DC0` remain. Startup remains 952 of 992 bytes.
- Import blob: 3,455,264 bytes; 673,504 bytes remain before English choices.

The new `AFKD` header/records occupy module offsets `B00..EC3`; code is bounded
below `B00` and the native part-copy bridge remains at `FE0`. Getters at
`808BD668`, `808BD690`, `808BD6B8`, `808BD6E0`, `808C2D4C`, and `808C32CC`
retain native table HI/LO relocations at offsets 12/24. Imported values delegate
to one shared reader with an explicit field index. Invalid indices preserve
the distinct original defaults. Existing motion/resource hooks are rebound to
the compiled helpers without changing their resources or semantics.

All nineteen static item/state resource pairs fit the combined 4,376-byte
equipment-bank limit; the largest is 4,032 bytes. Unsupported skeleton slots
remain missing, not approved substitutes. The actual item selector remains
unchanged and therefore still rejects the extra inventory identities. Source
item-routine values 21–23 are stored as dependencies, not installed dispatchers.

### Verification and next work

Risk: incorrect kind offsets, narrowed animation indices, changed native table
relocation, or oversized combined resources. The existing player-motion suite
now covers source-bound records, mutation rejection, every table field, all four
new complete animations, retained resources, exact cartridge ownership, two
relocation bases, source/ROM checksums, and reconstructible patches. The real C
readers pass address/undefined-behaviour sanitizers, including indices above
255, negative/missing resources, both kind bounds, and malformed headers.
All six checks pass on the first run.

The twelve current-build optional-composition checks pass, including exact V2
for no imports, exact ABI 99 for all imports, sparse selections, dependency
rejection, and save-profile codec. The first invocation stops before executing
tests because the temporary prospective-build override omitted `REPORT_SHA`.
The corrected invocation supplies all four existing pins and passes; no ROM or
composer change is needed. This is the single corrected setup retry.

The first native run, `build/smoke-v3-equipment-kinds-01/results.json`, passes
126 records and 106 assertions, SHA-256
`afea974561fd0498d7f7d764f754c8e54522646bab1953371a846965cbe4442e`.
The shared player-motion probe reuses the actual loaded owner, verifies its
complete relocated code, and calls all six getters for original tools, three
extended categories, and invalid bounds. Four representative animation
transfers cover tumble/get-up and two original indices, with full data and
untouched-tail comparisons. All five masks, equipment fallbacks, guards,
saved-profile retention, checkpoint restore, and graceful shutdown pass.
Isolated FlashRAM remains erased; there is no audio or user-save write.

The 104 choices and saved format 2 remain unchanged. Same-profile compatibility
with ABI 98 is expected in both directions; this batch does not claim another
ordinary save/restart or hardware playthrough. V3 saves remain unsuitable for
V2. Both served patchers stay unchanged.

Continue actual equipment selection, category/scene permissions, item drawing,
and the fan controller/request/action. Audit native action dispatch and all
action-indexed permission tables before adding a fan action; do not repurpose
an existing action or widen bounds over short tables. Preserve source swing
animation 140/native 270, explicit mask four, and frame-timed sound.
`Player_actor_sound_uchiwa` is donor `.text:16FA00`, calling
`Player_actor_set_sound_common2` with `NA_SE_UCHIWA`; the actual native sound
resource still needs identification/conversion, not an unrelated substitution.
Fan inventory, names/prices, acquisition, catalogue/collection, selected profiles,
ordinary take-out/put-away, and persistence remain. Balloon joint-work capacity,
net/rod graphics matrices, and pinwheel rig packing remain separate shared
category dependencies. No new handheld item is selectable or claimed playable.

## Native player motion and part masks

The existing importer's `--refresh-runtime --player-motion` mode extends the
shared held module with eight complete player motions: six equipment holding
poses, fan idle, and fan swing. Each is independently packed for the native
player-animation DMA. Their 2,256 bytes fit the existing 3,848-byte banks.
Indices are `130 + donor animation index`; all 130 original indices and tables
remain intact. No per-item installer or alternate simplified motion is used.

The source-derived default-part table and complete mask-copy function bind the
split-body conventions. All four original masks match their donor equivalents.
The fifth mask is copied from the donor, preserving all 27 entries. The fan's
action initializer explicitly selects mask four; its default animation-to-part
table returns three. The implementation retains both facts rather than
rewriting the default table to impersonate the action.

Output: `build/v3-player-motion-runtime-01/`, ABI 98, pinned by
`config/v3-import-build.json`.

- ROM SHA-256:
  `88106989dc341f554ba0979079539c96b05bba60550be2999994bf7b1eb0739c`.
- UPS SHA-256:
  `01a85334ad6c9ca80875065857e2bcf29cd9630d9a780492d75ff327455ddecf`.
- Build receipt SHA-256:
  `13050814fc10d39b25cd124df74c07f39b3bda66f4cc2bc8ab91b9ebcf9aaaae`.
- Shared module code: 1,304 bytes; module allocation remains 8,192 bytes at
  `804A3000`, VROM `02537DC0`. Startup remains 952 bytes.
- Import blob: 3,449,520 bytes; 679,248 bytes remain before English choices.

Core size/origin/VROM getters and mask copying support the additions. The
native player owner's pointer and default-part getters retain every original
HI/LO relocation and delegate only non-native indices. Actual DMA, segment
bias, native mask copying, player actor size, and bank allocations remain
unchanged. The guarded native mask-copy prologue bridge occupies module offset
`FE0`; the sparse `AFPM` table and extra mask use previously empty data space.
Existing held models/motions retain their exact resource locations and data.
Only the three unchanged terminal catalogue/shop owners move to make ROM space.

### Verification and remaining work

Risk: the new readers must preserve relocated native tables, animation banks,
mask lengths, and original equipment. The bounded checks cover actual C under
sanitizers, full source objects, two host relocation bases, cartridge ownership,
checksums/patch reconstruction, current optional composition, and one corrected
native category run. Player actions and ordinary graphical animation playback
are not inferred from these resource checks.

Seventeen distinct focused tests pass: five current motion/owner checks and
twelve existing optional-composition checks bound to ABI 98. The initial host
run passes three and exposes two fixture issues: comparing JSON-normalised
relocation dictionaries against Python tuples/integer keys, and directly
indexing an optional absent receipt field. Both corrected fixture checks pass
on their focused retry; production data/code are unchanged by that correction.
Empty/full/subset composition and saved-profile requirements pass.

The first native attempt verifies the resident module, then fails its test-only
221,184-byte allocation for a second player overlay. It does not enter an
animation test. The corrected probe derives the real loaded owner from
`Player_actor_ct_func`, verifies all 175,872 code bytes against expected
relocation, and allocates only 4,352 bytes for guarded animation scratch. Getter
calls use independently checked, function-sized code proofs. The live owner is
`80394490`, constructor `803BEE88`; the probe never overwrites that owner.

`build/smoke-v3-player-motion-02/results.json` passes 102 records with 79
assertions, SHA-256
`10c13dbdfb0f028b28f9695bb655f8b4491adb83785e58268f72e6cca3e98ba5`.
Seven representative transfers cover source-derived constant/animated categories
and original animation indices. All five masks, original equipment fallbacks,
invalid indices, untouched transfer tails, guards, and saved-profile retention
pass. Checkpoint restoration, fault status, and graceful shutdown pass; isolated
FlashRAM remains blank. No user save is used and no hardware test is claimed.

The 104 choices and saved format 2 remain unchanged. Same-profile ABI-97
compatibility is expected in both directions; no additional ordinary save/reload
cycle is claimed. V3 saves remain unsuitable for V2 and profiles must include
saved imported identities. Neither served patcher changes.

Next: native kind selection and dependent readers, real fan controller/request/
action flow and its explicit part mask/timing/sound, take-out/put-away/drawing,
inventory/acquisition, and optional profile selection. Net/rod joint matrices,
balloon textures and joint-work capacity, pinwheel rig packing, and combined
model/animation bank bounds remain actual dependencies. Imported animation
indices remain outside original footstep/event tables; new actions need their
own source timing, not enlarged bounds over short native tables. No new item
becomes playable or selectable solely from this batch.

## Native held-resource loading

`--refresh-runtime --equipment-art` installs one source-derived category through
the existing importer: fourteen complete static held models and sixteen complete
equipment animations. It reuses the prepared graphics, packs each animation for
independent native DMA, and reserves stable indices `17 + source index` in a
fifty-slot table. Unsupported skeleton slots remain empty. The eight prepared
player animations are not installed by this batch. No item choice or action is
enabled merely because its resource can load.

Output: `build/v3-equipment-resources-runtime-03/`, ABI 97, pinned by
`config/v3-import-build.json`.

- ROM SHA-256:
  `2ae396a32a1fbd86411c2dec5420fb45c702fdfb048828b8ddabce84185a4e3a`.
- UPS SHA-256:
  `1e175606802ef57eb4233f8a4e3f90faa5edc6f189acac9d24b5b5ffb778e743`.
- Build receipt SHA-256:
  `90068e8fa585961789f63638827f624039c837ebfe78e9538fd9b3d06dc74580`.
- Resources: 31,584 bytes; shared resident module: 8,192 bytes, 644 code bytes.
- Module RAM: `804A3000..804A4FFF`; VROM: `02537DC0`.
- Startup: 952 of 992 reserved bytes. Import blob: 3,447,264 bytes;
  681,504 bytes remain before the English-choice resource.

Five shared native getters provide pointers, types, sizes, segment origins, and
VROMs. Original indices, lookup tables, DMA, and segment-bias routines retain
their semantics. The original player bank switch and menu-close reload both
call those DMA routines; they are not separately reimplemented. The importer
moves only the three unchanged terminal catalogue/shop owners to append these
resources. All existing graphics, owner data, catalogue content, profiles, and
save code remain unchanged.

Initial linking exposed a 52-byte startup overflow. Sharing CRC-checked transfer
code and consolidating package instruction-cache coverage resolves it without
expanding the reservation or consuming configuration/scratch space. The complete
equipment module, including its header/footer, is bound by a compiled CRC.
No failed build is promoted. Intermediate local output directories remain intact.

### Verification and limits

Risk: changed startup and native equipment readers must not corrupt the resident
packages, original tools, or existing imports. Stop after shared reader/startup
sanitizers, current cartridge ownership/source checks, optional composition,
and one bounded representative native DMA pass. Do not add individual item tests
or infer playable actions from successful transfers.

All eighteen focused tests pass: six in `test_v3_equipment_runtime` and twelve
existing optional-composition tests directed at the new cartridge. Coverage
includes native-index fallback, malformed/empty records, all four startup
transfers and failure paths, complete source artwork/motion comparison, retained
unrelated owners, future terminal-tail reuse, code bounds, CRCs, N64 checksums,
UPS reconstruction, and optional/profile handling. Empty selection reproduces
the exact stable V2 cartridge; full selection reproduces ABI 97.

The first silent native run, `build/smoke-v3-equipment-resources-01/`, completes
115 records with 96 assertions. `results.json` SHA-256:
`0aa9746def1cbf54783a9b83be923983a9f60c3b71a4541e1ef5cd0f8510365f`.
The existing shared batch probe selects the largest object in each of five
imported resource categories and four original resources. All nine complete
transfers, untouched tails, pointers/types/origins, segment-base calculation,
invalid indices, allocation guards, resident guards, and unchanged saved profile
pass. The checkpoint restores, CPU fault status remains clear, shutdown is
clean, and isolated FlashRAM retains its blank hash. No user save is opened.

The 104 choices and saved format 2 remain unchanged. Same-profile compatibility
with ABI 96 is expected in both directions; no new ordinary save/restart or
hardware playthrough is claimed. V3 saves remain unsuitable for V2, and profiles
must include any imported identities already saved. Both served patchers remain
unchanged and this build is not a new playtest/release handoff.

Next: actual native kind selection and indexed readers, player holding/action
animations, fan waving with source timing/part masks, inventory/acquisition,
and selected-only profiles. Native player arrays contain seven work vectors,
while the donor has eight; balloon rigs need explicit buffer work. The bank
switch places animation after model, so paired sizes require separate validation.
Ordinary take-out/put-away, menu-close reload, model drawing, and player actions
remain untested. Resource loading alone is not a completed handheld import.

## Held-motion dependencies

`tools/v3_keyframes.py` implements shared complete rotational-skeleton and
keyframe parsing/packing. Source-derived equipment and player selectors feed it;
there is no maintained per-item animation list. All twenty held skeletons retain
their actual joint hierarchy, translations, streams, and model roots. The
sixteen equipment animations and eight equipment-related player animations
produce one 7,760-byte native-format object containing 84 complete arrays and
24 relocated headers. The fan swing comes from the complete donor setup
function's actual initializer argument, not a guessed animation name.

Output: `build/v3-held-motion-prepared-01/`.

- `held-motion.n64obj.bin` SHA-256:
  `e17c8d6251ee37845c3c693b2b226e2e911aba5043b6e493270ee8e70289663c`.
- `art.json` SHA-256:
  `09bac790415a75834fbfad6f58413e43a70c573e3e9c5beb96149928e0eae9d8`.

The same `v3_furniture_pipeline.py convert --representation handheld
--assets-only` command accepts `--category held-motion`. This is a complete
dependency bundle, not a selected gameplay profile. Individual gameplay
selection remains native/profile integration work. No alternate installer,
prepared furniture substitution, or public output is introduced.

Fourteen distinct focused checks pass: eight keyframe/source/packing checks and
six existing held-source checks. Complete source arrays and header pointers are
compared independently; root translation and every joint rotation consume
exactly the expected constants and keyframe tracks. Topology, source/player
bindings, preserved null pointers, malformed flags/counts/frames, stale
descriptions, and changed source selectors/setup reject as intended. The
initial run passes thirteen and exposes a stale cached relocation-address list
in one mutation fixture. Updating both fixture indexes gives a passing focused
retry; production source parsing is unchanged by that fixture correction.

The initial conversion identifies constant-only player poses with null key/count
pointers. Shared format handling preserves those nulls and validates their full
constant arrays; it does not create fake animation tracks. The prepared bundle
contains six such poses plus the fan's seventeen-frame idle and nine-frame swing.
No movement is resampled or shortened.

Native rig/model ownership and buffers, player actions, part masks, sound,
inventory readers, acquisition, and profile integration remain unfinished.
Net/rod graphics require joint-matrix commands; balloon graphics require wider
texture support. Pinwheel graphics pass existing preflight but have no complete
native rig/model installation. ABI 96, its 104 choices, saves, and both served
V2 patchers remain unchanged. No emulator or hardware result is claimed.

## Actual held-model batch

The shared converter prepares fourteen actual handheld models for nineteen
donor item/state IDs: eight fans, the ordinary/golden shovel, and four axe
appearances. Complete source discovery follows item-to-kind, kind-to-shape/
animation, resource-pointer, and resource-type functions and their full tables.
It classifies 79 equipment records: nineteen static, twenty animated, and forty
using separate umbrella ownership. Thirteen rejected item IDs remain rejected.
The full donor inventory attaches these records to its existing identities.

`prepare_models` and `compile_models` are shared with the furniture path;
no second graphics converter or per-item integration script is introduced.
The batch retains all 25,888 artwork bytes, 334 vertices, and 244 triangles.
It is prepared-only: native selection/actions/animation, model ownership,
readers, acquisition, catalogue/collection, and save-profile integration remain.
The distinct prepared format is rejected by the furniture installer. Static
models are not substituted for skeletons, and ordinary tools are not new choices.

Generated outputs:

- `build/v3-handheld-static-prepared-02/art.json`, SHA-256
  `a7f97f5ef8ecf6c8c4df3b1961a1f38cf5974b5696e8e0c4904897a6cfd724e6`.
- `build/v3-handheld-static-prepared-02/inventory.json`, SHA-256
  `8af47296a224e1d524108e71b16c8526be4d2adc6811b468a76587a9d3434ab4`.
- `build/v3-handheld-source-02/donor-catalogue.json`, SHA-256
  `956a4d7305b97ab8489061613234c2a44f0db8f21cb49e6616d68f7f91d4942f`.

Eleven distinct focused checks pass: nine in `test_v3_handheld_items`, plus
the existing static-linker and complete-current-furniture-artwork checks.
Coverage includes full source functions/tables/relocations, correct wear-state
shapes, single-inventory identity/name binding, unsupported-selection and
installation rejection, and every model's complete texels, vertices, triangles,
material state, bounds, and native commands. Recompiling the two current
constant-model-sequence assets through the factored compiler reproduces their
complete objects and receipts. This is not an old-cartridge emulator replay.

The initial seven-test run passes six checks and finds an incorrect custom-
umbrella range in one new test: the actual donor accepts `2224..222B`, not
through `2230`. Production discovery already has the correct bounds. The
corrected focused check and two existing checks pass; two further CLI/type
rejection checks also pass. No inconclusive or failed game result is hidden.

The original and ABI-96 native equipment selector agree over all 396 bytes at
`808BD3F8..808BD583`, SHA-256
`3e1e9584685cef3dcb81e6fe99ef412ddc49fd4a8df74901f55b1742f234258b`.
It only accepts ordinary IDs `2200..2223`; new held graphics therefore require
actual player integration. The donor fan draw/action and player-animation
entries are identified in [the equipment spec](../../specs/V3_HANDHELD_ITEMS.md).
The current cartridge/ABI, 104 installed choices, saved format, and both served
patchers remain unchanged. No new ordinary gameplay or hardware claim is made.

## Parent display contexts

The donor's conversion flag has different values in ordinary room placement
and collection recording/checking. This changes the integration plan for forty
of the forty-eight extra display representations: tools, golden tools, fans,
pinwheels, and diaries keep their inventory IDs when dropped indoors. Their
furniture models are catalogue/collection representations. The eight balloons
use furniture IDs in both contexts. The earlier generic placement terminology
must not be interpreted as an unconditional room conversion.

`tools/v3_room_aliases.py` now verifies complete `mTG_room_put_proc`,
`mPr_SetItemCollectBit`, and `mSP_CollectCheck` implementations and their complete
relocation dependencies. It checks each conversion branch and flag-setting
instruction independently, and finds exactly four direct callers in the donor
executable: two room drops with flag one and two collection calls with flag zero.
Unknown consumers and changed code/relocations fail before item classification.
The call scan is cached against immutable complete source bytes to avoid repeating
an executable scan for each candidate; consumer verification remains uncached.

Format `AFV3-DONOR-ROOM-ALIASES-2` renames ambiguous `placement_inputs` to
`conversion_inputs` and generates actual `context_outputs` for every accepted
input. The seven worn-axe states map to one collection display, but each keeps
its wear-state ID on ordinary and bulk room drops. Inverse display conversion
returning an ordinary axe does not mean ordinary dropping repairs an axe.
The full donor inventory, furniture scan, and browser review records inherit
the correct context and pending reason from this one discovery implementation.

Eight focused tests pass, covering all 48 aliases/55 accepted inputs, context
outputs, ordinary/bulk call modes, complete code and relocation mutation,
unreviewed direct callers, worn-state retention, all 2,333 donor inventory
identities, and rejection of standalone furniture installation. Existing current
converted furniture still passes source/asset verification. The first run takes
69.483 seconds; after adding the immutable call-scan cache, the final-source run
passes in 26.649 seconds. These are host/source checks, not emulator gameplay.

Generated outputs:

- `build/v3-alias-contexts-01/inventory.json`, SHA-256
  `3593bdd48e5411d24e5bb0a712cced4517dd24c6eae0a7e56f2b69d3c4fc7ecf`.
- `build/v3-alias-contexts-01/donor-catalogue.json`, SHA-256
  `63f9d9f1e9d9b4b4fa1d1e5b8eff62039289cab3817b9278b4293ed1bcba3611`.

The scan retains 76 converter-supported and 166 review entries, with no new
fully eligible furniture. ABI 96, its pinned cartridge, 104 installed choices,
saved format 2, and both served V2 patchers remain unchanged. No emulator replay
is required for this source-discovery change. Next: actual parent inventory/
player actions/acquisition and context-correct catalogue/collection integration,
reusing the complete prepared artwork. Do not add a global tool-to-furniture
room conversion, duplicate original tools, or claim prepared graphics as usable
parent items.

## Shared native display aliases

ABI 96 replaces the conversion/readers/garment-roster lists with generated
relationships from the actual installed parent and display records. The same
metadata serves placement, pickup, full names, prices, ownership, footprints,
and garment resources. All three existing garments retain their actual profile
owners, selected dependencies, and native mannequin drawing. No item identity,
artwork, acquisition route, logical option, or saved format changes.

The existing furniture installer supplies `--refresh-runtime`, which updates
shared readers without reconverting artwork or installing another item batch.
Normal furniture installation uses the same adapter and reuses unchanged code.
The forward index consumes 240 verified unused bytes inside the existing
package; canonical display records use the last four bytes of their existing
sparse slots. Permanent RAM reservations and the entire DMA directory remain.
The compiled conversion, roster/bridge, and metadata readers are 260, 360, and
640 bytes, each within its checked original reservation.

Output: `build/v3-shared-display-runtime-01/`, pinned by the active build lock.

- ROM SHA-256: `76d148124f4f2e3f4b7157608feb69c9a329612f814f1dffde320287e75ba406`.
- Receipt SHA-256: `c601ec56e93a35e035589a0a5c7ec2835e88715ca233f7308d8fe258b280a50c`.
- UPS SHA-256: `fe0c878a2abb0590e169c3e4dc9c51133cdf90a5abf1741307895f5e2a7dad62`.

Six dedicated shared-alias checks pass, including sanitizer execution with
synthetic identities absent from the installed list, both footprint behaviours,
malformed/recursive/duplicate records, all rotations, strict argument handling,
selection rejection, complete unrelated-resource retention, current CRCs,
reconstruction, and repeat-install reuse. Twelve current-cartridge selection/
save-profile checks pass; all-selected reproduces the new cartridge and empty
selection reproduces stable V2. Two targeted legacy-wrapper host checks pass.
One host test invocation used the wrong class name; the correctly named targeted
check passes. No old-build native scenario is replayed.

The first current native attempt stops at the first metadata-reader call because
the fixture requests a direct upper-memory entry, which the debugger deliberately
forbids. The failure occurs before dispatch, not inside game code. The one
justified retry uses the normal installed low-memory native entries for names,
types, prices, and footprints. It passes 187 records and 177 assertions at
`build/v3-shared-display-native-02/results.json`, SHA-256
`f5faf5a000150db6fa27d984a146896460fd45234e7f5dd172c124e91b897856`.
All three pairs, four rotations, full-width conversion arguments, complete
English names, prices, native footprint cells, independent clothing/display
selection flags, original category fallbacks, restored profile, stack and buffer
guards, clean return, and shutdown pass. The existing scenario omits unchanged
HRA/feng-shui runs instead of replaying unrelated evidence.

The 104 installed choices, all artwork, complete save codec/profile, and saved
format 2 remain unchanged. Same-profile ABI-95/96 compatibility is expected in
both directions, without claiming a new ordinary save/restart or hardware run.
The original 48 extra donor aliases are still pending actual parent inventory/
gameplay integration. The bounded index supports one parent per display; worn-axe
placement states still need their many-input mapping. No new tool/fan/pinwheel
gameplay is claimed, and neither served V2 patcher changes.

The current-lock scan also completes at
`build/v3-shared-display-scan-01/inventory.json`: 76 converter-supported entries,
166 review entries, and no uninstalled fully eligible furniture. This adapter
does not misclassify prepared parent displays as newly usable imports.

## Indexed model-sequence conversion

Converter/installer revision 9 adds the shared `indexed-model-sequence` category.
The complete donor draw instructions, actual pointer-table relocations, bounded
index masks, and matrix-helper calls identify three draw shapes. The ordinary
and golden-tool callbacks use one normalised implementation with checked base
and conditional-index parameters. All create/move/destroy callbacks remain
verified no-ops. No item-specific model list, converter, or native scenario is
added.

The shared converter retains complete material-only and geometry-only lists in
their original order. It removes only intermediate final returns when joining
lists on the same command stream. Every original part retains its source offset,
size, hash, and joined position. The ordinary strict graphics parser then checks
the complete joined list. The fishing rods retain both their opaque sequence
and conditional translucent sequence in separate native profile slots.
No runtime callback, source resizing, model simplification, or new allocation
is introduced.

One unrestricted category conversion completes all 24 display models at
`build/v3-furniture-indexed-sequence-prepared-01/`: eight fans, eight pinwheels,
four ordinary tools, and four golden tools. They retain 46,832 bytes, 852 vertices,
and 566 triangles. Forty-four original source parts become 26 complete native
lists. All source-derived parent relationships and pending placement/pickup
requirements remain attached to the prepared records. They are not selectable
standalone furniture or completed parent-item gameplay.

- Art receipt SHA-256: `fca095571099332fc5c451a2e578bd26095418aba76bc5d23d06af27c73ad436`.
- Inventory SHA-256: `ca0ee62b46cfad05d5e012e10ca35ea180c024bb68c3966e99870ddab0b30680`.

The donor's display names differ from the actual parent name for two entries:
`gold pinwheel` represents `striped pinwheel`, and `bug net` represents `net`.
The parent source records retain the correct inventory names; these are not
additional items or grounds to replace the actual parent wording.

The focused donor/alias suite runs 26 tests: 24 pass, one palette-only prepared
test is inapplicable to this batch, and one deliberately damaged-pointer test
has an inconsistent fixture index. Updating the fixture's address index with its
modified relocation dictionary resolves the test setup error; its targeted
retry passes. A targeted extension of the prepared-artwork check also passes,
verifying all native opaque/translucent profile bindings and null runtime
callbacks. Across these runs, 25 distinct checks pass and one is skipped.

Checks cover every complete texture sample, vertex, triangle, material command,
source part and relocation, all actual selector rows, both conditional layers,
changed code/effects, missing table pointers, malformed/relocated returns,
out-of-range selectors, parent dependencies, and installer rejection of
prepared-only output. The current revision-7 installed batch still passes the
current complete source/asset checks; unchanged palette/static categories retain
their passing donor checks. No native emulator replay is needed for this
converter-only change.

The ABI-95 build lock, 104 installed choices, runtime, saved format, and both
served V2 patchers remain unchanged. Reuse this prepared batch for shared native
parent-item and room-conversion work; do not redo the artwork per item or claim
hardware/playability evidence from conversion checks.

## Parent-item and room-display discovery

Converter/installer revision 8 adds `tools/v3_room_aliases.py`, shared by the
full donor inventory, furniture pipeline, and browser review generator. Complete
donor placement, pickup, and both item/index functions are checked before their
actual range constants supply the records. No per-item identity list, converter,
installer, or scenario is added.

The six categories contain 48 room-display models: eight balloons, sixteen
diaries, eight fans, eight pinwheels, four golden tools, and four ordinary tools.
Four balloon models fall in `1xxx`; the other 44 entries occur in the `3xxx`
queue. Every record retains the official parent name/source hash, parent ID,
all four rotations, pickup ID, and the actual `no_convert_tools` condition.
Seven worn-axe inputs share the ordinary axe's model and return the ordinary
axe ID on pickup. That donor asymmetry is explicit, not seven new furnishings.

Aliases cannot install as standalone furniture, including through older asset
reports. Prepared artwork retains the parent relationship; unsupported graphics
keep a separate `conversion_reason`. The full 2,333-name donor inventory keeps
its original identities and links each parent/display pair; the worn states
also link to their canonical parent. Classification does not approve a native
identity, complete room conversion, or implement the parent's actual gameplay.
No new selectable option is claimed. Both served patchers remain V2.

Actual supplied-disc/N64 inventory generation succeeds at
`build/v3-room-alias-discovery-01/donor-catalogue.json`, SHA-256
`29b575ef4705816d90b70298628e47d05336e6edd3cc65fdfeda323142901363`.
The final current scan is `build/v3-room-alias-discovery-02/inventory.json`,
SHA-256 `771dd65a627aec167e3844ab64fd7ba9788cb2e1e40fae30c2a4cc1db2366f6b`.
It records 76 converter-supported and 166 review rows, with no supported new
uninstalled furniture. Those statuses describe converter eligibility, not the
larger installed set or completed gameplay. Of the 54 uninstalled entries in
the existing bulk-prepared batch, sixteen are diary aliases, thirteen retain
unknown acquisition, twelve require Tortimer gifts, six harvest acquisition,
five island acquisition, and two native identity review.

The focused run executes 44 tests: 41 pass, two optional prepared-asset tests
are skipped, and one assertion still expects the old diary acquisition reason.
Its correction verifies the actual parent-support rejection. The targeted run
passes seven tests, including the corrected assertion, the six alias tests,
and current revision-7 artwork acceptance through complete current validation.
Across both runs, 43 distinct checks pass and two are skipped. Coverage includes
all ranges/rotations, cross-range balloons, every parent name, worn-state
canonicalisation, changed complete code/helpers/relocations, full inventory
links and repeat annotation, shared scan/metadata rejection, rejection before
conversion creates files, installed-alias refusal, and generated browser review
data. Existing graphics/parser/material checks also pass. No emulator is replayed
for a discovery-only change.

The ABI-95 cartridge retains SHA-256
`01c7da7f945f02a4eebb1bafdc258b0485db5dd9240cf2254a51f3eefaccd68c`.
Its build lock, 104 installed choices, saved format, and runtime are unchanged.
The private browser interface export is not regenerated or served.
Next work is native parent identity/gameplay and shared placement/pickup support,
plus the still-missing graphics categories; these dependencies are not waived
by recognising the aliases.

## Constant model-sequence imports

Converter/installer revision 7 adds the shared `constant-model-sequence`
category. Complete compiled draw functions, actual model-pointer relocations,
and the one matrix-helper call establish fixed one-/three-model submission.
Null lifecycle slots are supported, but present lifecycle callbacks must be
complete no-ops. Extra code, calls, DMA callbacks, changed relocation pairs,
and effects are rejected. The same checked-code normaliser serves the existing
palette-fade category without changing its source receipts or runtime.

The converter links complete native lists in donor order with a generated
display list, recorded separately from the original model lists. The normal
opaque profile slot points to that sequence; generic rigs, animations, and the
callback pointer remain null. Lady Liberty retains all three material layers
on the opaque command stream, including their original internal material modes.
The tanabata palm retains its complete single list. Source scalars are unchanged.
No per-item integration script, runtime callback, scenario, or allocation is added.

The unrestricted category conversion at
`build/v3-furniture-static-sequence-assets-01/` discovers both eligible records:
Lady Liberty `3010` (6,736 bytes) and tanabata palm `3054` (4,416 bytes).
Together they retain 11,152 bytes, 248 vertices, and 179 triangles. Generated
links occupy 32 and 16 bytes respectively. The installer regenerates their
exact order, target addresses, bounds, hash, and normal profile binding.
Official names are credited in `translations/provenance.json`. Lady Liberty
uses the existing selected Gulliver reward category and remains non-orderable;
tanabata palm uses the donor event-stock list and actual catalogue policy.

The ABI-95 cartridge is
`build/v3-furniture-static-sequence-runtime-01/animal-forest-v3-asset-loader.z64`.
Automatic additions total 42. The offline composer contains 104 installed
choices: 81 furniture, three shirts, and twenty villagers. The model bank,
item-rendering code, saved format, and existing assets remain unchanged. Blob size
is 3,407,488 bytes, leaving 721,280 before English choices. The catalogue's
conservative memory requirement remains 280,384 of 280,704 bytes.

- ROM SHA-256: `01c7da7f945f02a4eebb1bafdc258b0485db5dd9240cf2254a51f3eefaccd68c`.
- UPS SHA-256: `2d893591aa7f6b49f5e27f1749cfc8a19ae51d8f998eb232143e4428aebdbaf3`.
- Build receipt SHA-256: `0f3991f6e27f59cd9698bbffe7dbe618b528e719773efd5906905b469bd75c9a`.
- Art receipt SHA-256: `aaf6e06e8d3cec9cc705d016dbf86e932703aa8e70a5fb066c12b1f3bb4006a8`.

The combined pipeline/composition suite runs 60 tests: 59 pass, and the
scoring-alias test is skipped because these two records need no alias. The
prepared palette batch is supplied to check that shared code normalisation
retains that category. Complete texels, vertices, triangles, material state,
ordered links, invalid source rejection, retained assets/code, names/credits,
stock/rewards, scoring, catalogue, profile subsets, and exact V2/no-import output
pass. The first silent current-build native run at
`build/v3-furniture-static-sequence-native-01/results.json` passes 124 records
and 85 assertions, SHA-256
`82491eb4dda46a75c9e32bfda38a32bef6d70a7d93b6e8add3d4753b014d31f9`.
It covers actual owner loading/relocation, both complete model transfers,
source framing, selected Gulliver rewards, event stock, acquisition/ownership,
restored state, and guards. Unchanged palette callback evidence is retained;
that scenario is not replayed. The emulator exits cleanly.

Ordinary appearance, interaction, complete catalogue construction, save/restart,
and hardware acceptance remain open. Saved format 2 is unchanged, but saves
containing these new identities must not load older builds or V2. Both served
patchers remain V2, and the private interface export is not regenerated.

The follow-up source review identifies the tools/fans/pinwheels/diaries as
room-display aliases of parent items, not independently acquirable furniture.
The donor forward function is `.text:0760E4`, 640 bytes, SHA-256
`5228a779089eca94c3f751a814e169f74ff085a57626673c86d7d789fadd6c66`;
the inverse is `.text:076364`, 664 bytes, SHA-256
`a948f3ad02dcf0d9f967363bb22203091447edbb416345498564bb18efda353e`.
Their source is `local/ac-decomp/src/game/m_room_type.c`. The native equivalents
in `upstream/af/src/code/m_room_type.c` lack those extra categories. Parent
identity classification and room-conversion implementation remain work; this
finding does not declare those aliases supported or discard their dependencies.

## Shared switchable-palette category

Converter/installer revision 6 discovers eight complete building-model callback
sets without an item allowlist. Normalised complete PowerPC implementations,
exact local call targets, all relocation pairs, both endpoint palettes, and
actual draw order identify one reusable behaviour. All three layers remain on
the donor's opaque command stream, retaining each list's own material mode.
Constant transparent colours survive; changing colours require opaque endpoints.
Roof-colour selection and clocked station models are not silently flattened.

One category conversion produces all eight objects at
`build/v3-furniture-palette-fade-prepared-02/`: 29,664 bytes, 555 vertices, and
346 triangles. Each generated 32-byte header describes its complete size,
palettes, and ordered model pointers. Source callbacks and dependencies are
recorded in each descriptor. Post model requires `ftr_listPostoffice`; police,
museum, market, Katrina's tent, shop, and tailor models have no identified
acquisition list. Those seven remain prepared-only, not selectable gameplay.

The ordinary converter/installer discovers igloo model `31A4` and installs its
complete 2,944-byte object, official name, price, preview, scoring, canonical
profile, and winter-camping reward metadata. There is no dedicated item script,
browser entry, or native scenario. The installed name is credited in the single
provenance catalogue. Automatic additions total 40; the offline composer supplies
102 installed choices: 79 furniture, three shirts, and twenty villagers.

The shared callback compiles to 988 bytes, including reserved table/layout holes,
inside the existing 1,024-byte tent allocation. `80483700` retains the legacy
tent table; `80483720` is the generated-layout table. Creation, float-0.1 movement,
destruction, and drawing are shared; an immutable compatibility layout preserves
the installed tent object unchanged. The current item loader is 1,920 of 2,048
reserved bytes. It accepts the category by callback contract, not by a new item
ID case, and validates the complete loaded header before bank registration.
Startup already invalidates this complete code range; no new startup range,
heap, saved format, or permanent reservation is needed.

ABI 94 is pinned at
`build/v3-furniture-palette-fade-runtime-02/animal-forest-v3-asset-loader.z64`.
The `runtime-01` and `runtime-02` ROMs have the same SHA-256; the second receipt
also binds the legacy tent's current shared code/table correctly. No second
emulator replay is needed for that receipt-only correction.

- ROM SHA-256: `8dcb481ce08eb7bacbc4661cb06ec910bf3ec41d3eb6d3bb753ab0ebcfb6e358`.
- UPS SHA-256: `65d3bda763c7949146fb08d71a0dad11f6bdc73f8d6a51a2bd4c461d0cd5f972`.
- Build receipt SHA-256: `cfc62b59db3b27343a4bba5ce768cd878b6b0c7d09bb439c79176888b8a4ca0d`.
- Complete callback reservation SHA-256: `d9d7f05fe744e0e74ae712e1f53e09bd8372dc69af08001de9c9e40e2b189d5c`.

Blob size is 3,396,336 bytes, leaving 732,432 before English choices. Catalogue
memory is 280,384 of 280,704 reserved bytes. Every previously installed model
retains its VROM and data; only the declared helper/code tables change.

The combined focused suite executes 56 tests. Fifty-five pass; one old blanket
assertion incorrectly disallows the intentional furniture-loader change. Its
targeted correction verifies the exact declared helper/public jumps and proves
the rest of the resident prefix unchanged. That corrected test and a new complete
code/layout/vtable-binding test both pass: 57 distinct checks covered. Sanitizers
execute the shared C with all eight converted objects and the legacy tent,
covering independent instances, mid-fade reversals, submitted-frame lifetime,
all model commands, every palette colour, malformed headers, crowded graphics
arenas, and actor/arena guards. Complete texel/vertex/triangle/material checks,
source rejection, official credit, catalogue/scoring, optional subsets, full
profile, exact no-import V2 output, and saved-profile rules also pass.

The initial native invocation mistakenly omits the required Expansion Pak and
uses the short default timeout; the emulator disconnects before the startup
assertion. It supplies no gameplay result. The one corrected invocation uses
the explicit eight-MiB setting, 180-second bound, and existing Xvfb executable.
`build/v3-furniture-palette-fade-native-02/results.json` completes 190 records with
114 passing assertions, SHA-256
`5ed7848e5a353f5e0fff69f47d85106a8463c32eeb68d18192de1a87b8d474c8`.
The shared representative scenario verifies actual new/legacy model DMA,
all four callbacks, both draw layouts, full interpolated colours, surviving
submitted palettes, actor preservation, full seasonal trade preparation,
acquisition/ownership, restoration, and guards. The emulator exits cleanly.

Ordinary appearance, interaction, full catalogue construction, save/restart,
and original-hardware acceptance remain unverified. Saved format 2 is unchanged,
but saves using the new item must not load earlier builds or V2. Both served
patchers remain V2; the recorded private UI export stays at its earlier snapshot.
Continue remaining shared acquisition/callback categories, not per-item scripts.

## Shared seasonal reward records

Converter/installer revision 5 installs snowy tree model `31A8`, snow bunny
`31D4`, and sleigh `31E0` through the unrestricted automatic conversion and shared
installer. Their complete models contain 13,728 bytes, 322 vertices, and 275
triangles. No item-specific converter, integration script, or native scenario is
added. The three names use the official donor records in the single provenance
catalogue. Automatic additions total 39. The offline composer contains 101
installed development options: 78 furniture, three shirts, and twenty villagers.

The complete ABI-93 cartridge is
`build/v3-furniture-camping-runtime-01/animal-forest-v3-asset-loader.z64`, pinned
by `config/v3-import-build.json`. Artwork is in
`build/v3-furniture-camping-assets-01/`. The catalogue has 514 furniture and 248
clothing rows. Conservative menu memory remains 280,320 of 280,704 bytes. Blob
growth is exactly the 13,728 artwork bytes, to 3,393,376 bytes, leaving 735,392
bytes before English choices. Existing owner allocations and model VROMs remain.

Winter acquisition uses actual `ftr_listKamakura`, donor list type 19. The donor
normal-trade function at `.text:122B8C` rolls `random(100) >= 90` in scene 31;
the separate 10% house-gift roll follows it. The native body lacks this winter
special-list roll. The shared trade adapter enables it only when winter imports
are selected; otherwise the original native body runs without another RNG draw.
Summer scene 35 retains its `>= 80` roll and list type 23. Carpet/wall donor
descriptors have neither special-list pointer and retain physical-A fallback.

Both seasons and Gulliver share the same source-derived item metadata. The ten
summer items no longer live in a hand-maintained runtime array. All seventeen
installed reward records carry their actual category in byte 27. The 948-byte
resident reader preserves rare/existing-item exclusions, the donor's small-list
duplicate allowance, and exhausted-profile fallback. It exports a checked count
entry at `80474EFC`, used without randomness to select winter's original-body
fallback. Code and guards fit the same `80474BB0..80474FEF` reservation.

The dependent camper suffix compiles to 1,152 bytes, down from 1,344, with 192
zero padding bytes. Its complete normal owner remains 20,736 bytes and its
relocation file remains 2,272 bytes, with 558 entries. The original prefix outside
the two entry hooks, native state, quest descriptors, callbacks, and shared
conversation allocation remain unchanged. Both relocated bases are checked.
Future automatic batches rebuild the suffix against the actual resident count
entry rather than assuming a stale compiled address.

HRA donor category 33 maps to native scoring category 3, using the same verified
412-point equivalence as summer category 37. The actual donor point table,
installed native weights, expanded evaluator patches, and all three native
five-bit consumers are checked. This changes scoring metadata only, not the
reward route. Native counters, point weights, and stack allocation stay intact.

- ROM SHA-256: `fe9b175801c5b1d7eb00b7ddf23d01d4fd164643cd01d9f2f6270d7e89f8598e`.
- UPS SHA-256: `e80813e4d538cfe5d117afbc07e6d2ca90d3dc1bd01704a092aa3e4c881669ad`.
- Build receipt SHA-256: `4973f7d2705be2c280c321d29b7c51daddfa2e708b949db5c6cfd6153a5ec1c3`.
- Art receipt SHA-256: `463e19c092235b63f907b12a8493e799e6d2561268c2b4c16a404f6a8ebb26cf`.
- Blob SHA-256: `f4301306b6245a24b59d62225f34ded2d44545b615699f1224eaf2ad43d2e91c`.
- Shared reward code SHA-256: `193943c60d253c8eacc76250d2960a902ff8e79d648efa10587a61b36fd430b1`.
- Trade owner SHA-256: `1a6571128da3e3c8171a347af5a829eb8acaf3246362c0fcb5b7a5074056037e`.
- Trade relocation SHA-256: `f4a0fffe3564208ccd2ec1e95d65c8703a7f5efc54c62bbfbccad237bb5246bd`.

The combined suite runs 52 tests: 51 pass and the optional prepared-only artifact
check is skipped. Sanitizers execute the actual shared selector and camper C,
including all ten summer identities, sparse profiles, both seasonal thresholds,
house override/empty-house fallthrough, duplicate/exclusion rules, and unchanged
ordinary trades. Complete source texels/vertices/triangles, material commands,
owner-prefix retention, fixed allocations, scoring equivalence/rejection,
catalogue, source credits, profile composition, and exact V2/no-import output pass.

The first silent native run completes all 162 records with 118 passing assertions
at `build/v3-furniture-camping-native-01/results.json`, SHA-256
`c2cff0b14ccb4f61b7b2e95c37715fbe4ac3cf52fee77a80c06c6c90c1cfc92d`.
It covers actual current owner loading/relocation, complete model DMA, readers,
preview, ownership, all three selected reward categories, sparse first/last
choices, no-selection native stock fallback, and complete seasonal trade calls.
Real RNG seed 7 produces the selected winter reward; disabling winter imports
executes the original native trade body. Seed 6 checks the unchanged summer
threshold through the shared reader. Input identity/slot, carpet/wall candidates,
pitfall mode, state restoration, guards, and clean shutdown pass. No native retry
is needed, and no old build is rerun.

These results do not establish ordinary camper conversations, handover animation,
GPU appearance, full catalogue construction, save/restart, or original-hardware
playtesting. Saved format 2 and permanent allocations remain unchanged, but saves
using the three new IDs must not load older builds or V2. Both served patchers
remain V2 pending the user's testing and explicit approval.

The post-scan at `build/v3-furniture-camping-post-scan-01/inventory.json` identifies
73 supported entries, all installed, and 169 review entries. This includes seven
already-installed summer models now recognised by the shared metadata path.
Fifty-four additional real models pass artwork preparation but retain their
actual requirements: 29 unidentified acquisition routes, twelve Tortimer gifts,
six harvest, five island, and two identity reviews. Sixteen diary models also
need diary gameplay. Continue shared acquisition/callback categories and the
remaining V3 gameplay/browser integration; prepared assets are not playable imports.

## Shared acquisition categories

Converter/installer revision 4 discovers, converts, and installs five further
objects without an item list: Arc De Triomphe `3014`, mermaid statue `301C`,
plate armor `3034`, Chinese lion `3050`, and festive flag `327C`. Complete artwork
totals 20,128 bytes, 487 vertices, and 401 triangles. The four souvenirs use the
actual `ftr_listJonason`; the flag uses `ftr_listTrain`. Every name has official
source attribution in `translations/provenance.json`. Automatic additions total
36, with 98 installed offline development options: 75 furniture, three shirts,
and twenty villagers.

The complete ABI-92 cartridge is
`build/v3-furniture-acquisition-runtime-01/animal-forest-v3-asset-loader.z64`, pinned
by `config/v3-import-build.json`. The artwork is in
`build/v3-furniture-acquisition-assets-01/`. The shared catalogue has 511 furniture
and 248 clothing rows, using a conservative 280,320 of 280,704 menu-pool bytes.
The blob is 3,379,648 bytes, leaving 749,120 bytes before English choices.

The train gift uses native list 4 and its catalogue-orderability mask. Gulliver
already exists in the N64 game: actor `A8`, owner `00958220`, RAM `80A97FB0`.
The original gift function at `80A983B4` selects native rare furniture; the donor
selects souvenir list type 12. Only its list argument at `80A983BC` and selection
call at `80A983D8` change. Native conversations, inventory checks, demo requests,
pocket insertion, and event completion remain. The complete owner and unchanged
304-byte relocation resource are checked. The 3,712-byte compressed owner moves
once to uncompressed blob storage before the three regenerable terminal owners;
future batches can update it in place without accumulating copies.

One shared 700-byte reader at `80474BC0` uses canonical item metadata byte 27 and
enabled profiles, not per-item switches. Encoded route `0C02` supplies donor
category 12 with native fallback 2. Selected souvenirs retain the donor's random
rare-item rejection; empty/all-excluded selections use the original native route.
Souvenirs stay non-orderable and absent from ordinary shop lists. The code and
guards fit the checked gap between preview data and accessory artwork. Startup
is 924 bytes and explicitly invalidates the helper's code range. No permanent
RAM reservation, item-record width, saved format, or original identity changes.
Saved format 2 remains; saves containing these new IDs must not load older builds
or V2. Ordinary cross-version save/restart compatibility is not newly claimed.

- ROM SHA-256: `ffe996df066c4bfb85f8a438ffef852691e1e2ea4a58bda81d3816c2f3b92252`.
- UPS SHA-256: `4bf6a6e7d039dc431f7e81b21198ad4f75cce98edf7c67f5e8ba0da7c797bb5d`.
- Build receipt SHA-256: `5c99e5d37918f14f0af315eeaf77e6899300acf1acd922e9de2b0a023521db3d`.
- Art receipt SHA-256: `d02e0c22a1badb5dd11afc4a76ad7613add19004499c4d713099a9b5557c6a77`.
- Blob SHA-256: `066fefd4aba0bf5026b1866fb70b6c2a1dfab18d5954b7feb19b562513042679`.

The combined focused suite runs 49 tests: 48 pass and the optional prepared-only
artifact test is skipped. Complete conversion/material checks cover the new
installed batch. Host sanitizers cover multiple reward categories, sparse and
disabled records, canonical identity validation, random endpoints/rejection,
rare-only fallback, and all seven native arguments. Cartridge checks verify the
complete owner with exactly two instruction changes, retained relocations,
non-orderability, repeated helper installation, safe terminal reuse, source text
credits, scoring, subsets, select-all, and exact import-free V2 composition.

The first native run passes 87 assertions in 104 records, then the harness rejects
a direct upper-memory helper call before executing it. This is the debugger's
explicit below-4-MiB proof restriction, not an observed game failure. Its evidence
is retained at `build/v3-furniture-acquisition-native-01/results.json`, SHA-256
`08637abdc036b6dc2ac34dd0f56be9bf40edd445c564232635eb4cec67c582d4`.
The test reuses its existing checked low-memory jump bridge; no cartridge change
or debugger-permission expansion is needed. The one corrected retry passes all
131 records with 104 assertions at
`build/v3-furniture-acquisition-native-02/results.json`, SHA-256
`81bd7f935c9c901e334b3b54ac5cb5b85727df1d7dcc611566f63e6065838dc8`.
Representatives are selected by category (`3034`, `301C`, `327C`), not separate
scenarios. Actual owner loading/relocation, installed call instructions, complete
model DMA, native readers/footprints, preview, stock/catalogue rules, acquisition,
ownership, two isolated sparse souvenir selections, empty-selection native reward
fallback, restored state, and all final guards pass.

These checks do not establish ordinary NPC conversations/gift animation, train
gift delivery, GPU appearance, full catalogue construction, save/restart, or
hardware playtesting. Both served patchers remain V2. Source may be pushed;
switching either patcher still requires the user's testing and explicit approval.

The post-scan at `build/v3-furniture-acquisition-post-scan-01/inventory.json`
contains 63 supported entries, all installed, and 179 review entries. Fifty-seven
uninstalled real models pass artwork preparation: 29 unidentified acquisition
routes, 12 Tortimer gifts, six harvest, five island, three winter-camper, and two
identity reviews. Diary gameplay remains an additional dependency for sixteen.
Continue shared acquisition and animated callback categories; do not restart
per-item conversion, installers, or tests. Prepared assets remain distinct from
completed playable imports.

## Direct-colour category and bulk prepared assets

Converter/installer revision 3 adds shared RGBA16 materials and prepares every
eligible uninstalled static model in one command:

```sh
python3 tools/v3_furniture_pipeline.py convert --assets-only \
  --output build/v3-furniture-all-static-prepared-02
```

The resulting 62 non-placeholder objects contain 211,136 bytes, 5,065 vertices,
and 3,720 triangles. The art receipt SHA-256 is
`0cf956288f7c323d5d0571fd9b8426fd93105a070d4bcb205a3fb1b06d2dffad`.
No individual item list or specialised graphics description is used. The shared
RGBA16 category includes Diver Dan `31D0`, retaining all 5,120 bytes, 107 vertices,
102 triangles, CI4 body materials, direct-colour helmet, and I4 reflection layer.
Its actual island acquisition remains required.

The supplied executable SHA-256 is
`e3166b15b810ff20397784fc83b2eb053db5d0c2a9e22ac2ead63a645881d150`.
Its complete 64-byte `fmtxtbl__5emu64` at `800AAFC0` has SHA-256
`7ae4019ff69d72ee09dd42b8b1c5a4c7a3a236d07aa238e2acdb93c97302fe30`.
The actual RGBA/16 entry is GX format 5, RGB5A3, not RGB565. The matching source
is `src/static/libforest/emu64/emu64.c` in the pinned donor checkout. Conversion
untile uses complete four-by-four blocks and native RGBA5551. Opaque and fully
transparent alpha are retained exactly; partial alpha fails instead of being
thresholded. Textures remain bounded to 2,048 bytes so switching back to CI4
cannot lose palettes in upper TMEM. Native 16-bit loads retain source scales,
wrapping, and shifts. No texture is resized or dropped.

Bulk discovery identifies sixteen entries using the same `iam_dummy` profile at
donor `.data:00092D6C`; fifteen have plausible item names. Both actual profile
tables select that placeholder. The converter now excludes this category by
its source pointer, not a maintained item-name/ID list. These entries retain
`asset_ready: false` and an explicit missing-artwork reason. An initial prepared
collection at `build/v3-furniture-all-static-prepared-01/` exposed the placeholders;
it is retained but not the current prepared collection. Unknown/dummy names also
remain excluded. A missing model in this English donor is not proof that the
item is unused in other editions.

The final collection retains actual missing dependencies:

| Dependency | Prepared objects |
| --- | ---: |
| No identified acquisition list | 29 |
| Tortimer holiday gifts | 12 |
| Harvest rewards | 6 |
| Island rewards | 5 |
| Gulliver rewards | 4 |
| Winter-camper rewards | 3 |
| Native identity/artwork correspondence | 2 |
| Train reward route | 1 |

Acquisition is not the only possible requirement: the sixteen diary display
models also need their actual diary gameplay. Prepared output is a separate
format and cannot pass installation. No prepared object is added to the offline
selection catalogue or counted as a completed playable import.

Forty-six focused pipeline/composition checks pass with the new direct-colour
artifact; the additional actual-executable format-table check and updated shared
placeholder-discovery check also pass. The shared complete-artwork and compiled-
material checks pass again against all 62 final prepared objects. Thus forty-seven
distinct focused checks pass across this batch. Independent comparisons cover
every source sample, vertex, triangle, model layer, material state, native load
format, palette mode, stride, texture scale, wrap, and shift. Partial-alpha and
incomplete-block rejection are covered without a new native scenario.

The current cartridge, build pin, 93 installed development options, saves, and
both served patchers remain unchanged. ABI-91 native results below are retained;
no old cartridge or unchanged emulator path is rerun. The newer converter source
does not relabel the ABI-91 build receipt as produced by revision 3. The scan still
has 58 supported and 184 review records; placeholder classification improves the
reason rather than hiding those records. Continue shared acquisition and animated
callback implementation using these prepared assets.

## Current shared intensity materials and resource reuse

The complete development cartridge is ABI 91:
`build/v3-furniture-intensity-runtime-01/animal-forest-v3-asset-loader.z64`.
The shared `intensity-materials` category discovers G logo `31E8` and bird bath
`3240`, retaining complete CI4/I4 textures, all opaque/translucent model layers,
reflection/water material state, and actual stock A acquisition. Their 6,880 bytes
contain all 202 vertices and 126 triangles. No item-specific model definition,
installer, runtime code, or native scenario is added. Automatic additions total
thirty-one; the offline composer contains 93 installed development options:
70 furniture, three shirts, and twenty villagers.

Converter revision 2 supports complete four-bit CI and intensity textures without
resizing. Pure I4 objects do not require a palette. Mixed lists select native
TLUT state at every actual format transition. Independent positive S/T scales,
four-bit shifts, wrapping, primitive/environment colours, and reviewed generated
reflection coordinates retain their source values. Unknown formats/state still
fail. The earlier CI4-only category remains available; `static-4bit` covers both.
The same category prepares miniature car `3094`: 7,104 bytes, 170 vertices,
and 98 triangles. Its acquisition is unresolved, so this prepared-only artifact
cannot be installed. Harvest mirror passes graphics discovery but still needs
the harvest acquisition adapter. No unsupported callback or acquisition is waived.

The installer reuses exactly the preceding automatic batch's terminal catalogue,
relocation, and shop resources. Complete hashes, DMA mappings, aligned contiguous
extents, zero padding, terminal boundary, resident boundary, every other DMA
resource, and all canonical profile extents are checked before reuse. Changed
receipts or live overlaps fail. The 64,496-byte prior tail starts at blob offset
3,284,400. Its retained prefix SHA-256 is
`0bb5766df6d034e6fca7acbed4efe8b7213db38808110f5ccac0df1663d429ac`.
New art precedes the regenerated owners; their fixed VROM identities and all
previous model VROMs remain unchanged. Reuse affects only the fresh output, not
input ROMs, previous builds, or saves. It prevents new redundant copies; it does
not compact older superseded data elsewhere in the retained prefix.

The catalogue has 506 furniture and 248 clothing rows. Conservative menu memory
remains 280,320 of 280,704 bytes. The import blob is 3,355,776 bytes, leaving
772,992 bytes before English choices. Growth is exactly the new 6,880 artwork
bytes, rather than another catalogue/shop copy. No runtime code or permanent
allocation grows. Saved format 2 remains; saves containing either new item must
not be loaded by older builds or V2. Forward ordinary cross-version reload is
not newly claimed. Both served patchers remain V2.

- ROM SHA-256: `ad194977b9083764c0efe8636614ba45d69b9370d6322514e2fd0b24aff2c1e3`.
- UPS SHA-256: `419588ce3dbf295f27ce96c8647f9042ed7111645fb84560f1d19f1aed89a2cd`.
- Build receipt SHA-256: `cbd63fe09ae8661bf4f9490e7f9ab3adcfb1e014c5d7932408322fce4203809b`.
- Art receipt SHA-256: `53659935e7ba271730ff1cb7b5cc5fe89ed290c9d40a3ab5af7975fa97c5e035`.
- Import blob SHA-256: `1c125a28cb24537db05e4f81e5703050d910a4542291586e5acbb71d1959383d`.
- Prepared car receipt SHA-256: `d9235377ce673ab0119b5cb025e5df3abc68d4f6cd06889b56b9ed3698966077`.

All forty-four focused pipeline/composition checks pass, with no skips. Material
tests independently decode compiled format, palette mode, stride, S/T scale,
wrapping, and shifts against source commands. Complete sample/vertex/triangle
checks also cover the prepared car. Palette-free I4, CI4 palette rejection,
mixed LUT transitions, changed tail data/receipts, and retained-profile overlap
are covered. Every previous complete model stays unchanged; tail reuse is
verified again from the new receipt. Existing sanitizer, stock/scoring,
official-text attribution, original-code, optional-subset, full, and exact V2
composition checks pass. All twenty current build-source hashes match the receipt.

The first silent native run passes 88 records with 68 assertions:
`build/v3-furniture-intensity-native-01/results.json`, SHA-256
`0153c9a523feb3316d5ce3d809f06e195e08c43a2149d0e0b4c7ad4dd51118cb`.
Both items represent distinct model-layer configurations. Complete native owner
loading/relocation, model DMA and bank tails, names/prices, footprint, catalogue
framing/fallbacks, relocated owners, stock, acquisition, ownership, restoration,
guards, and clean exit pass. No retry is needed. This is not GPU appearance,
full catalogue construction, ordinary gameplay, save/restart, or hardware proof.
No old cartridge is rerun.

The post-scan at `build/v3-furniture-intensity-post-scan-01/inventory.json` has
58 supported entries, all installed, and 184 review entries. These include
aliases and special imports, not a completion percentage. Continue shared
callback/acquisition categories and verified RGBA16 conversion; miniature car,
holiday gifts, island items, harvest items, and diaries retain their actual
unresolved dependencies.

## Square-furniture and double-bed batch

The complete development cartridge is ABI 90:
`build/v3-furniture-square-runtime-01/animal-forest-v3-asset-loader.z64`.
One `convert --category 2x2` batch discovers picnic table `32DC`, neutral corner
`333C`, red corner `3340`, and blue corner `3344`. The shared installer supplies
their complete models, profiles, names/prices, catalogue/scoring records, and
stock C/A/event/lottery routes respectively. No item-specific converter,
installer, gameplay code, or native scenario is added. The 15,568 bytes of
new artwork retain all 330 vertices and 182 triangles. Automatic additions
total twenty-nine; the offline composer has 91 installed development options:
68 furniture, three shirts, and twenty villagers.

Square collision category `5` and shape `5` remain distinct profile fields.
The existing four-cell reader supplies the same clockwise, upper-left-anchored
footprint in every rotation. The build rechecks the actual original/donor
footprint tables and the complete installed 1,020-byte reader at `80483000`,
SHA-256 `baf6957601fea4fc0829382bbc21604ade478479e9f0f6375c6e4d49e2f0317d`.
The three ring corners keep contact action `0x10` and the existing native
double-bed routines; they are not flattened into decorative furniture or
single beds. The complete checked room engine and expanded profile bindings
remain unchanged. No permanent allocation, saved structure, or native code
reservation grows.

The catalogue contains 504 furniture rows and retains 248 clothing rows.
Conservative menu memory is 280,320 of 280,704 bytes. The import blob is
3,348,896 bytes, leaving 779,872 bytes before English choices. Saved format 2
remains, but saves containing the new four items require this build or a
compatible profile superset; older builds and V2 must not load those saves.
Ordinary cross-version save/reload is not newly claimed. Neither served patcher
changes.

- ROM SHA-256: `91be4e2ccd1fc9bb3be77f16c11eff74a7b387582475deed575d3a316ea02277`.
- UPS SHA-256: `935651090a5a5b62ac99ddb37a9871951b8b3eaa9813bca90e3bfb06603bc0cd`.
- Build receipt SHA-256: `bdbeb14058d69b704de14865b5b2bb47048636345d34eccb76887265fcbffdfe`.
- Art receipt SHA-256: `bec4490afaca0b848c3d8fb4b4d5bd5e5a22a3773e1befb034ba2847f4291d74`.
- Import blob SHA-256: `02b36fbc1e93a002ca5c3f9db66f46c260aae3853b24d8a7eb9b291562b0eaa5`.

Thirty-eight focused pipeline/composition checks pass; one optional prepared-
assets check is not requested. New checks cover shared square/double-bed
discovery, intact donor scalars, unknown collision rejection, changed native
reader rejection, and the existing four-cell host fixture under address and
undefined-behaviour sanitizers. Complete texture/vertex/material conversion,
installed records, official text credits, retained native code, stock/scoring,
and optional-profile composition also pass.

The first silent native run passes 180 records with 158 assertions:
`build/v3-furniture-square-native-01/results.json`, SHA-256
`208149336a2def36a3647f23eb8aa1bc3450527ef25c89e93824c020c297ba9e`.
All four items are representatives because their stock categories differ.
Their complete model DMA, names/prices, four-cell footprints in all rotations,
catalogue framing/eligibility, stock, acquisition, ownership, restoration,
and guards pass. One double-bed representative exercises the actual native
head-direction and both side-position functions in every rotation, retaining
the wider side span and half-cell pillow offset. Inactive-bed rejection and
complete temporary-actor preservation also pass. No retry is needed.

The shared probe checks bed geometry once per changed contact category and
tests imported chair sounds for the new batch rather than every previous
chair. Full source audio/code checks remain in the build contract; earlier
passing native evidence remains recorded. No old candidate is rerun.
These checks do not establish ordinary bed entry/rolling/exit, complete room
appearance, catalogue construction, save/restart, or original-hardware play.

The post-scan has 55 supported entries, all installed, and 187 review entries.
It includes aliases and special imports and is not a completion percentage.
The next shared storage improvement is safe reuse of the regenerated
catalogue/relocation/shop tail (64,496 bytes in this build), preserving every
retained resource and previous output. Shared mixed CI4/I4 material handling
also remains: miniature car, G logo, and bird bath have I4 layers, while Diver
Dan additionally has RGBA16. Keep acquisition/callback dependencies explicit.

## Single-bed batch

The complete development cartridge is ABI 89:
`build/v3-furniture-bed-runtime-02/animal-forest-v3-asset-loader.z64`.
The shared `single-bed` category discovers and installs hammock `329C` and
weight bench `3358` without per-item model definitions, installers, gameplay
code, or native scenarios. Both retain stock C, their complete two-layer
models, two-cell footprints, donor profile scalars, official names, prices,
scoring, and preview framing. Total new art is 8,416 bytes, 196 vertices, and
108 triangles. The automatic pipeline has installed twenty-five additions;
the offline composer contains 87 development options: 64 furniture, three
shirts, and twenty villagers.

The category uses native contact action `08`, not a decorative approximation.
The checked native room engine already handles bed positioning, contact, entry,
and exit through the expanded profile table. The build verifies the complete
owner SHA-256 `ca540a6f48fa15fb8bfad4d36abf77bb3d318799732d965f278063207f64b74a`
and the four reviewed profile bindings at `809404D0/809404DC`,
`809407BC/809407C8`, `80940FA8/80940FB8`, and `809419D0/809419E0`, all addressing
`80470010`. No gameplay code or permanent memory is added. Native timing and
player animations remain unchanged.

Beach chair and harvest bed pass this category's model/dependency discovery
but are not installed. Their actual `ftr_listIsland` and `ftr_listHarvest`
acquisition routes still need shared adapters. Their presence in a supported
bed category does not waive those requirements or replace them with shop stock.

The catalogue contains 500 furniture rows and retains all 248 clothing rows.
Conservative menu memory is 280,320 of 280,704 reserved bytes. The import blob
is 3,268,832 bytes, leaving 859,936 bytes before English choices. Model-bank
allocations and saved format 2 are unchanged. Saves containing the new items
must not load in older cartridges or V2. Ordinary cross-version reload is not
newly claimed; both served patchers remain V2.

- ROM SHA-256: `e460ec11ba2eb2abebcc7aa15c8060728a5c986ddfb0c3f67078689c1a0d9dff`.
- UPS SHA-256: `7020d093e96bb510a36e46383bb715d7a8b4e5757f4eda476bfc65636a478232`.
- Build receipt SHA-256: `ad8cc4af55fae0da16115b5d251ff6a07372b84abcbb70bdf734278b3d2ffb16`.
- Art receipt SHA-256: `56d48e0b812717e4368abb986813d89223920e896ac9b4152fc96d52a8b9205a`.
- Import blob SHA-256: `0dbf4c68f6f5bc46c105887be5d268816cbcff90ecc26c1b5d3af832cc5d489b`.

Thirty-five focused pipeline/composition checks pass; the optional prepared-
assets check is not requested in this batch. They include complete conversion,
source credits, shared category discovery with acquisition rejection, changed
native-engine/table-binding rejection, complete installation, retained native
code, stock, scoring, and selected-profile composition.

The first silent native run passes 112 records with 93 assertions:
`build/v3-furniture-bed-native-01/results.json`, SHA-256
`6fc9749bd4f071050ee9f506c3347f13c88c7a4ead97f6c7dce110f00804fe9f`.
The shared selector chooses the larger weight-bench model to represent the
same stock, footprint, material layers, preview, sound, and bed category.
Actual head-direction (`80940304`), foot-side (`80940498`), and pillow-side
(`80940784`) functions pass all four rotations through the installed imported
profile. Inactive beds return no positions; the complete temporary actor stays
unchanged. Complete owner loading, model DMA, shared item/catalogue/stock
readers, acquisition, ownership, restoration, and guards also pass. No retry
is needed. The final recipe receipt refreshes a source comment and reproduces
the exact native-tested cartridge; no emulator rerun follows that comment edit.

These checks do not establish ordinary climbing onto/leaving a bed, full
catalogue construction, GPU appearance, save/restart, or original-hardware
behaviour. Continue shared callback, graphics, and acquisition categories;
use the same representative batch scenario rather than adding an item scenario.
The post-scan at `build/v3-furniture-bed-post-scan-01/inventory.json` has 51
supported entries, all installed, and 191 review entries. Those entries include
aliases and special imports; these counts are not a completion percentage.

## Material and catalogue-framing batch

The complete development cartridge is ABI 88:
`build/v3-furniture-material-preview-runtime-02/animal-forest-v3-asset-loader.z64`.
Shared discovery installs bug zapper `3234`, coffee machine `323C`, candy machine
`3254`, and steam roller `328C`, with 15,104 complete object bytes, 258 vertices,
and 153 triangles. The first two retain stock A, candy machine retains stock C,
and steam roller retains event acquisition and its two-cell footprint. All names
have official-source credits in the single provenance catalogue. Automatic
additions total twenty-three; the offline composer contains 85 installed
development options: 62 furniture, three shirts, and twenty villagers.

All four use the same unlit texture/primitive material command. Its two cycles
pass texture RGBA through, then multiply RGB by primitive colour while retaining
alpha. The symbolic native `gsDPSetCombineLERP` compiles to donor words
`FCFFFE60 FFFCF3F8`; complete compiled material/geometry checks pass. The coffee
machine's environment-lighting flag is also retained. There is no item-specific
graphics description or installer.

Catalogue framing is now source-indexed for all 62 installed furnishings. Byte
26 of the existing 32-byte item record stores the donor framing index plus one.
The complete 328-byte/41-entry table and its guards occupy
`80474A30..80474B9F`, with table data at `80474A40`. It fits after the placement
table and before accessory artwork, without increasing any permanent allocation.
The general native helper changes only model Y and scale after native
construction; clothing aliases keep their existing presentation. It replaces
the installed per-item Western, bike, and campfire overrides. The steam roller
and campfire both obtain the donor's mode 19 (`0.86`, `-3.0`) through records.
Disabled, absent, invalid-selector, and original-native cases retain their input.

The complete catalogue suffix is 3,408 bytes, and its 498 furniture rows retain
all 248 clothing rows. Conservative menu memory is 280,256 of 280,704 reserved
bytes. The import blob is 3,195,952 bytes, with 932,816 bytes before English
choices. Model-bank allocation and saved format 2 are unchanged. The required
saved profile is a superset of ABI 87. Saves using the four new items must not
be loaded in older builds or V2; ordinary cross-version reload is not newly
claimed. Both served patchers remain V2.

- ROM SHA-256: `5644a08760b63a396747adf2d5926340255667309152c7d9d0e4290263945319`.
- UPS SHA-256: `ed9c1c5b54e57d7414cc6b1f2b4dca39e9b5e284925222b999f54249e809c74e`.
- Build receipt SHA-256: `c8181c0ccb92625fb8d031317f8b83df5be29d9a09a5e5bddff64340105f5cfe`.
- Art receipt SHA-256: `e0e93177e8b011b6f73d571ce6e805317f4d13797adf03eefd2ee70ba4598a57`.
- Import blob SHA-256: `76032e58970f9e296b3d8054b09220662ef571a20339b345034ca9e8a172521a`.
- Preview table SHA-256: `fa6592f8af1ebb2ddb984e59b39649c36afeb85bdd4f9127dbcae26ba62a2a98`.
- Preview reservation SHA-256: `44d06f4df2fca8da04bb6c6a4ee48f131d9a2e1d22dce012027f077cb32b71bb`.

Thirty-four focused pipeline/composition checks pass against this candidate
before promoting its lock. They include the shared native combiner expression,
complete resource/geometry comparisons, all source-derived framing selectors,
guarded repeat-batch reuse, source credits, installed metadata, and selected/save
profile composition. The catalogue's host address/undefined-behaviour checks
cover the complete framing-table range and invalid boundaries. The fixture
preserves the distinct clothing-display stock route when enabling the full
catalogue wrapper. An initial build catches the old seating helper's reserved-
byte check; the corrected check recognises byte 26 as framing metadata while
retaining zero checks on bytes 27–31. That partial build has no promoted ROM.

The first silent native run passes 146 records with 124 assertions:
`build/v3-furniture-material-preview-native-01/results.json`, SHA-256
`3ae031b8643fbcd3a029b4387e2a7e5fde499f4b1157e4d687878e159a20b777`.
The shared representative selector covers all four new records because their
stock, footprint, preview, and lighting categories differ. Actual owner loads,
complete model DMA, source framing with every other preview field unchanged,
disabled/invalid/native framing fallbacks, names, prices, rotations, stock,
acquisition, ownership, restoration, and guards pass. The emulator exits cleanly;
no native retry is needed. This is not proof of full catalogue initialization,
GPU appearance, ordinary gameplay/save-restart, or original-hardware execution.

The post-scan in `build/v3-furniture-material-preview-post-scan-01/inventory.json`
has 49 supported entries, all installed, and 193 entries needing review. That
inventory includes aliases and unused records and is not a remaining-content
percentage. Continue shared behaviour/format/acquisition categories.

## Shared identity-indexed model and palette conversion

The converter handles the complete nine-entry flower selector through one
`indexed-static-model-palette` rule. No item list, separate graphics converter,
installer, runtime helper, or native test scenario is added. The source's fixed
actor identity selects two opaque models and a palette. Both models retain
their full material/geometry commands, and their segment-eight palette loads
become direct loads of the selected native palette.

The checked donor has `fNFL_dw` at `.text:2D0768`, 192 bytes, SHA-256
`612998bdab7cb941114e08d66db7100ded74894f8c1ccfdbdffe4bb9fbb44917`.
Its four code relocations bind the save/restore helpers and the complete
`fNFL_model_data` table at `.data:092BE0`, 108 bytes. The actual instructions
subtract runtime index 1246 and multiply by a twelve-byte row stride. All three
lifecycle callbacks are four-byte returns; the DMA slot is null. The verifier
checks those facts and dependencies, not merely function names. The donor room
renderer's `aMR_DrawRegistModel` uses the same current matrix and opaque0/opaque1
order; the special callback adds only the constant palette selection. Catalogue
rendering also retains that model order. Native execution of these new assets
is not yet claimed.

One command prepares all nine variants:

```sh
python3 tools/v3_furniture_pipeline.py convert --assets-only \
  --category indexed-static-model-palette \
  --output build/v3-furniture-indexed-palette-art-01
```

The output contains 19,152 object bytes, 555 vertices, and 288 triangles across
all three pansies, three cosmos, and three tulips (`3378..3398`). Each object has
its actual official donor name/source index and its selected palette. The
complete prepared receipt SHA-256 is
`6e173ac1c9c1889389779d93b63fd7ac6589d5644bd6d0afa9387dfe72711e83`;
the inventory SHA-256 is
`20df1500755bc29f67ffcb923f84a34244430e79a758bc718eb6e89b4e61f522`.
Individual object/resource hashes are in that receipt.

All nine remain **prepared, not installed**. The donor's
`ftr_listEventPresentChumon` contains these nine flowers, two tree models, and
weed model. `mCL_furniture_init` and `mMpswd_check_present_user` treat this category as
orderable/password-eligible, but that does not establish a working native initial
acquisition route. The N64 has no matching stock-list slot. Do not put the objects
in ordinary shop stock or claim acquisition is complete. Shared acquisition and
catalogue handling must cover the twelve source records together.

The actual initial acquisition comes from `mSC_trophy_item`, not a random shop
list. Its 244-byte donor function at `.text:07C31C` has SHA-256
`48321dd6e22de9f11751b89f9557c5be837f142f70b36bbe5cbd8ff933ea8234`.
The 56-byte `soncho_item_table$582` at `.data:010714` has SHA-256
`2bf4a655de09672b8c202cad690e6595cae1859656b5f379e9b9347822ea2fd9`.

| Donor event | Source reward rule |
| --- | --- |
| Founder's Day, index 1 | Weed model `3080` |
| Cherry Blossom Festival, index 7 | Pink tree model `307C` |
| Nature Day, index 9 | Tree model `3078` |
| Groundhog Day, index 13 | Uniform random runtime index `1246 + RANDOM(9)` |

The gift list at `.data:698630` is 26 bytes including its terminator, SHA-256
`07391eb07d67a5f92dfcd3300ac0586bc3908bb470e8ff2257cd7e39e1a8040f`.
`aES2_talk_before_give` checks pocket space; `aES2_talk_give` performs the normal
handover, inserts the actual item, and records the event trophy. Their complete
function hashes are respectively
`a3129746c1e60b877ecd74ae82f6861db8ef00509f0f15bfebe097324683bacc`
and `adb99cc52df75acb980d5f865c3c20f9778e223011b86d6f0b00d59aeec0d699`.
This requires the donor Tortimer event actor, English conversations, calendar
integration, selected-reward eligibility, and reviewed per-player trophy/calendar
persistence; the N64 actor/profile inventory has no corresponding Tortimer
implementation. Donor private-data offsets are not native saved fields. Implement
the shared event route without turning these rewards into ordinary stock, and
continue unrelated conversion categories while that larger dependency is open.

Thirty-two focused pipeline/composition checks pass with
`V3_FURNITURE_PREPARED_ART=build/v3-furniture-indexed-palette-art-01`. The reused
asset checks compare complete texels, vertices, triangles, materials, and palette
load targets. New checks cover every actual selector row, independent relocation
resolution, unknown/changed callback rejection, extra DMA effects, bad indices,
ambiguous palette bindings, and refusal to install prepared-only output. No
native emulator run is repeated: ABI 87, the ROM, import lock, saves, and both
served V2 patchers are unchanged. The 81 installed options do not include these
nine prepared objects.

Callback inspection also identifies useful next shared categories: fifteen
station models with one animated clock/skeleton implementation; eight building
models using palette-fade callbacks; tool, fan, and pinwheel display selectors;
and move-only sound callbacks. These are category candidates, not approved static
substitutions. In particular, station clock hands and animated parts must remain.

## Collision and placement categories

The collision/placement cartridge is ABI 87:
`build/v3-furniture-placement-runtime-01/animal-forest-v3-asset-loader.z64`.
The same importer installs grass model `30E8`, dirt model `30F0`, and boxing
mat `3348`, retaining all 2,768 object bytes, 44 vertices, 24 triangles, textures,
and the donor's `0010` no-collision flag. Official name credits are in the single
provenance catalogue. Automatic additions total nineteen; the offline composer
contains 81 installed options: 58 furniture, three shirts, and twenty villagers.

Inspection identifies five native readers still indexing the original 947-entry
placement-layer table with imported indices. This can read unrelated data and
lose surface behaviour. The shared fix preserves the original prefix and adds
source-derived rows for every installed furnishing and all three clothing display
aliases. Four imported surfaces (teacher's desk, orange box, chess table, and
ringside table) and five surface-placeable objects (garden gnome, cow skull,
lantern, Luigi trophy, and Mario trophy) now have explicit correct categories.
Other imported furniture has category zero. No item-specific runtime branch is
added. The complete native collision-registration routine is unchanged except
for its corrected table address, preserving its ordinary-room/shop distinction.

The 2,051-entry table and guards occupy `804741F0..80474A1F` in the unused
registry-to-artwork gap. The five actual HI/LO pairs are at
`8093825C/80938268`, `80943878/8094387C`, `80943978/8094397C`,
`80943A34/80943A40`, and `809462C8/809462D4`. Ten obsolete relocations are
removed. All other native owner bytes and accessory records/artwork remain.
There is no added executable code, resident allocation, or saved-format growth.

- ROM SHA-256: `004a1173c51cdea009c3a5e291067469675d40809002bf8fd41d99f28f671c1d`.
- UPS SHA-256: `df73ad1e2f7c8f010bd6016356a2d03b333d4295de4bb8d04c44cc286906c999`.
- Receipt SHA-256: `64805f9215d264303347fc40842f5fa6b15d2c549453f3e6c5b7ac654b1e85ec`.
- Import-resource SHA-256: `c328b130c6bb338de7582f24ceb6f3b741769427477e5c237a7a9b5c53665a58`.
- Placement-table SHA-256: `9f6d51793f058d2b8ebe8952a4369fd4a7b5d48eb19c9998333b885aac89ef01`.
- Native owner SHA-256: `ca540a6f48fa15fb8bfad4d36abf77bb3d318799732d965f278063207f64b74a`.
- Relocation SHA-256: `c97bc9e48c97a6830145218f5fcdcaa664a7611167b2f013bc93d75f4e493bc5`.

The blob contains 3,116,400 bytes, with 1,012,368 bytes remaining before English
choices. The catalogue has 494 furniture rows and 248 clothing rows; conservative
menu memory remains 280,384 of 280,704 reserved bytes. All 28 focused pipeline/
composition tests pass. They include every converted texel/vertex/triangle,
unknown interaction/placement rejection, source-derived table entries, all five
retargeted references, complete relocation comparisons at two load addresses,
unrelated-owner retention, repeat-batch reuse, and save-profile composition.
The first silent native run passes 125 records and 107 assertions, including
the complete placement table/guards, native owner loading/relocation, actual
no-collision registration for all three new objects, complete model DMA,
one-/two-cell rotated footprints, names, prices, stock, catalogue eligibility,
acquisition, ownership, restored state, and guards. The existing four sound
routes also pass. The emulator exits cleanly; no native setup retry is needed.
Results are in `build/v3-furniture-placement-native-01/results.json`, SHA-256
`5757a4b7580348303195455ae9c1b5b17e425a3bafa18cfc19c549673a7e733a`.

Ordinary room appearance, table use, walking across the collision-less objects,
and save/restart remain unverified. Saved format 2 is unchanged and the profile
extends ABI 86; no ordinary cross-version reload is newly claimed. Saves using
the three new objects must not be loaded in older builds or V2. Neither served
patcher changes.

## Shared seating category

The seating-category cartridge is ABI 86:
`build/v3-furniture-seats-runtime-02/animal-forest-v3-asset-loader.z64`.
The automatic pipeline adds lawn chair `324C` and teacher's chair `3288`
without an item definition, dedicated installer, or separate native scenario.
Their 7,872 bytes retain all 163 vertices and 81 triangles. This brings the
automatic additions to sixteen and the offline composer to 78 installed options
(55 furniture, three shirts, and twenty villagers).

The category extension also supplies the donor's correct soft-chair sounds for
lawn chair and hard-chair sounds for teacher's chair, lefty desk, and righty desk.
Byte 25 of each existing item record stores its source-derived category. All
installed furniture is populated from the actual donor table, including entries
with no action sound. No per-item runtime branch or separate audio import is
needed. Full sound programs, timing, complete instruments, envelopes, samples,
loops, and predictors match native audio; matching sound numbers alone are not
the verification. Original native items retain their original reader body.

The helper is 208 bytes at `80483D00`, before the fire vtables at `80483FC0`.
The installer verifies the existing fire code and empty intervening bytes;
linker limits also prevent shared item/tent/fire/behaviour overlap. The helper
uses a bounded 32-byte stack frame and no new permanent RAM or audio resources.
The catalogue contains 491 furniture rows and 248 clothing rows. The resource is
3,049,104 bytes, with 1,079,664 bytes remaining before the English-choice region.

- ROM SHA-256: `e6f334027c352039fededafe8672d7ff480b5234bad914646b4beeffad00d1ab`.
- UPS SHA-256: `b20ac5cf1f0bc6452a3ec38b76d15ab76d5e215e9112fd81d0c912af42ce6d40`.
- Receipt SHA-256: `b3f9a540d3426a87dad66cc7eec0732fef38283b72de4fc312b87fd75eee4b54`.
- Import-resource SHA-256: `2963fa39c0886ac784b3b6ed842e8dc6a8c88cef65c7b4909868a7debbeefff5`.
- Native result: `build/v3-furniture-seats-native-01/results.json`, SHA-256
  `33895a6070a9e352a7fc663f22c4fc5b1e45d84eaed84919005199c897733f4c`.

All 26 focused pipeline/composition checks pass. The shared sound implementation
passes address/undefined-behaviour sanitizers for original delegation, complete
import index bounds, modes, categories, metadata identity, and disabled records.
The first silent native run passes 88 records and 73 assertions: complete helper
loading, original fallbacks, both modes for all four imported sound routes,
disabled-profile rejection, invalid indices/modes, complete chair model DMA,
names, prices, stock, catalogue eligibility, acquisition, ownership, restoration,
and guards. No audio is played through the user's speakers/headphones.

The initial installer attempt stops at a missing shared compiler-entry mapping;
the mapping is added and the completed build passes. There is no native setup
retry. Ordinary sitting, audible playback, GPU appearance, transactions, and
save/restart are not established by these component checks. Saved format 2 is
unchanged; the new profile is a superset of ABI 85, but ordinary cross-version
reload is not newly tested. Saves containing the new chairs must not be loaded
in an older cartridge or V2. Neither served patcher changes.

## Initial automatic batch

Source revision `7149f9c` discovers and installs fourteen new items in one
batch, without an item-specific converter definition, stock/catalogue switch,
installer, or test scenario. The complete command is:

```sh
python3 tools/v3_furniture_pipeline.py import \
  --base-lock tests/fixtures/v3-furniture-pipeline-base.json \
  --output build/furniture-reproduction
```

The recorded run used the same pinned input through the current-build lock
before that lock was promoted. The final output is
`build/v3-auto-furniture-final-01/animal-forest-v3-asset-loader.z64`, ABI 85.
The one-command output in `build/v3-auto-furniture-02/cartridge/` has the same
complete ROM and patch hashes. The final rebuild adds reusable predecessor/art
locations to the receipt; it does not change any cartridge bytes or require
another native run. The folder name identifies this implementation batch,
not a finished V3 release.

- ROM SHA-256: `571e849108cf36983c7129a38d08bfc3b47dd71db5c4347cfe16b7425b1ed35c`.
- UPS SHA-256: `d9283d2908b779694ee584889d5f1559523159bbc3f8ae4512d368bf11d664f5`.
- Final build receipt SHA-256: `9f1df24e3e98f4972afc7c38720f91947afe6417082a79d13bdeee3959b80166`.
- Appended import resource: 2,976,720 bytes, ending at VROM `024D6BD0`,
  leaving 1,152,048 bytes before the reserved English-choice resource.
- Models: 50,064 bytes, 1,038 vertices, and 570 triangles, with complete textures
  and palettes. No donor artwork is truncated or replaced with a placeholder.
- Catalogue: 489 furniture rows and 248 clothing rows. The compiled suffix is
  3,424 bytes; conservative menu memory is 280,384 of 280,704 reserved bytes.
- No additional permanent RAM, model-bank allocation, or saved-format growth.

Imported records: track model `30EC`, train car model `30F4`, orange box `30F8`,
merge sign `31EC`, radiator `3248`, chess table `3250`, cement mixer `325C`,
jackhammer `3260`, potbelly stove `326C`, flip-top desk `3278`, Luigi trophy
`32C8`, Mario trophy `32CC`, boxing barricade `3338`, and ringside table `334C`.
Names have generated official-source entries in `translations/provenance.json`.

The offline composer resolves 76 installed development options. The concrete
subset `build/v3-optional-auto-furniture-01/` selects radiator, Mario trophy,
and ringside table without other new furniture, ROM SHA-256
`a973cee3a9e2f24adca32dd95e766c6a94e5d965da52805a8562aff558ab6453`.
Empty selection reproduces V2; all selection reproduces the complete cartridge.
Neither served patcher changes, and this is not a public-release handoff.

### Initial batch verification

Seven shared format/donor tests, five current-cartridge tests, and twelve
composition tests pass: **24 focused tests**. Checks cover every new texel,
vertex, and triangle, actual source relocations, retained material commands,
complete installed assets/profiles, official names, stock membership, scoring,
catalogue order, ROM checksums, full/empty/subset selection, and saved-profile
requirements. The shared catalogue reader passes address/undefined-behaviour
sanitizers across its bounded index/list/category/rotation cases.

The initial native attempt stops before emulation because `Xvfb` is not on PATH.
The one corrected retry explicitly uses the existing executable:

```sh
python3 tools/emulator_smoke.py \
  --rom build/v3-auto-furniture-final-01/animal-forest-v3-asset-loader.z64 \
  --output build/furniture-native-reproduction \
  --scenario tests/scenarios/v3_furniture_batch.json \
  --xvfb /home/discordian/Games/OpenRSC/headless/vendor/usr/bin/Xvfb \
  --seconds 180 --expansion-pak --no-initial-screenshot
```

`build/v3-auto-furniture-native-02/results.json` passes **148 records and 133
assertions**, SHA-256
`d97bcd43bf3a6665c0e63f1d87a3e9cb99b7500d5c394acb6887e40f286e44f7`.
The manifest chooses train car model, Luigi trophy, Mario trophy, flip-top desk,
jackhammer, and ringside table to cover A/B/C, event, lottery, one-/two-cell,
and model-layer categories. Actual owner loading/relocation, names, prices,
rotated footprints, complete upper-memory model DMA and untouched tails, bank
assignment, stock membership, catalogue eligibility/rejection, acquisition,
saved ownership, restored state, and guards pass. The emulator exits cleanly.
No existing save is used and no test FlashRAM write is requested.

Ordinary room appearance, GPU rendering of these new models, transactions,
interactions, and save/restart remain unverified. The preceding full profile is
a subset of this profile; the codec accepts equal/superset requirements, but
ordinary cross-version reload is not newly tested. Do not load saves using the
new items in an older build or V2.

## Category queue

The donor worksheet contains 242 canonical 3xxx entries. This converter supports
43 under its present complete category rules, all installed. The post-install
scan identifies no remaining supported,
uninstalled entries. This is **not** a whole-project completeness percentage.
The other 199 entries include already-installed special adapters and explicit
identity/unused cases as well as genuinely missing imports.

Continue through shared feature categories, not individual item queues:

1. Shared callback families: 102 uninstalled entries stop on custom callback
   tables. Classify the actual callback/dependency patterns and implement shared
   behaviour adapters; never discard callbacks to fit the static category.
2. The supported `0010` flag exposes further dependencies: sixteen diary display
   models need diary identity/gameplay/acquisition; weed model needs the shared
   `ftr_listEventPresentChumon` reward route. Neither is a completed static import.
3. Acquisition categories, special preview framing, and graphics variants:
   extend reusable adapters for the inventory's explicit reasons. Some items
   need combined features; clearing one reason need not make the item complete.

No more bespoke furniture installers or item-by-item metadata definitions are
the default development path. The legacy scripts remain as reproducibility
records; new supported items flow through the shared pipeline.
