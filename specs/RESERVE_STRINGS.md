# Reserved general-string labels

## Exact translation scope

The 77 native general-string slots `02C5..02C9`, `02ED..02F3`, `0561..0565`,
and `05DE..0619` contain only `よび` (reserve/spare), encoded `60F7`.
Their explicit English translation is `spare`. Do not copy unrelated GameCube
book counters into native reserve slots, delete the slots, or turn empty donor
entries into missing translations. The three credit-roll reserves `0555..0557`
retain their separate existing credit translation.

This optional data-only group changes no selector, command, item identity,
saved field, timing, or font. It keeps all 1,562 native general-string indices
and uses the existing relocated bank. No other string receives extra capacity.
Reserved labels remain in the translation denominator; translating them does
not claim that they appear during normal gameplay.

## Five-byte capacity boundary

The unchanged generic loader accepts at most 64 stored bytes, stages at most
72 aligned bytes in its 80-byte buffer, then copies only the explicit destination
length and space-pads it. The five-byte label therefore fits the native loader.

The existing 34-call inventory supplies the consumer boundary. Fixed five-,
six-, ten-, fifteen-, and sixty-four-byte destinations can hold the whole label.
The narrower default-catchphrase calls select the verified 216-entry native
default table, which contains none of these IDs. The ordinary four-byte call at
`8092125C` selects season `0454..0457`, not reserves. Date suffix calls select
only `0001..0008`. The generic number-plus-unit routine at `800C43B8` accepts
an unsigned sixteen-bit number, leaving at least five of its ten bytes for the
unit. No dynamic ID or caller is redirected into a reserve range.

Build verification binds the original ROM, full bank, exact range/content,
complete native caller inventory, absence from default-catchphrase IDs, and
generic loader instructions. Installation permits only the established string
data-base relocation within the loader and verifies every installed label.
A flag or a matching source hash does not authorise arbitrary replacement text.

## Bounded checks

Verify all 77 complete labels, exact source and five-byte replacement, duplicate
or conflicting candidate rejection, disabled-option rejection, no capacity
transfer to another bank/policy/payload, unchanged unrelated entries, generic
loader guards, and the combined cartridge/UPS. Reuse passing native generic
loader evidence: no new runtime code or native harness is needed for this group.
