OUTPUT_ARCH(mips)
ENTRY(af_v3_balloon_descriptor)
af_v3_player_selected_equipment = 0x804A5828;
SECTIONS
{
    . = 0x804AC300;
    .text : { *(.text.af_v3_balloon_descriptor) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x804ACFF0, "Balloon actor overlaps category end guard")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "Unexpected balloon state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
