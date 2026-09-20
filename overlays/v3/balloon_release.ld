OUTPUT_ARCH(mips)
ENTRY(af_v3_balloon_request)
af_v3_player_selected_equipment = 0x804A5828;
af_v3_balloon_fly = 0x804AC778;
af_v3_reward_release_setup = 0x804AE818;
af_v3_reward_release_transition = 0x804AE914;
af_v3_reward_request = 0x804B24E0;
SECTIONS
{
    . = 0x804B1100;
    .text : {
        *(.text.af_v3_balloon_request) *(.text .text.*)
        ASSERT(. <= 0x804B1680, "Balloon release overlaps public queue entry");
        . = 0x580;
        *(.af_balloon_queue)
    }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x804B1800, "Balloon release overlaps room rigs")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "Unexpected balloon release state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
