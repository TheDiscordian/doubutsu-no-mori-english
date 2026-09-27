OUTPUT_ARCH(mips)
ENTRY(af_v3_qd_validate)
SECTIONS {
    . = 0;
    .text : { *(.text.af_v3_qd_validate) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0,"Unexpected disk globals")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
