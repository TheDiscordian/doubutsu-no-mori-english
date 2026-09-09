# Separate English glyph resource

## Implemented scope

This specification describes the five-glyph dialogue capability. The optional
fourteen-cell [mail resource](MAIL_GLYPHS.md) preserves those cells and adds
complete template glyphs under catalogue-four semantics. It does not widen
dialogue imports or authorise two-byte saved field/editor input.

Five otherwise unrepresentable English reference characters have an exact-source
resource, bounded C measurement/selection functions, and relocatable native draw
adapters. An opt-in cartridge installation owns the complete code and resource
from startup, before rendering threads start. Both original drawing paths and
the actual message cursor pass isolated execution. Six complete main-dialogue
references use the new encodings. Editors, saved text, and mail remain outside
this capability; ordinary glyph-bearing conversations and hardware need testing.

The approved N64 atlas, Japanese cells, and existing Latin spacing stay unchanged.
This work does not resume the paused atlas-edge investigation.

The optional [world-label variant](WORLD_ITEM_NAMES.md) retains the complete
fourteen-glyph resource and adds owned full item-name storage and consumers to
the same startup allocation. It does not change glyph encodings or pixels.
Both original font profiles retain their source identities and validation.

| Character | Two-byte encoding | Pixel advance |
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

## Cartridge installation and lifetime

`runtime/extended_font_loader.c` runs immediately after native `SystemHeap_Init`
and before graph/audio thread startup. It uses `SystemHeap_Malloc` at `8002BC60`,
not the gameplay arena, which is destroyed by play cleanup. The allocation
survives scene changes and remains owned until reset. No saved structure changes.
The resident image occupies 24,192 linked bytes, leaving 384 within its existing
24 KiB linked limit. Its 32 KiB reservation and separate test space do not grow.

The optional eight-word header at module offset `68` contains VROM `03400000`,
blob length, image length, relocation length, executable-text length, entry offset
zero, whole-blob CRC32, and ABI `41464701`. All zeros disable the feature. Partial
or invalid configuration fails. Configured startup failure enters the bootstrap's
existing failure loop before rendering; it does not continue with missing glyphs.

The position-adjustable image links at `80C00000` solely as a relocation origin.
Its 3,680 image bytes include zero BSS. A separate 288-byte native overlay
relocation table follows the image. The system allocation requests 3,983 bytes
including alignment allowance; code, state, and pixels occupy persistent memory.
The loader checks four-MiB bounds, DMA success, and complete CRC before invoking
native relocation. It writes back the image, invalidates executable instructions,
and runs the guarded installation entry. Failure releases the original allocation;
success publishes its aligned pointer and repeated initialization retains it.

Installation checks all replaced instructions before binding or writing any hook.
Five entries redirect texture selection, character width, prefix width, texture
loading, and character drawing. The native prefix API retains its explicit signed
byte count and even-pixel rounding; it has no added 1,024-byte limit. Its known
pairs count once, and ordinary/unknown bytes retain the approved width behaviour.
Unlike the bounded prototype helper, this is the actual native prefix consumer.

Ten instructions at `800A23C4..800A23EC` replace unconditional tag skipping with
registered-pair recognition. Known pairs proceed through ordinary reveal timing;
unknown tags retain the original two-byte skip. The cursor then processes the
following character. Native voice classification remains unchanged: symbol pairs
are silent, while ordinary fallback characters can set voice-queue flag `0020`.
Installed instructions receive both data- and instruction-cache maintenance.

## Import contract

`--extended-font <directory>` is required by both candidate generation and the
ROM builder. Each verifies the real current module, startup call, native consumer
instructions, complete font source/image/relocations, widths, and available DMA
space before accepting dependent text. Preflight uses copies; final installation
is repeated on the actual cartridge before ROM or patch publication. A flag,
Unicode text, or candidate metadata alone cannot bypass these checks.

The codec explicitly opts into only five Unicode mappings. Expansion accounting
includes both encoded bytes; layout uses the exact resource advances. Main
dialogue alone receives this capability. Unknown/truncated pairs, choices,
other banks, and unsupported builds remain rejected. Coverage recognises known
candidate glyphs without changing native-source classification or implying review.

Six identity approvals bind complete native, supplied-English, and final hashes.
`gamecube_glyph_offsets` lists every registered token in the encoded reference.
Only those prefix bytes are removed when reconstructing the actual disc stream;
command arguments and all other bytes remain. Missing/extra/interior offsets,
unknown pairs, other content adaptations, and changed full text fail validation.

| Native record | English content | Stored bytes | Expansion bound |
| --- | --- | ---: | ---: |
| `04D2` | Late-night peppy introduction | 431 | 537 |
| `04FA` | Busy snooty introduction | 378 | 514 |
| `08A2` | Stationary snowman joke | 376 | 392 |
| `08A6` | Snowman melting lament | 217 | 233 |
| `0A15` | Letter-show invitation | 103 | 179 |
| `0E2A` | Soccer conversation | 371 | 537 |

Every GameCube word, manual line, page, pause, native actor command, field, branch,
and ending remains. No paraphrase, truncation, or automatic reflow is introduced.

## Cartridge validation and remaining work

Portable loader tests cover allocation alignments, nested/repeated initialization,
disabled/malformed configuration, DMA/CRC/entry failures, release, and retry with
address/undefined-behaviour sanitizers. Host checks independently validate native
relocation sections and signed-low-address boundaries, all six actual disc
streams, complete output hashes, capability rejection, byte budgets, and widths.
Independent module, font, ROM, and UPS builds match; every installed edit and
the original-ROM UPS reconstruction pass.

The combined silent four-MiB cartridge batch passes 26 actual native draws,
eight actual cursor cases, and all six complete message loads: 54 native calls
and 324 memory assertions across 596 recorded steps. The persistent image is
loaded by startup at `8019C8F0`; the debugger uploads no font code or pixels.
Tests check complete instructions/resources, display lists/vertices, prefix widths,
two-frame protected waits, token advancement, voice flags, and allocation guards.
The complete native font, approved widths, and live save payload remain intact.
Fixture release, restored checkpoint, blank isolated FlashRAM/Pak, disabled audio,
and graceful shutdown pass. Generated drawing commands are not submitted to the
GPU; these tests do not establish ordinary visible conversations or hardware.

Required follow-ups:

- Audit formatting-span counts and other consumers before expanding imports.
  Keep main `0912` continuation/commands, scoped number-game choices, and the
  remaining native diagnostic records in the bulk-text queue.
- Re-audit unavailable mail parts and reader consumers; five supported glyphs
  do not enable every missing mail character or authorize changed catalog IDs.
- Handle actual input before enabling apology targets `048E/0491`. Movement,
  deletion, conversion, padding, and comparison must agree on token boundaries.
  The save validator still rejects `80`; do not weaken it globally. Complete
  rude-reply storage and its matching-length table together.
- Batch ordinary dialogue, editor, mail, scene-change, and save checks alongside
  further content work. Human playthrough and hardware acceptance remain required.
  Title artwork stays the first image-replacement task after the main port.
