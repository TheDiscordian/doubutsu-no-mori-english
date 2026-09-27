OUTPUT_ARCH(mips)
ENTRY(af_v3_creature_grid_item)
af_creature_ui_data = 0x80654F00;
af_v3_creature_collected = AF_CREATURE_COLLECTED;
af_creature_item_type = AF_CREATURE_ITEM_TYPE;
af_ui_native_fish_item = 0x800A56CC;
af_ui_item_name = 0x800BB6A8;
af_ui_set_message = 0x8007B5C0;
SECTIONS {
    . = 0x80654800;
    .text : { *(.text.af_v3_creature_grid_item) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x80654F00,"Creature collection/messages overlap identity data")
    ASSERT(SIZEOF(.data)==0 && SIZEOF(.bss)==0,"Unexpected creature UI globals")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
