# V1 playtest fix contract

The [human bug list](../docs/V1_PLAYTEST_BUGS.md) governs this fix pass. Preserve
original saves, all earlier translation resources, and tested native progression
fixes. Build fresh artifacts and provide one combined candidate after related
implementation changes. Intermediate fixes are not a completed V1 release.

## Press Start source representation

The English GC actor `ac_animal_logo.c`, `aAL_press_start_draw`, selects
`log_win_logo3_tex` and `log_win_logo4_tex` through the compatibility
`gDPLoadTextureTile` API: IA8, 64×16, X 96/160, Y 159. These two resources are
already linear N64 intensity:alpha bytes. They are not GX tiled alpha:intensity
textures. Texture storage must be established from its consuming path, not
inferred from the platform or from equal dimensions.

The pinned REL and scoped symbol map bind `.data:005E5020` and `005E5420`, each
1024 bytes. Their complete SHA-256 values are
`3d1eeece6cdc4781e256c7eade05979bb57ea3206b52a9b5656bbea783cbae95` and
`98b37743e07fb6b472434f5a651bf5948d4e53d8675f159faf25743946ad1fba`.
Copy them without untile or nibble exchange into native bank `01136000` at
`1110` and `1510`; keep the third 1024-byte tile at `1910` transparent. Preserve
the title overlay, allocation, transition logic, positions, native blink,
colours, and graphics commands.

`tools/title_start_fix.py` installs this correction after the title/artwork
combination. The earlier `title_assets.py` IA8 outputs and title-only builds
remain replay inputs, not corrected final prompt assets. A new playtest built
through that older path must apply this correction. The main animated logo's
23 model textures have their own verified tiled source path and stay unchanged.

Repack from the verified original, recovering every retained native DMA index,
relocated owner, expanded resource, and added file from the exact preceding
cartridge. Retain both physical/DMA startup copies, recalculate checksums,
require the same 32-MiB cartridge and complete unrelated resources, and prove
UPS reconstruction. Do not append a replacement to a padded cartridge and
silently expand it to 64 MiB.

## Mail and board layout

The human report distinguishes correct saved/read display from incorrect edit
display. The read-only mail and notice hooks deliberately fall back to native
fixed-column functions in editing mode. The letter header adapter also retains
native body/footer cursor handling. Changing the grid alone cannot fix those
caller windows.

The correction must share pixel measurements between wrapping, text, caret,
end markers, and vertical navigation. Keep explicit newline bytes and native
field capacities; do not enlarge the 96-byte mail/notice body merely by doubling
columns. Preserve letter header/body/footer selection, recipient identities,
confirmation, publication, and saved formats. Names and gyroid/apology editors
already have separate adapters and must not be accidentally replaced.
