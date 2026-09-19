OUTPUT_ARCH(mips)
ENTRY(af_v3_equipment_category)
SECTIONS
{
    . = 0x804AA000;
    .text : { *(.text.af_v3_equipment_category) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x804AA200, "Item category reader overlaps data")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "Unexpected item category state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
