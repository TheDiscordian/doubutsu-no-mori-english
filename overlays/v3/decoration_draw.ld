OUTPUT_ARCH(mips)
ENTRY(af_decor_draw)
SECTIONS {
    . = 0x80700000;
    .text : { *(.text.af_decor_draw) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x80704000, "Decoration renderer exceeds reserved code")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "Unowned decoration rendering state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
