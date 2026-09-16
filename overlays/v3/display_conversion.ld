OUTPUT_ARCH(mips)
ENTRY(af_v3_room_display_item)
af_v3_furniture_import_profile = 0x80465000;
af_v3_display_pocket_item = 0x80466C00;
af_v3_prior_display_item = 0x804665E0;
af_v3_prior_pocket_item = 0x804665F0;
SECTIONS
{
    . = 0x80466270;
    .text : { *(.text.af_v3_room_display_item) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x80466380, "Display conversion overlaps the display roster")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "Unexpected conversion state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
