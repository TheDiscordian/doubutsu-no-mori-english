OUTPUT_ARCH(mips)
ENTRY(af_holiday_scene_demo_init)
SECTIONS {
 . = 0x806FB200;
 .text : { *(.text.af_holiday_scene_demo_init) *(.text .text.*) . = ALIGN(16); }
 .rodata : { *(.rodata .rodata.*) . = ALIGN(16); }
 .forbidden : { *(.data .data.* .bss .bss.* COMMON) }
 /DISCARD/ : { *(.reginfo .MIPS.abiflags .pdr .comment .gnu.attributes .note.*) }
 ASSERT(SIZEOF(.forbidden)==0, "Event announcement uses native demo state")
 ASSERT(. <= 0x806FB700, "Event announcement overlaps its title directory")
}
