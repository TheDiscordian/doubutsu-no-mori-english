# Immutable English letter catalogs

## Contract

The cartridge resource stores complete reference templates, not expanded saved
letters. Snapshot catalog IDs identify immutable wording, glyph encoding, part
numbering, and assembly semantics. A changed template or encoding requires a new
ID; readers must retain old catalogs or provide a verified lossless migration.
IDs one and `FFFF` are test-only. ID two names the initial GAFE01 reference
catalog, with missing glyph rows explicitly unavailable. Its registered hashes
freeze that exact content; it is not an approval of native/reference matching.

Catalog construction requires the supplied English disc's verified banks,
decoder, and executable semantics. Generated wording remains local. The registry
contains only original metadata and hashes. A registered catalog cannot be
silently regenerated with changed text, normalization, or missing-row treatment.

## Binary layout

All integers are big-endian. VROM `03000000` is the catalog resource location.
The resident header's optional configuration word at offset `44` enables it.
The resource is bounded by one MiB and uses sixteen-byte-aligned DMA regions.

The 128-byte header contains eight words: magic `41464D4C`, format one, catalog
ID, assembly semantics one, complete file size, eight banks, directory offset
128, and sixteen-byte row stride. Bytes 32–63 contain the SHA-256 of everything
after the header. The remaining 64 bytes are zero. The registered complete-file
hash and payload hash are checked during installation; runtime readers check the
registered identity/header and each selected part's CRC-32.

The eight sixteen-byte directory entries follow at offset 128. Each contains
bank index, count, row-table offset, and zero. Bank order is `super`, `mail`,
`ps`, `superz`, `maila`, `mailb`, `mailc`, `psz`. The three classic counts are
982; the five composite counts are 384. Tables follow in bank order, with one
sixteen-byte entry per original reference ID. Numeric order is not permission to
substitute a GameCube record for a native record without semantic matching.

Each row contains a four-byte payload offset, two-byte length, two-byte flags,
four-byte twenty-field mask, and four-byte CRC-32 (IEEE, matching `zlib.crc32`).
Flag zero means available, including genuinely empty entries. Flag one means
unavailable and requires every other row field to be zero. Other flags fail.
Available payloads follow in row order, padded with zeroes to sixteen bytes;
empty entries consume no payload. No deduplication changes this canonical layout.
Each part is at most 1,024 bytes, retaining every explicit space and newline.

## Loading and restoration

Classic snapshots select one ID in all three classic banks. Composite snapshots
select their five recorded IDs in the five composite banks. A reader validates
the catalog, bank, index, range, flags, field mask, CRC, and source controls before
assembly. Unknown catalogs, unavailable entries, malformed tables, DMA errors,
and overflow fail; they never become blank successful letters.

The caller provides a separate aligned workspace holding the decoded record,
template descriptors, and 3,104 source-buffer bytes: up to 3,072 text bytes plus
the two additional alignment gaps between composite body parts. The three output sections
each retain the assembler's 1,024-byte input limit; the combined body parts share
one such limit. Workspace contents may change on failure, but the published
letter output and saved snapshot must remain unchanged. The workspace must not
overlap the snapshot or output and must not live in a small nested caller stack.
The existing formatter stages and publishes only a complete successful result.

Installing this resource does not install native mail-generation, discrimination,
viewer, editing, or save hooks. Those consumers must be connected explicitly.
The 59 unavailable reference parts and classic `0001` source bounds remain
completion requirements, not exclusions from the project.

## Executed evidence

The registered resource is 319,344 bytes and preserves all 4,866 reference
indices: 4,807 available parts and 59 explicit unavailable rows. Complete-file
SHA-256 is `d77591525d105391cf8190257b8ea768f521810d4ae5a36d27bcca991442a5e1`.
The host C reader agrees with the independent reference model on all 6,398
assembled probes. The probe set is not every possible composite combination;
classic `0001` still uses the explicitly limited ten-byte test fields.

The cartridge-read N64 CPU scenario passes 84 calls and 259 memory assertions
across 540 recorded steps. It restores 46 selected reference letters from real
DMA data, checks both captured capitalization states and unaligned snapshots,
rejects unavailable/out-of-range parts and unknown catalogs, checks disabled
configuration, and mutates every header word. Complete output and source/stack
guards pass; the machine checkpoint is restored. Host tests additionally cover
each selected DMA failure, modified directory/row/data bytes, CRCs, source masks,
padding, workspace aliasing, and immutable registry/installer rejection.

The o32 workspace is 3,552 bytes and remains caller-owned. Compiler-reported
stack frames are 256 bytes for restoration, 1,224 for assembly, 152 for nested
packing, and 408 for unpacking; the complete call paths must still be checked in
real gameplay callers. These APIs introduce no mutable global data or BSS.
