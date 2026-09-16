OUTPUT_ARCH(mips)
ENTRY(af_v3_equipment_pointer)
SECTIONS
{
    . = 0x804A3000;
    .text : { *(.text.af_v3_equipment_pointer) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x804A4000, "Equipment code overlaps resource records")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "Unexpected equipment state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
