OUTPUT_ARCH(mips)
ENTRY(af_v3_furniture_tables_init)
SECTIONS
{
    . = 0x8046A000;
    .text : { *(.text.af_v3_furniture_tables_init) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x8046A200, "Furniture table initializer overlaps the field bridge")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "Unexpected table initializer state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
