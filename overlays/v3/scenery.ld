OUTPUT_ARCH(mips)
ENTRY(af_v3_scenery_construct)
af_v3_ground_prepare = 0x804AD000;
af_v3_player_selected_equipment = 0x804A5828;
af_scenery_dma = 0x80026B44;
af_scenery_crc = 0x80195938;
af_scenery_writeback = 0x8002FE00;
af_scenery_invalidate = 0x80034CE0;
af_scenery_term = 0x800CA070;
af_scenery_fault = 0x80029AB4;
af_v3_native_tree_grow = 0x804ADFC0;
af_v3_native_tree_stump = 0x804ADFD0;
SECTIONS
{
    . = 0x804B5000;
    .text : { *(.text.af_v3_scenery_construct) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x804B6000, "Scenery runtime exceeds its reservation")
    ASSERT(SIZEOF(.data)==0 && SIZEOF(.bss)==0, "Unexpected scenery global state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
