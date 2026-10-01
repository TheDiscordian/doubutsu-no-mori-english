OUTPUT_ARCH(mips)
ENTRY(af_v3_npc_mail_heap_range)
SECTIONS {
    . = 0x804F3820;
    .text : { *(.text.af_v3_npc_mail_heap_range) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x804F3A00,"Mail heap guard exceeds unused startup space")
    ASSERT(SIZEOF(.data)==0 && SIZEOF(.bss)==0,"Unexpected mail heap state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
