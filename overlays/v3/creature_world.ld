OUTPUT_ARCH(mips)
ENTRY(af_v3_patrol_swim)
af_water_attribute = 0x80070D28;
af_water_unit = 0x80089888;
af_water_is_water = 0x8007620C;
af_water_block = 0x80089348;
af_water_centre = 0x80088C74;
af_water_ground = 0x80071884;
af_water_height = 0x80075EA0;
af_patrol_random = 0x8002C9AC;
af_patrol_random2 = 0x8002CA00;
af_patrol_sin = 0x80099A94;
af_patrol_chase_angle = 0x80099AD4;
af_patrol_chase_float = 0x80099C18;
PROVIDE(af_spawn_collision = 0x80089538);
PROVIDE(af_spawn_event = 0x8007FF08);
PROVIDE(af_spawn_weather = 0x80098EE4);
PROVIDE(af_spawn_rank = 0x80084DE0);
PROVIDE(af_v3_creature_profile_byte = 0x80654000);
PROVIDE(af_v3_creature_season = 0x80654600);
PROVIDE(af_creature_item_type = AF_CREATURE_ITEM_TYPE);
PROVIDE(af_creature_save_collect = AF_CREATURE_SAVE_COLLECT);
PROVIDE(af_v3_require_save_state = AF_CREATURE_REQUIRE_STATE);
PROVIDE(af_v3_save_halt = AF_CREATURE_SAVE_HALT);
PROVIDE(af_creature_icons = AF_CREATURE_ICONS);
SECTIONS {
    . = 0x8064A000;
    .text : { *(.text.af_v3_patrol_swim) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x8064D000,"Fish world code overlaps calendars")
    ASSERT(SIZEOF(.data)==0 && SIZEOF(.bss)==0,"Unexpected fish world globals")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
