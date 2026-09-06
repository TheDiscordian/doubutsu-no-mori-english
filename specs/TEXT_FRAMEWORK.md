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
budgets; expansion needs a documented loader and buffer audit.

## Halfwidth prototype

- Main code virtual file: `0x675720`, RAM load address `0x80051A80`.
- Width table: RAM `0x80106AF4`, 256 bytes, all zero in retail.
- Width function: RAM `0x8009028C`; returns `12 - offset` when cutting is enabled.
- Guard at `0x80090294`: `beqz a1, 0x800902B4` (`10A00007`).
- Font virtual file: `0xBCD000`; atlas at file offset `0x128`.
- Atlas: 192×256 intensity-4 texture, 16×16 glyph cells, each 12×16 pixels.

The prototype replaces the width guard with a NOP, sets supported Latin offsets
to six, and reduces Latin ink to at most five columns plus spacing. Other table
entries stay zero. Font storage size and Japanese textures stay unchanged.
This establishes a shared six-pixel measurement path. Every draw path, menu
cursor, text entry UI, and bubble still requires in-game verification.

## Buffer constraints

The retail message loader rejects entries larger than 1,024 bytes. That limit
includes control bytes; inserted player/item strings can require more room.
The retail choice loader accepts at most ten bytes. The general string loader
accepts at most 64 bytes and copies into caller-specific buffers.

Retail mail bodies are 96 bytes (`include/m_mail.h`). Header, footer, NPC
catchphrases, item aliases, and saved text each have independent limits. Increasing
ROM storage does not increase these buffers. Save format compatibility is a
separate requirement from rendering width.

## Coverage and validation

Inventory records untranslated, legacy candidate, reviewed, and tested states
separately. Changed command signatures indicate required review, not automatically
a proven crash. English glyph detection does not establish translation accuracy.

Acceptance requires new-town creation, all dialogue control types, menus, long
names, item bubbles, keyboard entry, mail, message board, calendar, RTC, FlashRAM,
Controller Pak travel, credits, and seasonal events. Emulator tests precede the
original hardware matrix. A boot screenshot is not a full stability test.
