# Complete ordinary-resident word fields

## Scope

The source-bound group contains 136 complete English values: drinks `0414..0433`,
colours `0434..0453`, shop types `0454..0457`, places `0464..0483`, reading material
`04A0..04BF`, and item categories `055D..0560`. Every value agrees completely
between the supplied English and legacy sources. Category labels fit ten bytes;
the other groups fit sixteen. Generated reference text stays outside git.

The five other thirty-two-entry families shared with NPC letter generation are
separate work. Its existing 352-phrase resource does not translate their ordinary
bank or grant capacity to other callers. Birthday animal/sign fields already
have their own complete resident implementation.

## Native preparation

The ordinary resident overlay is VROM `00815B70`, linked at `8091D7B0`, with its
original relocation file at `0081A1A0`. Helper `80920FFC` consumes one native RNG
draw, multiplies by its unchanged family size, truncates to an index, loads the
selected string, and sets one item field. Its four direct callers use the shared
temporary at `80921E08`; the next native BSS object starts at `80921E18`.
The available span is sixteen bytes. Only its loader and setter length words
change from ten to sixteen. No BSS size, pointer, table, random selection,
saved field, or persistent allocation changes.

The three ordinary preparers retain their original family tables and draw counts.
Unlike the GameCube version, the native game has no previous-choice skip logic
and selects only its original thirty-two fish/insect entries. This port does not
silently introduce the larger GameCube families or alter native RNG behaviour.
The fourth helper caller belongs to the original birthday body; the existing
date/birthday option replaces that body's entry separately.

The shop-type preparer originally constructs a six-byte `7F50` command followed
by a four-byte Japanese shop name at `sp+2A`. Complete English shop types are
plain text in the supplied version. Its frame grows from 48 to 56 bytes and the
loader writes sixteen bytes at `sp+24`, replacing the whole temporary. The
initial original ten-byte construction is overwritten before consumption.
The setter receives sixteen, and the original return-address slot remains at
`sp+14`. The original four valid shop levels and three random-number preparations
are unchanged. The complete English field does not retain a four-character
Japanese formatting command around the longer name.

Item-category labels use the unchanged ten-byte shared temporary and free-string
slot 11, not an item field. Their wording needs no larger destination. Category
selection and item identity remain unchanged.

## Installation and invariants

Seven original instruction words change. None has a native relocation. The
builder accepts only the original overlay or the exact existing date/birthday
patch as its predecessor, retaining every earlier date change and relocation.
The resident item setter keeps the native ten-byte compatibility fields while
retaining the full sixteen-byte values separately for message insertion.

`--english-resident-words` requires the verified resident module and the entire
136-entry group. It shares general-string relocation at `02600000`. Full source
and output hashes bind each capacity permit; no unrelated string receives a
larger budget. Partial, changed, non-text, overlong, stale, or conflicting groups
must fail. The title artwork and approved font metrics are unaffected.

## Acceptance checks

- Verify complete native and donor values, family tables, four helper callers,
  temporary ownership, all seven changed words, and unchanged relocations.
- Exercise construction with and without the existing date/birthday patch;
  reject unknown overlapping changes and missing resident support.
- Check complete installation and preservation of every earlier payload.
- Load the actual cartridge overlay and compare complete preparations, native
  random state, all shared item fields, shop types, and category labels.
- Check complete insertion, stack/BSS/heap/module guards, save retention, and
  restored isolated checkpoints in a silent bounded batch.
- Keep normal villager interactions, final presentation, and hardware acceptance
  distinct from isolated function tests. This specification is not test evidence.

## Current evidence

Seven source/build tests and the full 836-test regression batch pass. Four
additional fixture tests cover all native random-pool indices, float bits,
draw counts and ranges, selected request intervals, and buffer/frame ownership;
the final eleven focused tests pass together. Full generation adds 113 entries,
reaching 12,989. Twenty-three earlier texts remain identical with updated group
provenance; all other earlier edits and metadata are unchanged. Disabled
generation reproduces the shop-counter candidate file exactly. Basic generation
remains 12,015 because this feature requires the resident module.

Independent cartridge reconstruction verifies all 12,989 installed edits and
all 1,036 unchanged general strings, plus the complete original-ROM UPS round
trip. Only the ordinary actor, general-string data/offsets, and DMA metadata
differ from the shop-counter pilot. The actor changes exactly the seven approved
words; its existing date/birthday changes and relocation file are retained.
String data occupies 8,960 bytes. The resident stays at 24,192 linked bytes with
384 free; fonts, images, mail resources, other actors, and main text are unchanged.

`build/smoke-resident-words-01/` passes 606 native calls and 1,097 memory
assertions across 2,955 recorded steps. All 128 new random words pass actual
cartridge preparation and full insertion. Six original outer-dispatch cases
cover all three preparations and all four shop levels. Fifty-six independent
native RNG draws match preparation states and float bits. All 118 distinct
complete cartridge messages load, with 127 scoped field insertions inside their
unchanged surrounding text. Including isolated fields, 287 insertions pass.
Four category labels pass their native loader, free-string setter, and command
`37` insertion; the category-selection actor path itself is not executed.

Complete actor/BSS retention permits only the expected sixteen-byte temporary.
Stack locals, manager objects, relocation workspace, heap/module guards, and
complete save retention pass. Test shop levels change only their original two
bits in isolated RAM, then are restored. The checkpoint is restored, FlashRAM
and Pak stay blank, and shutdown succeeds with audio disabled and four MiB
configured. These isolated tests do not establish normal villager gameplay,
rendered presentation, or original-hardware acceptance.
