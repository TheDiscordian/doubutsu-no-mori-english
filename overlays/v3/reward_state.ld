OUTPUT_ARCH(mips)
ENTRY(af_v3_reward_data_valid)
af_v3_require_save_state = 0x804692F4;
af_v3_save_halt = 0x80469270;
af_v3_catalogue_clear = 0x80469B50;
af_v3_reward_stop_fanfare = 0x804B3A24;
SECTIONS
{
    . = 0x8046B408;
    .text : { *(.text.af_v3_reward_data_valid) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x8046B7A0, "Reward helpers overlap the stable save-pack entry")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "Unexpected reward helper state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
