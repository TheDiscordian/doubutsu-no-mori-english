OUTPUT_ARCH(mips)
ENTRY(af_holiday_transition_run)
SECTIONS {
 . = 0x806FC000;
 .text : { *(.text.af_holiday_transition_run) *(.text .text.*) . = ALIGN(16); }
 .rodata : { *(.rodata .rodata.*) . = ALIGN(16); }
 .forbidden : { *(.data .data.* .bss .bss.* COMMON) }
 /DISCARD/ : { *(.reginfo .MIPS.abiflags .pdr .comment .gnu.attributes .note.*) }
 ASSERT(SIZEOF(.forbidden)==0, "Event transitions use explicit caller state")
 ASSERT(. <= 0x806FE000, "Event transition overlaps the installed announcement module")
}
