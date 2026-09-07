# Generated-letter snapshot format

## Scope and integration state

This is a lossless storage prototype for generated letters. The Python reference
codec is `tools/mail_record.py`; the freestanding C implementation is
`runtime/mail/record.c`. The C file is deliberately outside the resident module's
top-level source list and is not installed in a playable ROM.

The snapshot stores immutable template identities plus the exact substitutions
and article choices captured when a letter is created. Reading an old letter
must not draw new random words, obtain current town names, or select a different
template. Native recipient/sender identities, gifts, stationery, and other
metadata remain separate. No template IDs are approved semantic matches merely
because they share a number with a GameCube record.

This format does not store arbitrary rewritten letters of unrestricted length.
Custom editing remains a separate representation requirement. In particular,
editing a generated letter may not discard its full text to fit this prototype.
The native editor's limits and the GameCube reference's larger text capacities
must remain distinct in all compatibility claims.

## Wire format

The envelope occupies the complete 122-byte contiguous native text area. For
`Mail_c`, this is offset `2A`; for `Anmplmail_c`, it is offset `05`. Offsets below
are relative to that text area. Multibyte integers are big-endian.

| Offset | Bytes | Meaning |
| --- | --- | --- |
| `00` | 1 | Magic `AF` |
| `01` | 1 | Version one in the high nibble; kind in the low nibble |
| `02` | 1 | Used bytes, including checksum, at most 122 |
| `03` | 2 | Nonzero immutable catalog identity |
| `05` | 3 | Twenty-field presence bitmap; upper four bits must be zero |
| `08` | 2 or 10 | One classic letter ID, or five composite part IDs |
| variable | variable | Present fields, in ascending index order |
| used minus 2 | 2 | CRC-16/CCITT-FALSE of all preceding used bytes |
| used | remaining | Zero padding to 122 bytes |

Kind zero has one ID naming a header/body/footer triple. Kind one has five IDs
in `superz`, `maila`, `mailb`, `mailc`, `psz` order. Every ID is sixteen bits;
catalog lookup must independently verify that the requested entry exists.

Each field has one metadata byte followed by zero to sixteen literal bytes.
The metadata's low five bits hold its length; the high three bits hold its
article: zero for none, one for `a`, two for `an`, three for `the`, and four for
`some`, matching the English reference enum. Other article values are invalid.
Trailing spaces, empty-but-present fields, and repeated or non-Latin byte values
are preserved. Missing and empty fields are different states.

CRC parameters are polynomial `1021`, initial value `FFFF`, no reflection, and
no final XOR. The checksum detects accidental damage; it is not authentication.
Decoders reject unknown versions/kinds/catalogs, reserved bits, missing payload,
invalid field metadata, extra payload, bad checksums, and nonzero padding.
Both C operations stage results and leave destinations unchanged on rejection,
including when source and destination overlap. C record pointers require their
normal structure alignment; the encoded byte buffer does not.

## Catalog and native record discrimination

A catalog identity must name an immutable mapping of templates and their exact
rendering semantics. Updating wording requires a new identity, retaining support
for existing saved catalogs or a verified migration. Catalog numbers must not be
reused or derived by truncating a hash. The resource builder must validate full
content hashes, and readers must reject unavailable catalog identities. Test
catalog number one is synthetic; no release catalog is assigned by this codec.

The magic byte is not sufficient to distinguish snapshots from native text.
Native letters can contain arbitrary font bytes. A verified external record
discriminator and complete reader audit are required before installation. No
native `font`, `mailType`, or other metadata bit is currently assigned for this
purpose. Passing a snapshot to the native text renderer is forbidden.

The codec treats field bytes as literal data. A future formatter must separately
validate its glyph/control domain and never recursively execute arbitrary field
bytes as mail commands. Codec acceptance alone does not approve text rendering.

## Exact capacity evidence

Classic overhead is twelve bytes; composite overhead is twenty bytes. Each
present field costs one metadata byte plus its literal length. Thus six
sixteen-byte fields and five composite IDs occupy exactly 122 bytes, including
the checksum. Overflow is rejected, never shortened.

`tools/audit_mail_templates.py` reads the actual extracted English bank bytes
and records hashes of every data/table input. It computes every distinct union
of fields for the twelve native reply groups, retaining a concrete combination
of part IDs for the largest union. This is an exact union calculation, not a
random sample. The 32-entry group boundaries and both native start tables are
checked against the original selection routine at `800A8DB4` through `800A8F30`.
Its SHA-256 is
`97919d8a755e399b85a058203f2b48bbac5efbfdd2ba6f3dff17f24b4784bdc3`.
The two sixteen-entry halves of the middle component together cover its full
32-entry range across the native gift/no-gift alternatives.

All twelve groups fit with every used substitution at sixteen bytes; the largest
needs six fields. Of 982 classic English records, 981 fit the same conservative
bound. Within the 544 native numeric IDs, 543 fit. Record `0001` uses ten distinct
fields and needs actual per-field bounds or another complete representation;
it is not declared unreachable or silently excluded from the translation goal.
These counts prove storage feasibility, not translation identity or full-output
rendering. Generated detailed evidence stays in `build/audits/mail-templates.json`.

## Required integration work

1. Define a collision-free native record discriminator after auditing every
   metadata reader, copying operation, and persistent destination.
2. Build immutable, source-verified template catalogs with reviewed identities,
   complete wording, original line breaks, and frozen substitution semantics.
3. Expand mail free-string sources with exact source identity and article data,
   capturing only used fields without losing original random selections.
4. Implement bounded full-text assembly, including header-name placement,
   capitalization/article behaviour, and all display/excerpt readers.
5. Implement lossless editing and conversion between generated and custom mail,
   including villager mail grading and quest checks.
6. Prove delivery, gifts, post-office storage, travel, actual save/reload, old-save
   behaviour, catalog upgrades, and original-hardware operation.

The current resident module uses 7,488 bytes. Its native test fixtures reserve
addresses beyond the first 8,192 bytes, so adding the codec requires a reviewed
module/test-memory layout change. The standalone MIPS object has no undefined
symbols or persistent data; compiling it does not prove runtime integration.
