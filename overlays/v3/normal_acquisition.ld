OUTPUT_ARCH(mips)
ENTRY(af_normal_shop_plants)
SECTIONS {
    . = 0x806E3600;
    .text : { *(.text.af_normal_shop_plants) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x806E3FF0,"Normal acquisition overlaps the retained packet guard")
    ASSERT(SIZEOF(.data)==0 && SIZEOF(.bss)==0,"Unexpected normal acquisition state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
