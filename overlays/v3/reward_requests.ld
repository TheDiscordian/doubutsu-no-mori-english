OUTPUT_ARCH(mips)
ENTRY(af_v3_reward_request)
SECTIONS
{
    . = 0x804B24E0;
    .text : { *(.text.af_v3_reward_request) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x804B2800, "Reward requests overlap retained bobber artwork")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "Unexpected reward request state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
