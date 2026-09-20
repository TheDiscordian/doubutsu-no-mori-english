OUTPUT_ARCH(mips)
ENTRY(af_v3_reward_wait_setup)
SECTIONS
{
    . = 0x804B3C90;
    .text : { *(.text.af_v3_reward_wait_setup) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x804B3FF0, "Reward wait overlaps retained icon guard")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "Unexpected reward wait state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
