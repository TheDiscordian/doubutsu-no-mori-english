# Persistent text-reader extension

The existing resident module is full. A small independently linked extension
owns twenty sixteen-byte general message fields and complete main-message
readers without changing the packed native window or saved structures. Its
system-arena allocation survives gameplay-arena teardown, like the existing
font owner. The main module, font, and existing item resource remain unchanged.

## Startup ownership

The ROM includes the extension image followed by its relocation at VROM
`03A00000`. It links at `80D00000`; startup allocates the complete blob plus
fifteen alignment bytes, requires a legal existing four-MiB system-arena range,
loads the complete blob, checks CRC, relocates, writes back data cache,
invalidates instruction cache, and calls its initializer. Failure releases the
allocation and takes the existing bootstrap failure path. Success retains it
until reset. Permission to require an Expansion Pak does not change this
implementation's actual RAM contract.

The original general-field setter span `8009D6D0..8009D820` contains this
one-shot loader in the ROM. No gameplay text setter executes before startup
finishes. The bootstrap keeps its original heap and font initialization and
their failure checks. Its success epilogue redirects to a short tail in verified
unused bootstrap padding, which invokes the loader, checks success, then restores
the original saved registers, stack, and return address.

The extension initializer checks all live reader/bridge source entries before
any write. It installs the real general-field setter over the loader's entry,
after that entry has executed; the remaining loader instructions and stack are
untouched while it returns. All changed instruction ranges receive both cache
operations. There is no lazy load during dialogue and no escaping freed pointer.

## Field and reader contracts

Native general fields remain twenty ten-byte rows at window offset `38`.
For the main window `80142410`, the extension keeps complete sixteen-byte rows
plus a validity mask. Each valid write stages its input, fills unused bytes with
spaces, and mirrors the first ten bytes into the original structure. Null/invalid
inputs do not replace rows. Slots one, two, and five retain the native colour-flag
reset, including null-source calls, and the unchanged coloured setter can set
those flags afterward. Other windows retain their ten-byte storage limit.

Main-message plain insertion at `800A1370` uses the complete valid row or its
native fallback. Main coloured insertion at `800A1394` inserts the colour command
and full field together, using the five original colour triples. It checks the
complete expansion before writing, retains the updated insertion index, and
counts the whole English name for colour duration. Both readers preserve the
1024-byte message limit, command size, suffix, and trimming of trailing spaces.
The existing build bound reserves thirty-two bytes per ordinary dynamic field,
covering sixteen text bytes plus the six-byte colour prefix.

The native item-to-free-field wrapper entry `800BB6F0` keeps its zero-item no-op.
Two entries in its bypassed tail supply explicit empty-item clearing and
coloured item insertion for direct actor callers. These fixed bridges point to
the relocated extension only after successful startup. Caller adapters preserve
their original unsigned item expression, slot, colour, and nonzero/quest branches.
No widened name is written into a native stack temporary.

The baseline profile supplies only main-message readers. The
[choice-capable profile](CHOICE_SUBSTITUTIONS.md) also installs complete bounded
substitutions in the twenty-byte shared choice destination. Its field state and
readers share the same allocation; the compatibility mirrors remain unchanged.
Other character/name callers and default catchphrase editing remain main work.

The native message initializer `8009E6F8` does not clear the twenty native general
fields; the complete rows likewise persist between message initializations.
It resets the three colour flags independently. Initial validity is zero and
only a complete successful setter call marks a row valid.

## Installed profile

The baseline approved image is 1,952 bytes including zero-filled private state, followed
by a 192-byte native relocation. The loader is 216 bytes inside the 336-byte
native setter span. Total system allocation is 2,159 bytes including alignment.
The initializer installs six jumps/calls: setter, plain reader, coloured reader,
and the three item bridge entries. Main-message command-size and movement helpers
retain their verified native implementations and resident command attributes.

The original wrapper `800BB6F0` retains zero-item no-op behaviour. New bridge
`800BB6F8` explicitly clears an empty item; `800BB700` also accepts the original
colour argument. The letter actor adapter `80919C68` retains slot two and colour
two. Reserve `80A09438` and shrine `80A0AA6C` retain slot zero and their original
unsigned item loads. The shrine's saved window pointer is the main singleton.
All three actor extents, relocations, BSS, and other instructions remain unchanged.

`tools/text_extension.py` binds the compiled profile, current sources, imports,
ELF and native relocations, existing startup/font ownership, actor sequences,
and unused allocation ranges. It applies changes only after every check passes.
The final verifier reconstructs all changed cartridge code/actors and rejects
incomplete application evidence. The progress tool invokes that verifier but
keeps resource-only item IDs pending while other required readers remain.

## Verification scope

Bind complete source code/actor spans, bootstrap bytes and unused tail, extension
code/data/relocation, imports, startup loader, and every installed adapter.
Reject references into reclaimed interiors and conflicting patches. Require
complete relocation and memory bounds before enabling the feature or crediting
its application evidence. Host checks cover fields, flags, colour lengths,
shorter/empty values, invalid inputs, overlapping input, and exact message limits.
Focused native startup/field execution and the combined v0 smoke must retain
their actual evidence and limitations; neither compilation nor an artifact
comparison constitutes gameplay or original-hardware validation.
