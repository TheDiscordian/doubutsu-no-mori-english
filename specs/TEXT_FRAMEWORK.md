# Translation framework

## Input and output

Accept only the Japanese retail ROM after byte-order normalisation:

- SHA-1: `e106dff7146f72415337c96deb14f630e1580efb`
- SHA-256: `d9417be056534fcc0bdff2e6cd5f1135511be7c0a4dace04a96a2649596ce908`
- Size: 16,777,216 bytes.
- Cartridge identity and IPL3 remain intact. Retail IPL3 uses CIC 6102/7101.

Build a separate ROM and a UPS patch. Validate every replacement and round-trip
the patch. Original source bytes are never modified on disk.

## Filesystem

The DMA table starts at physical ROM offset `0x19D50`. Each 16-byte record has
four big-endian u32 fields: virtual start, virtual end, physical start, physical
end. A nonzero physical end indicates Yaz0 compression. Physical start
`0xFFFFFFFF` denotes a RAM-only entry. Every source record is validated.

Replacing a file without changing its virtual size appends an uncompressed copy
to the ROM and changes its physical DMA address. Existing RAM addresses, file
identities, overlay relocation data, and save layouts are preserved.

## Text

The game uses a custom single-byte character set, not Shift-JIS. Most Latin
letters and digits have ASCII byte values, but several ASCII punctuation bytes
are Japanese glyphs or symbols. For example, `0x23` is む, `0x24` is め, and
`0x5B` is も. Unsupported punctuation must be rejected, not silently substituted.

`0xCD` is a newline. `0x7F` introduces commands; their lengths and attributes
are extracted from the retail code table at RAM `0x80106BF4`. `0x80` introduces
a two-byte glyph/control token, whose meaning remains under investigation.

Editable text uses exact tokens such as `{cmd:7F00}` and `{glyph:8042}`. The
inventory can preserve malformed legacy bytes as `{raw:...}`, but translation
builds reject raw tokens and unsupported commands.

Tables contain cumulative end offsets: entry zero starts at zero, entry one at
the first table value. A zero ends the table. Duplicate nonzero end offsets
represent empty entries. Preserve IDs and original unused bytes on round trips.

Each translation edit records the source entry hash, its bank and hexadecimal
ID, replacement text, provenance, and review status. A stale source hash fails
the build. Initial builds require unchanged control tokens and original byte
budgets for banks without an audited relocation. Main dialogue and choices
support bank expansion, within the unchanged runtime buffer limits.

Dialogue relocates to virtual ROM `0x02000000`. The loader address at RAM
`0x8009E474` changes from `3C1800BD27184000` to `3C18020027180000`.
Choices relocate to virtual ROM `0x02400000`; RAM `0x80065614` changes from
`3C1800D027185000` to `3C18024027180000`. Both patches require the exact retail
instructions before modification. End-offset tables retain their original IDs.
The DMA lookup is a linear scan, so relocated rows need not be sorted.

The optional `presentation` control policy permits pause (`7F03`) and text-colour
(`7F05`) differences. All other commands and arguments remain exact and ordered,
including button waits, page clears, animation, sound, insertions, choices, and
branches. A command mismatch blocks import; it is not repaired by guessing.

The dialogue-only `reference_text` policy additionally permits the English
delivery to omit, repeat, or reorder already available read-only text fields
(`7F1A..7F2F`, `7F31..7F3F`). A requested field absent from the N64 source is
rejected. RNG `7F30` and embedded mail `7F40` remain strict. This is not permission
to reorder branches, waits, animation, or sound. The expansion bound is applied
to the final candidate, including every repeated insertion.

Reference adaptation removes GameCube article-suppression `7F74` only directly
before a supported N64 text field: N64 does not generate articles there. Matched
actor-demo operations `7F08..7F0C` retain N64 arguments instead of importing
GameCube actor-specific values. Every adaptation is recorded for review.

## Halfwidth prototype

- Main code virtual file: `0x675720`, RAM load address `0x80051A80`.
- Width table: RAM `0x80106AF4`, 256 bytes, all zero in retail.
- Width function: RAM `0x8009028C`; returns `12 - offset` when cutting is enabled.
- Guard at `0x80090294`: `beqz a1, 0x800902B4` (`10A00007`).
- Font virtual file: `0xBCD000`; atlas at file offset `0x128`.
- Atlas: 192×256 intensity-4 texture, 16×16 glyph cells, each 12×16 pixels.

The prototype replaces the width guard with a NOP and reduces Latin ink to at
most five columns plus one spacing pixel. Narrow glyphs use their actual ink
width plus one; `i`, `I`, `l`, and the apostrophe advance four pixels. The width
table stores `12 - advance`, so these narrow glyphs have an offset of eight.
Space advances six pixels. Other table
entries stay zero. Font storage size and Japanese textures stay unchanged.
This establishes a shared proportional measurement path. Every draw path, menu
cursor, text entry UI, and bubble still requires in-game verification.

## Buffer constraints

The retail message loader rejects entries larger than 1,024 bytes. That limit
includes control bytes; inserted player/item strings can require more room.
The builder budgets 32 bytes per insertion, 96 for embedded mail, and a 16-byte
work/alignment reserve. Retail disassembly confirms six-byte player/NPC names,
four-byte catchphrases, ten-byte free/item strings, and colour wrappers of six
bytes. The country-name insertion adds a six-byte name and a suffix loaded into
a ten-byte buffer. The embedded-mail message setter uses a 68-byte buffer.
These deliberately generous bounds apply only while those runtime structures
remain unchanged. Two-byte message tags are excluded from expanded edits until
their semantics are established.

`mMsg_MoveDataCut` at RAM `0x8009EA2C` only moves an expanded suffix when its new
length is at most 1,024; callers still perform their insertion copy. Avoiding
overflow before building is therefore essential, even though the move routine
contains a size check.
The retail choice loader accepts at most ten bytes. The opt-in English runtime
supports sixteen plain bytes after patching every identified loader caller,
storage destination, and reader; see [English runtime](ENGLISH_RUNTIME.md).
The general string loader
accepts at most 64 bytes and copies into caller-specific buffers.

Retail mail bodies are 96 bytes (`include/m_mail.h`). Header, footer, NPC
catchphrases, item aliases, and saved text each have independent limits. Increasing
ROM storage does not increase these buffers. Save format compatibility is a
separate requirement from rendering width.

## Coverage and validation

### Layout and timing fidelity

The English GameCube version is the presentation reference. Preserve its
intentional line breaks, page breaks, emphasis, and pause timing wherever the
N64 engine can reproduce them. A sparse bubble is not itself a defect. Layout
checks report constraints; they must not silently rewrite the script or remove
pauses. Necessary departures require an explicit entry-level note and visual
review. Original translation drafts are not an approved pacing reference.

The `presentation` comparison policy allows an English candidate to retain its
GameCube pause/colour tokens while verifying the other N64 commands. It does
not strip pause tokens from the candidate or authorise arbitrary timing changes.

### Acceptance

Inventory records untranslated, legacy candidate, reviewed, and tested states
separately. Changed command signatures indicate required review, not automatically
a proven crash. English glyph detection does not establish translation accuracy.

Acceptance requires new-town creation, all dialogue control types, menus, long
names, item bubbles, keyboard entry, mail, message board, calendar, RTC, FlashRAM,
Controller Pak travel, credits, and seasonal events. Emulator tests precede the
original hardware matrix. A boot screenshot is not a full stability test.
