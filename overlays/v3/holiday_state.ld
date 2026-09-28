OUTPUT_ARCH(mips)
ENTRY(af_holiday_npc_event_world)
memcpy = 0x80034BF8;
memset = 0x8003B9B0;
af_holiday_rtc = 0x80136FBC;
af_holiday_random_native = 0x8002C9AC;
af_holiday_state_lunar = 0x800D60E4;
af_holiday_harvest_days = 0x806FBF80;
SECTIONS {
 . = 0x806F4000;
 .text : { *(.text.af_holiday_npc_event_world) *(.text .text.*) . = ALIGN(16); }
 .rodata : { *(.rodata .rodata.*) . = ALIGN(16); }
 .forbidden : { *(.data .data.* .bss .bss.* COMMON) }
 /DISCARD/ : { *(.reginfo .MIPS.abiflags .pdr .comment .gnu.attributes .note.*) }
 ASSERT(SIZEOF(.forbidden) == 0, "Holiday state is part of the checked saved diary")
 ASSERT(. <= 0x806FBF80, "Holiday services overlap the donor date table")
}
