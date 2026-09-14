# V3 clothing menu checkpoint

## Completed component

Selected imported garments receive ordinary clothing classification through the
shared full-register query, without altering their full IDs or admitting them
to furniture bounds/index arithmetic. Three additional tag detours connect
held-clothing animation, hand eligibility, and cursor destination. Existing
type-classification consumers inherit the checked clothing result; their later
rendering and gameplay are not all verified by this component test.

The new helper is 492 bytes at `80463C30..80463E1B`, retaining the loaded prefix,
heaps, owner sizes, and save format. The old query's entry redirects to the new
40-byte-frame function; its register-preserving wrapper and callers stay fixed.
The new tag pairs retain original branch logic and use existing relocation-safe
continuations. The builder preserves the complete villager-name edits in the
same tag resource.

Build: `build/v3-clothing-menu-02/animal-forest-v3-asset-loader.z64`, ABI 34.

- ROM SHA-256: `72b8fa29f4c852373546b6e9cd15ed876a5f5e3d6f7a7b7453510179739cd3bd`.
- UPS SHA-256: `7bf1a96726209f52a1fa34b85e891f7b2e79d2ec4b540bd119b2a25858897610`.
- Resident prefix SHA-256: `290cdac9476e03287a019d651fb44416c9f20443efab5fa52a9a8c6ebce346cb`.

## Verification

The sanitized host and complete cartridge tests pass. They cover selected/
disabled/adjacent clothing, invalid wide IDs, furniture rotations and both
unchanged arithmetic modes, original inputs, all new instruction pairs,
complete retained tag/name edits, complete retained code/resources, profile,
memory limits, CRC, and patch reconstruction.

The first cartridge check catches a composition mistake in build 01: editing
the earlier tag buffer lets the later name-reader merge overwrite the clothing
hooks. The builder now edits that final owner and updates both consumer reports;
build 02 passes the complete installed-resource comparison. Build 01 is not
tested in the emulator or supplied as a playtest build.

The initial native run `build/v3-clothing-menu-native-01` passes all 62 records
and exits normally. It relocates the complete current tag and verifies six
full-register windows for the imported shirt. The complete hand-eligibility
function accepts both original/imported shirts and rejects an adjacent or
unselected import. All five hand destinations match the original garment while
retaining `34BF`. Complete action-menu selection matches the original garment
in four field contexts, and wrapped/quest menus remain correct. The full tag
and resident prefix remain intact, all guards pass, and the fault pointer stays
zero. Globals are restored, allocation freed, and checkpoint restored.

The native fixture models the documented post-constructor parent state; it
does not execute ordinary inventory input or parent construction. It reuses
the parent allocation's existing inventory-pointer area, requiring `1F000`
bytes instead of another large dummy owner. No original save or device I/O is
used. Save format 2 remains incompatible with older format-1 V3 builds and V2.

## Next work

Exercise ordinary wearing/drop/display paths, connect remaining garment
renderer and buy/sell/catalogue consumers, and verify combined gameplay and
persistence. Retain unresolved NPC queued/second-owner evidence until covered.
Punchy's defaults/move-in remain disabled; the patchers stay V2.
