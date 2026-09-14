OUTPUT_ARCH(mips)
ENTRY(af_v3_menu_type_80872bb0)
af_v3_room_query = 0x804680B8;
SECTIONS
{
    . = 0x8046A800;
    .text : { *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x8046BFF0, "V3 menu detours exceed the resident allocation")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "Unexpected V3 menu state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
