OUTPUT_ARCH(mips)
ENTRY(af_holiday_placement_native_make)
SECTIONS {
 . = 0x806F1C00;
 .text : { *(.text.af_holiday_placement_native_make) *(.text .text.*) . = ALIGN(16); }
 .rodata : { *(.rodata .rodata.*) . = ALIGN(16); }
 .forbidden : { *(.data .data.* .bss .bss.* COMMON) }
 /DISCARD/ : { *(.reginfo .MIPS.abiflags .pdr .comment .gnu.attributes .note.*) }
 ASSERT(SIZEOF(.forbidden) == 0, "Holiday placement uses native placement storage")
 ASSERT(. <= 0x806F3FF0, "Holiday placement exceeds existing packet")
}
