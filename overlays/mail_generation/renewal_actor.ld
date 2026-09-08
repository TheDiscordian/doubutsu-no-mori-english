OUTPUT_ARCH(mips)
SECTIONS
{
    . = 0x809583B0;
    __renewal_start = .;
    .text : {
        native.o(.text.native)
        __renewal_creator = .;
        native.o(.text.creator)
        __renewal_adapter = .;
        *(.text .text.*)
        . = ALIGN(16);
    }
    __renewal_end = .;
    .unexpected : { *(.rodata .rodata.* .data .data.* .bss .bss.* COMMON) }
    ASSERT(__renewal_creator == 0x80959230, "Native renewal prefix changed")
    ASSERT(SIZEOF(.unexpected) == 0, "Renewal adapter must not have separate data or mutable globals")
    ASSERT(__renewal_end - __renewal_start <= 0x3000, "Renewal actor exceeds its guarded heap image budget")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
