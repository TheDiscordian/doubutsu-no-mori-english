# Villager secret letters

## Verified source and complete text

`tools/audit_secret_letters.py` verifies the original ordinary-conversation
overlay and relocation, its 156-byte secret-letter function, the supplied
English counterpart, and all 45 header/body/footer parts for templates
`0022..0030`. Neither source has free fields in these fifteen letters. The
complete texts require glyph catalogue four; catalogue two cannot represent
every supplied glyph. No wording, manual break, header, or footer is shortened.

The native overlay is VROM `00815B70`, linked RAM `8091D7B0`, relocation
`0081A1A0`. Its original file is 17,968 bytes, with section sizes
`{16768,1200,0,352}` and 552 relocation entries. The 156-byte function
`8091E960..8091E9FC` has SHA-256
`1f431bce746b485434b90471780e07add04acbbf87e8791a62672c00722a976a`.
The supplied `aQMgr_get_memory_mail_secret` has SHA-256
`f1fa6dc41cdacb0e1fb0c197196ee0c63c30893e18110138bc783211900cb088`.

The native function calls `8002C9AC`, multiplies its random fraction by fifteen,
truncates it, and adds `22` hexadecimal. It formats into the static compact
record at `80921B54`: font at offset zero, paper at one, split at four, and
the 122-byte text envelope at five. Header/body/footer begin at offsets
five/fifteen/111. It then gets the original paper through `800A9364`, clears
the selected-memory output pointer, and returns the static compact record.
Preserve the original random and paper call sequence, static storage lifetime,
present/date/padding semantics, and existing caller fallback on a null result.
The complete compact record is 132 bytes, not a 164-byte mailbox letter.

## Prepared snapshots

`build/secret-letter-snapshots/snapshots.bin` is a 600-byte immutable table:
fifteen templates, two capitalization states, twenty bytes per row. Each row
contains template BE16, final capitalization, reserved zero, and the first
sixteen bytes of the complete packed record. The record uses twelve bytes;
all remaining bytes in the 122-byte envelope are zero. The generator proves
complete formatter/reader output for every row before writing the table.
Table SHA-256 is
`ac0a0a3c9c50a6a3a448e3b5eb58ddfdd53a2d8d44763ccae06dbec3c9c121fe`.
`approval.json` retains every source hash and all thirty full reconstruction
cases. Two source/snapshot tests pass in `build/secret-letter-audit-tests.log`.
These artifacts are prepared inputs, not installed translation or native proof.

## Integration requirements

Append a small fixed-snapshot creator and the immutable table within the
ordinary overlay's managed allocation. The no-field texts permit complete
creation without new per-letter allocation or cartridge text reads. Preserve
the overlay's writable data, BSS, all original relocation semantics, and loader
metadata. Reject invalid capital/choice before modifying the static result.

Do not build the replacement from an unmodified original overlay and overwrite
existing translation work. In the shop-notice ROM this overlay already has
fifteen changed instruction words, with SHA-256
`37dc2946031c2d79a4b0ecb9facaff1e5ec77ac247b77a0493df7a50ea74af95`.
The changes belong to `dialogue_dates.py`, `resident_words.py`, and
`birthday_fields.py`: complete date helpers/leap text, wider item fields and
stack temporaries, and the birthday formatter hook. Retain those patches and
their adjusted relocation inventory when enlarging this overlay. Source-bind
the installed prefix and prove every unrelated instruction/resource remains.

Acceptance includes all fifteen native random choices, both capitalization
states, original paper/RNG comparisons, compact conversion and full readback,
the ordinary letter-show path, invalid-input/fallback handling, relocation at
multiple allocations, restored globals/heap/checkpoint, and earlier date/item/
birthday behaviour. Normal villager interaction, save/reload, presentation
review, and original hardware remain broader project acceptance.
