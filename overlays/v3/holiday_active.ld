OUTPUT_ARCH(mips)
ENTRY(af_holiday_active_update)
SECTIONS {
 . = 0x806F3000;
 .text : { *(.text.af_holiday_active_update) *(.text .text.*) . = ALIGN(16); }
 .rodata : { *(.rodata .rodata.*) . = ALIGN(16); }
 .forbidden : { *(.data .data.* .bss .bss.* COMMON) }
 /DISCARD/ : { *(.reginfo .MIPS.abiflags .pdr .comment .gnu.attributes .note.*) }
 ASSERT(SIZEOF(.forbidden)==0, "Hourly event code uses explicitly owned state")
 ASSERT(. <= 0x806F3FE0, "Hourly event code exceeds existing NPC packet tail")
}
