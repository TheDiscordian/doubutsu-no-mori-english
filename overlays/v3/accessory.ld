OUTPUT_ARCH(mips)
ENTRY(af_v3_accessory_draw)
SECTIONS
{
    . = 0x80473100;
    .text : { *(.text.af_v3_accessory_draw) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x80474000, "Accessory helper overlaps its registry")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "Accessory helper must have no persistent actor state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
