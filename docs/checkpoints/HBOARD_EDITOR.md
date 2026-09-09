# Owner-message editor checkpoint

## Implemented

The portable owner-editor core has a complete 128-byte private draft, exact
saved-default recognition, four-row proportional layout, manual-newline
preservation, pixel-based cursor navigation, insertion/deletion/case edits,
64-byte custom-save validation, default restoration, and saved-field conflict
detection. No operation silently truncates text. Opening and editing leave the
saved field alone; only accepted confirmation publishes it.

The native/editor/reference audit pins six original files, both allocation
records, eight supplied GameCube functions, both reference C files, and the
complete four-line default. The native field is immediately followed by held
Bells. Native mode 1 shares its editing function with mode 2, so the planned
bridge is attached to the mode-1 table entry rather than globally replacing it.
The [specification](../../specs/HBOARD_EDITOR.md) records the concrete offsets,
save contract, integration approach, and remaining acceptance.

## Evidence

`python3 -m unittest discover -s tests -p test_hboard_editor.py -v` passes all
nine focused tests. These cover all 16,320 one-byte saved-default variations,
unchanged custom round trips, the complete actual 92-byte English greeting with
installed font widths, line and draft limits, rejected confirmation and recovery,
saved-field conflicts and guards, navigation/case, invalid inputs, and the
source-bound MIPS object. Over 3,000 valid cursor positions compare with the
unchanged extracted GameCube `mED_get_col_line_width` and `mED_check_line_over`;
source line spans also compare with `mHB_strLineCheck`. This is execution of
the pinned C reference on the host, not execution of GameCube CPU instructions.

The AddressSanitizer/UndefinedBehaviorSanitizer executable passes 10,000 mixed
commands plus pointer, full-buffer, layout, save-limit, and adjacent-save guards:

```sh
gcc -std=c99 -Wall -Wextra -Werror -O1 -g \
  -fsanitize=address,undefined -fno-omit-frame-pointer \
  runtime/hboard_editor.c tests/hboard_editor_check.c \
  -o build/hboard-editor-core/sanitize-check
build/hboard-editor-core/sanitize-check
```

`python3 tools/build_hboard_editor_core.py` compiles through the pinned Docker
MIPS toolchain. The core has 2,312 text bytes, 32 read-only data bytes, zero
mutable globals/BSS, and no unresolved imports. GCC's implicit struct-copy/zero
library calls are eliminated through explicit private copy/zero helpers.
The object SHA-256 is
`f1cbdbbdb266209320061bc7599adf56337b725574bc8186988a5e226d66eb48`.
Generated artifacts, source/reference hashes, flags, disassembly, and compiler
stack reports are in `build/hboard-editor-core/`. An independent build in
`build/hboard-editor-core-repro/` produces the same object hash and both default
resource hashes.

Reported function frames are layout=72, insert=280, begin=224, command=96,
pack=88, and commit=24 bytes. The command→insert→layout chain uses at most
448 bytes of those frames; this is not a measured whole-game stack bound.
The draft structure is 196 bytes; the overlay also needs an explicitly allocated
width cache and bridge state.

The first real-default test incorrectly expected a trailing space and a
21-byte final line. The supplied full default ends at its period, is 92 bytes,
and has a 22-byte final line. The assertion is corrected to the bound source;
the production layout is unchanged by that fixture correction.

## Next work and limits

The current complete cartridge remains `build/gyroid-default-pilot`; this core
is not yet installed and adds no text-replacement credit. No completed native
batch is replayed for this preparatory work.

Connect initialization, mode-1 edits, cursor updates, drawing, capacity/conflict
warnings, successful confirmation, and cleanup in one owned overlay change.
Preserve all other editor modes and the original English-first palette. Grow
the verified submenu allocation for the actual combined editor/notice ownership,
update both relevant audits, and require atomic installation. Then build the
complete cartridge and perform a bounded native editor batch. Normal interaction,
save/reload, rendering review, original hardware, full project review, release,
title replacement, and the GameCube-style keyboard remain unfinished.
