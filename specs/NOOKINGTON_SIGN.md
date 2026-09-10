# Nookington's main sign

## Scope

Port the supplied GameCube NOOKINGTON lettering without scaling its pixels or
replacing the rest of the N64 building. This covers the main lit sign in summer
and winter, not every decorative mark on Nookington's other atlases.

The pinned English REL's winter `obj_w_shop4_t3_tex_txt` at `.data:0058D7C0`
contains the same sign indices as summer. Extract columns 32–127 into a 96×32
CI4 texture. The quad samples the original donor U range 1055–3552, translated
by −1024 for the extraction. Keep native V coordinates, which use the native
mirrored 32-row tile, and all original positions, flags, and normals. All used
colours match both native inline palettes when interpreted using the donor's
winter palette at `.data:0058C7A0`. Do not replace the shared native palette.

## Native loading and storage

`ovl_Structure`, VROM `008CB690`, RAM `809E7ED0`, streams individual buildings,
not the entire `00D5E000` object. `func_809E8118_jp` reads each building into one
of eight fixed `2E00`-byte slots. Summer/winter range tables at `00DF4000` hold
starts at offsets `8`/`178` and ends at `C0`/`230`; Nookington's type is 11.
The loader derives `offset = start - 06000000 + 8`, reads
`ALIGN16(end - start - 8)` bytes, and records `slot - offset` as segment 6.

Original summer/winter slices are `00DC39A0`/`00DC5F80`, each `25D0` bytes.
Each extended slice is `2C80` bytes: the original slice, a `600`-byte CI4 sign,
and a `B0`-byte nested display list. Both retain `180` bytes of slot headroom.

Add a separate expanded copy of the complete installed building object at VROM
`03D00000`, in a verified free interval after the title's `03C00000` range. Preserve its
original `95480`-byte prefix, including all earlier English shop replacements.
Append summer at object offset `95480` and winter at `98100`; the complete copy
is `9AD80` bytes. Keep the original `00D5E000` resource unchanged. Redirect only
the structure loader's VROM base constant at RAM `809E8198/809E819C` from
`00D5E000` to `03D00000`. This costs cartridge storage, not RAM, and keeps segment
offsets below one MiB. Do not rely on negative segment-base arithmetic.

Update only the four Nookington range-table words and the six seasonal skeleton,
animation, and window pointers in `ovl_Depart` at `008D0D20`. Rebase the 23
explicit internal pointers in each copied slice. All other building ranges read
identical installed bytes from the copied prefix. Preserve both actor sizes,
relocation files, allocations, saved data, doors, and gameplay instructions.

## Rendering

Replace the single native two-triangle command at slice offset `AC8` with a
nested display-list call. The nested list loads the separate English CI4 sign,
sets both native render tiles to its 96-pixel stride, draws exactly the original
cached vertices 7/8/9 and 8/10/9, and restores the original atlas and both tiles.
Only the U coordinates of those four vertices change. Pipeline synchronization
separates preceding geometry, sign geometry, and the restored following geometry.
Do not change the combiner, palette, light state, vertex cache, or triangle order.

## Bounded verification

Bind the source ROM/REL/symbol identities, donor model texture relocation, sign
pixels and visible palette colours, native source slices, all relocated pointers,
unchanged actor relocation ownership, compiled native texture commands, per-slot
rounded read bounds, and every building's range-table read. Reconstruct the UPS
and verify all prior resources. Native ordinary appearance and seasonal lighting
remain separate acceptance checks; installation does not establish those results.
