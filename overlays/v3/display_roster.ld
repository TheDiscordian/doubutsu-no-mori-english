OUTPUT_ARCH(mips)
ENTRY(af_v3_all_display_clothing_index)
af_v3_item_type = 0x8046744C;
SECTIONS
{
    . = 0x80466380;
    .text : { *(.text.af_v3_all_display_clothing_index) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x80466540, "Display roster overlaps the aloha profiles")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "Unexpected display roster state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
