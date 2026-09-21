OUTPUT_ARCH(mips)
ENTRY(af_v3_surface_shop_category)
af_v3_surface_item_type = 0x804BC148;
af_surface_prior_shop_category = 0x80469C00;
SECTIONS {
    . = 0x804BFE00;
    .text : {
        *(.text.af_v3_surface_shop_category) *(.text .text.*)
        *(.rodata .rodata.*)
        ASSERT(. <= 0x804BFFD0,"Surface stock helpers exceed reserved packet gap");
        . = 0x1D0;
        *(.stock_bridge)
    }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x804BFFF0,"Surface stock bridge overlaps packet guard")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0,"Unexpected surface stock state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
