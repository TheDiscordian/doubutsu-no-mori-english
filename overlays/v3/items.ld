OUTPUT_ARCH(mips)
ENTRY(af_v3_item_name)
af_v3_furniture_import_profile = 0x80465000;
af_v3_original_item_name = 0x80464600;
af_v3_original_item_type = 0x80464610;
af_v3_original_item_size = 0x80464620;
af_v3_original_item_place = 0x80464630;
af_v3_original_item_price = 0x80464640;
SECTIONS
{
    . = 0x80467300;
    .text : {
        *(.text.af_v3_item_name) *(.text.find)
        /* Public calls retain their addresses when the private table search
           changes from the compiler's two-row unroll to a bounded loop. */
        . = 0x14C;
        *(.text.af_v3_item_type) *(.text .text.*)
    }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x80467FF0, "V3 item helpers overlap the resident guard")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "Unexpected V3 item state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
