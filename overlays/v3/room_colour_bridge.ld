OUTPUT_ARCH(mips)
ENTRY(af_v3_room_colour_update_bridge)
SECTIONS {
    . = 0x804B1E60;
    .text : { *(.text.af_v3_room_colour_update_bridge) *(.text.af_v3_room_colour_draw_bridge) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x804B1F40, "Player colour bridges exceed reserved room padding")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "Unexpected player colour bridge state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
