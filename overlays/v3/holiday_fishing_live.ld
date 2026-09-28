OUTPUT_ARCH(mips)
ENTRY(af_hf_live_enter)
SECTIONS {
 . = 0x80734000;
 .text : { *(.text.af_hf_live_enter) *(.text .text.*) . = ALIGN(16); }
 .rodata : { *(.rodata .rodata.*) . = ALIGN(16); }
 .forbidden : { *(.data .data.* .bss .bss.* COMMON) }
 /DISCARD/ : { *(.reginfo .MIPS.abiflags .pdr .comment .gnu.attributes .note.*) }
 ASSERT(SIZEOF(.forbidden)==0,"Live fishing state is explicitly owned")
 ASSERT(.<=0x80737C00,"Fishing readers exceed their retained code reservation")
}
