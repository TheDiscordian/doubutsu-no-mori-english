# Native letter-menu selection

## Scope

`tools/mail_menu.py` pins the original N64 tag overlay and independently models
its relocation, static option definitions, and letter-menu selector. The isolated
native harness calls the original selector and label-length helper after loading
the original overlay with the game's own loader. It does not patch production
menu behaviour or execute the full inventory/storage UI.

This establishes which actions the selected native status values expose. It
does not approve generated snapshot status values, enable snapshot generation,
or complete player-created/edited letter handling.

## Source and layout

The tag overlay is VROM `777AE0`, linked RAM `8086F310`, with 41,600 file bytes
and 288 BSS bytes. Its relocation file starts at VROM `781D60`, with 3,200 bytes.
Section sizes and relocation count are `(38416, 3024, 160, 288, 792)`.
Both complete files are hash-guarded before inspecting or relocating them.

The native loader at `800262D0` loads the unmodified cartridge data into a
private heap allocation. An independent relocation model compares the complete
loaded file and zeroed BSS. The model checks relocation locations, target bounds,
jump instructions, high/low instruction pairs, and the four-MiB destination.
No original overlay bytes or reference labels are committed as fixtures.

## Static menu labels

The table at `80878F08` contains 44 eight-byte `(pointer, count)` definitions.
Each nonempty definition points to an immutable native data array. Array entries
point to twelve-byte records containing an eight-byte label and a callback.
All array, label, and nonnull callback addresses are checked against the pinned
file's section bounds. The maximum-label helper at `8086FA88` passes these
fixed eight-byte labels to `mMl_strlen` at `8086FAC4`.

The three layout callers obtain their definition through the indexed table at
`8087092C`, `80870944`, and `8087095C`. The helper does not receive a stored
letter body or snapshot envelope. Native calls cover all 44 definitions,
including the empty definitions, and verify the maximum trimmed label length.
This is not a translation or rendering test of those native labels.

## Letter actions

The selector at `80875888` resolves a complete letter through `8086FBE4` and
uses the original unused/sendable predicates. It reads status at `Mail+26`
and the gift at `Mail+24`, not the split marker at `Mail+27` or text at `Mail+2A`.
All offsets and addresses in this specification are hexadecimal unless stated
otherwise. Menu/status/action numbers below are decimal.

| Context | Native selection |
| --- | --- |
| Any tested context, unused status 255 | No letter action menu |
| Inventory, status 1, no gift | Type 22, or 23 when field type is nonzero; first action is Rewrite |
| Inventory, status 1, gift present | Type 24; first action is Rewrite |
| Inventory, other used statuses, no gift | Type 19, or 20 when unread status 0/3 or field type is nonzero; first action is Read |
| Inventory, other used statuses, gift present | Type 21; first action is Read |
| Mailbox or Pak storage | Type 20 for status 0/3, otherwise 19; first action is Read |
| Inventory send-mail mode 7 | Type 30 only for status 1; otherwise no letter action menu |

The four-word inventory decision table at `8087939C` is `(22, 24, 19, 21)`.
Types 19/20/21 begin with the native Read callback at `80873498`.
Types 22/23/24 begin with Rewrite at `80872684`.

Instruction inspection shows Read invokes the common board opener at `808717BC`
with mode one, then changes status 0 to 2 or 3 to 4 and records collected paper.
Rewrite invokes the same opener with mode two. The common opener passes the
complete letter pointer to board program 12; it does not extract text itself.
These callback/transition instructions are covered by the complete source hash,
but the selector harness does not execute the callbacks or their side effects.

## Relationship to the editor

The board copy hook handles existing snapshot records before the ordinary
header/body/footer scans and mode branch. It clears only the temporary text and
forces mode one. The native branch at `8088A49C` then sets next state two and
skips opening recipient-selector program 13. Non-read existing letters instead
open that selector with the board's temporary body pointer at board state `+3C`.
New-letter mode zero also passes that temporary pointer; the board initializer
completes native mail setup before the recipient-selector program runs.

