OUTPUT_ARCH(mips)
ENTRY(af_holiday_motion_animation)
SECTIONS {
 . = DEFINED(HOLIDAY_MOTION_BASE) ? HOLIDAY_MOTION_BASE : 0x806E6000;
 .text : { *(.text.af_holiday_motion_animation) *(.text .text.*) . = ALIGN(16); }
 .rodata : { *(.rodata .rodata.*) . = ALIGN(16); }
 .forbidden : { *(.data .data.* .bss .bss.* COMMON) }
 /DISCARD/ : { *(.reginfo .MIPS.abiflags .pdr .comment .gnu.attributes .note.*) }
 ASSERT(SIZEOF(.forbidden) == 0, "Holiday motion must not add hidden state")
 ASSERT(. <= (DEFINED(HOLIDAY_MOTION_BASE) ? HOLIDAY_MOTION_BASE+0x1000 : 0x806EE000), "Holiday actor code exceeds its reservation")
}
