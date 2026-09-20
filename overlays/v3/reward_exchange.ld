OUTPUT_ARCH(mips)
ENTRY(af_v3_reward_exchange)
af_v3_reward_completed = 0x804B2764;
af_v3_player_selected_equipment = 0x804A5828;
/* Bound to the current complete wrapped-parent implementation by the installer. */
af_v3_present_encode = 0x804B415C;
SECTIONS
{
    . = 0x804AD650;
    .text : { *(.text.af_v3_reward_exchange) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x804ADC00, "Reward exchange overlaps ground configuration")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "Unexpected reward exchange state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
