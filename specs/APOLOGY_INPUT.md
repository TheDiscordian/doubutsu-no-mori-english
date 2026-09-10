# Sun/skull apology input

## Required behaviour

The two remaining exact GC targets are `U R my ☀!` and `Reset = 💀`, mapped to
`string:048E` and `string:0491`. Their native encodings are respectively
`55 20 52 20 6D 79 20 80 A7 21` and
`52 65 73 65 74 20 3D 20 80 BA`: ten bytes each. Both symbol glyphs are already
present in the verified separate font. No approximation, substituted Japanese
glyph, shortened wording, or expanded saved field is required.

The apology buffer is temporary and ten bytes long. Input must insert/delete
each registered pair atomically, navigate between complete tokens, and keep
byte offsets for the native font's prefix-width and drawing APIs. The original
case/kana exchange must never modify the second byte of a symbol. Unknown or
truncated pairs and an interior cursor reject without changing state.

Other editors retain their current contracts. Player/town names, saved custom
catchphrases, letters, song requests, and the owner-message editor must not gain
two-byte input permission merely because the apology editor can use it.
Exact-apology comparison still precedes the unchanged English rude-reply matcher.

## Portable editing core

`overlays/apology_input/edit.c` operates on an explicitly owned ten-byte draft,
byte length, and byte cursor. The eight command numbers retain the native order:
left, down, up, right, done, backspace, exchange, and insert. Up/down do nothing
in this single-line field. Right moves over one complete token or inserts a
space at the end, matching the native editor. Newline insertion does nothing.
Done validates the draft and returns a distinct completion result for its owner;
the core does not close a window or copy into any saved or caller-owned field.

Valid single-byte input keeps its native encoding except command/tag prefixes
and newline. Only the sun/skull two-byte codes can enter this draft. The tail
remains space padded, including after middle insertion/deletion. Every failure
preserves text, cursor, length, and caller guards. No heap/global state is used.

## Native integration boundary

The native editor holds command/code/processed at `11/13/15`, byte cursor at
`16`, capacity at `18`, byte length at `1C`, exchange code at `1E`, and input
pointer at `24`. Its single-line handler is `808863B8`; original insertion is
`80885D2C/80885D94`, backspace `808860FC`, and exchange `80886168/808861AC`.
These routines currently advance single bytes. The generic editor's complete
owner-message variant already has independent init/cursor/command hooks and
must remain intact when an apology-only variant is added.

The adapter identifies name-entry kind three at `submenu.overlay+101E0`, editor
kind three at its menu `38`, matching input pointers at `101E8` and editor `24`,
ten-byte capacity, and one row. Init delegates to the complete owner editor
before capturing that identity; destruction clears the context before chaining
the previous destructor. Other name, song, mail, and owner-message modes delegate
unchanged. Invalid owned text cannot fall through to a single-byte edit.

In the apology symbol page only, key IDs `84/81/85` (Japanese comma, Japanese
period, middle dot) select sun, skull, and equals. The equals key is also needed
for the exact second target and is absent from the original radial tables.
Selected keys produce complete `80A7/80BA/3D` input; the key IDs are never saved
as aliases. A scoped wrapper at keyboard-character draw call `808877E4` emits
the same complete glyph tokens with all original colours, scales, and positions.
Native period/comma remain available through English punctuation keys.

The intended single-line command pointer is `80888830`, whose original value
is `808863B8`. Exchange preparation calls `80886168` at `80886950`; the adapter
returns unavailable when the preceding input token is a sun/skull pair.
Existing owner-editor init/cursor/destructor hooks chain through the new variant.
The exact preceding 20,416-byte image remains as the prefix, with five guarded
hook edits and one additional original-site relocation. The appended adapter
and context increase the complete image to 23,168 bytes. The relocation table
is 1,680 bytes and retains every preceding relocation. Code and relocation
hashes, source hashes, imports, ELF relocation inventory, and independently
reproduced compiler output bind the installed variant.

## Shared allocation and installation

The editor retains VROM `03940000/03948000` and its native DMA indices. The
submenu owner row changes only its image bounds and destructor target. Existing
owner-window drawing and all letter-editor hooks remain installed. A 256-byte
addition changes the final submenu pool from 247,168 to 247,424 bytes; the
conservative combined requirement is 247,232 bytes. Total shared growth is
12,352 bytes within the 12,544-byte reservation. The exact final pool instruction
at `800C4B10` is `25CE0C20`; the preceding high instruction remains `3C0E8089`.
No permanent resident-module, heap boundary, or saved-layout change is made.

`--english-apology-input` requires the complete owner and letter editors,
English Resetti matcher, and verified fourteen-cell font. Its two source-bound
permits allow only the exact ten-byte targets, with no new general-string or
name-input permission. The output verifier checks the actual installed image,
metadata, allocation, font, native loader, all 32 rude replies, and unchanged
matching code. Combined accounting credits these two records only after that
verification; resource presence or a portable-core test alone cannot grant credit.

`tools/build_apology_input_pilot.sh` reproduces the complete integration. The
[checkpoint](../docs/checkpoints/APOLOGY_INPUT.md) records build and test results.
Ordinary controller navigation and broader editor interactions remain in the
combined v0 gameplay check, with original-hardware acceptance in playtesting.

Use focused host/core tests, guarded assembly/relocation checks, and one bounded
combined native editor/matcher check. This work does not require replacing the
entire keyboard with the v1 GameCube-style grid.
