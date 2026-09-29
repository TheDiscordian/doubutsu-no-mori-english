OUTPUT_ARCH(mips)
ENTRY(af_holiday_calendar_mode)
EXTERN(af_holiday_calendar_copy af_holiday_calendar_schedule
       af_holiday_calendar_status af_holiday_calendar_today
       af_holiday_calendar_run_today af_holiday_calendar_owner_today
       af_diary_native_selected af_diary_native_open af_diary_native_visit
       af_diary_native_live_player af_diary_native_attend
       af_diary_native_context_bytes af_holiday_calendar_choice)
memcpy = 0x80034BF8;
memset = 0x8003B9B0;
SECTIONS {
 . = AF_HCAL_LINK_RAM;
 .text : { *(.text.af_holiday_calendar_mode) *(.text .text.*) . = ALIGN(16); }
 .rodata : { *(.rodata .rodata.*) . = ALIGN(16); }
 .forbidden : { *(.data .data.* .bss .bss.* COMMON) }
 /DISCARD/ : { *(.reginfo .MIPS.abiflags .pdr .comment .gnu.attributes .note.*) }
 ASSERT(SIZEOF(.forbidden)==0, "Calendar state belongs to the native owner and saved diary")
 ASSERT(. <= AF_HCAL_LINK_RAM+0x8000, "Calendar connection exceeds reservation")
}
