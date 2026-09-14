# V3 player clothing animation checkpoint

## Implementation

The player animation's original 256-shirt bounds reject `34BF` and would pass
index zero to the texture loader. The complete 36-byte decision now calls the
checked full-index query, preserving native item outputs, animation timing,
saved identity, collection, and the existing double-buffered resource loader.
Native `24xx` retains its original index; selected `34BF` uses `10BF`; unknown
or disabled garments retain the original zero fallback.

Build: `build/v3-clothing-wear-01/animal-forest-v3-asset-loader.z64`, ABI 35.

- ROM SHA-256: `07f684e157b7e5c056b2df6e002704e5570f2916a89cbfce0881919f074284b2`.
- UPS SHA-256: `130415f6151f2601ff824f4120ec52e21a49f09aeec577d7b08012f702c11216`.
- Resident prefix SHA-256: `56fd3983bdba0de37fdc15c9b1e997c261b85af7daadf92fcfeeefadd1cbde74`.

The combined clothing routing code is 672 bytes at `80463C30`, ending before
`80463ED0`. It retains the 40-byte C frame and existing register-preserving
wrapper. Only the reviewed player decision and linked clothing tag targets
change outside that helper and the ABI. Save format 2, ownership, resources,
player field sizes, and heaps remain unchanged. Older format-1 V3 builds and
V2 remain incompatible with clothing saves.

## Component verification

The current sanitized host and complete cartridge tests pass. They cover native
range edges, selected/disabled/unknown garments, wide-ID rejection, retained
classification/furniture modes, complete installed player/tag edits, full
retained resources and save code, memory bounds, checksums, and reconstruction.

The initial native run `build/v3-clothing-wear-native-01` passes 33 records and
exits normally. It executes the exact installed nine-instruction window in a
192-byte disposable allocation, with six original/imported/disabled/boundary
cases and complete unrelated-register comparisons. Three current classification
calls retain native clothing, imported clothing, and imported furniture results.
It restores the owner-pointer arithmetic fixture and selection byte, verifies
the complete prefix and all guards, frees the allocation, and restores the
checkpoint. The fault pointer stays zero. This is a copied instruction-window
test, not complete player-owner loading or an ordinary clothing change.

## Ordinary gameplay check

The copied-town fixture `build/v3-clothing-town-fixture-01` uses source save
SHA-256 `d489736e39abc7eff1c5b5085bf52e679186f2882a0247339e11603799b80b60`.
It seeds only player zero's first pocket with `34BF`, sets that fixture's
ownership, and encodes the current format-2 profile. Original villagers, other
items, and the source file remain intact. Fixture SHA-256:
`e18d679ca8e78e97b2c0119641e7350d3a219164641470afb1ceb1eba28fe4df`.
This is not ordinary acquisition evidence.

The ordinary input sequence passes on that cartridge:

- `build/v3-clothing-inventory-gameplay-01`: cold boot the copied town, select
  the resident, and open inventory. The full `34BF` item survives loading and
  appears as “cherry shirt”.
- `build/v3-clothing-action-gameplay-01` and `v3-clothing-grab-gameplay-01`:
  select Grab and move the held garment onto the miniature player.
- `build/v3-clothing-wearing-gameplay-01`: confirm the change. The native
  animation completes, the miniature player wears the correct imported artwork,
  and the saved fields become index `10BF`, item `34BF`. The original `2410`
  shirt returns to the first pocket; all fourteen other pockets are unchanged.
- `build/v3-clothing-world-gameplay-01`: close inventory and return to ordinary
  outdoor play. The imported artwork remains correct, and the menu closes
  normally. The full clothing identity and pockets remain intact.

These checks use ordinary controller inputs without editing live game memory.
Fault pointers stay zero, guards remain intact, and every process exits normally.
The intervening checkpoints resume the identical ROM; they are not game-save
evidence.

The ordinary gyroid sequence proceeds through greeting, Save, house entry,
Save & Quit, the complete save dialogue, and return to the title screen in
`build/v3-clothing-gyroid-gameplay-01`, `v3-clothing-save-choice-01`,
`v3-clothing-save-enter-01`, `v3-clothing-save-quit-01`, and
`v3-clothing-save-finish-01`. A read-only comparison during that sequence finds
the complete 544-byte imported texture/palette in the ordinary active bank:
SHA-256 `4144452f514d67a012abc5c81209099ef36b246b021028b5ea5b3f65eac37bce`.

The resulting 128-KiB FlashRAM save has SHA-256
`ab2ccb9b7e8a85c6fae4dfd088a9e313da576ee6ef505330945ff97b5695ab94`.
Both banks contain `10BF/34BF`, original pocket shirt `2410`, and imported
ownership. Both complete banks match independent format-2 reference re-encoding,
including native checksums, payload CRCs, and extension CRCs.

The first fresh-process reload invocation uses a 65-second emulator lifetime
for a controller sequence that explicitly waits over 87 seconds. The timeout
terminates the emulator before the first snapshot; no reload result is claimed.
The single corrected attempt, `build/v3-clothing-reload-gameplay-02`, uses a
160-second lifetime with the same source save, ROM, and controller sequence.
It passes: ordinary town entry restores `10BF/34BF`, all fifteen expected
pockets, imported ownership, and the complete 544-byte active garment artwork.
The save-state guard, translation guard, and zero fault pointer pass; the
process exits normally. This closes ordinary player clothing save/restart/load
for this copied town, not Controller Pak transport or original hardware.

## Remaining work

Complete dropped/displayed clothing, remaining renderer/shop/catalogue consumers,
and their gameplay persistence. Retain unresolved NPC queued
and second-owner evidence for the combined clothing check. Punchy's defaults
and move-in eligibility remain off; both patchers stay V2.
