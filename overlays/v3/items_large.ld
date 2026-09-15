OUTPUT_ARCH(mips)
ENTRY(af_v3_item_name_extended)
af_v3_furniture_import_profile = 0x80465000;
af_v3_roster_clothing_record = 0x80473A00;
af_v3_original_item_name = 0x80464600;
af_v3_original_item_type = 0x80464610;
af_v3_original_item_size = 0x80464620;
af_v3_original_item_place = 0x80464630;
af_v3_original_item_price = 0x80464640;
SECTIONS
{
    . = 0x80483000;
    .text : { *(.text.af_v3_item_name_extended) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x80483FF0, "Multi-cell item code overlaps the checked package guard")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "Unexpected multi-cell item state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
