OUTPUT_ARCH(mips)
ENTRY(af_carried_insect_spawn)
SECTIONS {
 . = 0x807AC000;
 .text : { *(.text.af_carried_insect_spawn) *(.text .text.*) . = ALIGN(16); }
 .rodata : { *(.rodata .rodata.*) . = ALIGN(16); }
 .forbidden : { *(.data .data.* .bss .bss.* COMMON) }
 /DISCARD/ : { *(.reginfo .MIPS.abiflags .pdr .comment .gnu.attributes .note.*) }
 ASSERT(SIZEOF(.forbidden)==0,"Quest spawning uses existing event/field state")
 ASSERT(. <= 0x807ADFF0,"Quest spawning overlaps the guarded quest reservation")
}
