# Retained reserve letters

Classic templates `00C0..00C4` use complete English `Extra` in their native
header, body, and footer banks. The header retains one newline, the body retains
six, and the footer has none. The native source is the two-character reserve
label in every part. The supplied English GameCube disc translates the header
and footer but leaves the original Japanese body bytes in place. The body edit
is an original translation matching those English edges, not a conversion of
the donor decoder's misleading accented characters.

The three values require 6, 11, and 5 bytes, respectively, within the unchanged
10/96/16-byte destinations. No commands, new runtime code, selectors, or saved
layout changes are required. Both immutable catalogue four and catalogue five
remain unchanged; these native-only reserve IDs are not newly selected by a
snapshot creator.

`tools/reserve_letters.py` verifies the retail source, complete donor bank
hashes, decoder, native letter loaders and capacities, exact predecessor, and
all fifteen source records. It rebuilds the three data banks and their existing
tables. The body payload grows one byte beyond its original DMA size. Fifteen
zero padding bytes keep the file aligned, so the DMA range grows sixteen bytes
within the existing virtual address gap before its table. The packer's explicit
same-base resize retains the native loader address. Every rounded eight-byte
read remains inside the complete file; no virtual base is moved.
The combined counter reads the complete installed standalone variable bank,
including that final byte. Sub-bank slicing remains unchanged.

The installer reconstructs the cartridge from the retail ROM and retained
predecessor payloads, checks the complete six-file update, and verifies the UPS
round trip. Unchanged runtime and saved-letter consumers reuse prior evidence.
Focused tests cover complete wording, intentional line breaks, bounds, all
unmodified records/files, the extended bank's last row, and installed accounting.
