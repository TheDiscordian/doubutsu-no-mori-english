# V2 N64-inspired keyboard

## Active scope

V2 implementation is authorised. Keep V1 Final and its accepted results intact,
use its exact cartridge as the development baseline, and create V2 outputs in
new ignored directories. No public release is authorised; the repository and
all patch artifacts remain private. Publication approval is not the active task.

## Requested presentation

- Keep a layout similar to the English GameCube keyboard.
- Use a greyer background inspired by the Nintendo 64 controller.
- Use button images matching the N64 controller and the actual input bindings.
- Include a control-stick image on the left, as in the GC layout and original
  N64 keyboard. Prefer the existing native artwork where suitable.

## Retained behaviour

Preserve V1's accepted keyboard sounds, corrected corner/label positioning,
consolidated symbol page, proportional editor, N64 input controls, and save
compatibility. The visual redesign must not silently remap controls or imply
GameCube-only buttons. Bind the native stick/button assets to their actual
texture loads, inspect them, and reuse their pixels where suitable. Prefer
renderer tint/geometry changes and native artwork to unnecessary redraws.

Replace only the keyboard's owned presentation suffix. Preserve its complete
editing/input prefix, existing key positions and glyph metrics, page tables,
sound calls, saved fields, native callbacks, and all unrelated ROM resources.
Respect the existing 8-KiB suffix reservation where possible; any additional
memory requirement must be explicitly checked before installation. Bound all
graphics commands and texture rectangles, including animated menu positions.

Compile with the existing pinned Docker toolchain. Verify the new suffix,
relocations, resource retention, and patch reconstruction with focused checks.
Use one bounded silent native drawing check when useful; do not rerun old
candidate tests, the full suite, or previously accepted save/editor workflows.

## Implemented presentation

`tools/keyboard_v2.py` replaces the existing suffix, not the complete editor.
The source uses the accepted corrected GC panel geometry and textures with
primitive colour `(235,235,235)` and environment colour `(174,177,181)`.
The light grey body keeps the existing dark control hints readable.
All forty keys and the complete quarter-pixel glyph-origin table retain their
accepted positions. There are still two pages and the existing input bindings.

The native resource at VROM `00A40000` supplies all controller textures without
pixel edits. Its native editor tables and each material's texture load and
dimensions bind the selected assets. A, B, and Start use their original RGBA16
colour textures with the separate I4 soft alpha mask; drawing the colour alone
would create opaque coloured squares. Four separate yellow C buttons identify
caret control. The blank native R shoulder is mirrored for L, with L/R labels
drawn by the existing font. Z retains its native labelled texture. Held buttons
select the original pressed frames using the read-only button getter.

The centre stick texture is placed at `(18,137)` in a 48×48 rectangle; its
transparent margins leave the visible stick to the left of the key grid.
The stick is a static illustration, not a new input-control implementation.
English hints retain case, page, order, movement, caret, insert, delete, space,
completion, and alteration instructions. Plus signs use the native font code.
Movement is explained in the bottom control hint. Do not place a separate
full-size `Move` label beside the stick: the curved panel edge and staggered
keys leave insufficient readable space for that redundant hint.

Every icon is clipped before emitting an unsigned RDP rectangle. Frame/icon/key
commands reserve 8,192 graphics bytes before emission; each subsequent font
call retains its own existing buffer check. The current suffix occupies 7,744
rounded bytes inside the existing 8,192-byte overlay reservation, leaving 448
bytes. No additional pool allocation, resident module, or saved fields change.

## Ownership

The exact V1 Final cartridge SHA-256 is
`0561182044c1526010ed77b1b9c72ac268794c2f7b615f8fa70c007f366483bf`.
Keep all 30,272 prefix bytes except the four-byte drawing call at linked
`808882D8`. Recover its original internal target only for suffix compilation;
do not restore the earlier page counts, symbol tables, or ordinary-space code.
The recovered prefix SHA-256 is
`649bc5f566bff529357b697b810d2b314641a55cf4953d74206a39e39d5bcf4b`.

The owner remains `03E70000`, relocation remains `03E80000`, and linked RAM
remains `80885140`. Change only its length fields in `007749C0+2B50`; retain
main-code pool instruction `25CE7620`. Compare the complete retained prefix
against V1 Final at runtime bases `80200010` and `80378010`, including the
low-half carry. The finished cartridge retains every unrelated resource and
DMA identity, and its UPS must reconstruct the complete output.

## Current verification boundary

Four current artifact checks pass, and the unchanged decoder retains its four
passing checks. Controlled native drawing and screenshot review pass on the
recorded `v2-keyboard-03` build before the redundant-label removal. The
checkpoint-restored preview uses verified-empty Expansion Pak scratch, with
the relocation model explicitly configured for eight MiB. The preview binds
the cartridge loader, loads the installed keyboard and native matrix callback,
and checks retained key geometry, the grey material, guards, and editor/save RAM.

The fixture supplies the normal native menu projection and routes its drawing
after the title world. It stores commands/vertices in the large opaque arena,
skips that block in the ordinary opaque stream, then calls the block from the
final overlay stream. These changes exist only in the fixture, not the ROM.
Use the isolated emulator display to judge appearance: debugger RAM framebuffer
reads can contain unfinished GPU output. Do not mistake a partially drawn RAM
image or omitted title-fixture menu setup for a cartridge rendering defect.

The [ordinary work record](../docs/checkpoints/KEYBOARD_V2_ORDINARY.md) contains
the current hashes and exact executed builds. Ordinary name entry, spaces,
caret movement, deletion, and Start confirmation pass. Representative held
controls are reviewed in isolated screenshots. The final redundant-label
removal receives focused cartridge checks, without another native replay.
Other keyboard callers, remaining pressed states, and original hardware remain
playtest limits. Unchanged saved formats support expected V1 Final ↔ V2
compatibility, not a claim that those loading directions have been executed.

## Private offline handoff

`tools/package_v2.py` packages the recorded development ROM's existing UPS,
without compiling or changing the cartridge. It binds the complete ROM/patch
and construction-receipt hashes, verifies every recorded builder source at
the cartridge revision, and requires committed package documents and patcher
sources. The standalone patcher must reconstruct the exact current ROM from
the original Japanese input before the package is written.

The archive contains the UPS, offline instructions, source/build guides,
credits, tooling licence, standalone Python patcher and library, manifest,
and checksums. Only the allowlisted files are included: never ROMs, saves,
checkpoints, or extracted artwork. Output paths must be fresh and inside the
ignored build directory. Keep V1 Final and all existing artifacts unchanged.

The manifest distinguishes cartridge and packaging revisions, retained native
evidence and exact-output execution, hardware limits, and expected save loading
in both directions. V2 Development is a private handoff, not an RC sequence,
public release, or claim of exhaustive acceptance. Packaging does not authorise
an upload or repository visibility change.
