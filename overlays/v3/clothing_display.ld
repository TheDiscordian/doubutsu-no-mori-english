OUTPUT_ARCH(mips)
ENTRY(af_v3_display_clothing_index)
af_v3_item_type = 0x8046744C;
SECTIONS
{
    . = 0x80466200;
    .text : { *(.text.af_v3_display_clothing_index) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x80466600, "Clothing display helper overlaps its profile")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "Unexpected clothing display state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
