# Imported outdoor-house fault and fix

## Confirmed cause

The ABI 58 reproduction uses a fresh disposable copy of the preserved source
town. `build/v3-house-diagnostic-seed-01/test.flash` has SHA-256
`64ff4d18e83d6e32aba2eb085eb528db2b98a1a8e31de4335e43c7078e0af98a`.
The original save remains unchanged. Only the fixture substitutes Punchy and
matching saved outdoor house `50ED`; positioning is explicitly test-only.

`build/v3-house-diagnostic-native-01` reproduces the previously unexplained
post-positioning read failure. The actual packet is `S0a`, an emulated CPU
address-error signal, not hexadecimal memory. The pending ordinary memory reply
then shifts subsequent raw diagnostic responses by one. The complete raw receipt
has SHA-256 `289c7850469943c7f0e5a1cf3e803a2529a1522eecdb3f0f3892c7660bda9b31`.
The emulator source explicitly maps MIPS address exceptions to this signal.

The diagnostic reader retains the pending response, halts, and captures registers
and complete RAM without suppressing the original scenario failure. The first
capture attempt, `build/v3-house-fault-native-01`, fails before debugger connection:
Xvfb resets and tries to write to the closed display-number pipe; ares subsequently
dereferences a null X display in `hiro::pApplication::initialize`. The host core
and display log establish this separate setup failure. Adding `-noreset` to the
isolated X server corrects it. No desktop display or system package changes.

`build/v3-house-fault-native-02` captures the stopped machine:

- Fault receipt SHA-256: `1c6c5b6ef87f7b82fd8da5d33abc33214368090734859c790a07875a3784a5ec`.
- Full 8-MiB RAM SHA-256: `185793d380d80ef4da68f8893bb18562f2a4558ea367bdddfa1a3013acda0eed`.
- Reported PC: `80051F74`, inside `cKF_KeyCalc`; bad address: `80000011`.
- Actor list contains two player actors: ordinary `80250B40` and `8029A598`
  with foreground identity `50ED`. The latter is profile 0/category 2, not a house.
- No house actor exists. Seventy scene-arena nodes have valid magic/back-links,
  with 40,096 free bytes. This evidence does not indicate an exhausted scene heap.
- The original player's animation headers and all three stack combine-work
  records reference invalid keyframe data. A second player shares the native
  singleton resource banks; it must never be constructed for a house.

The native `aSTR_setupActor_proc` treats only values below `50DA` as NPC houses.
`50ED` enters its other-structure table with index `50ED - 5800`, selecting the
wrong profile. The fix and source/data contracts are in the
[specification](../../specs/V3_HOUSE_EXTERIOR.md). The captured emulated exception
is a real defect, independently of the separately corrected display setup.

## Corrected artifact and focused checks

- ROM: `build/v3-house-exterior-01/animal-forest-v3-asset-loader.z64`, ABI 59.
- ROM SHA-256: `ba188ffb7579a92418de4861f1b6daa92e6140f276ae4b17deaeb027cebed8df`.
- UPS SHA-256: `c7bf3c46408fbcbbed8faf0c6a8ea0498d8c3c49586ebafe4264da76da55d20f`.
- Blob SHA-256: `ae38c63d5c8bf4b7b5f1cdfb7c96dcf88a6399a8616b9fbd8cc335897b7c0874`.

Build: `python3 tools/v3_house_exterior.py --output build/v3-house-exterior-01`.
`python3 -m unittest tests.test_v3_house_exterior -v` passes two tests in
4.383 seconds: six exact instruction edits, complete identity-decision domains,
unchanged unrelated/dummy-marker behaviour, rejected unknown owners, all allowed
physical writes, retained profile/data, startup/ROM checksums, and full UPS.
Three debugger-memory tests pass separately in 0.069 seconds, including exact
malformed-response retention and no silent retry/consumption on ordinary reads.
After the stopped-RAM capture and display-startup changes, the combined
`tests.test_debugger_memory tests.test_xvfb_display` check passes all five tests
in 0.072 seconds. This verifies the current reader and display-allocation logic;
the current native run also establishes successful isolated-display startup.

## Native outcome and remaining defect

```sh
python3 tools/emulator_smoke.py --rom build/v3-house-exterior-01/animal-forest-v3-asset-loader.z64 --output build/v3-house-exterior-native-01 --seed-save build/v3-house-diagnostic-seed-01 --xvfb /home/discordian/Games/OpenRSC/headless/vendor/usr/bin/Xvfb --expansion-pak --no-initial-screenshot --scenario tests/scenarios/v3_town_resident_house_corrected.json --seconds 210 --port 19398
```

The first corrected native run passes the previous fault point, constructs the
actual native House actor at `8029A598` with identity `50ED`, and retains exactly
one player at `80250B40`. The house's real home is `3020,160,2180`; ordinary
movement resumes, and all nine recorded fault/guard assertions pass.

The full scenario is **not passed**: after approaching the door, the final
house-owner assertion expects `E0ED` but observes `FFFF`. No completed entry,
interior scene allocation, conversation, or ordinary save is established. There
are 28 retained results, SHA-256
`b79ebd62ddc5d839760c6110d8b9b770df3ce3f6b4f89ed4a1891840eda5e9e5`.
The failed final assertion is in the process output, not a recorded passing row.
The final matching-ROM checkpoint retains the player near `3018,160,2236`.

An independent source/binary review finds the temporary house-marker collision:
the native actor generates `F005 + index`, while `F0DF` already belongs to player
house 0. New NPC markers would overlap existing structures. This needs a fixed
additive namespace and its actual readers; it is not permission to renumber the
original buildings or simply raise the original `F0DF` comparison. Do not assume
this collision alone explains the missed door approach before verification.

Next implement the temporary-marker mapping, then continue the focused house
entry/interaction test. Do not replay the successful catalogue or earlier builds.
Full villager persistence, ordinary arrivals/conversations, and new-instrument
playback remain work. ABI 59 retains ABI 58's saved format/profile but does not
establish new ordinary cross-build compatibility. Neither web patcher changes.
