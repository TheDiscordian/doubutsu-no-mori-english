OUTPUT_ARCH(mips)
ENTRY(af_holiday_pickup_try)
SECTIONS {
 . = 0x80707000;
 .text : { *(.text.af_holiday_pickup_try) *(.text .text.*) . = ALIGN(16); }
 .rodata : { *(.rodata .rodata.*) . = ALIGN(16); }
 .forbidden : { *(.data .data.* .bss .bss.* COMMON) }
 /DISCARD/ : { *(.reginfo .MIPS.abiflags .pdr .comment .gnu.attributes .note.*) }
 ASSERT(SIZEOF(.forbidden) == 0, "Event pickup uses the existing controller context")
 ASSERT(. <= 0x80708000, "Event pickup exceeds shared reservation")
}
