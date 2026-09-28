OUTPUT_ARCH(mips)
ENTRY(af_holiday_owner_start)
SECTIONS {
 . = 0x806EC900;
 .text : { *(.text.af_holiday_owner_start) *(.text .text.*) . = ALIGN(16); }
 .rodata : { *(.rodata .rodata.*) . = ALIGN(16); }
 .forbidden : { *(.data .data.* .bss .bss.* COMMON) }
 /DISCARD/ : { *(.reginfo .MIPS.abiflags .pdr .comment .gnu.attributes .note.*) }
 ASSERT(SIZEOF(.forbidden) == 0, "Holiday owners use checked explicit state")
 ASSERT(. <= 0x806ED800, "Holiday owners overlap source event data")
}
