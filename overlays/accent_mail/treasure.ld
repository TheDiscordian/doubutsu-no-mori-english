OUTPUT_ARCH(mips)
SECTIONS
{
    . = __accent_extension_base;
    __accent_start = .;
    .text : { *(.text .text.*) . = ALIGN(16); }
    __accent_code_end = .;
    .data : { *(.data .data.* .rodata .rodata.*) . = ALIGN(16); }
    __accent_end = .;
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(SIZEOF(.bss) == 0, "Accent notice adapter must not add unowned BSS")
    ASSERT(__accent_end - __accent_start <= 0x1000, "Accent notice adapter exceeds its budget")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
