OUTPUT_ARCH(mips)
ENTRY(af_v3_creature_profile_byte)
af_v3_spawn_terms = AF_CREATURE_SPAWN_TERMS;
af_creature_item_type = AF_CREATURE_ITEM_TYPE;
af_v3_require_save_state = AF_CREATURE_REQUIRE_STATE;
af_v3_save_halt = AF_CREATURE_SAVE_HALT;
SECTIONS {
    . = 0x80654000;
    .text : {
        *(.text.af_v3_creature_profile_byte) *(.text.af_v3_creature_player_clear)
        ASSERT(. <= 0x80654600,"Creature profile readers overlap season entry");
        . = 0x600;
        *(.text.af_v3_creature_season) *(.text .text.*)
    }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x80654FF0,"Creature saved readers exceed checked page")
    ASSERT(SIZEOF(.data)==0 && SIZEOF(.bss)==0,"Unexpected creature save globals")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
