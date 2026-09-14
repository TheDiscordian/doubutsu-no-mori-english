OUTPUT_ARCH(mips)
ENTRY(af_v3_ground_type_8090f888)
af_v3_room_query = 0x804680B8;
SECTIONS
{
    . = 0x8046AE00;
    .text : { *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x8046BFF0, "V3 ground detours exceed the resident allocation")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "Unexpected V3 ground state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
