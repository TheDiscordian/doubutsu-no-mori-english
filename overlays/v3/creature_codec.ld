OUTPUT_ARCH(mips)
ENTRY(af_v3_save_check_extended)
af_v3_reward_data_valid = 0x8046B408;
af_v3_surface_profile_byte = 0x804BC900;
af_v3_creature_profile_byte = 0x80654000;
SECTIONS {
    . = 0x8064E000;
    .text : { *(.text.af_v3_save_check_extended) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x80650000,"Creature canonical codec overlaps save runtime")
    ASSERT(SIZEOF(.data)==0 && SIZEOF(.bss)==0,"Unexpected creature codec globals")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
