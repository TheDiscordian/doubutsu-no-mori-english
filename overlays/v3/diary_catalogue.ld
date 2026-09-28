OUTPUT_ARCH(mips)
ENTRY(af_diary_clutter_query)
SECTIONS {
 . = 0x806E1000;
 .text : { *(.text.af_diary_clutter_query) *(.text .text.*) . = ALIGN(16); }
 .rodata : { *(.rodata .rodata.*) . = ALIGN(16); }
 .forbidden : { *(.data .data.* .bss .bss.* COMMON) }
 /DISCARD/ : { *(.reginfo .MIPS.abiflags .pdr .comment .gnu.attributes .note.*) }
 ASSERT(SIZEOF(.forbidden) == 0, "Diary clutter query has no mutable storage")
 ASSERT(. <= 0x806E2000, "Diary clutter query exceeds packet reservation")
}
