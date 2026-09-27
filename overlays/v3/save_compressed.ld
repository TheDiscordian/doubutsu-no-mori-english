OUTPUT_ARCH(mips)
ENTRY(af_v3_save_compress)
SECTIONS {
    . = 0;
    .text : { *(.text.af_v3_save_compress) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x4000,"Compressed save envelope exceeds preparation bound")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0,"Unexpected save envelope globals")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
