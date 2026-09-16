OUTPUT_ARCH(mips)
ENTRY(af_v3_player_action_v0)
SECTIONS
{
    . = 0x804A5000;
    .text : { *(.text.af_v3_player_action_v0) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x804A6000, "Player action code overlaps held parent readers")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "Unexpected player action state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
