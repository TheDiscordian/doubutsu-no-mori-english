OUTPUT_ARCH(mips)
SECTIONS
{
    . = __classic_extension_base;
    __classic_start = .;
    .text : { *(.text .text.*) . = ALIGN(16); }
    __classic_code_end = .;
    .data : { *(.data .data.* .rodata .rodata.*) . = ALIGN(16); }
    __classic_end = .;
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(SIZEOF(.bss) == 0, "Classic letter adapters must not add unowned BSS")
    ASSERT(__classic_end - __classic_start <= 0x1000, "Classic letter adapter exceeds its budget")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
