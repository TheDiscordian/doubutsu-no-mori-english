# Nookington's English main sign

## Installed candidates

`build/nookington-sign-02/animal-forest-halfwidth.z64` adds the full-resolution
English main sign in both seasons to the complete keyboard/grid/artwork/fix
candidate. ROM SHA-256:
`28c551708dbbc1d78333abc7ebf81d5001663859775ca9f85427ced8208b0020`.
UPS SHA-256:
`2456e7fb2695aa86feccbeb98836460c8bf4f5705fac5b5ea74d8893e3d0c735`.
The cartridge is 32 MiB and requires four MiB without the title. It remains
separate from the recommended title playtest handoff.

`build/title-nookington-combined-01/animal-forest-title-preview.z64` combines
the same sign and keyboard with the unchanged English title/warning. ROM:
`76757a029aca2d0564daff08e3f2a790bf572b66efb6a2a84fee8f26a8acf4c4`.
UPS: `dfe9cbf687f58d1f9658b302ad078018aa64468a021d68a378841888b658918a`.
This combined candidate requires an Expansion Pak; ordinary heap bounds stay
at four MiB. Incomplete keyboard acceptance remains incomplete after combination.

## Implementation

The [specification](../../specs/NOOKINGTON_SIGN.md) binds the supplied English
pixels, native model references, and per-building loader. Each sign uses a
96×32 CI4 extraction with no glyph resizing or palette changes. Only the four
sign vertices' U coordinates and their two-triangle command change; the nested
draw list restores the original atlas and both render tiles immediately after
the sign. Building positions, animation, doors, lighting, and saved data remain.

The native loader streams buildings into eight fixed 11,776-byte slots. Each
extended Nookington resource is 11,392 bytes, leaving 384 bytes. A separate
634,240-byte cartridge resource at VROM `03D00000` retains the complete earlier
building object, then appends both extended seasonal slices. The loader's source
constant changes; its algorithm and allocation do not. All other building
streams retain their exact installed contents, including the earlier English
shop textures. The original building resource remains untouched.

## Verification

Five focused checks pass in 7.473 seconds: exact sign pixels and native state
restoration, all 92 seasonal building ranges, bounded slot/CPU/RSP addresses,
unchanged native actor relocation across two heap placements, source/command
rejections, full previous-resource retention, and complete UPS reconstruction.
The relocation fixture includes the original structure BSS and its two
source-bound compiler array/sentinel constants; those are not new game pointers.
The independent native GBI compiler output matches the fixed command specification.

One additional title-combination check passes in 8.538 seconds. It verifies
complete rebuild/patch reconstruction, retained building/grid/text resources,
strict grid ownership, and identical title actor/assets/boot/warning compared
with the natively tested title. Unchanged title execution reuses its existing
evidence, not a new native run.

Native ordinary sign appearance, lighting, keyboard interaction, and hardware
acceptance remain unverified. Other decorative marks on Nookington's atlases,
bags, and remaining signs require separate work. The next combined screen check
must deliberately clear the name field before keyboard assertions; the earlier
fixed-count opening attempts are not evidence of an empty starting field. Keep
the bounded harness limit and isolated saves. No user save is accessed here.
