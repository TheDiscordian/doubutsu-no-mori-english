OUTPUT_ARCH(mips)
ENTRY(af_carried_catalogue_bit)
SECTIONS {
 . = AF_CARRIED_CATALOGUE_RAM;
 .text : { *(.text.af_carried_catalogue_bit) *(.text .text.*) . = ALIGN(16); }
 .rodata : { *(.rodata .rodata.*) . = ALIGN(16); }
 .forbidden : { *(.data .data.* .bss .bss.* COMMON) }
 /DISCARD/ : { *(.reginfo .MIPS.abiflags .pdr .comment .gnu.attributes .note.*) }
 ASSERT(SIZEOF(.forbidden)==0,"Catalogue uses existing saved ownership")
 ASSERT(. <= 0x80773800,"Carried catalogue overlaps item records")
}
