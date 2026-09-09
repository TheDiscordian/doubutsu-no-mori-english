OUTPUT_ARCH(mips)
ENTRY(af_secret_create)
SECTIONS {
    . = 0x8091D7B0;
    __secret_start = .;
    .text : {
        KEEP(*(.native))
        *(.text .text.*)
        . = ALIGN(16);
        __secret_code_end = .;
        KEEP(*(.secret_table))
        . = ALIGN(16);
    }
    __secret_end = .;
    .unexpected : { *(.rodata .rodata.* .data .data.* .bss .bss.* COMMON) }
    ASSERT(SIZEOF(.unexpected) == 0, "Unexpected secret creator storage")
    ASSERT(__secret_end - __secret_start <= 0x8800, "Conversation allocation exceeded")
    /DISCARD/ : { *(.reginfo .MIPS.abiflags .pdr .comment .gnu.attributes .note.*) }
}
