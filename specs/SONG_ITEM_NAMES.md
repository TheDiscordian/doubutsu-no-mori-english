# Complete selected song titles in dialogue

## Native contract

The fruit-box actor's `80AA4794..80AA47E8` routine takes an integer item-field
slot and an unsigned eight-bit song index. It obtains the main message window,
loads native item `2A00+index` into a ten-byte stack local, and sends ten bytes
to `8009D88C`. The complete original 84-byte function hashes to
`5b15d2a4dfd5d3542a2529d83a22f530e714337da11be24c429671e7e26f248d`.
There are no relocation entries within this function. The function's local
name cannot hold most complete English song titles.

The actor and its profile/relocation ownership are already bound by
[the English credits integration](NATIVE_CREDITS.md). The donor equivalent is
`aMKBC_clip_set_itemstr` in `local/ac-decomp/src/actor/ac_mikanbox_clip.c_inc`.
Its field names establish the selected-title operation, not song-request input.
The native initializer constructs this callback with the HI/LO pair at
`80AA3C00/80AA3C28` and stores it at clip offset `20` hexadecimal at `80AA3C50`.
Those pointer instructions and relocations remain intact. All three tested relocation
bases preserve the callback's complete address. Aligned literal and decoded
direct jump/branch scans find no references to the replaced function interior;
the actual entry is registered through the pointer pair, not a direct call.

## Implementation

`--english-song-names` requires the complete item runtime, English credits,
and installed sixteen-byte item resource. Four instructions replace the native
function, preserving the slot and low eight-bit song index before tail-calling
`800BB6A0` with the actual song item ID. The remainder of the old function slot
is zero padding. The installed wrapper must jump to the verified resident
`af_quest_set_item`; an absent or changed dependency rejects installation.

The existing wrapper stages the complete sixteen-byte name and sends it to
the full main-message item field. The existing message insertion consumes that
full field. Its disabled-resource fallback remains the original ten-byte
loader. Valid song selections, collection state, music, presentation commands,
and credits are unchanged. Invalid slots or out-of-range song IDs retain the
existing full-wrapper no-write checks. No new resident or saved memory, overlay
allocation, relocation entry, or temporary name buffer is added.

The request echo at `80AA47E8..80AA482C` reads ten bytes from the saved K.K.
event structure and is unchanged. Full typed song requests need an explicitly
compatible event/editor design and matcher; this selected-title hook does not
claim that work. Accented song titles also remain pending item encoding support.

## Acceptance

Check the exact complete original function and absence of interior relocations;
verify all surrounding actor instructions, credits changes, BSS, and relocation
contents. Independently assemble the four instructions. Check installation
dependencies, rejected mutations, and actual-ROM retention. A bounded silent
native batch must execute the cartridge-loaded actor routine at a real relocated
base and pass all 55 full-name field values through the native insertion handler,
with slot/ID bounds, disabled-resource fallback, guards, restored state, and
blank isolated saves. No normal performance, request input, or original-hardware
claim follows from injected native calls.

The native actor table's loaded address and signed instance count are mutable;
all other ownership bytes must match the installed actor. A live actor may have
an eight-byte-aligned base. The host relocation model permits that alignment
only when explicitly selected; its existing sixteen-byte default and memory
bounds remain. Acceptance checks both the live actor's cartridge-derived code
and a separately allocated, cartridge-loaded fixture, retaining all live state.
