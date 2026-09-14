OUTPUT_ARCH(mips)
ENTRY(af_v3_mannequin_80959320)
af_v3_room_query = 0x804680B8;
SECTIONS
{
    . = 0x80464C00;
    .text : { *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x80465000, "V3 shop mannequin overlaps furniture adapter")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "Unexpected mannequin state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
