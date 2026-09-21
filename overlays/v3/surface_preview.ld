OUTPUT_ARCH(mips)
ENTRY(af_v3_preview_wall)
af_surface_dma = 0x80026B44;
af_surface_stock = 0x800C0490;
af_surface_price = 0x800C0194;
SECTIONS {
    .text 0x808A6854 : {
        *(.text.af_v3_preview_wall)
        ASSERT(. <= 0xF8, "Wall preview exceeds complete native function");
        . = 0xF8;
        *(.text.af_v3_preview_floor)
    }
    ASSERT(SIZEOF(.text) <= 0x1F0, "Floor preview exceeds complete native function")
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(SIZEOF(.rodata) == 0 && SIZEOF(.data) == 0 && SIZEOF(.bss) == 0,
           "Surface preview must not acquire absolute local data references")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
