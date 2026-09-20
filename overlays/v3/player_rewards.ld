OUTPUT_ARCH(mips)
ENTRY(af_v3_reward_bgm)
SECTIONS
{
    . = 0x804B3880;
    .text : { *(.text.af_v3_reward_bgm) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x804B3FF0, "Reward controls overlap the retained icon guard")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "Unexpected reward state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
