OUTPUT_ARCH(mips)
ENTRY(af_v3_scenery_boot)
af_scenery_dma = 0x80026B44;
af_scenery_crc = 0x80195938;
af_scenery_writeback = 0x8002FE00;
af_scenery_invalidate = 0x80034CE0;
af_scenery_fault = 0x80029AB4;
SECTIONS
{
    . = 0x804ADC90;
    .text : { *(.text.af_v3_scenery_boot) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x804ADFF0, "Scenery bootstrap overlaps retained ground guard")
    ASSERT(SIZEOF(.data)==0 && SIZEOF(.bss)==0, "Unexpected bootstrap state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
