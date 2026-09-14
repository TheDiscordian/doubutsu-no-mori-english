OUTPUT_ARCH(mips)
ENTRY(af_v3_shop_type_809cacbc)
af_v3_room_query = 0x804680B8;
SECTIONS
{
    . = 0x80467600;
    .text : { *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x80467FF0, "Shop interaction detours exceed checked resident space")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "Unexpected shop interaction state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
