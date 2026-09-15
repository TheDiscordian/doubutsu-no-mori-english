# V3 imported-house markers and entry

## Artifact

- ROM: `build/v3-house-markers-01/animal-forest-v3-asset-loader.z64`, ABI 60.
- ROM SHA-256: `55a715831671c989aa465fbf6d04c49caa975a761105ffa1f3acecd10ac7b8cf`.
- UPS SHA-256: `34b95e341fc9b864e75c6b317521c52c69ee4e1dfa30e82cb46355921d0522a4`.
- Blob SHA-256: `dcd71359efebc2d953c537888c322a971a0137c29127cd50210842064868a557`.
- Complete compiled leaves: 116 bytes, SHA-256
  `44c064ec0110a7f55a23dab72d7d5450521e1f3257f9c725b153a1bae12d92eb`.

The [specification](../../specs/V3_HOUSE_MARKERS.md) defines the three guarded
native windows and separate `F200..F213` registry. The cartridge grows to
**64 MiB**; RAM stays **8 MiB**, with no new runtime allocation. The original
compressed house owner, all other resources, and original building markers stay
intact. The profile and saved format match ABI 59; ordinary cross-build reload
is not newly verified. Keep copied saves and backups, and do not use imported
saves in V2 or older builds lacking their dependencies.

This remains a development artifact, not a complete V3 handoff. Development
source may be pushed on `v3/optional-imports`; neither web patcher changes.

## Build and focused checks

`python3 tools/v3_house_markers.py --output build/v3-house-markers-01` passes all
owner hashes, exact instruction/relocation guards, bounded ROM/RAM placement,
startup checksums, N64 checksum, and complete UPS reconstruction.

The first proposed code gap was occupied by native growth data. The builder
rejected it before creating output. The corrected `80461F80..80461FFF` reservation
is separate from growth, modes, and NPC drawing records; no guard was relaxed.

`python3 -m unittest tests.test_v3_house_markers -v` passes three tests in
5.100 seconds. The compiled leaves execute for all 65,536 possible input values
per entry under a narrow independent instruction decoder, including delay slots,
64-bit unsigned comparisons, sign-extended word arithmetic, and all other GPRs.
The full cartridge check verifies only declared windows/data changed, complete
relocation retention, original player-house constants, zero padding, the unchanged
profile, and patch reconstruction.

## Native setup correction

`build/v3-house-markers-native-01` fails before debugger connection: Xvfb reports
`Cannot write display number to fd 4`, then host ares exits with SIGSEGV. The
host coredump's first frame is ares offset `3BE5F9`, the same display-opening
site as the prior setup fault. This is not emulated game execution.

The readiness reader used one pipe read and closed the pipe after the display
digits. A partial read can precede Xvfb's newline write, causing that write to
fail. The reader now waits for the complete newline-terminated reply, rejects
invalid/unfinished replies, and has a ten-second deadline. The `-noreset` flag
alone did not prevent the failed setup. Four display-allocation/readiness tests
pass in 0.009 seconds. The justified corrected native run starts successfully.

## Native marker and house entry

```sh
python3 tools/emulator_smoke.py --rom build/v3-house-markers-01/animal-forest-v3-asset-loader.z64 --output build/v3-house-markers-native-02 --seed-save build/v3-house-diagnostic-seed-01 --xvfb /home/discordian/Games/OpenRSC/headless/vendor/usr/bin/Xvfb --expansion-pak --no-initial-screenshot --scenario tests/scenarios/v3_house_markers.json --seconds 210 --port 19399
```

The corrected run completes 32 records and ten explicit passing assertions.
Results SHA-256:
`ae80943ebd3d9b7f8872cbe08ee0344b0a78ebd3dec307688262a003b56764a8`.

- The copied town cold-boots with the fixture-seeded, at-home Punchy. This is
  not evidence of a natural arrival or schedule transition.
- His actual house `50ED` constructs normally, with one player. The foreground
  cell at `8012EC1E` contains the separate marker `F213`.
