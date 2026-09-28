OUTPUT_ARCH(mips)
ENTRY(af_v3_save_reset)
SECTIONS {
    . = 0x80670000;
    .text : { *(.text.af_v3_save_reset) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x80675FF0,"Diary/save code overlaps guarded diary state")
    ASSERT(SIZEOF(.data)==0 && SIZEOF(.bss)==0,"Unexpected diary storage globals")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
