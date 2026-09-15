OUTPUT_ARCH(mips)
ENTRY(af_v3_roster_clothing_record)
SECTIONS
{
    . = 0x80473A00;
    .text : { *(.text.af_v3_roster_clothing_record) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x80474000, "Clothing roster overlaps accessory registry")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "Clothing roster has unexpected state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
