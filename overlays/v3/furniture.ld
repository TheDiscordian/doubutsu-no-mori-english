OUTPUT_ARCH(mips)
ENTRY(af_v3_furniture_import_profile)
SECTIONS
{
    . = 0x80465000;
    .text : { *(.text.af_v3_furniture_import_profile) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x80465800, "V3 furniture code overlaps its profile table")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "Unexpected furniture helper state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
