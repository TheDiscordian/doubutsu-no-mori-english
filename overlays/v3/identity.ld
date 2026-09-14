OUTPUT_ARCH(mips)
ENTRY(af_v3_identity_item)
af_v3_furniture_import_profile = 0x80465000;
af_v3_furniture_item = 0x804652E4;
SECTIONS
{
    . = 0x80469D00;
    .text : { *(.text.af_v3_identity_item) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x8046A200, "V3 room identity overlaps the field bridge")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "Unexpected V3 identity state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
