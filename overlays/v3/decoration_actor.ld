OUTPUT_ARCH(mips)
ENTRY(af_decor_actor_call)
SECTIONS {
 . = 0x8072A000;
 .text : { *(.text.af_decor_actor_call) *(.text .text.*) }
 .rodata : { *(.rodata .rodata.*) }
 .forbidden : { *(.data .data.* .bss .bss.* COMMON) }
 /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
 ASSERT(. <= 0x8072FFF0, "Decoration controllers exceed checked extension")
 ASSERT(SIZEOF(.forbidden) == 0, "Decoration controllers have unowned writable state")
}
