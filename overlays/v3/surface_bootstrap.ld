OUTPUT_ARCH(mips)
ENTRY(af_v3_surface_init)
af_surface_dma = 0x80026B44;
af_surface_crc = 0x80195938;
af_surface_writeback = 0x8002FE00;
af_surface_invalidate = 0x80034CE0;
af_surface_prior_init = 0x8046A000;
SECTIONS {
    . = 0x804A8D40;
    .text : { *(.text.af_v3_surface_init) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x804A8FF0,"Surface bootstrap overlaps the equipment guard")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0,"Unexpected surface bootstrap state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
