# Selected song-title integration checkpoint

## Installed scope

`build/song-names-pilot/animal-forest-halfwidth.z64` installs the complete
selected song-title caller, retaining all ordinary-name, quest-letter, other
text, font, and runtime work. Its only changed DMA payload relative to the
complete ordinary-name ROM is the existing fruit-box/credits actor `00963DF0`.
Four instructions replace the old 84-byte song-name function; no actor size,
relocation, BSS, resident memory, or saved layout grows.

The [specification](../../specs/SONG_ITEM_NAMES.md) binds the original function,
callback pointer, complete field reader, dependency checks, and request-input
boundary. Full selected names pass through the existing sixteen-byte item path.
The resource contains 53 complete English song names; the two accented names
still require item encoding support. Typed song requests are not expanded here.

## Verified checks

`build/song-item-names-host-tests.log` passes all seventeen initial caller,
field, and credit tests. `build/song-item-names-tests.log` passes four installer
and actual-ROM checks. The additional scenario test passes, and the combined
`build/song-item-names-regressions.log` passes all 53 tests in 32.700 seconds.
These checks cover source guards, exact instruction effects, full-width slots,
all low-byte song inputs, three relocation bases and the actual callback address,
unchanged surrounding actor/credits data, rejected dependency mutations,
all ordinary-name retention, current native-batch evidence, and full UPS
reconstruction. No all-project regression claim follows.

Independent Docker assembly matches the sixteen instruction bytes; all remaining
bytes in the old function slot are zero. The original-ROM aligned-pointer and
decoded direct jump/branch scan finds no entry-interior references. The actual
callback registration uses the retained HI/LO instructions and clip offset `20`,
not a direct jump or aligned literal pointer.

The completed silent batch `build/smoke-song-item-names-03` passes all 55 complete
resource names through the cartridge-loaded setter and real native insertion
handler. Five slot/index rejections, three eight-bit argument cases, and disabled
resource fallback/recovery pass. All 125 native calls and 326 assertions pass in
516 records, including 63,872 unchanged save bytes, live actor ownership/code/
credits state, heap, seven fixture/stack guards, six restored globals, checkpoint
reload, blank isolated FlashRAM/Pak files, and graceful shutdown. The runner is
bounded at 600 seconds, with audio, screenshots, and game-save writes disabled.
Normal performance, request entry/matching, save/reload, full presentation review,
and hardware remain unverified.

The first two attempts stop before any song cases on test-fixture assumptions:
`01` expects zero mutable actor ownership fields despite a loaded live actor;
`02` rejects that actor's legitimate eight-byte-aligned base in the host relocation
model. The corrected helper guards every static metadata byte and explicitly
permits eight-byte alignment for this live-owner proof. The production ROM is
unchanged. Attempt `03` resumes the original isolated same-ROM checkpoint, not
the partially modified second attempt. The eight relocation/installer tests in
`build/song-item-names-relocation-tests.log` pass in 2.687 seconds. The frozen
native result test checks every setter argument and complete inserted title,
restore order, source-bound scenario, and all save hashes without replaying it.

## Artifacts

- ROM: `f499acc510c33917ead14bd18eb9148053ff225654d47f44998be705d849719b`.
- UPS: `24b08ada757af2511671a6f8c20c805e4e428cef8a5333a378fd802ed76906a7`.
- Patched actor: `cbb0b08439b7289c3e22ff7332d953c31ad385dc2aff05983671c4a009569e12`.
- Unchanged credits relocation: `5b347ca673af7e0487ee7ef1a5ab68e9647ae878bb0ee70d49cbbaf9068b2123`.
- Complete function patch: `52aa999e253a59374161909dd32b9d9b1d50d0c2788c99ef21a8c188b02aaa23`.
- Native scenario: `41851a54752d321ea571a3011163d62f26086499c23e15e8d0a5f9f62529aa23`.
- Resume scenario: `d060e29fb9e2e8f7806d504938ea02deb622903d1dd92f3918377ffc757a82cc`.
- Native results: `958609e5839f4fcb1beffa363e2f24c1e79dc133ecbdf0e8df2bd2a211fee3b4`.
- Input checkpoint: `2d451168de28ce62cc58017ed3441cb41eb17fb4fa10d38a6b0f480a9e6dee91`.
- Restored checkpoint: `8e9ece8f9fd078d7168684bcfc441471ef69e6f2842378c2522d455f61620cc2`.
- Native helper: `6fa80f0edf88d4d7f89b12d1dbf61883d2eedc95890774bbeb51efc4af80d69a`.

## Reproduction and continuation

Retain the complete [ordinary-name ROM recipe](ORDINARY_ITEM_NAMES.md), add
`--english-song-names`, and select output `build/song-names-pilot`. All other
flags and generated dependencies remain. Verify the assembly and prepare the
single native scenario with:

```sh
python3 tools/check_song_item_assembly.py
python3 tools/song_item_names_scenario.py --output build/song-item-names-scenario.json
```

Continue remaining item-name callers and identities, accented/native-specific
names, noticeboard/general text, review, normal save/travel/gameplay acceptance,
patch-only release preparation, title artwork, and the GameCube-style keyboard.
The full project remains active.
