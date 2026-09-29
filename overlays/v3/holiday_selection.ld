OUTPUT_ARCH(mips)
ENTRY(af_holiday_world_bind)
SECTIONS {
 . = AF_HS_LINK_RAM;
 .text : { *(.text.af_holiday_world_bind) *(.text .text.*) . = ALIGN(16); }
 af_hs_code_end = .;
 .rodata : {
   *(.rodata .rodata.*) *(.data .data.*) . = ALIGN(16);
   af_hs_state_start = .;
   *(.bss .bss.* COMMON) . = ALIGN(16);
   af_hs_state_end = .;
   LONG(0x4146484F); LONG(0x4146484F); LONG(0x4146484F); LONG(0x4146484F);
 }
 af_hs_end = .;
 /DISCARD/ : { *(.reginfo .MIPS.abiflags .pdr .comment .gnu.attributes .note.*) }
 ASSERT(. <= 0x807DA800, "Optional holiday dialogue exceeds resident memory")
}
