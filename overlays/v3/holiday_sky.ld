OUTPUT_ARCH(mips)
ENTRY(af_sky_ready)
SECTIONS {
 . = 0x80738000;
 .text : { *(.text.af_sky_ready) *(.text .text.*) . = ALIGN(16); }
 .rodata : { *(.rodata .rodata.*) . = ALIGN(16); }
 .forbidden : { *(.data .data.* .bss .bss.* COMMON) }
 /DISCARD/ : { *(.reginfo .MIPS.abiflags .pdr .comment .gnu.attributes .note.*) }
 ASSERT(SIZEOF(.forbidden)==0,"Sky effects use the native effect pool")
 ASSERT(.<=0x8073C000,"Sky effects exceed their code reservation")
}
