OUTPUT_ARCH(mips)
ENTRY(af_v3_surface_floor)
af_surface_dma = 0x80026B44;
SECTIONS {
    .text 0x80951BC4 : {
        *(.text.af_v3_surface_floor)
        ASSERT(. <= 0x118, "Floor copy exceeds complete native function");
        . = 0x118;
        *(.text.af_v3_surface_wall)
    }
    ASSERT(SIZEOF(.text) <= 0x230, "Wall copy exceeds complete native function")
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(SIZEOF(.rodata) == 0 && SIZEOF(.data) == 0 && SIZEOF(.bss) == 0,
           "Surface copies must not acquire absolute local data references")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
