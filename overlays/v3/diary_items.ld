OUTPUT_ARCH(mips)
ENTRY(af_diary_item_name)
SECTIONS {
 . = 0x806E0000;
 .text : { *(.text.af_diary_item_name) *(.text .text.*) . = ALIGN(16); }
 .rodata : { *(.rodata .rodata.*) . = ALIGN(16); }
 .forbidden : { *(.data .data.* .bss .bss.* COMMON) }
 /DISCARD/ : { *(.reginfo .MIPS.abiflags .pdr .comment .gnu.attributes .note.*) }
 ASSERT(SIZEOF(.forbidden) == 0, "Diary items use resident data only")
 ASSERT(. <= 0x806E2000, "Diary item code exceeds reservation")
}
