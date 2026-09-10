OUTPUT_ARCH(mips)
SECTIONS
{
    . = __title_extension_base;
    __title_start = .;
    .text : { *(.text .text.*) . = ALIGN(16); }
    __title_code_end = .;
    .data : { *(.data .data.* .rodata .rodata.*) . = ALIGN(16); }
    __title_end = .;
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(SIZEOF(.bss) == 0, "Title state must belong to the actor instance")
    ASSERT(__title_code_end - __title_start <= 0x2000, "Title code exceeds its budget")
    ASSERT(__title_end - __title_start <= 0x50000, "Title image exceeds its budget")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
