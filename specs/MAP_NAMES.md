# Complete map villager names

## Native layout and hooks

The map overlay is VROM `00795350`, linked at `8088DBD0`, with relocation
`00797870`. Its original 9,504-byte image is followed by 16,256 bytes of BSS.
The map state begins at `808900F0`. Fifteen animal records start at state
offset `3C68`, each nine bytes wide: six name bytes, sex, house layer, and house
index. The block-label lists point into those records; sorting moves pointers,
not records. Player and empty-house records use the same packed layout.

`af_map_load_name` replaces the call at `8088E030`. It invokes the original
six-byte identity-name loader to preserve the packed fields, then stages the
complete eight-byte resource name into a separate fifteen-entry cache keyed by
the native name pointer. Only animal identities `E000..E0D7` use the resource;
special-actor IDs do not bypass the native animal-identity fallback. Failed loads retain the freshly generated native name
with two spaces, not a previous resident's English name. A full cache falls back
to the unchanged native record without writing beyond it.

The resident-name draw calls at `8088F2F0` and `8088F32C` use `af_map_draw`.
Cached animal pointers resolve to complete eight-byte names. Player/empty-house
pointers keep their original text and six-byte length. The native sex lookup
at `8088F29C`, colour branches, positions, scales, twelve-pixel vertical steps,
and all fourteen font-call arguments remain unchanged. Building labels do not
pass through these two calls. Drawing performs no additional ROM loads.

The constructor's initialization call at `8088FC98` uses `af_map_init`, which
clears cache keys before tail-calling native `8088FB70`. Native initialization
calls `8088E430`, which rebuilds block labels through `8088DE88`. Reset therefore
precedes name population on every entry, including reuse of an allocated map.
Reloaded overlay storage also begins zeroed. No player, animal, or saved identity
is widened, and no random-number or dialogue-timing call changes.

## Ownership and memory

The new image materializes original BSS at the same offsets and appends the
helpers and zero-initialized cache. Only four instructions in the native prefix
change. Original relocation entries retain their targets; new local calls and
addresses receive explicit relocations. Resident imports remain fixed.

The 26,544-byte image moves to VROM `03B00000`, with adjacent DMA relocation
entry at `03B10000`. The original submenu owner's map row at offset `2AB0`
retains its constructor/destructor/setup pointers and supplies the new image
endpoints. The aligned map allocation grows by 768 bytes. No permanent module,
main-code allocation, save field, or submenu pool reservation changes.

The native map dependency flag is zero (`flg_table_916`, program five); the map
does not request inventory/tag/hand/editor children. `mSM_set_other_seg` and
`mSM_ovl_prog_seg` in the pinned native submenu source define loading and aligned
allocation. The allocation check conservatively substitutes this map for the
larger catalogue in the existing alternative bound, retaining that branch's
unused inventory/tag and sixteen-KiB miscellaneous allowances. This bound must
fit the already verified combined submenu pool. It is not added to the mutually
exclusive owner-message-editor maximum.

## Verification scope

Installation binds exact native image, relocation, owner, imported name loader,
complete name resource, compiled helpers, and new relocation inventory. The
notice-owner verifier includes the approved map row and rejects other changes.
Combined translation accounting verifies the installed map route and removes
it from the description of pending name readers; other readers retain pending
credit without duplicating source IDs.

Focused checks cover packed status bytes, all fifteen cache positions, player
names, reset/update/failure, overflow fallback, complete draw arguments,
sanitizers, two relocation bases, source guards, ROM retention, and UPS recovery.
Ordinary map opening/navigation and original hardware remain part of combined
v0 validation; host checks do not claim those interactions have been played.
