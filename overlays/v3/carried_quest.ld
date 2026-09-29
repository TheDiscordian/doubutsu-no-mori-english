OUTPUT_ARCH(mips)
ENTRY(af_cw_calendar_before_cleanup)
SECTIONS {
 . = 0x807B2000;
 .text : {
   KEEP(*(.text.af_cw_calendar_before_cleanup))
   KEEP(*(.text.af_cw_get_save .text.af_cw_reserve_save .text.af_cw_get_common .text.af_cw_reserve_common))
   KEEP(*(.text.af_cw_check_keep .text.af_cw_set_keep .text.af_cw_clear_keep))
   KEEP(*(.text.af_cw_finish_hunt .text.af_cw_placement))
   *(.text .text.*) . = ALIGN(16);
 }
 .rodata : { *(.rodata .rodata.*) . = ALIGN(16); }
 .forbidden : { *(.data .data.* .bss .bss.* COMMON) }
 /DISCARD/ : { *(.reginfo .MIPS.abiflags .pdr .comment .gnu.attributes .note.*) }
 ASSERT(SIZEOF(.forbidden)==0,"Quest state is explicitly owned")
 ASSERT(. <= 0x807B3F00,"Quest services overlap their state/guard")
}
