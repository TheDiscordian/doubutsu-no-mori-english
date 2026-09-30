OUTPUT_ARCH(mips)
ENTRY(af_hr_calendar_before_cleanup)
SECTIONS {
 . = 0x807F0000;
 af_hr_packet_start = .;
 .text : { *(.text .text.*) . = ALIGN(16); }
 af_hr_code_end = .;
 .rodata : { *(.rodata .rodata.*) . = ALIGN(16); }
 .data : { *(.data .data.*) . = ALIGN(16); }
 af_hr_bss_start = .;
 .bss : { *(.bss .bss.* COMMON) . = ALIGN(16); }
 af_hr_bss_end = .;
 .guard : { LONG(0x41464852); LONG(0x41464852); LONG(0x41464852); LONG(0x41464852); }
 af_hr_packet_end = .;
 ASSERT(. <= 0x807FC000, "Complete Harvest owner exceeds its code/state reservation")
 /DISCARD/ : { *(.reginfo .MIPS.abiflags .pdr .comment .gnu.attributes .note.*) }
}
