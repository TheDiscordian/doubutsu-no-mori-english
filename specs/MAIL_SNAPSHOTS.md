# Generated-letter snapshot format

## Scope and integration state

This is a lossless storage prototype for generated letters. The Python reference
codec is `tools/mail_record.py`; the freestanding C implementation is
`runtime/mail/record.c`. Full-letter assembly is implemented separately in
`tools/mail_format.py` and `runtime/mail/format.c`. Both C files are linked into
the experimental resident module and pass isolated N64 CPU calls. Native
generation, readers, editing, and persistence are not connected to these APIs.
See [assembly semantics and executed coverage](MAIL_FORMAT.md).

The snapshot stores immutable template identities plus the exact substitutions,
article choices, and initial capitalization state captured when a letter is
created. Reading an old letter must not draw new random words, obtain current
town names, or select a different
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
| `01` | 1 | Version two in the high nibble; kind in the low nibble |
| `02` | 1 | Used bytes, including checksum, at most 122 |
| `03` | 2 | Nonzero immutable catalog identity |
| `05` | 3 | Twenty-field presence bitmap; bit 20 captures initial capitalization; upper three bits must be zero |
| `08` | 2 or 10 | One classic letter ID, or five composite part IDs |
| variable | variable | Present fields, in ascending index order |
| used minus 2 | 2 | CRC-16/CCITT-FALSE of all preceding used bytes |
| used | remaining | Zero padding to 122 bytes |

Version two is the current prototype; gameplay does not generate these records.
Version-one envelopes are
rejected; no version-one catalog or generated-mail save format is released.
The initial-capital bit preserves GAFE01's actual sticky capitalization state
without making an existing letter depend on global state when reopened. It does
not increase the record's storage requirement.

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
catalog numbers one and `FFFF` are test-only; no release catalog is assigned by
this codec or the local reference preparation tool.

The magic byte is not sufficient to distinguish snapshots from native text.
Native letters can contain arbitrary font bytes. A verified external record
discriminator and complete reader audit are required before installation. No
native `font`, `mailType`, or other metadata bit is currently assigned for this
purpose. Passing a snapshot to the native text renderer is forbidden.

The codec treats field bytes as literal data. The standalone formatter separately
validates its glyph/control domain and never recursively executes arbitrary
field bytes as mail commands. Codec acceptance alone does not approve rendering.

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

### Native viewer constraints

`tools/mail_viewer.py`, included in the mail audit, verifies the complete native
`board_ovl` at VROM `007908A0`, linked RAM `80888E90`, 7,536 bytes. SHA-256:
`abade0c99f31b39b2a2b0b80c3ad1557ba5d9aadf1b10b512a662a4b76b3cbad`.
These are linked overlay addresses, not permission to call those addresses in a
live emulator without resolving the loaded overlay.

The native board object is `C0` bytes. Its embedded `Mail_c` begins at `08`,
with text fields at `32`, `3C`, and `9C`; its source/destination pointer is at
`AC`. Three one-byte lengths live at offsets `05`, `06`, and `07`. The board
pointer is at submenu overlay offset `106E4`.

| Consumer | Linked address | Verified constraint |
| --- | --- | --- |
| Initial copy | `8088A47C` | Copies an existing native record into the board object |
| Initialization | `8088A2D0` | Scans 10/96/16-byte fields and normalizes footer padding |
| Header split clamp | `8088A538` | Clamps values above ten and writes the clamped byte at `8088A54C` |
| Body renderer | `80889A9C` | Six lines, sixteen characters per line, explicit `CD` newlines |
| Header renderer | `80889CD8` | Local header assembly, native name insertion, and special mail-type cases |
| Footer renderer | `808899E4` | Right positioning uses the native sixteen-cell geometry |

The read-only open mode is one; the initializer selects wait state two for that
mode. Other modes may enter an editor. Exit/writeback paths and every caller's
mode still need validation before treating a generated-letter view as read-only.

A header-split flag would be erased by the current initializer's clamp. A
decoder must run before any such normalization, and opaque bytes must never be
passed through the native body/footer length and rendering paths. Full English
rendering must preserve reference newlines and use verified pixel widths; merely
doubling the sixteen-character limit is not proof of matching GameCube layout.

The field named `font` in the native decompilation also controls mail behaviour:
`FF` means an unused slot, the send check at `8009C89C` accepts value one, and
the attachment check at `8009C8C0` accepts one, three, or four. That byte is not
an available tag without updating its consumers. No discriminator is assigned
by this audit.

### Remaining implementation

1. Define a collision-free native record discriminator after auditing every
   metadata reader, copying operation, and persistent destination.
2. Build immutable, source-verified template catalogs with reviewed identities,
   complete wording, original line breaks, and frozen substitution semantics.
3. Expand mail free-string sources with exact source identity and article data,
   capturing only used fields without losing original random selections.
4. Integrate the bounded full-text assembler with header-name placement and
   all display/excerpt readers. Preserve its captured capitalization/article
   behaviour without changing generation state when reading existing letters.
5. Implement lossless editing and conversion between generated and custom mail,
   including villager mail grading and quest checks.
6. Prove delivery, gifts, post-office storage, travel, actual save/reload, old-save
   behaviour, catalog upgrades, and original-hardware operation.

The resident module uses 10,336 linked bytes within a 32 KiB reservation. The
linker limits code/data/BSS to the first 24 KiB; isolated native-call fixtures
and stack use the separate final 8 KiB. Actual codec, formatter, and selected
English reference tests pass with complete output and memory/stack guard checks.
The source inventory includes nested mail files and rejects stale artifacts.
Neither compilation nor isolated API execution proves gameplay or save integration.
