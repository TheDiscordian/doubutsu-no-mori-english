# Complete default catchphrases

## Goal and saved-data contract

Display the GameCube English default catchphrases without truncation. The native
saved `Animal+4E5` field remains four bytes. Its setter, default loader, reset,
animal copies, and save format remain unchanged. A separate display resource
maps those original saved bytes to full English text at the main-message `7F1C`
insertion. This is one part of catchphrase support, not completion of ten-character
custom editing, mail substitutions, shared choices, or travel compatibility.

The GameCube defaults are obtained through the confirmed villager identities and
the actual `npc_def_list` REL table. The native table at VROM `00E03000` has 216
six-byte records, followed by padding. Both tables contain the same catchphrase
string IDs for these identities. Complete table and string hashes guard every
row. English reference words are not shortened or reflowed.

## Lookup resource

An optional resource at VROM `02E00000`, enabled by module configuration word
`40` hexadecimal, has a 32-byte header followed by 216 sixteen-byte rows.
Header words are `41464350`, ABI one, English width ten, row count 216, row width
sixteen, native width four, and two zero reserves. A row contains the original
four saved bytes, the two-byte native villager ID, and ten space-padded English
bytes. Rows sort by the unsigned saved-byte key, then villager ID.

The loader validates the header and uses aligned sixteen-byte DMA reads with a
bounded binary search. It never modifies the saved source or writes a destination
smaller than ten bytes. A matching default for the current villager takes
precedence. A phrase borrowed from a different villager resolves only when every
matching row has the same English text. Ambiguous borrowed phrases remain native
pending a separately reviewed policy; do not infer a unique English source from
identical Japanese bytes. Custom phrases with no key match retain their saved
text. Original keys must contain a non-Latin byte, so English custom input is
not mistaken for a Japanese default. Already imported complete defaults of four
or fewer English bytes remain plain native text.

## Main-message consumer

Only the caller at `800A114C` is redirected from `mMsg_CopyTail` (`8009EDBC`).
The shared native insertion and `mNpc_GetWordEnding` (`800A9E7C`) remain intact.
The replacement stages ten bytes, trims trailing padding, validates command
and cursor bounds, and rejects a result exceeding 1,024 bytes before calling
the native move/copy functions. The existing command dispatch still consumes
capitalization and updates the message header. For an empty phrase, capitalization
applies to the following output byte, matching the GameCube insertion routine.
Disabled resources and unsupported
actors use the native four-byte result; null actors insert zero characters.

Candidate layout warnings use the greater of four native cells and ten maximum
Latin advances for this field when the resident runtime is selected. This is a
conservative review warning, not automatic reflow or a change to any English
line, page, pause, or capitalization command.

Executable/literal reference auditing finds two shared insertion calls:
`800656EC` for dynamic choices and `800A114C` for main dialogue. The getter has
one direct call at `8009EDF0`; the resetter has one overlay call at `80979ED8`.
No direct setter calls or aligned literal pointers to these four routines are
found. This does not prove that inline saved-field users are absent.

## Native editor and ambiguous borrowing

The native name-entry actor does not prefill the catchphrase editor from the
saved default. Its initializer at `80884B30` selects a private four-byte buffer,
clears it to spaces at `80884C38`, and opens the editor at `80884C68`. Confirmation
copies four bytes to the caller at `8088445C`. The four-character custom-input
limit is a saved-storage constraint, not a remaining Japanese-default reader.

The pinned default resource has one ambiguous saved key: `D0 90 20 20` (`グー`).
Dozer (`E014`) uses the GC English `zzzzzz`; Bea (`E0C5`) uses `bingo`. Own-ID
display succeeds. An unrelated villager holding that key falls back to native
text because four saved bytes contain no donor identity. Native greeting
copies propagate those same four bytes. All other key groups have a single
English value. Complete borrowed-phrase application requires an explicit policy
and installed implementation for this ambiguity, not a guessed donor identity.

## Validation requirements

Confirm every default-table/string/name identity, duplicate-key behaviour,
unaligned destinations, absent/disabled/malformed resources, full command and
message boundaries, and unchanged source/save fields. Audit executable and literal
references to the getter, setter, resetter, and shared insertion. Exercise actual
`7F1C` dispatch on native MIPS, all default rows, custom and borrowed phrases,
capitalization, exact buffer limits, and checkpoint restoration. Broader gameplay,
custom editing, mail, travel, actual saves, and hardware remain separate checks.
