OUTPUT_ARCH(mips)
ENTRY(af_carried_name)
SECTIONS {
 . = 0x80771000;
 .text : { *(.text.af_carried_name) *(.text .text.*) . = ALIGN(16); }
 .rodata : { *(.rodata .rodata.*) . = ALIGN(16); }
 .forbidden : { *(.data .data.* .bss .bss.* COMMON) }
 /DISCARD/ : { *(.reginfo .MIPS.abiflags .pdr .comment .gnu.attributes .note.*) }
 ASSERT(SIZEOF(.forbidden) == 0, "Carried items use resident table state")
 ASSERT(. <= 0x80773800, "Carried code overlaps its records")
}
