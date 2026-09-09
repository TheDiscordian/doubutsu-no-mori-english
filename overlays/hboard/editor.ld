OUTPUT_ARCH(mips)
ENTRY(af_hboard_editor_init)
INCLUDE imports.ld
SECTIONS {
    . = 0x80885140;
    __hboard_start = .;
    .text : {
        KEEP(*(.native))
        __hboard_code_start = .;
        *(.text .text.*)
        . = ALIGN(16);
        __hboard_code_end = .;
        KEEP(*(.hboard_defaults))
        *(.rodata .rodata.* .data .data.*)
        . = ALIGN(16);
        __hboard_bss_start = .;
        *(.bss .bss.* COMMON)
        . = ALIGN(16);
    }
    __hboard_end = .;
    ASSERT(__hboard_code_start == 0x80888B30, "Native editor state/callback reservation changed")
    ASSERT(__hboard_end - 0x80888B20 <= 0x2000, "Additional editor pool reservation exceeded")
    /DISCARD/ : { *(.reginfo .MIPS.abiflags .pdr .comment .gnu.attributes .note.*) }
}
