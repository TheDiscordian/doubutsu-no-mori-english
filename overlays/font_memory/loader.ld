OUTPUT_ARCH(mips)
ENTRY(af_font_expansion_init)
af_crc32 = 0x80195938;
SECTIONS {
    . = 0x8019614C;
    .text : SUBALIGN(4) { *(.text .text.*) *(.rodata .rodata.*) }
    ASSERT(af_font_expansion_init == 0x8019614C, "Changed font startup entry")
    ASSERT(SIZEOF(.text) <= 0x26C, "Font loader exceeds its original function")
    .data : { *(.data .data.* .bss .bss.* COMMON) }
    ASSERT(SIZEOF(.data) == 0, "Font loader needs unexpected writable storage")
    /DISCARD/ : { *(.reginfo .MIPS.abiflags .pdr .comment .gnu.attributes .note.*) }
}
