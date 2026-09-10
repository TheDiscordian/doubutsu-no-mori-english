# RC4 ordinary gyroid interaction and save-prompt evidence

The ordinary home-gyroid menu opens with controller input, and the Save selection
reaches the native Save & Quit / Save & Continue question. No save is confirmed.
Save completion and cold restart remain unverified. This is new interaction
evidence, not a ROM change or a passing persistence test.

## Native distance check

The original actor constructor stores float `43.0` at actor offset `144`.
The native demo selector uses that field as the horizontal talking limit, with
its separate height and facing checks. Starting to dance below 80 units and
returning to idle above 90 units are different conditions, not talk thresholds.
The earlier failed route stops about 45.994 units from the gyroid at
`(2060,160,1500)`, outside the actual talking limit.

Verified original/RC4 routine ranges retain identical content:

| Routine | Native address range | SHA-256 |
| --- | --- | --- |
| Gyroid constructor | `8096AB90..8096AC5F` | `613d60e086aed6da10ae86c5196556fa97889d121a00c7a34e3911c40a13ee87` |
| Dance entrance | `8096B168..8096B1A3` | `1bba65b1a05ad3266fa10ef3dc5e4a5f9fb91076458439ee23b51c7802c7f7b0` |
| Dance/request | `8096B398..8096B473` | `6f429e328aa086ec9442b5325fab1807a94b627a537c92b5cb090a45905ec71f` |
| Demo talk priority | `8007C6C0..8007C80F` | `00f23043ffbb7ede9b902ac9a15ae0daa76b87a113f9285a3c554af611a81f57` |

The actor is native VROM `0085F7D0`, installed at `03930000` in RC4, linked at
`8096AB90`. Main-code comparison uses each cartridge's actual CODE resource.
`flash_mail.evidence(rc4)` also passes its three native save-code/table guards.
These unchanged routines alone do not prove a save operation succeeds.
The initial local disassembly generated with origin `8096AB80` has incorrect
address labels and is not used as address evidence; the matching actor listing,
main-code listing, native symbols, and actual resource comparisons above are used.

## Executed interaction

ROM: `build/v1rc4/Animal Forest English V1RC4.z64`, SHA-256
`5930435f588947df35313ae9cc2ea301af9fc7e68d59a7d8e13a48741d4f3067`.
All runs use the existing silent isolated runner, Expansion Pak, port 9194,
explicit local Xvfb executable, and no screenshot. There are no injected game
calls, game-memory writes, teleports, or progression changes.

`tests/rc4-ordinary-save-talk-radius.json`, seeded from the retained
`build/rc4-ordinary-save-route-view-01`, changes the final northward approach
from 0.10 to 0.14 seconds. The player reaches approximately
`(2053.938,160,1540.332)`, facing `8000`. A normal A press opens message `0925`,
and one further page advance activates all four English choices in native order:
Revise, Store an item, Save, and Never mind. Both fault-pointer assertions pass.
The runner completes nineteen recorded steps and graceful shutdown.

Output: `build/rc4-ordinary-save-talk-radius-01`.
Scenario SHA-256:
`8725c187a5a34b392f24052e7622b3d3bd671b92c93361939ac54caf2be3072d`.
Results SHA-256:
`24005fd792add823b25718db09c42878822f6896c03ceb552a4a4103429b7f95`.
Its final `test.bs1` SHA-256 is
`69a9fc5bf15e3627f9e14f32ebd377012264b8741ff3ab7c609c3234869c965a`.
That retained checkpoint is at the active gyroid menu, not proof of saving.

The observed inventory has items `2406/1DA4/201B/2617`, eleven empty slots,
all fifteen condition fields zero, wallet 0, loan 17,400, and clothing
`0010/2410`. Those are pre-save observations, not post-reload comparisons.

## Save-selection attempts and limits

Both confirmation attempts start from the active menu checkpoint, without
replaying navigation. `confirm-01` uses D-pad Down and stops because the choice
cursor remains zero. `confirm-02` corrects this to analogue-stick down (`s`):
the cursor reaches two, the selected text is Save, and native `092D` says
to enter the house. Ordinary advancement then reaches active message `2B12`,
"Calling it a day?", with Save & Quit / Save & Continue. The driver incorrectly
expects `092D` still to be active and stops before confirming either choice.
The native route agrees with `specs/SERVICE_SAVE_DIALOGUE.md`; the GameCube's
different gyroid save flow is not an instruction for the N64 driver.

| Output suffix | Attempted scenario SHA-256 | Results SHA-256 |
| --- | --- | --- |
| `confirm-01` | `9a4ee9b8cfa5430f5c2a5bfcc58c6be251f740ec6373eed833212f728fdba6cc` | `de641ee26e0389afb45865fcd31d6e2406cf447fb289292ada636f00b7b49fac` |
| `confirm-02` | `25f2040688285e07b62a8590ab5c49c9f32de872f6a5cf0a0d98cbdb3247fcb1` | `6d54311f06306ad29d5775b42720d4d4e384e8a62f901bac3e55427d9fcbc0e0` |

Output prefix: `build/rc4-ordinary-save-`. Both processes are terminal. Neither
attempt reaches its later checkpoint, save confirmation, twenty-second wait,
or final fault/guard checks. Those checks are not passed. No checkpoint at
`2B12` is retained; each failed output's copied checkpoint is still the original
active gyroid menu. Do not relabel it as the save question.

The committed confirmation scenario corrects the expected ID to `2B12` and
checks the exact two English choices. This corrected continuation is **not
executed**: the confirmation setup reaches its initial-attempt/one-retry limit.
Its earlier attempted versions differ by that ID/choice assertion and, for
`confirm-01`, the two Down keys in place of `s`. Retain the actual run hashes
above; do not claim they bind the revised unexecuted scenario.

## Save preservation and next work

All three isolated FlashRAM outputs retain SHA-256
`9fb7fd3382527b7d3dd0c1d83531e39dcbb4b210ee321396f3caa0826493c012`.
The original copied RC2 save retains SHA-256
`d489736e39abc7eff1c5b5085bf52e679186f2882a0247339e11603799b80b60`.
Read-only native validation passes on each: two matching payloads, valid
checksums/signature, town ID `306C`. No SD-card access occurs.

Do not repeat completed navigation or this setup batch. A later justified
persistence batch can use the retained active gyroid menu and the verified N64
question/quit/continue branches, preserving the explicit unexecuted status of
the corrected continuation until then. Complete an actual save before a cold
boot with `--seed-save`, not `--seed-state`; compare player/town identity,
pockets, conditions, and balances against the recorded pre-save state. Same-ROM
saving, cross-version round trips, and original-hardware acceptance remain
separate unverified requirements. Continue unrelated V1 work at this limit.
