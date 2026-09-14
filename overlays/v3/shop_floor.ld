OUTPUT_ARCH(mips)
ENTRY(af_v3_shop_floor_80953e54)
af_v3_room_query = 0x804680B8;
SECTIONS
{
    . = 0x80467C00;
    .text : { *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x80467FF0, "Shop floor branches exceed checked resident space")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "Unexpected shop floor state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
