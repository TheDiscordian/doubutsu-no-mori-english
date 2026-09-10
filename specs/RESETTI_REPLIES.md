# Complete English Resetti reply matching

## Native and English contract

Majin3 loads the requested apology from `0484..0493`, compares all ten padded
reply bytes, then checks the 32 rude replies `04C0..04DF` only if the exact
apology comparison failed. Native results are zero for accepted, one for a rude
reply, and two for another incorrect answer. The comparison is case-sensitive.
The rude-reply test checks every substring position that fits in ten bytes;
it is not a whole-word or case-folded filter.

All 32 supplied English rude replies agree with their complete legacy values.
They fit the same ten-byte temporary and input fields. Their lengths in index
order are two through ten, with transitions at `1,2,4,8,10,17,24,28`.
The GameCube actor source declares precisely those transitions and the same
matching order. Native Japanese uses `6,16,25,30,31` instead, reaching seven.
Importing text alone would therefore compare the wrong prefixes.

## Scoped implementation

The existing 24-byte native transition array at `809B572C` holds the eight
English transition indices followed by byte `FF`, with zero padding. The native
`lw t7,0(s7)` at `809B4C68` becomes `lbu t7,0(s7)`; the pointer increment at
`809B4C80` becomes one instead of four. The sentinel never equals loop indices
zero through 31. No new table allocation, loop replacement, frame change,
relocation change, actor state change, or resident code is needed.

`--english-resetti-replies` requires the complete source-bound 32-record group
in generation and construction. Each permitted entry binds original and final
hashes; a length-prefixed group hash binds order and complete English content.
Other general strings do not gain capacity. The general-string data relocation
to `02600000` is shared with the optional fortune integration, preserving the
native table, entry count, loader staging, and all caller copy lengths.

This integration supplies the rude-reply dictionary and its matcher. The
[apology input extension](APOLOGY_INPUT.md) supplies the remaining two requested
targets, `048E/0491`, with actual sun/skull input and display. All sixteen targets
then retain exact GC wording. No replacement wording or unavailable keyboard
character is silently substituted. Saved formats remain unchanged.

## Verified scope

All seven focused tests and the complete 817-test regression pass. The installed
audit reconstructs all 12,742 candidates and unchanged general strings, verifies
the original-ROM UPS round trip, and confines changes relative to the fortune
pilot to the Majin3 actor, string data/table, and DMA metadata. Main code, resident
image, font/graphics, other actors, and all other resource files remain unchanged.
The string data is 8,144 bytes; the ROM stays 32 MiB. Basic generation supplies
11,881 candidates with the reply option, and disabling it reproduces the full
12,711-edit fortune candidate file exactly.

`build/smoke-resetti-replies-01/` passes 1,154 recorded steps, 306 native calls,
and 302 memory assertions. The original cartridge loader loads and relocates
the patched actor; no actor code is uploaded. All 32 dictionary loads and
227 detector cases pass: 126 fitting positions, 32 case variants, 32 incomplete
prefixes, 32 right-edge overread traps, and five neutral/partial replies.
Fourteen complete installed English apology targets pass exact matching;
thirty combined classifications distinguish accepted, rude, and other incorrect
answers. Full actor/input and saved-memory retention, stack/heap/module guards,
checkpoint restoration, blank isolated FlashRAM/Pak, and graceful shutdown pass.
Audio is disabled and four-MiB configuration is selected. Independent scenario
regeneration checks every detector return and complete loaded dictionary hash.
These calls do not exercise ordinary keyboard entry, retries, or hardware.

## Required verification

- Verify every complete reference/legacy/source value, the exact English length
  grouping, group rejection, source/patch overlap, and unrelated capacity limits.
- Verify only the two instructions and existing table change, retaining all
  native relocated pointers and the exact good-answer-before-rude-answer order.
- Load the actual patched actor through the cartridge loader. Test all dictionary
  entries at every fitting position, nonmatching/case/prefix/boundary cases,
  all fourteen complete English apology targets, and their classification.
- Check complete actor/input/save retention, native stack/heap/module guards,
  silent bounded execution, checkpoint restoration, and blank isolated saves.
- Leave ordinary input, retries/acceptance, symbol targets, and original hardware
  explicitly unverified until their corresponding integration tests exist.
