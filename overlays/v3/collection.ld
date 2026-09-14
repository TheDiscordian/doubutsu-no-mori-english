OUTPUT_ARCH(mips)
ENTRY(af_v3_catalogue_record)
af_v3_require_save_state = 0x804692F4;
af_v3_save_halt = 0x80469270;
af_v3_save_collect = 0x8046B9C4;
af_v3_furniture_import_profile = 0x80465000;
af_v3_original_collect = 0x8046BA80;
af_v3_original_private_clear = 0x8046BA90;
SECTIONS
{
    . = 0x804699C0;
    .text : { *(.text.af_v3_catalogue_record) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x8046A200, "V3 collection code overlaps field bridge")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "Unexpected V3 collection state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
