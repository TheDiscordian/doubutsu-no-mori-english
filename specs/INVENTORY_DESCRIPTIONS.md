# English inventory letter and delivery descriptions

## Presentation and ownership

The tag menu composes the supplied GameCube English descriptions in three lines.
Ordinary mail uses `Letter to / recipient / from sender`; delivery items use
`Delivery for / recipient / from sender`. Fortune slips use the GameCube order
`recipient's / fortune / from Katrina`. Museum recipients receive `the` before
their name. Mother uses `home`, and the Happy Room Academy uses `the HRA`.
The original N64 mail-kind dispatch remains authoritative; GC-only mail kinds
are not added to the native game.

The GameCube strings and name-colour table are checked against the supplied REL
and its complete symbol-table identity. Its D3 separator is represented by an
explicit native space, not copied as an unrelated N64 glyph. Names use the
GameCube colour roles, and ordinary prose retains native RGB 90/60/50.
The native 0.75 drawing scale, three-line window, twelve-pixel columns,
sixteen-pixel line interval, opening/closing animation, and action dispatch stay.
The actual halfwidth advances determine both fragment positions and window width.

A single overlay-owned description belongs to the first tag, the only item-name
tag initialized by native `8086FD3C`. It holds two eight-byte display names, an
owner pointer, and a kind byte. Every mail/quest initialization replaces it;
drawing performs no DMA. Ordinary items use the separate complete item-name path.
The original `tag+44` and `tag+4E` six-byte name consumers remain in bounds and
unchanged. No saved record, letter status, gift, quest, or identity is rewritten.

## Name resolution

Mail identity type one and a villager index below 216 select the complete
display-name resource at `02C00000`. Player/unsupported identities retain their
six-byte saved spelling. Type-two Museum identities display the complete English
`Museum`, including when an existing save retains the native Japanese spelling.
Special mail kinds resolve the native actor IDs:
Jingle D00F, Tom Nook D008, Redd D001, Katrina D03D, and Snowman 800D.
Failed/unsupported display lookups retain the original six-byte resolver and
two padding spaces; existing save capacity is never treated as eight bytes.

Quest names use an owned copy of native `800BB4B0..800BB5DC`, bound by SHA-256
`5634dbf8d2931f4fc194b7928700356b586fccc5e5c491120897fdbf01d06bcd`.
Only its four animal-name calls and one special-name call change. Native pocket
checks, delivery/errand lookup, saved record offsets, first-job Tom Nook
substitution, branches, and return semantics remain. Complete names are written
only into the owned description, not the native caller's two six-byte fields.

## Installation

`808700A0` jumps to an owned width/preparation bridge after native mail/quest
classification. The bridge passes the first tag, saved mail pointer at `sp+44`,
and pocket index at `sp+3C`. It returns the complete width in twelve-pixel cells,
with a minimum four, to `80870164`; the original window setup, width temporary,
positioning, and epilogue remain. `808784EC` calls the complete English drawer.

The replaced Japanese drawer occupied `80877B0C..80877EC4`. Its space holds the
928-byte English segment walker; unused bytes are padding. Old relocation rows
inside that function are removed, and the compiled English rows replace them.
The earlier 42,976-byte menu profile remains reconstructible exactly outside
that function and the three explicit changed instruction words. New helpers,
the private quest resolver, text, and zeroed description storage extend the image
to 44,384 bytes. The accepted DMA pair remains `03950000/03960000`.

The 2,496-byte aligned tag growth plus the owner's 5,568 bytes consumes 8,064 of
the existing 8,192-byte reservation. No main-code, resident-module, heap-bound,
save-format, or memory-requirement change is needed. Relocation and full-profile
validation reject changed source, incomplete code/data, altered imports,
overlapping allocation, and missing full-name dependencies. Earlier profiles
remain verifiable; their passing tests are not new native execution evidence.

## Counting and verification

Eight original embedded Japanese records belong to the combined counter:
fortune, HRA, delivery, letter, recipient suffix, sender suffix, mother, and
the canonical Museum spelling at main-code address `8010AE40`.
Shorter museum/sender suffixes alias the containing four-byte record and do not
count again. Name-display consumers add no duplicate name credit.

Focused checks cover complete English line order, colours, fragment positions,
eight-byte names, saved spelling, special senders, reset, buffer guards, actual
font widths, source-bound quest control flow, hook ABI, relocation, all earlier
resources, and patch reconstruction. Normal mail/item/menu transitions belong
in the combined v0 safety pass. Source and host checks alone do not establish
ordinary gameplay, save/restart, or original-hardware acceptance.
