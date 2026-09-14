OUTPUT_ARCH(mips)
ENTRY(af_v3_room_value_clothing)
af_v3_furniture_import_profile = 0x80465000;
af_v3_item_type = 0x8046744C;
af_v3_room_query = 0x804680B8;
SECTIONS
{
    . = 0x80463C30;
    .text : { *(.text.af_v3_room_value_clothing) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x80464000, "V3 clothing menu overlaps villager readers")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "Unexpected clothing menu state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
