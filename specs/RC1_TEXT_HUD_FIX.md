# V1RC1 first-player, currency-unit, and clock-edge correction

Apply after the checked hiring-notice correction, retaining the supplied V1RC1
and all save data. `tools/rc1_text_hud_fix.py` addresses findings V1-13, V1-15,
and V1-16. The keyboard follow-up is a separate pending implementation.

## First-time-player choice

The actor at VROM `008A1F10`, linked RAM `809BE720`, retains the four-byte
`はじめて` label at offset `2518`. The branch at `809BF348..809BF364` copies
that literal into one of the existing enlarged choice rows. The supplied GC
`ac_npc_p_sel2_talk.c_inc` uses the seven-byte `I'm new` string, bound to
`new_player_str$706`, `.data:00071010`.

Append those complete seven bytes plus nine alignment bytes to the actor's
read-only section. Change only low-address instruction `809BF354` from
`24A50C38` to `24A50E40`, and copy length `809BF360` from `24060004` to
`24060007`. Preserve the native mem_copy call, choice branches, player names,
stack expansion, all prior reader patches, and saved formats. Do not overwrite
the data after the original four-byte label to make the English fit.

The section sizes change from `(9376,592,48,0)` to `(9376,592,64,0)`; all 188
relocations retain their offsets/types. Check relocated images at `80200010`
and `80378010`, including signed-low carry, exact English pointer, and every
unrelated instruction/data byte. Move the actor/relocation DMA entries to
`03E90000/03EA0000`, preserving their indices and adjacency. Update the actor
table's four allocation words at `80101950`; its loaded/profile fields remain.
The actor grows sixteen bytes, with no new persistent allocation or save field.

## Shop currency unit

The already translated heading and the unit after the amount are distinct
images. Native `00A22000:B7D0` is 32×16 I4 `ベル`; its reader at `B408` and
quad at `B2E0` remain. English GC `mny_win_beruT_model` at `.data:008972A0`
binds `fri_win_bell_tex` at `008968A0`, also 32×16 I4. Untile all 256 source
bytes and install the complete `Bells` image in the existing slot.

Keep the native unit quad and amount spacing. GC's amount layout differs, so
moving the native unit six pixels left just to match its donor X position would
be an unrelated spacing change. Preserve the corrected heading, bubble, cash
calculation, number rendering, and all other texture/geometry data.

## PM edge artifact

The native clock uses two 16×16 I4 images at bank offsets `3408/3488`, selected
by the retained table at `3510`. The PM image's first column contains the `p`
descender at rows fourteen/fifteen, while its final column is blank there.
The AM/PM quad samples through S=16 with bilinear filtering and wrapping:
its right edge blends that descending first column beside the `m`.

Compile the native load with clamp on both axes, retaining format, dimensions,
mask sizes, segment-8 image source, and all other parameters. In the original
56-byte load at `2B80`, only the two tile words gain bits `00080200`.
The pixels, selection table, timekeeping, blink, and corrected AM/PM placement
do not change. This fixes out-of-bounds edge wrapping, not the font atlas.

## Validation and output

Require the exact input cartridge and supplied GC hashes. Reconstruct the
32-MiB ROM from the verified retail source, retaining every unrelated DMA
resource and both startup copies. Verify the full UPS round trip, actor
relocations, exact donor pixels, compiled tile flags, and unchanged saved data
contracts. Ordinary screen/hardware rechecking remains separate evidence.
