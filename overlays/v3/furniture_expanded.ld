OUTPUT_ARCH(mips)
ENTRY(af_v3_furniture_import_profile)
af_v3_display_clothing_index = 0x80466200;
af_v3_save_halt = 0x80469270;
SECTIONS
{
    . = 0x80465800;
    .text : { *(.text.af_v3_furniture_import_profile) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x80466000, "Expanded furniture code overlaps the clothing mannequin")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "Unexpected expanded furniture state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
