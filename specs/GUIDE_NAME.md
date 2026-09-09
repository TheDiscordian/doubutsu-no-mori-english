# Complete opening-guide dialogue name

The guide2 actor's preparation at `809C8248..809C834C` places the selected
animal's name in coloured dialogue field five. Its eight-byte temporary at
`sp+2C..34` fits immediately below the saved animal-identity pointer at `sp+34`
in the existing `40`-byte frame. Earlier numeric fields three and four reuse
the temporary at their native six-byte capacity; those preparations do not
change. The field's original colour-one fifth argument is preserved.

Only the name call at `809C8318` and field length at `809C8338` change. The new
private `af_guide_name` adapter first fills the native six-byte name and appends
two spaces, then requests the complete resource name for animal identities
`E000..E0D7`. Null, out-of-range, and special-actor identities keep the native
animal-name fallback. A rejected resource leaves that complete padded fallback
intact. The verified resident loader performs no writes on failure.

The adapter uses its own 32-byte stack frame and preserves `ra`, `s0`, and `s1`.
It appends 112 bytes to the actor without widening the caller frame, actor data
structure, or saved identity. The original image is 9,152 bytes; the new image
is 9,264. Original relocation offsets/targets remain intact after flattening the
original text/data/rodata sections, and only the new local adapter call adds a
relocation. The adapter's two main/resident calls remain fixed.

The actor/relocation DMA entries move from `008AB7E0`/`008ADBA0` to
`03B20000`/`03B30000` at the same indices. The native main-code actor row at
`80101970` changes its ROM/RAM endpoints, retaining its actor-profile pointer
and other fields. Installation rejects changed source images, relocation,
owner metadata, overlapping changes, altered native identity fallback,
unapproved resident code, or missing full-name resources.

Focused checks cover independent MIPS assembly, caller and adapter frames,
colour/slot/length, all identity-range boundaries, unchanged numeric fields,
two relocation bases, failed-guard atomicity, full cartridge retention, and UPS
reconstruction. Combined accounting verifies this installed reader and keeps
other incomplete name readers pending without duplicating source weights.
Normal opening-guide interaction remains in the combined v0 smoke pass.
