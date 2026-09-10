OUTPUT_ARCH(mips)
ENTRY(af_apology_editor_init)
INCLUDE imports.ld
SECTIONS {
    . = 0x80885140;
    .text : {
        KEEP(*(.native))
        __apology_start = .;
        *(.text .text.*)
        . = ALIGN(16);
        __apology_code_end = .;
        *(.rodata .rodata.* .data .data.*)
        . = ALIGN(16);
        __apology_bss_start = .;
        *(.bss .bss.* COMMON)
        . = ALIGN(16);
    }
    __apology_end = .;
    ASSERT(__apology_start == 0x8088A100, "Previous complete editor size changed")
    ASSERT(__apology_end - 0x80888B20 <= 0x3000, "Apology editor exceeds its construction bound")
    /DISCARD/ : { *(.reginfo .MIPS.abiflags .pdr .comment .gnu.attributes .note.*) }
}
