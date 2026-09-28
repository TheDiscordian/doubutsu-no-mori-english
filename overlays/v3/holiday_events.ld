OUTPUT_ARCH(mips)
ENTRY(af_holiday_event_plan)
SECTIONS {
 . = 0x806EB400;
 .text : { *(.text.af_holiday_event_plan) *(.text .text.*) . = ALIGN(16); }
 .rodata : { *(.rodata .rodata.*) . = ALIGN(16); }
 .forbidden : { *(.data .data.* .bss .bss.* COMMON) }
 /DISCARD/ : { *(.reginfo .MIPS.abiflags .pdr .comment .gnu.attributes .note.*) }
 ASSERT(SIZEOF(.forbidden) == 0, "Holiday events use caller-owned state")
 ASSERT(. <= 0x806ED800, "Holiday events exceed the retained NPC packet")
}
