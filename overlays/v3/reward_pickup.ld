OUTPUT_ARCH(mips)
ENTRY(af_v3_reward_pickup)
af_v3_reward_flag = 0x8046B4A8;
af_v3_player_selected_equipment = 0x804A5828;
af_v3_reward_request = 0x804B24E0;
SECTIONS
{
    . = 0x804B2620;
    .text : { *(.text.af_v3_reward_pickup) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x804B2800, "Reward pickup overlaps retained bobber artwork")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "Unexpected reward pickup state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
