OUTPUT_ARCH(mips)
ENTRY(af_v3_furniture_action_sound)
af_v3_furniture_import_profile = 0x80465000;
SECTIONS {
    . = 0x80483D00;
    .text : { *(.text.af_v3_furniture_action_sound) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x80483FC0, "Furniture behaviour code overlaps the fire vtables")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "Unexpected furniture behaviour state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
