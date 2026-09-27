OUTPUT_ARCH(mips)
ENTRY(af_v3_console_validate)
/* Zero-linked preparation only; a native installer must assign checked RAM. */
SECTIONS {
    . = 0;
    .text : { *(.text.af_v3_console_validate) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x4000,"Console persistence core exceeds preparation bound")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0,"Unexpected console globals")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
