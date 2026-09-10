# RC4 ordinary-save navigation attempt

**Ordinary save/quit/cold-restart remains unverified.** The bounded batch does
not reach the home gyroid's Save menu. No Save choice is selected, and no cold
restart from a newly written game save is attempted. The navigation setup has
reached its retry limit; do not replay it unchanged.

## Scope and preserved inputs

The packaged RC4 ROM has SHA-256
`5930435f588947df35313ae9cc2ea301af9fc7e68d59a7d8e13a48741d4f3067`.
Initial seed `build/rc4-town-stick-01` has checkpoint SHA-256
`11edd72e6f3882926d30ace79a316de72567b4240fffd7575c222460db9b1f44`
and FlashRAM SHA-256
`9fb7fd3382527b7d3dd0c1d83531e39dcbb4b210ee321396f3caa0826493c012`.
This is the retained isolated town, not the original supplied save.

Original `local/rc2-save-report-g3O4lU/rc2.fla` remains at SHA-256
`d489736e39abc7eff1c5b5085bf52e679186f2882a0247339e11603799b80b60`.
Read-only `flash_mail.validate_flash` passes on both original and isolated seed:
two matching payload copies, valid native checksums/signature, town ID `306C`.
The SD card is not accessed. No earlier save, ROM, or test output is overwritten.

Every run uses the existing silent isolated emulator runner, Expansion Pak,
ordinary controller input, and read-only debugger observations. No native
function calls, game-memory writes, teleportation, or progression edits occur.
F5 is an emulator checkpoint, not game-save evidence. The runner SHA-256 is
`0c222d4f62250246d994f24dc80ca5c31c09d362dd97bc1019d27c80bca92d84`.

## Executed sequence

Output prefix is `build/rc4-ordinary-save-`; matching committed scenarios have
prefix `tests/rc4-ordinary-save-`. Each `run.json` binds the scenario, ROM, and
complete seed-file hashes. Time limits are 45–75 seconds, port 9194, with
`--no-initial-screenshot` and `--expansion-pak`.

| Output | Seed | Result |
| --- | --- | --- |
| `approach-01` | `rc4-town-stick-01` | Xvfb absent from PATH; game never starts |
| `approach-02` | `rc4-town-stick-01` | Explicit existing Xvfb path works; player reaches outside of house fence |
| `gyroid-01` | `approach-02` | Player moves south beside fence; no dialogue |
| `menu-01` | `gyroid-01` | No menu after four permitted A presses; attempt fails |
| `route-view-01` | `gyroid-01` | Isolated image identifies fence blocking eastward route |
| `fence-route-01` | `route-view-01` | Corrected-route retry rounds fence, but no dialogue after six permitted A presses |

The existing executable is
`/home/discordian/Games/OpenRSC/headless/vendor/usr/bin/Xvfb`.
The `approach-02` and `gyroid-01` runs pass fault-pointer checks at `8003CE34`
and finish with graceful emulator shutdown. Their FlashRAM retains the seed's
hash. Both failed menu attempts stop before their final fault assertion,
capture, and checkpoint; those unexecuted checks are not passed. Both observe
loaded-message state zero and stale player-selection ID `1404`, not gyroid text.
Final observed position is approximately `(2055.413, 160, 1545.765)`; the target
gyroid is at `(2060, 160, 1500)`. This does not establish that the player reaches
the native talk threshold, or prove a gyroid interaction defect.

## Retained evidence and next useful check

| Output | `results.json` SHA-256 |
| --- | --- |
| `approach-02` | `79cc6a14dd62676105fc7bb40ef33111109ee9752c0679821460ecc31f1d04c2` |
| `gyroid-01` | `dc2357e5f4ac7564ed93b255b4cb280cc3da22f4b8d3e17154620b7ee9113c3e` |
| `menu-01` | `588ea16c73fb082a03ed4b3e863f41862b6354333c69c65ef767f83084dd6cc6` |
| `route-view-01` | `54f671aea08bf15e6fd8aacf58b5b5876f342df3181331632675e42ed0a2b11a` |
| `fence-route-01` | `8b1af003b9928825c401818075ce0c5106d9b6d02b6aa490786dcbbb371cd235` |

The isolated `route-view-01/route.png` hash is
`cd1b5d7238333a248712cb2694e79206610d65f75485576c895f9afc6bf42b3a`.
Only the isolated emulator window is inspected; the desktop is not captured.

A later justified interaction batch should establish the native talk distance
and facing requirement, or use an available checkpoint at an active gyroid
menu. Do not build another blind timed-navigation loop. After actual ordinary
saving, validate written FlashRAM and cold boot with `--seed-save`, without an
emulator checkpoint. Compare player/town identity, pockets, and balances with
pre-save observations. Preserve the unverified persistence, cross-version
round-trip, and hardware limits until those operations actually pass.
