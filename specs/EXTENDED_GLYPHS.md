# Separate English glyph resource

## Implemented scope

Five otherwise unrepresentable English reference characters have an exact-source
resource, bounded C measurement/selection functions, and relocatable native draw
adapters. Both original native drawing paths pass isolated execution. This is
not a production installation: cartridge loading, message reveal, input/save
acceptance, and translation-import permissions remain required.

The approved N64 atlas, Japanese cells, and existing Latin spacing stay unchanged.
This work does not resume the paused atlas-edge investigation.

| Character | Proposed two-byte encoding | Pixel advance |
| --- | --- | ---: |
| Semicolon | `80D0` | 3 |
| Slash | `80AE` | 6 |
| Sun | `80A7` | 12 |
| Snowman | `80AB` | 12 |
| Skull | `80BA` | 12 |

The second byte retains the actual English GameCube code. Only these five pairs
are recognised. A scan of all 29 native banks finds no existing `80` token; this
does not establish computed-string, editor, or saved-text compatibility.

## Exact source and storage

`tools/extended_glyphs.py` requires the supplied English executable, complete
font, symbol listing, and character-decoder agreement. Source SHA-256 hashes:

- Executable: `29306a927eee861b073c571408393f99cb384048684eee4bff3d219725429837`.
- Symbol listing: `e5267b989d235655c51885bd2a660b3e8c2cbd46d60b2b3c46166d337c7bca87`.
- Complete font: `54965b012354699b29d26683fa0c496c21ef7178d35299b67a8fe55c50174fc4`.

The symbol is `FONT_nes_tex_font1`, `.data + 00204700`, size `6000`; its executable
file location is `004E1A40`. GameCube I4 uses 8×8 blocks, which are untiled before
extracting the 12×16 cells. An independent inverse test crosses both block axes.
Semicolon and slash use the existing proportional resize algorithm. The three
symbols retain every source pixel and full twelve-pixel advances.

The complete resource occupies 1,600 bytes, aligned to at least eight bytes:

- `00..1F`: eight big-endian words: magic `41464758`, ABI 1, width 192, height 16,
  count 5, texture offset 64, texture length 1,536, and reserved zero.
- `20..2F`: five source codes, then eleven zero slots.
- `30..3F`: five widths, then eleven zero slots.
- `40..63F`: one 192×16 linear I4 row; five occupied cells and eleven empty cells.

Host validation rejects nonzero unused cells. The generated resource hash is
`30dddc658038fea1a4abc359121e1e4fa110edac5f5757ad6001703eff8aae7e`.
Extracted pixels and generated binaries remain ignored, not committed assets.

## Native adapters and ownership

The C binder checks the complete header, mapping, padding, alignment, and width
bounds. Failed binding retains the preceding resource. The owner retains the
resource until all queued GPU work finishes; the library does not allocate/free.
Rebinding is rejected during an active draw; nested scopes restore their caller.

Ordinary characters retain their native texture and `12 - offset` advance. A
registered pair selects its separate cell and width. Prefix measurement accepts
an explicit count up to 1,024 bytes and retains even-pixel rounding. It is not a
command-aware layout parser. Unknown bytes keep the old byte-wise fallback;
they are not approved English input. The separate generic command-size function
already recognises `80` as two bytes.

The character wrapper reads the native pointer, token byte count, and drawing
flag, then invokes the unchanged rectangle `8009167C` or polygon `800917C8`
routine. The texture adapter preserves all six O32 arguments and enters the
original loader at `800906B4`, after recreating its complete prologue. Temporary
hooks cover getter `80090178`, width `8009028C`, texture loader `8009069C`, and
character dispatcher `800918A8`.

An instruction/pointer audit finds no external interior references into the
getter, width function, replaced loader prologue, or dispatcher across 1,838
pinned executable segments. This is not an exhaustive indirect-caller proof.

The cross-compiled image has 1,356 text bytes, twenty read-only/alignment bytes,
and eight mutable bytes: 1,384 total. Internal jumps and paired signed high/low
addresses relocate; fixed native addresses remain. Missing, duplicate,
unsupported, unpaired, out-of-image, and stale relocations fail. Load/store low
halves are checked explicitly. Linked `8019A900` is only an assembly origin;
the passing test executes new code in a native heap allocation, not the resident
module's separate reserved scratch area.

The fixture owns a complete 8 KiB native allocation containing code, resource,
and drawing buffers. Original cache-maintenance calls and complete immutable
instruction checks precede allocated-code execution. No generated display list
is submitted to the GPU. Hooks are restored and flushed before freeing the
allocation; the entire checkpoint is then restored. This is not a production
memory-reservation decision.

## Verified scope

Eight focused host tests pass: sanitizers, all 256 second-byte values, bounded
and truncated inputs, nested contexts, resource rejection, source pixels,
relocation failures, and native fixture construction. Five reader-probe tests
also pass. Independent compilation produces identical code and relocation data.

The silent four-MiB batch passes 26 actual one-token sentence draws: thirteen
mixed tokens through each native drawing path. Every display-list word, polygon
vertex, token index, width, restored context, and guard matches. Narrow
`i/I/l/apostrophe`, other Latin, Japanese, and an unknown tag exercise fallback
beside all five extensions. Eight direct tag-skip-helper cases pass; the actual
message cursor is not hooked or exercised with extensions in this batch.

There are 113 calls, 67 declared returns, 286 memory assertions, and 185 writes
across 593 recorded steps. Complete native font, approved widths, live save
payload, and immutable probe code remain intact. Allocation release, restored
checkpoint, blank FlashRAM/Pak, disabled audio, and graceful shutdown pass.
Logs and hashes are recorded in the work log. These are native drawing-command
checks, not displayed gameplay, timing, input, saved-text, or hardware validation.

## Required production integration

1. Provide cartridge code/texture resources, persistent allocation ownership,
   source guards, cache maintenance, and failure handling. The resident image
   has only 1,088 linked bytes free. Do not consume its separate test reservation
   or assume an Expansion Pak; the fixture is not a cartridge loader.
2. Integrate recognition into actual message reveal. Native `800A223C` skips all
   `80` tags without ordinary character timing. The helper distinguishes pairs,
   but its call site and full reveal/control interaction remain unimplemented.
   Audit prefix widths, formatting spans, and truncated pairs at each consumer.
3. Add explicit capability and source-encoding checks to the codec, generator,
   independent builder, expansion bounds, and layout accounting. Unsupported
   builds must keep rejecting these glyphs. Preserve full reference wording,
   manual newlines, pages, and pauses.
4. Import otherwise compatible main references `04D2/04FA/08A2/08A6/0A15/0E2A`
   after those contracts pass. Re-audit unavailable mail parts; five glyphs do
   not establish support for every missing mail glyph.
5. Handle actual input before enabling apology targets `048E/0491`. The complete
   sun/skull phrases fit ten encoded bytes, but movement, deletion, conversion,
   padding, and matching must agree on token boundaries. The save-character
   validator rejects `80`; do not globally weaken it or alter saved formats for
   apology-only text. Keep the separate rude-reply detector/storage work queued.
6. Batch ordinary dialogue/keyboard/mail checks after implementation, then the
   human playthrough and hardware checks. Prototype success adds no translated
   records and does not change the current production font or candidate counts.
