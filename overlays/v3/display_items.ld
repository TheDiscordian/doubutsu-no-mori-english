OUTPUT_ARCH(mips)
ENTRY(af_v3_display_pocket_item)
af_v3_furniture_import_profile = 0x80465000;
af_v3_base_item_name = 0x8046D8DC;
af_v3_base_item_type = 0x8046D9E8;
af_v3_base_item_place = 0x8046DA6C;
af_v3_base_item_price = 0x8046DB2C;
af_v3_prior_catalogue_record = 0x80466F00;
af_v3_prior_catalogue_owned = 0x80466F10;
SECTIONS
{
    . = 0x80466C00;
    .text : { *(.text.af_v3_display_pocket_item) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x80466F00, "Display item readers overlap collection bridges")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "Unexpected display item state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
