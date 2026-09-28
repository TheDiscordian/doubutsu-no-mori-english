OUTPUT_ARCH(mips)
ENTRY(af_holiday_fish_reset)
SECTIONS {
 . = 0x80730000;
 .text : { *(.text.af_holiday_fish_reset) *(.text .text.*) . = ALIGN(16); }
 .rodata : { *(.rodata .rodata.*) . = ALIGN(16); }
 .forbidden : { *(.data .data.* .bss .bss.* COMMON) }
 /DISCARD/ : { *(.reginfo .MIPS.abiflags .pdr .comment .gnu.attributes .note.*) }
 ASSERT(SIZEOF(.forbidden)==0,"Fishing state belongs to the caller")
 ASSERT(.<=0x80737C00,"Fishing code overlaps its caller-owned state")
}
