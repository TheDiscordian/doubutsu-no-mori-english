OUTPUT_ARCH(mips)
ENTRY(af_v3_field_shop)
af_v3_furniture_import_profile = 0x80465000;
af_v3_room_query = 0x804680B8;
af_v3_original_shop_furniture = 0x8046A200;
SECTIONS
{
    . = 0x8046A400;
    .text : { *(.text.af_v3_field_shop) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x8046BFF0, "V3 field helpers exceed the resident allocation")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "Unexpected V3 field state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
