OUTPUT_ARCH(mips)
ENTRY(af_v3_furniture_import_profile)
SECTIONS
{
    . = 0x80465800;
    .text : { *(.text.af_v3_furniture_import_profile) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x804666CC, "Expanded furniture code overlaps imported seed profiles")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "Unexpected expanded furniture state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
