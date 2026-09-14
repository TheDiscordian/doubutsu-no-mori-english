OUTPUT_ARCH(mips)
ENTRY(af_v3_room_value)
af_v3_furniture_import_profile = 0x80465000;
SECTIONS
{
    . = 0x80468000;
    .text : { *(.text.af_v3_room_value) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x8046BFF0, "V3 room detours overlap the resident guard")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "Unexpected V3 room state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
