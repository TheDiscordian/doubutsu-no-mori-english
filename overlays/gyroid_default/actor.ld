OUTPUT_ARCH(mips)
ENTRY(af_gyroid_default_demo)
SECTIONS {
    . = 0x8096AB90;
    __gyroid_start = .;
    .text : {
        KEEP(*(.native))
        default.o(.text .text.*)
        adapter.o(.text .text.*)
        . = ALIGN(16);
        __gyroid_code_end = .;
        KEEP(*(.gyroid_default))
        . = ALIGN(16);
    }
    __gyroid_end = .;
    .unexpected : { *(.rodata .rodata.* .data .data.* .bss .bss.* COMMON) }
    ASSERT(SIZEOF(.unexpected) == 0, "Unexpected gyroid writable storage or constants")
    ASSERT(__gyroid_end - __gyroid_start == 0x1B40, "Changed gyroid actor allocation")
    /DISCARD/ : { *(.reginfo .MIPS.abiflags .pdr .comment .gnu.attributes .note.*) }
}
