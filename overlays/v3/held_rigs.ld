OUTPUT_ARCH(mips)
ENTRY(af_v3_held_setup)
af_v3_held_setup_displacement = 0x808DD748 - (0x808B83B4 + 8);
SECTIONS
{
    . = 0x804B0000;
    .text : { *(.text.af_v3_held_setup) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= (DEFINED(af_v3_held_balloon_draw) ? 0x804B1800 : 0x804B0FE0),
           "Animated equipment overlaps room-rig code or loop-volume state")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "Unexpected shared rig state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
