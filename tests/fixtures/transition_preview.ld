OUTPUT_ARCH(mips)
ENTRY(af_transition_preview)
SECTIONS {
    . = 0x80500000;
    .text : { *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss : { *(.bss .bss.* COMMON) }
    /DISCARD/ : { *(.pdr .reginfo .MIPS.abiflags .comment .gnu.attributes .note*) }
}
