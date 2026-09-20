OUTPUT_ARCH(mips)
ENTRY(af_v3_reward_message_id)
SECTIONS
{
    . = 0x804B2280;
    .text : { *(.text.af_v3_reward_message_id) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x804B2800, "Reward messages overlap the inventory bobber")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "Unexpected reward-message state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
