OUTPUT_ARCH(mips)
ENTRY(af_hi_menu_type)
SECTIONS {
 . = AF_HI_LINK_RAM;
 .text : { *(.text.af_hi_menu_type) *(.text .text.*) . = ALIGN(16); }
 .rodata : { *(.rodata .rodata.*) . = ALIGN(16); }
 .forbidden : { *(.data .data.* .bss .bss.* COMMON) }
 /DISCARD/ : { *(.reginfo .MIPS.abiflags .pdr .comment .gnu.attributes .note.*) }
 ASSERT(SIZEOF(.forbidden)==0, "Carried event controls keep state in their native owner")
 ASSERT(. <= AF_HI_LINK_RAM+0x2000, "Carried event controls exceed reservation")
}
