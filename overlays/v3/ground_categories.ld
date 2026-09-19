OUTPUT_ARCH(mips)
ENTRY(af_v3_ground_prepare)
af_v3_room_query = 0x804680B8;
SECTIONS
{
    . = 0x804AD000;
    .text : { *(.text.af_v3_ground_prepare) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x804ADC00, "Ground adapter overlaps configuration")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "Unexpected resident ground state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
