# First V1 hardware report: source and fix evidence

## Reported cartridge and open work

The user identifies `title-stall-combined-01/animal-forest-title-preview.z64`,
SHA-256 `128f19b734565e5e0c3af15aaf1fef8fb066155039404a2bfdd29efe8010bf19`.
Press Start is corrupt on both first boot and return. The
[eleven recorded findings](../V1_PLAYTEST_BUGS.md) include broken mail/board
editing, remaining Japanese interface/name readers, and keyboard presentation.
The positive keyboard-layout feedback does not cover its caller-window layout.

## Press Start cause

The former import wrongly treated the two compatibility textures as tiled GX
IA4. Untiling and exchanging their intensity/alpha nibbles scrambled already
linear N64 IA8 source bytes. Direct source decoding with the correct format
shows readable English. The supplied GC actor's `aAL_press_start_draw` uses
`gDPLoadTextureTile`, not the Dolphin tiled model path. The native title actor
and installed main-logo models do not need code changes for this correction.

`build/title-start-hardware-diagnostic-02` observes one ordinary native Press
Start draw in the exact reported cartridge. It verifies the full relocated
title and loaded texture bank, traverses 1298 actual root/nested drawing commands,
and resolves the three prompt reads to bank `802CF7E0` plus `1110/1510/1910`.
The five-step silent run shuts down gracefully; no game-memory write or user
save is involved. This confirms the reader/load binding, not correct appearance.
The first attempt stops before emulation because Xvfb is absent from PATH; the
single corrected retry selects the already installed headless Xvfb explicitly.

The source views are `gc-press-start-first.png`, `gc-start-linear.png`, and
`gc-start-linear-nibble-swap.png` in `build/artwork-inspection/`. These are decoded
source assets, not desktop screenshots or a human hardware recheck.

## Intermediate correction

`tools/title_start_fix.py` installs the two untouched English source tiles over
the complete civic-interior candidate, retaining the transparent third tile.
Its deterministic reconstruction retains all 3386 DMA identities, all unrelated
resources, both startup copies, 32-MiB ROM size, Expansion Pak requirement,
native title animation/blink/positions, and saved formats.

Local ROM: `build/v1-playtest-fixes-01/animal-forest-title-preview.z64`.
ROM SHA-256:
`1898c04ffb844f5cd7ccd0199dae9c41c733e63e8accbe128a1a5933b71a0a08`.
UPS SHA-256:
`4db17ca213d5fbf3e0a80e2922e7d27cd22154695cb58c78448a6009a3fa2dd1`.
Installed title-bank SHA-256:
`9732ea7ac8712d6b7b2d99149b236afd38af5fbc6cd5b4730ccbed320d779046`.

Three focused tests pass in 8.718 seconds: exact source representation and
incorrect-format rejection, full cartridge/UPS/owner/startup retention, and
unknown predecessor/allocation/boot-change rejection. The first repacking build
correctly rejects an expanded same-address dialogue bank; the corrected
reconstruction records those existing expanded ranges explicitly. No partial
cartridge is published by that failed build.

This is an intermediate fix artifact, not a claim that the other ten findings
are complete. A combined fix handoff, public recipe/package update, and hardware
recheck remain. The earlier supplied ROMs and packages stay unchanged.

## Editor cause and next implementation

The mail read-body/footer hooks and notice reader explicitly fall back to
native fixed-column code in editing mode. The full-name letter header adapter
retains the native body/footer cursor. Saved text therefore displays with the
English pixel-width layout while editing wraps at sixteen original columns
and advances the caret in twelve-pixel steps.

Replace those linked editing layout/draw/navigation paths together. Preserve
the native 96-byte body storage, header/body/footer selection, manual newlines,
confirmation, and publication. Do not simply double the saved column count or
halve only the cursor constant. Names, gyroid drafts, and apology input retain
their separate existing adapters. See the [fix contract](../../specs/V1_PLAYTEST_FIXES.md).

## Pixel-editor candidate

`tools/editor_pixel_fix.py` builds
`build/v1-editor-pixel-fix-03/animal-forest-title-preview.z64` on the corrected
title ROM. ROM SHA-256:
`7c43f742009e391cae42bdf410f239f8a9c3aaf58003fd4f27371561109313ad`.
UPS SHA-256:
`3d683fddb0189b999ef6035688d9e9c2e942ea1cbe179d569c39ecf363b000b3`.
The complete images grow by 4160 aligned bytes across the shared editor,
letter window, and notice window. The shared pool reserves 5120 extra bytes.
All previous text/artwork resources, physical boot code, DMA identities, and
saved capacities are retained.

Four tests pass in 3.062 seconds under `test_editor_pixels.py`. The host bridge
runs with address/undefined-behaviour sanitizers and checks field switching,
96-byte insertion bounds, manual blank lines, pixel-based vertical movement,
body/footer caret alignment, and silent sound-call accounting. An independent
per-glyph check uses the actual installed width table. ROM checks verify both
relocation bases, every untouched resource, pool instruction arithmetic, and UPS
reconstruction. Resizing requires explicit resource ownership and rejects VROM
overlap. No original save is edited.

The first compilation attempt rejects an unconfigured resident-module report;
the builder uses the complete cartridge's configured report. The next attempt
rejects an obsolete pool predecessor; the current embedded-menu-text reservation
is retained before adding the new allowance. Neither failed attempt writes a
candidate cartridge. The three successful images and their source/relocation/
stack records are in the candidate's `editor/`, `letter/`, and `notice/` folders.

Native checking uses the real loader and editing functions in disposable owned
RAM. The first attempt requests its fixture allocation at the title, receives a
clean null allocation, and stops before testing editor code. The single setup
retry enters the game before taking its checkpoint and passes: 16 native calls,
45 assertions, all three complete cartridge loads/relocations, actual native
insertion at 31/95/96-byte boundaries, pixel-position queries and vertical
movement, native body-to-header selection, refreshed grid ownership, and actual
mail/notice font drawing into bounded command buffers. All allocation/stack/
resident guards and the complete live save remain unchanged. The fixture frees
its allocation, restores its checkpoint, resumes, and shuts down gracefully.
Evidence is `build/v1-editor-pixel-native-02/results.json` (135 records).
No code is uploaded and no audio is played. This is controlled native execution,
not an original-hardware recheck. Remaining labels/background work continues
without replaying the passing setup.
