OUTPUT_ARCH(mips)
ENTRY(af_v3_reward_bury_submenu)
af_v3_reward_request = 0x804B24E0;
af_v3_reward_exchange = 0x804AD650;
SECTIONS
{
    . = 0x804AE690;
    .text : { *(.text.af_v3_reward_bury_submenu) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x804AEF00, "Deferred rewards overlap event stock records")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "Unexpected deferred reward state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