- After the guarded approach and ordinary forward/A input, the interior loads.
  The player is `8023F0F0`, at `160,40,300`; the owner is `E0ED`, and Punchy is
  drawn inside at `220,40,139.5`. The inside snapshot retains one player.
- Fault, translation, and save-state guards pass after entry. The emulator
  remains alive and shuts down cleanly. The checkpoint is an emulator state,
  not evidence of an ordinary save/restart cycle.

The owner observation comes from the recorded snapshot. The source scenario's
final unasserted fixed old-player-address read is replaced with an explicit owner
assertion for future runs; the recorded scenario hash identifies the executed
version. No already-passing boot is repeated for this assertion-only correction.

## Interior allocation and marker restoration

`build/v3-house-interior-native-01` resumes the matching current interior state
with `tests/scenarios/v3_house_interior.json`. Seventeen records include five
explicit passing assertions; results SHA-256:
`5dea6b34be3cb7ebd8949a6134b9f2b8b581fe39b11bfbca7014487184a5bb31`.

The actual owner remains `E0ED`, and the outdoor map cell is restored to `50ED`
after the exterior actor is unloaded. The stopped-frame scene-arena walk verifies
all 65 nodes and back-links: 483,824 allocated bytes, 358,528 free bytes, and a
358,528-byte largest free block. One player and the moving/drawn Punchy remain
present. Fault and resident guards pass. This establishes Punchy's loaded room
allocation and marker restoration, not every imported room or saved persistence.

The automatic straight-line conversation approach stalls at `160,40,275.4`,
with no active message. That is an incomplete conversation check, despite the
scenario's successful read-only assertions. The room's actual foreground contains
furniture along the approach; the bounded correction uses a side approach from
this checkpoint rather than replaying cold boot or house entry.

## Interior conversation

`build/v3-house-conversation-native-01` resumes that checkpoint with
`tests/scenarios/v3_house_conversation.json`. The side approach reaches
`128.384,40,218`; its short automatic approach still reports a stalled path,
but the subsequent ordinary A presses start and advance Punchy's conversation.
The run completes 39 records, three guard assertions, and the active-choice
check. Results SHA-256:
`25c8d8ec249abc7a750f2c993a493684e60497949456f2a33dca858d636d6f1d`.

Actual message `2289` contains his English home dialogue; its live insertion
expands the message from 123 to 127 bytes with the complete `mrmpht` catchphrase.
Message `02AC` then supplies the English request and three live options:
`Can I help you?`, `Entertain me!`, and `My mistake!`. Eleven ordinary A presses
reach the choice without truncation or a fault. The matching checkpoint retains
that active menu. This is ordinary resident speech, not only a direct reader test;
physical audio remains disabled, and it does not validate the unresolved four
new instruments used by other imports.

## Return outside

`build/v3-house-exit-native-01` continues from the active menu with
`tests/scenarios/v3_house_exit.json`. Ordinary inputs select `My mistake!`,
close the dialogue, and walk through the exit. Twenty-four records include four
explicit guard/marker assertions, both choice checks, and the actual-house check.
Results SHA-256:
`21d27b379641dbd4d1a2ad9c34aac4cbedd4e364f9ccc31b537cfbda56463e0f`.

The player returns to `3020,160,2240`. The real house `50ED` reconstructs at
`3020,160,2180`, its temporary foreground value is again `F213`, and there is
exactly one player. The outdoor scene has 69 valid arena nodes, 801,728 allocated
bytes, and 40,608 free bytes in one block. Fault and resident guards remain intact.

This establishes the current Punchy-house entry, ordinary English conversation,
and exit cycle, including both actual/temporary map-ID transitions. It does not
establish ordinary villager saving/loading, natural arrivals, all other homes,
or the unresolved new-instrument playback. Continue from the matching current
checkpoint where possible. The preserved original town and stable V2 ROM hashes
remain unchanged.