Program 13 is the recipient selector, not the keyboard. Its native calls at
`8088B540` and `8088C3E8` open editor program 10 with the supplied pointer,
mode zero, and sixteen columns. The editor initializer at `8088587C` stores
its input pointer at editor state `+24`; a positive column count reaches the
shared length call at `8088590C`. Thus the editor remains a real ordinary-text
consumer, even though the tested snapshot read path bypasses its opener.

The distinct edit-accept state at `80889288` contains the persistent letter copy
and footer scan at `80889334`. Complete editor-input ownership, actual generated
status assignments, parent-menu interaction, and normal custom editing remain
required checks. Received-letter Read selection alone does not justify removing
the lossless editing requirement or assuming every future snapshot is read-only.

## Shared close transitions

The original shared submenu overlay is VROM `7749C0`, linked `8085BAC0`, with
12,016 file bytes and 67,376 BSS bytes. Its complete file SHA-256 is
`ff0c90d15d6e17baa1eee5acdf86cf1fe8af9ce5479acc8f6e55d731fc837a20`.
Instruction inspection establishes these callback assignments and effects:

| Overlay field | Callback | Effect relevant to closing a letter |
| --- | --- | --- |
| `106B0` | `8085D4D4`, change motion | Sets current state zero, stores direction, and sets next state one for odd directions or four for even directions |
| `106A8` | `8085D92C`, move | Updates position/speed and copies next state to current state when motion finishes |
| `106AC` | `8085DA08`, end | Calls the shared return routine at `8085D718` |
| `106A4` | `8085D718`, return | Repairs menu links, restores the previous menu or destroys loaded programs, and clears the closing menu's state fields |

The initializer writes those pointers at `8085DB9C`, `8085DBB4`, `8085DBCC`,
and `8085DBE4`. The change-motion function's complete 44-byte SHA-256 is
`1472986a8d6afe4aae3391bbde52a00932e65ea40800a5ce4a36772d8ca994d5`.
The complete return/motion/end range `8085D718..8085DA28` has SHA-256
`1c0f0cefe4b82e80e1a48ca82bbb02288755f6c163891fcc1b016cd43f78e59d`.

For the board's read mode, initialization selects next state two. Opening
motion reaches read-wait state two at `8088913C`; A/B/START requests direction
four. Change-motion then selects current state zero and next state four.
Closing motion reaches end state four, whose board handler at `808894E4`
calls the shared end callback. These transitions never select edit-accept
state three and never call its letter-copy or footer-scan instructions.

The shared return routine itself does not access a letter. Returning to a parent
calls that program's procedure setter, not its constructor; standalone close
calls the loaded programs' destructors. The board destructor only clears its
registered pointer. The board dispatcher also invokes a saved parent move
callback before its own state handler. Full parent-menu interaction remains
separate from these inspected shared helpers and the existing isolated window
close tests; it must not be reported as completed normal inventory gameplay.

## Isolated native acceptance

The matrix covers 120 cases: six status values `(0, 1, 2, 3, 4, 255)`, gift
absent/present, ordinary/snapshot marker, and five inventory/field/mailbox/Pak/send
contexts. Marker cases contain deliberately opaque bytes, not valid decoder
envelopes; they test that selection does not interpret letter text.

Every case verifies the selector return and the complete unchanged 164-byte
letter. All 44 static definitions pass native label-length checks. The complete
tag image remains unchanged. Current-player and field globals are restored;
the entire live save payload, allocation/stack/module guards, allocation free,
checkpoint restoration, blank FlashRAM, and graceful shutdown are checked.

The fixture allocates its complete synthetic structures, including the large
submenu overlay prefix. It does not use fabricated pointers into unallocated
memory. It runs in a fresh, silent emulator process and requires a saved machine
checkpoint. Existing user saves are not inputs or write targets.

Portable tests cover the reference selector across all 256 status bytes, paired
marker cases, static pointers/callbacks at three relocation bases, unchanged
unrelocated bytes, BSS, altered-source rejection, and invalid destinations.
The portable model is not additional native execution coverage for untested
status values. Exact run identifiers and hashes are recorded in the work log.
