OUTPUT_ARCH(mips)
ENTRY(af_holiday_item_name)
SECTIONS {
 . = 0x80705600;
 .text : { *(.text.af_holiday_item_name) *(.text .text.*) . = ALIGN(16); }
 .rodata : { *(.rodata .rodata.*) . = ALIGN(16); }
 .forbidden : { *(.data .data.* .bss .bss.* COMMON) }
 /DISCARD/ : { *(.reginfo .MIPS.abiflags .pdr .comment .gnu.attributes .note.*) }
 ASSERT(SIZEOF(.forbidden) == 0, "Event items use resident data only")
 ASSERT(. <= 0x80705E00, "Event item code exceeds reservation")
}
