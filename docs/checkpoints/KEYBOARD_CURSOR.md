# Corrected keyboard cursor and native input

## Defect and correction

The frame-controlled `grid-checkpoint-frames-01` run proves uppercase/lowercase
entry, single deletion, and the six-character name limit, then fails C-left:
cursor 6 remains 6 instead of becoming 5. This is a game defect, not another
timing failure. The original game disassembly proves that the grid's internal
direction enumeration uses incorrect native command numbers for left, right,
and down. `core.h` now emits right=1, left=2, up=3, down=4.

The source-compiled correction preserves all bridge/data/state addresses with
12 bytes of linker padding. It changes 623 controller bytes, retains every
previous editor instruction outside that controller, and updates the exact
relocation profile. Saved fields, capacities, handlers, drawing, and allocation
remain unchanged. See [the native ABI specification](../../specs/KEYBOARD_CURSOR_ABI.md).

## Results

- Five existing controller/resource/bridge checks pass, including sanitizers
  and independent MIPS compilation.
- Three existing compiled/integration checks pass, including a fresh full
  corrected compilation and strict verification of the retained original build.
- Three correction checks pass: original-ROM numeric ABI, complete artwork/text
  retention and patch reconstruction, and rejection of mixed/unreviewed profiles.
  The numeric test's initial fixture uses the wrong VROM constant; using the
  existing authoritative `EDITOR` constant passes the focused rerun (0.042 s).
  The other two checks pass on their first run (combined batch 33.387 s).
- Two frame-input helper checks pass, including controller release on failure.
- `grid-cursor-frames-01` completes 40 recorded steps with graceful shutdown.
  From an empty six-character field it types Q/q, deletes only q, refuses excess
  input at `Qqqqqq`, moves the cursor 6→5→6, changes page 0→1, and accepts Done.
  Rover's English message `2ACA` follows. The visible name and returned
  conversation are inspected in the isolated captures. The captured symbol-page
  image still shows the preceding rendered page; the page-state check is native
  state evidence, not visual approval of that frame. All observed grid errors
  remain zero, and the resident memory guards remain intact.

The native correction probe uses the exact older
`title-nookington-combined-01` ROM and matching isolated checkpoint, with guarded
replacement of only the loaded controller code. It is not a fresh boot of the
latest cartridge. The old hint glyphs visible in those captures belong to that
older ROM; current builds retain the separately checked three-byte hint fix.
The checkpoint is restored before exit. No normal save or hardware proof is
inferred from test-save files.

## Combined candidates

Without the title: `build/keyboard-grid-cursor-01/animal-forest-halfwidth.z64`.
ROM SHA-256:
`2725492f603d6dda9d1984ae4e3dcced520786a6c43e9180082e288d62cdd419`.
UPS SHA-256:
`1705dff2b87c17d2639412715f9615ecc64e500a3257f7107bf2326b63339d3c`.

With the complete English title:
`build/title-cursor-combined-01/animal-forest-title-preview.z64`.
ROM SHA-256:
`b42b63b0c59b9e947338dc3ac477f7c8562dd6cbd9dddbdc3831ca49622b63c6`.
UPS SHA-256:
`058429ee60ecd3fd6e78505fbacf8cc394203097470be1f5e0b735c219390615`.
This 32-MiB cartridge requires an Expansion Pak. The ordinary four-MiB heap and
save format remain unchanged. All preceding conversation fixes, Shrine wording,
screen headings, shop/police/Redd art, and English resources are retained.
One focused full title-combination check passes in 8.353 seconds, including
patch reconstruction, every preceding resource, strict corrected grid ownership,
and identical tested title/boot/warning resources.
The full combined translation counter also runs successfully against the new
untitled cartridge with all installed text routes retained. No artwork inventory
completion or gameplay acceptance is inferred from that text measurement.

The title component reuses recorded native evidence for its unchanged code,
assets, low-memory warning, and START path. Ordinary multi-line letter/notice/
owner-message editing, normal save/restart, changed buildings in their normal
scenes, and original-hardware acceptance remain playtest work. Continue remaining
Japanese artwork and actual reported defects; do not repeat the opening sequence
or expand this completed test into an exhaustive keyboard matrix.
