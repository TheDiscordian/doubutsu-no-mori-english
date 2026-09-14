OUTPUT_ARCH(mips)
ENTRY(af_v3_save_check_extended)
af_v3_furniture_import_profile = 0x80465000;
af_v3_clothing_source = 0x804608F0;
af_v3_original_item_name = 0x80464600;
af_v3_original_item_type = 0x80464610;
af_v3_original_item_size = 0x80464620;
af_v3_original_item_place = 0x80464630;
af_v3_original_item_price = 0x80464640;
SECTIONS
{
    . = 0x8046D000;
    .text : {
        *(.text.af_v3_save_check_extended)
        code.o(.text .text.*)
        *(.text.find_clothing) *(.text.find)
        /* Keep the installed display-reader calls stable; reject growth past
           this fixed public entry instead of silently moving every consumer. */
        . = 0x8DC;
        *(.text.af_v3_item_name_extended) *(.text .text.*)
    }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x8046DBF0, "V3 clothing codec exceeds its ROM and RAM reservation")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "Unexpected V3 clothing codec state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
