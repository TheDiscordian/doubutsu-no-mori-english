OUTPUT_ARCH(mips)
ENTRY(af_font_entry)
SECTIONS
{
    . = 0x80C00000;
    __font_start = .;
    .text : { entry.o(.text) *(.text .text.*) . = ALIGN(16); }
    __font_text_end = .;
    .data : { *(.data .data.*) . = ALIGN(16); }
    __font_data_end = .;
    .rodata : { *(.rodata .rodata.*) . = ALIGN(16); }
    __font_bss_start = .;
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) . = ALIGN(16); }
    __font_end = .;
    ASSERT(__font_end - __font_start <= 0x3000, "Persistent English font exceeds allocation budget")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
