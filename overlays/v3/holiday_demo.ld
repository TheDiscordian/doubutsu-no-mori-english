OUTPUT_ARCH(mips)
ENTRY(af_holiday_demo_main)
SECTIONS {
 . = 0x806FE000;
 .text : { *(.text.af_holiday_demo_main) *(.text .text.*) . = ALIGN(16); }
 .rodata : { *(.rodata .rodata.*) . = ALIGN(16); }
 .forbidden : { *(.data .data.* .bss .bss.* COMMON) }
 /DISCARD/ : { *(.reginfo .MIPS.abiflags .pdr .comment .gnu.attributes .note.*) }
 ASSERT(SIZEOF(.forbidden)==0, "Demo state uses an owned transient reservation")
 ASSERT(. <= 0x806FFF80, "Demo code overlaps its transient state")
}
