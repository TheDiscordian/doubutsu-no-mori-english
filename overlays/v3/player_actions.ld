OUTPUT_ARCH(mips)
ENTRY(af_v3_player_action_v0)
SECTIONS
{
    . = 0x804A5000;
    .text : { *(.text.af_v3_player_action_v0) *(.text .text.*) }
    /* Keep existing constants at their fixed addresses when appending the
       shared tool adapter. Both sections are included in the runtime image. */
    .rodata : { *(.rodata .rodata.*) *(.af_tool_controls) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x804A6000, "Player action code overlaps held parent readers")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "Unexpected player action state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
