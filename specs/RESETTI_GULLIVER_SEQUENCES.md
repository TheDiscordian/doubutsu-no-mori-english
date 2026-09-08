# Complete Resetti and Gulliver sequences

Six complete supplied English scripts retain every word, manual newline/page,
pause, emphasis, and native action. Three longer scripts use existing English
wait/newline/page-clear boundaries and independently checked native reserves.

| Root | English conversation | Parts and expanded bounds |
| --- | --- | --- |
| `1B3B` | Reset Alarm, attempted denial, and bright Reset Center light | `1B3B`: 896 |
| `1B41` | No-reset promise, bathing advice, and farewell | `1B41`: 610 |
| `2362` | Relaxed life rather than epic battles, looking away, and scolding | `2362 → 2B42`: 672, 580 |
| `23E8` | Reset duty interrupts everything; only one sock is on | `23E8`: 842 |
| `2511` | Complete mock-reset threat and farewell | `2511 → 2B43`: 564, 523 |
| `23FF` | Roughhousing, inability to swim, video games, rescue, and treasure | `23FF → 2B46`: 578, 487 |

Split gaps are `[619,624)`, `[511,516)`, and `[555,560)` respectively. Each is
exactly `7F04 CD 7F02`; all other reference bytes remain. The three generic
reserve records share source hash
`b2c0b6f9facf02630f093fd1b6a5a6e47d722ecadd50e6c82fae305db4821e2c`.
They have no incoming native message-script, relevant code-immediate, or aligned
data references in the pinned scan. Nearby reserves with data hits are not used.

`23FF` uses only Gulliver's original expression values plus `0F`, individually
bound to Gulliver's own `240E`. Final `01` remains; ordinary treasure delivery
is not inferred from cartridge loads or termination calls.

## Sound cues, not state assignments

Native `59` requests a sound effect. It is not an idempotent voice-mode change.
Four explicit `retain_reference_sound_triggers` approvals retain the complete
GameCube placement/count of cues `05/06`. These index the same native and English
table values `0427/0428`. Native/English cue counts are `9/10` for `1B3B`, `5/6`
for `1B41`, `9/8` for `2362`, and `6/7` for `23E8`. The additional or fewer
repetitions correspond to the complete English presentation; they are not
removed from the installed scripts.

Validation permits repetition differences only within the same actor/action
interval. Collapse adjacent identical cues only for comparison after removing
text-presentation commands and read-only fields. Actor requests, branches, music
operations, different cue values, and timed endings separate intervals. The
complete native and translated interval sequences must agree. Arbitrary cue
types, missing intervals, changed order, and non-GameCube permissions fail.
Every full reference and installed part remains hash-bound independently.

Native dispatch `59` at `800A1F1C` parses its parameter, calls `8009FC2C`, and
advances both cursor positions. Its table at `80107CA4` is seven unsigned
halfwords: `1050 012E 012F 0130 0131 0427 0428`. Host checks pin the dispatcher,
consumer, and full table. Tests remain silent and do not claim audible output.

## Timed endings

`1B41/2511` end with native `5808`, not ordinary `00/01`. An explicit
`timed_end: 7F5808` permits only that exact original final command in complete
GameCube sequences. Each part has exactly one terminator; intermediate parts
still end with `01`, and only the final part retains `5808`. Early timed ends,
changed arguments, normal-end substitutions, and absent permissions fail.

Native `800A1EA0` uses two phases: first set status bit eight and retain the
ending cursor; then clear the bit and set the signed-halfword end timer at
window `270`. For argument eight, native `(8 - 1) * 2 + 1` yields **15**. The
GameCube source shifts by two and yields 29 instead. Retain the N64's actual
timing behaviour; no runtime timer patch is installed. Music operations remain
exact, and the mock-reset speech does not add a reset or save-erasure operation.

## Acceptance and limits

Host checks require complete reconstruction, exact bounds/ending/cues, all-member
installation, native reserve scans, source hashes, unsupported-mutation rejection,
unchanged non-expression actions, and full/basic parity. The combined native
batch loads all nine parts, dispatches every cue silently, and checks each link
and both ordinary/timed ending phases with complete buffers and memory guards.
Restore the isolated checkpoint, leave FlashRAM/Pak blank, and shut down cleanly.

Normal Resetti encounter progression, apology input, fake-reset scene, Gulliver
recovery/gift actions, audible presentation, final layout, human playthrough,
and original hardware remain separate acceptance requirements. No production
runtime, font, save format, or asset is changed.

Eight focused tests, 110 reference tests, ten earlier special-actor tests, and
five train-phone tests pass. The independent artifact audit verifies all 12,591
installed edits and full UPS reconstruction; only six new roots and three
reserve conversions differ from the menu-follow-up checkpoint in both full and
basic candidates. All earlier other edits and runtime/font/name/item/mail
resources remain unchanged.

`build/smoke-resetti-gulliver-01/` passes 309 steps, 68 native calls/returns,
nine full message loads, 35 sound-cue dispatches, and 143 memory assertions.
Both timed endings set the native timer to 15. Independent regeneration verifies
every call, argument, return, complete read, restored stack/checkpoint, blank
FlashRAM/Pak, silent four-MiB execution, and graceful shutdown. Scenario SHA-256:
`e92d7a1222c4a35da98086fe602285c16d9c8914d5697ce965ff09fe68e6d7d3`.
