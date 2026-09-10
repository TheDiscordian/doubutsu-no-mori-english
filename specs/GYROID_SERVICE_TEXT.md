# Gyroid service responses

## Source and matching

Native owner `00794380`, RAM `8088CBD0`, is 3,856 bytes, SHA-256
`3aa5fc187475a596bf7360b66bd2b3ea9de72d98277f45fa6ad1a1d37b03d039`.
Its `00795290` relocation is 192 bytes, SHA-256
`c292e1fbd6bc837d46ab976bb807b8d9d6481c1bdce00c22951507b432d24ce7`,
with sections `(3616, 240, 0, 48, 42)`. Parent metadata at `007749C0 + 2BD0` is
`00794380 00795290 8088CBD0 8088DB10 8088D924 8088D9D4 8088D81C 00000000`.

Twelve pointer/length entries at owner offset `0E94` select the sales/configuration
responses. The three-character prefix at `0E20`, "それは", introduces states
8–11; state 11 additionally inserts the selected native five-digit price.
These are live menu responses, separate from the custom/default home greeting.
Bind the supplied GC `mHW_make_cond_message` strings in `.data:0007FD60..0007FE24`.
The native state order maps to GC 0, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, and 12.
Do not import GC's extra state or change native selectors.

Use the full GC wording for each response. Free/display/configuration states
are complete phrases without the Japanese prefix. The price state uses
"It's " + unchanged native digits + " Bells". The donor's `D3` wide-space
glyph advances six pixels in its verified font table, exactly matching this
build's ordinary space. The apostrophe is already ordinary ASCII in the donor.
No item, wallet, price storage, sale action, or saved layout changes.

## Transient buffer and installation

The native transient message has only twelve bytes at state `+20`. Its callback
is at `+2C`, immediately after those bytes. Increasing the copy length in place
would overwrite a function pointer. Preserve the entire old 48-byte state and
callback address. Add a separate 32-byte transient buffer at state `+30` and
redirect the three explicit compose/initialise/draw buffer origins to it.
Use the GC 22-character clear/reveal limit; retain one revealed character per
update, native colours, font scale, location, and all input decisions.

Append zero-filled old state plus the new 32-byte buffer, then complete English
strings. Redirect the twelve existing table pointers/counts and the existing
prefix high/low relocation. Flatten section offsets while preserving all 42
relocation types/sites/order and the original state address. No additional
pointer sites are introduced. Reserve VROM `03E40000`/`03E50000`, retaining the
original adjacent DMA indices and only the reviewed parent row.

The existing embedded-warning 4-KiB menu reservation must cover the conservative
sum of both warning growths and this owner's growth. Keep the same pool word,
ordinary four-MiB heap, and Expansion Pak title allocation. Shared owner checks
accept the new row only after exact resource, relocation, and pool verification.

## Verification

Check complete original/donor identities and source-state mapping, every patched
instruction, full pointers/lengths and relocation at three ordinary heap bases,
all selected prices within the native unsigned-16-bit range, and the retained
callback/old state. Every complete response must fit the 22-character buffer
and original message width. Retain unrelated resources and reconstruct UPS.
Use a bounded native composition/drawing check for the changed transient buffer;
do not invoke sales or write the user's saves. Ordinary gyroid interaction and
hardware acceptance remain separate from controlled tests.
