OUTPUT_ARCH(mips)
ENTRY(af_holiday_message)
af_holiday_dialogue_data = 0x806E7800;
SECTIONS {
 . = 0x806E6800;
 .text : { *(.text.af_holiday_message) *(.text .text.*) . = ALIGN(16); }
 .rodata : { *(.rodata .rodata.*) . = ALIGN(16); }
 .forbidden : { *(.data .data.* .bss .bss.* COMMON) }
 /DISCARD/ : { *(.reginfo .MIPS.abiflags .pdr .comment .gnu.attributes .note.*) }
 ASSERT(SIZEOF(.forbidden) == 0, "Holiday dialogue must not add hidden state")
 ASSERT(. <= 0x806E7800, "Holiday dialogue exceeds reserved code")
}
