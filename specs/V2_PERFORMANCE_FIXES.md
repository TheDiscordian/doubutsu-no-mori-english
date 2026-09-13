# V2 museum recipient and performance fixes

## Report and cause

The user reports Japanese in the faraway museum's address-list entry and long
screen freezes during K.K. Dirge, selected by K.K. without a song request. Music
continues normally. Keep the existing V2-07 cartridge and saves intact.

The address display helper receives an 18-byte Mail_nm. Type one resolves a
villager index; type two is the museum. The missing type-two display case falls
back to six saved Japanese bytes. Resolve that display to `Museum`, without
altering saved identity, recipient selection, or delivery logic.

The native font arena contains 0x700 eight-byte commands. Credits draw every
byte of each 25-byte padded row, including blank rows and trailing spaces.
Nine rows request 225 glyphs; the current polygon path uses nine commands per
glyph, exceeding the 1,792-command arena even before row setup. Eight-row pages
also exceed it. `graph_draw_finish` detects the exhausted arena, and `graph_main`
skips submitting the frame. Audio continues independently.

## Correction constraints

Trim only trailing ordinary-space bytes from the credits draw length; do not
change stored text, leading indentation, internal spaces, X/Y origins, glyph
advances, scales, page boundaries, fade timers, song selection, or audio code.
An all-space row needs no draw call. Native code still advances the stored row
pointer by 25 and controls every row's Y position.

Use the 68 verified zero bytes at `80AA47A4..80AA47E8`, after the already installed
16-byte full-song-title helper. A 56-byte leaf adapter passes the existing ABI
and stack arguments through to `80090E1C` with only the shortened length. The
call at `80AA3FFC` uses a PC-relative branch-and-link so relocation tables,
actor size, BSS, and allocation remain unchanged. Preserve the request-echo
entry at `80AA47E8` and all song logic.

The address helper is rebuilt with its museum case, retaining the native
prefix, complete villager lookup/fallback, and all other UI helpers. Check its
allocated owner and existing submenu reservation before installation.

## Bounded verification

Check both input hashes, the entire preceding owners and relocations, source
ABI, strict branch/cave bounds, and unrelated resource retention. Use sanitizer
tests for museum/villager/player/unknown recipient identities. Compile with the
pinned Docker toolchain. Reconstruct the UPS from the original ROM.

Use one current-build native batch with an isolated blank save. Measure credits
command usage against the real font capacity, compare visible glyph geometry,
and check all sixteen pages and representative fade points, complete loaded
text, guards, and saved-data restoration. Reproduce the untrimmed draw in owned
test memory, never submit an overflowing list. These checks do not claim a
full hardware performance or another ordinary save/reload playthrough.
