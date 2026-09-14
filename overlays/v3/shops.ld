OUTPUT_ARCH(mips)
ENTRY(af_v3_shop_category)
af_v3_furniture_import_profile = 0x80465000;
af_v3_original_shop_category = 0x8046BAA0;
SECTIONS
{
    . = 0x80469C00;
    .text : { *(.text.af_v3_shop_category) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x8046A000, "V3 shop helper exceeds its reserved gap")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "Unexpected V3 shop state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
