OUTPUT_ARCH(mips)
ENTRY(af_notice_construct)
INCLUDE imports.ld
SECTIONS {
    . = 0x80894250;
    __notice_start = .;
    .text : {
        KEEP(*(.native))
        __notice_code_start = .;
        *(.text .text.*)
        . = ALIGN(16);
        __notice_code_end = .;
        *(.rodata .rodata.*)
        *(.data .data.*)
        . = ALIGN(16);
        __notice_bss_start = .;
        *(.bss .bss.* COMMON)
        . = ALIGN(16);
    }
    __notice_end = .;
    ASSERT(__notice_code_start == 0x80895CD0, "Native BSS address changed")
    ASSERT(__notice_end - __notice_code_start <= 0x4000, "Notice reserve exceeded")
    /DISCARD/ : { *(.reginfo .MIPS.abiflags .pdr .comment .gnu.attributes .note.*) }
}
