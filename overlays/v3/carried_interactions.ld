OUTPUT_ARCH(mips)
ENTRY(af_carried_interaction_menu)
SECTIONS {
 . = 0x80772070;
 .text : { *(.text.af_carried_interaction_menu) *(.text .text.*) . = ALIGN(16); }
 .rodata : { *(.rodata .rodata.*) . = ALIGN(16); }
 .forbidden : { *(.data .data.* .bss .bss.* COMMON) }
 /DISCARD/ : { *(.reginfo .MIPS.abiflags .pdr .comment .gnu.attributes .note.*) }
 ASSERT(SIZEOF(.forbidden) == 0, "Carried interactions use native transient state")
 ASSERT(. <= 0x80773800, "Carried interactions overlap item records")
}
