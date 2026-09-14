# V3 placed-clothing persistence checkpoint

## Artifact and scope

The current ABI 44 cartridge is
`build/v3-clothing-catalogue-01/animal-forest-v3-asset-loader.z64`, SHA-256
`1f53456846a8f7f6ed9cd327ffc06e0e2f8d0253466a2bcdcb8e62b2cd1dab00`.
No ROM code, format, profile, or assets change in this verification batch.
Both web patchers remain V2-11.

The fresh copied-town fixture `build/v3-display-persistence-fixture-01` seeds
player zero's first pocket with `34BF` and its independent clothing ownership.
It preserves other pockets, villagers, and the original source save. This is
not an ordinary acquisition or purchase test.

- Original save SHA-256: `d489736e39abc7eff1c5b5085bf52e679186f2882a0247339e11603799b80b60`.
- Fixture SHA-256: `85cf01b63dfb0cc8e184329208db56bbb769d7ea22b5da1b681ee60893cb037c`.

All emulator processes use silent private displays and an Expansion Pak.
Controller actions change gameplay; debugger observations only read memory.
No screenshot, GPU appearance, or original-hardware acceptance is claimed.

## Placement and bounded rotation attempts

`build/v3-display-rotation-gameplay-01` passes ordinary cold boot, player
selection, house entry, and inventory Drop. Pocket zero becomes empty, the
home contains `3AFC`, and expanded model-bank entry `804726FF` becomes `01`.
The other fourteen pockets, item conditions, wallet, loan, and native worn
shirt `0010/2410` remain intact.

The simultaneous A/right rotation attempt moves the player sideways without
changing the room item. The single corrected approach in
`build/v3-display-rotation-gameplay-02` faces toward the mannequin and presses
A before A/right, but its timed movement overshoots the intended position.
It also leaves `3AFC` unchanged. Neither run establishes a successful grab or
rotation. Both keep the model bank, inventory, translation guard, and zero fault
pointer intact and exit normally. Stop navigation retries for this batch;
ordinary rotation remains unverified, not a passed test or established defect.

## Ordinary saving

`build/v3-display-save-request-01` exits the house with `3AFC` still placed and
reaches the gyroid's four-option greeting. The first
`build/v3-display-save-quit-01` run selects Save, receives message `092D`, enters
the house, reaches the two-option `2B0F` question, and selects Save & Quit.
The native save dialogue runs, both banks are written, and the process exits
normally with its fault and translation checks passing.

The resulting 128-KiB FlashRAM file has SHA-256
`628debdc911c7a54b20811a21e218d04a56123d851c0c15dc5c29353c82ee6ad`.
Each 64-KiB bank has SHA-256
`9f1830f84fe77c74b39897d64559936956793e42e7fd69f8928bc88adde8c19d`.

Independent checks using `tests/test_v3_save_clothing.py::reference_pack`
confirm both complete banks, including native checksums and extension/payload
CRCs. Reconstructed 832-byte state equals the observed live state; its selected
profile equals the cartridge profile and clothing ownership bit `BF` remains set.
Both banks contain `3AFC` at saved offset `3606`, empty pocket zero, and the
unchanged native worn shirt. Their complete 1,104-byte home region at
`35B0..39FF` equals the live pre-save region at `8012A450`.

- Complete home-region SHA-256: `48c485516b09fa55296e4da5303a940d6d1f3531f90be14a69322b4b08d519b5`.
- Complete working-state SHA-256: `a86e0dcae878006923b662aa4e929ee5c1c07675fe0886218143753b32e52a17`.

## Fresh-process reload and pickup

`build/v3-display-reload-gameplay-01` cold-boots the written FlashRAM file;
its receipt lists only FlashRAM, RTC, and Controller Pak inputs, not a saved
emulator checkpoint. The first 17 recorded steps establish:

- Ordinary player selection and entry into the saved town.
- Complete restored 832-byte working state and 1,104-byte home region matching
  the pre-save observations, including the placed `3AFC` and ownership.
- House entry and actual model-bank allocation `01` for the display.
- Both expanded furniture-table memory guards intact.
- Ordinary B pickup returning full pocket identity `34BF`, clearing the room
  cell, and releasing the model bank to `FF`.
- Every other inventory field unchanged, including the fourteen other pockets,
  conditions, wallet, loan, and native worn shirt.

The run then stops on an incorrect test expectation: the scenario compares the
save-state guard at `8046C350` against the furniture guard `AF46C0DE`. The log
contains the correct, intact save guard `AF53C0DE` repeated four times. The
committed scenario corrects this constant. The fault/translation checks, final
checkpoint, and graceful-shutdown tail after that assertion are not executed;
do not label the complete scenario passed. The tested scenario SHA-256 is
`611678a94eeab40a5c55127c25f7bd6d349989a4efb5aa65f38e72f20e56908b`.
Do not replay the completed save/load prefix solely for that expectation fix.

This establishes ordinary same-build placed-shirt save/restart/load and pickup,
not ordinary rotation, another saved orientation, save-after-pickup, acquisition,
catalogue ordering/payment, Controller Pak travel, or cross-build compatibility.
A final complete-hash check confirms that the original source save is unchanged.

## Next work

Continue the remaining villager integration and Punchy's animated speed-bag
dependency. Retain ordinary rotation and transaction checks for the combined
gameplay pass instead of looping on navigation. Older profiles without the
display dependency still reject new saves; preserve backups. No playable-import
or web-patcher approval follows from this check.
