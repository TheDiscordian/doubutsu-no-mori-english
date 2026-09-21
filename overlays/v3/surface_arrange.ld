OUTPUT_ARCH(mips)
ENTRY(af_v3_single_wall)
af_surface_dma = 0x80026B44;
SECTIONS {
    .text 0x80950EC8 : {
        *(.text.af_v3_single_wall)
        ASSERT(. <= 0x54, "Wall copy exceeds complete native function");
        . = 0x54;
        *(.text.af_v3_single_floor)
    }
    ASSERT(SIZEOF(.text) <= 0xA8, "Floor copy exceeds complete native function")
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(SIZEOF(.rodata) == 0 && SIZEOF(.data) == 0 && SIZEOF(.bss) == 0,
           "Surface copies must not acquire absolute local data references")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
