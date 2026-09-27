OUTPUT_ARCH(mips)
ENTRY(af_v3_save_reset)
af_v3_original_save_read = 0x8046BA60;
af_v3_original_save_clear = 0x8046BA70;
af_v3_surface_profile_byte = 0x804BC900;
af_v3_creature_profile_byte = 0x80654000;
af_v3_creature_player_clear = AF_CREATURE_CLEAR;
SECTIONS {
    . = 0x80650000;
    .text : { *(.text.af_v3_save_reset) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x80654000,"Creature save runtime overlaps saved readers")
    ASSERT(SIZEOF(.data)==0 && SIZEOF(.bss)==0,"Unexpected creature storage globals")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
