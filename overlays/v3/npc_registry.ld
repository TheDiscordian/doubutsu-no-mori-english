OUTPUT_ARCH(mips)
ENTRY(af_v3_npc_extra_descriptor)
SECTIONS {
 . = 0x806E4000;
 .text : { *(.text.af_v3_npc_extra_descriptor) *(.text .text.*) . = ALIGN(16); }
 .rodata : { *(.rodata .rodata.*) . = ALIGN(16); }
 .forbidden : { *(.data .data.* .bss .bss.* COMMON) }
 /DISCARD/ : { *(.reginfo .MIPS.abiflags .pdr .comment .gnu.attributes .note.*) }
 ASSERT(SIZEOF(.forbidden) == 0, "NPC registry state belongs to the checked packet")
 ASSERT(. <= 0x806E6000, "NPC registry code exceeds its reservation")
}
