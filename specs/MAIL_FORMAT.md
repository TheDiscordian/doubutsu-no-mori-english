# Complete generated-letter assembly

## Implementation and limits

`tools/mail_format.py` and `runtime/mail/format.c` assemble complete header,
body, and footer text from a decoded snapshot and explicitly identified template
parts. The C formatter is freestanding and has no mutable global state. It is
linked into the resident module and passes isolated N64 CPU calls. Native mail
creation, viewing, editing, excerpts, and saves are not yet connected to it.

`tools/mail_reference.py` prepares source-verified local references from the
supplied English disc. It does not assign release catalog identities, approve
native/GameCube semantic matches, or enable wider ordinary-bank imports.
`tools/check_mail_assembly.py` cross-compiles both C files with the pinned
VR4300/o32 Docker toolchain and records object/source hashes, undefined symbols,
sections, and compiler-reported stack usage. Compilation is not MIPS execution.
`tools/mail_runtime_test_scenario.py` separately executes the installed functions
with big-endian o32 structures, guarded buffers, and complete checkpoint restore.
`af_mail_restore` connects snapshot decoding, cartridge template loading, and
complete assembly using a separate caller-owned workspace. The
[catalog contract](MAIL_CATALOG.md) fixes template identities and validates
individual source parts before publication. Gameplay creation/viewer hooks
remain separate from this restoration API.

## Reference semantics

The supplied GAFE01 executable's `mHandbill_clr_capital_flag` contains the same
five PowerPC instructions as `mHandbill_clr_force_art`. Both write value five at
handbill-data offset `190`, the article override, and neither clears the capital
flag. Both functions have SHA-256
`31ed5e79b37f74d03010f1c85c2af5cfcbc49e95150c90359f7cbb368b8caf25`.
The guarded insertion and initialization functions call those routines, while
the capitalization handler sets the separate flag. The pinned decompilation's
`BUGFIXES` alternative is not the implementation on this disc.

Consequently capitalization is sticky between insertions and letter-generation
calls. Snapshot version two stores the initial state. The assembler returns the
final state for the future generation hook; reading an existing snapshot must
not modify the generator's current state. This preserves complete, deterministic
output without replacing the observed behaviour with main-dialogue one-shot
capitalization.

Thirteen full function hashes guard the reference implementation. The four
article strings are independently checked at English general-string records
`0738` through `073B`, with complete bank/table hashes. The decoder and each of
the eight mail banks also require the supplied reference's full hashes.

### Ordered substitution

- Classic processing order is header, footer, then body. Composite order is
  header, concatenated A/B/C body, then footer. Flags may cross those boundaries;
  A/B/C boundaries are not extra lines or spaces.
- Commands `24`–`2D` and `36`–`3F` select the twenty captured free-string slots.
  A missing field is rejected; an explicitly present empty field is valid.
- Command `74` suppresses the next insertion's article. The override is consumed
  by that insertion. Command `75` sets sticky capitalization.
- Article values zero through four mean none, `a`, `an`, `the`, and `some`.
  A nonempty article is followed by one space. Capitalization affects the first
  inserted byte, including the article's first letter when present.
- Only trailing space padding is omitted from a displayed substitution, matching
  the actual backwards-scanning length routine. The saved snapshot retains all
  captured bytes, including trailing spaces. Embedded and leading spaces stay.
- For an empty insertion with capitalization enabled, the reference uppercases
  the following byte in place. The streaming implementation preserves this
  detail, including a following ordinary letter or command prefix.

Substitution bytes use the existing single-byte N64 glyph domain. `7F` and `80`
are rejected in fields; a captured value cannot introduce executable commands
or an unchecked extended glyph. ASCII lowercase letters capitalize to their
native uppercase glyphs. Unsupported GameCube accented/symbol glyphs are not
silently replaced or transliterated. Existing font assets and metrics are not
changed by this work.

### Header and layout

The header's single `CD` newline is a recipient-name insertion marker. Assembly
removes it and reports the position after expanding any earlier substitutions.
If a header has no marker, name insertion is at its end. For multiple markers,
the reference removes all markers but uses the original size for the split;
assembly preserves the resulting trailing spaces. The reference banks include
one such two-marker header. Marker bytes cannot split a control token.

All body/footer newlines and template spaces remain exact. Assembly does not
insert padding lines, fit text to the native 96-byte field, wrap words, change
timing, or truncate at the GameCube's 192-byte body capacity. Header recipient
bytes come from the native persistent recipient identity in the future reader;
the assembler returns the insertion position without inventing a recipient.
Mail types that omit the name remain a reader integration responsibility.

The result contains header/body/footer offsets and lengths, header split,
final capitalization state, and 1,024 bytes of output storage. Its offsets
reflect processing order; consumers must not assume body immediately follows
header in a classic result. All unused bytes are zero. Inputs above 1,024 bytes
per part or concatenated body are rejected, as is aggregate output overflow.
The entire result is staged before publication, so rejection leaves the caller's
destination unchanged and success permits overlap with inputs. Callers provide
correctly aligned structures and stable, valid input memory.

## Executed coverage

The Python streamer, C formatter, and independent in-place reference model agree
on every slot, field length, article, and initial capitalization combination;
random command sequences; exact capacity and rejection cases; empty fields;
header placement; classic/composite order; and overlapping buffers. The model
is derived from the guarded functions, not execution of the GameCube binary.

Of 4,866 individual reference parts, 4,807 transcode without changing glyph
identity. The other 59 remain explicitly rejected for missing glyph support.
Their IDs and exact errors are retained in the generated reference report.

The retail-input test compares 6,398 assembled cases across all classic triples,
diagonal composite replies, individual variations of every native reply part,
largest-field-union witnesses, and both initial capitalization states. Fifty-eight
requested combinations encounter rejected glyph rows. Composite combinations
are not exhaustively enumerated. Two assembled cases probe classic `0001` with
ten-byte fields; actual source-bound verification for that letter remains open.

Observed maximum header/body/footer lengths are 22/228/51 bytes, and the largest
aggregate result is 255 bytes, for those probes. These are not universal bounds
on every possible substitution and reply combination. In particular, a body
longer than the reference storage capacity is preserved for subsequent layout
review, not silently shortened. The separate exact field-union audit covers
snapshot storage feasibility, not every rendered line width.

### Resident N64 CPU coverage

The resident codec passes 215 calls and 303 memory assertions across 779 recorded
steps, including all field slots, lengths, unaligned envelopes, exact capacity,
corruption, rejection, and aliasing. The resident formatter passes 350 calls and
544 assertions across 1,652 steps, including every opcode and complete output.
A separate source-verified run passes 92 calls and 280 assertions across 611
steps for 46 selected English reference cases. Those selections include long
outputs, all twelve native reply groups, both capitalization states, and two
classic `0001` probes whose actual source-width limits remain unresolved.

The module reserves 32 KiB, with a linker-enforced 24 KiB code/data/BSS bound and
a separate 8 KiB test area. Stack and buffer guards pass; these isolated calls
do not establish gameplay mail integration or hardware compatibility.

## Integration remaining

1. Review native/reference identities in the immutable catalog and resolve the
   rejected glyph rows without changing an existing catalog's saved meaning.
2. Capture wider actual fields, articles, template selections, and initial
   capitalization during generation; choose a verified record discriminator.
3. Decode before native viewer normalization; connect complete header/body/footer
   drawing and every excerpt, editing, grading, and delivery consumer.
4. Verify real save/reload, existing saves, gifts, storage, travel, upgrades, and
   original hardware. Isolated formatter calls prove none of these by themselves.
