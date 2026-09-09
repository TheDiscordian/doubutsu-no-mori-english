# Owner-message editor checkpoint

## Implemented

The complete `build/hboard-editor-pilot` cartridge installs initialization,
editing, cursor, drawing/status, confirmation, and destructor bridges together.
The original frame, portrait, English-first palette, all other editor modes,
and every earlier translation resource remain. Native editor execution is the
next acceptance step; this checkpoint does not claim it.

The portable owner-editor core has a complete 128-byte private draft, exact
saved-default recognition, four-row proportional layout, manual-newline
preservation, pixel-based cursor navigation, insertion/deletion/case edits,
64-byte custom-save validation, default restoration, and saved-field conflict
detection. No operation silently truncates text. Opening and editing leave the
saved field alone; only accepted confirmation publishes it.

The native/editor/reference audit pins six original files, both allocation
records, eight supplied GameCube functions, both reference C files, and the
complete four-line default. The native field is immediately followed by held
Bells. Native mode 1 shares its editing function with mode 2, so the installed
bridge is attached to the mode-1 table entry rather than globally replacing it.
The [specification](../../specs/HBOARD_EDITOR.md) records the concrete offsets,
save contract, integration approach, and remaining acceptance.

The 20,416-byte editor retains the original 48-byte BSS addresses and adds its
owned callback and 472-byte context. Its 1,440-byte relocation file preserves
original row order and includes only verified owned pointers/calls. The window
uses a 52-byte stack-preserving indirect bridge; its native allocation and
relocation file stay unchanged. Main-code pool arithmetic reserves a separate
8 KiB for the editor's 5,568 aligned bytes of growth, alongside the notice
reader's existing 20 KiB. The combined dominant submenu pool is 243,072 bytes.

Confirmation never truncates. A too-long custom draft remains editable with an
explicit capacity message. A saved-field conflict keeps the newer value and
explains that another Done press closes without saving. Each new editor entry
resets ownership, and destruction discards unconfirmed private text.

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
The draft structure is 196 bytes; the overlay explicitly allocates its
width cache and bridge state in the 472-byte context.

The first real-default test incorrectly expected a trailing space and a
21-byte final line. The supplied full default ends at its period, is 92 bytes,
and has a 22-byte final line. The assertion is corrected to the bound source;
the production layout is unchanged by that fixture correction.

## Complete overlay and cartridge evidence

All eight `test_hboard_overlay.py` tests pass. The instrumented bridge C runs
under AddressSanitizer/UndefinedBehaviorSanitizer and covers all four homes,
complete default draws and positions, custom edits/confirmation/reopening,
oversized confirmation rejection and recovery, discarded drafts, conflicts,
all four other native modes, invalid-width setup, safe closing, and adjacent
saved-data guards. It checks 21 initializations, twelve destructions, and thirteen
draw-matrix calls. These use mocked native imports on the host, not MIPS execution.

Compiled/cartridge checks cover independent builds, three relocation bases,
all unchanged native prefix words, retained notice mode and metadata relocation
rules, rejected rehashed mutations, complete ROM/UPS reconstruction, actual
combined allocation instruction arithmetic, rejected partial shared installs,
and failure without modifying caller maps. Nine core tests remain passing.
Ten initial-notice and eleven seasonal-notice regression tests pass without
replaying their completed native batches.

The resident source inventory includes the new core/header while explicitly
excluding the overlay-owned C unit from resident linking. A complete rebuild
retains module SHA-256
`493bc25a922bbd9d321759677134520bbb179413985f0e047df45e6e432664c6`
and bootstrap SHA-256
`9c20b82708856897c19301bb23e35b84335482f9c10d4dd5ba5c3a3f7fb1d10f`.
All resident symbols, the 24,576-byte linked size, memory reservation, and actual
four-MiB layout remain. No saved byte count changes.

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| Editor image | 20,416 | `265ed7752365a963b5dcb4d5e21f39ba085564615b4aba8b1aaa07a60d5a21a6` |
| Appended editor code/data/state | 5,584 | `2057042c1ffa3b96ff063496d10a1e38c2408685dd0c1ac5353c5b752379470d` |
| Editor relocation | 1,440 | `a7b8a96e5b090f95be9cf85c6258117de29fc8f0edcc28186a0666b72150c3ab` |
| Complete ROM | 33,554,432 | `471ce785f009781378af34cd85c84381b6b8cd0cf1db29dde333df84fb170186` |
| UPS patch | 4,512,057 | `5860529fe593cbc664db1e3cf5aaf17db4d6c80883090e4a2e8e68c5e3c41531` |

Source-bound artifacts and disassembly are in `build/hboard-editor-overlay/`;
the independent `build/hboard-editor-overlay-repro/` agrees. That first directory
also holds the core, integration, notice/seasonal regression, compilation, and
full-build logs. The only common decompressed files changed from
`build/gyroid-default-pilot` are DMA metadata, main code's pool instruction,
submenu-owner metadata, and the window bridge. The editor/relocation pair moves
to `03940000/03948000`. Message, name, letter, font, creator, visitor actor, and
other resources remain unchanged. This installs an additional route for already
credited default text; it adds no second text-replacement credit.

## Next work and limits

Prepare one bounded silent native editor batch using the new complete cartridge.
Load the real submenu owner, editor, and window through their cartridge DMA and
relocations; exercise actual initialization, the patched mode dispatch, drawing,
confirmation, and destruction. Preserve save, stack, heap, live ownership, and
checkpoint state. Test the complete default and custom message for all four homes,
rejected oversized confirmation, and unaffected other editor modes together.
Do not replay the completed visitor-default or notice-body native batches.

The existing owner fixture in `tools/notice_reader_smoke.py` provides the verified
native loader at owner-relative `8085D128`, asset callback `8085D43C`, transition
callback `8085D4D4`, owned-state layout, graphics arena setup, and checkpoint
restoration pattern. Adapt its setup, not its already completed body tests.
Its original owner has a 64-KiB asset arena; inspect the keyboard constructor's
actual asset selection and required bounds before assuming all keyboard graphics
fit there. The editor's original state is at image offset `39B0`, callback `39E0`,
and appended context `4DE0`; code proof ranges must exclude mutable state.

Normal gameplay interaction, save/reload, window/keyboard visual review, original
hardware, remaining project text/review, release, title replacement, and the
GameCube-style keyboard remain unfinished. Controlled host drawing verifies
coordinates and full text, not the final in-game appearance.
