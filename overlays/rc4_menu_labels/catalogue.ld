OUTPUT_ARCH(mips)
ENTRY(af_catalog_price_draw)
af_catalog_native_font = 0x80090E98;
SECTIONS {
    . = 0x808B3250;
    .text : { *(.text) }
    /DISCARD/ : { *(.reginfo) *(.MIPS.abiflags) *(.pdr) *(.gnu.attributes) }
}
