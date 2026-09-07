# Complete NPC reply-word source resource

## Scope

`tools/npc_mail_words.py` prepares 352 complete English phrases for the eleven
native randomized reply-word families. It verifies the original and legacy
string-bank data/tables, the supplied English string bank, the native/reference
creator contracts, the English string loader and field setter, and the decoder source.

Every selected English phrase exactly equals the complete transcoded legacy
value for the native-selected ID. This comparison does not trim spaces, fold
case, accept a prefix, or infer identity solely from a shared numeric ID.
Native and reference hashes are recorded per row. The resource and manifest
remain local under `build/npc-mail-words/`; no resource or capture hook is
installed in the production ROM.

All 352 values fit sixteen bytes. Eighty-three exceed ten bytes, so those values
cannot pass through the original ten-byte temporary without losing text. The
resource does not replace the shared native string bank or enlarge arbitrary
callers. It supplies complete literal values for the separate generation capture.

## Identity and random selection

Rows are ordered by native field slots three through thirteen, with 32 selected
values per slot. The exact native and reference bases are checked against the
[creator contracts](NPC_MAIL_GENERATION.md). Fish and insects use the verified
first 32 entries of their respective 40-entry English families. The additional
eight entries are not substituted for native creatures or added to random draws.

`lookup` consumes a validated row tuple, a field slot, and the native-selected
string ID. It rejects a wrong slot, out-of-family ID, or inconsistent identity.
It returns the full `Field` value for the existing snapshot codec. It never
draws randomness, picks another phrase, or shortens a word. All fields use article
zero: the English NPC preparation uses `mHandbill_Set_free_str`, whose actual
instructions clear the corresponding article word after setting the string.
Template-directed article suppression and sticky capitalization remain the
existing formatter's responsibility.

The compact resource and Python `lookup` preserve literal lengths. The actual
English loader space-pads the sixteen-byte temporary before the setter receives
it, so the [native capture consumer](NPC_MAIL_CAPTURE.md) captures length sixteen
and preserves that padding. Only formatting omits trailing padding from display.
Both complete English executable routines are hash-guarded; a changed loader or
setter is rejected even if the extracted string bank itself is unchanged.

This source mapping is mechanically verified. It is not approval of every
containing letter's meaning or evidence that normal gameplay captures these
values. Player/NPC/town names, capture lifetime, on-demand loading, and creation
failure propagation remain separate bindings.

## Canonical binary format

The candidate resource occupies 11,328 bytes, with a 64-byte header and 352
32-byte rows. Integers are big endian. It has no assigned cartridge VROM address
and is not a persistent save format.

| Header offset, decimal | Field |
| --- | --- |
| 0 | Magic `AFNW`, unsigned 32-bit |
| 4 | Version one |
| 8 | Row count 352 |
| 12 | Row width 32 |
| 16 | Header width 64 |
| 20 | Family count eleven |
| 24 | Complete field capacity sixteen |
| 28 | Reserved zero |
| 32 | SHA-256 of the complete row payload, 32 bytes |

| Row offset, decimal | Field |
| --- | --- |
| 0 | Native string ID, unsigned 16-bit |
| 2 | English reference ID, unsigned 16-bit |
| 4 | Field slot, unsigned byte |
| 5 | Literal length, one through sixteen |
| 6 | Article zero |
| 7 | Reserved zero |
| 8 | Sixteen literal bytes, zero-padded after the declared length |
| 24 | Eight reserved zero bytes |

Every row must have the exact expected source/reference identity at its position.
Only supported plain Latin glyph bytes are accepted; command bytes, extended
glyph prefixes, newlines, empty words, overflow, and nonzero padding are rejected.
Explicit spaces within a value remain intact. Packing/unpacking is canonical.

The embedded digest establishes structural integrity, not source approval. A
consumer of generated content must also check the expected complete resource
hash obtained from verified preparation. A modified word with a recomputed
embedded digest is still rejected against that complete hash. Tests explicitly
distinguish these two checks.

## Verification and next integration

Eight tests cover every row and lookup, snapshot field round trips, all native
family boundaries, record order, field/article/glyph constraints, padding,
header/payload corruption, bound content hashes, all three source banks/tables,
changed decoder output, and both complete executable source routines. Retail checks verify all 352 full phrases directly
against both English and legacy sources, not an editable inventory file.

The runtime consumer must validate its source and row before publishing a field,
invalidate a failed replacement, and preserve the native-selected ID. It must
capture the full value before the ten-byte native loader truncates it. Bounded
loading and real cartridge-read/failure tests remain required before installation.
