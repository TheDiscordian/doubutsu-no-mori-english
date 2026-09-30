OUTPUT_ARCH(mips)
ENTRY(af_bank_menu_construct_entry)
SECTIONS {
 . = 0x807D8040;
 .text : { *(.text .text.*) . = ALIGN(16); }
 .rodata : { *(.rodata .rodata.*) . = ALIGN(16); }
 .data : { *(.data .data.*) . = ALIGN(16); }
 af_bank_bss_start = .;
 .bss (NOLOAD) : { *(.bss .bss.* COMMON) . = ALIGN(16); }
 af_bank_bss_end = .;
 af_bank_code_end = .;
 /DISCARD/ : { *(.reginfo .MIPS.abiflags .pdr .comment .gnu.attributes .note.*) }
 ASSERT(. <= 0x807E2030, "Complete bank code/state overlaps its guard or artwork")
}
