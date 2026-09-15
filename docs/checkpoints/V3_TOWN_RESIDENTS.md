# Complete-roster town integration checkpoint

## Current artifact

ABI 57 enables explicit ordinary-town adaptation for all twenty imported
villagers in the experimental cartridge. See the
[specification](../../specs/V3_TOWN_RESIDENTS.md) for scope and memory contracts.

- ROM: `build/v3-town-residents-03/animal-forest-v3-asset-loader.z64`.
- ROM SHA-256: `8ea1dd5de03a2d03db7e8bcafc58099a963a9ff2d5bdb8057e538e0100d92b58`.
- UPS SHA-256: `ce94d9f6f2d7ae24289124bf93b22218a31f5f79dd118a260add634f82ae4778`.
- Blob SHA-256: `f04d6050c769a4aec54e13b473e244f675c6de96c1467c1e59368cab9b76d553`.

Build command: `python3 tools/v3_town_residents.py --output build/v3-town-residents-03 --enable all`.
The `-01` attempt rejected an incorrect expected predicate instruction before
writing a ROM. The `-02` attempt reached a report-variable type error, also before
writing a ROM. The corrected `-03` artifact passes complete patch reconstruction.
Neither failed attempt produced a cartridge for testing or distribution.

## Focused and native verification

`python3 -m unittest tests.test_v3_town_residents -v` passes all six tests in
4.396 seconds. Cases cover native/invalid identity bounds, twenty fixed imports,
role preservation, independent mode/flag/profile/metadata/outfit rejection,
complete native schedules, exact preserving-bridge instructions, permitted ROM
writes only, unchanged physical allocations, startup/ROM checksums, and UPS.

The first native run, `build/v3-town-residents-native-01`, verifies all six
personality counts, three independent Maelle exclusion controls, her fixed
candidate bit, and unseen-history retention. It then correctly returns no free
resident slot: the fixture zero-filled home coordinates, while native free-slot
detection requires both home acre bytes to be `FF`. This is confirmed in
`mNpc_CheckFreeAnimalInfo`, not assumed to be a fixture failure from a timeout.
The run has 23 records and six passing memory assertions, with results SHA-256
`53c13036965ddea31f6ef40ce59db028efdfd65ddf35328721f5e06ae5f48ef5`.
It remains an incomplete run, not a passed full scenario.

The corrected tail calls the game's complete resident-clear routine first and
does not replay the successful counts/exclusion prefix. It passes on its only
retry: `build/v3-town-residents-native-02`, 90 records and 56 passing assertions.
Results SHA-256:
`41b0809235b5bd9d9dcdf6705ba7d537cfc98e7ab9b470bfd177bc2934e9ac57`.

```sh
python3 tools/emulator_smoke.py --rom build/v3-town-residents-03/animal-forest-v3-asset-loader.z64 --output build/v3-town-residents-native-02 --xvfb /home/discordian/Games/OpenRSC/headless/vendor/usr/bin/Xvfb --expansion-pak --no-initial-screenshot --scenario tests/v3-town-residents-native-tail.json --seconds 240 --port 19388
```

The game's `mNpc_SetGrowNpc` creates Maelle in free slot 0 with full identity,
personality, red aloha garment, phrase reference, and moved-in flag. Existing
resident exclusion and history reset retain her fixed bit. This is controlled
native resident creation, not an elapsed-day natural arrival.

Two complete initial populations match independent native-RNG expectations:
imports disabled with seed 1 retains `E018 E0B7 E033 E07C E066 E0C4`; imports
enabled with seed 76 yields `E0B3 E0E9 E066 E0DA E012 E04C`, including June and
Maelle. Each population contains all six personalities and leaves nine slots
untouched. Identity mapping never uses the transient checkbox/shuffle ordinal.

Bliss, Elina, Boomer, Drift, O'Hare, and Maelle exercise all six native schedules
at 04:00, 12:00, and 20:00. Complete slot assertions verify the schedule pointer,
current/saved state, and timer. The timed override, forced-outdoors path, and
schedule release pass. Prefix/package/state, stack/allocation/module guards,
checkpoint restoration, and zero faulted-thread checks pass. No save is written
and no physical audio is emitted by this native fixture.

## Gameplay and next implementation

Current-cartridge copied-town gameplay is checked separately. The
initial disposable seed `build/v3-town-resident-seed-01` uses the preserved source town
without changing it, and updates only its copy to the current profile and
Punchy's fixed identity/defaults. Seed FlashRAM SHA-256:
`296249581f402b1fd0ceb71d70bf41449b7831d68f1289402f2d5de8bd760626`.
Its at-home state is explicit fixture input, not natural schedule evidence.

`build/v3-town-resident-arrival-01` cold-boots the current cartridge and reaches
the world with the full imported identity/outfit and intact guards: 16 records,
four assertions, results SHA-256
`7d9ee2119c179001fcc005d6c54d5385931f8bfb820d212c78d79415c26ff117`.
The wall-clock controller route stops before the destination acre, so it does
not repeat the older build's successful acre-crossing result. The controlled
near-house follow-up `build/v3-town-resident-house-entry-01` does not enter;
owner remains `FFFF`, while all fault/guard assertions pass. Results SHA-256:
`adeffd3bcd8ee067e6f71ec73cae0296358b443391695d58ba8b2640d5a9fcbe`.

Source inspection identifies an independent omission in the disposable fixture:
replacing resident `E004` with `E0ED` leaves the saved outdoor-house tile at
`5004`. `mNpc_SetNpcHome` only constructs a house for an unassigned home; it does
not rewrite an existing one after this test-only resident substitution. The
corrected fixture assigns `50ED` at saved offset `7D7E` in both copied banks,
retaining the complete location, all other foreground cells, and other residents.
This is a test-data correction, not a ROM fix or proof that every missed approach
had that cause. Two current-build fixture checks pass in 0.405 seconds, including
the actual save-codec reader. The original save remains unchanged.

Corrected seed: `build/v3-town-resident-seed-02`, FlashRAM SHA-256
`9234e8a88cb2f6379770f1052b3410da6e8920fabf2ef899b63ab4691cd29e84`.
Its focused cold-boot/house continuation uses guarded, frame-paused test-only
player positioning to avoid another navigation loop, followed by normal controls.
It does not establish an entirely unmodified controller journey or natural arrival.

The corrected run `build/v3-town-resident-house-corrected-01` cold-boots and
verifies resident `E0ED`, outdoor tile `50ED`, and the player/frame pointers.
It records twelve results, including five passing assertions, then stops at the
first post-positioning snapshot: the debugger's memory response is not hexadecimal.
The raw response is not retained by the current reader, so a protocol error cannot
be distinguished from a game failure in this result. No house entry, fault-state
tail, or complete scene-allocation assertion is established. Do not label this
a passed visit or a proven fixture-only failure. The native resident/schedule
checks above remain separate valid evidence.

The initial attempt and corrected retry finish this gameplay-setup batch. Do not
start another blind navigation/retry loop. At the next meaningful house/gameplay
investigation, retain the raw debugger response and immediately inspect the fault
thread/registers, scene allocation, and loaded house actor before changing timing.
Proceed with the independent aloha display/catalogue/acquisition implementation.

Ordinary arrivals, conversations, house entry, and persistence remain incomplete.
The new instrument playback issue and aloha item display/catalogue/acquisition
also remain work. This is not an accepted V3 handoff. Saved formats/profile match
ABI 56, but ordinary cross-build save compatibility is not newly verified.
Only source on `v3/optional-imports` may be pushed; both patchers stay V2 pending
user testing and explicit approval.
