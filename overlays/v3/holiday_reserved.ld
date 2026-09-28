OUTPUT_ARCH(mips)
ENTRY(af_holiday_map_get)
memcpy = 0x80034BF8;
memset = 0x8003B9B0;
SECTIONS {
 . = 0x806F8800;
 .text : { *(.text.af_holiday_map_get) *(.text .text.*) . = ALIGN(16); }
 .rodata : { *(.rodata .rodata.*) . = ALIGN(16); }
 .forbidden : { *(.data .data.* .bss .bss.* COMMON) }
 /DISCARD/ : { *(.reginfo .MIPS.abiflags .pdr .comment .gnu.attributes .note.*) }
 ASSERT(SIZEOF(.forbidden) == 0, "Reserved event placement uses caller-owned state")
 ASSERT(. <= 0x806FB800, "Reserved event readers/owners exceed existing holiday packet")
}
