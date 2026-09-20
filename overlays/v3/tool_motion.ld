OUTPUT_ARCH(mips)
ENTRY(af_v3_tool_action_setup)
SECTIONS
{
    . = 0x804A5A50;
    .text : { *(.text.af_v3_tool_action_setup) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) *(.af_tool_recovery) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x804A6000, "Tool setup overlaps held parent readers")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "Unexpected tool state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
