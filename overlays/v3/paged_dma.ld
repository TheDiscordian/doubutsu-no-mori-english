OUTPUT_ARCH(mips)
ENTRY(af_v3_paged_dma)
af_resource_virtual = 0x80026B44;
SECTIONS {
    . = AF_RESOURCE_DMA_RAM;
    .text : { *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= AF_RESOURCE_DMA_RAM + 256, "Resource DMA adapter exceeds reservation")
    ASSERT(SIZEOF(.data)==0 && SIZEOF(.bss)==0, "Unexpected resource DMA state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
