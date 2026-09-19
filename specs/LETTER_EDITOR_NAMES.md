# Complete letter-editor recipient names

## Implementation contract

The resident header shim at `80194CB4` uses the resident recipient renderer
in read mode. Its non-read branch derives the original header entry,
`80889CD8`, from the board call's return address; that entry redirects to the
owned editing-header adapter.

The display adapter resolves packed NPC recipient type one, index below
216, through the existing eight-byte English resource. The
[museum-header extension](MUSEUM_LETTER_HEADERS.md) resolves type two to the
official English museum name in both editing and reading. Unsupported identities,
players, and unavailable resources retain fresh saved-name fallback. Saved
identity fields and the ten-byte editable header remain unchanged. Opening and
closing animation compose an eighteen-byte temporary from the current board,
never the persistent snapshot-reader cache. New-letter initialization does not
reset that cache, and a reused board address must not revive old letter text.
Native leaflet/fortune types two, three, and five retain their header-only draw.
Active
editing retains separate normal-colour prefix/suffix and red recipient draws.
The header-selected name retains its padding; other fields use the trimmed name.

The supplied English reference measures the prefix using font advances and
reserves eighty pixels between the recipient start and suffix. The new header
cursor uses the same prefix widths and eighty-pixel post-name allowance, with
the reference's seven-pixel cursor origin adjustment. The on-name marker keeps
the existing graphics and thirty-six-pixel origin, correcting only the prefix
advance. Body/footer cursor logic remains native. No stored header, split,
recipient, editor position, acceptance, or preference byte is rewritten.

## Native fields and calls

The board is at submenu overlay `106E4`; the editor is at `106E0`. Board field
zero selects the header; header position one is on-name and two is post-name.
The header length, saved name length, split, text, recipient type, and index
are board offsets `5`, `3`, `2F`, `32`, `18`, and `14`. The native editor's
one-based column is signed halfword `20`; cursor callback is at `2C`.

The original header function is `80889CD8..80889FB0`. The original cursor entry
is `80889878`; its on-name marker is `8088973C`. The cursor call at `8088A114`
has an internal overlay relocation. All offsets/addresses are hexadecimal.
The installed full-letter copy, read-body/footer, pagination, trigger, and header
shim must remain intact. Hook placement, image sizes, relocation, allocation,
and compiled profile require verified installation before this work receives
translation credit.

## Installed image and allocation

The owned board image is 9,232 bytes, including the unchanged 7,536-byte native
prefix except three patched words, the original 192 BSS bytes initialized to
zero, and 1,504 helper/constant bytes. Both native read and edit fields retain
their offsets. The original header entry jumps to the appended header adapter;
the cursor call targets the appended cursor adapter. Existing read-mode shims,
copy/pagination hooks, acceptance/preferences, and native cursor/marker functions
remain. An executable/literal audit rejects references to the overwritten second
header instruction. Native internal calls and the new header jump remain
relocated; resident imports remain fixed.

The board and relocation move together to VROM `03B60000` and `03B70000`,
preserving their original DMA indices. Only owner row `007749C0+2B90` changes.
The shared submenu pool receives an additional 4,096 bytes. The allocator's
endpoint becomes `80890B20`, exactly 4,096 above `8088FB20`: its existing
`lui t6,8089` remains valid, while `addiu t6,t6,FB20` becomes
`addiu t6,t6,0B20`. Form the instruction explicitly so the immediate carry cannot
change its destination register. Bound the complete combined editor/tag/board
growth against this reservation; no saved data or resident module grows.

The header, cursor, and prefix-width helpers use 112-, 56-, and 32-byte stack
frames. The replaced header's original frame is 128 bytes. The actual cartridge
still uses four MiB; the added reservation is not an Expansion Pak switch.

## Bounded verification

Host checks cover complete/short/fallback names, strict packed identity bounds,
fresh animation composition, cached-reader independence, native header-only
types, exact draw spans/colours, header cursor and marker
positions, unsupported columns, body/footer forwarding, and unchanged state.
Verify compiled code, imports, relocated native calls, allocation, preceding
reader preservation, and complete cartridge/UPS retention. Reuse the unchanged
resident name loader's native evidence; ordinary editor interaction and
save/restart join combined v0 smoke.
