OUTPUT_ARCH(mips)
ENTRY(af_grid_editor_init)
INCLUDE imports.ld
SECTIONS {
    . = 0x80885140;
    .text : {
        KEEP(*(.native))
        __grid_start = .;
        *(.text .text.*)
        . = ALIGN(16);
        __grid_code_end = .;
        *(.rodata .rodata.* .data .data.*)
        . = ALIGN(16);
        __grid_bss_start = .;
        *(.bss .bss.* COMMON)
        . = ALIGN(16);
    }
    __grid_end = .;
    ASSERT(__grid_start == 0x8088ABC0, "Complete apology editor size changed")
    ASSERT(__grid_end <= 0x8088D140, "Grid exceeds its 32-KiB image reservation")
    /DISCARD/ : { *(.reginfo .MIPS.abiflags .pdr .comment .gnu.attributes .note.*) }
}
