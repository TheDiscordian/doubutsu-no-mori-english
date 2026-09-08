OUTPUT_ARCH(mips)
ENTRY(af_glyph_bind)
SECTIONS
{
    . = 0x8019A900;
    __font_start = .;
    .text : { *(.text .text.*) }
    __font_text_end = .;
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    . = ALIGN(16);
    __font_bss_start = .;
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    __font_end = .;
    ASSERT(__font_end <= 0x8019B300, "Extended-font probe exceeds isolated scratch")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
