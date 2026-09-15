OUTPUT_ARCH(mips)
ENTRY(af_v3_catalogue_bit)
af_v3_native_catalogue_bit = 0x808A931C;
af_v3_catalogue_program_continue = 0x808A6150;
af_v3_catalogue_furniture_continue = 0x808A6284;
af_v3_catalogue_type_continue = 0x808A6B1C;
af_v3_room_query = 0x804680B8;
af_v3_native_catalogue_available = 0x800C0490;
af_v3_catalogue_owned = 0x80469AD4;
af_v3_furniture_import_profile = 0x80465000;
af_v3_save_halt = 0x80469270;
SECTIONS
{
    . = 0x808B32B0;
    .text : { *(.text.af_v3_catalogue_bit) *(.text .text.*) }
    /* The native loader places its relocation DMA immediately after this
       complete image. Keep that destination aligned for the PI DMA engine. */
    .rodata : { *(.rodata .rodata.*) . = ALIGN(16); }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x808B3F00, "V3 catalogue suffix exceeds its bounded pool allowance")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "Unexpected V3 catalogue state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
