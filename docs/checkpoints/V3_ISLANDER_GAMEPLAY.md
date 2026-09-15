# V3 ordinary islander integration

## Current scope

Use the ABI-60 cartridge from the [house-marker checkpoint](V3_HOUSE_MARKERS.md),
SHA-256 `55a715831671c989aa465fbf6d04c49caa975a761105ffa1f3acecd10ac7b8cf`.
The cartridge is unchanged in this batch. Both patchers stay on V2.

`tools/v3_punchy_gameplay_fixture.py --actor E0DA` makes a disposable Maelle town
from the preserved source, with her fixed identity, personality, actual red aloha
shirt, full default-phrase reference, matching house, and current save profile.
This substitutes one resident in a test save, not in the ROM. It does not prove a
natural arrival. The default Punchy fixture retains its prior behaviour.

The current fixture tests pass all three checks in 0.712 seconds: both-bank
boundaries, actual native codec acceptance of the default fixture, Maelle's
declared edits without unrelated payload changes, and rejected invalid inputs.
Maelle's seed is `build/v3-maelle-gameplay-seed-01`, FlashRAM SHA-256
`e22d4551330ab154817a4db212af12a4aa5b49c9826e2a02ee0ad0518dfee841`.
The preserved original save remains unchanged.

## House and schedule observation

`build/v3-maelle-house-native-01` uses `tests/scenarios/v3_maelle_house.json`.
The copied town cold-boots, loads the native Maelle actor and actual house
`50DA`, installs marker `F200`, and admits the player into her room. The interior
owner is `E0DA`; one player remains, with 59 valid scene-arena nodes,
483,200 allocated bytes, and 359,248 free bytes.

The run is not a passed conversation: Maelle's indoor actor is at `0,40,0`, the
approach exhausts its limit, and no active choice opens. Fifty-five retained
records have SHA-256
`9a1097df951aef1fad96ef0e65866e7b3aa875dd8a382d9c83fd04a66b7b108b`.
The final conversation/guard tail is not executed.

The matching-state continuation establishes `is_home = 0` and an outdoor
recorded position of `2925.537,160,2416.874`. She has left home under the ordinary
schedule. Native instructions `8099EE80..8099EE90` and `8099EFEC..8099EFFC`
set an away resident's indoor X/Z to zero, matching the donor's
`ac_npc2_schedule_field.c_inc` and `ac_npc2_schedule_in_house.c_inc`. This is
intentional absent-resident handling, not a newly established room-spawn defect.
An installed draw callback in the actor snapshot does not prove visible pixels.
No room geometry or schedule behaviour is patched for this observation.

The combined fixture and speech-helper tests pass all six checks in 0.818
seconds. The helper checks restrict position writes to the player's two
positions and headings, reject cross-acre/ambiguous/active-dialogue targets,
and reject unbounded observation counts before I/O. The cartridge is unchanged.

## Voice work

Maelle's actual voice is 263. Each of her nineteen donor tracks begins with an
original instrument and changes later to one of the added instruments 84–87.
The retained source explicitly includes those later notes and their durations.
An initial original-instrument note alone cannot validate the new samples.

`tools/v3_voice_observation.py` observes the current native sample-cache rows
during ordinary conversation. It does not call an audio entry, replace a melody,
write audio data, or play through hardware. It distinguishes active-cache matches
from retained inactive-cache matches, compares transferred bytes against the
actual cartridge samples, records full voice tags, and checks post-observation
fault/resident guards. Empty coverage is an unresolved observation, not success.
The initial `build/v3-maelle-outdoor-voice-01` run leaves the house normally and
finds Maelle outdoors. Controller navigation stalls about 399 units away, and
no conversation starts. Its 120-frame observation records no imported samples
or voice tags, but the final fault/resident guards pass. The later choice step
fails. Fifty retained records have SHA-256
`01b97be4f55544d6d54d09124f8229df27e645d4e0c8f59135eabbb817cd0854`.
This does not establish an audio defect or validate the new instruments.

The one corrected setup is `build/v3-maelle-voice-positioned-01`, resumed from
that exact cartridge checkpoint. The explicit fixture places only the player
30 units south of the live Maelle in the same loaded acre; it changes the
player's current/previous positions and both headings, not Maelle or her
schedule. It is not natural navigation. The subsequent normal movement/A input
leaves a 40-unit separation, Maelle's `isDrawn` field is zero, and no active
message starts. The observer now rejects that state before sampling. No new
audio or final guard result is claimed for the corrected run.

Stop this setup batch here. The retained matching checkpoint
`build/v3-maelle-voice-positioned-01/test.bs1`, SHA-256
`2cdb2fdcef04955133f131b649db3d6a140e5e2d8a0b62bfd0189a14ac605f03`,
can support a later inspection of actual visibility/interaction conditions;
the cause is not established. Do not replay the old direct audio calls or
repeat the navigation prefix. Continue independent V3 implementation.
