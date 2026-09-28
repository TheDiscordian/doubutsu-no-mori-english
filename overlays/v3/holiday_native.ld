OUTPUT_ARCH(mips)
ENTRY(af_holiday_native_type)
SECTIONS {
 . = 0x806EC300;
 .text : { *(.text.af_holiday_native_type) *(.text .text.*) . = ALIGN(16); }
 .rodata : { *(.rodata .rodata.*) . = ALIGN(16); }
 .forbidden : { *(.data .data.* .bss .bss.* COMMON) }
 /DISCARD/ : { *(.reginfo .MIPS.abiflags .pdr .comment .gnu.attributes .note.*) }
 ASSERT(SIZEOF(.forbidden) == 0, "Native holiday bridge uses existing event storage")
 ASSERT(. <= 0x806ED800, "Native holiday bridge overlaps source schedule")
}
