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
