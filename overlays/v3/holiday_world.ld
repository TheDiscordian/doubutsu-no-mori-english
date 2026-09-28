OUTPUT_ARCH(mips)
ENTRY(af_holiday_world_bind)
af_holiday_reward_data = 0x806E7B00;
af_holiday_destination_data = 0x806E7C80;
af_holiday_players = 0x80126EC0;
af_holiday_visitor = 0x801439A0;
af_holiday_active = 0x80136FD8;
af_holiday_player = 0x80136EA3;
af_holiday_rtc = 0x80136FBC;
af_holiday_profiles = 0x80484000;
af_holiday_metadata = 0x80498000;
af_holiday_native_free = 0x800B83D4;
af_holiday_native_give = 0x800B8B8C;
memset = 0x8003B9B0;
memcpy = 0x80034BF8;
SECTIONS {
 . = 0x806E8000;
 .text : { *(.text.af_holiday_world_bind) *(.text .text.*) . = ALIGN(16); }
 .rodata : { *(.rodata .rodata.*) . = ALIGN(16); }
 .forbidden : { *(.data .data.* .bss .bss.* COMMON) }
 /DISCARD/ : { *(.reginfo .MIPS.abiflags .pdr .comment .gnu.attributes .note.*) }
 ASSERT(SIZEOF(.forbidden) == 0, "Holiday world must not add hidden state")
 ASSERT(. <= 0x806EE000, "Holiday world/controller exceeds existing packet")
}
